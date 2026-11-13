using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/* (bd-ui W3, no Godot: tests link this file) The campaign bar's auto tiles and the stance block, as numbers and words.
 * Round for what she acts by (the keys' seats), square for what fires by itself (the auto tiles). */
public static class AutoRowModel
{
    /// <summary>A tile's side, the gap between her three, and the right edge of her first tile (design px at 1.0, the
    /// bar's space: the coin stands at 960, her tiles grow leftward from its left).</summary>
    public const float Tile = 34, Gap = 6, HerRight = 910;
    /// <summary>The item autos' places (the 4th and 5th tiles) and the left edge nothing is drawn past.</summary>
    public static readonly float[] ItemX = [756, 716];
    public const float Floor = 716;
    public const int HerSlots = 3;

    /// <summary>The gap between the tile row's bottom and the key caps' top edge, and between the status shelf's bottom and the
    /// tiles' top (design px).</summary>
    public const float CapGap = 3, ShelfGap = 5;
    /// <summary>The status shelf's marks are 30 px round centred on y 950: its bottom edge.</summary>
    public const float ShelfBottom = 950 + 15;

    /// <summary>The key caps' top edge: each cap's chip is centred on the seat's 12 o'clock, midway between the plate's top
    /// line and the ring's top (SeatKeys.Socket.SetCap), chipH tall (the tallest chip drawn: the mouse glyph's).</summary>
    public static float CapTop(float plateTopY, float seatY, float seatR, float chipH) => (plateTopY + seatY - seatR) / 2 - chipH / 2;

    /// <summary>The tile row's top: its bottom CapGap above the caps' top edge.</summary>
    public static float RowTop(float plateTopY, float seatY, float seatR, float chipH) => CapTop(plateTopY, seatY, seatR, chipH) - CapGap - Tile;

    /// <summary>How far the status shelf rises (campaign, tiles shown) so its bottom is ShelfGap above the tiles' top.</summary>
    public static float ShelfRaise(float rowTop) => Math.Max(0, ShelfBottom - (rowTop - ShelfGap));

    public enum Kind { Her, Item, More }

    /// <summary>One place in the row: its kind, its index (her: 0-2 left of the coin outward; item: its order in the bar;
    /// More: how many item autos are not shown) and its left edge.</summary>
    public readonly record struct Place(Kind Kind, int Index, float X);

    /// <summary>Her three places (always), then the item autos: up to two places; with more than two, the 4th holds the
    /// first and the 5th "+N" for the rest (N = items - 1).</summary>
    public static List<Place> Places(int items)
    {
        var l = new List<Place>();
        for (int i = 0; i < HerSlots; i++) l.Add(new Place(Kind.Her, i, HerRight - Tile - i * (Tile + Gap)));
        if (items <= 0) return l;
        if (items <= ItemX.Length) { for (int j = 0; j < items; j++) l.Add(new Place(Kind.Item, j, ItemX[j])); return l; }
        l.Add(new Place(Kind.Item, 0, ItemX[0]));
        l.Add(new Place(Kind.More, items - 1, ItemX[1]));
        return l;
    }

    /// <summary>The share of the tile the sweep darkens, clockwise from 12: what is not yet ready.</summary>
    public static float NotReady(double ready) => (float)Math.Clamp(1 - ready, 0, 1);

    /// <summary>It fired this frame: it was ready and the ready share fell (the seats' rule).</summary>
    public static bool Fired(double was, double now) => was >= 0.98 && now < was - 0.4;

    /// <summary>The 0.25 s brightening after it fires: 1 at once, 0 after.</summary>
    public const double FlashLen = 0.25;
    public static float Flash(double sinceFire) => sinceFire < 0 || sinceFire >= FlashLen ? 0 : (float)(1 - sinceFire / FlashLen);

    /// <summary>A swap strike's ready share: 1 - readyIn / cooldown.</summary>
    public static float StrikeShare(double readyIn, double cooldown) => cooldown <= 0 ? 1 : (float)Math.Clamp(1 - readyIn / cooldown, 0, 1);
}

/// <summary>The stance's hover card as lines: what it gives (pale gold) and what it costs (muted red), from stances.json.</summary>
public static class StanceText
{
    static string Name(string stat) => stat switch
    {
        "block" => "Block", "armor" => "Armor", "damage" => "Damage", "moveSpeed" => "Move speed", "cooldown" => "Attack speed",
        "maxHealth" => "Health", "knockback" => "Knockback", _ => stat,
    };

    /// <summary>One mod as a short line and whether it is a gift: "Armor +25%", "Block +1", "Move speed -8%". A cooldown is
    /// shown as speed (cooldown x1.18 is 15% slower).</summary>
    public static (string Text, bool Gift) Mod(StanceMod m)
    {
        if (m.Stat == "cooldown")
        {
            int pct = (int)Math.Round((1 / (1 + m.Value) - 1) * 100);
            return ($"{Name(m.Stat)} {Sign(pct)}%", pct >= 0);
        }
        if (m.Kind == ModKind.Flat) return ($"{Name(m.Stat)} {(m.Value >= 0 ? "+" : "-")}{Math.Abs(m.Value):0.##}", m.Value >= 0);
        int p = (int)Math.Round(m.Value * 100);
        return ($"{Name(m.Stat)} {Sign(p)}%", p >= 0);
    }

    static string Sign(int n) => (n >= 0 ? "+" : "-") + Math.Abs(n);

    static string Ordinal(int n) => n switch { 2 => "2nd", 3 => "3rd", _ => n + "th" };

    /// <summary>What her blows carry: "Every 3rd blow stuns", "Every blow bleeds"; plus the Warding light line.</summary>
    public static List<string> Blow(StanceBlow b)
    {
        var l = new List<string>();
        string every = b.Every <= 1 ? "Every blow" : $"Every {Ordinal(b.Every)} blow";
        if (b.Stun > 0) l.Add($"{every} stuns");
        else if (b.Stagger > 0) l.Add($"{every} staggers");
        if (b.Bleed != null) l.Add($"{every} bleeds");
        if (b.Ward > 0) l.Add("Blows bring her Warding light back sooner");
        return l;
    }

    /// <summary>The gifts (blow lines first, then the mods that help) and the prices (the mods that cost).</summary>
    public static (List<string> Gifts, List<string> Prices) Lines(StanceDef s)
    {
        var gifts = Blow(s.Blow);
        var prices = new List<string>();
        foreach (var m in s.Mods) { var (t, g) = Mod(m); (g ? gifts : prices).Add(t); }
        return (gifts, prices);
    }

    /// <summary>The weapon glyph of a stance (glyphs.json has no mace or crossed blades: the nearest).</summary>
    public static string Glyph(string? stanceId) => stanceId switch { "shield" => "shield", "twin_blades" => "dagger", "mace" => "fist", _ => "sword" };
}
