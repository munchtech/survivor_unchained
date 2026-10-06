p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
a = s.index("    protected override void Build()\n    {\n        var ch = G.Journey.Ch;\n        var body = Frame(ch.Name, new Vector2(1500, 790)")
b = s.index("    /// <summary>The standing; with an attribute named, what a point in it would change.</summary>")
new = '''    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var page = Page(ch.Name, $"Level {ch.Level} {Callings.Background(ch.Background).Name} {Callings.Archetype(ch.Archetype).Name}");

        // Who they are: the figure, the way to the next level, the art in hand, what they know.
        var who = Pane(page, new Rect2(0, 0, 560, 920));
        var fig = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        fig.AddChild(InventoryScreen.Figure(ch, 400, 470));
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
        var knows = ch.Knowledge.Where(Know.ContainsKey).Select(k => Know[k]).ToList();
        who.AddChild(Style.Label(knows.Count == 0 ? "You know little yet that others do not." : $"You know {string.Join(", ", knows)}: it opens words and ways others miss.", Style.TextItalic, Style.Small, Style.InkDim, true));
        foreach (var c in ch.Conditions)
        {
            bool good = c.Id is ConditionId.Blessed or ConditionId.Rested or ConditionId.Warmed;
            who.AddChild(Style.H(6, Glyphs.Icon(good ? "sun" : "skull", 16, good ? Style.Good : Style.Bad), Style.Label($"{Cond.GetValueOrDefault(c.Id, c.Id.ToString())}  ·  {c.Days} day{(c.Days == 1 ? "" : "s")}", Style.UiBold, Style.Caption, good ? Style.Good : Style.Bad, true)));
        }

        // The four attributes, as pillars: the number is the hero.
        var head = new Section("Attributes", ch.Points > 0 ? $"{ch.Points} to spend: a + shows what it would change" : "more with each level");
        head.Position = new Vector2(590, 0);
        head.Size = new Vector2(838, 26);
        page.AddChild(head);
        for (int i = 0; i < Attrs.Length; i++)
        {
            var (id, nm, text) = Attrs[i];
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 16, ch.Points > 0 ? Style.Ember : Style.Gold);
            box.Crest = 90;
            var pillar = Style.Panel(UiArt.Frame("pillar", box));
            pillar.Position = new Vector2(590 + i * 212, 36);
            pillar.Size = new Vector2(200, 420);
            pillar.MouseFilter = MouseFilterEnum.Ignore;
            page.AddChild(pillar);
            var v = Style.V(Style.Gap2);
            v.Alignment = BoxContainer.AlignmentMode.Begin;
            pillar.AddChild(v);
            var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            med.AddChild(new Medallion(112, $"{Attr(ch, id)}"));
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

        // Traits, as cards to choose and cards held.
        var th = new Section("Traits", ch.TraitPicks > 0 ? $"choose {ch.TraitPicks}" : null);
        th.Position = new Vector2(590, 476);
        th.Size = new Vector2(838, 26);
        page.AddChild(th);
        var traits = new GridContainer { Columns = 3, Position = new Vector2(590, 512), Size = new Vector2(838, 400), MouseFilter = MouseFilterEnum.Ignore };
        traits.AddThemeConstantOverride("h_separation", 12);
        traits.AddThemeConstantOverride("v_separation", 12);
        page.AddChild(traits);
        Control TraitCard(string name, string text, bool earned, Action? take, string? navId)
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Slab, 14, take != null ? Style.Ember : earned ? Style.EmberHi : Style.Gold);
            var inner = Style.V(2, Style.Label(name, Style.UiBold, Style.Body, take != null || earned ? Style.EmberHi : Style.GoldHi), Style.Label(text, Style.Ui, Style.Caption, Style.Ink, true));
            inner.MouseFilter = MouseFilterEnum.Ignore;
            if (take == null)
            {
                var p = Style.Panel(box, inner);
                p.CustomMinimumSize = new Vector2(271, 104);
                return p;
            }
            var bt = Style.Button("", take);
            foreach (var st in new[] { "normal", "hover", "pressed" }) bt.AddThemeStyleboxOverride(st, box);
            inner.Position = new Vector2(14, 10);
            inner.Size = new Vector2(243, 84);
            bt.AddChild(inner);
            bt.CustomMinimumSize = new Vector2(271, 104);
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
            traits.AddChild(Style.Label("None yet. Traits come with levels, and with what you do.", Style.TextItalic, Style.Small, Style.InkDim, true));

        // The whole standing, grouped by what it is for.
        var sh = new Section("Standing", "where each comes from: hover");
        sh.Position = new Vector2(1458, 0);
        sh.Size = new Vector2(382, 26);
        page.AddChild(sh);
        standing = Style.V(Style.Gap2);
        standing.Position = new Vector2(1458, 36);
        standing.Size = new Vector2(382, 880);
        page.AddChild(standing);
        ShowStanding(null);
        if (Controls.Instance.UsingPad)
            PageFooter(Footer((Act.Confirm, ch.Points > 0 ? "Spend a point" : "Choose"), (Act.TabPrev, "Pack"), (Act.TabNext, "Arts"), (Act.Cancel, "Close")));
    }

'''
s = s[:a] + new + s[b:]
old = '''        foreach (var (group, lines) in Standing)
        {
            standing.AddChild(Style.Gap(Style.Gap1));
            standing.AddChild(Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.Gold));
            foreach (var (key, name, fmt) in lines)
            {'''
new2 = '''        foreach (var (group, lines) in Standing)
        {
            // Each group on a plate of its own.
            var plate = Style.Panel(Style.Slab(12));
            plate.MouseFilter = MouseFilterEnum.Ignore;
            var col = Style.V(2, Style.Label(group.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));
            plate.AddChild(col);
            standing.AddChild(plate);
            foreach (var (key, name, fmt) in lines)
            {'''
assert old in s
s = s.replace(old, new2, 1)
old3 = '''                Nav.Mark(holder, $"stat:{key}", null, focus: () => Tip(Breakdown(k, name, fmt), holder), blur: () => Tip(null, null));
                standing.AddChild(holder);'''
new3 = '''                Nav.Mark(holder, $"stat:{key}", null, focus: () => Tip(Breakdown(k, name, fmt), holder), blur: () => Tip(null, null));
                col.AddChild(holder);'''
assert old3 in s
s = s.replace(old3, new3, 1)
old4 = '''                var label = Style.Label(name, Style.Ui, Style.Small, Style.InkDim);
                label.CustomMinimumSize = new Vector2(190, 0);'''
new4 = '''                var label = Style.Label(name, Style.Ui, Style.Small, Style.InkDim);
                label.CustomMinimumSize = new Vector2(150, 0);'''
assert old4 in s
s = s.replace(old4, new4, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
