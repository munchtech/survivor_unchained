using System;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The item filter's first face (docs/design/LOOT_DESIGN.md 7): how strict the ground is (four
/// presets, each one plain sentence), five promises in plain words, and what can never be hidden.
/// It opens beside the Pack on the world's side (Filter sits beside Sort), so the pack stays in
/// view while it is set. The owner: "an item filter and more poe/diablo style drops that can be
/// seen or hidden". The rule list is for later, for the few.
/// </summary>
public partial class FilterPanel : PanelContainer
{
    public const float W = 430;

    static readonly (FilterPreset Preset, string Name, string Says)[] Presets =
    {
        (FilterPreset.Everything, "Everything", "Every piece shows. Nothing is hidden."),
        (FilterPreset.Default, "Default", "Commons hide, unless they would serve you. The rest shows."),
        (FilterPreset.Strict, "Strict", "Uncommons hide too, unless they are better than what you wear."),
        (FilterPreset.Best, "Only the best", "Epic and finer, and what is better than you wear. The rest hides."),
    };

    readonly Game g;
    readonly Action close;

    public FilterPanel(Game g, Action close)
    {
        this.g = g;
        this.close = close;
        AddThemeStyleboxOverride("panel", Kit.Window(26, 18, 20));
        CustomMinimumSize = new Vector2(W, 0);
        MouseFilter = MouseFilterEnum.Stop;
        Build();
    }

    LootFilter F => g.Journey.Ch.Filter;

    void Build()
    {
        foreach (var c in GetChildren()) { RemoveChild(c); c.QueueFree(); }
        var v = Style.V(Style.Gap3);
        AddChild(v);
        var head = Style.H(8, new Title("Loot filter", 22, false) { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        var shut = Kit.Word("Close", close, Kit.Dim, 14);
        shut.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        head.AddChild(shut);
        v.AddChild(head);
        v.AddChild(Style.Label("What the ground shows you, and what it keeps quiet.", Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));

        v.AddChild(Kit.Head("How strict"));
        foreach (var (preset, name, says) in Presets)
        {
            bool on = F.Preset == preset;
            var p = preset;
            v.AddChild(Choice(name, says, on, () => { F.Preset = p; Changed(); }));
        }

        v.AddChild(Kit.Head("Always"));
        v.AddChild(Toggle("Show what is better than I wear", F.Upgrades, () => { F.Upgrades = !F.Upgrades; Changed(); }));
        v.AddChild(Toggle("Show weapons of my calling", F.CallingWeapons, () => { F.CallingWeapons = !F.CallingWeapons; Changed(); }));
        v.AddChild(Toggle("Show Commons of a better make than mine", F.BetterMakes, () => { F.BetterMakes = !F.BetterMakes; Changed(); }));
        v.AddChild(Toggle("Break down what I hide, at a fight's end", F.BreakHidden, () => { F.BreakHidden = !F.BreakHidden; Changed(); }));

        v.AddChild(Kit.Head("Drop sounds"));
        var sounds = Style.H(6);
        foreach (var (tier, name) in new[] { (LootTier.Rare, "From Rare"), (LootTier.Epic, "From Epic"), (LootTier.Legendary, "Legendary only") })
        {
            var t = tier;
            var b = Style.Segment(name, F.SoundsFrom == tier, () => { F.SoundsFrom = t; Changed(); });
            b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            sounds.AddChild(b);
        }
        v.AddChild(sounds);

        v.AddChild(Kit.RuleH());
        v.AddChild(Style.Label("Legendary, Set and Storied things, what the story needs, and a make you have never seen always show.", Style.TextItalic, 14, Kit.Dim, true));
    }

    void Changed()
    {
        Sound.Sfx.Click();
        Callable.From(Build).CallDeferred();
    }

    /// <summary>One of a few, chosen: a row with its name and what it means, the chosen one marked in ember.</summary>
    static Button Choice(string name, string says, bool on, Action pick)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 50) };
        var box = new StyleBoxFlat { BgColor = on ? new Color("#2f241c") : new Color(0, 0, 0, 0), BorderColor = Style.Ember, CornerDetail = 4 };
        box.SetCornerRadiusAll(3);
        box.BorderWidthLeft = on ? 2 : 0;
        var hover = new StyleBoxFlat { BgColor = new Color("#2c292e"), CornerDetail = 4 };
        hover.SetCornerRadiusAll(3);
        b.AddThemeStyleboxOverride("normal", UiArt.Frame(on ? "row_on" : "row", box));
        b.AddThemeStyleboxOverride("hover", on ? UiArt.Frame("row_on", box) : UiArt.Frame("row", hover));
        b.AddThemeStyleboxOverride("pressed", UiArt.Frame("row_on", box));
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        var inner = Style.V(1, Style.Label(name, Style.UiBold, 16, on ? Kit.Ink : Kit.Ink2), Style.Label(says, Style.Ui, 14, on ? Kit.Ink2 : Kit.Dim, true));
        inner.MouseFilter = MouseFilterEnum.Ignore;
        inner.Position = new Vector2(14, 5);
        b.AddChild(inner);
        b.Resized += () => inner.Size = new Vector2(b.Size.X - 24, b.Size.Y - 8);
        b.Pressed += pick;
        return b;
    }

    /// <summary>A promise, on or off: a small box ticked in ember, and the promise in words.</summary>
    static Button Toggle(string text, bool on, Action flip)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, Flat = true, CustomMinimumSize = new Vector2(0, 30) };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        var tick = new Tick(on) { SizeFlagsVertical = SizeFlags.ShrinkCenter };
        var row = Style.H(10, tick, Style.Label(text, Style.Ui, 15, on ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(2, 3);
        b.AddChild(row);
        b.MouseEntered += () => row.Modulate = new Color(1.15f, 1.12f, 1.08f);
        b.MouseExited += () => row.Modulate = Colors.White;
        b.Pressed += flip;
        return b;
    }

    partial class Tick : Control
    {
        readonly bool on;
        public Tick(bool on) { this.on = on; CustomMinimumSize = new Vector2(18, 18); MouseFilter = MouseFilterEnum.Ignore; }

        public override void _Draw()
        {
            DrawRect(new Rect2(1, 1, 16, 16), Kit.Tile);
            DrawRect(new Rect2(1, 1, 16, 16), on ? Style.Ember : new Color("#5a565c"), false, 1.5f);
            if (on) DrawPolyline(new[] { new Vector2(4.5f, 9), new Vector2(7.5f, 12.5f), new Vector2(13.5f, 5) }, Style.EmberHi, 2.2f, true);
        }
    }
}
