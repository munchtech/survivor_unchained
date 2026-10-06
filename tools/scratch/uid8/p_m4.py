PAIRS = [
("""        AddChild(shade);
        var col = Fitted(new Vector2(Inset, Inset), W);
        col.AddChild(new Title("Paused", 30, false));""", """        AddChild(shade);
        // The panel and, when open, its settings or controls beside it, side by side with the same
        // gap as the screen's edge: each as wide as it needs (the book's chain sets the pause's).
        var pair = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(Inset, Inset) };
        pair.AddThemeConstantOverride("separation", (int)Inset);
        AddChild(pair);
        var col = Plate(pair, W);
        col.AddChild(new Title("Paused", 30, false));"""),
("""            var side = Fitted(new Vector2(Inset * 2 + W, Inset), panel == "controls" ? 880 : 780);""", """            var side = Plate(pair, panel == "controls" ? 600 : 780);"""),
("""    public override bool Key(Act a)
    {
        if (panel != "")
        {
            // Back from a panel; inside it, focus moves over its rows.
            if (a is Act.Cancel or Act.Pause) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }
}

/// <summary>
/// A night at the Last Lamp""", """    /// <summary>A fitted panel in a row of them: as tall as what it holds, its ground a little
    /// see-through, the same margin on every side. Returns its column.</summary>
    static VBoxContainer Plate(Control row, float width)
    {
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.CustomMinimumSize = new Vector2(width, 0);
        panel.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        row.AddChild(panel);
        var v = Style.V(Style.Gap4);
        panel.AddChild(v);
        return v;
    }

    public override bool Key(Act a)
    {
        if (panel != "")
        {
            // Back from a panel; inside it, focus moves over its rows.
            if (a is Act.Cancel or Act.Pause) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }
}

/// <summary>
/// A night at the Last Lamp"""),
("""            height = Math.Clamp(need + OpenBook.Chrome + 16, MinH, MaxH);""", """            // (the Journal's chrome less the foot line its leaves carry, which this book has not)
            height = Math.Clamp(need + OpenBook.Chrome - 14, MinH, MaxH);"""),
]
