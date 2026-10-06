R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\GameHud.cs', [
("""    /// <summary>A round medallion rimmed in gold (the ember's, the heart's).</summary>
    static Panel Medal(Control parent, Vector2 at, float size, Color inner)
    {
        var p = new Panel { Position = at, Size = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore };
        var s = Style.Box(inner, Style.GoldDim, 3, (int)(size / 2), 0);
        s.ShadowColor = new Color(1f, 0.55f, 0.2f, 0.35f);
        s.ShadowSize = 10;
        p.AddThemeStyleboxOverride("panel", s);
        parent.AddChild(p);
        return p;
    }""",
"""    /// <summary>A round medallion rimmed in gold (the ember's, the heart's);
    /// painted (hud/NAME.png, drawn larger than the medallion, centred on it) when there is art.</summary>
    static Panel Medal(Control parent, Vector2 at, float size, Color inner, string? art = null)
    {
        var p = new Panel { Position = at, Size = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore };
        var s = Style.Box(inner, Style.GoldDim, 3, (int)(size / 2), 0);
        s.ShadowColor = new Color(1f, 0.55f, 0.2f, 0.35f);
        s.ShadowSize = 10;
        if (art != null && UiArt.Art($"hud/{art}.png") is { } tex)
        {
            p.AddThemeStyleboxOverride("panel", new StyleBoxEmpty());
            var r = new TextureRect { Texture = tex, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore, ShowBehindParent = true };
            r.Size = tex.GetSize();
            r.Position = (new Vector2(size, size) - r.Size) / 2;
            p.AddChild(r);
        }
        else p.AddThemeStyleboxOverride("panel", s);
        parent.AddChild(p);
        return p;
    }

    /// <summary>A bar's fill: painted (bars/NAME.png, stretched along the bar) or the drawn gradient.</summary>
    static TextureRect Fill(string art, Color[] colors, float[] stops, bool vertical = false)
    {
        var r = GradientRect(colors, stops, vertical);
        if (UiArt.Art($"bars/{art}.png") is { } tex) r.Texture = tex;
        return r;
    }"""),
("""        track.AddThemeStyleboxOverride("panel", Style.Box(Hex("#120c0a"), new Color(0.85f, 0.71f, 0.42f, 0.28f), 1, 5, 0));""",
"""        track.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track", Style.Box(Hex("#120c0a"), new Color(0.85f, 0.71f, 0.42f, 0.28f), 1, 5, 0)));"""),
("""        emberFill = GradientRect([Hex("#6a1e04"), Hex("#c24a0a"), Hex("#ff8a2a"), Hex("#ffd070")], [0, 0.45f, 0.85f, 1]);""",
"""        emberFill = Fill("ember_fill", [Hex("#6a1e04"), Hex("#c24a0a"), Hex("#ff8a2a"), Hex("#ffd070")], [0, 0.45f, 0.85f, 1]);"""),
("""        growFill = GradientRect([Hex("#16222e"), Hex("#34587a"), Hex("#86b0d8"), Hex("#e6f2ff")], [0, 0.45f, 0.85f, 1]);""",
"""        growFill = Fill("experience_fill", [Hex("#16222e"), Hex("#34587a"), Hex("#86b0d8"), Hex("#e6f2ff")], [0, 0.45f, 0.85f, 1]);"""),
("""        var medal = Medal(combat, new Vector2(x, 6), 46, Hex("#3a2210"));""",
"""        var medal = Medal(combat, new Vector2(x, 6), 46, Hex("#3a2210"), "medal_level");"""),
("""        bar.AddThemeStyleboxOverride("panel", Style.Box(Hex("#160a0a"), new Color(0.85f, 0.71f, 0.42f, 0.32f), 1, 4, 0));""",
"""        bar.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track", Style.Box(Hex("#160a0a"), new Color(0.85f, 0.71f, 0.42f, 0.32f), 1, 4, 0)));"""),
("""        hpFill = GradientRect([Hex("#ff6a5a"), Hex("#d2262c"), Hex("#8a0e16")], [0, 0.35f, 1], true);""",
"""        hpFill = Fill("health_fill", [Hex("#ff6a5a"), Hex("#d2262c"), Hex("#8a0e16")], [0, 0.35f, 1], true);"""),
("""        var h = Medal(v, new Vector2(0, 30), 41, Hex("#3a0c10"));""",
"""        var h = Medal(v, new Vector2(0, 30), 41, Hex("#3a0c10"), "medal_heart");"""),
("""        abilityRing = new Ring { Size = new Vector2(89, 89), MouseFilter = Control.MouseFilterEnum.Ignore };
        ab.AddChild(abilityRing);""",
"""        abilityRing = new Ring { Size = new Vector2(89, 89), MouseFilter = Control.MouseFilterEnum.Ignore };
        ab.AddChild(abilityRing);
        // The art's ring painted over the drawn one (hud/ring_art.png, a ring with an empty middle).
        if (UiArt.Art("hud/ring_art.png") is { } ringArt)
        {
            var rr = new TextureRect { Texture = ringArt, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore, Size = ringArt.GetSize() };
            rr.Position = (new Vector2(89, 89) - rr.Size) / 2;
            ab.AddChild(rr);
        }"""),
("""        hintBox = Style.Panel(Style.Box(Hex("#e6d6b0"), new Color(0.35f, 0.24f, 0.08f, 0.45f), 1, 4, 14));""",
"""        hintBox = Style.Panel(UiArt.Frame("hint", Style.Box(Hex("#e6d6b0"), new Color(0.35f, 0.24f, 0.08f, 0.45f), 1, 4, 14)));"""),
("""        promptBox = Style.Panel(Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.92f), Style.Line, 1, 24, 10));""",
"""        promptBox = Style.Panel(UiArt.Frame("prompt", Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.92f), Style.Line, 1, 24, 10)));"""),
("""        track.AddThemeStyleboxOverride("panel", Style.Box(Hex("#140808"), Style.GoldDim, 1, 3, 0));""",
"""        track.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track_boss", Style.Box(Hex("#140808"), Style.GoldDim, 1, 3, 0)));"""),
("""            var chip = Style.Panel(Style.Box(new Color(0.04f, 0.03f, 0.05f, 0.8f), col, 1, 13, 5), Style.H(3, Glyphs.Icon(glyph, 17, col), Style.Label($"{Math.Ceiling(left)}", Style.UiBold, 13, col)));""",
"""            var chip = Style.Panel(UiArt.Frame("chip", Style.Box(new Color(0.04f, 0.03f, 0.05f, 0.8f), col, 1, 13, 5)), Style.H(3, Glyphs.Icon(glyph, 17, col), Style.Label($"{Math.Ceiling(left)}", Style.UiBold, Style.Badge, col)));"""),
("""            chip.AddThemeStyleboxOverride("panel", Style.Box(Hex("#1a1720"), col with { A = 0.55f }, 1, bd.Kind == BoonKind.Blessing ? 6 : 17, 0));""",
"""            chip.AddThemeStyleboxOverride("panel", UiArt.Frame("chip", Style.Box(Hex("#1a1720"), col with { A = 0.55f }, 1, bd.Kind == BoonKind.Blessing ? 6 : 17, 0)));"""),
])

edit(r'Ui\UiArt.cs', [
("""        ["plate"] = new("frames/plate.png", 28, 28, 28, 28),
        ["plate_header"] = new("frames/plate_header.png", 40, 20, 40, 20),""",
"""        ["plate"] = new("frames/plate.png", 28, 28, 28, 28),"""),
("""        ["bar_track_boss"] = new("bars/track_boss.png", 24, 8, 24, 8),
        ["minimap_frame"] = new("minimap/frame.png", 0, 0, 0, 0),""",
"""        ["bar_track_boss"] = new("bars/track_boss.png", 24, 8, 24, 8),
        ["map_frame"] = new("frames/map_frame.png", 20, 20, 20, 20),"""),
])

edit(r'Ui\MapScreen.cs', [
("""        frame.AddThemeStyleboxOverride("panel", Style.Box(new Color("#d9cba8"), new Color("#5a3e24"), 2, 3, 0));""",
"""        frame.AddThemeStyleboxOverride("panel", UiArt.Frame("map_frame", Style.Box(new Color("#d9cba8"), new Color("#5a3e24"), 2, 3, 0)));"""),
])

edit(r'Ui\ArtsScreen.cs', [
("""        if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4));
        var tint""",
"""        if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
        var tint"""),
("""            if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.EmberHi, 2, 4));""",
"""            if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.EmberHi, 2, 4)));"""),
("""        if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4));
        var col = ItemViews""",
"""        if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
        var col = ItemViews"""),
])

edit(r'Ui\Front.cs', [
("""        var brand = Style.V(2);
        brand.Position = new Vector2(134, 140);
        brand.AddChild(Style.Label("A tale of the Ember Watch", Style.TextItalic, 19, new Color("#c8a878")));
        var b1 = Style.Label("SURVIVOR", Style.Display, 92, new Color("#f0c878"));
        b1.AddThemeConstantOverride("outline_size", 0);
        brand.AddChild(b1);
        brand.AddChild(Style.Label("U N C H A I N E D", Style.Display, 54, new Color("#d8a050")));""",
"""        var brand = Style.V(2);
        brand.Position = new Vector2(134, 140);
        brand.AddChild(Style.Label("A tale of the Ember Watch", Style.TextItalic, 19, new Color("#c8a878")));
        // The painted logo (title/logo.png) when there is one; else the name set in Cinzel.
        if (UiArt.Art("title/logo.png") is { } logo)
            brand.AddChild(new TextureRect { Texture = logo, CustomMinimumSize = logo.GetSize(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspect, MouseFilter = MouseFilterEnum.Ignore });
        else
        {
            var b1 = Style.Label("SURVIVOR", Style.Display, 92, new Color("#f0c878"));
            b1.AddThemeConstantOverride("outline_size", 0);
            brand.AddChild(b1);
            brand.AddChild(Style.Label("U N C H A I N E D", Style.Display, 54, new Color("#d8a050")));
        }"""),
])

edit(r'Ui\Overlay.cs', [
("""            if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab_on", Style.Box(new Color("#3a2614"), Style.LineHi, 1, 4)));""",
"""            if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab_on", Style.Box(new Color("#3a2614"), Style.LineHi, 1, 4)));
            else if (UiArt.Has("tab")) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab", new StyleBoxEmpty()));"""),
])

# A flourish under the big headings: the draft, the arena's end, the chapter's end.
edit(r'Ui\Style.cs', [
("""    /// <summary>A darkening over the game behind an overlay; a click on it closes.</summary>""",
"""    /// <summary>The ornament under a great heading (ornaments/flourish.png), or nothing.</summary>
    public static Control Flourish()
    {
        if (UiArt.Art("ornaments/flourish.png") is not { } art) return Gap(0);
        return new TextureRect { Texture = art, CustomMinimumSize = art.GetSize(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = Control.MouseFilterEnum.Ignore, SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter };
    }

    /// <summary>A darkening over the game behind an overlay; a click on it closes.</summary>"""),
])
edit(r'Ui\Panels.cs', [
("""        col.AddChild(Style.Label(head.ToUpperInvariant(), Style.Display, 48, new Color("#ffe6b8"), false, HorizontalAlignment.Center));""",
"""        col.AddChild(Style.Label(head.ToUpperInvariant(), Style.Display, 48, new Color("#ffe6b8"), false, HorizontalAlignment.Center));
        col.AddChild(Style.Flourish());"""),
])
edit(r'Ui\ArenaResult.cs', [
("""        wrap.AddChild(Style.Label(r.Spec.Name, Style.Display, 48, Style.GoldHi, false, HorizontalAlignment.Center));""",
"""        wrap.AddChild(Style.Label(r.Spec.Name, Style.Display, 48, Style.GoldHi, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Flourish());"""),
])
edit(r'Ui\Menus.cs', [
("""        wrap.AddChild(Style.Label("The Waystation", Style.Display, 52, Style.GoldHi, false, HorizontalAlignment.Center));""",
"""        wrap.AddChild(Style.Label("The Waystation", Style.Display, 52, Style.GoldHi, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Flourish());"""),
])

# The minimap's arrow, painted when there is one.
edit(r'Ui\Minimap.cs', [
("""        AddChild(you);""",
"""        AddChild(you);
        // A painted arrow (minimap/you.png, pointing up, 24 by 24 shown) in place of the drawn one.
        if (UiArt.Art("minimap/you.png") is { } arrow)
        {
            you.Color = Colors.Transparent;
            var a = new TextureRect { Texture = arrow, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = MouseFilterEnum.Ignore, Size = arrow.GetSize() };
            a.Position = -a.Size / 2;
            you.AddChild(a);
        }"""),
])
print('done')
