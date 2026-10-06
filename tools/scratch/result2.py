p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\ArenaResult.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""    readonly System.Collections.Generic.List<(Label L, double To, System.Func<double, string> Fmt, double At)> counts = new();""",
    """    readonly System.Collections.Generic.List<(Medallion M, double To, System.Func<double, string> Fmt, double At)> counts = new();""")
rep("""        foreach (var (l, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(l)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            l.Text = fmt(to * k);
        }""", """        foreach (var (m, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(m)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != m.Text) { m.Text = t; m.Arc = (float)k; m.QueueRedraw(); }
        }""")
rep("""        AddChild(Style.Scrim(null, r.Won ? 0.62f : 0.74f));
        var wrap = Style.Centered(Style.V(12), new Vector2(1060, 720));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        wrap.AddChild(Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE ARENA IS WON", Style.UiHeavy, 15, tone, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Label(r.Spec.Name, Style.Display, 48, Style.GoldHi, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Flourish());""", """        AddChild(new Backdrop(null, r.Won ? 0.82f : 0.9f));
        var wrap = Style.Centered(Style.V(14), new Vector2(1240, 900));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        // The verdict on a banner, the arena's name under it.
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 30, r.Won ? Style.Gold : Style.BloodHi),
            Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE ARENA IS WON", Style.Display, 40, r.Won ? new Color("#ffe6b8") : Style.BloodHi, false, HorizontalAlignment.Center));
        banner.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        wrap.AddChild(banner);
        wrap.AddChild(Style.Label(r.Spec.Name, Style.TextItalic, Style.Lead, Style.GoldHi, false, HorizontalAlignment.Center));""")
rep("""        var tally = Style.H(36,""", """        var tally = Style.H(48,""")
rep("""        // What comes out.
        var outv = Style.V(8, Style.SubLabel("What you take out"));""", """        // What comes out, on a forged plate; what stays, on a slab gone to ash.
        var outv = Style.V(8, new Section("What you take out"));""")
rep("""        var stay = Style.V(8, Style.SubLabel("What stays in the arena"));
        if (G.Battle is { } b)
        {
            foreach (var w in b.Weapons)
                stay.AddChild(Style.H(8, Glyphs.Icon(w.Evolution?.Art ?? w.Def.Art, 20, Style.InkDim),
                    Style.Label($"{w.Evolution?.Name ?? w.Def.Name}  {Numeral(w.Rank)}", Style.Ui, Style.Small, Style.InkDim)));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd)
                    stay.AddChild(Style.H(8, Glyphs.Icon(bd.Icon, 20, Style.InkDim), Style.Label(bd.Max > 1 ? $"{bd.Name}  {Numeral(rank)}" : bd.Name, Style.Ui, Style.Small, Style.InkDim)));
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
        two.AddChild(Card(stay));""", """        var stay = Style.V(8, new Section("What stays in the arena"));
        if (G.Battle is { } b)
        {
            // The build the ember made, as grey medallions: it does not leave with you.
            var ash = new GridContainer { Columns = 5, MouseFilter = MouseFilterEnum.Ignore };
            ash.AddThemeConstantOverride("h_separation", 10);
            ash.AddThemeConstantOverride("v_separation", 10);
            Control Faded(string glyph, string name)
            {
                var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
                mc.AddChild(new Medallion(64, "", glyph) { Ring = Style.InkFaint, Ink = Style.InkDim, Core = new Color("#16131a") });
                var v = Style.V(2, mc, Style.Label(name, Style.Ui, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
                v.CustomMinimumSize = new Vector2(100, 0);
                return v;
            }
            foreach (var w in b.Weapons) ash.AddChild(Faded(w.Evolution?.Art ?? w.Def.Art, $"{w.Evolution?.Name ?? w.Def.Name} {Numeral(w.Rank)}"));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd) ash.AddChild(Faded(bd.Icon, bd.Max > 1 ? $"{bd.Name} {Numeral(rank)}" : bd.Name));
            stay.AddChild(ash);
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
        var stayCard = Card(stay, Style.Slab(18));
        stayCard.Modulate = new Color(1, 1, 1, 0.85f);
        two.AddChild(stayCard);""")
rep("""    Control Stat(string glyph, double value, System.Func<double, string> fmt, string label, double at)
    {
        var l = Style.Label(fmt(0), Style.Display, 34, Style.GoldHi);
        counts.Add((l, value, fmt, at));
        var h = Style.H(8, Glyphs.Icon(glyph, 24, Style.GoldHi), l);
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(0, h, Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.Gold, false, HorizontalAlignment.Center));
    }""", """    /// <summary>A number of the night on a medallion, counting up with its ring filling, its name under it.</summary>
    Control Stat(string glyph, double value, System.Func<double, string> fmt, string label, double at)
    {
        var m = new Medallion(150, fmt(0)) { Ring = r.Won ? Style.Gold : Style.InkDim, ArcColor = r.Won ? Style.Ember : Style.BloodHi, Ink = Style.GoldHi };
        counts.Add((m, value, fmt, at));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(m);
        var name = Style.H(6, Glyphs.Icon(glyph, 16, Style.Gold), Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));
        name.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(4, mc, name);
    }""")
rep("""    static Control Card(Control inner)
    {
        var p = Style.Panel(Style.Plate(18), Style.Scroll(inner));""", """    static Control Card(Control inner, StyleBox? box = null)
    {
        var p = Style.Panel(box ?? Style.Plate(20), Style.Scroll(inner));""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
