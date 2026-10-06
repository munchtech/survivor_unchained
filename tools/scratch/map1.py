p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\MapScreen.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""/// out and what the journal told you always are). The wheel zooms, a drag
/// pans, M or Escape puts it away.
/// </summary>""",
"""/// out and what the journal told you always are). The wheel zooms, a drag
/// pans, M or Escape puts it away; with a pad, the stick or the D-pad pans
/// and the triggers zoom.
/// </summary>"""),
("""    protected override void Build()
    {
        var scene = G.Scene!;
        var zone = G.Zone!;
        var meta = scene.Data.Meta;
        float extent = Extent(meta);
        AddChild(Style.Scrim(G.CloseOverlay, 0.7f));
        var sheet = Style.Centered(Style.V(6), new Vector2(760, 860));
        AddChild(sheet);
        sheet.AddChild(Style.Label(zone.Name, Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center));
        if (zone.Region != null) sheet.AddChild(Style.Label(zone.Region, Style.TextItalic, 16, Style.InkDim, false, HorizontalAlignment.Center));
        const int Frame = 740;
        var frame = new Panel { CustomMinimumSize = new Vector2(Frame, Frame), ClipContents = true, MouseFilter = MouseFilterEnum.Stop };""",
"""    /// <summary>Pan with the D-pad or the stick, zoom with the triggers (or , and .).</summary>
    public override bool Key(Act a)
    {
        const int F = 740;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right:
                var d = a switch { Act.Up => new Vector2(0, 1), Act.Down => new Vector2(0, -1), Act.Left => new Vector2(1, 0), _ => new Vector2(-1, 0) } * (0.06f / zoom);
                pan = new Vector2(Math.Clamp(pan.X + d.X, -0.5f, 0.5f), Math.Clamp(pan.Y + d.Y, -0.5f, 0.5f));
                Place(F);
                return true;
            case Act.SubNext: zoom = Math.Min(3.5f, zoom * 1.25f); Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(1, zoom / 1.25f); Place(F); return true;
        }
        return false;
    }

    protected override void Build()
    {
        var scene = G.Scene!;
        var zone = G.Zone!;
        var meta = scene.Data.Meta;
        float extent = Extent(meta);
        AddChild(Style.Scrim(G.CloseOverlay, 0.7f));
        var sheet = Style.Centered(Style.V(6), new Vector2(760, 880));
        AddChild(sheet);
        BookTabs(new Vector2((1920 - 760) / 2, (1080 - 880) / 2 - 40));
        sheet.AddChild(Style.Label(zone.Name, Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center));
        if (zone.Region != null) sheet.AddChild(Style.Label(zone.Region, Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center));
        const int Frame = 740;
        // Exactly its size: a frame stretched wider shows the ink past the fog's edge.
        var frame = new Panel { CustomMinimumSize = new Vector2(Frame, Frame), SizeFlagsHorizontal = SizeFlags.ShrinkCenter, ClipContents = true, MouseFilter = MouseFilterEnum.Stop };"""),
("""        foreach (var m in zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).OrderByDescending(m => m.Kind == MarkKind.Place))
        {
            var (glyph, color) = m.Kind switch
            {
                MarkKind.Quest or MarkKind.Turn => ("quest", new Color("#a8321e")), MarkKind.Danger => ("skull", new Color("#6a1a10")),
                MarkKind.Mystery => ("eye", new Color("#5a3a7a")), MarkKind.Exit => ("next", new Color("#2a4a3a")), MarkKind.Person => ("talk", new Color("#3a2414")),
                _ => ("map", new Color("#3a2414")),
            };
            Mark(marks, Px(m.X, m.Z), m.Label, glyph, color, m.Kind == MarkKind.Place);
        }
        if (G.Journey.World.Corpse is { } corpse && corpse.Zone == zone.Id) Mark(marks, Px(corpse.X, corpse.Z), $"{corpse.HeroName}'s belongings", "skull", new Color("#6a1a10"), false);""",
"""        foreach (var m in zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).OrderByDescending(m => m.Kind == MarkKind.Place))
            Mark(marks, Px(m.X, m.Z), m.Label, m.Kind);
        if (G.Journey.World.Corpse is { } corpse && corpse.Zone == zone.Id) Mark(marks, Px(corpse.X, corpse.Z), $"{corpse.HeroName}'s belongings", MarkKind.Danger);"""),
("""        var foot = Style.H(16);
        foreach (var (glyph, text) in new[] { ("quest", "Someone needs you"), ("skull", "Hostile"), ("eye", "Unexplained"), ("next", "The way out") })
            foot.AddChild(Style.H(4, Glyphs.Icon(glyph, 14, Style.GoldHi), Style.Label(text, Style.Ui, 14, Style.Ink)));
        foot.AddChild(Style.Label($"{G.Key(Act.Map)} close · wheel to zoom · drag to move", Style.Ui, 13, Style.InkDim));
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        sheet.AddChild(foot);""",
"""        // The legend, in the marks' own look (the corner map's too).
        var foot = Style.H(16);
        foreach (var (kind, text) in new[] { (MarkKind.Quest, "Someone needs you"), (MarkKind.Danger, "Hostile"), (MarkKind.Mystery, "Unexplained"), (MarkKind.Exit, "The way out") })
            foot.AddChild(Style.H(5, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        sheet.AddChild(foot);
        sheet.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Up, "Move"), (Act.SubNext, "Closer"), (Act.SubPrev, "Further"), (Act.Cancel, "Close"))
            : MouseFooter($"{G.Key(Act.Map)} to close", "wheel to zoom", "drag to move"));"""),
("""    static void Mark(Control parent, Vector2 at, string label, string glyph, Color color, bool place)
    {
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Glyphs.Icon(glyph, 16, color);
            icon.Position = new Vector2(-8, -8);
            icon.Size = new Vector2(16, 16);
            node.AddChild(icon);
        }
        var l = Style.Label(label, place ? Style.Display : Style.TextBold, place ? 14 : 13, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);""",
"""    static void Mark(Control parent, Vector2 at, string label, MarkKind kind)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Minimap.Mark(kind, 20);
            icon.Position = new Vector2(-10, -10);
            node.AddChild(icon);
        }
        var l = Style.Label(label, place ? Style.Display : Style.TextBold, place ? 15 : 14, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);"""),
("""        l.Size = new Vector2(220, 18);
        l.Position = new Vector2(-110, place ? -9 : 9);""",
"""        l.Size = new Vector2(220, 20);
        l.Position = new Vector2(-110, place ? -10 : 11);"""),
]
for old, new in pairs:
    assert old in s, old[:90]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
