PAIRS = [
("""            var s = GetParent<Control>().Size;
            for (int k = 5; k >= 1; k--)
                DrawRect(new Rect2(new Vector2(-k * 2 + 5, -k * 2 + 9), s + new Vector2(k * 4, k * 4)), new Color(0, 0, 0, 0.09f));""",
"""            // (drawn from the sheet's own corner: the sheet lays this out inside its margins)
            var s = GetParent<Control>().Size;
            for (int k = 5; k >= 1; k--)
                DrawRect(new Rect2(new Vector2(-k * 2 + 5, -k * 2 + 9) - Position, s + new Vector2(k * 4, k * 4)), new Color(0, 0, 0, 0.09f));"""),
("""                var b = Nav.Id(Style.Button($"{other.Chart!.Name}  ·  {other.Chart.Tier}", () => { chartUid = uid; Sound.Sfx.Page(); Refresh(); }, false, true), $"chart:{uid}");""",
"""                var b = Nav.Id(InkWord($"{other.Chart!.Name}, tier {other.Chart.Tier}", () => { chartUid = uid; Sound.Sfx.Page(); Refresh(); }, 15), $"chart:{uid}");"""),
("""            row.AddThemeConstantOverride("h_separation", 6);
            row.AddThemeConstantOverride("v_separation", 6);""",
"""            row.AddThemeConstantOverride("h_separation", 18);
            row.AddThemeConstantOverride("v_separation", 4);"""),
("""        var go = Nav.Id(Style.Button("Set it on the table", () => SetOut(chosen.Uid), true), "chart:set");
        go.CustomMinimumSize = new Vector2(0, 44);""",
"""        var go = Nav.Id(InkWord("Set it on the table", () => SetOut(chosen.Uid), 21), "chart:set");"""),
("""            var work = Nav.Id(Style.Button("Work it first", () => { ForgeScreen.PutDown = uid; Sound.Sfx.Page(); G.Open($"forge:{SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter}"); }, false), "chart:work");
            work.CustomMinimumSize = new Vector2(0, 44);
            var both = Style.H(Style.Gap2, work, go);
            go.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            v.AddChild(both);""",
"""            var work = Nav.Id(InkWord("Work it first", () => { ForgeScreen.PutDown = uid; Sound.Sfx.Page(); G.Open($"forge:{SurvivorUnchained.Rpg.Crafting.Rules.Charts.Crafter}"); }, 19), "chart:work");
            work.AddThemeColorOverride("font_color", InkSoft);
            v.AddChild(Style.H(28, go, work));"""),
("""                var raise = Nav.Id(Style.Button(r == 0 ? "Learn it" : "Deepen it", () => { if (Atlas.Raise(w, bias)) { Sound.Sfx.Discovery(); Refresh(); } }, true, true), $"bias:{id}");
                raise.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;""",
"""                var raise = Nav.Id(InkWord(r == 0 ? "Learn it" : "Deepen it", () => { if (Atlas.Raise(w, bias)) { Sound.Sfx.Discovery(); Refresh(); } }, 17), $"bias:{id}");"""),
("""                    follow.AddChild(Nav.Id(Style.Segment(Style.Cap1(p.Name), Atlas.Road(w) == pid, () => { Atlas.Follow(w, pid); Refresh(); }), $"road:{pid}"));""",
"""                    var word = InkWord(Style.Cap1(p.Name), () => { Atlas.Follow(w, pid); Refresh(); }, 15);
                    // (the people followed is in full ink, the rest faint)
                    if (Atlas.Road(w) != pid) word.AddThemeColorOverride("font_color", InkSoft with { A = 0.7f });
                    follow.AddChild(Nav.Id(word, $"road:{pid}"));"""),
("""        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 120, InkSoft with { A = 0.2f }));
        v.AddChild(rose);""",
"""        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 96, InkSoft with { A = 0.2f }));
        v.AddChild(rose);"""),
]
