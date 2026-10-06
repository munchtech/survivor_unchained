from ed import sub

sub("src/Ui/Forge.cs", [
("""        bool on = k == seam, pinned = c.Pinned == m.Id;
        var box = new StyleBoxFlat { BgColor = on ? new Color("#33251b") : Kit.Well, BorderColor = on ? Style.Ember : new Color("#0a090b"), CornerDetail = 4 };
        box.SetCornerRadiusAll(3);
        box.SetBorderWidthAll(on ? 1 : 0);
        box.BorderWidthTop = 1;
        box.ContentMarginLeft = box.ContentMarginRight = 12;
        box.ContentMarginTop = box.ContentMarginBottom = 7;
        var panel = Style.Panel(box);
        panel.MouseFilter = MouseFilterEnum.Stop;""",
"""        bool on = k == seam, pinned = c.Pinned == m.Id;
        // A ledger's row, as the seams are: the wax, the oath's words, a fine rule; the one on the table
        // with a thin ember mark at its left.
        var panel = Style.Panel(new StyleBoxEmpty { ContentMarginTop = 6, ContentMarginBottom = 6 });
        panel.MouseFilter = MouseFilterEnum.Stop;"""),
("""        var words = Style.V(1, Style.Label(m.Says, Style.UiBold, 17, Kit.Ink, true),
            Style.Label($"{m.Name}  ·  pays {string.Join(", ", pays)}", Style.TextItalic, 15, Kit.Dim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var h = Style.H(14, seal, words);
        if (pinned) h.AddChild(Style.Label("PINNED", Style.UiHeavy, 12, Style.GoldHi));
        if (on) h.AddChild(Style.Label("ON THE TABLE", Style.UiHeavy, 12, Style.Ember));
        panel.AddChild(h);""",
"""        var words = Style.V(0, Style.Label(m.Says, Style.UiBold, 17, on ? Kit.Ink : Kit.Ink2, true),
            Style.Label($"{m.Name}  ·  pays {string.Join(", ", pays)}{(pinned ? "  ·  pinned" : "")}", Style.TextItalic, 15, pinned ? Style.GoldHi : Kit.Dim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var h = Style.H(14, new ColorRect { Color = on ? Style.Ember : Colors.Transparent, CustomMinimumSize = new Vector2(2, 0), MouseFilter = MouseFilterEnum.Ignore }, seal, words);
        panel.AddChild(h);"""),
("""        Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        if (index >= 0) rows[index] = (panel, seal);
        return panel;""",
"""        Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        if (index >= 0) rows[index] = (panel, seal);
        return Style.V(0, panel, Kit.RuleH());"""),
])
