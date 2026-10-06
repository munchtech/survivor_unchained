R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit('Menus.cs', [
("""    public Control Build()
    {
        var v = Style.V(2);""",
"""    public Control Build()
    {
        // It moves its own focus (the ember mark), so the screen's focus leaves it alone.
        var v = Nav.Skip(Style.V(2));"""),
("""            if (sub != null) row.AddChild(Style.Label(sub, Style.TextItalic, 15, new Color("#9a8e78")));""",
"""            if (sub != null) row.AddChild(Style.Label(sub, Style.TextItalic, Style.Small, new Color("#a89c84")));"""),
("""            b.MouseEntered += () => { if (Focus != index) { Focus = index; refresh(); } };
            b.Pressed += act;""",
"""            b.MouseEntered += () => { if (Focus != index) { Focus = index; refresh(); } };
            b.Pressed += act;
            if (on) row.AddChild(Style.Prompt(Act.Confirm));"""),
("""        if (a == Act.Up) { Focus = (Focus + Items.Count - 1) % Items.Count; refresh(); return true; }
        if (a == Act.Down) { Focus = (Focus + 1) % Items.Count; refresh(); return true; }
        if (a == Act.Confirm) { Items[Focus].Act(); return true; }""",
"""        if (a == Act.Up) { Focus = (Focus + Items.Count - 1) % Items.Count; Sound.Sfx.Hover(); refresh(); return true; }
        if (a == Act.Down) { Focus = (Focus + 1) % Items.Count; Sound.Sfx.Hover(); refresh(); return true; }
        if (a == Act.Confirm) { Sound.Sfx.Click(); Items[Focus].Act(); return true; }"""),
("""        Control Row(string label, string[] options, string now, Action<string> set)
        {
            var r = Style.H(8);
            var l = Style.Label(label, Style.UiBold, 16, Style.Ink);
            l.CustomMinimumSize = new Vector2(150, 0);""",
"""        Control Row(string label, string[] options, string now, Action<string> set)
        {
            var r = Style.H(8);
            var l = Style.Label(label, Style.UiBold, Style.Small, Style.Ink);
            l.CustomMinimumSize = new Vector2(190, 0);"""),
("""        v.AddChild(Row("Screen shake", ["full", "reduced", "off"], s.Motion, x => s.Motion = x));
        v.AddChild(Style.Label("Lower settings trade shadow detail, grass and ambient occlusion for speed. Reduced gore keeps a little blood and throws nothing. Screen shake off also stops the world holding still on a heavy blow.",
            Style.TextItalic, 14, Style.InkDim, true));""",
"""        v.AddChild(Row("Screen shake", ["full", "reduced", "off"], s.Motion, x => s.Motion = x));
        v.AddChild(Row("Health under you", ["on", "off"], s.UnderBar ? "on" : "off", x => s.UnderBar = x == "on"));
        v.AddChild(Style.Label("Lower settings trade shadow detail, grass and ambient occlusion for speed. Reduced gore keeps a little blood and throws nothing. Screen shake off also stops the world holding still on a heavy blow. Health under you draws your health beneath your feet in a night's fight.",
            Style.TextItalic, Style.Caption, Style.InkDim, true));"""),
("""        ("Move", [Act.Up, Act.Left, Act.Down, Act.Right], "Left stick"), ("Dash", [Act.Dash], null), ("Ability", [Act.Ability], null),
        ("Draught", [Act.Ultimate], null), ("Talk, use, pick up", [Act.Interact], null), ("Pack", [Act.Inventory], null),
        ("Self", [Act.Character], "Menu"), ("Arts", [Act.Arts], "Menu"), ("Journal", [Act.Journal], "Menu"), ("Map", [Act.Map], "Menu"), ("Pause", [Act.Pause], null),
        ("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], null), ("Draft: banish", [Act.Banish], null),""",
"""        ("Move", [Act.Up, Act.Left, Act.Down, Act.Right], "Left stick"), ("Dash", [Act.Dash], null), ("Ability", [Act.Ability], null),
        ("Draught", [Act.Ultimate], null), ("Talk, use, pick up", [Act.Interact], null), ("Pack", [Act.Inventory], "View"),
        ("Self", [Act.Character], "View, then RB"), ("Arts", [Act.Arts], "View, then RB"), ("Journal", [Act.Journal], "View, then RB"), ("Map", [Act.Map], "View, then RB"), ("Pause", [Act.Pause], null),
        ("Turn the book's pages", [Act.TabPrev, Act.TabNext], "LB / RB"), ("A screen's own pages", [Act.SubPrev, Act.SubNext], "LT / RT"),
        ("In menus: choose, back", [Act.Confirm, Act.Cancel], "A, B"), ("In menus: more", [Act.Alt], "X, Y"),
        ("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], "X"), ("Draft: banish", [Act.Banish], "Y"),"""),
("""            grid.AddChild(Style.Label(label, Style.UiBold, 15, Style.Ink));""",
"""            grid.AddChild(Style.Label(label, Style.UiBold, Style.Caption, Style.Ink));"""),
("""            grid.AddChild(Style.Label(pads == "" ? "-" : pads, Style.Ui, 14, Style.InkDim));
        }
        AddChild(grid);
        AddChild(Style.H(12, Style.Label(waiting != null ? "Press the new key, or Escape to leave it." : "Click a gold key to change it. Most attacks fire on their own.", Style.TextItalic, 14, Style.InkDim),""",
"""            grid.AddChild(Style.Label(pads == "" ? "-" : pads, Style.Ui, Style.Caption, Style.InkDim));
        }
        AddChild(grid);
        AddChild(Style.H(12, Style.Label(waiting != null ? "Press the new key, or Escape to leave it." : "Click a gold key to change it. Most attacks fire on their own.", Style.TextItalic, Style.Caption, Style.InkDim),"""),
# Pause
("""            var box = Style.Centered(Style.Panel(Style.Plate(22)), panel == "controls" ? new Vector2(760, 640) : new Vector2(640, 380));
            AddChild(box);
            var v = Style.V(10, Style.Cap(panel == "controls" ? "Controls" : "Settings", 18), Style.Rule());
            v.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            v.AddChild(Style.Button("Back", () => { panel = ""; Refresh(); }));
            box.AddChild(v);
            return;""",
"""            var box = Style.Centered(Style.Panel(Style.Plate(22)), panel == "controls" ? new Vector2(860, 780) : new Vector2(700, 440));
            AddChild(box);
            var v = Style.V(10, Style.Cap(panel == "controls" ? "Controls" : "Settings", 18), Style.Rule());
            v.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            v.AddChild(Style.Button("Back", () => { panel = ""; Refresh(); }));
            box.AddChild(v);
            Nav.Scope = box;
            return;"""),
("""        menu.Add("Leave to the title", G.QuitToTitle);
        menu.Add("Quit the game", G.QuitGame);
        var plate = Style.Centered(Style.Panel(Style.Plate(22)), new Vector2(460, 640));
        AddChild(plate);
        var col = Style.V(6, Style.Label("PAUSED", Style.Display, 26, Style.GoldHi, false, HorizontalAlignment.Center), Style.Rule(), menu.Build());
        var keys = Style.H(10);
        foreach (var (a, name) in new[] { (Act.Inventory, "Pack"), (Act.Character, "Self"), (Act.Arts, "Arts"), (Act.Journal, "Journal"), (Act.Map, "Map") })
            keys.AddChild(Style.H(4, Style.Key(G.Key(a)), Style.Label(name, Style.Ui, 13, Style.InkDim)));
        col.AddChild(keys);
        plate.AddChild(col);
    }

    public override bool Key(Act a)
    {
        if (panel != "")
        {
            if (a is Act.Cancel or Act.Pause or Act.Confirm) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }""",
"""        menu.Add("Leave to the title", G.QuitToTitle);
        menu.Add("Quit the game", G.QuitGame);
        Nav.Scope = null;
        var plate = Style.Panel(Style.Plate(22));
        plate.CustomMinimumSize = new Vector2(460, 0);
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        centre.AddChild(plate);
        AddChild(centre);
        var col = Style.V(6, Style.Label("PAUSED", Style.Display, 26, Style.GoldHi, false, HorizontalAlignment.Center), Style.Rule(), menu.Build());
        col.AddChild(Style.Gap(Style.Gap2));
        // The book's keys, as a reminder: each opens its page from play.
        var keys = Style.H(10);
        keys.Alignment = BoxContainer.AlignmentMode.Center;
        if (Controls.Instance.UsingPad) keys.AddChild(Style.Hint(Act.Inventory, "Pack, Self, Arts, Journal, Map"));
        else foreach (var (a, name) in new[] { (Act.Inventory, "Pack"), (Act.Character, "Self"), (Act.Arts, "Arts"), (Act.Journal, "Journal"), (Act.Map, "Map") })
            keys.AddChild(Style.H(4, Style.Key(G.Key(a)), Style.Label(name, Style.Ui, Style.Caption, Style.InkDim)));
        col.AddChild(keys);
        plate.AddChild(col);
    }

    public override bool Key(Act a)
    {
        if (panel != "")
        {
            // Back from a panel; inside it, focus moves over its rows.
            if (a is Act.Cancel or Act.Pause) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }"""),
# Rest
("""        AddChild(Style.Scrim(G.CloseOverlay));
        int cost = G.Journey.RestCost;
        bool afford = G.Journey.Ch.Gold >= cost;
        var plate = Style.Centered(Style.Panel(Style.Plate(22)), new Vector2(480, 330));
        AddChild(plate);
        var col = Style.V(8, Style.Label("THE LAST LAMP", Style.Display, 24, Style.GoldHi, false, HorizontalAlignment.Center), Style.Rule());
        var sleep = Style.Button($"Sleep until morning  ·  {(cost > 0 ? $"{cost} gold" : "on the house")}", () => G.Rest(false), true);
        sleep.Disabled = !afford;
        col.AddChild(sleep);
        if (w.Time != TimeOfDay.Night) col.AddChild(Style.Button("Wait until nightfall", () => G.Rest(true)));
        col.AddChild(Style.Button("Not yet", G.CloseOverlay));
        col.AddChild(Style.Label("Sleeping lets a day pass. The world will not wait for you, and the ember goes out while you sleep.", Style.TextItalic, 14, Style.InkDim, true));
        plate.AddChild(col);""",
"""        AddChild(Style.Scrim(G.CloseOverlay));
        int cost = G.Journey.RestCost;
        bool afford = G.Journey.Ch.Gold >= cost;
        var plate = Style.Panel(Style.Plate(22));
        plate.CustomMinimumSize = new Vector2(500, 0);
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        centre.AddChild(plate);
        AddChild(centre);
        var col = Style.V(8, Style.Label("THE LAST LAMP", Style.Display, 24, Style.GoldHi, false, HorizontalAlignment.Center), Style.Rule());
        var sleep = Style.Button($"Sleep until morning  ·  {(cost > 0 ? $"{cost} gold" : "on the house")}", () => G.Rest(false), true);
        sleep.Disabled = !afford;
        col.AddChild(sleep);
        if (!afford) col.AddChild(Style.Label($"You need {cost} gold; you have {Math.Floor(G.Journey.Ch.Gold)}.", Style.UiBold, Style.Caption, Style.Bad, false, HorizontalAlignment.Center));
        if (w.Time != TimeOfDay.Night) col.AddChild(Style.Button("Wait until nightfall", () => G.Rest(true)));
        col.AddChild(Style.Button("Not yet", G.CloseOverlay));
        col.AddChild(Style.Label("Sleeping lets a day pass. The world will not wait for you, and the ember goes out while you sleep.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        plate.AddChild(col);"""),
("""            foreach (var l in report) v.AddChild(Style.Label(l, Style.Text, 17, Style.ParchmentInk, true, HorizontalAlignment.Left, false));""",
"""            foreach (var l in report) v.AddChild(Style.Label(l, Style.Text, Style.Body, Style.ParchmentInk, true, HorizontalAlignment.Left, false));"""),
# Chapter
("""    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.CloseOverlay(); return true; }
        return a is Act.Cancel or Act.Pause;
    }
}""",
"""    public override bool Key(Act a)
    {
        // Enter keeps walking; with focus shown, A presses the button it is on.
        if (a == Act.Confirm && !Nav.KeyMode) { G.CloseOverlay(); return true; }
        return a is Act.Cancel or Act.Pause;
    }
}"""),
])

edit('Front.cs', [
("""        var list = menu.Build();
        list.Position = new Vector2(134, 560);
        AddChild(list);

        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(20));
            box.Position = new Vector2(540, panel == "controls" ? 140 : 540);
            box.CustomMinimumSize = new Vector2(panel == "controls" ? 720 : 520, 0);""",
"""        var list = menu.Build();
        list.Position = new Vector2(134, 560);
        AddChild(list);
        Nav.Scope = null;

        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(20));
            box.Position = new Vector2(540, panel == "controls" ? 90 : panel == "credits" ? 300 : 500);
            box.CustomMinimumSize = new Vector2(panel == "controls" ? 820 : panel == "credits" ? 760 : 560, 0);
            Nav.Scope = box;"""),
("""                        var words = Style.V(0, Style.Label(s.Name, Style.Display, 18, s.Alive ? new Color("#f2e6cc") : new Color("#a08a80")),
                            Style.Label($"{arch?.Name} {s.Level} · Day {s.Day} · {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.UiBold, 13, Style.InkDim),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.TextItalic, 13, Style.InkFaint));""",
"""                        var words = Style.V(0, Style.Label(s.Name, Style.Display, 18, s.Alive ? new Color("#f2e6cc") : new Color("#a08a80")),
                            Style.Label($"{arch?.Name} {s.Level} · Day {s.Day} · {ZoneNames.GetValueOrDefault(s.Zone, s.Zone)}", Style.UiBold, Style.Caption, Style.InkDim),
                            Style.Label(s.Alive ? $"Saved {Ago(s.SavedAt)}" : "Fallen", Style.TextItalic, Style.Caption, Style.InkFaint));"""),
("""                    foreach (var line in Credits) v.AddChild(Style.Label(line, Style.Text, 15, new Color("#ddd0b8"), true));""",
"""                    foreach (var line in Credits) v.AddChild(Style.Label(line, Style.Text, Style.Small, new Color("#ddd0b8"), true));"""),
("""        var foot = Style.Label("BETA  ·  THE FIRST CHAPTER", Style.UiBold, 12, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
    }""",
"""        var foot = Style.Label("BETA  ·  THE FIRST CHAPTER", Style.UiBold, Style.Badge, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
    }"""),
("""        if (a == Act.Cancel && panel != "") { panel = ""; Refresh(); return true; }
        return menu.Key(a);
    }
}""",
"""        if (panel != "")
        {
            // Back closes the panel; inside it, focus moves over its rows.
            if (a is Act.Cancel or Act.Pause) { panel = ""; Refresh(); return true; }
            return false;
        }
        return menu.Key(a);
    }
}"""),
])
print('done')
