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
    /// <summary>Opened wide: the book lying open over the world, its two parchment leaves (the owner:
    /// the Journal and the Map keep to the book's half-window panel, "with an option to expand").
    /// Kept for the session, so it opens as it was left.</summary>
    static bool wide;
    /// <summary>The ink: a hand's on the parchment, the book's own type on the panel.</summary>
    Color Ink => wide ? Style.ParchmentInk : Kit.Ink;
    Color InkSoft => wide ? new Color("#5a4a36") : Kit.Dim;
    Color Red => wide ? new Color("#8a2a1a") : Style.Ember;
    Color HeadInk => wide ? new Color("#3a2414") : Kit.Ink;
    Color Good => wide ? new Color("#3a6a2a") : new Color("#8ac06a");

    // In the panel she stands beside it, near enough that her face reads (as for the rest of the book);
    // with the book opened wide, the view is the book's.
    public override float CameraShift => wide ? 0 : -330;
    public override float CameraNear => wide ? 1 : 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => wide ? null : BookFrame;

    // (--journal people|deeds|codex: opened at that section, for pictures; --journal-wide: opened wide)
    public JournalScreen(Game g) : base(g)
    {
        if (Args.Get("journal") is string t && Array.Exists(Sections, x => x.Id == t)) tab = t;
        if (Args.Has("journal-wide")) wide = true;
    }

    static readonly (string Id, string Name)[] Sections = { ("quests", "Quests"), ("people", "People"), ("deeds", "Deeds"), ("codex", "Codex") };

    public override bool Key(Act a)
    {
        int i = Array.FindIndex(Sections, x => x.Id == tab);
        // Its own pages turn with LT and RT (, and .); LB and RB turn the book's.
        if (a == Act.SubNext) { tab = Sections[(i + 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        if (a == Act.SubPrev) { tab = Sections[(i + Sections.Length - 1) % Sections.Length].Id; Refresh(); Sound.Sfx.Page(); return true; }
        if (a == Act.Expand) { Widen(); return true; }
        // Pages with nothing to choose on them scroll.
        if (a is Act.Up or Act.Down && tab is "deeds" or "codex" && page is { } sc && IsInstanceValid(sc))
        {
            Nav.KeyMode = true;
            sc.ScrollVertical += a == Act.Down ? 90 : -90;
            return true;
        }
        return false;
    }

    void Widen()
    {
        wide = !wide;
        Sound.Sfx.Page();
        Refresh();
    }

    ScrollContainer? page;

    /// <summary>The open book's width (a reading measure, about 75 letters to a leaf's line) and its
    /// height's bounds: between them it hugs what is written in the section open, measured once laid
    /// out (an empty book was a screen of blank parchment).</summary>
    const float OpenW = 1440, MinH = 520, MaxH = 820;
    /// <summary>In the panel: the list's column and the page's beside it.</summary>
    const float ListW = 250, Gutter = 28;
    /// <summary>In the panel, the columns' height's bounds (the panel hugs what is written, up to the
    /// screen's height less its head and foot).</summary>
    const float ColMin = 220, ColMax = 800;
    readonly Dictionary<string, float> heights = new();
    readonly List<Control> measured = new();
    readonly List<ScrollContainer> leaves = new();
    /// <summary>The section whose height is still being found (shown only once it holds), the
    /// frames left before the next measure, and how many measures it has taken.</summary>
    string? settling;
    int measuring, tries;
    string Key2(string t) => (wide ? "w:" : "p:") + t;

    protected override void Build()
    {
        page = null;
        measured.Clear();
        leaves.Clear();
        if (!heights.ContainsKey(Key2(tab))) { settling = Key2(tab); tries = 0; }
        if (wide) BuildOpen(); else BuildPanel();
    }

    /// <summary>The sections as the house's tabs, LT and RT (, and .) either side to turn them.</summary>
    Control SectionTabs()
    {
        bool pad = Controls.Instance.UsingPad;
        int on = Array.FindIndex(Sections, x => x.Id == tab);
        var lt = pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev));
        var rt = pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext));
        var tabs = Kit.Tabs(Sections.Select(x => x.Name).ToArray(), on, k => { tab = Sections[k].Id; Refresh(); }, 18, 44);
        // (LT and RT turn them; focus keeps to the pages)
        foreach (var b in tabs.GetChildren().OfType<Button>()) Nav.Skip(b);
        var bar = Style.H(Style.Gap5, lt, tabs, rt);
        foreach (var c in bar.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        bar.Alignment = BoxContainer.AlignmentMode.Center;
        return bar;
    }

    (Control Left, Control Right, List<Control> Others) Leaves() => tab switch { "people" => People(), "deeds" => Deeds(), "codex" => Codex(), _ => Quests() };

    /// <summary>In the book's panel, as the Pack, Self and Arts are: the sections as tabs, then the list
    /// at the left and what is chosen at the right, as type on the panel; the day and whose journal
    /// along the foot. The columns hug what is written, measured once laid out.</summary>
    void BuildPanel()
    {
        var v = BookPanel(null, expand: Widen, wide: false);
        v.AddChild(SectionTabs());
        var (left, right, others) = Leaves();
        float pageW = BookW - 2 * Margin - ListW - Gutter;
        float h = heights.TryGetValue(Key2(tab), out var known) ? known : ColMax;
        var cols = Style.H((int)Gutter);
        v.AddChild(cols);
        cols.AddChild(Leaf(left, new Vector2(ListW, h)));
        cols.AddChild(Leaf(right, new Vector2(pageW, h)));
        var w = G.Journey.World;
        var foot = Style.Label($"Day {w.Day}  ·  {G.Journey.Ch.Name}'s journal", Style.TextItalic, Style.Caption, Kit.Dim, false, HorizontalAlignment.Center);
        v.AddChild(foot);
        bool pad = Controls.Instance.UsingPad;
        v.AddChild(pad
            ? Kit.Prompts(Kit.Prompt(Act.SubNext, "Section"), Kit.Prompt(Act.Up, "Choose"), Kit.Prompt(Act.Expand, "Open wide"), Kit.Prompt(Act.TabNext, "Turn"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt(G.Key(Act.SubPrev) + " " + G.Key(Act.SubNext), "Section"), Kit.Prompt("[ ]", "Turn"), Kit.Prompt(G.Key(Act.Journal), "Close")));
        Settle(new[] { left, right }, others, pageW);
    }

    /// <summary>Opened wide: the book lying open over the world, the chain and the sections over it, its
    /// leaves the parchment's. The list on the left leaf, what is chosen on the right.</summary>
    void BuildOpen()
    {
        HideHud();
        var shade = new ColorRect { Color = new Color(0.02f, 0.015f, 0.03f, 0.45f), MouseFilter = MouseFilterEnum.Stop };
        Style.Fill(shade);
        AddChild(shade);
        float h = heights.TryGetValue(Key2(tab), out var known) ? known : MaxH;
        // The book's head over it: the chain and its tabs at the left, Fold and Close at the right; the
        // sections under them; the book under those, the whole centred on the screen.
        const float headH = 56, tabsH = 40, gap = 12;
        float top = Math.Max(16, (1080 - headH - tabsH - gap * 2 - h) / 2), x = (1920 - OpenW) / 2;
        var head = Style.H(Style.Gap3);
        int on = Array.FindIndex(Book, b => b.Kind == Kind);
        head.AddChild(new ChainTabs(Book.Select(b => (b.Name, Controls.Instance?.KeyLabel(b.Key) ?? "")).ToArray(), on, k => { Sound.Sfx.Page(); G.Open(Book[k].Kind); }));
        head.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var fold = Nav.Skip(Kit.Keyed(Act.Expand, "Fold", Widen, Kit.Ink2, 15));
        fold.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(fold);
        head.AddChild(new Control { CustomMinimumSize = new Vector2(Style.Gap5, 0), MouseFilter = MouseFilterEnum.Ignore });
        var close = Nav.Skip(CloseButton(G.Key(Act.Journal), G.CloseOverlay));
        close.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(close);
        head.Position = new Vector2(x, top);
        head.Size = new Vector2(OpenW, headH);
        AddChild(head);
        var bar = SectionTabs();
        bar.Position = new Vector2(x, top + headH + gap);
        bar.Size = new Vector2(OpenW, tabsH);
        AddChild(bar);
        var book = new OpenBook(new Vector2(OpenW, h)) { Position = new Vector2(x, top + headH + gap + tabsH + gap) };
        AddChild(book);
        var (left, right, others) = Leaves();
        Fill(book.Left, left);
        Fill(book.Right, right);
        // The leaves' feet: the day on the left, whose book on the right.
        var w = G.Journey.World;
        Foot(book.Left, $"Day {w.Day}");
        Foot(book.Right, $"{G.Journey.Ch.Name}'s journal");
        if (settling == Key2(tab))
        {
            book.Modulate = Colors.Transparent;
            measured.Add(left);
            measured.Add(right);
            foreach (var o in others) Offstage(o, book.Right.Size.X);
            measuring = 4;
        }
        if (Controls.Instance.UsingPad)
            PageFooter(Footer((Act.SubNext, "Turn to a section"), (Act.Up, "Choose"), (Act.Expand, "Fold"), (Act.TabNext, "Map"), (Act.Cancel, "Close")));
    }

    /// <summary>A column of the panel: its words in a scroll as tall as the column may be.</summary>
    Control Leaf(Control words, Vector2 size)
    {
        var sc = words as ScrollContainer ?? Style.Scroll(words);
        sc.CustomMinimumSize = size;
        sc.HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled;
        leaves.Add(sc);
        page ??= sc;
        return sc;
    }

    /// <summary>Laid out at a column's width off the screen, to be measured with the page in view.</summary>
    void Offstage(Control o, float width)
    {
        var holder = new Control { Position = new Vector2(-4000, 0), Size = new Vector2(width, 10), Modulate = Colors.Transparent, MouseFilter = MouseFilterEnum.Ignore };
        o.Size = new Vector2(width, 0);
        holder.AddChild(o);
        AddChild(holder);
        measured.Add(o);
    }

    /// <summary>The panel's columns measured before they are shown: this page and every page the list can
    /// open here (a quest chosen later scrolls in a column cut to the first), at the page's width.</summary>
    void Settle(Control[] shown, List<Control> others, float pageW)
    {
        if (settling != Key2(tab)) return;
        if (bookPanel != null) bookPanel.Modulate = Colors.Transparent;
        measured.AddRange(shown);
        foreach (var o in others) Offstage(o, pageW);
        measuring = 4;
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        // Laid out: the columns (or the open book) take their writing's height, measured again at it until
        // it holds (wrapped words settle their lines a frame or two after the width they wrap to; a scroll
        // bar, once shown, narrows them onto more), then shown.
        if (measuring > 0 && --measuring == 0 && settling == Key2(tab))
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y)
                .Concat(leaves.Where(IsInstanceValid).Select(s => (float)s.GetVScrollBar().MaxValue)).DefaultIfEmpty(0).Max();
            float had = heights.GetValueOrDefault(Key2(tab), wide ? MaxH : ColMax);
            float now = wide ? Math.Clamp(need + OpenBook.Chrome + 16, MinH, MaxH) : Math.Clamp(need + 8, ColMin, ColMax);
            // (it only grows once measured: cut short, a scroll bar wraps the words longer; grown, the bar goes
            // and they measure short again, and the two would take turns)
            if (tries > 0) now = Math.Max(now, had);
            heights[Key2(tab)] = now;
            if (Math.Abs(now - had) <= 2 || ++tries >= 4) settling = null;
            if (Args.Has("shot")) GD.Print($"journal {(wide ? "open" : "panel")} {tab}: words {need:0}, height {now:0}{(settling == null ? ", held" : "")}");
            Refresh();
        }
    }

    /// <summary>A leaf's words, scrolled if they run long; the left leaf's scroll is the one the keys move.</summary>
    void Fill(Control leaf, Control words)
    {
        var sc = words as ScrollContainer ?? Style.Scroll(words);
        sc.Position = Vector2.Zero;
        sc.Size = leaf.Size - new Vector2(0, 30);
        leaf.AddChild(sc);
        leaves.Add(sc);
        page ??= sc;
    }

    void Foot(Control leaf, string text)
    {
        var l = Style.Label($"~  {text}  ~", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Center);
        l.Position = new Vector2(0, leaf.Size.Y - 18);
        l.Size = new Vector2(leaf.Size.X, 20);
        leaf.AddChild(l);
    }

    // Reading text: body size, in the ink of the hand that wrote it (on the parchment) or the book's type.
    Label P(string text, int size = Style.Body, Font? font = null, Color? color = null) => Style.Label(text, font ?? Style.Text, size, color ?? Ink, true, HorizontalAlignment.Left, false);
    // (a size down in the panel, whose list's column is narrow: "Those you have met" broke its last word off)
    Label H2(string text) => Style.Label(text, Style.Display, wide ? Style.Title : 20, HeadInk, true, HorizontalAlignment.Left, false);

    (Control, Control, List<Control>) Quests()
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
        var page = quest != null ? QuestPage(quest) : Style.V(8);
        if (quest == null && list.Count > 0) page.AddChild(P("Choose an entry.", Style.Body, Style.TextItalic, InkSoft));
        return (side, page, list.Where(q => q.Id != quest).Select(q => (Control)QuestPage(q.Id)).ToList());
    }

    /// <summary>A quest's page: its name, what it is about, what has been written of it, how it ended.</summary>
    VBoxContainer QuestPage(string id)
    {
        var w = G.Journey.World;
        var page = Style.V(8);
        if (w.Quests.TryGetValue(id, out var qst) && Lore.Quests.TryGetValue(id, out var qd))
        {
            page.AddChild(H2(qd.Name));
            page.AddChild(P(qd.Summary, Style.Body, Style.TextItalic, InkSoft));
            page.AddChild(Style.Rule());
            foreach (var e in qst.Entries) page.AddChild(P(qd.Entries.GetValueOrDefault(e, e)));
            if (qst.Outcome != null && qd.Outcomes?.GetValueOrDefault(qst.Outcome) is string o) page.AddChild(P(o, Style.Body, Style.TextBold, Red));
            if (qst.StartedDay is int d) page.AddChild(P($"Begun on day {d}", Style.Caption, Style.TextItalic, InkSoft));
        }
        return page;
    }

    /// <summary>A measure from -100 to 100 as a line with a mark: green for you, red against, the middle marked.</summary>
    Control Feel(double v, float w = 120)
    {
        var p = new Control { CustomMinimumSize = new Vector2(w, 14), MouseFilter = MouseFilterEnum.Ignore };
        var track = wide ? new Color(0.35f, 0.25f, 0.12f, 1) : Kit.Faint;
        p.AddChild(new ColorRect { Color = track with { A = 0.35f }, Position = new Vector2(0, 6), Size = new Vector2(w, 2), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = track with { A = 0.6f }, Position = new Vector2(w / 2 - 1, 2), Size = new Vector2(2, 10), MouseFilter = MouseFilterEnum.Ignore });
        float x = (float)((Math.Clamp(v, -100, 100) + 100) / 200 * (w - 8));
        var col = v >= 0 ? Good : Red;
        // The stretch from the middle to the mark, then the mark.
        p.AddChild(new ColorRect { Color = col with { A = 0.35f }, Position = new Vector2(Math.Min(x + 4, w / 2), 5), Size = new Vector2(Math.Abs(x + 4 - w / 2), 4), MouseFilter = MouseFilterEnum.Ignore });
        p.AddChild(new ColorRect { Color = col, Position = new Vector2(x, 1), Size = new Vector2(8, 12), MouseFilter = MouseFilterEnum.Ignore });
        return p;
    }

    string? person;

    /// <summary>People as the quests are: a list of those met (how each feels, in a word), and
    /// the one chosen on the page beside it, drawn as they look, with how they feel about you
    /// on four measures, what is on their mind, and what they know you did.</summary>
    (Control, Control, List<Control>) People()
    {
        var w = G.Journey.World;
        var ctx = G.Journey.Ctx;
        var met = Lore.Npcs.Values.Where(d => w.Npcs.TryGetValue(d.Id, out var s) && s.Flags.TryGetValue("met", out var m) && m.Truthy).ToList();
        if (met.Count == 0) return (Style.V(0, H2("People"), P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft)), Style.V(0), new());
        if (person == null || met.All(d => d.Id != person)) person = met[0].Id;
        var side = Style.V(2, H2("Those you have met"));
        foreach (var d in met)
        {
            var st = w.Npcs[d.Id];
            var id = d.Id;
            var bt = Style.Button("", () => { person = id; Refresh(); }, false, true);
            // The one chosen is in the red ink, as a quest is; the pointer reddens a name (a tinted
            // band behind the line was a box on the page).
            foreach (var state in new[] { "normal", "hover", "pressed" }) bt.AddThemeStyleboxOverride(state, new StyleBoxEmpty());
            var who0 = Style.Label(d.Name, Style.TextBold, Style.Body, id == person ? Red : Ink, false, HorizontalAlignment.Left, false);
            bt.MouseEntered += () => who0.AddThemeColorOverride("font_color", Red);
            bt.MouseExited += () => who0.AddThemeColorOverride("font_color", id == person ? Red : Ink);
            var line = Style.V(0, who0,
                Style.Label($"{d.Role}  ·  {(st.Alive ? Rules.Attitude(st) : "dead")}", Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));
            line.Position = new Vector2(0, 3);
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
        return (side, page, new());
    }

    (Control, Control, List<Control>) Deeds()
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
            var tone = st.Tone switch { StandingTone.Ally or StandingTone.Friend => Good, StandingTone.Hostile => Red, StandingTone.Wary => wide ? new Color("#8a5a1a") : new Color("#d8a050"), _ => InkSoft };
            right.AddChild(Style.V(1, Style.H(10, P(st.Name, Style.Body, Style.TextBold), P(st.Word, Style.Small, Style.TextItalic, tone)), P(st.Why, Style.Caption, Style.Text, InkSoft)));
        }
        right.AddChild(Style.Rule());
        // The road so far as a ledger line, numerals over their names (it was a run-on line of captions).
        var tally = Style.H(0);
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var (n, what) in new[] { ($"{w.Day}", "days on the road"), ($"{ch.Stats.Kills:N0}", "slain"), ($"{ch.Stats.Deaths}", "falls"), ($"{Math.Floor(ch.Stats.GoldEarned):N0}", "gold earned") })
        {
            var cell = Style.V(0, Style.Label(n, Style.Display, 26, Ink, false, HorizontalAlignment.Center, false),
                Style.Label(what.ToUpperInvariant(), Style.UiHeavy, 11, InkSoft, false, HorizontalAlignment.Center, false));
            cell.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            tally.AddChild(cell);
        }
        right.AddChild(tally);
        return (left, right, new());
    }

    (Control, Control, List<Control>) Codex()
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
        // The discoveries under the beasts: the left leaf held one line beside a right leaf of
        // sixty, so the two now share the spread.
        left.AddChild(Style.Gap(10));
        int dn = Discoveries.All.Count(d => w.Codex.Contains(d.Id));
        left.AddChild(H2($"Discoveries  ({dn} of {Discoveries.All.Length})"));
        foreach (var d in Discoveries.All)
        {
            bool found = w.Codex.Contains(d.Id);
            // (one not yet found is its hint alone, in the margin's hand: "Not yet found" over each was sixty words of nothing)
            left.AddChild(found ? Style.V(1, P(d.Name, Style.Small, Style.TextBold), P(d.Description, Style.Caption, Style.TextItalic, InkSoft))
                : P(d.Hint, Style.Caption, Style.TextItalic, InkSoft));
        }
        // What the ember has made, as a ledger: each art on one line with what it takes at rank 8,
        // a making named in its place once made (a "???" over every recipe was a wall of them).
        var right = Style.V(8);
        var arts = Weapons.All.Values.Where(x => x.Findable && x.Evolutions.Length > 0).ToList();
        int all = arts.Sum(x => x.Evolutions.Length) + Unions.All.Length;
        int known = arts.Sum(x => x.Evolutions.Count(e => w.Codex.Contains($"evo:{e.Id}"))) + Unions.All.Count(u => w.Codex.Contains($"union:{u.Id}"));
        right.AddChild(H2($"What the ember makes  ({known} of {all})"));
        right.AddChild(P("Each art at rank 8, with one of the things named beside it.", Style.Caption, Style.TextItalic, InkSoft));
        var ledger = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        ledger.AddThemeConstantOverride("h_separation", 18);
        ledger.AddThemeConstantOverride("v_separation", 3);
        foreach (var wd in arts)
        {
            var made = wd.Evolutions.Where(e => w.Codex.Contains($"evo:{e.Id}")).ToList();
            var name = P(wd.Name, Style.Small, Style.TextBold, made.Count > 0 ? Ink : InkSoft);
            name.AutowrapMode = TextServer.AutowrapMode.Off;
            name.SizeFlagsHorizontal = SizeFlags.Fill;
            ledger.AddChild(name);
            string Way(Evolution e) => string.Join(" or ", e.Catalysts.Select(c => Boons.Find(c)?.Name ?? c)) + (w.Codex.Contains($"evo:{e.Id}") ? $": {e.Name}" : "");
            ledger.AddChild(P(string.Join("  ·  ", wd.Evolutions.Select(Way)), Style.Caption, Style.TextItalic, made.Count > 0 ? Ink : InkSoft));
        }
        right.AddChild(ledger);
        right.AddChild(Style.Gap(6));
        right.AddChild(P("Unions", Style.Small, Style.TextBold, Ink));
        foreach (var u in Unions.All)
        {
            bool found = w.Codex.Contains($"union:{u.Id}");
            right.AddChild(P($"{Weapons.All[u.A].Name} and {Weapons.All[u.B].Name}, both evolved{(found ? $": {u.Name}" : "")}", Style.Caption, Style.TextItalic, found ? Ink : InkSoft));
        }
        return (left, right, new());
    }
}
