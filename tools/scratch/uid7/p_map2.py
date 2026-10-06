PAIRS = [
("""        var scroll = Style.Scroll(list);
        col.AddChild(scroll);
        col.AddChild(Kit.RuleH());""",
"""        // The list hugs its lines, and scrolls only past the room the column has (one line on the
        // Verge stood over a column of nothing, its legend at the foot).
        var scroll = Style.Scroll(list);
        scroll.SizeFlagsVertical = SizeFlags.Fill;
        col.AddChild(scroll);
        col.AddChild(Kit.RuleH());"""),
("""        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim, true));
    }""",
"""        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim));
        // (none of the list's words wrap, so its height is known before it is laid out)
        float room = ListAt.Size.Y - col.GetCombinedMinimumSize().Y;
        scroll.CustomMinimumSize = new Vector2(0, Math.Min(list.GetCombinedMinimumSize().Y, Math.Max(120, room)));
    }"""),
]
