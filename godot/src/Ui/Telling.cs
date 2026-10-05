using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

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
}
