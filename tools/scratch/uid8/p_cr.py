PAIRS = [
("""        // The texts the licences ask for also lie beside the game.
        var slab = Style.Panel(Style.Slab(16));
        var sv = Style.V(Style.Gap2, Style.Label("Every licence text, and these credits, also lie beside the game in its licences folder.", Style.TextItalic, Style.Small, Style.InkDim, true));
        var open = Style.Button("", OpenFolder, false, true);
        var row = Style.H(Style.Gap2, Style.Prompt(Act.Alt), Style.Label("Open the licences folder", Style.UiBold, Style.Small, Style.GoldHi));
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(10, 5);
        open.AddChild(row);
        open.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 22, 36);
        open.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        sv.AddChild(Nav.Skip(open));
        slab.AddChild(sv);
        v.AddChild(slab);""", """        // The texts the licences ask for also lie beside the game: said, and the way to them, as type
        // under a rule (no slab and no button's box).
        var open = Kit.Keyed(Act.Alt, "Open the licences folder", OpenFolder, Style.GoldHi, 16);
        open.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        v.AddChild(Style.V(Style.Gap3, Kit.RuleH(),
            Style.Label("Every licence text, and these credits, also lie beside the game in its licences folder.", Style.TextItalic, 16, Kit.Dim, true, HorizontalAlignment.Left, false),
            Nav.Skip(open)));"""),
("""            Link(seal, licence, link ?? "", Style.UiHeavy, 15, Style.EmberHi);
            var frame = Style.Box(new Color(0.25f, 0.12f, 0.05f, 0.55f), Style.Ember with { A = 0.55f }, 1, 3, 0);
            frame.ContentMarginLeft = frame.ContentMarginRight = 12;
            frame.ContentMarginTop = 4;
            frame.ContentMarginBottom = 2;
            var box = Style.Panel(frame, seal);
            box.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(box);""", """            // (its name in the ember's small capitals at the head's end: no seal's box)
            Link(seal, licence, link ?? "", Style.UiHeavy, 15, Style.EmberHi);
            seal.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(seal);"""),
]
