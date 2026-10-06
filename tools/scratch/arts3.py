R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\ArtsScreen.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

rep("""        var left = Pane(page, new Rect2(0, 56, 560, 864));
        left.AddChild(new Section($"Known  ·  {known.Count}"));
        left.AddChild(Medals(ch, known.Select(Abilities.ById), true));
        var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
        if (rest.Count > 0)
        {
            left.AddChild(new Section("Not yet learned", "manuals teach them"));
            left.AddChild(Medals(ch, rest, false));
        }""", """        var pane = Pane(page, new Rect2(0, 56, 560, 864));
        var left = Style.V(Style.Gap3);
        left.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var scroll = Style.Scroll(left);
        scroll.SizeFlagsVertical = SizeFlags.ExpandFill;
        pane.AddChild(scroll);
        left.AddChild(new Section($"Known  ·  {known.Count}"));
        left.AddChild(Medals(ch, known.Select(Abilities.ById), true));
        var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
        if (rest.Count > 0)
        {
            left.AddChild(new Section("Not yet learned", "manuals teach them"));
            left.AddChild(Medals(ch, rest, false));
        }""")
rep("""        head.AddChild(words);
        d.AddChild(head);
        d.AddChild(Facets(ch, a, known));
    }""", """        head.AddChild(words);
        d.AddChild(head);
        d.AddChild(Facets(ch, a, known));
        d.AddChild(Road(rank));
    }

    /// <summary>The road to mastery: the five ranks in a line, what each brings, this one lit.</summary>
    static Control Road(int rank)
    {
        var v = Style.V(Style.Gap2, new Section("The road to mastery", "every use, and what dies while it is fresh"));
        var row = Style.H(0);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        for (int k = 1; k <= Abilities.MaxRank; k++)
        {
            bool reached = k <= rank, here = k == rank;
            string gives = k switch { 2 => "a facet", 4 => "a second facet", 5 => "mastered", 1 => "learned", _ => "stronger" };
            var m = new Medallion(here ? 64 : 52, Numerals[k - 1])
            {
                Ring = here ? Style.Ember : reached ? Style.Gold : Style.InkFaint,
                Ink = here ? Style.EmberHi : reached ? Style.GoldHi : Style.InkDim,
                Core = reached ? new Color("#3a2210") : new Color("#120f14"),
                Lit = here,
            };
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(0, 66) };
            mc.AddChild(m);
            var col = Style.V(2, mc,
                Style.Label(gives, Style.UiBold, Style.Caption, reached ? Style.GoldHi : Style.InkDim, false, HorizontalAlignment.Center),
                Style.Label($"+{(Abilities.RankPower(k) - 1) * 100:0}% strength", Style.Ui, Style.Caption, Style.InkFaint, false, HorizontalAlignment.Center));
            col.CustomMinimumSize = new Vector2(150, 0);
            row.AddChild(col);
            if (k < Abilities.MaxRank)
            {
                // The road between two ranks: gold where it is walked.
                var line = new ColorRect { Color = k < rank ? Style.Gold : Style.Line, CustomMinimumSize = new Vector2(70, 2), SizeFlagsVertical = SizeFlags.ShrinkBegin, MouseFilter = MouseFilterEnum.Ignore };
                var lw = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
                lw.AddThemeConstantOverride("margin_top", 32);
                lw.AddChild(line);
                row.AddChild(lw);
            }
        }
        v.AddChild(row);
        return v;
    }""")
rep("""            b.CustomMinimumSize = new Vector2(287, 300);""", """            b.CustomMinimumSize = new Vector2(287, 280);""")
rep("""            inner.Size = new Vector2(255, 268);""", """            inner.Size = new Vector2(255, 248);""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
