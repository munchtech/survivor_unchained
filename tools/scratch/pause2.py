p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Menus.cs'
s = open(p, encoding='utf-8').read()

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

cut("""    protected override void Build()
    {
        AddChild(Style.Scrim(panel == "" ? G.CloseOverlay : () => { panel = ""; Refresh(); }));""", """    public override bool Key(Act a)
    {
        if (panel != "")""", '''    protected override void Build()
    {
        // The world stays in view, paused, behind a column down the left: the eye goes to the
        // list, the game is still there (docs/UI_DESIGN.md, "Pause").
        var shade = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Stop,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.03f, 0.92f), new Color(0.02f, 0.015f, 0.03f, 0.55f), new Color(0.02f, 0.015f, 0.03f, 0.35f) }, Offsets = new[] { 0f, 0.35f, 1f } },
                Width = 256, Height = 4,
            },
        };
        Style.Fill(shade);
        shade.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) { if (panel == "") G.CloseOverlay(); else { panel = ""; Refresh(); } } };
        AddChild(shade);
        var column = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Plate, 0));
        column.Position = new Vector2(-30, -30);
        column.Size = new Vector2(530, 1140);
        AddChild(column);
        var col = Style.V(Style.Gap3);
        col.Position = new Vector2(56, 64);
        col.Size = new Vector2(400, 980);
        AddChild(col);
        var plaque = new Plaque("Paused", 34, 70);
        col.AddChild(plaque);
        // Where you stand: the place, the day, what you are about.
        var w = G.Journey.World;
        if (G.Zone is { } z)
        {
            col.AddChild(Style.Label(z.Name, Style.Display, 24, Style.GoldHi));
            col.AddChild(Style.Label($"Day {w.Day}{(z.Region != null ? $"  ·  {z.Region}" : "")}", Style.TextItalic, Style.Small, Style.InkDim, true));
        }
        var doing = w.Quests.Values.Where(q => q.Status == QuestStatus.Active && Lore.Quests.ContainsKey(q.Id)).OrderBy(q => Lore.Quests[q.Id].Mystery).FirstOrDefault();
        if (doing != null)
            col.AddChild(Style.H(6, Glyphs.Icon("quest", 16, Style.EmberHi), Style.Label(Lore.Quests[doing.Id].Name, Style.UiBold, Style.Small, Style.EmberHi, true)));
        col.AddChild(Style.Rule());
        menu.Items.Clear();
        menu.Add("Resume", G.CloseOverlay);
        // Nothing is kept of an arena until it is over; once won, it can be left.
        if (G.Zone is Play.Zones.ArenaRun ar) { if (ar.Won) menu.Add("Leave the arena", () => { G.CloseOverlay(); ar.Leave(); }); }
        else menu.Add("Save", () => { G.Save("manual"); G.Toast(new Toast(ToastKind.World, "Journey saved")); });
        menu.Add("Settings", () => { panel = panel == "settings" ? "" : "settings"; Refresh(); });
        menu.Add("Controls", () => { panel = panel == "controls" ? "" : "controls"; Refresh(); });
        menu.Add("Leave to the title", G.QuitToTitle);
        menu.Add("Quit the game", G.QuitGame);
        col.AddChild(menu.Build());
        col.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        // The book, one press away: each page as a medallion with its key.
        col.AddChild(new Section("The book"));
        var book = Style.H(Style.Gap2);
        bool pad = Controls.Instance.UsingPad;
        foreach (var (a, name, glyph, kind) in new[] { (Act.Inventory, "Pack", "relic", "inventory"), (Act.Character, "Self", "hood", "character"), (Act.Arts, "Arts", "arcane", "arts"), (Act.Journal, "Journal", "book", "journal"), (Act.Map, "Map", "map", "map") })
        {
            var b = Style.Button("", () => G.Open(kind), false, true);
            foreach (var st in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(st, new StyleBoxEmpty());
            var v = Style.V(2);
            v.MouseFilter = MouseFilterEnum.Ignore;
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(new Medallion(62, "", glyph));
            v.AddChild(mc);
            v.AddChild(Style.Label(name, Style.UiBold, Style.Caption, Style.GoldHi, false, HorizontalAlignment.Center));
            var kc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            kc.AddChild(pad ? (a == Act.Inventory ? Style.PadButton("View") : Style.Label("then RB", Style.Ui, Style.Badge, Style.InkFaint)) : Style.Key(G.Key(a)));
            v.AddChild(kc);
            v.Size = new Vector2(72, 116);
            b.AddChild(v);
            b.CustomMinimumSize = new Vector2(72, 116);
            b.TooltipText = name;
            book.AddChild(Nav.Skip(b));
        }
        col.AddChild(book);

        // Settings and controls open beside the column, the column still there to go back to.
        if (panel != "")
        {
            var box = Style.Panel(Style.Plate(26));
            box.Position = new Vector2(540, 70);
            box.Size = new Vector2(panel == "controls" ? 1000 : 1100, panel == "controls" ? 940 : 560);
            AddChild(box);
            var v = Style.V(Style.Gap3, new Plaque(panel == "controls" ? "Controls" : "Settings", 28, 60));
            v.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            v.AddChild(Style.Button("Back", () => { panel = ""; Refresh(); }));
            box.AddChild(v);
            Nav.Scope = box;
        }
        else Nav.Scope = null;
    }

''')
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
