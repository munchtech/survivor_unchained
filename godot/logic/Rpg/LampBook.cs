using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Rpg;

/// <summary>One way of lighting the board, a whole build: the type (the road given at creation), the lamps lit,
/// the Flare, the wicks, the links' picks and the skills carried by day. A survivor keeps three
/// (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.5).</summary>
public sealed class LampLayout
{
    public string Type = "";
    public List<string> Lit = new();
    public string Flare = "";
    /// <summary>Each skill's wick plan (Rpg/WickBook.cs): its lamp ids in the order they light. A layout holds
    /// its wicks, so swapping layouts swaps builds (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.5).</summary>
    public Dictionary<string, List<string>> Wicks = new();
    /// <summary>Lamps v2: each link's pick, its lamp id to the skill it fires (docs/design/LAMPS_V2_RULES.md "Links").
    /// No pick, or one not carried: Light my way's (Battle.LinkSkill).</summary>
    public Dictionary<string, string> Links = new();
    /// <summary>The day slots' skills, in order. The active layout's live copy is the character's Slotted
    /// (what everything reads); it is kept here on a switch and on a save (LampBook.Keep).</summary>
    public List<string> Carried = new();
}

public sealed class LampState
{
    public const int Count = 3;
    public List<LampLayout> Layouts = new() { new(), new(), new() };
    public int Active;
    /// <summary>Light my way: the suggested lamp is lit for you every level (§2.5).</summary>
    public bool LightMyWay;
    public LampLayout Now => Layouts[Math.Clamp(Active, 0, Layouts.Count - 1)];
}

/// <summary>A dim lamp's reason (LampBook.Sleeps): any one of these skills (ids) or tags, carried, wakes it.</summary>
public sealed record LampSleep(string[] Skills, string[] Tags);

/// <summary>Why a lamp can't be lit or put out (None: it can).</summary>
public enum LampNo { None, Unknown, Lit, Unlit, NoLamps, NotHome, Dark, Gate, Free, Holds }

/* The lamps a survivor has lit (docs/design/CLASSES.md §2.4-2.5).
 *
 * Lamps come from levels (one a level from 2 to 30), the story's bosses
 * (one each, the first win), the atlas (a tier's first clear; eight on v1,
 * thirty on v2) and, on v2, the dark lamp-posts relit. Three are free: the
 * hearth's first lamp, and the chosen type's entry and Strike.
 *
 * A lamp is lit next to a lit one, past its road's depth gate. Lamps go out
 * free, by day, at a town's lamp-post (the caller asks Journey.LampsOpen):
 * one at a time while what's left still hangs together, or all at once.
 * Changing the type puts every lamp out. */
public static class LampBook
{
    /// <summary>The atlas's lamps at most: 8 on v1, 30 on v2 (CLASS_IDENTITY_AND_TALENTS.md 3.2 "Points").</summary>
    public static int AtlasLamps => Lamps.V2 ? 30 : 8;

    public static LampState State(CharacterData ch)
    {
        if (ch.Lamps != null) return ch.Lamps;
        Begin(ch, null);
        return ch.Lamps!;
    }

    /// <summary>The board as creation leaves it: the chosen type (one of the calling's roads; anything
    /// else walks the default) lit on every layout, so switching layouts never drops the pick.</summary>
    public static void Begin(CharacterData ch, string? type)
    {
        if (type == null || !Lamps.Roads.TryGetValue(type, out var r) || r.Calling != ch.Archetype) type = DefaultType(ch.Archetype);
        ch.Lamps = new LampState();
        foreach (var l in ch.Lamps.Layouts) { Reset(ch, l, type); l.Carried = ch.Slotted.ToList(); }
    }

    /// <summary>Every layout carries what she carries now (creation: the three start equal).</summary>
    public static void CarryOnAll(CharacterData ch)
    {
        foreach (var l in State(ch).Layouts) l.Carried = ch.Slotted.ToList();
    }

    /// <summary>The active layout keeps the skills she carries now (a switch and a save call it).</summary>
    public static void Keep(CharacterData ch) => Now(ch).Carried = ch.Slotted.ToList();

    public static LampLayout Now(CharacterData ch) => State(ch).Now;

    /// <summary>A calling's first road: the type a survivor who never chose one walks.</summary>
    public static string DefaultType(string calling) => Lamps.RoadsOf(calling).First().Id;

    /// <summary>Lamps earned: levels, the story's bosses beaten, the atlas's milestones, and (v2) the lamp-posts relit.</summary>
    public static int Earned(CharacterData ch, WorldState? w) => Math.Max(0, ch.Level - 1) + StoryLamps(w) + AtlasLit(w) + PostLamps(w);

    /// <summary>Lamps v2: the dark lamp-posts relit (lamps_v2.json "posts", four an act), a lamp each.</summary>
    public static int PostLamps(WorldState? w) => w == null || !Lamps.V2 ? 0 : Lamps.Posts.Count(p => w.Fact(PostFact(p.Id)).Truthy);

    static string PostFact(string post) => $"lampposts.{post}";

    /// <summary>Whether a lamp-post burns: relit or lit by her (a world fact: never a zone's state, so never reset), or a
    /// town's post (lit from the start). Any post of lamp_posts.json; a board post only counts for the board on v2.</summary>
    public static bool PostLit(WorldState? w, string postId) => w != null && (w.Fact(PostFact(postId)).Truthy || LampPosts.Get(postId)?.Town == true);

    static string LastFact(string zone) => $"lamppost_last.{zone}";

    /// <summary>She lights a lamp-post (lamp_posts.json) where she stands: a checkpoint is lit for good (a world fact, no
    /// board point), a dark post is relit (RelightPost: its board point, on v2 only); either becomes her last post in its
    /// zone, where she rises. True the first time it is lit by her.</summary>
    public static bool LightPost(WorldState w, string postId)
    {
        if (LampPosts.Get(postId) is not { } p) return false;
        bool first;
        if (p.Dark) first = RelightPost(w, postId);
        else
        {
            first = !p.Town && !w.Fact(PostFact(postId)).Truthy;
            if (first) w.Facts[PostFact(postId)] = true;
        }
        if (PostLit(w, postId)) w.Facts[LastFact(p.Zone)] = postId;
        return first;
    }

    /// <summary>The last lamp-post she lit in a zone, while it burns (where she rises there), or null.</summary>
    public static LampPosts.Post? LastPost(WorldState? w, string zone) =>
        w != null && w.Fact(LastFact(zone)) is { Truthy: true } f && LampPosts.Get(f.Str ?? "") is { } p && p.Zone == zone && PostLit(w, p.Id) ? p : null;

    /// <summary>Her last post in a zone set (or forgotten: null), as a part of the zone she has walked past is left behind.</summary>
    public static void SetLastPost(WorldState w, string zone, string? postId)
    {
        if (postId == null) w.Facts.Remove(LastFact(zone));
        else w.Facts[LastFact(zone)] = postId;
    }

    /// <summary>Lamps v2: a dark lamp-post is relit (where it stands is the zone's). True the first time; false if it
    /// was lit already, or isn't one of the board's posts (none on v1).</summary>
    public static bool RelightPost(WorldState w, string postId)
    {
        if (!Lamps.V2 || Lamps.Post(postId) == null || w.Fact(PostFact(postId)).Truthy) return false;
        w.Facts[PostFact(postId)] = true;
        return true;
    }

    public static int StoryLamps(WorldState? w) => w == null ? 0 : Lamps.StoryFights.Count(id => w.Fact($"arena.{id}").Str == "won");

    /// <summary>The atlas's lamps (its milestones grow the fact: Maps.Atlas.Complete), AtlasLamps at most.</summary>
    public static int AtlasLit(WorldState? w) => w == null ? 0 : Math.Clamp((int)w.Fact("lamps.atlas").Number, 0, AtlasLamps);

    /// <summary>The lamps that cost nothing: the hearth's first, the type's entry and its Strike.</summary>
    public static HashSet<string> Free(CharacterData ch, LampLayout? l = null)
    {
        l ??= Now(ch);
        var o = new HashSet<string> { Lamps.Start(ch.Archetype) };
        if (Lamps.Roads.TryGetValue(l.Type, out var road))
        {
            o.Add(Lamps.Entry(road.Id));
            if (Lamps.FlareLamp(road.Strike) is { } s) o.Add(s);
        }
        return o;
    }

    public static int Spent(CharacterData ch) { var free = Free(ch); return Now(ch).Lit.Count(id => !free.Contains(id)); }

    public static int Spare(CharacterData ch, WorldState? w) => Earned(ch, w) - Spent(ch);

    public static bool IsLit(CharacterData ch, string id) => Now(ch).Lit.Contains(id);

    /// <summary>Lamps lit on a road (the free Strike counts): what its depth gates read.</summary>
    public static int Depth(CharacterData ch, string road) => Depth(Now(ch).Lit, road);

    static int Depth(IEnumerable<string> lit, string road) => lit.Count(id => Lamps.Find(id)?.Road == road);

    public static LampNo CanLight(CharacterData ch, WorldState? w, string id)
    {
        var why = Check(ch, Now(ch).Lit, id);
        if (why != LampNo.None) return why;
        if (Spare(ch, w) <= 0) return LampNo.NoLamps;
        return LampNo.None;
    }

    /// <summary>CanLight's rules on any lit list, the count of spare lamps aside (PathTo and Suggested walk copies).</summary>
    static LampNo Check(CharacterData ch, List<string> lit, string id) =>
        Check(ch, lit.Contains, road => Depth(lit, road), lit.Any(Unhouses), id);

    /// <summary>The rules themselves, on any lit set: is it lit, a road's depth, and is an Unhoused blue lit.</summary>
    static LampNo Check(CharacterData ch, Func<string, bool> isLit, Func<string, int> depth, bool unhoused, string id)
    {
        if (Lamps.Find(id) is not { } def) return LampNo.Unknown;
        if (isLit(id)) return LampNo.Lit;
        if (def.Home && def.Calling != ch.Archetype) return LampNo.NotHome;
        if (!Lamps.Next(id).Any(isLit)) return LampNo.Dark;
        if (def.Road != null && depth(def.Road) < def.Gate && !Ungated(ch, unhoused, def)) return LampNo.Gate;
        return LampNo.None;
    }

    /// <summary>The Lamps screen's far lamp (LAMPS_SCREEN_BRIEF.md §14.3): the unlit lamps to light, in lighting order, each
    /// lightable (CanLight's rules) after those before it; the fewest the roads allow, gates and home honored. Empty when it
    /// is lit, unknown or can't be reached. The spare lamps are not counted (LightPath does).</summary>
    public static IReadOnlyList<string> PathTo(CharacterData ch, WorldState? w, string id)
    {
        var now = Now(ch).Lit;
        if (Lamps.Find(id) is not { } goal || now.Contains(id) || (goal.Home && goal.Calling != ch.Archetype)) return [];
        var s = now.ToList();
        int start = s.Count;
        // Each round lights the shortest chain to the goal that its own lamps open; failing that, the nearest lamp on
        // the road whose gate shuts the way (its depth grows a lamp a round), until the goal is in reach.
        for (int guard = Lamps.All.Count; guard-- > 0;)
        {
            if (Chain(ch, s, x => x == id) is { } c) { s.AddRange(c); return s.Skip(start).ToList(); }
            // The first gate on the open way (gates and Unhoused aside): which road needs more lamps lit.
            if (Chain(ch, s, x => x == id, gates: false) is not { } way) return [];
            var t = s.ToList();
            string? road = null;
            foreach (var x in way)
            {
                if (Check(ch, t, x) == LampNo.Gate) { road = Lamps.Get(x).Road; break; }
                t.Add(x);
            }
            if (road == null || Chain(ch, s, x => Lamps.Find(x)?.Road == road) is not { } more) return [];
            s.AddRange(more);
        }
        return [];
    }

    /// <summary>The shortest run of unlit lamps from the lit list to one that matches, each lightable after the ones
    /// before it (gates: false, only joined and home), in order; null when none is reached.</summary>
    static List<string>? Chain(CharacterData ch, List<string> lit, Func<string, bool> goal, bool gates = true)
    {
        var from = new Dictionary<string, string?>();
        var q = new Queue<string>();
        var litSet = lit.ToHashSet();
        var depth = new Dictionary<string, int>();
        foreach (var x in lit) if (Lamps.Find(x)?.Road is { } r) depth[r] = depth.GetValueOrDefault(r) + 1;
        bool unhoused = lit.Any(Unhouses);
        List<string> Run(string? c) { var r = new List<string>(); for (; c != null; c = from[c]) r.Add(c); r.Reverse(); return r; }
        bool Ok(string n, string? via)
        {
            if (litSet.Contains(n) || from.ContainsKey(n)) return false;
            if (!gates) return Lamps.Find(n) is { } d && !(d.Home && d.Calling != ch.Archetype);
            // CanLight's rules on the lit list plus the run to `via`.
            bool OnRun(string x) { for (string? c = via; c != null; c = from[c]) if (c == x) return true; return false; }
            int Deep(string road) { int k = depth.GetValueOrDefault(road); for (string? c = via; c != null; c = from[c]) if (Lamps.Find(c)?.Road == road) k++; return k; }
            bool un = unhoused;
            for (string? c = via; c != null && !un; c = from[c]) un = Unhouses(c);
            return Check(ch, x => litSet.Contains(x) || OnRun(x), Deep, un, n) == LampNo.None;
        }
        foreach (var l in lit) foreach (var n in Lamps.Next(l)) if (Ok(n, null)) { from[n] = null; q.Enqueue(n); }
        while (q.Count > 0)
        {
            var c = q.Dequeue();
            if (goal(c)) return Run(c);
            foreach (var n in Lamps.Next(c)) if (Ok(n, c)) { from[n] = c; q.Enqueue(n); }
        }
        return null;
    }

    /// <summary>§14.3: light PathTo's lamps, all or none (a refusal puts every lamp it lit out again, the Flare as it was).</summary>
    public static bool LightPath(CharacterData ch, WorldState? w, string id)
    {
        var p = PathTo(ch, w, id);
        if (p.Count == 0 || p.Count > Spare(ch, w)) return false;
        var l = Now(ch);
        var keep = l.Lit.ToList();
        var flare = l.Flare;
        foreach (var x in p)
            if (!Light(ch, w, x)) { l.Lit.Clear(); l.Lit.AddRange(keep); l.Flare = flare; return false; }
        return true;
    }

    public static bool Light(CharacterData ch, WorldState? w, string id)
    {
        if (CanLight(ch, w, id) != LampNo.None) return false;
        Now(ch).Lit.Add(id);
        return true;
    }

    /// <summary>Can it go out (the caller has checked the place)? Not a free lamp, and what stays lit
    /// must still hang together from the hearth and meet its gates.</summary>
    public static LampNo CanUnlight(CharacterData ch, string id)
    {
        var l = Now(ch);
        if (!l.Lit.Contains(id)) return LampNo.Unlit;
        if (Free(ch).Contains(id)) return LampNo.Free;
        var rest = l.Lit.Where(x => x != id).ToList();
        return Holds(ch, rest) ? LampNo.None : LampNo.Holds;
    }

    public static bool Unlight(CharacterData ch, string id)
    {
        if (CanUnlight(ch, id) != LampNo.None) return false;
        var l = Now(ch);
        l.Lit.Remove(id);
        if (!Learned(ch).Contains(l.Flare)) l.Flare = Lamps.Road(l.Type).Strike;
        return true;
    }

    /// <summary>Every lamp out but the free ones.</summary>
    public static void Clear(CharacterData ch) => Reset(ch, Now(ch), Now(ch).Type);

    /// <summary>Walk another of the calling's roads: every lamp goes out, and the new type's are lit.</summary>
    public static bool SetType(CharacterData ch, string road)
    {
        if (!Lamps.Roads.TryGetValue(road, out var r) || r.Calling != ch.Archetype) return false;
        Reset(ch, Now(ch), road);
        return true;
    }

    /// <summary>The towns, where layouts change (Act 1 has one).</summary>
    public static readonly HashSet<string> Towns = new() { "waystation" };

    /// <summary>The lit lamp-post she stands at out of a fight, for a world, or null (the post menu sets it as it opens the
    /// Lamps there: it says so only while she is still at the post and calm). Never saved.</summary>
    public static Func<WorldState, string?>? Bench;

    /// <summary>Can layouts change here and now (the respec bench, ARPG.md 3.5)? In a town, not by night; or at a lit lamp-post
    /// she stands at out of a fight (Bench); never mid-map or mid-arena.</summary>
    public static bool LayoutsOpen(WorldState? w, string? zone) => LayoutsOpen(w, zone, w == null ? null : Bench?.Invoke(w));

    /// <summary>LayoutsOpen, with the lit post she stands at out of a fight (or null) given.</summary>
    public static bool LayoutsOpen(WorldState? w, string? zone, string? atPost) =>
        w != null && zone != null && w.Map == null && w.Arena == null
        && (Towns.Contains(zone) && w.Time != TimeOfDay.Night || atPost != null && LampPosts.Get(atPost)?.Zone == zone && PostLit(w, atPost));

    /// <summary>Take up another saved layout, the whole build: the board, the wicks, the links, the Flare and the
    /// skills carried (the one left keeps what she carried). Only where LayoutsOpen.</summary>
    public static bool Switch(CharacterData ch, int index, WorldState? w, string? zone)
    {
        var s = State(ch);
        if (index < 0 || index >= s.Layouts.Count || !LayoutsOpen(w, zone)) return false;
        Keep(ch);
        s.Active = index;
        if (s.Now.Type == "") Reset(ch, s.Now, DefaultType(ch.Archetype));
        s.Now.Carried ??= new();
        ch.Slotted = s.Now.Carried.Where(id => SkillBook.Knows(ch, id) && SkillBook.Carries(ch, id)).Distinct().Take(SkillBook.Slots(ch)).ToList();
        return true;
    }

    /// <summary>Save v6 (from v5): three layouts, each refunded to its free lamps with no wick plans (Light my way's
    /// strands) and no link picks; skills her calling can no longer carry go to the storeroom as tomes; and the
    /// skills she carries are copied into each layout.</summary>
    public static void MigrateSix(CharacterData ch, WorldState w)
    {
        var s = State(ch);
        while (s.Layouts.Count < LampState.Count) s.Layouts.Add(new());
        if (s.Layouts.Count > LampState.Count) s.Layouts.RemoveRange(LampState.Count, s.Layouts.Count - LampState.Count);
        s.Active = Math.Clamp(s.Active, 0, LampState.Count - 1);
        foreach (var id in ch.Skills.Where(id => !SkillBook.Carries(ch, id)).ToList())
        {
            ch.Skills.Remove(id);
            ch.Slotted.Remove(id);
            if (Items.Find(SkillBook.Tome(id)) == null) continue;
            var tome = Inventory.Make(ch, SkillBook.Tome(id), 1);
            int at = w.Stash.IndexOf(null);
            if (at < 0) { at = w.Stash.Count; for (int i = 0; i < WorldState.Shelf; i++) w.Stash.Add(null); }
            w.Stash[at] = tome;
        }
        foreach (var l in s.Layouts)
        {
            var type = Lamps.Roads.TryGetValue(l.Type ?? "", out var r) && r.Calling == ch.Archetype ? l.Type! : DefaultType(ch.Archetype);
            Reset(ch, l, type);
            l.Wicks = new();
            l.Links = new();
            l.Carried = ch.Slotted.ToList();
        }
    }

    static void Reset(CharacterData ch, LampLayout l, string type)
    {
        l.Type = type;
        l.Lit = Free(ch, l).ToList();
        l.Flare = Lamps.Road(type).Strike;
    }

    /// <summary>Does this set of lamps hang together (every lamp reached from the hearth through lit
    /// lamps) and meet every gate?</summary>
    static bool Holds(CharacterData ch, List<string> lit)
    {
        var set = lit.ToHashSet();
        var seen = new HashSet<string>();
        var q = new Queue<string>(Free(ch).Where(set.Contains));
        foreach (var f in q) seen.Add(f);
        while (q.Count > 0)
            foreach (var n in Lamps.Next(q.Dequeue()))
                if (set.Contains(n) && seen.Add(n)) q.Enqueue(n);
        if (seen.Count != set.Count) return false;
        var free = Free(ch);
        return lit.All(id => free.Contains(id) || Lamps.Get(id) is var d && (d.Road == null || Depth(lit, d.Road) >= d.Gate || Ungated(ch, lit, d)));
    }

    /// <summary>blue.unhoused (the Ford's blue, v2): lamps on other callings' roads open with no depth.</summary>
    static bool Ungated(CharacterData ch, List<string> lit, LampDef d) => Ungated(ch, lit.Any(Unhouses), d);

    static bool Ungated(CharacterData ch, bool unhoused, LampDef d) =>
        Lamps.V2 && d.Calling != null && d.Calling != ch.Archetype && unhoused;

    static bool Unhouses(string id) => Lamps.Find(id) is { } d && d.Effects.Any(e => e.Rule == "blue.unhoused" && e.Phase <= Lamps.LivePhase);

    /// <summary>Lamps v2 on: the lit ids a save holds that the v2 board lacks are dropped (and links on them), the
    /// free lamps lit again, and a type v2 lacks walks the default.</summary>
    public static void DropUnknown(CharacterData ch)
    {
        if (ch.Lamps == null) return;
        foreach (var l in ch.Lamps.Layouts)
        {
            if (l.Type == "") continue;
            if (!Lamps.Roads.TryGetValue(l.Type, out var r) || r.Calling != ch.Archetype) { Reset(ch, l, DefaultType(ch.Archetype)); continue; }
            l.Lit.RemoveAll(id => Lamps.Find(id) == null);
            foreach (var f in Free(ch, l)) if (!l.Lit.Contains(f)) l.Lit.Add(f);
            l.Links ??= new();
            foreach (var k in l.Links.Keys.ToList()) if (Lamps.Find(k) == null) l.Links.Remove(k);
            if (Lamps.Flare(l.Flare) == null) l.Flare = Lamps.Road(l.Type).Strike;
        }
    }

    /* ------------------------------------------------------- the Flare -- */

    /// <summary>The Flares the lit lamps have learned (the calling's own only).</summary>
    public static List<string> Learned(CharacterData ch) =>
        Now(ch).Lit.Select(Lamps.Find).Where(d => d != null && d.Kind == LampKind.Ultimate && d.Calling == ch.Archetype)
            .SelectMany(d => d!.Effects.Where(e => e.Do == LampDo.Flare).Select(e => e.Flare!)).ToList();

    /// <summary>The Flare carried: chosen by day, or at a night's start before the first draft.</summary>
    public static string Carried(CharacterData ch)
    {
        var l = Now(ch);
        var learned = Learned(ch);
        return learned.Contains(l.Flare) ? l.Flare : learned.FirstOrDefault() ?? "";
    }

    public static bool Carry(CharacterData ch, string flare)
    {
        if (!Learned(ch).Contains(flare)) return false;
        Now(ch).Flare = flare;
        return true;
    }

    /* --------------------------------------------------- light my way -- */

    /// <summary>The lamp the board suggests next (§2.5): along the survivor's own road first, what
    /// changes most for what they carry. Null when none can be lit.</summary>
    public static string? Suggest(CharacterData ch, WorldState? w) => Suggest(ch, w, Now(ch).Lit, Spare(ch, w));

    static string? Suggest(CharacterData ch, WorldState? w, List<string> lit, int spare)
    {
        if (spare <= 0) return null;
        var l = Now(ch);
        var carried = SkillBook.Carried(ch).Select(s => s.Id).ToHashSet();
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s] is { } it && Items.Find(it.Def)?.Weapon is { } wd) carried.Add(wd.Id);
        string? best = null;
        double bestScore = double.MinValue;
        foreach (var id in lit.SelectMany(Lamps.Next).Distinct())
        {
            if (Check(ch, lit, id) != LampNo.None) continue;
            var d = Lamps.Get(id);
            // Banked Flame is a choice, never a suggestion: it pays only to a hand that holds a charge back, and
            // spent as it fills it is a trap (the owner, 12 October: Light my way never lights it).
            if (d.Effects.Any(e => e.Rule == "flare.banked")) continue;
            // Before Act 1 is done it lights only the modifier marked early: the strong ones stay a hand's choice (§7).
            if (d.Kind == LampKind.UltimateMod && !d.Early && w != null && !w.Fact("chapter.done").Truthy) continue;
            double sc = d.Road == l.Type ? 100 : d.Region == LampRegion.Hearth ? 60 : 0;
            sc += d.Kind switch
            {
                LampKind.Ultimate => 40, LampKind.Reflex => 35, LampKind.Notable => 30, LampKind.Blue => 5,
                LampKind.Form or LampKind.ReflexUp or LampKind.FlareLamp => 20, LampKind.UltimateMod => 18,
                LampKind.Skill => d.Feeds.Any(carried.Contains) ? 32 : 2, _ => 10,
            };
            // Nothing live yet is no gift (a later phase's lamp).
            if (d.Effects.Length > 0 && d.Effects.All(e => e.Phase > Lamps.LivePhase)) sc -= 50;
            // Deterministic: ties go to the board's order.
            if (sc > bestScore) { bestScore = sc; best = id; }
        }
        return best;
    }

    /// <summary>Light my way: the suggested lamps, while there are lamps to light.</summary>
    public static int LightSuggested(CharacterData ch, WorldState? w)
    {
        int n = 0;
        while (Suggest(ch, w) is { } id && Light(ch, w, id)) n++;
        return n;
    }

    /// <summary>§14.6: the next n lamps Light my way would light, in order, lighting none (it walks a copy of the lit list).</summary>
    public static IReadOnlyList<string> Suggested(CharacterData ch, WorldState? w, int n)
    {
        var lit = Now(ch).Lit.ToList();
        int spare = Spare(ch, w);
        var got = new List<string>();
        while (got.Count < n && Suggest(ch, w, lit, spare) is { } s) { got.Add(s); lit.Add(s); spare--; }
        return got;
    }

    /* --------------------------------------------- what wakes a lamp -- */

    /// <summary>§14.4: why a lamp is dim (lit: asleep), by the sim's own rule. Null when it works on what she fights with
    /// by day (Character.DaySkills, each as WickBook.Weapon builds it): a lamp with any effect on every skill, a link while
    /// she carries anything (BoardRules.LinkPick sleeps only on nothing), or a skill or tag effect that covers one of them
    /// (LampLoadout.Covers, the rule the v2 rites and tags rules read). Null too when it names nothing (no live effect).
    /// Otherwise the skills (ids) and tags any one of which, carried, would wake it.</summary>
    public static LampSleep? Sleeps(CharacterData ch, string id)
    {
        if (Lamps.Find(id) is not { } d) return null;
        var live = d.Effects.Where(e => e.Phase <= Lamps.LivePhase).ToList();
        if (live.Count == 0) return null;
        bool link = live.Any(e => e.Rule == "link");
        var scoped = live.Where(e => e.Rule != "link").ToList();
        if (!link && scoped.Any(e => e.Skill == null && e.Tags == null)) return null;
        var day = DayWeapons(ch);
        if (link ? day.Count > 0 : day.Any(w => scoped.Any(e => LampLoadout.Covers(e, w.Def.Id, w.Tags)))) return null;
        bool Wakes(string skill)
        {
            if (!Weapons.All.ContainsKey(skill) || !SkillBook.Carries(ch, skill)) return false;
            if (link) return true;
            var w = WickBook.Weapon(ch, skill, SkillBook.Rank(ch));
            return scoped.Any(e => LampLoadout.Covers(e, w.Def.Id, w.Tags));
        }
        var names = scoped.Where(e => e.Skill != null).Select(e => e.Skill!).Concat(d.Feeds).Where(Wakes).Distinct().ToList();
        if (names.Count == 0) names = ch.Skills.Where(Wakes).Distinct().ToList();
        if (names.Count == 0) names = Weapons.All.Values.Where(x => x.Findable).Select(x => x.Id).Where(Wakes).ToList();
        string[] tags = link ? [] : scoped.Where(e => e.Tags != null).SelectMany(e => e.Tags!).Distinct().Select(t => t.ToString().ToLowerInvariant()).ToArray();
        return new LampSleep(names.ToArray(), tags);
    }

    /// <summary>What she fights with by day, as the fight builds each (its rank, its lit wick).</summary>
    static List<WeaponInst> DayWeapons(CharacterData ch) =>
        Character.DaySkills(ch).Select(x => WickBook.Weapon(ch, x.Id, x.Rank)).ToList();

    /* ------------------------------------------------------- links -- */

    /// <summary>The link lamp's rule (its trigger, wait and hint tags), or null when it is no live link.</summary>
    static LampEffect? LinkRule(string link) =>
        Lamps.Find(link)?.Effects.FirstOrDefault(e => e.Rule == "link" && e.Phase <= Lamps.LivePhase);

    /// <summary>§14.5: the skill the link fires by day: her pick if she carries it, else Light my way's (the most tags
    /// shared with the link's: Battle.LinkPick, the rule Battle.LinkSkill fires by). Null: no link, or nothing carried.</summary>
    public static string? LinkPick(CharacterData ch, string link) =>
        LinkRule(link) is { } e ? Battle.LinkPick(DayWeapons(ch), Now(ch).Links.GetValueOrDefault(link), e.Tags)?.Id : null;

    /// <summary>§14.5: the skills the link may be bound to: what she fights with by day (the sim fires a pick only if carried).</summary>
    public static IReadOnlyList<string> LinkChoices(CharacterData ch, string link) =>
        LinkRule(link) == null ? [] : Character.DaySkills(ch).Select(x => x.Id).ToList();

    /// <summary>§14.5: bind the link to one of LinkChoices.</summary>
    public static bool SetLinkPick(CharacterData ch, string link, string skill)
    {
        if (!LinkChoices(ch, link).Contains(skill)) return false;
        Now(ch).Links[link] = skill;
        return true;
    }

    /* ------------------------------------------------ into the fight -- */

    /// <summary>What the lit lamps bring a fight. By night (an ember arena, a story fight) sizes run at
    /// a quarter, counts add one at most, and small lamps only lean the draft (§2.10).</summary>
    public static LampLoadout Loadout(CharacterData ch, bool night)
    {
        var l = Now(ch);
        var o = new LampLoadout { Night = night, Type = l.Type, Flare = Carried(ch), Lit = l.Lit.Count };
        var counts = new Dictionary<string, double>();
        if (l.Links != null) foreach (var (k, v) in l.Links) o.Links[k] = v;
        foreach (var id in l.Lit)
        {
            if (Lamps.Find(id) is not { } d) continue;
            bool small = d.Kind is LampKind.Small or LampKind.Attribute;
            foreach (var e in d.Effects)
            {
                if (e.Phase > Lamps.LivePhase) continue;
                switch (e.Do)
                {
                    case LampDo.Mod when e.Stat != null:
                        if (night && small) break;
                        if (night && Lamps.IsCount(e.Stat) && !e.Price)
                        {
                            counts[e.Stat] = counts.GetValueOrDefault(e.Stat) + e.Value;
                            break;
                        }
                        o.Mods.Add(new StatMod(e.Stat, e.Mod, night && !e.Price ? e.Value * Lamps.NightSize : e.Value, $"lamp:{id}", e.When));
                        break;
                    case LampDo.Attr when e.Attr != null:
                        if (!night) o.Attributes[e.Attr] = o.Attributes.GetValueOrDefault(e.Attr) + (int)e.Value;
                        break;
                    // By night a small lamp gives nothing but its road's lean (CLASSES.md §2.10).
                    case LampDo.Rule when e.Rule != null:
                        if (night && small) break;
                        o.Add(e);
                        break;
                    case LampDo.Facet when e.Facet != null: o.Facets.Add(e.Facet); break;
                    case LampDo.Form when e.Art != null: o.Kin = e.Art; o.KinWait = e.Wait; break;
                    case LampDo.Reflex when e.Art != null: o.Reflexes.Add(new ReflexDef(e.Art, e.Trigger ?? "", e.Wait, e.Args)); break;
                    case LampDo.FlareMod when e.Flare != null: o.FlareMods.Add(e.Rule ?? id); break;
                }
            }
        }
        foreach (var (stat, v) in counts) o.Mods.Add(new StatMod(stat, ModKind.Flat, Math.Min(Lamps.NightCount, v), "lamps:counts"));
        if (Lamps.V2) BluePrices(o);
        o.Lean = LeanRoad(ch);
        return o;
    }

    /// <summary>Lamps v2: the blue lamps whose price is a number of hers (LAMPS_V2_RULES.md "The new blue lamps"), kept in
    /// full by night. The rest of their prices are rules the fight reads (Sim/BoardRules.cs).</summary>
    const double BaseDashCharges = 2;

    static void BluePrices(LampLoadout o)
    {
        // blue.butchers_block: less maximum health.
        if (o.Has("blue.butchers_block")) o.Mods.Add(new StatMod(Stat.MaxHealth, ModKind.More, -o.Full("blue.butchers_block", "health", 0.2), "price:blue.butchers_block"));
        // blue.poachers_mercy, blue.pack_remembers: "you have 1 dash charge" (`charges`), from the base two: one fewer.
        foreach (var r in new[] { "blue.poachers_mercy", "blue.pack_remembers" })
            if (o.Has(r)) o.Mods.Add(new StatMod(Stat.DashCharges, ModKind.Flat, Math.Min(0, o.Full(r, "charges", 1) - BaseDashCharges), "price:" + r));
    }

    /// <summary>The road lit deepest (the type's own on a tie): its cards lean by night.</summary>
    public static string LeanRoad(CharacterData ch)
    {
        var l = Now(ch);
        return Lamps.Roads.Keys.OrderByDescending(r => Depth(l.Lit, r) + (r == l.Type ? 0.5 : 0)).First();
    }
}
