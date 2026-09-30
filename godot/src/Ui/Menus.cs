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
        var v = Style.V(2);
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
            if (sub != null) row.AddChild(Style.Label(sub, Style.TextItalic, 15, new Color("#9a8e78")));
            b.AddChild(row);
            b.MouseEntered += () => { if (Focus != index) { Focus = index; refresh(); } };
            b.Pressed += act;
            v.AddChild(b);
        }
        return v;
    }

    public bool Key(Act a)
    {
        if (Items.Count == 0) return false;
        if (a == Act.Up) { Focus = (Focus + Items.Count - 1) % Items.Count; refresh(); return true; }
        if (a == Act.Down) { Focus = (Focus + 1) % Items.Count; refresh(); return true; }
        if (a == Act.Confirm) { Items[Focus].Act(); return true; }
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
            var l = Style.Label(label, Style.UiBold, 16, Style.Ink);
            l.CustomMinimumSize = new Vector2(150, 0);
            r.AddChild(l);
            foreach (var o in options) r.AddChild(Style.Segment(Style.Cap1(o), o == now, () => { set(o); s.Save(); g.ApplySettings(); refresh(); }));
            return r;
        }
        v.AddChild(Row("Picture", ["low", "medium", "high"], s.Quality, x => s.Quality = x));
        v.AddChild(Row("Sound", ["on", "quiet", "off"], s.Sound, x => s.Sound = x));
        v.AddChild(Row("Display", ["window", "fullscreen"], s.Fullscreen ? "fullscreen" : "window", x => s.Fullscreen = x == "fullscreen"));
        v.AddChild(Row("Gore", ["full", "reduced", "off"], s.Gore, x => s.Gore = x));
        v.AddChild(Row("Screen shake", ["full", "reduced", "off"], s.Motion, x => s.Motion = x));
        v.AddChild(Style.Label("Lower settings trade shadow detail, grass and ambient occlusion for speed. Reduced gore keeps a little blood and throws nothing. Screen shake off also stops the world holding still on a heavy blow.",
            Style.TextItalic, 14, Style.InkDim, true));
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
        ("Draught", [Act.Ultimate], null), ("Talk, use, pick up", [Act.Interact], null), ("Pack", [Act.Inventory], null),
        ("Self", [Act.Character], "Menu"), ("Arts", [Act.Arts], "Menu"), ("Journal", [Act.Journal], "Menu"), ("Map", [Act.Map], "Menu"), ("Pause", [Act.Pause], null),
        ("Draft: take a card", [Act.Pick1], "D-pad, A"), ("Draft: reroll", [Act.Reroll], null), ("Draft: banish", [Act.Banish], null),
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
            grid.AddChild(Style.Label(label, Style.UiBold, 15, Style.Ink));
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
            grid.AddChild(Style.Label(pads == "" ? "-" : pads, Style.Ui, 14, Style.InkDim));
        }
        AddChild(grid);
        AddChild(Style.H(12, Style.Label(waiting != null ? "Press the new key, or Escape to leave it." : "Click a gold key to change it. Most attacks fire on their own.", Style.TextItalic, 14, Style.InkDim),
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
        AddChild(Style.Scrim(panel == "" ? G.CloseOverlay : () => { panel = ""; Refresh(); }));
        if (panel != "")
        {
            var box = Style.Centered(Style.Panel(Style.Plate(22)), panel == "controls" ? new Vector2(760, 640) : new Vector2(640, 380));
            AddChild(box);
            var v = Style.V(10, Style.Cap(panel == "controls" ? "Controls" : "Settings", 18), Style.Rule());
            v.AddChild(panel == "controls" ? new ControlsPanel() : SettingsPanel.Build(G, Refresh));
            v.AddChild(Style.Button("Back", () => { panel = ""; Refresh(); }));
            box.AddChild(v);
            return;
        }
        menu.Items.Clear();
        menu.Add("Resume", G.CloseOverlay);
        // Nothing is kept of an arena until it is over; once won, it can be left.
        if (G.Zone is Play.Zones.ArenaRun ar) { if (ar.Won) menu.Add("Leave the arena", () => { G.CloseOverlay(); ar.Leave(); }); }
        else menu.Add("Save", () => { G.Save("manual"); G.Toast(new Toast(ToastKind.World, "Journey saved")); });
        menu.Add("Settings", () => { panel = "settings"; Refresh(); });
        menu.Add("Controls", () => { panel = "controls"; Refresh(); });
        menu.Add("Pack", () => G.Open("inventory"));
        menu.Add("Self", () => G.Open("character"));
        menu.Add("Arts", () => G.Open("arts"));
        menu.Add("Journal", () => G.Open("journal"));
        menu.Add("Map", () => G.Open("map"));
        menu.Add("Leave to the title", G.QuitToTitle);
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
            foreach (var l in report) v.AddChild(Style.Label(l, Style.Text, 17, Style.ParchmentInk, true, HorizontalAlignment.Left, false));
            v.AddChild(Style.Gap(8));
            v.AddChild(Style.Button("Get up", G.FinishRest, true));
            paper.AddChild(Style.Scroll(v));
            return;
        }
        AddChild(Style.Scrim(G.CloseOverlay));
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
        plate.AddChild(col);
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
        var sum = Chapter.Summary(G.Journey.Ch, G.Journey.World);
        AddChild(Style.Scrim(null, 0.8f));
        var wrap = Style.Centered(Style.V(10), new Vector2(1400, 900));
        AddChild(wrap);
        wrap.AddChild(Style.Label("THE END OF THE FIRST CHAPTER", Style.UiHeavy, 15, Style.Gold, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Label("The Waystation", Style.Display, 52, Style.GoldHi, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Label(sum.Epithet, Style.TextItalic, 20, Style.Ink, false, HorizontalAlignment.Center));
        var book = Style.Panel(Style.Paper(28));
        book.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(book);
        var ink = Style.ParchmentInk;
        var soft = new Color("#5a4a36");
        Label P(string t, int size = 15, Font? f = null, Color? c = null) => Style.Label(t, f ?? Style.Text, size, c ?? ink, true, HorizontalAlignment.Left, false);
        Label H(string t) => Style.Label(t, Style.Display, 21, new Color("#3a2414"), false, HorizontalAlignment.Left, false);
        var left = Style.V(8, H("What was done"));
        foreach (var t in sum.Threads)
        {
            var tone = t.Tone switch { ThreadTone.Good => new Color("#3a6a2a"), ThreadTone.Bad => new Color("#8a2a1a"), _ => soft };
            left.AddChild(Style.V(2, Style.H(10, P(t.Name, 17, Style.TextBold), P(t.Verdict, 15, Style.TextItalic, tone)), P(t.Outcome)));
            foreach (var b in t.Beats.TakeLast(3)) left.AddChild(P($"• {b}", 14, Style.Text, soft));
        }
        left.AddChild(H("Still waiting"));
        foreach (var o in sum.Open) left.AddChild(Style.V(1, P(o.Name, 16, Style.TextBold), P(o.Line, 14, Style.TextItalic, soft)));
        var right = Style.V(8, H("Who remembers you"));
        if (sum.People.Count == 0) right.AddChild(P("Nobody, yet. You kept to yourself.", 15, Style.TextItalic, soft));
        foreach (var p in sum.People)
        {
            var warm = p.Warmth >= 25 ? new Color("#3a6a2a") : p.Warmth <= -25 ? new Color("#8a2a1a") : soft;
            right.AddChild(Style.V(1, Style.H(10, P(p.Name, 16, Style.TextBold), P(p.Role, 14, Style.TextItalic, soft)), P(Style.Cap1(p.Regard), 15, Style.Text, warm)));
            if (p.Knows != null) right.AddChild(P($"Knows that you {p.Knows}.", 14, Style.Text, soft));
        }
        right.AddChild(H("What the world says you did"));
        if (sum.Deeds.Count == 0) right.AddChild(P("Nothing it has noticed. Give it time.", 15, Style.TextItalic, soft));
        foreach (var d in sum.Deeds) right.AddChild(P($"You {d}.", 14));
        right.AddChild(P(string.Join("     ", sum.Stats.Select(s => $"{s.Value} {s.Label}")), 14, Style.UiBold, soft));
        var two = Style.H(34);
        left.SizeFlagsHorizontal = right.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        two.AddChild(Style.Scroll(left));
        two.AddChild(Style.Scroll(right));
        book.AddChild(two);
        var acts = Style.H(12, Style.Button("Keep walking", G.CloseOverlay), Style.Button("Return to the fire", G.QuitToTitle, true));
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
        wrap.AddChild(Style.Label("Your journey is saved. The second chapter begins where this one leaves off.", Style.TextItalic, 14, Style.InkDim, false, HorizontalAlignment.Center));
    }

    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.CloseOverlay(); return true; }
        return a is Act.Cancel or Act.Pause;
    }
}
