PAIRS = [
("""        paper.SizeFlagsVertical = SizeFlags.Fill;""",
"""        // (each as tall as its own words: sheets lying on a table, not a row of equal boxes)
        paper.SizeFlagsVertical = SizeFlags.ShrinkBegin;"""),
("""        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        v.AddChild(L("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, InkSoft));""",
"""        v.AddChild(Style.Gap(4));
        v.AddChild(L("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, InkSoft));"""),
("""        v.AddChild(L($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, InkSoft));""",
"""        v.AddChild(L(Kit.Balance($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, 380), Style.TextItalic, Style.Caption, InkSoft));"""),
("""        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 96, InkSoft with { A = 0.2f }));
        v.AddChild(rose);""",
"""        var rose = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        rose.AddChild(Glyphs.Icon("compass", 72, InkSoft with { A = 0.2f }));
        v.AddChild(rose);"""),
("""        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        // The others carried, to choose among (the highest tier first).""",
"""        // The others carried, to choose among (the highest tier first)."""),
]
