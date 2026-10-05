using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>A column of menu lines, moved through with the keys or the
/// mouse (the pause menu, the title), the chosen one marked with an ember.</summary>
public sealed class MenuList
{
    public readonly List<(string Label, string? Sub, Action Act, bool Primary)> Items = new();
    public int Focus;
    readonly int size;
    readonly Action refresh;

    public MenuList(Action refresh, int size = 22) { this.refresh = refresh; this.size = size; }

    public void Add(string label, Action act, string? sub = null, bool primary = false) => Items.Add((label, sub, act, primary));

    public Control Build()
    {
        // It moves its own focus (the ember mark), so the screen's focus leaves it alone.
        var v = Nav.Skip(Style.V(2));
        for (int i = 0; i < Items.Count; i++)
        {
            var (label, sub, act, primary) = Items[i];
            int index = i;
            bool on = i == Focus;
            var b = new Button { FocusMode = Control.FocusModeEnum.None, Flat = true, CustomMinimumSize = new Vector2(360, size + 18), MouseDefaultCursorShape = Control.CursorShape.PointingHand };
            b.AddThemeStyleboxOverride("normal", new StyleBoxEmpty());
            b.AddThemeStyleboxOverride("hover", new StyleBoxEmpty());
            b.AddThemeStyleboxOverride("pressed", new StyleBoxEmpty());
            var row = Style.H(12);
            row.Position = new Vector2(8, 4);
            var mark = new ColorRect { Color = on ? Style.Ember : new Color(0, 0, 0, 0), CustomMinimumSize = new Vector2(9, 9), Rotation = Mathf.Pi / 4, MouseFilter = Control.MouseFilterEnum.Ignore };
            var markBox = new Control { CustomMinimumSize = new Vector2(16, size), MouseFilter = Control.MouseFilterEnum.Ignore };
            mark.Position = new Vector2(6, size / 2f - 6);
            markBox.AddChild(mark);
            row.AddChild(markBox);
            row.AddChild(Style.Label(label.ToUpperInvariant(), Style.Display, size, on ? new Color("#fff2d8") : primary ? Style.GoldHi : new Color("#cbbd9f")));
            if (sub != null) row.AddChild(Style.Label(sub, Style.TextItalic, Style.Small, new Color("#a89c84")));
            b.AddChild(row);
            b.MouseEntered += () => { if (Focus != index) { Focus = index; refresh(); } };
            b.Pressed += act;
            if (on) row.AddChild(Style.Prompt(Act.Confirm));
            v.AddChild(b);
        }
        return v;
    }

    public bool Key(Act a)
    {
        if (Items.Count == 0) return false;
        if (a == Act.Up) { Focus = (Focus + Items.Count - 1) % Items.Count; Sound.Sfx.Hover(); refresh(); return true; }
        if (a == Act.Down) { Focus = (Focus + 1) % Items.Count; Sound.Sfx.Hover(); refresh(); return true; }
        if (a == Act.Confirm) { Sound.Sfx.Click(); Items[Focus].Act(); return true; }
        return false;
    }
}

/// <summary>The settings, as rows of choices (from the title and the pause menu).</summary>
public static class SettingsPanel
{
    public static Control Build(Game g, Action refresh)
    {
        var s = Settings.Current;
        var v = Style.V(8);
        Control Row(string label, string[] options, string now, Action<string> set)
        {
            var r = Style.H(8);
            var l = Style.Label(label, Style.UiBold, Style.Small, Style.Ink);
            l.CustomMinimumSize = new Vector2(190, 0);
            r.AddChild(l);
            foreach (var o in options) r.AddChild(Style.Segment(Style.Cap1(o), o == now, () => { set(o); s.Save(); g.ApplySettings(); refresh(); }));
            return r;
        }
        v.AddChild(Row("Picture", ["low", "medium", "high"], s.Quality, x => s.Quality = x));
        v.AddChild(Row("Upscaling (FSR 2)", ["native", "quality", "balanced", "performance"], s.Scale, x => s.Scale = x));
        v.AddChild(Row("Sound", ["on", "quiet", "off"], s.Sound, x => s.Sound = x));
        var voices = Row("Voices", ["on", "off"], s.Voices ? "on" : "off", x => s.Voices = x == "on");
        voices.AddChild(new Control { CustomMinimumSize = new Vector2(10, 0), MouseFilter = Control.MouseFilterEnum.Ignore });
        voices.AddChild(Style.Slider(s.VoiceVolume, x => { s.VoiceVolume = x; g.ApplySettings(); }, s.Save, s.Voices));
        v.AddChild(voices);
        v.AddChild(Row("Display", ["window", "fullscreen"], s.Fullscreen ? "fullscreen" : "window", x => s.Fullscreen = x == "fullscreen"));
        v.AddChild(Row("Gore", ["full", "reduced", "off"], s.Gore, x => s.Gore = x));
        v.AddChild(Row("Screen shake", ["full", "reduced", "off"], s.Motion, x => s.Motion = x));
        v.AddChild(Row("Pad rumble", ["full", "low", "off"], s.Rumble, x => s.Rumble = x));
        v.AddChild(Row("Health under you", ["on", "off"], s.UnderBar ? "on" : "off", x => s.UnderBar = x == "on"));
        v.AddChild(Style.Label("Lower pictures trade shadow detail, grass, sparks and ambient occlusion for speed. Upscaling draws the world at fewer pixels and brings it up to your screen; the interface stays sharp. Reduced gore keeps a little blood and throws nothing. Screen shake off also stops the world holding still on a heavy blow. Health under you draws your health beneath your feet in a night's fight.",
            Style.TextItalic, Style.Caption, Style.InkDim, true));
        return v;
    }
}

/// <summary>Every binding, keyboard and pad, in the words a player uses. A
/// key in gold can be moved: click it and press the new one (Escape leaves
/// it as it was).</summary>
public partial class ControlsPanel : VBoxContainer
{
    static readonly (string Label, Act[] Acts, string? Pad)[] Rows =
    {
        ("Move", [Act.Up, Act.Left, Act.Down, Act.Right], "Left stick"), ("Dash", [Act.Dash], null), ("Ability", [Act.Ability], null),
        ("Draught", [Act.Ultimate], null), ("Talk, use, pick up", [Act.Interact], null), ("Pack", [Act.Inventory], "View"),
        ("Self", [Act.Character], "View, then RB"), ("Arts", [Act.Arts], "View, then RB"), ("Journal", [Act.Journal], "View, then RB"), ("Map", [Act.Map], "View, then RB"), ("Pause", [Act.Pause], null),
        ("Turn the book's pages", [Act.TabPrev, Act.TabNext], "LB / RB"), ("A screen's own pages", [Act.SubPrev, Act.SubNext], "LT / RT"),
        ("In menus: choose, back", [Act.Confirm, Act.Cancel], "A, B"), ("In menus: more", [Act.Alt], "X, Y"),
        ("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], "X"), ("Draft: banish", [Act.Banish], "Y"), ("Draft: skip", [Act.Skip], "R3"),
    };

    Act? waiting;

    public override void _Ready() => Build();

    void Build()
    {
        foreach (var old in GetChildren()) { RemoveChild(old); old.QueueFree(); }
        AddThemeConstantOverride("separation", 4);
        var c = Controls.Instance;
        var grid = new GridContainer { Columns = 3 };
        grid.AddThemeConstantOverride("h_separation", 18);
        grid.AddThemeConstantOverride("v_separation", 5);
        grid.AddChild(new Control());
        grid.AddChild(Style.SubLabel("Keyboard and mouse"));
        grid.AddChild(Style.SubLabel("Pad"));
        foreach (var (label, acts, pad) in Rows)
        {
            grid.AddChild(Style.Label(label, Style.UiBold, Style.Caption, Style.Ink));
            var keys = Style.H(4);
            if (acts[0] == Act.Pick1) keys.AddChild(Style.Key("1-4"));
            else foreach (var a in acts)
            {
                var labels = c.KeyLabels(a).Distinct().ToList();
                if (Controls.Rebindable.Contains(a))
                {
                    var act = a;
                    var chip = Style.Button(waiting == a ? "..." : labels.FirstOrDefault() ?? "-", () => { waiting = waiting == act ? null : act; Build(); }, true, true);
                    keys.AddChild(chip);
                    if (acts.Length == 1) foreach (var k in labels.Skip(1)) keys.AddChild(Style.Key(k));
                }
                else foreach (var k in labels) keys.AddChild(Style.Key(k));
            }
            grid.AddChild(keys);
            var pads = pad ?? string.Join(" / ", acts.SelectMany(a => c.PadLabels(a)).Distinct());
            grid.AddChild(Style.Label(pads == "" ? "-" : pads, Style.Ui, Style.Caption, Style.InkDim));
        }
        AddChild(grid);
        AddChild(Style.H(12, Style.Label(waiting != null ? "Press the new key, or Escape to leave it." : "Click a gold key to change it. Most attacks fire on their own.", Style.TextItalic, Style.Caption, Style.InkDim),
            Style.Button("Defaults", () => { c.ResetBindings(); waiting = null; Build(); }, false, true)));
    }

    public override void _Input(InputEvent e)
    {
        if (waiting is not Act a || e is not InputEventKey { Pressed: true, Echo: false } k) return;
        GetViewport().SetInputAsHandled();
        if (k.PhysicalKeycode != Godot.Key.Escape && Controls.CodeOf(k.PhysicalKeycode) is string code) Controls.Instance.Rebind(a, code);
        waiting = null;
        Build();
    }
}

/// <summary>The pause menu (the web game's overlays/Menus.tsx).</summary>
public partial class PauseScreen : Overlay
{
    public override string Kind => "pause";
    string panel = "";
    readonly MenuList menu;

    public PauseScreen(Game g) : base(g) { menu = new MenuList(Refresh, 20); }

    protected override void Build()
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
        var column = Style.Panel(Style.Plate(0));
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
        menu.Add("Credits and licences", G.Credits);
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
            // As tall as what it holds.
            box.Size = new Vector2(panel == "controls" ? 1000 : 1100, 0);
            AddChild(box);
            var v = Style.V(Style.Gap3, new Plaque(panel == "controls" ? "Controls" : "Settings", 28, 60));
            v.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            var back = Style.Button("Back", () => { panel = ""; Refresh(); });
            back.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            back.CustomMinimumSize = new Vector2(160, 0);
            v.AddChild(back);
            box.AddChild(v);
            Nav.Scope = box;
        }
        else Nav.Scope = null;
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
    }
}

/// <summary>A night at the Last Lamp: the choice, then the morning after.</summary>
public partial class RestScreen : Overlay
{
    public override string Kind => "rest";
    List<string>? report;

    public RestScreen(Game g) : base(g) { }

    public void Report(List<string> lines) { report = lines; Refresh(); }
    public bool Reporting => report != null;

    protected override void Build()
    {
        var w = G.Journey.World;
        if (report != null)
        {
            var paper = Style.Centered(Style.Panel(Style.Paper(34)), new Vector2(680, 560));
            AddChild(paper);
            var v = Style.V(10, Style.Label($"Day {w.Day}", Style.Display, 34, new Color("#3a2414"), false, HorizontalAlignment.Center, false),
                Style.Label("Morning, at the Last Lamp", Style.TextItalic, 17, new Color("#5a4a36"), false, HorizontalAlignment.Center, false), Style.Rule());
            foreach (var l in report) v.AddChild(Style.Label(l, Style.Text, Style.Body, Style.ParchmentInk, true, HorizontalAlignment.Left, false));
            v.AddChild(Style.Gap(8));
            v.AddChild(Style.Button("Get up", G.FinishRest, true));
            paper.AddChild(Style.Scroll(v));
            return;
        }
        // The choice made in the place itself (docs/UI_DESIGN.md 7.7): three crested cards on a plate,
        // each with its sign, what it does and what it costs; the world stays in view round it.
        AddChild(Style.Scrim(G.CloseOverlay, 0.5f));
        int cost = G.Journey.RestCost;
        bool afford = G.Journey.Ch.Gold >= cost;
        var plate = Style.Panel(Style.Plate(26));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        centre.AddChild(plate);
        AddChild(centre);
        var col = Style.V(Style.Gap3);
        col.AddChild(new Plaque("The Last Lamp", 30, 120));
        col.AddChild(Style.Label("Mother Rook keeps a bed, a fire and the door. What will you do with the hours?", Style.TextItalic, Style.Body, Style.InkDim, false, HorizontalAlignment.Center));
        var row = Style.H(Style.Gap4);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.AddChild(Choice("moon", "Sleep until morning", "A day passes. You wake rested; the ember goes out while you sleep.",
            cost > 0 ? $"{cost} gold" : "On the house", afford ? null : $"You need {cost} gold; you have {Math.Floor(G.Journey.Ch.Gold)}.", () => G.Rest(false), true, "rest:sleep"));
        if (w.Time != TimeOfDay.Night)
            row.AddChild(Choice("hourglass", "Wait until nightfall", "The day goes by at the fire. By dark the arenas burn and the road is not safe.", null, null, () => G.Rest(true), false, "rest:wait"));
        row.AddChild(Choice("next", "Not yet", "Back out into the day. The lamp will be lit when you come back.", null, null, G.CloseOverlay, false, "rest:leave"));
        col.AddChild(row);
        plate.AddChild(col);
    }

    /// <summary>One of the lamp's choices: a crested card with its sign, words, price and, if refused, why.</summary>
    Control Choice(string glyph, string title, string text, string? price, string? refused, Action go, bool primary, string id)
    {
        var box = OrnateBox.Make(OrnateBox.Kind.Card, 18, refused != null ? Style.InkFaint : primary ? Style.Ember : Style.Gold);
        box.Crest = 70;
        var lit = OrnateBox.Make(OrnateBox.Kind.Card, 18, refused != null ? Style.InkFaint : Style.EmberHi);
        lit.Crest = 70;
        lit.Glow = refused != null ? 0 : 1.2f;
        var b = new Button { CustomMinimumSize = new Vector2(300, 330), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = refused != null ? CursorShape.Forbidden : CursorShape.PointingHand };
        b.AddThemeStyleboxOverride("normal", box);
        b.AddThemeStyleboxOverride("hover", lit);
        b.AddThemeStyleboxOverride("pressed", lit);
        b.AddThemeStyleboxOverride("disabled", box);
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        b.Disabled = refused != null;
        b.Pressed += go;
        var v = Style.V(Style.Gap2);
        v.MouseFilter = MouseFilterEnum.Ignore;
        v.Position = new Vector2(20, 18);
        v.Size = new Vector2(260, 294);
        var med = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        med.AddChild(new Medallion(96, "", glyph) { Lit = primary && refused == null });
        v.AddChild(med);
        v.AddChild(Style.Label(title, Style.Display, 21, refused != null ? Style.InkDim : Style.GoldHi, true, HorizontalAlignment.Center));
        var words = Style.Label(text, Style.Text, Style.Small, Style.Ink, true, HorizontalAlignment.Center);
        words.SizeFlagsVertical = SizeFlags.ExpandFill;
        v.AddChild(words);
        if (price != null)
        {
            var tag = Style.H(4, Glyphs.Icon("coin", 16, Style.GoldHi), Style.Label(price, Style.UiBold, Style.Small, refused != null ? Style.Bad : Style.GoldHi));
            tag.Alignment = BoxContainer.AlignmentMode.Center;
            v.AddChild(tag);
        }
        if (refused != null) v.AddChild(Style.Label(refused, Style.UiBold, Style.Caption, Style.Bad, true, HorizontalAlignment.Center));
        b.AddChild(v);
        Nav.Id(b, id);
        return b;
    }

    public override bool Key(Act a)
    {
        if (report != null && a is Act.Confirm or Act.Cancel or Act.Pause) { G.FinishRest(); return true; }
        return false;
    }
}

/// <summary>The end of the first chapter: the survivor's own book, closed
/// for now. What was done and what still waits; who remembers, and how.
/// Read back from the world, not written down.</summary>
public partial class ChapterScreen : Overlay
{
    public override string Kind => "chapter";
    public override bool Dismissable => false;

    public ChapterScreen(Game g) : base(g) { }

    protected override void Build()
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
            foreach (var bt in t.Beats.TakeLast(3)) left.AddChild(P($"\u2022 {bt}", 15, Style.Text, soft));
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

    public override bool Key(Act a)
    {
        // Enter keeps walking; with focus shown, A presses the button it is on.
        if (a == Act.Confirm && !Nav.KeyMode) { G.CloseOverlay(); return true; }
        return a is Act.Cancel or Act.Pause;
    }
}
