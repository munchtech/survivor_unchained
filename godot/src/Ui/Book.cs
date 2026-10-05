using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The journal (the web game's overlays/Journal.tsx): what you are doing,
/// who you know, what you have done and what you have learned. Written like
/// a book because it is one, the survivor's own; every line in it is the
/// world's memory, read back.
/// </summary>
public partial class JournalScreen : Overlay
{
    public override string Kind => "journal";
    public override Act? Toggle => Act.Journal;
    string tab = "quests";
    string? quest;
    static readonly Color Ink = Style.ParchmentInk, InkSoft = new("#5a4a36"), Red = new("#8a2a1a");

    public JournalScreen(Game g) : base(g) { }

    static readonly (string Id, string Name)[] Sections = { ("quests", "Quests"), ("people", "People"), ("deeds", "Deeds"), ("codex", "Codex") };

    public override bool Key(Act a)
    {
        int i = Array.FindIndex(Sections, x => x.Id == tab);
        // Its own pages turn with LT and RT (, and .); LB and RB turn the book's.
        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        // Pages with nothing to choose on them scroll.
        if (a is Act.Up or Act.Down && tab is "deeds" or "codex" && page is { } sc && IsInstanceValid(sc))
        {
            Nav.KeyMode = true;
            sc.ScrollVertical += a == Act.Down ? 90 : -90;
            return true;
        }
        return false;
    }

    ScrollContainer? page;

    /// <summary>Each section's ribbon: its silk, so a glance at the book's top edge finds it.</summary>
    static readonly Dictionary<string, Color> Silk = new()
    {
        ["quests"] = new("#8a2418"), ["people"] = new("#2f5a32"), ["deeds"] = new("#2c3f6a"), ["codex"] = new("#8a6a1e"),
    };

    protected override void Build()
    {
        var content = Page("Journal");
        // The book lies open on the page: the list on the left leaf, what is chosen on the right.
        var book = new OpenBook(new Vector2(1700, 852)) { Position = new Vector2(70, 52) };
        content.AddChild(book);
        page = null;
        var (left, right) = tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() };
        Fill(book.Left, left);
        Fill(book.Right, right);
        if (right.GetChildCount() == 0)
        {
            var mark = Glyphs.Icon(tab switch { "people" => "talk", "deeds" => "sigil", "codex" => "book", _ => "quest" }, 220, new Color(0.35f, 0.24f, 0.1f, 0.12f));
            mark.Position = (book.Right.Size - new Vector2(220, 220)) / 2;
            book.Right.AddChild(mark);
        }
        // The leaves' feet: the day on the left, whose book on the right.
        var w = G.Journey.World;
        Foot(book.Left, $"Day {w.Day}");
        Foot(book.Right, $"{G.Journey.Ch.Name}'s journal");

        // The sections as silk ribbons over the top edge, the open one hanging lower; LT and RT turn them.
        bool pad = Controls.Instance.UsingPad;
        var ribbons = Style.H(14);
        ribbons.Position = new Vector2(70 + 120, 52 + 22 - 86);
        ribbons.MouseFilter = MouseFilterEnum.Ignore;
        content.AddChild(ribbons);
        var lt = pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev));
        lt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        ribbons.AddChild(lt);
        foreach (var (id, name) in Sections)
        {
            bool on = tab == id;
            var b = Style.Button(name, () => { tab = id; Refresh(); Sound.Sfx.Page(); }, false, true);
            var rb = new RibbonBox { Silk = Silk[id] };
            var rh = new RibbonBox { Silk = Silk[id], Raised = true };
            b.AddThemeStyleboxOverride("normal", rb);
            b.AddThemeStyleboxOverride("pressed", rb);
            b.AddThemeStyleboxOverride("hover", rh);
            b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
            Style.Font(b, Style.UiHeavy, Style.Small, on ? Colors.White : new Color(1, 0.94f, 0.85f, 0.82f), false);
            b.CustomMinimumSize = new Vector2(132, on ? 86 : 66);
            b.SizeFlagsVertical = SizeFlags.ShrinkEnd;
            ribbons.AddChild(Nav.Skip(b));
        }
        var rt = pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext));
        rt.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        ribbons.AddChild(rt);
        if (pad)
            PageFooter(Footer((Act.SubNext, "Turn to a section"), (Act.Up, "Choose"), (Act.TabPrev, "Arts"), (Act.TabNext, "Map"), (Act.Cancel, "Close")));
    }

    /// <summary>A leaf's words, scrolled if they run long; the left leaf's scroll is the one the keys move.</summary>
    void Fill(Control leaf, Control words)
    {
        var sc = words as ScrollContainer ?? Style.Scroll(words);
        sc.Position = Vector2.Zero;
        sc.Size = leaf.Size - new Vector2(0, 30);
        leaf.AddChild(sc);
        page ??= sc;
    }

    static void Foot(Control leaf, string text)
    {
        var l = Style.Label($"~  {text}  ~", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Center);
        l.Position = new Vector2(0, leaf.Size.Y - 18);
        l.Size = new Vector2(leaf.Size.X, 20);
        leaf.AddChild(l);
    }

    // Reading text on paper: body size, the ink of a hand that wrote it.
    static Label P(string text, int size = Style.Body, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    static Label H2(string text) => Style.Label(text, Style.Display, Style.Title, new Color("#3a2414"), true, HorizontalAlignment.Left, false);

    (Control, Control) Quests()
    {
        var w = G.Journey.World;
        // The troubles first, then the mysteries (the lamps open on the Low
        // Ford road, before anyone in town has asked the survivor for anything).
        var list = w.Quests.Values.Where(q => q.Status != QuestStatus.Unknown && Lore.Quests.ContainsKey(q.Id)).OrderBy(q => Lore.Quests[q.Id].Mystery).ToList();
        quest ??= list.FirstOrDefault(q => q.Status == QuestStatus.Active)?.Id ?? list.FirstOrDefault()?.Id;
        var side = Style.V(4);
        foreach (var (st, label) in new[] { (QuestStatus.Active, "Under way"), (QuestStatus.Resolved, "Done"), (QuestStatus.Failed, "Lost") })
        {
            var qs = list.Where(x => st == QuestStatus.Failed ? x.Status is QuestStatus.Failed or QuestStatus.Abandoned : x.Status == st).ToList();
            if (qs.Count == 0) continue;
            if (side.GetChildCount() > 0) side.AddChild(Style.Gap(Style.Gap2));
            side.AddChild(H2(label));
            foreach (var q in qs)
            {
                var def = Lore.Quests[q.Id];
                var id = q.Id;
                var b = new Button { Text = (def.Mystery ? "? " : "• ") + def.Name, Alignment = HorizontalAlignment.Left, FocusMode = FocusModeEnum.None, Flat = true };
                Nav.Id(b, $"quest:{id}");
                Style.Font(b, quest == id ? Style.TextBold : Style.Text, Style.Body, quest == id ? Red : Ink, false);
                b.AddThemeColorOverride("font_hover_color", Red);
                b.Pressed += () => { quest = id; Refresh(); };
                side.AddChild(b);
            }
        }
        if (list.Count == 0) side.AddChild(P("Nothing written yet. What people ask of you is written here as you hear it.", Style.Small, Style.TextItalic, InkSoft));
        var page = Style.V(8);
        if (quest != null && w.Quests.TryGetValue(quest, out var qst) && Lore.Quests.TryGetValue(quest, out var qd))
        {
            page.AddChild(H2(qd.Name));
            page.AddChild(P(qd.Summary, Style.Body, Style.TextItalic, InkSoft));
            page.AddChild(Style.Rule());
            foreach (var e in qst.Entries) page.AddChild(P(qd.Entries.GetValueOrDefault(e, e)));
            if (qst.Outcome != null && qd.Outcomes?.GetValueOrDefault(qst.Outcome) is string o) page.AddChild(P(o, Style.Body, Style.TextBold, Red));
            if (qst.StartedDay is int d) page.AddChild(P($"Begun on day {d}", Style.Caption, Style.TextItalic, InkSoft));
        }
        else if (list.Count > 0) page.AddChild(P("Choose an entry.", Style.Body, Style.TextItalic, InkSoft));
        return (side, page);
    }

    /// <summary>A measure from -100 to 100 as a line with a mark: green for you, red against, the middle marked.</summary>
    static Control Feel(double v, float w = 120)
    {
        var p = new Control { CustomMinimumSize = new Vector2(w, 14), MouseFilter = MouseFilterEnum.Ignore };
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.35f), Position = new Vector2(0, 6), Size = new Vector2(w, 2), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = new Color(0.35f, 0.25f, 0.12f, 0.6f), Position = new Vector2(w / 2 - 1, 2), Size = new Vector2(2, 10), MouseFilter = MouseFilterEnum.Ignore });
        float x = (float)((Math.Clamp(v, -100, 100) + 100) / 200 * (w - 8));
        var col = v >= 0 ? new Color("#3a6a2a") : new Color("#8a2a1a");
        // The stretch from the middle to the mark, then the mark.
        p.AddChild(new ColorRect { Color = col with { A = 0.35f }, Position = new Vector2(Math.Min(x + 4, w / 2), 5), Size = new Vector2(Math.Abs(x + 4 - w / 2), 4), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = col, Position = new Vector2(x, 1), Size = new Vector2(8, 12), MouseFilter = MouseFilterEnum.Ignore });
        return p;
    }

    string? person;

    /// <summary>People as the quests are: a list of those met (how each feels, in a word), and
    /// the one chosen on the page beside it, drawn as they look, with how they feel about you
    /// on four measures, what is on their mind, and what they know you did.</summary>
    (Control, Control) People()
    {
        var w = G.Journey.World;
        var ctx = G.Journey.Ctx;
        var met = Lore.Npcs.Values.Where(d => w.Npcs.TryGetValue(d.Id, out var s) && s.Flags.TryGetValue("met", out var m) && m.Truthy).ToList();
        if (met.Count == 0) return (Style.V(0, H2("People"), P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft)), Style.V(0));
        if (person == null || met.All(d => d.Id != person)) person = met[0].Id;
        var side = Style.V(2, H2("Those you have met"));
        foreach (var d in met)
        {
            var st = w.Npcs[d.Id];
            var id = d.Id;
            var bt = Style.Button("", () => { person = id; Refresh(); }, false, true);
            foreach (var state in new[] { "normal", "hover", "pressed" })
                bt.AddThemeStyleboxOverride(state, Style.Box(id == person || state == "hover" ? new Color(0.35f, 0.24f, 0.08f, id == person ? 0.16f : 0.08f) : new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0, 4, 0));
            var line = Style.V(0, Style.Label(d.Name, Style.TextBold, Style.Body, id == person ? Red : Ink, false, HorizontalAlignment.Left, false),
                Style.Label($"{d.Role}  ·  {(st.Alive ? Rules.Attitude(st) : "dead")}", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));
            line.Position = new Vector2(8, 3);
            line.MouseFilter = MouseFilterEnum.Ignore;
            bt.AddChild(line);
            bt.CustomMinimumSize = new Vector2(0, 50);
            // Focus on a name shows them (a pad reads the page as it moves down the list).
            Nav.Mark(bt, $"person:{id}", () => { person = id; Refresh(); }, focus: () => { if (person != id) { person = id; Refresh(); } });
            side.AddChild(bt);
        }
        var d0 = met.First(d => d.Id == person);
        var s0 = w.Npcs[d0.Id];
        var page = Style.V(Style.Gap2);
        var head = Style.H(Style.Gap4);
        var frame = Style.Panel(Style.Box(new Color(0.16f, 0.12f, 0.08f, 0.9f), new Color("#5a3e24"), 2, 4, 0));
        frame.CustomMinimumSize = new Vector2(190, 230);
        if (d0.Person != null) frame.AddChild(new Portrait(new Vector2I(190, 230), Portrait.Framing.Bust).Of(d0.Person, d0.Arms, d0.Scale ?? 1));
        head.AddChild(frame);
        var who = Style.V(4, H2(d0.Name), P(d0.Role + (d0.Title != "" && d0.Title != d0.Role ? $"  ·  {d0.Title}" : ""), Style.Small, Style.TextItalic, InkSoft),
            P(s0.Alive ? Style.Cap1(Rules.Attitude(s0)) : "Dead.", Style.Body, Style.TextBold, Red));
        who.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (s0.Alive && Lore.ConcernOf(d0.Id, ctx) is string mind) { who.AddChild(Style.Gap(4)); who.AddChild(P(mind, Style.Body, Style.TextItalic)); }
        head.AddChild(who);
        page.AddChild(head);
        page.AddChild(Style.Rule());
        // Four measures, each a bar from against you to for you, with a word.
        var axes = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        axes.AddThemeConstantOverride("h_separation", 14);
        axes.AddThemeConstantOverride("v_separation", 6);
        foreach (var (label, val, lo, hi) in new[] { ("Trust", s0.Trust, "doubts you", "trusts you"), ("Warmth", s0.Affection, "cold to you", "fond of you"), ("Respect", s0.Respect, "thinks little of you", "respects you"), ("Fear", s0.Fear, "unafraid", "afraid of you") })
        {
            var name = Style.Label(label, Style.UiBold, Style.Small, Ink, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(90, 0);
            axes.AddChild(name);
            axes.AddChild(Feel(val, 260));
            axes.AddChild(Style.Label(Math.Abs(val) < 12 ? "neither way" : $"{(Math.Abs(val) > 55 ? "much " : "")}{(val < 0 ? lo : hi)}".Replace("much unafraid", "quite unafraid"), Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));
        }
        page.AddChild(axes);
        var heard = s0.Memories.Select(m => w.History.FirstOrDefault(h => h.Id == m)).Where(h => h != null).Select(h => h!.Text).ToList();
        page.AddChild(Style.Gap(4));
        page.AddChild(P(heard.Count > 0 ? $"Knows that you {string.Join("; ", heard)}." : "Has heard nothing of what you have done.", Style.Small, Style.Text, InkSoft));
        return (side, page);
    }

    (Control, Control) Deeds()
    {
        var w = G.Journey.World;
        var ch = G.Journey.Ch;
        var left = Style.V(8, H2("What the world remembers"));
        if (w.History.Count == 0) left.AddChild(P("Nothing, yet. Give it time.", 16, Style.TextItalic, InkSoft));
        foreach (var h in Enumerable.Reverse(w.History))
        {
            var knowers = w.Npcs.Values.Where(n => n.Memories.Contains(h.Id)).Select(n => Lore.Person(n.Id)?.Name).Where(n => n != null).ToList();
            left.AddChild(Style.V(1, P($"Day {h.Day}", Style.Badge, Style.UiHeavy, InkSoft), P($"You {h.Text}."),
                P(knowers.Count > 0 ? $"Known to {string.Join(", ", knowers)}" : h.Spread > 0 ? "Word has not got round yet." : "Nobody saw.", Style.Caption, Style.TextItalic, InkSoft)));
        }
        var right = Style.V(8, H2("Where you stand"));
        var stand = Standings.Of(G.Journey.Ctx);
        if (stand.Count == 0) right.AddChild(P("Nobody out here knows you yet.", 16, Style.TextItalic, InkSoft));
        foreach (var st in stand)
        {
            var tone = st.Tone switch { StandingTone.Ally or StandingTone.Friend => new Color("#3a6a2a"), StandingTone.Hostile => Red, StandingTone.Wary => new Color("#8a5a1a"), _ => InkSoft };
            right.AddChild(Style.V(1, Style.H(10, P(st.Name, Style.Body, Style.TextBold), P(st.Word, Style.Small, Style.TextItalic, tone)), P(st.Why, Style.Caption, Style.Text, InkSoft)));
        }
        right.AddChild(Style.Rule());
        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", Style.Caption, Style.UiBold, InkSoft));
        return (left, right);
    }

    (Control, Control) Codex()
    {
        var w = G.Journey.World;
        var left = Style.V(8, H2("Bestiary"));
        var seen = w.Bestiary.Where(kv => Content.Enemies.All.ContainsKey(kv.Key)).ToList();
        if (seen.Count == 0) left.AddChild(P("Nothing put down yet.", 16, Style.TextItalic, InkSoft));
        foreach (var (id, n) in seen)
        {
            var e = Content.Enemies.Get(id);
            left.AddChild(Style.V(1, P($"{e.Name}  × {n}", Style.Body, Style.TextBold), P(e.Note, Style.Caption, Style.Text, InkSoft)));
        }
        // What the ember has made: evolutions and unions, named once made; until
        // then the recipe stands as the hint.
        var right = Style.V(8);
        var evos = Weapons.All.Values.Where(x => x.Findable).SelectMany(x => x.Evolutions.Select(e => (W: x, E: e))).ToList();
        int known = evos.Count(x => w.Codex.Contains($"evo:{x.E.Id}")) + Unions.All.Count(u => w.Codex.Contains($"union:{u.Id}"));
        right.AddChild(H2($"What the ember makes  ({known} of {evos.Count + Unions.All.Length})"));
        foreach (var (wd, e) in evos)
        {
            bool found = w.Codex.Contains($"evo:{e.Id}");
            string recipe = $"{wd.Name} at rank 8, with {string.Join(" or ", e.Catalysts.Select(c => Boons.Find(c)?.Name ?? c))}";
            right.AddChild(Style.V(1, P(found ? e.Name : "???", 16, Style.TextBold, found ? Ink : InkSoft), P(found ? $"{recipe}. {e.Description}" : recipe, 14, Style.TextItalic, InkSoft)));
        }
        foreach (var u in Unions.All)
        {
            bool found = w.Codex.Contains($"union:{u.Id}");
            string recipe = $"{Weapons.All[u.A].Name} and {Weapons.All[u.B].Name}, both evolved";
            right.AddChild(Style.V(1, P(found ? u.Name : "??? (a union)", 16, Style.TextBold, found ? Ink : InkSoft), P(found ? $"{recipe}. {u.Description}" : recipe, 14, Style.TextItalic, InkSoft)));
        }
        right.AddChild(Style.Gap(10));
        right.AddChild(H2("Discoveries"));
        foreach (var d in Discoveries.All)
        {
            bool found = w.Codex.Contains(d.Id);
            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));
        }
        return (left, right);
    }
}
