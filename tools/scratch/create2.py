p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Front.cs'
s = open(p, encoding='utf-8').read()

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

cut("""    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        // As tall as its step needs""", """    Control Calling()""", '''    protected override void Build()
    {
        var a = Callings.Archetype(d.Archetype);
        // A forged column down the left, the figure by the fire in the middle, the choice read
        // closely on the right (docs/UI_DESIGN.md, "Creation").
        var column = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Plate, 0));
        column.Position = new Vector2(-30, -30);
        column.Size = new Vector2(620, 1140);
        AddChild(column);
        var col = Style.V(Style.Gap3);
        col.Position = new Vector2(52, 44);
        col.Size = new Vector2(486, 1000);
        AddChild(col);
        col.AddChild(Style.Label("By the fire on the Low Ford road", Style.TextItalic, Style.Body, new Color("#c8a878")));
        col.AddChild(new Plaque("Who sits here?", 30, 30));
        col.AddChild(StepRoad());
        var body = d.Step switch { 0 => Calling(), 1 => Arms(a), 2 => Origin(), _ => NameLook(a) };
        var sc = Style.Scroll(body);
        sc.SizeFlagsVertical = SizeFlags.ExpandFill;
        col.AddChild(sc);
        var foot = Style.H(10, Nav.Id(Style.Button(d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); }), "back"));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(d.Step < 3 ? Nav.Id(Style.Button($"Next: {Steps[d.Step + 1]}", () => Set(() => d.Step++), true), "next") : Nav.Id(Style.Button("Begin the journey", Begin, true), "begin"));
        col.AddChild(foot);

        var right = Style.Panel(Style.Plate(24));
        right.Position = new Vector2(1380, 110);
        right.Size = new Vector2(500, 0);
        right.CustomMinimumSize = new Vector2(500, 0);
        right.AddChild(d.Step switch { 0 => CallingDetail(a), 1 => ArmsDetail(), 2 => OriginDetail(), _ => Summary(a) });
        AddChild(right);

        // Who they are becoming, on a banner at the figure's feet.
        var cap = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 20), Style.V(0, Style.Label(d.Name.Trim() == "" ? "NAMELESS" : d.Name.Trim().ToUpperInvariant(), Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center),
            Style.Label($"{Callings.Background(d.Background).Name} {a.Name}", Style.TextItalic, Style.Body, Style.Ink, false, HorizontalAlignment.Center)));
        cap.CustomMinimumSize = new Vector2(380, 0);
        AddChild(cap);
        cap.Position = new Vector2(1010 - 190, 960);
    }

    /// <summary>The four steps as a road of medallions: done in gold, this one lit, the rest dark.</summary>
    Control StepRoad()
    {
        bool pad = Controls.Instance.UsingPad;
        var road = Style.H(0);
        road.Alignment = BoxContainer.AlignmentMode.Center;
        var lb = pad ? Style.PadButton("LB") : Style.Key(G.Key(Act.TabPrev));
        lb.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        road.AddChild(lb);
        for (int i = 0; i < Steps.Length; i++)
        {
            int st = i;
            bool here = d.Step == i, done = i < d.Step;
            var b = Style.Button("", () => Set(() => d.Step = st), false, true);
            foreach (var x in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(x, new StyleBoxEmpty());
            var v = Style.V(2);
            v.MouseFilter = MouseFilterEnum.Ignore;
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(new Medallion(here ? 52 : 44, Numerals[i])
            {
                Ring = here ? Style.Ember : done ? Style.Gold : Style.InkFaint, Ink = here ? Style.EmberHi : done ? Style.GoldHi : Style.InkDim,
                Core = done || here ? new Color("#3a2210") : new Color("#120f14"), Lit = here,
            });
            v.AddChild(mc);
            v.AddChild(Style.Label(Steps[i], Style.UiBold, Style.Caption, here ? Style.EmberHi : done ? Style.GoldHi : Style.InkDim, false, HorizontalAlignment.Center));
            v.Size = new Vector2(84, 80);
            b.AddChild(v);
            b.CustomMinimumSize = new Vector2(84, 80);
            road.AddChild(Nav.Skip(b));
            if (i < Steps.Length - 1)
            {
                var line = new ColorRect { Color = i < d.Step ? Style.Gold : Style.Line, CustomMinimumSize = new Vector2(16, 2), MouseFilter = MouseFilterEnum.Ignore };
                var lw = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
                lw.AddThemeConstantOverride("margin_top", 26);
                lw.AddChild(line);
                road.AddChild(lw);
            }
        }
        var rb = pad ? Style.PadButton("RB") : Style.Key(G.Key(Act.TabNext));
        rb.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        road.AddChild(rb);
        return road;
    }

    /// <summary>A choice as a crested card: its mark on a medallion, its name, its words; the one taken lit in ember.</summary>
    static Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null)
    {
        var b = Style.Button("", act);
        b.CustomMinimumSize = new Vector2(470, 92);
        Nav.Id(b, $"choice:{name}");
        var box = OrnateBox.Make(OrnateBox.Kind.Card, 0, on ? Style.Ember : Style.GoldDim);
        box.Crest = on ? 40 : 0;
        box.Glow = on ? 0.8f : 0;
        var hover = OrnateBox.Make(OrnateBox.Kind.Card, 0, on ? Style.EmberHi : Style.Gold);
        hover.Crest = 40;
        b.AddThemeStyleboxOverride("normal", box);
        b.AddThemeStyleboxOverride("hover", hover);
        b.AddThemeStyleboxOverride("pressed", hover);
        if (on) b.SetMeta("on", true);
        var row = Style.H(14, new Medallion(64, "", glyph) { Ring = on ? Style.Ember : Style.Gold, Ink = on ? Style.EmberHi : Style.GoldHi, Lit = on });
        var words = Style.V(0, Style.Label(name.ToUpperInvariant(), Style.Display, 21, on ? Colors.White : Style.GoldHi), Style.Label(tag, Style.Ui, Style.Small, tagColor ?? Style.InkDim, true));
        words.CustomMinimumSize = new Vector2(360, 0);
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(words);
        row.Position = new Vector2(14, 14);
        row.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        return b;
    }

''')
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
