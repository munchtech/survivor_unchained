R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
o = open(R + r'\Ornate.cs', encoding='utf-8').read()
add = open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\book_ornate.cs.txt', encoding='utf-8').read()
if 'class OpenBook' not in o:
    o = o.rstrip('\n') + '\n' + add
    open(R + r'\Ornate.cs', 'w', encoding='utf-8', newline='').write(o)

p = R + r'\Book.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

cut("    protected override void Build()\n    {\n        AddChild(Style.Scrim(G.CloseOverlay));\n        var wrap = Style.Centered(Style.V(0), new Vector2(1240, 720));",
    "    // Reading text on paper: body size, the ink of a hand that wrote it.",
'''    /// <summary>Each section's ribbon: its silk, so a glance at the book's top edge finds it.</summary>
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
        // The leaves' feet: the day on the left, whose book on the right.
        var w = G.Journey.World;
        Foot(book.Left, $"Day {w.Day}");
        Foot(book.Right, $"{G.Journey.Ch.Name}'s journal");

        // The sections as silk ribbons over the top edge, the open one hanging lower; LT and RT turn them.
        bool pad = Controls.Instance.UsingPad;
        var ribbons = Style.H(14);
        ribbons.Position = new Vector2(70 + 120, 52 - 30);
        ribbons.MouseFilter = MouseFilterEnum.Ignore;
        content.AddChild(ribbons);
        var lt = pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev));
        lt.SizeFlagsVertical = SizeFlags.ShrinkBegin;
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
            b.CustomMinimumSize = new Vector2(124, on ? 96 : 70);
            b.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            ribbons.AddChild(Nav.Skip(b));
        }
        var rt = pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext));
        rt.SizeFlagsVertical = SizeFlags.ShrinkBegin;
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

''')

# Each section now hands back its two leaves.
rep("""    HBoxContainer Two(Control a, Control b)
    {
        var h = Style.H(30);
        a.SizeFlagsHorizontal = b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        page = Style.Scroll(a);
        h.AddChild(page);
        h.AddChild(Style.Scroll(b));
        return h;
    }

    Control Quests()""", """    (Control, Control) Quests()""")
rep("""        var side = Style.V(4);
        side.CustomMinimumSize = new Vector2(300, 0);
        foreach (var (st, label) in new[] { (QuestStatus.Active, "Under way"), (QuestStatus.Resolved, "Done"), (QuestStatus.Failed, "Lost") })
        {
            var qs = list.Where(x => st == QuestStatus.Failed ? x.Status is QuestStatus.Failed or QuestStatus.Abandoned : x.Status == st).ToList();
            if (qs.Count == 0) continue;
            side.AddChild(Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, InkSoft, false, HorizontalAlignment.Left, false));""",
"""        var side = Style.V(4);
        foreach (var (st, label) in new[] { (QuestStatus.Active, "Under way"), (QuestStatus.Resolved, "Done"), (QuestStatus.Failed, "Lost") })
        {
            var qs = list.Where(x => st == QuestStatus.Failed ? x.Status is QuestStatus.Failed or QuestStatus.Abandoned : x.Status == st).ToList();
            if (qs.Count == 0) continue;
            if (side.GetChildCount() > 0) side.AddChild(Style.Gap(Style.Gap2));
            side.AddChild(H2(label));""")
rep("""        var h = Style.H(30);
        h.AddChild(Style.Scroll(side));
        side.SizeFlagsHorizontal = SizeFlags.Fill;
        h.GetChild<ScrollContainer>(0).CustomMinimumSize = new Vector2(310, 0);
        h.GetChild<ScrollContainer>(0).SizeFlagsHorizontal = SizeFlags.Fill;
        h.AddChild(Style.Scroll(page));
        return h;
    }""", """        return (side, page);
    }""")
rep("""    Control People()
    {""", """    (Control, Control) People()
    {""")
rep("""        if (met.Count == 0) return Style.V(0, P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft));""",
    """        if (met.Count == 0) return (Style.V(0, H2("People"), P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft)), Style.V(0));""")
rep("""        var side = Style.V(2);
        side.CustomMinimumSize = new Vector2(300, 0);
        foreach (var d in met)""", """        var side = Style.V(2, H2("Those you have met"));
        foreach (var d in met)""")
rep("""            bt.CustomMinimumSize = new Vector2(290, 50);""", """            bt.CustomMinimumSize = new Vector2(0, 50);""")
rep("""        var h = Style.H(30);
        var list = Style.Scroll(side);
        list.CustomMinimumSize = new Vector2(310, 0);
        list.SizeFlagsHorizontal = SizeFlags.Fill;
        h.AddChild(list);
        this.page = Style.Scroll(page);
        h.AddChild(this.page);
        return h;
    }""", """        return (side, page);
    }""")
rep("""    Control Deeds()
    {""", """    (Control, Control) Deeds()
    {""")
rep("""        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", Style.Caption, Style.UiBold, InkSoft));
        return Two(left, right);""", """        right.AddChild(P($"Days on the road: {w.Day}    Creatures slain: {ch.Stats.Kills}    Falls: {ch.Stats.Deaths}    Gold earned: {Math.Floor(ch.Stats.GoldEarned)}", Style.Caption, Style.UiBold, InkSoft));
        return (left, right);""")
rep("""    Control Codex()
    {""", """    (Control, Control) Codex()
    {""")
rep("""            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));
        }
        return Two(left, right);""", """            right.AddChild(Style.V(1, P(found ? d.Name : "Not yet found", Style.Body, Style.TextBold, found ? Ink : InkSoft), P(found ? d.Description : d.Hint, Style.Caption, Style.TextItalic, InkSoft)));
        }
        return (left, right);""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
