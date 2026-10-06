PAIRS = [
("""            var l = Style.Label(label, Style.UiBold, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            l.CustomMinimumSize = new Vector2(200, 0);
            l.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
            var r = Style.H(Style.Gap5, l);""", """            // (set on the words' own line: they sit 2 px into their row, over their underline's room)
            var l = Style.Label(label, Style.UiBold, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            l.CustomMinimumSize = new Vector2(150, 0);
            var m = new MarginContainer { MouseFilter = Control.MouseFilterEnum.Ignore, SizeFlagsVertical = Control.SizeFlags.ShrinkBegin };
            m.AddThemeConstantOverride("margin_top", 2);
            m.AddChild(l);
            var r = Style.H(Style.Gap5, m);"""),
("""            var side = Plate(pair, panel == "controls" ? 600 : 780);""", """            var side = Plate(pair, 600);"""),
]
