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
            // Only a hand that moves the mouse takes the focus: a new button built under a resting pointer
            // (every rebuild) would otherwise take it back from the keys at once.
            b.MouseEntered += () => { if (Focus != index && Nav.MouseMoved) { Focus = index; refresh(); } };
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

/// <summary>The settings, as rows of words to choose between (from the title and the pause menu):
/// each row's name, then its choices as the house's tabs, the one set over the ember's underline.</summary>
public static class SettingsPanel
{
    public static Control Build(Game g, Action refresh)
    {
        var s = Settings.Current;
        var v = Style.V(Style.Gap2);
        HBoxContainer Row(string label, string[] options, string now, Action<string> set)
        {
            var l = Style.Label(label, Style.UiBold, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            l.CustomMinimumSize = new Vector2(200, 0);
            l.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
            var r = Style.H(Style.Gap5, l);
            foreach (var o in options) r.AddChild(Kit.Tab(Style.Cap1(o), o == now, () => { if (o == now) return; Sound.Sfx.Click(); set(o); s.Save(); g.ApplySettings(); refresh(); }, 16));
            return r;
        }
        v.AddChild(Row("Picture", ["low", "medium", "high"], s.Quality, x => s.Quality = x));
        v.AddChild(Row("Upscaling (FSR 2)", ["native", "quality", "balanced", "performance"], s.Scale, x => s.Scale = x));
        v.AddChild(Row("Sound", ["on", "quiet", "off"], s.Sound, x => s.Sound = x));
        var voices = Row("Voices", ["on", "off"], s.Voices ? "on" : "off", x => s.Voices = x == "on");
        var level = Style.Slider(s.VoiceVolume, x => { s.VoiceVolume = x; g.ApplySettings(); }, s.Save, s.Voices);
        level.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        voices.AddChild(level);
        v.AddChild(voices);
        v.AddChild(Row("Display", ["window", "fullscreen"], s.Fullscreen ? "fullscreen" : "window", x => s.Fullscreen = x == "fullscreen"));
        v.AddChild(Row("Gore", ["full", "reduced", "off"], s.Gore, x => s.Gore = x));
        v.AddChild(Row("Screen shake", ["full", "reduced", "off"], s.Motion, x => s.Motion = x));
        v.AddChild(Row("Pad rumble", ["full", "low", "off"], s.Rumble, x => s.Rumble = x));
        v.AddChild(Row("Health under you", ["on", "off"], s.UnderBar ? "on" : "off", x => s.UnderBar = x == "on"));
        v.AddChild(Style.Gap(Style.Gap2));
        v.AddChild(Style.Label("Lower pictures trade shadow detail, grass, sparks and ambient occlusion for speed. Upscaling draws the world at fewer pixels and brings it up to your screen; the interface stays sharp. Reduced gore keeps a little blood and throws nothing. Screen shake off also stops the world holding still on a heavy blow. Health under you draws your health beneath your feet in a night's fight.",
            Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Left, false));
        return v;
    }
}

/// <summary>Every binding, keyboard and pad, in the words a player uses, as a ledger: the action,
/// its keys as the keys themselves, the pad's buttons. A key in gold can be moved: click it and
/// press the new one (Escape leaves it as it was).</summary>
public partial class ControlsPanel : VBoxContainer
{
    static readonly (string Label, Act[] Acts, string? Pad)[] Rows =
    {
        ("Move", [Act.Up, Act.Left, Act.Down, Act.Right], "Left stick"), ("Dash", [Act.Dash], null), ("Ability", [Act.Ability], null),
        ("Draught", [Act.Ultimate], null), ("Talk, use, pick up", [Act.Interact], null), ("Pack", [Act.Inventory], "View"),
        ("Self", [Act.Character], "View, then RB"), ("Arts", [Act.Arts], "View, then RB"), ("Journal", [Act.Journal], "View, then RB"), ("Map", [Act.Map], "View, then RB"), ("Answer the night (hold)", [Act.Answer], "L3"), ("Pause", [Act.Pause], null),
        ("Turn the book's pages", [Act.TabPrev, Act.TabNext], "LB / RB"), ("A screen's own pages", [Act.SubPrev, Act.SubNext], "LT / RT"),
        ("In menus: choose, back", [Act.Confirm, Act.Cancel], "A, B"), ("In menus: more", [Act.Alt], "X, Y"),
        ("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], "X"), ("Draft: banish", [Act.Banish], "Y"), ("Draft: skip", [Act.Skip], "R3"),
    };

    Act? waiting;

    public override void _Ready() => Build();

    /// <summary>A key that can be moved: its cap in gold, lit under the pointer, ember while it waits.</summary>
    Button Movable(string text, Act a)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        var cap = Style.Key(waiting == a ? "..." : text);
        Kit.Quiet(cap);
        if (waiting == a) cap.Modulate = new Color(1.3f, 0.85f, 0.55f);
        b.AddChild(cap);
        b.CustomMinimumSize = cap.GetCombinedMinimumSize();
        b.Ready += () => b.CustomMinimumSize = cap.GetCombinedMinimumSize();
        b.MouseEntered += () => cap.Modulate = new Color(1.35f, 1.25f, 1.1f);
        b.MouseExited += () => cap.Modulate = waiting == a ? new Color(1.3f, 0.85f, 0.55f) : Colors.White;
        b.Pressed += () => { waiting = waiting == a ? null : a; Build(); };
        return b;
    }

    void Build()
    {
        foreach (var old in GetChildren()) { RemoveChild(old); old.QueueFree(); }
        AddThemeConstantOverride("separation", Style.Gap3);
        var c = Controls.Instance;
        var grid = new GridContainer { Columns = 3 };
        grid.AddThemeConstantOverride("h_separation", Style.Gap6);
        grid.AddThemeConstantOverride("v_separation", 5);
        Label Head(string t) => Style.Label(t.ToUpperInvariant(), Style.UiHeavy, 13, Kit.HeadInk, false, HorizontalAlignment.Left, false);
        grid.AddChild(new Control());
        grid.AddChild(Head("Keyboard and mouse"));
        grid.AddChild(Head("Pad"));
        foreach (var (label, acts, pad) in Rows)
        {
            var name = Style.Label(label, Style.UiBold, 15, Kit.Ink2, false, HorizontalAlignment.Left, false);
            name.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            grid.AddChild(name);
            var keys = Style.H(Style.Gap1);
            if (acts[0] == Act.Pick1) keys.AddChild(Style.Key("1-4"));
            else foreach (var a in acts)
            {
                var labels = c.KeyLabels(a).Distinct().ToList();
                if (Controls.Rebindable.Contains(a))
                {
                    keys.AddChild(Movable(labels.FirstOrDefault() ?? "-", a));
                    if (acts.Length == 1) foreach (var k in labels.Skip(1)) keys.AddChild(Style.Key(k));
                }
                else foreach (var k in labels) keys.AddChild(Style.Key(k));
            }
            grid.AddChild(keys);
            var pads = pad ?? string.Join(" / ", acts.SelectMany(a => c.PadLabels(a)).Distinct());
            var p = Style.Label(pads == "" ? "-" : pads, Style.Ui, 15, Kit.Dim, false, HorizontalAlignment.Left, false);
            p.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            grid.AddChild(p);
        }
        AddChild(grid);
        var note = Style.Label(waiting != null ? "Press the new key, or Escape to leave it." : "Click a gold key to change it. Most attacks fire on their own.", Style.TextItalic, 15, waiting != null ? Style.EmberHi : Kit.Dim, false, HorizontalAlignment.Left, false);
        note.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var defaults = Kit.Word("Back to the defaults", () => { c.ResetBindings(); waiting = null; Build(); }, Kit.Ink2, 15);
        AddChild(Style.H(Style.Gap4, note, defaults));
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

/// <summary>
/// The pause (the web game's overlays/Menus.tsx): a fitted panel at the left over the live world,
/// paused, the book's panel's twin. Where you stand, the menu, and the book's tabs on their chain,
/// cold until a page is opened. Settings and controls open in a second panel beside it.
/// </summary>
public partial class PauseScreen : Overlay
{
    public override string Kind => "pause";
    string panel = "";
    readonly MenuList menu;

    public PauseScreen(Game g) : base(g) { menu = new MenuList(Refresh, 20); }

    /// <summary>The ember on a line of the menu (back from the credits, on the credits).</summary>
    public void FocusOn(string label)
    {
        focus = label;
        Refresh();
    }

    string? focus;

    /// <summary>The panel's width and inset: creation's panels' and the book's, on the left.</summary>
    const float W = 560, Inset = 16;

    protected override void Build()
    {
        // The world stays in view, paused, the HUD stepped away as the book does it; the world shaded
        // a little toward the panel, as the book shades toward its own. A click on the world goes back.
        HideHud();
        static Color Dark(float a) => new(0.02f, 0.015f, 0.03f, a);
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D { Gradient = new Gradient { Colors = new[] { Dark(0.34f), Dark(0.34f), Dark(0.08f), Dark(0.02f) }, Offsets = new[] { 0f, (Inset + W) / 1920f, 0.7f, 1f } }, Width = 256, Height = 4 },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Stop,
            Position = Vector2.Zero, Size = new Vector2(1920, 1080),
        };
        shade.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) { if (panel == "") G.CloseOverlay(); else { panel = ""; Refresh(); } } };
        AddChild(shade);
        // The panel and, when open, its settings or controls beside it, side by side with the same
        // gap as the screen's edge: each as wide as it needs (the book's chain sets the pause's).
        var pair = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(Inset, Inset) };
        pair.AddThemeConstantOverride("separation", (int)Inset);
        AddChild(pair);
        var col = Plate(pair, W);
        col.AddChild(new Title("Paused", 30, false));
        // Where you stand: the place, the day, what you are about.
        var w = G.Journey.World;
        var where = Style.V(2);
        if (G.Zone is { } z)
        {
            where.AddChild(Style.Label(z.Name, Style.Display, 22, Kit.Ink, false, HorizontalAlignment.Center, false));
            where.AddChild(Style.Label($"Day {w.Day}{(z.Region != null ? $"  ·  {z.Region}" : "")}", Style.TextItalic, 17, Kit.HeadInk, false, HorizontalAlignment.Center, false));
        }
        var doing = w.Quests.Values.Where(q => q.Status == QuestStatus.Active && Lore.Quests.ContainsKey(q.Id)).OrderBy(q => Lore.Quests[q.Id].Mystery).FirstOrDefault();
        if (doing != null)
        {
            var q = Style.H(Style.Gap2, Glyphs.Icon("quest", 16, Style.EmberHi), Style.Label(Lore.Quests[doing.Id].Name, Style.UiBold, 16, Style.EmberHi, false, HorizontalAlignment.Left, false));
            foreach (var c in q.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            q.Alignment = BoxContainer.AlignmentMode.Center;
            where.AddChild(Style.Gap(Style.Gap1));
            where.AddChild(q);
        }
        if (where.GetChildCount() > 0) col.AddChild(where);
        col.AddChild(Kit.RuleH());
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
        if (focus != null) { menu.Focus = Math.Max(0, menu.Items.FindIndex(i => i.Label == focus)); focus = null; }
        // (a centred block, its lines flush left on the ember's column)
        var list = menu.Build();
        list.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        col.AddChild(list);
        // The book, one press away: its tabs on their chain, as they hang over its own panel.
        col.AddChild(Kit.HeadMid("The book"));
        col.AddChild(new ChainTabs(Book.Select(b => (b.Name, Controls.Instance?.KeyLabel(b.Key) ?? "")).ToArray(), -1, k => { Sound.Sfx.Page(); G.Open(Book[k].Kind); })
            { SizeFlagsHorizontal = SizeFlags.ShrinkCenter });

        // Settings and controls open in a panel beside it, the menu still there to go back to.
        if (panel != "")
        {
            var side = Plate(pair, panel == "controls" ? 600 : 780);
            side.AddChild(new Title(panel == "controls" ? "Controls" : "Settings", 30, false));
            side.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            var back = Nav.Id(Kit.Keyed(Act.Cancel, "Back", () => { panel = ""; Refresh(); }), "back");
            side.AddChild(Style.V(Style.Gap3, Kit.RuleH(), back));
            Nav.Scope = side;
        }
        else Nav.Scope = null;
    }

    /// <summary>A fitted panel in a row of them: as tall as what it holds, its ground a little
    /// see-through, the same margin on every side. Returns its column.</summary>
    static VBoxContainer Plate(Control row, float width)
    {
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.CustomMinimumSize = new Vector2(width, 0);
        panel.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        row.AddChild(panel);
        var v = Style.V(Style.Gap4);
        panel.AddChild(v);
        return v;
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

/// <summary>
/// A night at the Last Lamp, as a held moment (the fall's choices are the model): no plate and no
/// cards, the world hushed under it, the lamp's name and Mother Rook's question over her head and
/// the choices under her feet as type on the world, each its mark, its key, its word, what it
/// means and what it costs; the lamp's warmth breathing behind the first. Then the morning after,
/// told the same way.
/// </summary>
public partial class RestScreen : Overlay
{
    public override string Kind => "rest";
    List<string>? report;
    TextureRect? warmth;
    Control? warmHead;
    double t;
    readonly List<Action> picks = new();

    public RestScreen(Game g) : base(g) { }

    public void Report(List<string> lines) { report = lines; Refresh(); }
    public bool Reporting => report != null;

    /// <summary>Where the words sit about her (she stands at the screen's middle): what is said
    /// ends above her head, the choices begin under her feet.</summary>
    const float Over = 420, Under = 640;
    static readonly Color Ink = new("#f2e8d4"), Ink2 = new("#d8cebc"), Quiet = new("#b8ad9a");

    protected override void Build()
    {
        HideHud();
        picks.Clear();
        warmth = null;
        // (lighter in the morning: the night is over)
        AddChild(Hush(report == null ? G.CloseOverlay : null, report == null ? 1 : 0.6f));
        if (report != null) { Morning(); return; }
        var w = G.Journey.World;
        int cost = G.Journey.RestCost;
        bool afford = G.Journey.Ch.Gold >= cost;
        Said("THE LAST LAMP", "Mother Rook keeps a bed, a fire and the door. What will you do with the hours?");
        var row = new List<Control>
        {
            Choice("Sleep until morning", "A day passes. You wake rested; the ember goes out while you sleep.",
                cost > 0 ? $"{cost} gold" : "On the house", afford ? null : $"You need {cost} gold; you have {Math.Floor(G.Journey.Ch.Gold)}.", () => G.Rest(false), true, "rest:sleep"),
        };
        if (w.Time != TimeOfDay.Night)
            row.Add(Choice("Wait until nightfall", "The day goes by at the fire. By dark the arenas burn and the road is not safe.", null, null, () => G.Rest(true), false, "rest:wait"));
        row.Add(Choice("Not yet", "Back out into the day. The lamp will be lit when you come back.", null, null, G.CloseOverlay, false, "rest:leave"));
        Lay(row);
    }

    /// <summary>The world hushed under the words: darker toward the edges, no shape seen. A click
    /// on it does what it is given (not yet, at the choice).</summary>
    static TextureRect Hush(Action? click, float depth)
    {
        var r = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1.1f, 1.1f), Width = 128, Height = 128,
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.025f, 0.32f * depth), new Color(0.02f, 0.015f, 0.025f, 0.72f * depth) }, Offsets = new[] { 0f, 1f } },
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Stop,
            Position = Vector2.Zero, Size = new Vector2(1920, 1080),
        };
        if (click != null) r.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) click(); };
        return r;
    }

    /// <summary>What is said, its last line ending above her head: a title and its words under it.</summary>
    void Said(string title, string line, IEnumerable<string>? more = null)
    {
        var v = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.End, Position = new Vector2(0, 0), Size = new Vector2(1920, Over) };
        v.AddThemeConstantOverride("separation", Style.Gap2);
        Label Centred(Label l) { l.HorizontalAlignment = HorizontalAlignment.Center; return l; }
        v.AddChild(Centred(WorldType.Lettering(title, Style.Display, 44, Ink)));
        v.AddChild(Centred(WorldType.Lettering(line, Style.TextItalic, 21, Ink2)));
        if (more != null)
        {
            v.AddChild(Style.Gap(Style.Gap3));
            foreach (var m in more) v.AddChild(Centred(WorldType.Lettering(Kit.Balance(m, Style.Text, 21, 860), Style.Text, 21, Ink)));
        }
        AddChild(v);
    }

    /// <summary>The choices in a row under her, each in a column of one width, the row centred.</summary>
    void Lay(List<Control> row)
    {
        const float colW = 400, gap = 40;
        float x = 960 - (row.Count * colW + (row.Count - 1) * gap) / 2;
        foreach (var c in row)
        {
            var holder = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(x, Under), Size = new Vector2(colW, 0) };
            c.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            holder.AddChild(c);
            AddChild(holder);
            x += colW + gap;
        }
    }

    /// <summary>One of the lamp's choices as type: its key and its name, what it means,
    /// and what it costs (or, refused, why); the first with the lamp's warmth behind its name.</summary>
    Control Choice(string title, string text, string? price, string? refused, Action go, bool primary, string id)
    {
        int n = picks.Count;
        picks.Add(() => { if (refused == null) go(); else Sound.Sfx.Deny(); });
        bool pad = Controls.Instance.UsingPad;
        var ink = refused != null ? Quiet : primary ? Style.EmberHi : Ink;
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = refused != null ? CursorShape.Forbidden : CursorShape.PointingHand };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus", "disabled" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        b.Pressed += picks[n];
        Nav.Id(b, id);
        var v = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
        v.AddThemeConstantOverride("separation", Style.Gap2);
        var word = WorldType.Lettering(title.ToUpperInvariant(), Style.Display, 27, ink);
        var head = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
        head.AddThemeConstantOverride("separation", 12);
        // (the number keys take them in turn on a keyboard; a pad walks to them)
        if (!pad) head.AddChild(Style.Key($"{n + 1}"));
        head.AddChild(word);
        foreach (var c in head.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        v.AddChild(head);
        var line = WorldType.Lettering(Kit.Balance(text, Style.TextItalic, 19, 360), Style.TextItalic, 19, Ink2);
        line.HorizontalAlignment = HorizontalAlignment.Center;
        v.AddChild(line);
        if (price != null)
        {
            var tag = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Center };
            tag.AddThemeConstantOverride("separation", 6);
            tag.AddChild(Glyphs.Icon("coin", 18, Style.GoldHi));
            tag.AddChild(WorldType.Lettering(price, Style.UiBold, 18, refused != null ? Style.Bad : Style.GoldHi));
            foreach (var c in tag.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            v.AddChild(tag);
        }
        if (refused != null)
        {
            var why = WorldType.Lettering(refused, Style.UiBold, 16, Style.Bad);
            why.HorizontalAlignment = HorizontalAlignment.Center;
            v.AddChild(why);
        }
        Kit.Quiet(v);
        b.AddChild(v);
        b.CustomMinimumSize = v.GetCombinedMinimumSize();
        b.Ready += () => { b.CustomMinimumSize = v.GetCombinedMinimumSize(); v.Size = b.CustomMinimumSize; };
        b.MouseEntered += () => word.AddThemeColorOverride("font_color", ink.Lightened(0.25f));
        b.MouseExited += () => word.AddThemeColorOverride("font_color", ink);
        if (primary && refused == null)
        {
            // The lamp's warmth behind the first choice's name, breathing while it waits.
            warmth = WorldType.Light(new Vector2(520, 190), Style.Ember with { A = 0 });
            warmth.ShowBehindParent = true;
            b.AddChild(warmth);
            b.MoveChild(warmth, 0);
            warmHead = head;
        }
        return b;
    }

    /// <summary>The morning after: the day and where, what the night held, and getting up.</summary>
    void Morning()
    {
        var w = G.Journey.World;
        Said($"DAY {w.Day}", "Morning, at the Last Lamp", report);
        var (up, _) = WorldType.Keyed(Act.Confirm, "GET UP", Style.Display, 27, Style.EmberHi, G.FinishRest);
        Nav.Id(up, "getup");
        Lay(new List<Control> { up });
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        t += delta;
        if (warmth != null && IsInstanceValid(warmth) && warmHead != null && IsInstanceValid(warmHead))
        {
            // (centred on the name, wherever the column has laid it)
            warmth.Position = warmHead.GetParent<Control>().Position + warmHead.Position + warmHead.Size / 2 - warmth.Size / 2;
            warmth.Modulate = Style.Ember with { A = 0.2f + 0.07f * Mathf.Sin((float)t * 2.1f) };
        }
    }

    public override bool Key(Act a)
    {
        if (report != null)
        {
            if (a is Act.Confirm or Act.Cancel or Act.Pause) { G.FinishRest(); return true; }
            return false;
        }
        // The number keys take the choices in turn; Escape is "not yet".
        int n = a switch { Act.Pick1 => 0, Act.Pick2 => 1, Act.Pick3 => 2, _ => -1 };
        if (n >= 0 && n < picks.Count) { Sound.Sfx.Click(); picks[n](); return true; }
        if (a == Act.Cancel) { G.CloseOverlay(); return true; }
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

    /// <summary>The book's width (the Journal's reading measure) and its height's bounds: between
    /// them it hugs what is written, measured once laid out and shown when it holds.</summary>
    const float BookW = 1440, MinH = 520, MaxH = 760;
    float? height;
    int measuring, tries;
    readonly List<Control> measured = new();
    readonly List<ScrollContainer> leaves = new();
    bool settling = true;

    protected override void Build()
    {
        // The survivor's own book, lying open over the world gone soft behind it (docs/UI_DESIGN.md
        // 7.10): the same book as the Journal, so the chapter closes in the hand that kept it. The
        // whole is one centred column: the chapter's name between its chains, the book, the way on.
        var sum = Chapter.Summary(G.Journey.Ch, G.Journey.World);
        HideHud();
        measured.Clear();
        leaves.Clear();
        AddChild(new Backdrop(null, 0.94f));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        AddChild(centre);
        var page = Style.V(Style.Gap4);
        centre.AddChild(page);
        var head = Style.V(Style.Gap1, Style.Label("THE END OF THE FIRST CHAPTER", Style.UiHeavy, 15, Kit.HeadInk, false, HorizontalAlignment.Center, false),
            new Title("The Waystation", 46), Style.Label(sum.Epithet, Style.TextItalic, 21, Kit.Ink2, false, HorizontalAlignment.Center, false));
        page.AddChild(head);

        float h = height ?? MaxH;
        var book = new OpenBook(new Vector2(BookW, h)) { SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        page.AddChild(book);
        var ink = Style.ParchmentInk;
        var soft = new Color("#5a4a36");
        Label P(string t, int size = 17, Font? f = null, Color? c = null, bool wrap = true) => Style.Label(t, f ?? Style.Text, size, c ?? ink, wrap, HorizontalAlignment.Left, false);
        Control H(string t) => Style.V(2, Style.Label(t, Style.Display, 23, new Color("#3a2414"), false, HorizontalAlignment.Left, false),
            new ColorRect { Color = new Color("#3a2414") with { A = 0.35f }, CustomMinimumSize = new Vector2(0, 1), MouseFilter = MouseFilterEnum.Ignore });
        // A name with what is said of it after it on the same line (not pushed to a far column).
        Control Named(string name, string said, Color tone) => Style.H(Style.Gap3, P(name, 18, Style.TextBold, null, false), P(said, 16, Style.TextItalic, tone, false));

        // The left leaf looks back: what was done, what the world says of it, and the tally of the road
        // as a ledger line after the words. The right looks on: who remembers you, and what still waits.
        var left = Style.V(Style.Gap2, H("What was done"));
        foreach (var th in sum.Threads)
        {
            var tone = th.Tone switch { ThreadTone.Good => new Color("#3a6a2a"), ThreadTone.Bad => new Color("#8a2a1a"), _ => soft };
            left.AddChild(Style.V(2, Named(th.Name, th.Verdict, tone), P(th.Outcome)));
            foreach (var bt in th.Beats.TakeLast(3)) left.AddChild(P($"•  {bt}", 15, Style.Text, soft));
        }
        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(H("What the world says you did"));
        if (sum.Deeds.Count == 0) left.AddChild(P("Nothing it has noticed. Give it time.", 16, Style.TextItalic, soft));
        foreach (var d in sum.Deeds) left.AddChild(P($"You {d}."));
        left.AddChild(Style.Gap(Style.Gap2));
        left.AddChild(Style.Rule());
        // (numerals over their names, as the Journal's Deeds ends: not coins pinned to the page's foot)
        var tally = Style.H(0);
        foreach (var (label, value) in sum.Stats)
        {
            var cell = Style.V(0, Style.Label(value, Style.Display, 28, ink, false, HorizontalAlignment.Center, false),
                Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 11, soft, false, HorizontalAlignment.Center, false));
            cell.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            tally.AddChild(cell);
        }
        left.AddChild(tally);

        var right = Style.V(Style.Gap2, H("Who remembers you"));
        if (sum.People.Count == 0) right.AddChild(P("Nobody, yet. You kept to yourself.", 16, Style.TextItalic, soft));
        foreach (var pe in sum.People)
        {
            var warm = pe.Warmth >= 25 ? new Color("#3a6a2a") : pe.Warmth <= -25 ? new Color("#8a2a1a") : soft;
            right.AddChild(Style.V(1, Named(pe.Name, pe.Role, soft), P(Style.Cap1(pe.Regard), 16, Style.Text, warm)));
            if (pe.Knows != null) right.AddChild(P($"Knows that you {pe.Knows}.", 15, Style.Text, soft));
        }
        right.AddChild(Style.Gap(Style.Gap2));
        right.AddChild(H("Still waiting"));
        foreach (var o in sum.Open) right.AddChild(Style.V(1, P(o.Name, 17, Style.TextBold), P(o.Line, 15, Style.TextItalic, soft)));
        foreach (var (leaf, words) in new[] { (book.Left, left), (book.Right, right) })
        {
            var sc = Style.Scroll(words);
            sc.Position = Vector2.Zero;
            sc.Size = leaf.Size;
            leaf.AddChild(sc);
            measured.Add(words);
            leaves.Add(sc);
        }
        if (settling) { page.Modulate = Colors.Transparent; measuring = 4; }

        // The way on, as words with their keys, mirrored about the middle as the fall's choices are.
        var (walk, _) = WorldType.Keyed(Act.Confirm, "KEEP WALKING", Style.Display, 22, Style.EmberHi, G.CloseOverlay);
        var (fire, _) = WorldType.Keyed(null, "RETURN TO THE FIRE", Style.Display, 22, Kit.Ink2, G.QuitToTitle);
        Nav.Id(walk, "walk");
        Nav.Id(fire, "fire");
        var acts = Style.H(0);
        var l = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.End, CustomMinimumSize = new Vector2(BookW / 2 - 40, 0) };
        l.AddChild(walk);
        var r = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.Begin, CustomMinimumSize = new Vector2(BookW / 2 - 40, 0) };
        r.AddChild(fire);
        acts.AddChild(l);
        acts.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(80, 34) });
        acts.AddChild(r);
        acts.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        page.AddChild(acts);
        page.AddChild(Style.Label("Your journey is saved. The chapter ends here, but the road does not: the Waystation, the Verge and the Wayfinder's table are still yours to walk. What lies north is not written yet.",
            Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center, false));
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        // Laid out: the book takes its writing's height (the taller leaf's), measured again at it
        // until it holds (wrapped words settle their lines a frame or two after the width they wrap
        // to; a scroll bar, once shown, narrows them onto more), as the Journal's book does; then shows.
        if (measuring > 0 && --measuring == 0 && settling)
        {
            float need = measured.Where(IsInstanceValid).Select(c => c.GetCombinedMinimumSize().Y)
                .Concat(leaves.Where(IsInstanceValid).Select(s => (float)s.GetVScrollBar().MaxValue)).DefaultIfEmpty(0).Max();
            float had = height ?? MaxH;
            // (the Journal's chrome less the foot line its leaves carry, which this book has not)
            float now = Math.Clamp(need + OpenBook.Chrome - 14, MinH, MaxH);
            if (tries > 0) now = Math.Max(now, had);
            height = now;
            if (Math.Abs(now - had) <= 2 || ++tries >= 4) settling = false;
            if (Args.Has("shot")) GD.Print($"chapter: words {need:0}, book {now:0}{(settling ? "" : ", held")}");
            Refresh();
        }
    }

    public override bool Key(Act a)
    {
        // Enter keeps walking; with focus shown, A presses the button it is on.
        if (a == Act.Confirm && !Nav.KeyMode) { G.CloseOverlay(); return true; }
        return a is Act.Cancel or Act.Pause;
    }
}
