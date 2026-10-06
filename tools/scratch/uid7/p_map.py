PAIRS = [
("""    /// <summary>The drawing's size at zoom 1, and the part of the screen the map shows through
    /// (the list stands over the rest).</summary>
    const int F = 1080;
    static readonly Rect2 View = new(0, 96, 1440, 984);""",
"""    /// <summary>The drawing's size at zoom 1; the map's window and the list beside it, the two
    /// centred on the page together between its bands (the sheet sat in the middle of all but the
    /// list, a band of bare table either side of it and another before the list, which kept to the
    /// screen's edge).</summary>
    const int F = 1080;
    const float ListW = 440, Between = 32;
    static readonly Rect2 View = new((1920 - 1040 - Between - ListW) / 2, 112, 1040, 904);
    static Rect2 ListAt => new(View.End.X + Between, View.Position.Y, ListW, View.Size.Y);"""),
("""        // The map is the screen: under the header band and the list, over the dark.
        var frame = new Control { Position = Vector2.Zero, Size = new Vector2(1920, 1080), ClipContents = true, MouseFilter = MouseFilterEnum.Stop };""",
"""        // The map in its window: the sheet on the table, cut cleanly at the window's edge.
        var frame = new Control { Position = View.Position, Size = View.Size, ClipContents = true, MouseFilter = MouseFilterEnum.Stop };"""),
("""            Size = new Vector2(1920, 1080), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        });
        world = new Control""",
"""            Size = View.Size, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        });
        world = new Control"""),
("""        // A compass in the corner, the way the old maps had one.
        var rose = Glyphs.Icon("compass", 72, Style.Gold with { A = 0.75f });
        rose.Position = new Vector2(36, 120);
        AddChild(rose);
        var north = Style.Label("N", Style.Display, 18, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Position = new Vector2(36, 96);
        north.Size = new Vector2(72, 22);
        AddChild(north);
""",
"""        // A compass in the window's corner, the way the old maps had one.
        var rose = Glyphs.Icon("compass", 64, Style.Gold with { A = 0.75f });
        rose.Position = View.Position + new Vector2(22, 40);
        AddChild(rose);
        var north = Style.Label("N", Style.Display, 18, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Position = View.Position + new Vector2(22, 16);
        north.Size = new Vector2(64, 22);
        AddChild(north);
"""),
("""        // The list: where to go, what has been found, what to beware of; each line glides the map to it.
        var col = Pane(page, new Rect2(1420, 0, 420, 920), Style.Column(18), Style.Gap2);
        col.AddChild(new Section("Where to go", "nearest first"));
        var list = Style.V(2);""",
"""        // The list beside it, as type on the page (its lines were boxes): where to go, what has been
        // found, what to beware of; each line glides the map to it.
        var col = Style.V(Style.Gap3);
        col.Position = ListAt.Position - page.Position;
        col.Size = ListAt.Size;
        page.AddChild(col);
        col.AddChild(Kit.Head("Where to go", "nearest first"));
        var list = Style.V(0);"""),
("""            if (!first) list.AddChild(Style.Gap(Style.Gap2));
            first = false;
            list.AddChild(Style.SubLabel(title));""",
"""            if (!first) list.AddChild(Style.Gap(Style.Gap4));
            first = false;
            list.AddChild(Style.Label(title.ToUpperInvariant(), Style.UiHeavy, 12, Kit.HeadInk, false, HorizontalAlignment.Left, false));"""),
("""        var scroll = Style.Scroll(list);
        col.AddChild(scroll);
        col.AddChild(Style.Rule());""",
"""        var scroll = Style.Scroll(list);
        col.AddChild(scroll);
        col.AddChild(Kit.RuleH());"""),
("""        // The prompts in the list's foot: under the map they would sit on the drawing.
        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim, true));

        // Zoom and find-me, at the map's foot, where the hand is.
        var tools = Style.Panel(Style.Slab(8));
        tools.Position = new Vector2(40, 1000);
        AddChild(tools);
        var tr = Style.H(Style.Gap2);
        tools.AddChild(tr);
        Button Tool(string glyph, string? pad, string text, Action go)
        {
            var bt = Style.Button("", go, false, true);
            var r = Style.H(6, pad != null && Controls.Instance.UsingPad ? Style.PadButton(pad) : Glyphs.Icon(glyph, 16, Style.GoldHi), Style.Label(text, Style.UiBold, Style.Small, Style.GoldHi));
            r.MouseFilter = MouseFilterEnum.Ignore;
            r.Position = new Vector2(10, 5);
            bt.AddChild(r);
            bt.CustomMinimumSize = new Vector2(r.GetCombinedMinimumSize().X + 22, 34);
            return Nav.Skip(bt);
        }
        tr.AddChild(Tool("crosshair", "Y", "Find me", FindMe));
        tr.AddChild(Tool("expand", "RT", "Closer", () => Key(Act.SubNext)));
        tr.AddChild(Tool("expand", "LT", "Further", () => Key(Act.SubPrev)));
        tr.AddChild(Tool("map", null, "All I know", () => { Fit(seen); gliding = false; Place(F); }));
    }""",
"""        // Zoom and find-me as words in the list's foot (they were a slab of buttons on the drawing),
        // then the prompts.
        var tools = Style.H(Style.Gap4);
        Control Tool(string? pad, string text, Action go)
        {
            var wd = Kit.Word(text, go, Style.GoldHi, 15);
            if (pad == null || !Controls.Instance.UsingPad) return Nav.Skip(wd);
            var r = Style.H(6, Style.PadButton(pad), Nav.Skip(wd));
            foreach (var c in r.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            return r;
        }
        tools.AddChild(Tool("Y", "Find me", FindMe));
        tools.AddChild(Tool("RT", "Closer", () => Key(Act.SubNext)));
        tools.AddChild(Tool("LT", "Further", () => Key(Act.SubPrev)));
        tools.AddChild(Tool(null, "All I know", () => { Fit(seen); gliding = false; Place(F); }));
        col.AddChild(tools);
        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim, true));
    }"""),
("""    /// <summary>A line of the list: its mark, its name, how far and which way from you.</summary>
    Control Line(Entry e, Vector2 at)
    {
        var b = Style.Button("", () => { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }, false, true);
        var row = Style.H(8, Minimap.Mark(e.Kind, 18), Style.Label(e.Label, Style.UiBold, Style.Small, Style.Ink));
        if (G.Battle?.Player is { } p)
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            row.AddChild(Style.Label(d < 8 ? "here" : $"{Math.Round(d / 5) * 5:0} m {Way(dx, dz)}", Style.TextItalic, Style.Caption, Style.InkDim));
        }
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(10, 6);
        b.AddChild(row);
        b.CustomMinimumSize = new Vector2(0, 36);
        b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        Nav.Mark(b, $"mark:{e.Label}", () => { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }, focus: () => Glide(e.X, e.Z, at));
        b.MouseEntered += () => Glide(e.X, e.Z, at);
        return b;
    }""",
"""    /// <summary>A line of the list as type over a fine rule (no box): its mark and its name, and in
    /// a column at the right how far and which way from you, so the distances line up and are
    /// scanned. The pointer lights the name in ember and glides the map to it.</summary>
    Control Line(Entry e, Vector2 at)
    {
        void Go() { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }
        var b = new Button { Flat = true, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 34), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        foreach (var s in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(s, new LineUnder());
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        var name = Style.Label(e.Label, Style.UiBold, Style.Small, Style.Ink);
        name.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        name.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        var row = Style.H(10, Minimap.Mark(e.Kind, 18), name);
        if (G.Battle?.Player is { } p)
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            row.AddChild(Style.Label(d < 8 ? "here" : $"{Math.Round(d / 5) * 5:0} m {Way(dx, dz)}", Style.TextItalic, Style.Caption, Style.InkDim, false, HorizontalAlignment.Right));
        }
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        b.AddChild(row);
        b.Pressed += Go;
        Nav.Mark(b, $"mark:{e.Label}", Go, focus: () => Glide(e.X, e.Z, at));
        b.MouseEntered += () => { name.AddThemeColorOverride("font_color", Style.EmberHi); Glide(e.X, e.Z, at); };
        b.MouseExited += () => name.AddThemeColorOverride("font_color", Style.Ink);
        return b;
    }"""),
("""        // The point the pan names sits at the middle of the part of the screen the map shows through.
        var centre = View.Position + View.Size / 2;""",
"""        // The point the pan names sits at the middle of the map's window.
        var centre = View.Size / 2;"""),
]
