using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A page told in beats, as the end of a night or a map is (the experience director's brief:
/// the end is what the player remembers, the peak-end rule). Its numbers count up on
/// medallions, each landing with a blow; then its lines are set down one at a time, each with
/// its sound, the best last. A press tells it all at once, and the next leaves.
/// </summary>
public abstract partial class TellingScreen : Overlay
{
    protected TellingScreen(Game g) : base(g) { }

    // The numbers counting up: each medallion, its final value, how it is written, when it starts.
    readonly List<(Medallion M, double To, Func<double, string> Fmt, double At)> counts = new();
    // What is shown in turn: each thing, when, and its sound.
    readonly List<(Control C, double At, Action? Sound)> beats = new();
    readonly HashSet<Control> shown = new();
    readonly HashSet<Medallion> landed = new();
    protected double ShownFor, EndAt;
    /// <summary>Told all at once (a press, a click, a choice made), so it is never told twice.</summary>
    protected bool told;
    double tick;
    protected const double Count = 0.9;

    /// <summary>Everything told (a press skipped the telling, or it ran its course).</summary>
    protected bool Told => told || ShownFor >= EndAt;

    /// <summary>Ready to be told again from its first beat (the page is being built afresh).</summary>
    protected void Retell()
    {
        counts.Clear();
        beats.Clear();
        shown.Clear();
        landed.Clear();
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        ShownFor += delta;
        tick -= delta;
        foreach (var (m, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(m)) continue;
            double k = Told ? 1 : Math.Clamp((ShownFor - at) / Count, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != m.Text) { m.Text = t; m.Arc = (float)k; m.QueueRedraw(); if (!Told && tick <= 0) { tick = 0.07; Sound.Sfx.Hover(); } }
            // (each number lands with a blow)
            if (k >= 1 && landed.Add(m) && !told) Sound.Sfx.Bash();
        }
        CountWords();
        foreach (var (c, at, sound) in beats)
        {
            if (!IsInstanceValid(c)) continue;
            if (!shown.Contains(c) && (Told || ShownFor >= at))
            {
                shown.Add(c);
                if (!told) sound?.Invoke();
            }
            // In from a little to the left, as a line is set down.
            float k = Told ? 1 : (float)Math.Clamp((ShownFor - at) / 0.35, 0, 1);
            k = 1 - (1 - k) * (1 - k);
            c.Modulate = new Color(1, 1, 1, k);
            if (c.GetParent() is not Container) c.Position = c.Position with { X = (1 - k) * -18 };
        }
    }

    /// <summary>Shown in its turn, with its sound.</summary>
    protected T Beat<T>(T c, double at, Action? sound = null) where T : Control
    {
        c.Modulate = new Color(1, 1, 1, 0);
        beats.Add((c, at, sound));
        EndAt = Math.Max(EndAt, at + 0.35);
        return c;
    }

    /// <summary>A number on a medallion, counting up with its ring filling, its name under it.</summary>
    protected Control Stat(string glyph, double value, Func<double, string> fmt, string label, double at, bool good)
    {
        var m = new Medallion(150, fmt(0)) { Ring = good ? Style.Gold : Style.InkDim, ArcColor = good ? Style.Ember : Style.BloodHi, Ink = Style.GoldHi };
        counts.Add((m, value, fmt, at));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(m);
        var name = Style.H(6, Glyphs.Icon(glyph, 16, Style.Gold), Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));
        name.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(4, mc, name);
    }

    protected static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    protected static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, Style.Body, c));

    /// <summary>A column of the page: dark glass (or the box given), scrolling if it runs long.</summary>
    protected static Control Card(Control inner, StyleBox? box = null)
    {
        var p = Style.Panel(box ?? Style.Column(20), Style.Scroll(inner));
        p.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        inner.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return p;
    }

    /// <summary>What came out in the fist (ember shards, the people's own), as the things
    /// themselves; on a fall, what spilled, greyed beside it (docs/CRAFTING_DESIGN.md 6.1: the
    /// run's last decision, shown as what it cost).</summary>
    protected static Control Haul(Dictionary<string, int> carried, Dictionary<string, int> spilled, string carriedTitle)
    {
        static Control Things(Dictionary<string, int> d, bool lost)
        {
            var h = Style.H(Style.Gap2);
            foreach (var (m, n) in d)
            {
                var def = Rpg.Items.Get(m);
                var slot = ItemViews.Slot(new Rpg.ItemInstance { Def = m, Qty = n, Rarity = def.Rarity }, 60);
                slot.MouseFilter = MouseFilterEnum.Ignore;
                // (one spilled is named as one: "pieces of scar-glass" under a single piece misread it)
                var name = Style.Label(n == 1 ? def.Name.ToLowerInvariant() : def.Plural ?? def.Name.ToLowerInvariant(),
                    Style.Ui, Style.Caption, lost ? Style.InkFaint : Style.Ink, true, HorizontalAlignment.Center);
                var cell = Style.V(2, slot, name);
                cell.CustomMinimumSize = new Vector2(76, 0);
                if (lost) cell.Modulate = new Color(1, 1, 1, 0.45f);
                h.AddChild(cell);
            }
            return h;
        }
        var row = Style.H(Style.Gap4);
        if (carried.Count > 0)
            row.AddChild(Style.V(4, Style.Label(carriedTitle.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.EmberHi), Things(carried, false)));
        if (spilled.Count > 0)
            row.AddChild(Style.V(4, Style.Label("SPILLED WHEN YOU FELL", Style.UiHeavy, Style.Badge, Style.InkDim), Things(spilled, true)));
        return Style.V(4, row);
    }

    /// <summary>The way on: the button that first tells the rest, then goes.</summary>
    protected Control Onward(string text, Action go)
    {
        var b = Style.Button("", () => { if (Told) go(); else told = true; }, true);
        var row = Style.H(8, Style.Prompt(Act.Confirm), Style.Label(text, Style.UiBold, Style.Body, new Color("#ffe4b0")));
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(16, 7);
        b.AddChild(row);
        b.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 32, 42);
        var acts = Style.H(12, b);
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        return acts;
    }

    /* ------------------------------------------------- the result's page -- */

    // The numbers set as type, counting up: each label, its final value, how it is written, when.
    readonly List<(Label L, double To, Func<double, string> Fmt, double At)> words = new();

    /// <summary>
    /// A result's page as one panel over the world (the owner: "we like to see our beautiful game";
    /// no boxes in it): fitted to what it holds, centred, its ground a little see-through, with the
    /// verdict as its title between the chains, the place under it. Returns the panel's column.
    /// </summary>
    protected VBoxContainer ResultPanel(string verdict, Color tone, string place, float width = 1180)
    {
        HideHud();
        words.Clear();
        landedWords.Clear();
        // (a click anywhere off the panel tells the rest at once)
        AddChild(new Backdrop(() => told = true, 0.55f));
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(centre);
        AddChild(centre);
        // (a little more at the foot: the title's chains stand above its words, so equal pads
        // looked heavier at the top)
        var panel = Style.Panel(Kit.Window(Margin + 8, Margin, Margin + 10));
        panel.CustomMinimumSize = new Vector2(width, 0);
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) told = true; };
        centre.AddChild(panel);
        var v = Style.V(Style.Gap4);
        panel.AddChild(v);
        var title = new Title(verdict, 34);
        title.Modulate = tone;
        v.AddChild(title);
        v.AddChild(Style.Label(place, Style.TextItalic, 18, Kit.HeadInk, true, HorizontalAlignment.Center));
        return v;
    }

    /// <summary>The numbers as a ledger line, as Self's attributes are: a large numeral counting up
    /// over its name in small capitals, each on one baseline, fine rules between. No medallions.</summary>
    protected Control Tally(params (double Value, Func<double, string> Fmt, string Label, double At, bool Good)[] stats)
    {
        var line = Style.H(0);
        line.Alignment = BoxContainer.AlignmentMode.Center;
        for (int i = 0; i < stats.Length; i++)
        {
            var (value, fmt, label, at, good) = stats[i];
            if (i > 0) line.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(57, 56) });
            var n = Style.Label(fmt(0), Style.Display, 40, good ? Kit.Ink : Style.BloodHi, false, HorizontalAlignment.Center, true);
            words.Add((n, value, fmt, at));
            var cell = Style.V(0, n, Style.Label(label.ToUpperInvariant(), Style.DisplayLight, 14, Kit.HeadInk, false, HorizontalAlignment.Center, false));
            cell.CustomMinimumSize = new Vector2(130, 0);
            line.AddChild(cell);
        }
        return line;
    }

    /// <summary>Two columns side by side with a fine rule between them, no boxes; returns both.</summary>
    protected static (VBoxContainer Left, VBoxContainer Right) Columns(VBoxContainer page, float rightW)
    {
        var row = Style.H(0);
        var left = Style.V(Style.Gap3);
        left.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var right = Style.V(Style.Gap3);
        right.CustomMinimumSize = new Vector2(rightW, 0);
        row.AddChild(left);
        var rule = new LedgerRule { CustomMinimumSize = new Vector2(49, 0), SizeFlagsVertical = SizeFlags.Fill };
        row.AddChild(rule);
        row.AddChild(right);
        page.AddChild(row);
        return (left, right);
    }

    /// <summary>A register of the page opened: a little more air above its centred head than the
    /// page's lines have between them, so the registers read as groups.</summary>
    protected static void Register(VBoxContainer page, string title, string? note = null)
    {
        page.AddChild(Style.Gap(6));
        page.AddChild(Kit.HeadMid(title, note));
    }

    /// <summary>A counted thing as a ledger entry: its picture and how many, with no tile (it is
    /// counted, not a piece); greyed where it was lost.</summary>
    protected static Control Counted(string id, int n, bool lost = false)
    {
        var def = Rpg.Items.Get(id);
        var h = Sum(ItemPhotos.Icon(def.Icon, 36, Style.RarityOf(def.Rarity)), Rpg.Items.Several(id, n), lost ? Kit.Dim : Kit.Ink);
        if (lost) h.Modulate = new Color(1, 1, 1, 0.6f);
        return h;
    }

    /// <summary>A sum as a ledger entry: its mark and its words in its colour, on one centre line.</summary>
    protected static HBoxContainer Sum(Control mark, string text, Color c)
    {
        var h = Style.H(Style.Gap2, mark, Style.Label(text, Style.UiBold, 17, c));
        foreach (var x in h.GetChildren().OfType<Control>()) x.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        return h;
    }

    /// <summary>What came out as one centred ledger line (no boxes, no columns): the entries given,
    /// then on a fall what spilled, greyed, behind a fine rule; past the panel's width it breaks
    /// onto a second centred line rather than widening the panel.</summary>
    protected static HFlowContainer LedgerLine(IEnumerable<Control> kept, Dictionary<string, int>? spilled = null)
    {
        var row = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = FlowContainer.AlignmentMode.Center };
        row.AddThemeConstantOverride("h_separation", Style.Gap6);
        row.AddThemeConstantOverride("v_separation", Style.Gap2);
        foreach (var c in kept) row.AddChild(c);
        if (spilled is { Count: > 0 })
        {
            if (row.GetChildCount() > 0) row.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(29, 40), SizeFlagsVertical = SizeFlags.ShrinkCenter });
            var lost = Style.H(Style.Gap4, Style.Label("SPILLED", Style.UiHeavy, 12, Kit.Dim, false, HorizontalAlignment.Left, false));
            foreach (var (m, n) in spilled) lost.AddChild(Counted(m, n, true));
            foreach (var c in lost.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(lost);
        }
        return row;
    }

    /// <summary>The way on, as type with its key, there from the first moment: pressed during the
    /// telling it tells the rest; pressed after, it goes.</summary>
    protected Control OnwardWord(string text, Action go)
    {
        var w = Kit.Word(text, () => { if (Told) go(); else told = true; }, Style.EmberHi, 18);
        var row = Style.H(10, Style.Prompt(Act.Confirm), w);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        return row;
    }

    /// <summary>The numbers set as type, counting each frame (as the medallions do).</summary>
    protected void CountWords()
    {
        foreach (var (l, to, fmt, at) in words)
        {
            if (!IsInstanceValid(l)) continue;
            double k = Told ? 1 : Math.Clamp((ShownFor - at) / Count, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != l.Text) { l.Text = t; if (!Told && tick <= 0) { tick = 0.07; Sound.Sfx.Hover(); } }
            if (k >= 1 && landedWords.Add(l) && !told) Sound.Sfx.Bash();
        }
    }

    readonly HashSet<Label> landedWords = new();

    /// <summary>A find as a tile, its card beside it when hovered.</summary>
    protected Control FindTile(ItemInstance it, int size = 56)
    {
        var tile = ItemViews.Slot(it, size, ch: G.Journey.Ch);
        tile.MouseEntered += () =>
        {
            var (card, worn) = ItemViews.Compare(it, G.Journey.Ch, Rpg.Items.SlotFor(Rpg.Items.Get(it.Def)) != null);
            TipBeside(card, worn, tile, false, tile.GetGlobalRect().End.X);
        };
        tile.MouseExited += () => TipBeside(null, null, null, false, 0);
        return tile;
    }
}
