p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
a = s.index("        var who = Pane(page, new Rect2(0, 0, 560, 920));")
b = s.index("        ShowStanding(null);\n        if (Controls.Instance.UsingPad)\n            PageFooter(Footer((Act.Confirm, ch.Points > 0")
new = '''        var who = Pane(page, new Rect2(0, 0, 560, 920));
        var fig = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        fig.AddChild(InventoryScreen.Figure(ch, 400, 430));
        who.AddChild(fig);
        double need = Character.XpForLevel(ch.Level);
        var lvl = new Medallion(76, $"{ch.Level}") { Arc = (float)(ch.Xp / need), ArcColor = Style.Day, Core = new Color("#1c2a3a"), Ink = Style.DayHi };
        var lw = Style.V(4, Style.Label("Level", Style.Display, 22, Style.GoldHi), Bar(ch.Xp / need, $"{Math.Floor(ch.Xp)} / {need} to level {ch.Level + 1}", Style.Day, 400));
        lw.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        who.AddChild(Style.H(Style.Gap3, lvl, lw));
        var ab = Abilities.ById(ch.Ability);
        var arts = Style.Button("", () => G.Open("arts"), false, true);
        var artRow = Style.H(8, Glyphs.Icon(ab.Icon, 20), Style.Label($"In hand: {ab.Name}  ·  rank {ArtBook.Rank(ch, ch.Ability)}", Style.UiBold, Style.Small, Style.GoldHi), Style.Key(G.Key(Act.Arts)));
        artRow.Position = new Vector2(10, 7);
        artRow.MouseFilter = MouseFilterEnum.Ignore;
        arts.AddChild(artRow);
        arts.CustomMinimumSize = new Vector2(0, 38);
        arts.TooltipText = "Your arts: the one in hand, its rank and facets";
        who.AddChild(Nav.Id(arts, "arts"));
        // The calling: how they fight and where they came from, in the game's own words.
        var arch = Callings.Archetype(ch.Archetype);
        var back = Callings.Background(ch.Background);
        who.AddChild(new Section("Calling"));
        var calling = Style.Panel(Style.Slab(14));
        calling.MouseFilter = MouseFilterEnum.Ignore;
        var cv = Style.V(Style.Gap2,
            Style.V(0, Style.Label(arch.Name, Style.UiBold, Style.Body, Style.GoldHi), Style.Label(arch.Tagline, Style.TextItalic, Style.Caption, Style.InkDim, true)),
            Style.V(0, Style.Label(back.Name, Style.UiBold, Style.Body, Style.GoldHi), Style.Label(back.Summary, Style.TextItalic, Style.Caption, Style.InkDim, true)));
        calling.AddChild(cv);
        who.AddChild(calling);
        var knows = ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]).ToList();
        who.AddChild(Style.Label(knows.Count == 0 ? "You know little yet that others do not." : $"You know {string.Join(", ", knows)}: it opens words and ways others miss.", Style.TextItalic, Style.Small, Style.Ink, true));
        foreach (var c in ch.Conditions)
        {
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            who.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 16, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }

        // The four attributes as pillars, the number the hero; traits under them as cards.
        var mid = Pane(page, new Rect2(590, 0, 840, 920));
        mid.AddChild(new Section("Attributes", ch.Points > 0 ? $"{ch.Points} to spend: a + shows what it would change" : "more with each level"));
        var pillars = Style.H(16);
        mid.AddChild(pillars);
        for (int i = 0; i < Attrs.Length; i++)
        {
            var (id, nm, text) = Attrs[i];
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 14, ch.Points > 0 ? Style.Ember : Style.Gold);
            box.Crest = 90;
            var pillar = Style.Panel(UiArt.Frame("pillar", box));
            pillar.CustomMinimumSize = new Vector2(188, 320);
            pillar.MouseFilter = MouseFilterEnum.Ignore;
            pillars.AddChild(pillar);
            var v = Style.V(Style.Gap2);
            pillar.AddChild(v);
            var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            med.AddChild(new Medallion(108, $"{Attr(ch, id)}"));
            v.AddChild(med);
            v.AddChild(Style.Label(nm.ToUpperInvariant(), Style.Display, 22, Style.GoldHi, false, HorizontalAlignment.Center));
            var words = Style.Label(text, Style.Ui, Style.Caption, Style.Ink, true, HorizontalAlignment.Center);
            words.SizeFlagsVertical = SizeFlags.ExpandFill;
            v.AddChild(words);
            if (ch.Points > 0)
            {
                var attr = id;
                var plus = Style.Button("+  Spend", () => G.Gear((j, b) => j.SpendPoint(attr, b)), true, false);
                plus.MouseEntered += () => ShowStanding(attr);
                plus.MouseExited += () => ShowStanding(null);
                Nav.Mark(plus, $"attr:{attr}", () => G.Gear((j, b) => j.SpendPoint(attr, b)), focus: () => ShowStanding(attr), blur: () => ShowStanding(null));
                v.AddChild(plus);
            }
        }

        mid.AddChild(Style.Gap(Style.Gap2));
        mid.AddChild(new Section("Traits", ch.TraitPicks > 0 ? $"choose {ch.TraitPicks}: each is for good" : "chosen at levels, or given for what you do"));
        var traits = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        traits.AddThemeConstantOverride("h_separation", 12);
        traits.AddThemeConstantOverride("v_separation", 12);
        mid.AddChild(traits);
        Control TraitCard(string name, string text, bool earned, Action? take, string? navId)
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Slab, 14, take != null ? Style.Ember : earned ? Style.EmberHi : Style.Gold);
            var inner = Style.V(4, Style.Label(name, Style.UiBold, Style.Body, take != null || earned ? Style.EmberHi : Style.GoldHi), Style.Label(text, Style.Ui, Style.Caption, Style.Ink, true));
            inner.MouseFilter = MouseFilterEnum.Ignore;
            if (take == null)
            {
                var p = Style.Panel(box, inner);
                p.CustomMinimumSize = new Vector2(258, 118);
                return p;
            }
            var bt = Style.Button("", take);
            foreach (var st in new[] { "normal", "hover", "pressed" }) bt.AddThemeStyleboxOverride(st, box);
            inner.Position = new Vector2(14, 12);
            inner.Size = new Vector2(230, 94);
            bt.AddChild(inner);
            bt.CustomMinimumSize = new Vector2(258, 118);
            if (navId != null) Nav.Id(bt, navId);
            return bt;
        }
        foreach (var t in ch.Traits)
        {
            var def = Callings.Trait(t);
            traits.AddChild(TraitCard((def?.Name ?? t) + (def?.Source == TraitSource.World ? "  ·  earned" : ""), def?.Text ?? "", def?.Source == TraitSource.World, null, null));
        }
        if (ch.TraitPicks > 0)
            foreach (var t in Offer(ch))
            {
                var def = Callings.Trait(t)!;
                traits.AddChild(TraitCard(def.Name, def.Text, false, () => G.Gear((j, bt) => j.PickTrait(t, bt)), $"trait:{t}"));
            }
        if (ch.Traits.Count == 0 && ch.TraitPicks == 0)
            mid.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Small, Style.InkDim, true));

        // The whole standing, grouped by what it is for.
        var right = Pane(page, new Rect2(1460, 0, 380, 920), null, Style.Gap2);
        right.AddChild(new Section("Standing", "hover: where from"));
        standing = Style.V(Style.Gap2);
        right.AddChild(standing);
'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
