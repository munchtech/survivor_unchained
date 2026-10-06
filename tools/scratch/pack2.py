p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Pack.cs'
s = open(p, encoding='utf-8').read()
a = s.index("    protected override void Build()\n    {\n        var ch = Ch;")
b = s.index("    static IEnumerable<ItemInstance> Carried(CharacterData ch) =>")
new = '''    protected override void Build()
    {
        var ch = Ch;
        if (!seeded) { seeded = true; foreach (var it in Carried(ch)) seen.Add(it.Uid); }
        // A full page: the survivor as they stand on the left, what they carry on the right.
        var page = Page("Pack");

        // The survivor, large, with what they wear round them; their standing beneath.
        var you = Pane(page, new Rect2(0, 0, 780, 920));
        var name = Style.H(12, Style.Label(ch.Name, Style.Display, 30, Style.GoldHi),
            Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.TextItalic, Style.Small, Style.InkDim));
        name.Alignment = BoxContainer.AlignmentMode.Center;
        you.AddChild(name);
        var doll = Style.H(Style.Gap4, Column(Left, ch), Figure(ch), Column(Right, ch));
        doll.Alignment = BoxContainer.AlignmentMode.Center;
        you.AddChild(doll);
        you.AddChild(new Section("Standing", "hover a thing to see what it would change"));
        var standWell = Style.Panel(Style.Well(14));
        stats = Style.V(2);
        standWell.AddChild(stats);
        you.AddChild(standWell);
        ShowStats(null);

        // What they carry.
        var carried = Pane(page, new Rect2(810, 0, 1030, 920));
        carried.AddChild(FilterRow());
        var well = Style.Panel(Style.Well(12));
        well.AddChild(ItemViews.Grid(ch.Pack, 8, 112, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, SetupCell));
        carried.AddChild(well);
        carried.AddChild(Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 18, Style.GoldHi), Style.Label($"{Math.Floor(ch.Gold)} gold", Style.UiBold, Style.Body, Style.GoldHi)),
            Style.Label($"{ch.Pack.Count(p => p != null)} of {ch.Pack.Count} carried", Style.Ui, Style.Small, Style.InkDim)));
        carried.AddChild(new Section("Read closely"));
        inspect = Style.V(Style.Gap2);
        inspect.SizeFlagsVertical = SizeFlags.ExpandFill;
        carried.AddChild(inspect);
        ShowInspect(sel != null ? Inventory.Find(ch, sel)?.Item : null);
        foot = new Control { CustomMinimumSize = new Vector2(1840, 30), MouseFilter = MouseFilterEnum.Ignore };
        PageFooter(foot);
        Footer();
    }

'''
s = s[:a] + new + s[b:]
pairs = [
("""    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(8);""",
"""    Control Column(EquipSlot[] slots, CharacterData ch)
    {
        var v = Style.V(Style.Gap3);
        v.Alignment = BoxContainer.AlignmentMode.Center;"""),
("""            var view = ItemViews.Slot(it, 78, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,""",
"""            var view = ItemViews.Slot(it, 96, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,"""),
("""    Control Figure(CharacterData ch)
    {
        var v = Style.V(4);
        v.AddChild(new Portrait(new Vector2I(230, 340)).Of(Loadouts.Of(ch)));
        v.AddChild(Style.Label(ch.Name, Style.Display, 20, Style.GoldHi, false, HorizontalAlignment.Center));
        v.AddChild(Style.Label($"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}", Style.Ui, Style.Caption, Style.InkDim, false, HorizontalAlignment.Center));
        return v;
    }""",
"""    /// <summary>The survivor drawn live, large, on a pool of ember light.</summary>
    public static Control Figure(CharacterData ch, int w = 400, int h = 560)
    {
        var holder = new Control { CustomMinimumSize = new Vector2(w, h), MouseFilter = MouseFilterEnum.Ignore };
        var glow = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.5f, 0.2f, 0.16f), new Color(1, 0.5f, 0.2f, 0) }, Offsets = new[] { 0f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.6f), FillTo = new Vector2(1f, 0.6f), Width = 128, Height = 128,
            },
            Size = new Vector2(w, h), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        holder.AddChild(glow);
        holder.AddChild(new Portrait(new Vector2I(w, h)).Of(Loadouts.Of(ch)));
        return holder;
    }"""),
("""        var card = ItemViews.Card(it, Ch, loc.InPack, acts, 560);
        inspect.AddChild(Style.Scroll(card));""",
"""        var card = ItemViews.Card(it, Ch, loc.InPack, acts, 980);
        inspect.AddChild(Style.Scroll(card));"""),
("""        f.Size = new Vector2(1460, 30);
        foot.AddChild(f);""",
"""        f.Size = new Vector2(1840, 30);
        foot.AddChild(f);"""),
]
for old, new2 in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new2, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
