p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Front.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""/// Four steps, each a question the world will ask again later: Calling (how
/// do you fight?), Arms (with what, and what do your hands do?), Origin
/// (where are you from?), Name (who are you?). The figure by the fire
/// changes as you choose; the panel on the right says what each choice means.
/// </summary>""",
"""/// Four steps, each a question the world will ask again later: Calling (how
/// do you fight?), Arms (with what, and what do your hands do?), Origin
/// (where are you from?), Name (who are you?). The figure by the fire
/// changes as you choose; the panel on the right says what each choice means.
/// Enter or A on a choice takes it; on the one already taken, it moves on
/// (so A, A walks through); LB and RB turn the steps.
/// </summary>"""),
("""    void Begin()
    {
        if (!CanBegin) { Set(() => d.Step = 3); return; }
        G.BeginJourney(d.Choice());
    }""",
"""    void Begin()
    {
        if (!CanBegin)
        {
            // No name yet: offer one from the road (a pad cannot type), and wait for a second word.
            Set(() => { d.Step = 3; d.Name = Names[Random.Shared.Next(Names.Length)]; });
            Nav.FocusId = "begin";
            return;
        }
        G.BeginJourney(d.Choice());
    }"""),
("""        var steps = Style.H(4);
        for (int i = 0; i < Steps.Length; i++)
        {
            int s = i;
            steps.AddChild(Style.Button($"{Numerals[i]}  {Steps[i]}", () => Set(() => d.Step = s), d.Step == i, true));
        }
        col.AddChild(steps);""",
"""        var steps = Style.H(4);
        bool pad = Controls.Instance.UsingPad;
        steps.AddChild(pad ? Style.PadButton("LB") : Style.Key(G.Key(Act.TabPrev)));
        for (int i = 0; i < Steps.Length; i++)
        {
            int s = i;
            steps.AddChild(Nav.Skip(Style.Button($"{Numerals[i]}  {Steps[i]}", () => Set(() => d.Step = s), d.Step == i, true)));
        }
        steps.AddChild(pad ? Style.PadButton("RB") : Style.Key(G.Key(Act.TabNext)));
        col.AddChild(steps);"""),
("""        var foot = Style.H(10, Style.Button(d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); }));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(d.Step < 3 ? Style.Button($"Next: {Steps[d.Step + 1]}", () => Set(() => d.Step++), true) : Style.Button("Begin the journey", Begin, true));
        col.AddChild(foot);""",
"""        var foot = Style.H(10, Nav.Id(Style.Button(d.Step > 0 ? "Back" : "Leave", () => { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); }), "back"));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(d.Step < 3 ? Nav.Id(Style.Button($"Next: {Steps[d.Step + 1]}", () => Set(() => d.Step++), true), "next") : Nav.Id(Style.Button("Begin the journey", Begin, true), "begin"));
        col.AddChild(foot);"""),
("""    static Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null)
    {
        var b = Style.Button("", act);
        b.CustomMinimumSize = new Vector2(440, 66);
        if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4));
        var row = Style.H(12, Glyphs.Icon(glyph, 28, on ? Style.EmberHi : Style.Gold));
        var words = Style.V(0, Style.Label(name, Style.Display, 17, on ? Colors.White : Style.GoldHi), Style.Label(tag, Style.Ui, 13, tagColor ?? Style.InkDim, true));
        words.CustomMinimumSize = new Vector2(360, 0);
        row.AddChild(words);
        row.Position = new Vector2(12, 8);
        b.AddChild(row);
        return b;
    }""",
"""    static Button Choice(string glyph, string name, string tag, bool on, Action act, Color? tagColor = null)
    {
        var b = Style.Button("", act);
        b.CustomMinimumSize = new Vector2(440, 70);
        Nav.Id(b, $"choice:{name}");
        if (on)
        {
            b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
            b.SetMeta("on", true);
        }
        var row = Style.H(12, Glyphs.Icon(glyph, 30, on ? Style.EmberHi : Style.Gold));
        var words = Style.V(0, Style.Label(name, Style.Display, 18, on ? Colors.White : Style.GoldHi), Style.Label(tag, Style.Ui, Style.Caption, tagColor ?? Style.InkDim, true));
        words.CustomMinimumSize = new Vector2(360, 0);
        row.AddChild(words);
        row.Position = new Vector2(12, 8);
        row.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        return b;
    }"""),
("""        v.AddChild(Style.H(8, Style.SubLabel("Art in hand"), Style.Label("you know all four; more are learned on the road", Style.TextItalic, 13, Style.InkDim)));""",
"""        v.AddChild(Style.H(8, Style.SubLabel("Art in hand"), Style.Label("you know all four; more are learned on the road", Style.TextItalic, Style.Caption, Style.InkDim)));"""),
("""        v.AddChild(Style.H(8, nameBox, Style.Button("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), false, true)));
        Callable.From(() => nameBox?.GrabFocus()).CallDeferred();""",
"""        v.AddChild(Style.H(8, Nav.Skip(nameBox), Nav.Id(Style.Button("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), false, true), "roadname")));
        // The keyboard types at once; a pad cannot type, so it is offered names instead.
        if (!Controls.Instance.UsingPad) Callable.From(() => nameBox?.GrabFocus()).CallDeferred();
        else if (d.Name.Trim() == "") Nav.Prefer = "roadname";"""),
("""            var slider = new HSlider { MinValue = 0, MaxValue = 1.5, Step = 0.1, Value = d.Figure, CustomMinimumSize = new Vector2(220, 24) };
            slider.DragEnded += _ => Set(() => d.Figure = slider.Value);""",
"""            var slider = new HSlider { MinValue = 0, MaxValue = 1.5, Step = 0.1, Value = d.Figure, CustomMinimumSize = new Vector2(220, 24), FocusMode = FocusModeEnum.None };
            slider.DragEnded += _ => Set(() => d.Figure = slider.Value);
            // With focus, left and right move it a step.
            Nav.Mark(slider, "figure", null, adjust: dir => Set(() => d.Figure = Math.Clamp(Math.Round((d.Figure + dir * 0.1) * 10) / 10, 0, 1.5)));"""),
("""            var b = new Button { CustomMinimumSize = new Vector2(30, 30), FocusMode = FocusModeEnum.None, TooltipText = c.Name };""",
"""            var b = new Button { CustomMinimumSize = new Vector2(32, 32), FocusMode = FocusModeEnum.None, TooltipText = c.Name };
            Nav.Id(b, $"swatch:{now}:{id}");"""),
("""        h.AddChild(Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.Ui, 14, Style.InkDim));""",
"""        h.AddChild(Style.Label(list.FirstOrDefault(c => c.Id == now)?.Name ?? "", Style.Ui, Style.Caption, Style.InkDim));"""),
("""    public override bool Key(Act a)
    {
        if (nameBox != null && nameBox.HasFocus() && a is not (Act.Cancel or Act.Confirm)) return true;
        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(3, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }
        if (a == Act.Cancel) { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); return true; }
        if (a == Act.Confirm) { if (d.Step < 3) Set(() => d.Step++); else Begin(); return true; }
        return true;
    }""",
"""    public override bool Key(Act a)
    {
        // Typing a name: the letters are the name's, not the menu's.
        if (nameBox != null && nameBox.HasFocus() && a is not (Act.Cancel or Act.Confirm)) return true;
        if (nameBox != null && nameBox.HasFocus() && a == Act.Confirm) { nameBox.ReleaseFocus(); Begin(); return true; }
        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(3, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }
        if (a == Act.Cancel) { if (d.Step > 0) Set(() => d.Step--); else G.CancelCreation(); return true; }
        if (a == Act.Confirm)
        {
            // On a choice not yet taken, Enter or A takes it (focus does it); otherwise, onward.
            if (Nav.KeyMode && Nav.Current is { } c && !c.C.HasMeta("on")) return false;
            if (d.Step < 3) Set(() => d.Step++); else Begin();
            return true;
        }
        return false;
    }"""),
]
for old, new in pairs:
    assert old in s, old[:90]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')
