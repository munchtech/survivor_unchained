PAIRS = [
("""        var v = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        v.AddThemeConstantOverride("separation", Style.Gap2);
        var mark = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mark.AddChild(Glyphs.Icon(glyph, 40, refused != null ? Quiet : primary ? Style.EmberHi : Style.GoldHi));
        v.AddChild(mark);
        var word""", """        var v = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        v.AddThemeConstantOverride("separation", Style.Gap2);
        var word"""),
("""    Control Choice(string glyph, string title, string text, string? price, string? refused, Action go, bool primary, string id)""", """    Control Choice(string title, string text, string? price, string? refused, Action go, bool primary, string id)"""),
("""            Choice("moon", "Sleep until morning",""", """            Choice("Sleep until morning","""),
("""            row.Add(Choice("hourglass", "Wait until nightfall",""", """            row.Add(Choice("Wait until nightfall","""),
("""        row.Add(Choice("next", "Not yet",""", """        row.Add(Choice("Not yet","""),
("""    /// <summary>One of the lamp's choices as type: its mark, its key and its name, what it means,""", """    /// <summary>One of the lamp's choices as type: its key and its name, what it means,"""),
("""        AddChild(Hush(report == null ? G.CloseOverlay : null));""", """        // (lighter in the morning: the night is over)
        AddChild(Hush(report == null ? G.CloseOverlay : null, report == null ? 1 : 0.6f));"""),
("""    static TextureRect Hush(Action? click)
    {""", """    static TextureRect Hush(Action? click, float depth)
    {"""),
("""                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.025f, 0.32f), new Color(0.02f, 0.015f, 0.025f, 0.72f) }, Offsets = new[] { 0f, 1f } },""", """                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.025f, 0.32f * depth), new Color(0.02f, 0.015f, 0.025f, 0.72f * depth) }, Offsets = new[] { 0f, 1f } },"""),
("""        var (up, _) = WorldType.Keyed(Act.Confirm, "Get up", Style.Display, 27, Style.EmberHi, G.FinishRest);""", """        var (up, _) = WorldType.Keyed(Act.Confirm, "GET UP", Style.Display, 27, Style.EmberHi, G.FinishRest);"""),
("""        var (walk, _) = WorldType.Keyed(Act.Confirm, "Keep walking", Style.Display, 22, Style.EmberHi, G.CloseOverlay);
        var (fire, _) = WorldType.Keyed(null, "Return to the fire", Style.Display, 22, Kit.Ink2, G.QuitToTitle);""", """        var (walk, _) = WorldType.Keyed(Act.Confirm, "KEEP WALKING", Style.Display, 22, Style.EmberHi, G.CloseOverlay);
        var (fire, _) = WorldType.Keyed(null, "RETURN TO THE FIRE", Style.Display, 22, Kit.Ink2, G.QuitToTitle);"""),
("""        // The left leaf: what was done, and what still waits.
        var left = Style.V(Style.Gap2, H("What was done"));""", """        // The left leaf looks back: what was done, what the world says of it, and the tally of the road
        // as a ledger line after the words. The right looks on: who remembers you, and what still waits.
        var left = Style.V(Style.Gap2, H("What was done"));"""),
("""        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(H("Still waiting"));
        foreach (var o in sum.Open) left.AddChild(Style.V(1, P(o.Name, 17, Style.TextBold), P(o.Line, 15, Style.TextItalic, soft)));

        // The right leaf: who remembers, what the world says, and the tally as a ledger line after the words.
        var right = Style.V(Style.Gap2, H("Who remembers you"));""", """        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(H("What the world says you did"));
        if (sum.Deeds.Count == 0) left.AddChild(P("Nothing it has noticed. Give it time.", 16, Style.TextItalic, soft));
        foreach (var d in sum.Deeds) left.AddChild(P($"You {d}."));
        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(Style.Rule());
        // (numerals over their names, as the Journal's Deeds ends: not coins pinned to the page's foot)
        var tally = Style.H(0);
        foreach (var (label, value) in sum.Stats)
        {
            var cell = Style.V(0, Style.Label(value, Style.Display, 28, ink, false, HorizontalAlignment.Center, false),
                Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 11, soft, false, HorizontalAlignment.Center, false));
            cell.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            tally.AddChild(cell);
        }
        left.AddChild(tally);

        var right = Style.V(Style.Gap2, H("Who remembers you"));"""),
("""        right.AddChild(Style.Gap(Style.Gap2));
        right.AddChild(H("What the world says you did"));
        if (sum.Deeds.Count == 0) right.AddChild(P("Nothing it has noticed. Give it time.", 16, Style.TextItalic, soft));
        foreach (var d in sum.Deeds) right.AddChild(P($"You {d}."));
        right.AddChild(Style.Gap(Style.Gap2));
        right.AddChild(Style.Rule());
        // (numerals over their names, as the Journal's Deeds ends: not coins pinned to the page's foot)
        var tally = Style.H(0);
        foreach (var (label, value) in sum.Stats)
        {
            var cell = Style.V(0, Style.Label(value, Style.Display, 28, ink, false, HorizontalAlignment.Center, false),
                Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 11, soft, false, HorizontalAlignment.Center, false));
            cell.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            tally.AddChild(cell);
        }
        right.AddChild(tally);""", """        right.AddChild(Style.Gap(Style.Gap2));
        right.AddChild(H("Still waiting"));
        foreach (var o in sum.Open) right.AddChild(Style.V(1, P(o.Name, 17, Style.TextBold), P(o.Line, 15, Style.TextItalic, soft)));"""),
]
