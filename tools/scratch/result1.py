R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit('ArenaResult.cs', [
("""/// <summary>An arena over (Arena/Arena.cs): how long, how many, and what
/// comes out of it (experience, gold, skills discovered) set against what
/// stays behind (the build the ember made). Then back to the story.</summary>""",
"""/// <summary>An arena over (Arena/Arena.cs): how long, how many, and what
/// comes out of it (experience, gold, skills discovered) set against what
/// stays behind (the build the ember made). Then back to the story. The
/// end of half an hour is what the player remembers of it (the peak-end
/// rule), so the tally counts up rather than appearing, one after another.</summary>"""),
("""    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";
""",
"""    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    // The numbers counting up: each label, its final value, how it is written, when it starts.
    readonly System.Collections.Generic.List<(Label L, double To, System.Func<double, string> Fmt, double At)> counts = new();
    double shownFor;

    public override void _Process(double delta)
    {
        base._Process(delta);
        shownFor += delta;
        foreach (var (l, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(l)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            l.Text = fmt(to * k);
        }
    }
"""),
("""        var tally = Style.H(28,
            Stat("hourglass", Clock(r.Seconds), r.Won ? "survived" : "held out"),
            Stat("skull", $"{r.Kills:N0}", "slain"),
            Stat("flame", $"{r.EmberLevel}", "ember"));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", Clock(beyond), "past the half hour"));""",
"""        counts.Clear();
        var tally = Style.H(36,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.2),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.45),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 0.7));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", beyond, Clock, "past the half hour", 0.95));"""),
("""        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, 15, Style.EmberHi, false, HorizontalAlignment.Center));""",
"""        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));"""),
("""        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  level {G.Journey.Ch.Level}" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));""",
"""        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  you are level {G.Journey.Ch.Level} now" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));"""),
("""            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, 14, Style.InkDim, true));""",
"""            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""                    Style.Label($"{w.Evolution?.Name ?? w.Def.Name}  {Numeral(w.Rank)}", Style.Ui, 15, Style.InkDim)));""",
"""                    Style.Label($"{w.Evolution?.Name ?? w.Def.Name}  {Numeral(w.Rank)}", Style.Ui, Style.Small, Style.InkDim)));"""),
("""                    stay.AddChild(Style.H(8, Glyphs.Icon(bd.Icon, 20, Style.InkDim), Style.Label(bd.Max > 1 ? $"{bd.Name}  {Numeral(rank)}" : bd.Name, Style.Ui, 15, Style.InkDim)));
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, 14, Style.InkFaint, true));""",
"""                    stay.AddChild(Style.H(8, Glyphs.Icon(bd.Icon, 20, Style.InkDim), Style.Label(bd.Max > 1 ? $"{bd.Name}  {Numeral(rank)}" : bd.Name, Style.Ui, Style.Small, Style.InkDim)));
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));"""),
("""        wrap.AddChild(Style.Label(after, Style.TextItalic, 17, Style.Ink, true, HorizontalAlignment.Center));
        var acts = Style.H(12, Style.Button("Back to the road", () => G.LeaveArena(r), true));
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
    }""",
"""        wrap.AddChild(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
        var go = Style.Button("", () => G.LeaveArena(r), true);
        var gr = Style.H(8, Style.Prompt(Act.Confirm), Style.Label("Back to the road", Style.UiBold, Style.Body, new Color("#ffe4b0")));
        gr.MouseFilter = MouseFilterEnum.Ignore;
        gr.Position = new Vector2(16, 7);
        go.AddChild(gr);
        go.CustomMinimumSize = new Vector2(gr.GetCombinedMinimumSize().X + 32, 42);
        var acts = Style.H(12, go);
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
    }"""),
("""    static Control Stat(string glyph, string value, string label) =>
        Style.V(0, Style.H(6, Glyphs.Icon(glyph, 20, Style.GoldHi), Style.Label(value, Style.Display, 30, Style.GoldHi)),
            Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 11, Style.Gold, false, HorizontalAlignment.Center));""",
"""    Control Stat(string glyph, double value, System.Func<double, string> fmt, string label, double at)
    {
        var l = Style.Label(fmt(0), Style.Display, 34, Style.GoldHi);
        counts.Add((l, value, fmt, at));
        var h = Style.H(8, Glyphs.Icon(glyph, 24, Style.GoldHi), l);
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(0, h, Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.Gold, false, HorizontalAlignment.Center));
    }"""),
("""    static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, 17, c));""",
"""    static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, Style.Body, c));"""),
("""        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, 16, col), Style.Label(what, Style.TextItalic, 13, Style.InkDim)));""",
"""        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, Style.Small, col), Style.Label(what, Style.TextItalic, Style.Caption, Style.InkDim)));"""),
("""    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }
        return true;
    }""",
"""    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }
        // Nothing else leaves it: the arena's end is read, not skipped by a stray key.
        return a is not (Act.Up or Act.Down or Act.Left or Act.Right);
    }"""),
])

edit('MapTable.cs', [
("""        v.AddChild(row);
    }
}""",
"""        v.AddChild(row);
        if (Controls.Instance.UsingPad) v.AddChild(Footer((Act.Left, "Choose a map"), (Act.Confirm, "Enter the arena"), (Act.Cancel, "Close")));
    }
}"""),
("""            var pick = o;
            card.AddChild(Style.Label("Half an hour; the ember from nothing", Style.TextItalic, 13, Style.InkDim, true));
            card.AddChild(Style.Button("Enter the arena", () => G.SetOut(pick), true));""",
"""            var pick = o;
            card.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
            card.AddChild(Style.Label("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, Style.InkDim, true));
            card.AddChild(Nav.Id(Style.Button("Enter the arena", () => G.SetOut(pick), true), $"enter:{o.Spec.Name}"));"""),
("""                Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, 13, Style.Gold),
                Style.Label(o.Spec.Name, Style.Display, 26, Style.GoldHi, true),
                Style.Label($"Held by {people.Name}", Style.TextItalic, 16, Style.Ink, true),
                Style.Label($"Ruled by {people.BossName}", Style.Text, 15, Style.InkDim, true),
                Style.Label($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, 13, new Color("#b8a8d8"), true),""",
"""                Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, Style.Gold), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
                Style.Label(o.Spec.Name, Style.Display, 26, Style.GoldHi, true),
                Style.Label($"Held by {people.Name}", Style.TextItalic, Style.Body, Style.Ink, true),
                Style.Label($"Ruled by {people.BossName}", Style.Text, Style.Small, Style.InkDim, true),
                Style.Label($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, Style.Caption, new Color("#b8a8d8"), true),"""),
("""                card.AddChild(Style.V(1,
                    Style.Label(oath.Name, Style.UiBold, 15, Style.Ink, true),
                    Style.Label($"Asks: {oath.Asks}", Style.Text, 14, new Color("#d08a6a"), true),
                    Style.Label($"Gives: {oath.Gives}", Style.Text, 14, new Color("#9ac48a"), true),
                    Style.Label($"Answered by {oath.Answer}", Style.TextItalic, 13, new Color("#b8a8d8"), true)));""",
"""                card.AddChild(Style.V(1,
                    Style.Label(oath.Name, Style.UiBold, Style.Small, Style.Ink, true),
                    Style.Label($"Asks: {oath.Asks}", Style.Text, Style.Caption, new Color("#e09a7a"), true),
                    Style.Label($"Gives: {oath.Gives}", Style.Text, Style.Caption, new Color("#a8d498"), true),
                    Style.Label($"Answered by {oath.Answer}", Style.TextItalic, Style.Caption, new Color("#c0b0e0"), true)));"""),
("""            if (o.Spec.Oaths.Count == 0) card.AddChild(Style.Label("Sworn under no oath.", Style.TextItalic, 15, Style.InkDim, true));""",
"""            if (o.Spec.Oaths.Count == 0) card.AddChild(Style.Label("Sworn under no oath.", Style.TextItalic, Style.Small, Style.InkDim, true));"""),
])
print('done')
