using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests.Explorer;

/* The story explorer.
 *
 * A bot that plays the story through the game's own logic, from new
 * journeys, taking every choice it can: every interactable in every zone,
 * every line in every conversation, the shops, the bed, the Wayfinder's
 * table, the night's arenas won and lost, a fight won and a fall. It keeps
 * each state it reaches (the journey, saved, and the zone's own memory),
 * hashes it to know it again, and goes breadth-first, a layer at a time,
 * keeping the most promising of each layer when there are too many (those
 * that reached something nobody had yet). Every state keeps the steps that
 * reached it, so whatever it finds can be played again step by step.
 *
 * What it looks for is what a reading of the files cannot see: the story
 * stuck (a quest that can no longer move, a conversation with no way out),
 * the story contradicting itself (the dead talking, a settled quest settled
 * again, a thing asked for after it is gone), choices whose effects cannot
 * happen, words that do not fill in, and what no road reaches at all. */

sealed class Options
{
    public List<Root> Roots = new();
    /// <summary>States expanded, per survivor.</summary>
    public int MaxStates = 2000;
    public int MaxDepth = 400;
    /// <summary>States kept per layer, per survivor.</summary>
    public int Beam = 12;
    /// <summary>The last day slept into.</summary>
    public int MaxDay = 6;
    /// <summary>Play the prologue's night (otherwise skip it, as the game's --zone does).</summary>
    public bool Prologue;
    /// <summary>States a stuck quest is given to move, before it is called a softlock.</summary>
    public int Confirm = 300;
    /// <summary>Keep every state's save once its survivor is done (to replay them).</summary>
    public bool Keep;
}

sealed class StoryExplorer
{
    public readonly Options O;
    public readonly List<Node> Nodes = new();
    readonly Dictionary<string, int> known = new();
    public readonly Dictionary<string, Finding> Findings = new();
    public readonly Coverage Seen = new();
    public readonly Stopwatch Clock = new();
    public int Expanded, Built;

    public StoryExplorer(Options o)
    {
        O = o;
        (Playthrough.StoryItems, Playthrough.StoryTags, Playthrough.StoryTraits) = StoryThings();
        Seen.Where = () => (at, doing);
    }

    /* -------------------------------------------------------- reporting -- */

    Node? at;
    Step? doing;
    Root root = null!;

    void Report(string kind, string key, string text, string file)
    {
        var k = $"{kind}:{key}";
        if (Findings.ContainsKey(k)) return;
        var trace = at?.Trace() ?? new();
        if (doing != null) trace.Add(doing);
        Findings[k] = new Finding(kind, k, text, file, root, trace);
    }

    void Wire(Playthrough p)
    {
        p.Report = Report;
        p.MaxDay = O.MaxDay;
        p.Locks = (k, why) => Seen.Lock(k, why);
        p.Offered = (where, pr) => Seen.Offer(where, pr, p.J);
    }

    /* -------------------------------------------------------------- run -- */

    public StoryExplorer Run()
    {
        Clock.Start();
        foreach (var r in O.Roots)
        {
            start = Nodes.Count;
            Explore(r);
            // What only this survivor's states can say, said now; then what
            // the analysis no longer needs let go (the saves are most of it).
            Softlocks();
            Lost();
            Loops();
            known.Clear();
            for (int i = start; i < Nodes.Count && !O.Keep; i++)
            {
                var n = Nodes[i];
                n.Save = "";
                n.Visit = n.Visit with { EntrySave = "", Done = null };
            }
        }
        Gates();
        Clock.Stop();
        return this;
    }

    /// <summary>A new survivor, through the prologue (or past it), into the Waystation.</summary>
    public Playthrough Begin(Root r)
    {
        var a = Callings.Archetype(r.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Wren", Archetype = r.Calling, Background = r.Background, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0], Sex = r.Sex,
        }, 42);
        if (O.Prologue)
        {
            var (p, stuck) = Playthrough.Night(j, Report);
            if (p != null) { Wire(p); return p; }
            Report("softlock", "prologue", $"The prologue cannot be played through: {stuck}", "logic/Play/Zones/Prologue.cs");
            j = Journey.Begin(new CreationChoice
            {
                Name = "Wren", Archetype = r.Calling, Background = r.Background, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
                Ability = a.Abilities[0], Sex = r.Sex,
            }, 42);
        }
        // Skipping ahead, as the game's --zone does: the prologue counts as done.
        j.World.Facts["prologue.done"] = true;
        j.World.Time = TimeOfDay.Day;
        var w = Playthrough.Enter(j, "waystation", "lowford", null, Report);
        Wire(w);
        return w;
    }

    void Explore(Root r)
    {
        root = r;
        at = null; doing = null;
        var p = Begin(r);
        var first = new Node { Id = Nodes.Count, Root = r, Save = p.Save(), Mode = Mode.Roam, Visit = p.Visit };
        first.Hash = Hash(first, p.J);
        Remember(first, p.J, null);
        var layer = new List<Node> { first };
        int expanded = 0;
        for (int depth = 0; depth < O.MaxDepth && layer.Count > 0 && expanded < O.MaxStates; depth++)
        {
            var next = new List<(Node N, int Fresh)>();

            foreach (var n in layer)
            {
                if (expanded++ >= O.MaxStates) break;
                next.AddRange(Expand(n));
            }
            // The most promising first: what reached something new, then what is
            // furthest into the story, then as found.
            layer = next.Select((x, i) => (x, i)).OrderByDescending(t => t.x.Fresh).ThenByDescending(t => t.x.N.Progress).ThenBy(t => t.i)
                .Take(O.Beam).Select(t => t.x.N).ToList();
        }
    }

    /// <summary>Everything that can be done from a state, done: the new states.</summary>
    List<(Node N, int Fresh)> Expand(Node n, Dictionary<string, int>? local = null)
    {
        n.Expanded = true;
        Expanded++;
        at = n;
        root = n.Root;
        var output = new List<(Node, int)>();
        var before = Playthrough.Load(n.Save);
        Playthrough p;
        if (n.Mode == Mode.Roam) { p = Playthrough.Rebuild(n.Visit, null); Built++; }
        else p = Playthrough.Paused(n, null);
        Wire(p);
        List<Step> steps;
        try { steps = p.Choices(); }
        catch (Exception e) { Crash(e, "choices"); return output; }
        var (x0, z0) = p.B != null ? (p.B.Player.X, p.B.Player.Z) : (0, 0);
        bool dirty = false, firstStep = true;
        foreach (var s in steps)
        {
            doing = s;
            if (n.Mode != Mode.Roam) { p = Playthrough.Paused(n, null); Wire(p); }
            else if (dirty) { p = Playthrough.Rebuild(n.Visit, null); Built++; Wire(p); dirty = false; }
            else if (!firstStep) p.Swap(n.Save, x0, z0);
            firstStep = false;
            Playthrough.Result? r;
            Seen.Pending = null;
            try { r = p.Do(s.Key); }
            catch (Exception e) { Crash(e, s.Key); dirty = true; continue; }
            if (n.Mode == Mode.Roam)
            {
                dirty = r?.Kind == Playthrough.Kind.Moved || p.Mark() != n.Visit.ZoneMark;
            }
            if (r == null) continue;
            try
            {
                var child = Child(n, s, p, r);
                if (child == null) continue;
                if (local != null)
                {
                    if (local.TryGetValue(child.Hash, out var id)) { n.Next.Add(id); continue; }
                    child.Id = Nodes.Count;
                    Nodes.Add(child);
                    local[child.Hash] = child.Id;
                    var cj = Playthrough.Load(child.Save);
                    child.Quests = Quests(cj);
                    child.Held = Held(cj.Ch).Select(string.Intern).ToArray();
                    Seen.Pending = null;
                    n.Next.Add(child.Id);
                    output.Add((child, 0));
                    continue;
                }
                if (known.TryGetValue(child.Hash, out var seenId)) { n.Next.Add(seenId); continue; }
                child.Id = Nodes.Count;
                int fresh = Remember(child, Playthrough.Load(child.Save), before);
                n.Next.Add(child.Id);
                output.Add((child, fresh));
            }
            catch (Exception e) { Crash(e, s.Key); dirty = true; }
        }
        doing = null;
        return output;
    }

    void Crash(Exception e, string key)
    {
        var site = e.StackTrace?.Split('\n').Select(l => l.Trim()).FirstOrDefault(l => l.Contains("SurvivorUnchained.") && !l.Contains(".Tests.")) ?? "";
        Report("crash", $"{e.GetType().Name}:{e.Message}:{site}", $"The game throws {e.GetType().Name}: {e.Message} ({site})", "logic");
    }

    /// <summary>The state a step led to: its visit carried on (or begun
    /// again, in a new zone), found fresh again when it can be.</summary>
    Node? Child(Node n, Step s, Playthrough p, Playthrough.Result r)
    {
        Visit v;
        if (r.Kind == Playthrough.Kind.Moved) v = p.Visit;
        else if (r.Kind == Playthrough.Kind.NeedZone)
        {
            // Back to walking about from a conversation or a screen: the zone,
            // as it was, with this step done in it.
            v = n.Visit with { Done = new Steps(s, n.Visit.Done) };
            p = Playthrough.Rebuild(v, null);
            Built++;
            v = v with { ZoneMark = p.Mark() };
        }
        else v = n.Visit with { Done = new Steps(s, n.Visit.Done), ZoneMark = p.Mode == Mode.Roam ? p.Mark() : n.Visit.ZoneMark };
        if (p.Mode == Mode.Roam) Look(p);
        var c = new Node
        {
            Parent = n, Step = s, Depth = n.Depth + 1, Root = n.Root, Save = p.Save(), Mode = p.Mode, Npc = p.Npc,
            At = p.Mode == Mode.Talk ? p.Runner!.Node!.Id : null, Arena = p.Arena != null && p.Mode == Mode.Arena ? Json.Write(p.Arena) : null, Visit = v,
        };
        c.Hash = Hash(c, p.J);
        if (known.ContainsKey(c.Hash)) return c;
        // The zone found as fresh as a new visit would make it: the visit begins
        // again here, so rebuilding it later need not replay the road to it.
        if (c.Mode == Mode.Roam && v.Done != null && Worth(v.Zone))
        {
            var f = Playthrough.Rebuild(new Visit(v.Zone, v.From, v.At, c.Save, null, ""), null);
            Built++;
            bool same = f.Mark() == v.ZoneMark && Canon(f.J) == Canon(p.J);
            var (tried, found) = rebased.GetValueOrDefault(v.Zone);
            rebased[v.Zone] = (tried + 1, found + (same ? 1 : 0));
            if (same) { c.Visit = new Visit(v.Zone, v.From, v.At, c.Save, null, v.ZoneMark); }
        }
        return c;
    }

    readonly Dictionary<string, (int Tried, int Found)> rebased = new();

    /// <summary>Whether finding a zone fresh again is worth a try: in a zone
    /// where it seldom is (the wood, roused), only now and then.</summary>
    bool Worth(string zone)
    {
        var (tried, found) = rebased.GetValueOrDefault(zone);
        return tried < 20 || found * 5 >= tried || tried % 10 == 0;
    }

    /// <summary>Walking about again: the chapter's page must read, and the
    /// tracker must work out what to do next.</summary>
    void Look(Playthrough p)
    {
        p.Chapter("walking about");
        try { Objectives.Of(p.J.Ctx); }
        catch (Exception e) { Crash(e, "objectives"); }
    }

    /* ------------------------------------------------------ remembering -- */

    /// <summary>A new state kept: what it reached that nothing had, and what
    /// went wrong on the way to it. How much was new, for the beam.</summary>
    int Remember(Node c, Journey j, Journey? before)
    {
        Nodes.Add(c);
        known[c.Hash] = c.Id;
        var w = j.World;
        c.Quests = Quests(j);
        c.Progress = j.World.Quests.Values.Sum(q => q.Entries.Count + (q.Status == QuestStatus.Resolved ? 5 : 0)) + j.World.Knowledge.Count + j.Ch.Knowledge.Count
            + j.World.Facts.Count(f => f.Value.Type is Fact.Kind.Str);
        c.Held = Held(j.Ch).Select(string.Intern).ToArray();
        int fresh = Seen.Take(c, j);
        if (c.Step?.Key.StartsWith("use:") == true) fresh += Seen.Add("use", $"{c.Parent!.Visit.Zone}:{c.Step.Key[4..]}");
        if (c.Mode == Mode.Talk && c.Parent?.Mode != Mode.Talk) fresh += Seen.Add("talk", c.Npc!);
        if (c.Step?.Key.StartsWith("say:") == true) fresh += Seen.Add("said", $"{c.Parent!.Npc}.{c.Parent.At}#{c.Step.Key[4..]}");
        if (c.Mode == Mode.Talk) c.Wants = Seen.WantsAt(c, j);
        if (before != null) Contradictions(before, j);
        Sane(j);
        return fresh;
    }

    static Dictionary<string, string> Quests(Journey j) =>
        j.World.Quests.ToDictionary(q => string.Intern(q.Key), q => string.Intern($"{q.Value.Status}:{string.Join(",", q.Value.Entries)}:{q.Value.Outcome}"));

    static IEnumerable<string> Held(CharacterData ch) =>
        ch.Pack.Where(i => i != null).Select(i => i!.Def).Concat(Items.EquipSlots.Select(s => ch.Equipment[s]?.Def).Where(d => d != null)!).Distinct().OrderBy(x => x, StringComparer.Ordinal)!;

    /// <summary>The world going back on itself between one state and the next.</summary>
    void Contradictions(Journey a, Journey b)
    {
        foreach (var (k, v) in a.World.Facts)
            if (v.Str == "dead" && b.World.Fact(k).Str != "dead")
                Report("contradiction", $"risen:{k}", $"{k} was dead, and is now {Show(b.World.Fact(k))}", "data/content");
        foreach (var (id, q) in a.World.Quests)
        {
            if (!b.World.Quests.TryGetValue(id, out var q2)) { Report("contradiction", $"quest-gone:{id}", $"The quest {id} vanished from the journal", "data/content/quests.json"); continue; }
            bool settled(QuestStatus s) => s is QuestStatus.Resolved or QuestStatus.Failed or QuestStatus.Abandoned;
            if (settled(q.Status) && settled(q2.Status) && q.Status != q2.Status)
                Report("contradiction", $"settled-twice:{id}", $"The quest {id} was {q.Status}, and is now {q2.Status}", "data/content/quests.json");
            if (q.Outcome != null && q2.Outcome != null && q.Outcome != q2.Outcome)
                Report("contradiction", $"outcome:{id}:{q.Outcome}>{q2.Outcome}", $"The quest {id} ended {q.Outcome}, and then ended {q2.Outcome}", "data/content/quests.json");
            foreach (var e in q.Entries.Where(e => !q2.Entries.Contains(e)))
                Report("contradiction", $"unwritten:{id}/{e}", $"The journal line {id}/{e} was written, and then taken out", "data/content/quests.json");
        }
        foreach (var (id, s) in a.World.Npcs)
            if (!s.Alive && b.World.Npc(id).Alive) Report("contradiction", $"alive:{id}", $"{id} was dead, and is alive", "data/content");
    }

    static string Show(Fact f) => f.IsNull ? "nothing" : $"'{f}'";

    /// <summary>Things that can never be: a purse below nothing, a stack of none.</summary>
    void Sane(Journey j)
    {
        if (j.Ch.Gold < 0) Report("contradiction", "gold", $"The survivor's purse is {j.Ch.Gold} gold", "logic");
        foreach (var it in j.Ch.Pack.Concat(j.World.Stash))
            if (it != null && it.Qty <= 0) Report("contradiction", $"qty:{it.Def}", $"The survivor carries {it.Qty}× {it.Def}", "logic");
        foreach (var (id, s) in j.World.Npcs)
            foreach (var axis in new[] { Axis.Trust, Axis.Affection, Axis.Respect, Axis.Fear })
                if (Math.Abs(s[axis]) > 100) Report("contradiction", $"rel:{id}:{axis}", $"{id}'s {axis} is {s[axis]}, past the scale", "logic");
    }

    /* -------------------------------------------------------------- hash -- */

    string Hash(Node n, Journey j)
    {
        var sb = new StringBuilder(n.Root.ToString()).Append('|').Append(Canon(j, coarse: true));
        sb.Append("|m:").Append(n.Mode).Append(':').Append(n.Npc).Append(':').Append(n.At).Append(':').Append(n.Arena?.GetHashCode());
        sb.Append("|z:").Append(n.Visit.ZoneMark);
        return Convert.ToHexString(System.Security.Cryptography.SHA1.HashData(Encoding.UTF8.GetBytes(sb.ToString())));
    }

    /// <summary>The journey as the story sees it: what conditions can ask
    /// about, and not what they cannot (the lines already read, the fog of the
    /// map, the ids the inventory gives things).</summary>
    /// <summary>Coarse, for knowing a state again: feelings and the purse to
    /// the nearest five (the gates ask in fives and tens), experience by the
    /// level, the deeds as a set. Two roads that differ by a kind word are one.</summary>
    public static string Canon(Journey j, bool coarse = false)
    {
        double F(double v) => coarse ? Math.Floor(v / 5) * 5 : v;
        var w = j.World; var ch = j.Ch;
        var sb = new StringBuilder();
        static string O<T>(IEnumerable<T> xs) => string.Join(",", xs.Select(x => x?.ToString()).OrderBy(x => x, StringComparer.Ordinal));
        sb.Append($"d{w.Day}{w.Time}|f:");
        foreach (var (k, v) in w.Facts.OrderBy(k => k.Key, StringComparer.Ordinal)) sb.Append(k).Append('=').Append(v.Type).Append(v).Append(';');
        sb.Append("|k:").Append(O(w.Knowledge));
        foreach (var (id, s) in w.Npcs.OrderBy(k => k.Key, StringComparer.Ordinal))
            sb.Append($"|n:{id}:{s.Alive}:{F(s.Trust)}:{F(s.Affection)}:{F(s.Respect)}:{F(s.Fear)}:{s.Location}:{O(s.Flags.Select(f => $"{f.Key}={f.Value}"))}:{O(s.Memories)}");
        foreach (var (id, f) in w.Factions.OrderBy(k => k.Key, StringComparer.Ordinal)) sb.Append($"|fa:{id}:{f.Standing}:{f.Strength}");
        foreach (var (id, q) in w.Quests.OrderBy(k => k.Key, StringComparer.Ordinal)) sb.Append($"|q:{id}:{q.Status}:{string.Join(",", q.Entries)}:{q.Outcome}:{(coarse ? null : q.StartedDay)}");
        sb.Append("|h:").Append(coarse ? O(w.History.Select(h => h.Id)) : string.Join(",", w.History.Select(h => h.Id)));
        sb.Append("|s:").Append(O(w.Scheduled.Select(s => $"{s.Day}:{s.Id}")));
        foreach (var (id, z) in w.Zones.OrderBy(k => k.Key, StringComparer.Ordinal)) sb.Append($"|z:{id}:{O(z.Where(f => f.Key != "seen").Select(f => $"{f.Key}={f.Value}"))}");
        if (w.Corpse is { } c) sb.Append($"|corpse:{c.Zone}:{c.Gold}:{O(c.Items.Select(i => i.Def))}");
        if (w.Nemesis is { } ne) sb.Append($"|nemesis:{ne.Def}:{ne.Killed}:{O(ne.Carries.Select(i => i.Def))}");
        sb.Append("|r:").Append(O(w.Rematches.Select(r => r.Id))).Append("|a:").Append(w.Arena?.Id);
        foreach (var (id, s) in w.Shops.OrderBy(k => k.Key, StringComparer.Ordinal)) sb.Append($"|shop:{id}:{s.RestockDay}:{O(s.Stock.Select(i => $"{i.Def}x{i.Qty}"))}");
        sb.Append("|stash:").Append(O(w.Stash.Where(i => i != null).Select(i => $"{i!.Def}x{i.Qty}")));
        sb.Append($"|ch:{ch.Level}:{(coarse ? 0 : ch.Xp)}:{ch.Points}:{ch.TraitPicks}:{F(Math.Min(ch.Gold, coarse ? 200 : ch.Gold))}:{F(ch.Stats.Kills)}:{ch.Stats.Deaths}");
        sb.Append("|t:").Append(O(ch.Traits)).Append("|ck:").Append(O(ch.Knowledge));
        sb.Append("|c:").Append(O(ch.Conditions.Select(x => $"{x.Id}:{x.Days}")));
        sb.Append("|p:").Append(O(ch.Pack.Where(i => i != null).Select(i => $"{i!.Def}x{i.Qty}:{i.Rarity}")));
        sb.Append("|e:").Append(O(Items.EquipSlots.Select(s => $"{s}={ch.Equipment[s]?.Def}:{ch.Equipment[s]?.Rarity}")));
        sb.Append("|sk:").Append(O(ch.Discovered)).Append('/').Append(O(ch.Skills)).Append('/').Append(O(ch.Known));
        return sb.ToString();
    }

    /* ------------------------------------------------------------ replay -- */

    /// <summary>A trace played again from the start, on one zone kept live
    /// the whole way (none of the explorer's short cuts): the journey it ends
    /// on, and the canon of it.</summary>
    public (Playthrough Play, string Canon) Replay(Root r, IEnumerable<Step> trace)
    {
        var silent = new StoryExplorer(O);
        silent.root = r;
        var p = silent.Begin(r);
        p.Report = null;
        foreach (var s in trace)
        {
            var res = p.Do(s.Key) ?? throw new InvalidOperationException($"could not {s.Words}");
        }
        return (p, Canon(p.J));
    }

    /* ---------------------------------------------------------- analysis -- */

    /// <summary>Where the survivor being explored begins in Nodes.</summary>
    int start;
    /// <summary>Quests seen settled, on any survivor's road so far.</summary>
    readonly HashSet<string> settles = new();

    IEnumerable<Node> Ours => Nodes.Skip(start);

    /// <summary>A quest in the journal that nothing moves on any more. Where
    /// the exploration saw a quest at some point of its story and never saw
    /// it move from there, it is given a search of its own to move it; if
    /// that cannot either, the quest is stuck.</summary>
    void Softlocks()
    {
        var places = new Dictionary<(string Q, string At), List<Node>>();
        foreach (var n in Ours.Where(n => n.Expanded && n.Mode == Mode.Roam))
            foreach (var (q, sig) in n.Quests)
                if (sig.StartsWith("Active:"))
                {
                    if (!places.TryGetValue((q, sig), out var l)) places[(q, sig)] = l = new();
                    l.Add(n);
                }
        // A quest that settles somewhere (on any road) and on this one cannot;
        // one that never settles in the chapter is an open thread, and the
        // report counts it among the quests never resolved.
        settles.UnionWith(Ours.SelectMany(n => n.Quests).Where(q => !q.Value.StartsWith("Active:") && !q.Value.StartsWith("Unknown:")).Select(q => q.Key));
        foreach (var ((q, sig), list) in places)
        {
            if (!settles.Contains(q)) continue;
            bool moves = list.Any(n => Reach(n, m => m.Quests.GetValueOrDefault(q) != sig, 4000));
            if (moves) continue;
            var from = list.OrderBy(n => n.Depth).First();
            if (Unstick(from, q, sig)) continue;
            at = from; doing = null; root = from.Root;
            Report("softlock", $"{q}:{sig}", $"The quest {q} is active ({sig[7..].TrimEnd(':')}), and nothing found moves it on", "data/content/quests.json");
        }
    }

    /// <summary>Whether a state leads (in what was explored) to one that holds.</summary>
    bool Reach(Node from, Func<Node, bool> goal, int limit)
    {
        var seen = new HashSet<int> { from.Id };
        var q = new Queue<Node>();
        q.Enqueue(from);
        while (q.Count > 0 && seen.Count < limit)
        {
            var n = q.Dequeue();
            foreach (var id in n.Next)
            {
                if (!seen.Add(id)) continue;
                var m = Nodes[id];
                if (goal(m)) return true;
                q.Enqueue(m);
            }
        }
        return false;
    }

    /// <summary>A search of a stuck quest's own, breadth-first and unpruned
    /// from where it was seen stuck: does anything move it?</summary>
    bool Unstick(Node from, string quest, string sig)
    {
        var local = new Dictionary<string, int>();
        var layer = new List<Node> { from };
        int count = 0;
        while (layer.Count > 0 && count < O.Confirm)
        {
            var next = new List<Node>();
            foreach (var n in layer)
            {
                if (count++ >= O.Confirm) break;
                var kids = n.Expanded ? n.Next.Select(i => Nodes[i]).ToList() : Expand(n, local).Select(x => x.N).ToList();
                foreach (var k in kids)
                {
                    if (k.Quests.GetValueOrDefault(quest) != sig) return true;
                    next.Add(k);
                }
            }
            layer = next;
        }
        return false;
    }

    /// <summary>A thing the story asks for after the survivor has lost it
    /// (sold it, given it up), when nothing explored after gets it back.</summary>
    void Lost()
    {
        var wanted = Playthrough.StoryItems;
        foreach (var n in Ours.Where(n => n.Parent != null).ToList())
        {
            foreach (var item in n.Parent!.Held.Except(n.Held).Where(wanted.Contains))
            {
                var key = $"gone:{item}";
                if (Findings.ContainsKey($"contradiction:{key}")) continue;
                // Asked for later, and never held again on the way.
                Node? asked = null;
                var seen = new HashSet<int> { n.Id };
                var q = new Queue<Node>(); q.Enqueue(n);
                bool back = false;
                while (q.Count > 0 && seen.Count < 3000 && !back)
                {
                    var m = q.Dequeue();
                    if (m.Held.Contains(item)) { back = true; break; }
                    if (m.Wants?.Contains(item) == true) asked ??= m;
                    foreach (var id in m.Next) if (seen.Add(id)) q.Enqueue(Nodes[id]);
                }
                if (back || asked == null) continue;
                at = asked; doing = null; root = asked.Root;
                Report("contradiction", key, $"{item} is asked for ({asked.Npc}.{asked.At}) after it was {n.Step!.Words.ToLowerInvariant()}, and nothing explored gets it back", "data/content");
            }
        }
    }

    /// <summary>A conversation that, once in a stretch of it, can only go
    /// round: every way on leads back into it, and none out.</summary>
    void Loops()
    {
        var talk = Ours.Where(n => n.Mode == Mode.Talk).ToList();
        var outs = new Dictionary<int, bool?>();
        foreach (var n in talk)
        {
            if (!n.Expanded) continue;
            var seen = new HashSet<int> { n.Id };
            var st = new Stack<Node>(); st.Push(n);
            bool exit = false, unknown = false;
            while (st.Count > 0 && !exit && seen.Count < 2000)
            {
                var m = st.Pop();
                if (!m.Expanded) { unknown = true; continue; }
                foreach (var id in m.Next)
                {
                    var k = Nodes[id];
                    if (k.Mode != Mode.Talk || k.Npc != n.Npc) { exit = true; break; }
                    if (seen.Add(id)) st.Push(k);
                }
            }
            if (exit || unknown || seen.Count >= 2000) continue;
            at = n; doing = null; root = n.Root;
            Report("deadend", $"{n.Npc}.{n.At}:loop", $"Talking to {n.Npc}, from {n.At} every choice comes back round and none leaves", "data/content/dialogue.json");
        }
    }

    /// <summary>Gates of respect and affection shown and never opened. Where
    /// the content cannot add up to the gate on any road (every way of
    /// earning it once-only, and all of them together short), the gate can
    /// never be met; where it could and nothing explored did, it is only
    /// unseen (said in the report, not failed).</summary>
    void Gates()
    {
        foreach (var (key, g) in Seen.Gates.Where(g => !g.Value.Opened))
        {
            var unmet = g.Needs.Where(nd => !nd.Met(Seen.Best(nd.Npc, nd.Axis))).ToList();
            if (unmet.Count == 0) continue;
            var never = unmet.Where(nd => !nd.Met(Most.Of(nd.Npc, nd.Axis))).ToList();
            at = g.First; doing = g.Doing; root = g.First.Root;
            if (never.Count > 0)
                Report("gate", key, $"\"{g.Text}\" asks {string.Join(", ", never.Select(nd => $"{nd.Npc} {nd.Axis.ToString().ToLowerInvariant()} {nd.Op} {nd.Value}"))}, " +
                    $"and everything in the story that raises it adds up to {string.Join(", ", never.Select(nd => Most.Of(nd.Npc, nd.Axis)))}", "data/content/dialogue.json");
            else
                Report("unseen", key, $"\"{g.Text}\" asks {string.Join(", ", unmet.Select(nd => $"{nd.Npc} {nd.Axis.ToString().ToLowerInvariant()} {nd.Op} {nd.Value} (best seen {Seen.Best(nd.Npc, nd.Axis)})"))}, and no road explored got there", "data/content/dialogue.json");
        }
    }

    /* ------------------------------------------------------------- items -- */

    /// <summary>What a story asks the survivor to have: read from every
    /// condition and change in the content, and from the zone scripts.</summary>
    public static (HashSet<string> Items, HashSet<string> Tags, HashSet<string> Traits) StoryThings()
    {
        var items = new HashSet<string>();
        var tags = new HashSet<string>();
        var traits = new HashSet<string>();
        void C(Cond? c)
        {
            if (c == null) return;
            if (c.HasItem != null) items.Add(c.HasItem);
            if (c.HasTag != null) tags.Add(c.HasTag);
            if (c.Trait != null) traits.Add(c.Trait);
            foreach (var x in c.All ?? new()) C(x);
            foreach (var x in c.Any ?? new()) C(x);
            C(c.Not);
        }
        void E(IEnumerable<Change>? es)
        {
            foreach (var e in es ?? Enumerable.Empty<Change>())
            {
                if (e.Take != null) items.Add(e.Take);
                if (e.Give != null) items.Add(e.Give);
                C(e.If); E(e.Then); E(e.Else);
                if (e.Later != null) E(e.Later.Effect);
            }
        }
        foreach (var c in Dialogue.All.Values)
        {
            foreach (var en in c.Entry) C(en.When);
            foreach (var n in c.Nodes.Values)
            {
                E(n.Effects);
                foreach (var v in n.Text) C(v.When);
                foreach (var ch in n.Choices ?? new()) { C(ch.Show); C(ch.When); E(ch.Effects); foreach (var v in ch.Text) C(v.When); }
            }
        }
        foreach (var r in Simulation.DailyRules) { C(r.When); E(r.Effect); }
        foreach (var s in Lore.Shops.Values) foreach (var l in s.Lines) C(l.When);
        var logic = Path.GetFullPath(Path.Combine(DataFiles.Dir, "..", "logic"));
        foreach (var f in Directory.EnumerateFiles(logic, "*.cs", SearchOption.AllDirectories))
        {
            var t = File.ReadAllText(f);
            foreach (Match m in Regex.Matches(t, @"(?:HasItem\(|""hasItem""\s*:\s*|""take""\s*:\s*|""give""\s*:\s*)""(\w+)""")) items.Add(m.Groups[1].Value);
            foreach (Match m in Regex.Matches(t, @"""hasTag""\s*:\s*""(\w+)""")) tags.Add(m.Groups[1].Value);
            foreach (Match m in Regex.Matches(t, @"(?:""trait""\s*:\s*|Traits\.Contains\()""(\w+)""")) traits.Add(m.Groups[1].Value);
        }
        foreach (var d in Items.All.Values)
            if (d.Kind == ItemKind.Quest || (d.Tags?.Any(tags.Contains) ?? false)) items.Add(d.Id);
        foreach (var t in Callings.Traits.Values)
            if (t.Tags?.Any(tags.Contains) ?? false) traits.Add(t.Id);
        items.RemoveWhere(i => Items.Find(i) == null);
        return (items, tags, traits);
    }
}

/// <summary>What the explorer reached against what there is, and what it
/// found, as Markdown for docs/cloud/story-explorer.md.</summary>
static class Reporting
{
    /// <summary>Every fact = value a condition in the content compares against.</summary>
    public static HashSet<string> Asked()
    {
        var set = new HashSet<string>();
        void C(Cond? c)
        {
            if (c == null) return;
            if (c.FactKey != null && c.Eq is { } eq && eq.Type is Fact.Kind.Str or Fact.Kind.Bool) set.Add($"{c.FactKey}={eq}");
            foreach (var x in c.All ?? new()) C(x);
            foreach (var x in c.Any ?? new()) C(x);
            C(c.Not);
        }
        void E(IEnumerable<Change>? es) { foreach (var e in es ?? Enumerable.Empty<Change>()) { C(e.If); E(e.Then); E(e.Else); } }
        foreach (var c in Dialogue.All.Values)
        {
            foreach (var en in c.Entry) C(en.When);
            foreach (var n in c.Nodes.Values)
            {
                E(n.Effects);
                foreach (var v in n.Text) C(v.When);
                foreach (var ch in n.Choices ?? new()) { C(ch.Show); C(ch.When); E(ch.Effects); foreach (var v in ch.Text) C(v.When); }
            }
        }
        foreach (var r in Simulation.DailyRules) { C(r.When); E(r.Effect); }
        return set;
    }

    public sealed record Line(string What, int Reached, int Of, List<string> Missing);

    public static List<Line> Lines(StoryExplorer x)
    {
        var s = x.Seen;
        Line L(string what, IEnumerable<string> all, Func<string, bool> reached)
        {
            var list = all.Distinct().OrderBy(k => k, StringComparer.Ordinal).ToList();
            var miss = list.Where(k => !reached(k)).ToList();
            return new Line(what, list.Count - miss.Count, list.Count, miss);
        }
        var nodes = Dialogue.All.SelectMany(c => c.Value.Nodes.Keys.Select(n => $"{c.Key}.{n}"));
        var choices = Dialogue.All.SelectMany(c => c.Value.Nodes.SelectMany(n => (n.Value.Choices ?? new()).Select((_, i) => $"{c.Key}.{n.Key}#{i}")));
        var entries = Lore.Quests.SelectMany(q => q.Value.Entries.Keys.Select(e => $"{q.Key}/{e}"));
        var endings = Lore.Quests.SelectMany(q => (q.Value.Outcomes ?? new()).Keys.Select(o => $"{q.Key}:{o}"));
        var values = s.Of("value");
        bool Ending(string k)
        {
            var (q, o) = (k[..k.IndexOf(':')], k[(k.IndexOf(':') + 1)..]);
            return s.Of("outcome").Contains(k) || values.Any(v => v.StartsWith(q + ".") && v.EndsWith("=" + o));
        }
        return
        [
            L("Conversations started", Dialogue.All.Keys, s.Of("talk").Contains),
            L("Dialogue nodes reached", nodes, s.Of("node").Contains),
            L("Choices taken", choices, s.Of("said").Contains),
            L("Journal lines written", entries, s.Of("entry").Contains),
            L("Quest endings reached", endings, Ending),
            L("Quests resolved", Lore.Quests.Keys.Select(q => $"{q}:Resolved"), s.Of("status").Contains),
            L("Fact values the story asks about, seen", Asked(), values.Contains),
            L("Story items held", Playthrough.StoryItems, s.Of("item").Contains),
        ];
    }

    public static string Markdown(StoryExplorer x, Func<Finding, string?> accepted)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"States reached: {x.Nodes.Count:N0} ({x.Expanded:N0} expanded, deepest {x.Nodes.Max(n => n.Depth)} steps), " +
            $"over {x.O.Roots.Count} survivors, in {x.Clock.Elapsed.TotalSeconds:0} s.");
        sb.AppendLine();
        sb.AppendLine("| Reached | of | |");
        sb.AppendLine("|---:|---:|---|");
        var lines = Lines(x);
        foreach (var l in lines) sb.AppendLine($"| {l.Reached} | {l.Of} | {l.What} |");
        sb.AppendLine();
        foreach (var l in lines.Where(l => l.Missing.Count > 0))
        {
            sb.AppendLine($"<details><summary>{l.What}: not reached ({l.Missing.Count})</summary>");
            sb.AppendLine();
            sb.AppendLine(string.Join(", ", l.Missing.Select(m => $"`{m}`")));
            sb.AppendLine();
            sb.AppendLine("</details>");
            sb.AppendLine();
        }
        var locked = x.Seen.Locked.Keys.Where(k => k.Contains('#') && !x.Seen.Open.Contains(k)).OrderBy(k => k, StringComparer.Ordinal).ToList();
        if (locked.Count > 0)
        {
            sb.AppendLine($"<details><summary>Choices shown locked and never opened ({locked.Count})</summary>");
            sb.AppendLine();
            foreach (var k in locked) sb.AppendLine($"- `{k}`: {x.Seen.Locked[k]}");
            sb.AppendLine();
            sb.AppendLine("</details>");
            sb.AppendLine();
        }
        sb.AppendLine("### Findings");
        sb.AppendLine();
        if (x.Findings.Count == 0) sb.AppendLine("None.");
        foreach (var f in x.Findings.Values.OrderBy(f => f.Kind).ThenBy(f => f.Key, StringComparer.Ordinal))
        {
            var why = accepted(f);
            sb.AppendLine($"#### `{f.Key}`{(why != null ? " (accepted)" : "")}");
            sb.AppendLine();
            sb.AppendLine($"{f.Text}. File: `{f.File}`. Survivor: {f.Root}.{(why != null ? $" Accepted: {why}" : "")}");
            sb.AppendLine();
            sb.AppendLine("<details><summary>Replay</summary>");
            sb.AppendLine();
            sb.AppendLine("```");
            sb.AppendLine(f.Replay);
            sb.AppendLine("```");
            sb.AppendLine();
            sb.AppendLine("</details>");
            sb.AppendLine();
        }
        return sb.ToString();
    }
}
