PAIRS = [
("""        var v = Style.V(8);
        if (!Her && Hero == null)
        {
            v.AddChild(Style.SubLabel("Beard"));
            v.AddChild(Nav.Id(Style.Segment(d.Beard ? "Bearded" : "Clean-shaven", d.Beard, () => Set(() => d.Beard = !d.Beard)), "beard"));
        }
        v.AddChild(Style.SubLabel("Skin"));
        v.AddChild(Beads(Lore.Skins, d.Skin, id => d.Skin = id, Bead.Kind.Skin, "#f2c4a8"));
        v.AddChild(Style.SubLabel($"Colours of {Their.ToLowerInvariant()} outfit"));
        var pal = new GridContainer { Columns = 2 };
        pal.AddThemeConstantOverride("h_separation", 6);
        pal.AddThemeConstantOverride("v_separation", 6);
        foreach (var p in a.Palettes) pal.AddChild(Style.Segment(p.Name, d.Palette == p.Id, () => Set(() => d.Palette = p.Id)));
        v.AddChild(pal);
        v.AddChild(Style.SubLabel("Cloak"));""", """        var v = Style.V(Style.Gap2);
        if (!Her && Hero == null)
        {
            v.AddChild(Kit.Head("Beard"));
            v.AddChild(Flow(new[] { ("Bearded", d.Beard, (Action)(() => Set(() => d.Beard = true)), "beard:on"), ("Clean-shaven", !d.Beard, () => Set(() => d.Beard = false), "beard:off") }));
        }
        v.AddChild(Kit.Head("Skin"));
        v.AddChild(Beads(Lore.Skins, d.Skin, id => d.Skin = id, Bead.Kind.Skin, "#f2c4a8"));
        v.AddChild(Kit.Head($"Colours of {Their.ToLowerInvariant()} outfit"));
        v.AddChild(Flow(a.Palettes.Select(p => (p.Name, d.Palette == p.Id, (Action)(() => Set(() => d.Palette = p.Id)), $"palette:{p.Id}"))));
        v.AddChild(Kit.Head("Cloak"));"""),
("""        var v = Style.V(8, Style.SubLabel($"{Their} hair"));
        // (large: a cut is told by its shape, which a small picture loses)""", """        var v = Style.V(Style.Gap2, Kit.Head($"{Their} hair"));
        // (large: a cut is told by its shape, which a small picture loses)"""),
("""            v.AddChild(Style.SubLabel("Beard"));
            var beards = Grid(4);""", """            v.AddChild(Kit.Head("Beard"));
            var beards = Grid(4);"""),
("""        v.AddChild(Style.Gap(4));
        v.AddChild(Style.SubLabel("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));""", """        v.AddChild(Kit.Head("Colour"));
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, OwnHair().ToHtml(false)));"""),
("""        var v = Style.V(8, Style.H(8, Style.SubLabel($"{Their} hair"), hidden ? Style.Label("under the hood", Style.TextItalic, 13, Style.InkDim) : new Control()));
        var cuts = Style.H(4);
        foreach (var h in Lore.HairStyles(d.Sex).Append("none")) cuts.AddChild(Style.Segment(HairNames.GetValueOrDefault(h, h), d.HairStyle == h, () => Set(() => d.HairStyle = h)));
        if (hidden) cuts.Modulate = new Color(1, 1, 1, 0.5f);
        v.AddChild(cuts);
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, "#6a5a48"));
        if (d.Archetype != "reaver")
        {
            v.AddChild(Style.SubLabel("Hood"));
            if (a.AltModel != null) v.AddChild(Style.Button(d.Model == a.Model ? "Hood up" : "Hood down", () => Set(() => d.Model = d.Model == a.Model ? a.AltModel! : a.Model), false, true));
            if (d.Archetype != "stalker") v.AddChild(Style.Button(d.Headgear ? "Hood up" : "Hood down", () => Set(() => d.Headgear = !d.Headgear), false, true));
        }
        return v;""", """        var v = Style.V(Style.Gap2, Kit.Head($"{Their} hair", hidden ? "under the hood" : null));
        var cuts = Flow(Lore.HairStyles(d.Sex).Append("none").Select(h => (HairNames.GetValueOrDefault(h, h), d.HairStyle == h, (Action)(() => Set(() => d.HairStyle = h)), $"cut:{h}")));
        if (hidden) cuts.Modulate = new Color(1, 1, 1, 0.5f);
        v.AddChild(cuts);
        v.AddChild(Beads(Lore.Hairs, d.Hair, id => d.Hair = id, Bead.Kind.Hair, "#6a5a48"));
        if (d.Archetype != "reaver")
        {
            v.AddChild(Kit.Head("Hood"));
            // (a hooded body of its own for the calling, or the calling's headgear)
            bool up = a.AltModel != null ? d.Model == a.Model : d.Headgear;
            if (a.AltModel != null || d.Archetype != "stalker")
                v.AddChild(Flow(new[] { ("Hood up", up, (Action)(() => Set(Hood(a, true))), "hood:up"), ("Hood down", !up, () => Set(Hood(a, false)), "hood:down") }));
        }
        return v;"""),
("""            v.AddChild(Style.SubLabel($"{Their} face"));
            var grid = Grid(4);""", """            v.AddChild(Kit.Head($"{Their} face"));
            var grid = Grid(4);"""),
("""            v.AddChild(Style.SubLabel("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        }
        if (k.Sliders.Count > 0)
            v.AddChild(Style.Label("Shape it by hand in the next part.", Style.TextItalic, Style.Caption, Style.InkDim));""", """            v.AddChild(Kit.Head("Eyes"));
            v.AddChild(Beads(k.Eyes, d.Eyes, id => d.Eyes = id, Bead.Kind.Eye, ""));
        }
        if (k.Sliders.Count > 0)
            v.AddChild(Style.Label("Shape it by hand in the next part.", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false));"""),
("""        var v = Style.V(8);
        var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
        int g = Math.Clamp(d.FaceGroup, 0, groups.Length - 1);
        v.AddChild(Style.SubLabel($"Shape {Their.ToLowerInvariant()} face"));
        var tabs = new GridContainer { Columns = Math.Min(4, groups.Length) };
        tabs.AddThemeConstantOverride("h_separation", 6);
        tabs.AddThemeConstantOverride("v_separation", 6);
        for (int i = 0; i < groups.Length; i++)
        {
            int at = i;
            var seg = Nav.Id(Style.Segment(groups[i], g == i, () => Set(() => d.FaceGroup = at)), $"group:{groups[i]}");
            seg.CustomMinimumSize = new Vector2(114, 34);
            tabs.AddChild(seg);
        }
        v.AddChild(tabs);
        v.AddChild(Style.Gap(4));""", """        var v = Style.V(Style.Gap2);
        var groups = k.Sliders.Select(s => s.Group).Distinct().ToArray();
        int g = Math.Clamp(d.FaceGroup, 0, groups.Length - 1);
        v.AddChild(Kit.Head($"Shape {Their.ToLowerInvariant()} face"));
        // (the groups as words, the one shown over the ember's underline; no boxes)
        v.AddChild(Flow(groups.Select((name, i) => (name, g == i, (Action)(() => Set(() => d.FaceGroup = i)), $"group:{name}"))));
        v.AddChild(Style.Gap(Style.Gap1));"""),
("""            v.AddChild(Style.Gap(4));
            v.AddChild(Nav.Id(Style.Button(preset != null ? $"Back to {preset.Name.ToLowerInvariant()}" : $"Back to {Their.ToLowerInvariant()} own face",
                () => Set(() => d.Face = new Dictionary<string, double>(preset?.Shape ?? new())), false, true), "unshape"));""", """            var back = Nav.Id(Kit.Word(preset != null ? $"Back to {preset.Name.ToLowerInvariant()}" : $"Back to {Their.ToLowerInvariant()} own face",
                () => Set(() => d.Face = new Dictionary<string, double>(preset?.Shape ?? new())), Style.EmberHi, 16), "unshape");
            back.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            v.AddChild(back);"""),
("""        var v = Style.V(8, Style.SubLabel($"Paint on {Their.ToLowerInvariant()} face"));""", """        var v = Style.V(Style.Gap2, Kit.Head($"Paint on {Their.ToLowerInvariant()} face"));"""),
("""    /// <summary>A grid of cameos, so many to a row.</summary>
    static GridContainer Grid(int columns)
    {
        var g = new GridContainer { Columns = columns };
        g.AddThemeConstantOverride("h_separation", columns > 3 ? 6 : 10);
        g.AddThemeConstantOverride("v_separation", 2);
        return g;
    }""", """    /// <summary>Cameos in rows, so many to a row, each row centred (a short last row sits in the
    /// middle, not against the left).</summary>
    static HFlowContainer Grid(int columns)
    {
        var g = new HFlowContainer { Alignment = FlowContainer.AlignmentMode.Center, MouseFilter = MouseFilterEnum.Ignore };
        g.AddThemeConstantOverride("h_separation", columns > 3 ? 6 : 10);
        g.AddThemeConstantOverride("v_separation", 2);
        return g;
    }

    /// <summary>Words to choose between, as the house's tabs in centred lines, each with its focus id.</summary>
    static HFlowContainer Flow(IEnumerable<(string Text, bool On, Action Press, string Id)> words)
    {
        var list = words.ToList();
        var f = Kit.TabFlow(list.Select(w => (w.Text, w.On, w.Press)), 16, 24, 4);
        int i = 0;
        foreach (var b in f.GetChildren().OfType<Button>()) Nav.Id(b, list[i++].Id);
        return f;
    }

    /// <summary>The hood up or down: the calling's hooded body where it has one, else its headgear.</summary>
    Action Hood(Archetype a, bool up) => () =>
    {
        if (a.AltModel != null) d.Model = up ? a.Model : a.AltModel;
        else d.Headgear = up;
    };"""),
("""        var wrap = new HFlowContainer();
        wrap.AddThemeConstantOverride("h_separation", 6);""", """        var wrap = new HFlowContainer { Alignment = FlowContainer.AlignmentMode.Center };
        wrap.AddThemeConstantOverride("h_separation", 6);"""),
("""        var v = Style.V(2, wrap, Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.TextItalic, Style.Caption, Style.InkDim));""", """        var v = Style.V(2, wrap, Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false));"""),
]
