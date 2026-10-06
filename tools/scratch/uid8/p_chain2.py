PAIRS = [
("""        if (pad) row.AddChild(Style.PadButton("LB"));
        else if (ends is { } e0) row.AddChild(Style.Key(e0.Prev));
        for (int i = 0; i < tabs.Length; i++)""", """        if (pad) row.AddChild(Style.PadButton("LB"));
        for (int i = 0; i < tabs.Length; i++)"""),
("""        if (pad) row.AddChild(Style.PadButton("RB"));
        else if (ends is { } e1) row.AddChild(Style.Key(e1.Next));
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(row);""", """        if (pad) row.AddChild(Style.PadButton("RB"));
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(row);
        // The turning keys outside the eyes, level with the names (laid out once in the tree, where
        // the caps measure as they are drawn).
        if (!pad && ends is { } e)
        {
            caps = (Style.Key(e.Prev), Style.Key(e.Next));
            AddChild(caps.Value.L);
            AddChild(caps.Value.R);
        }"""),
("""        float first = row.GetChildren().OfType<Button>().FirstOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20;
        float inset = F.Eye ? Math.Max(0, Run + F.Tail + 26 - first) : 0;
        row.Position = new Vector2(inset, 0);
        CustomMinimumSize = new Vector2(min.X + inset, chainY + 22);
    }
""", """        // (the same at the last tab, so a chain set in the middle of a panel is centred, eyes and all)
        var buttons = row.GetChildren().OfType<Button>().ToList();
        float first = buttons.FirstOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20, last = buttons.LastOrDefault()?.GetCombinedMinimumSize().X / 2 ?? 20;
        insetL = F.Eye ? Math.Max(0, Run + F.Tail + 26 - first) : 0;
        insetR = F.Eye ? Math.Max(0, Run + F.Tail + 26 - last) : 0;
        row.Position = new Vector2(insetL, 0);
        CustomMinimumSize = new Vector2(min.X + insetL + insetR, chainY + 22);
    }

    (Control L, Control R)? caps;
    float insetL, insetR;

    public override void _Ready()
    {
        if (caps is not { } c) return;
        // The caps' own room each side, the row stepped in past the left one, the right one past the eye.
        var min = row.GetCombinedMinimumSize();
        var ls = c.L.GetCombinedMinimumSize();
        var rs = c.R.GetCombinedMinimumSize();
        const float gap = 6;
        row.Position = new Vector2(ls.X + gap + insetL, 0);
        c.L.Position = new Vector2(0, (min.Y - ls.Y) / 2);
        c.R.Position = new Vector2(ls.X + gap + insetL + min.X + insetR + gap, (min.Y - rs.Y) / 2);
        CustomMinimumSize = new Vector2(c.R.Position.X + rs.X, CustomMinimumSize.Y);
    }
"""),
]
