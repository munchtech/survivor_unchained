PAIRS = [
("""    static void Mark(Control parent, Vector2 at, string label, MarkKind kind)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Minimap.Mark(kind, 22);
            icon.Position = new Vector2(-11, -11);
            node.AddChild(icon);
        }
        var l = Style.Label(label, place ? Style.Display : Style.TextBold, place ? 16 : 15, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);
        l.AddThemeColorOverride("font_outline_color", new Color("#e4d6b6"));
        l.AddThemeConstantOverride("outline_size", 5);
        l.Size = new Vector2(240, 22);
        l.Position = new Vector2(-120, place ? -11 : 12);
        node.AddChild(l);
        parent.AddChild(node);
    }
""",
"""    /// <summary>Each mark's name on the drawing: where its mark stands, the words, what it is, how wide.</summary>
    readonly List<(Control Node, Label Text, MarkKind Kind, float W)> names = new();

    void Mark(Control parent, Vector2 at, string label, MarkKind kind)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Minimap.Mark(kind, 22);
            icon.Position = new Vector2(-11, -11);
            node.AddChild(icon);
        }
        var font = place ? Style.Display : Style.TextBold;
        int size = place ? 16 : 15;
        var l = Style.Label(label, font, size, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);
        l.AddThemeColorOverride("font_outline_color", new Color("#e4d6b6"));
        l.AddThemeConstantOverride("outline_size", 5);
        float w = font.GetStringSize(label, HorizontalAlignment.Left, -1, size).X + 8;
        l.Size = new Vector2(w, 22);
        l.Position = new Vector2(-w / 2, place ? -11 : 12);
        node.AddChild(l);
        parent.AddChild(node);
        names.Add((node, l, kind, w));
    }

    /// <summary>
    /// The names set clear of one another and of every mark, at the size they are read (two names
    /// printed over each other read as neither: "WENI Old Wenna"). A place keeps its name on its
    /// roof if it can, above or below it if not; then the way out and who needs you, then people,
    /// each under its mark, or above it, or to a side; a name with nowhere to go is left to the list.
    /// </summary>
    void Declutter()
    {
        var taken = new List<Rect2>();
        foreach (var (node, _, kind, _) in names)
            if (kind != MarkKind.Place) taken.Add(new Rect2(node.GlobalPosition - new Vector2(11, 11), new Vector2(22, 22)));
        static int Order(MarkKind k) => k == MarkKind.Place ? 0 : k is MarkKind.Quest or MarkKind.Exit ? 1 : k == MarkKind.Person ? 2 : 3;
        foreach (var (node, text, kind, w) in names.OrderBy(n => Order(n.Kind)))
        {
            Vector2[] spots = kind == MarkKind.Place
                ? [new(-w / 2, -11), new(-w / 2, -33), new(-w / 2, 11)]
                : [new(-w / 2, 12), new(-w / 2, -34), new(15, -11), new(-w - 15, -11)];
            text.Visible = false;
            foreach (var at in spots)
            {
                var r = new Rect2(node.GlobalPosition + at + new Vector2(2, 3), new Vector2(w - 4, 16));
                if (taken.Any(t => t.Intersects(r))) continue;
                taken.Add(r);
                text.Position = at;
                text.Visible = true;
                break;
            }
        }
    }
"""),
("""        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not ColorRect && mk is not MapInk && mk != ring) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
    }""",
"""        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not ColorRect && mk is not MapInk && mk != ring) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
        Declutter();
    }"""),
]
