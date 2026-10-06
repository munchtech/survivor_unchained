R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\Ornate.cs', [
("""        label = Style.Label(text.ToUpperInvariant(), Style.Display, size, color ?? Style.GoldHi, false, HorizontalAlignment.Center);
        AddChild(label);
        var ls = label.GetCombinedMinimumSize();
        CustomMinimumSize = new Vector2(ls.X + rule * 2 + 40, ls.Y);
        label.Position = new Vector2(rule + 20, 0);""",
"""        var up = text.ToUpperInvariant();
        label = Style.Label(up, Style.Display, size, color ?? Style.GoldHi, false, HorizontalAlignment.Center);
        AddChild(label);
        // Measured from the face itself: a label not yet in the tree does not know its size.
        var ts = Style.Display.GetStringSize(up, HorizontalAlignment.Left, -1, size);
        CustomMinimumSize = new Vector2(ts.X + rule * 2 + 56, size * 1.35f);
        label.Position = new Vector2(rule + 28, 0);
        label.Size = new Vector2(ts.X, size * 1.35f);"""),
("""        float l = rule + 8, r = w - rule - 8;""",
"""        float l = rule + 14, r = w - rule - 14;"""),
])

edit(r'Ui\Pack.cs', [
("""        var well = Style.Panel(Style.Well(12));
        well.AddChild(ItemViews.Grid(ch.Pack, 8, 112, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, SetupCell));""",
"""        var well = Style.Panel(Style.Well(12));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        centre.AddChild(ItemViews.Grid(ch.Pack, 8, 112, it => it.Uid == sel, null, it => Select(it.Uid), Primary, Hover, "pack", Leave, SetupCell));
        well.AddChild(centre);"""),
("""        var view = ItemViews.Slot(it, 96, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,""",
"""        var view = ItemViews.Slot(it, 104, it != null && it.Uid == sel, null, false, it != null ? () => Select(it.Uid) : null, off,"""),
("""    public static Control Figure(CharacterData ch, int w = 400, int h = 560)""",
"""    public static Control Figure(CharacterData ch, int w = 420, int h = 620)"""),
])
print('done')
