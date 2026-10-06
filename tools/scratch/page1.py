R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\Style.cs', [
("""    /// <summary>An iron plate with a gold hairline and a shadow under it.</summary>
    public static StyleBox Plate(int pad = 18)
    {
        var b = Box(new Color(0.09f, 0.08f, 0.105f, 0.97f), Line, 1, 6, pad);
        b.ShadowColor = new Color(0, 0, 0, 0.6f);
        b.ShadowSize = 18;
        b.ShadowOffset = new Vector2(0, 6);
        return UiArt.Frame("plate", b);
    }

    public static StyleBox Paper(int pad = 22)
    {
        var b = Box(new Color("#e4d6b6"), new Color(0.35f, 0.24f, 0.08f, 0.35f), 1, 4, pad);
        b.ShadowColor = new Color(0, 0, 0, 0.6f);
        b.ShadowSize = 18;
        return UiArt.Frame("paper", b);
    }""",
"""    /// <summary>A forged iron plate: gradient, bevel, inset hairline, bracketed corners (Ornate.cs).</summary>
    public static StyleBox Plate(int pad = 18) => UiArt.Frame("plate", OrnateBox.Make(OrnateBox.Kind.Plate, pad));

    public static StyleBox Paper(int pad = 22) => UiArt.Frame("paper", OrnateBox.Make(OrnateBox.Kind.Paper, pad));

    /// <summary>Iron sunk into a plate: where a grid or a list sits.</summary>
    public static StyleBox Well(int pad = 12) => UiArt.Frame("well", OrnateBox.Make(OrnateBox.Kind.Well, pad));

    /// <summary>A quieter plate inside a plate (a group, a card's body).</summary>
    public static StyleBox Slab(int pad = 14) => UiArt.Frame("slab", OrnateBox.Make(OrnateBox.Kind.Slab, pad));"""),
])

edit(r'Ui\UiArt.cs', [
("""        ["paper"] = new("frames/paper.png", 32, 32, 32, 32),""",
"""        ["paper"] = new("frames/paper.png", 32, 32, 32, 32),
        ["well"] = new("frames/well.png", 12, 12, 12, 12),
        ["slab"] = new("frames/slab.png", 14, 14, 14, 14),
        ["header"] = new("frames/header.png", 0, 0, 0, 12),
        ["banner"] = new("frames/banner.png", 24, 14, 24, 14),"""),
])

edit(r'Ui\Overlay.cs', [
("""    /// <summary>Close, with its key: a pad shows B, the keyboard the screen's own key.</summary>""",
"""    /// <summary>
    /// A full-screen page (docs/UI_DESIGN.md, "The page"): the world dark
    /// behind, a header band across the top with the book's tabs at the left,
    /// the page's title plaque in the middle and Close at the right; returns
    /// the content area, 1840 by 920 at (40, 112). Screens lay their panes in
    /// it with <see cref="Pane"/>.
    /// </summary>
    protected Control Page(string title, string? sub = null, Action? close = null, string? closeKey = null)
    {
        AddChild(new Backdrop());
        var band = Style.Panel(UiArt.Frame("header", OrnateBox.Make(OrnateBox.Kind.Slab, 0)));
        band.Position = new Vector2(-4, -4);
        band.Size = new Vector2(1928, 100);
        band.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(band);
        if (InBook) BookTabs(new Vector2(40, 30));
        var plaque = new Plaque(title, 34, 120);
        AddChild(plaque);
        plaque.Position = new Vector2((1920 - plaque.CustomMinimumSize.X) / 2, sub != null ? 14 : 26);
        if (sub != null)
        {
            var s = Style.Label(sub, Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center);
            s.Position = new Vector2(360, 58);
            s.Size = new Vector2(1200, 24);
            AddChild(s);
        }
        var btn = Nav.Skip(CloseButton(closeKey ?? (Toggle is Act t ? G.Key(t) : "Esc"), close ?? G.CloseOverlay));
        btn.Position = new Vector2(1880 - btn.CustomMinimumSize.X, 30);
        AddChild(btn);
        var content = new Control { Position = new Vector2(40, 112), Size = new Vector2(1840, 920), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(content);
        return content;
    }

    /// <summary>A pane on a page: an ornate frame at a place, with a column inside it.</summary>
    protected static VBoxContainer Pane(Control parent, Rect2 at, StyleBox? box = null, int gap = Style.Gap3)
    {
        var p = Style.Panel(box ?? Style.Plate(20));
        p.Position = at.Position;
        p.Size = at.Size;
        p.MouseFilter = MouseFilterEnum.Ignore;
        parent.AddChild(p);
        var v = Style.V(gap);
        p.AddChild(v);
        return v;
    }

    /// <summary>The page's footer of prompts, under the content area.</summary>
    protected void PageFooter(Control row)
    {
        if (row is BoxContainer b) b.Alignment = BoxContainer.AlignmentMode.Center;
        if (row is Label l) l.HorizontalAlignment = HorizontalAlignment.Center;
        row.Position = new Vector2(40, 1040);
        row.Size = new Vector2(1840, 32);
        AddChild(row);
    }

    /// <summary>Close, with its key: a pad shows B, the keyboard the screen's own key.</summary>"""),
])
print('done')
