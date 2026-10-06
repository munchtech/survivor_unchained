p = 'godot/src/Ui/Menus.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')
a = s.index('    protected override void Build()\n    {\n        var sum = Chapter.Summary(')
b = s.index('    public override bool Key(Act a)\n    {\n        // Enter keeps walking')
new = '''    protected override void Build()
    {
        // The survivor's own book, lying open on the dark (docs/UI_DESIGN.md 7.10): the same
        // book as the journal, so the chapter closes in the hand that kept it.
        var sum = Chapter.Summary(G.Journey.Ch, G.Journey.World);
        HideHud();
        AddChild(new Backdrop(null, 0.94f));
        var kicker = Style.Label("THE END OF THE FIRST CHAPTER", Style.UiHeavy, 15, Style.Gold, false, HorizontalAlignment.Center);
        kicker.Position = new Vector2(0, 34); kicker.Size = new Vector2(1920, 20);
        AddChild(kicker);
        var plaque = new Plaque("The Waystation", 46, 170);
        plaque.Position = new Vector2((1920 - plaque.CustomMinimumSize.X) / 2, 58);
        AddChild(plaque);
        var epithet = Style.Label(sum.Epithet, Style.TextItalic, 21, Style.Ink, false, HorizontalAlignment.Center);
        epithet.Position = new Vector2(0, 128); epithet.Size = new Vector2(1920, 28);
        AddChild(epithet);

        var book = new OpenBook(new Vector2(1560, 760)) { Position = new Vector2(180, 172) };
        AddChild(book);
        var ink = Style.ParchmentInk;
        var soft = new Color("#5a4a36");
        Label P(string t, int size = 16, Font? f = null, Color? c = null) => Style.Label(t, f ?? Style.Text, size, c ?? ink, true, HorizontalAlignment.Left, false);
        Control H(string t) => Style.V(2, Style.Label(t, Style.Display, 23, new Color("#3a2414"), false, HorizontalAlignment.Left, false),
            new ColorRect { Color = new Color("#3a2414") with { A = 0.35f }, CustomMinimumSize = new Vector2(0, 1), MouseFilter = MouseFilterEnum.Ignore });

        // The left leaf: what was done, and what still waits.
        var left = Style.V(Style.Gap2, H("What was done"));
        foreach (var t in sum.Threads)
        {
            var tone = t.Tone switch { ThreadTone.Good => new Color("#3a6a2a"), ThreadTone.Bad => new Color("#8a2a1a"), _ => soft };
            var name = Style.H(10, P(t.Name, 18, Style.TextBold), P(t.Verdict, 16, Style.TextItalic, tone));
            left.AddChild(Style.V(2, name, P(t.Outcome)));
            foreach (var bt in t.Beats.TakeLast(3)) left.AddChild(P($"\\u2022 {bt}", 15, Style.Text, soft));
        }
        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(H("Still waiting"));
        foreach (var o in sum.Open) left.AddChild(Style.V(1, P(o.Name, 17, Style.TextBold), P(o.Line, 15, Style.TextItalic, soft)));
        var ls = Style.Scroll(left);
        Style.Fill(ls);
        book.Left.AddChild(ls);

        // The right leaf: who remembers, what the world says, and the tally on medallions at its foot.
        var right = Style.V(Style.Gap2, H("Who remembers you"));
        if (sum.People.Count == 0) right.AddChild(P("Nobody, yet. You kept to yourself.", 16, Style.TextItalic, soft));
        foreach (var pe in sum.People)
        {
            var warm = pe.Warmth >= 25 ? new Color("#3a6a2a") : pe.Warmth <= -25 ? new Color("#8a2a1a") : soft;
            right.AddChild(Style.V(1, Style.H(10, P(pe.Name, 17, Style.TextBold), P(pe.Role, 15, Style.TextItalic, soft)), P(Style.Cap1(pe.Regard), 16, Style.Text, warm)));
            if (pe.Knows != null) right.AddChild(P($"Knows that you {pe.Knows}.", 15, Style.Text, soft));
        }
        right.AddChild(Style.Gap(Style.Gap2));
        right.AddChild(H("What the world says you did"));
        if (sum.Deeds.Count == 0) right.AddChild(P("Nothing it has noticed. Give it time.", 16, Style.TextItalic, soft));
        foreach (var d in sum.Deeds) right.AddChild(P($"You {d}.", 16));
        var rs = Style.Scroll(right);
        rs.Size = new Vector2(book.Right.Size.X, book.Right.Size.Y - 128);
        book.Right.AddChild(rs);
        var tally = Style.H(Style.Gap3);
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var (label, value) in sum.Stats)
        {
            var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            med.AddChild(new Medallion(70, value));
            tally.AddChild(Style.V(4, med, Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 12, new Color("#5a3a1c"), false, HorizontalAlignment.Center)));
        }
        tally.Position = new Vector2(0, book.Right.Size.Y - 112);
        tally.Size = new Vector2(book.Right.Size.X, 104);
        book.Right.AddChild(tally);

        var acts = Style.H(Style.Gap3, Style.Button("Keep walking", G.CloseOverlay), Style.Button("Return to the fire", G.QuitToTitle, true));
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        acts.Position = new Vector2(0, 952); acts.Size = new Vector2(1920, 40);
        AddChild(acts);
        var note = Style.Label("Your journey is saved. The chapter ends here, but the road does not: the Waystation, the Verge and the Wayfinder's table are still yours to walk. What lies north is not written yet.", Style.TextItalic, Style.Caption, Style.InkDim, false, HorizontalAlignment.Center);
        note.Position = new Vector2(0, 1008); note.Size = new Vector2(1920, 24);
        AddChild(note);
    }

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok')
