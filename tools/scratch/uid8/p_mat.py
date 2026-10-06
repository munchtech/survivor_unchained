PAIRS = [
("""        AddChild(Style.Scrim(null, 0.75f));
        var card = Style.Centered(Style.Panel(Style.Plate(26)), new Vector2(560, 300));
        AddChild(card);
        var v = Style.V(10, Style.Cap("For adults", 18));
        if (left) v.AddChild(Style.Label("Another time, then. The fire will still be burning.", Style.Text, 17, Style.Ink, true));
        else
        {
            v.AddChild(Style.Label("Survivor Unchained is made for adults. It has graphic violence and gore, strong language, revealing clothes and sexual themes. Nothing sexual is shown on screen.", Style.Text, 17, Style.Ink, true));
            v.AddChild(Style.Label("Gore can be reduced or turned off in Settings.", Style.TextItalic, 15, Style.InkDim, true));
            v.AddChild(Style.H(10, Style.Button("I am 18 or over", Agree, true), Style.Button("Leave", () => { left = true; Refresh(); })));
        }
        card.AddChild(v);""", """        AddChild(Style.Scrim(null, 0.75f));
        // The first thing the game says: a fitted panel over the fire, its words as type and its two
        // answers as words with their keys (no card, no buttons' boxes).
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        AddChild(centre);
        var panel = Style.Panel(Kit.Window(Margin + 8, Margin, Margin));
        panel.CustomMinimumSize = new Vector2(620, 0);
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        centre.AddChild(panel);
        var v = Style.V(Style.Gap4, new Title("For adults", 30, false));
        Label Words(string t, bool quiet = false) => Style.Label(t, quiet ? Style.TextItalic : Style.Text, quiet ? 16 : 18, quiet ? Kit.Dim : Kit.Ink2, true, HorizontalAlignment.Center, false);
        if (left) v.AddChild(Words("Another time, then. The fire will still be burning."));
        else
        {
            v.AddChild(Words("Survivor Unchained is made for adults. It has graphic violence and gore, strong language, revealing clothes and sexual themes. Nothing sexual is shown on screen."));
            v.AddChild(Words("Gore can be reduced or turned off in Settings.", true));
            var agree = Nav.Id(Kit.Keyed(Act.Confirm, "I am 18 or over", Agree, Style.EmberHi), "agree");
            var leave = Nav.Id(Kit.Keyed(Act.Cancel, "Leave", () => { left = true; Refresh(); }), "leave");
            v.AddChild(Style.V(Style.Gap3, Kit.RuleH(), Style.H(0, agree, new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore }, leave)));
        }
        panel.AddChild(v);"""),
("""            if (a == Act.Confirm && !left) { Agree(); return true; }
            return true;""", """            if (a == Act.Confirm && !left) { Agree(); return true; }
            if (a == Act.Cancel && !left) { left = true; Refresh(); }
            return true;"""),
]
