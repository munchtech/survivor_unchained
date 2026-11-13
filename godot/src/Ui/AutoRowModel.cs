using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/* (bd-ui W3, no Godot: tests link this file) The campaign bar's auto tiles and the stance block, as numbers and words.
 * Round for what she acts by (the keys' seats), square for what fires by itself (the auto tiles). */
public static class AutoRowModel
{
    /// <summary>A tile's side, the gap between tiles, and the right edge of her first tile (design px at 1.0, the bar's
    /// space: the coin stands at 960; her three grow leftward from its left; what she wears grows rightward from its right).</summary>
    public const float Tile = 34, Gap = 6, HerRight = 910;
    /// <summary>Where the item tiles start with no stance block, the stance block's front disc's left edge, the gap from the
    /// Swap chip to the first item tile, and the right edge nothing is drawn past.</summary>
    public const float RightStart = 1012, StanceLeft = 1012, SwapGap = 8, RightEdge = 1264.5f, FitSlack = 2.5f, SwapChipRight = 1105;   // (bd-ui W15: RightEdge = silhouette 1226 minus 6 screen px; SwapChipRight = the Swap chip's settled right edge, a constant so the start never drifts; W13: the keeper statue's left silhouette at the row's height, screen x 1226 in .shots/bdui_r5_items4.png, minus 8 screen px: design 1263 at HUD 0.85)
    /// <summary>The row control's left edge.</summary>
    public const float Floor = 716;
    public const int HerSlots = 3;

    /// <summary>bd-ui W8, the HUD's tiers above the key caps, bottom up (design px, one place): the tile + stance row's bottom
    /// CapGap above the caps' top edge; the status shelf (marks ShelfH tall) with its bottom ShelfGap above the row's top; the
    /// level cards' bottom CardGap above the shelf's top.</summary>
    public const float CapGap = 12, ShelfGap = 6, ShelfH = 30, CardGap = 8;
    /// <summary>The status shelf's marks are 30 px round centred on y 950: its bottom edge.</summary>
    public const float ShelfBottom = 950 + 15;

    /// <summary>The status shelf's top edge (campaign, raised) for a row top.</summary>
    public static float ShelfTop(float rowTop) => rowTop - ShelfGap - ShelfH;

    /// <summary>The level card's bottom edge for a row top: CardGap above the shelf's top.</summary>
    public static float CardBottom(float rowTop) => ShelfTop(rowTop) - CardGap;

    /// <summary>The auto tile's timer bar (inside the tile's bottom edge): height, inset from the sides and the bottom.</summary>
    public const float BarH = 3.5f, BarInset = 3;

    /// <summary>The timer bar's fill width for a ready share.</summary>
    public static float BarFill(double ready) => (Tile - 2 * BarInset) * (float)Math.Clamp(ready, 0, 1);

    /// <summary>The fire cue: 120 ms, a gold-white flash (modulate 1.6 back to 1) and a 1.15x pop, both easing out.</summary>
    public const double FireLen = 0.12;
    public const float FireLight = 1.6f, FirePop = 1.15f;
    static float FireK(double since) => since < 0 || since >= FireLen ? 0 : (float)Math.Pow(1 - since / FireLen, 2);
    public static float FireModulate(double since) => 1 + (FireLight - 1) * FireK(since);
    public static float FireScale(double since) => 1 + (FirePop - 1) * FireK(since);

    /// <summary>The key caps' top edge: each cap's chip is centred on the seat's 12 o'clock, midway between the plate's top
    /// line and the ring's top (SeatKeys.Socket.SetCap), chipH tall (the tallest chip drawn: the mouse glyph's).</summary>
    public static float CapTop(float plateTopY, float seatY, float seatR, float chipH) => (plateTopY + seatY - seatR) / 2 - chipH / 2;

    /// <summary>The tile row's top: its bottom CapGap above the caps' top edge.</summary>
    public static float RowTop(float plateTopY, float seatY, float seatR, float chipH) => CapTop(plateTopY, seatY, seatR, chipH) - CapGap - Tile;

    /// <summary>How far the status shelf rises (campaign, tiles shown) so its bottom is ShelfGap above the tiles' top.</summary>
    public static float ShelfRaise(float rowTop) => Math.Max(0, ShelfBottom - (rowTop - ShelfGap));

    /// <summary>bd-ui W8, the stance block: the front disc (r 20) stands on the row's middle line; the back one (r 14) up and right.</summary>
    public const float StanceR = 20, StanceBackR = 14, StanceGlyph = 26, StanceBackGlyph = 18;
    public static readonly (float X, float Y) StanceBack = (34, -8);

    /// <summary>A set's disc middle once settled, from the front disc's middle: the active set in front, the other behind.</summary>
    public static (float X, float Y) DiscCentre((float X, float Y) front, int set, int active) =>
        set == active ? front : (front.X + StanceBack.X, front.Y + StanceBack.Y);

    /// <summary>The set a NewStance card's tail goes to: set II (index 1), the back disc while set I is up.</summary>
    public const int CardSet = 1;

    /// <summary>The level her auto slot opens at (a locked tile shows it): the first with her, the second at 7, the third at 10.</summary>
    public static int OpensAt(int index) => index switch { <= 0 => 1, 1 => 7, _ => 10 };

    public enum Kind { Her, Item, More }

    /// <summary>One place in the row: its kind, its index (her: 0-2 left of the coin outward; item: its order in the bar;
    /// More: how many item autos are not shown) and its left edge.</summary>
    public readonly record struct Place(Kind Kind, int Index, float X);

    /// <summary>Where the item tiles start: the Swap chip's right edge + 10 with the stance block shown, else 1012.</summary>
    public static float ItemStart(bool stanceShown) => stanceShown ? SwapChipRight + SwapGap : RightStart;

    /// <summary>How many item places fit from start with the last tile's right edge at or before RightEdge.</summary>
    public static int ItemCapacity(float start) => Math.Max(0, (int)Math.Floor((RightEdge + FitSlack - start + Gap) / (Tile + Gap)));

    /// <summary>Her three places (always, left of the coin), then the item autos right of the stance block from itemStart:
    /// with more items than places, the last place holds "+N" (N = the items it stands for).</summary>
    public static List<Place> Places(int items, float itemStart = RightStart)
    {
        var l = new List<Place>();
        for (int i = 0; i < HerSlots; i++) l.Add(new Place(Kind.Her, i, HerRight - Tile - i * (Tile + Gap)));
        int cap = ItemCapacity(itemStart);
        if (items <= 0 || cap <= 0) return l;
        float X(int j) => itemStart + j * (Tile + Gap);
        if (items <= cap) { for (int j = 0; j < items; j++) l.Add(new Place(Kind.Item, j, X(j))); return l; }
        for (int j = 0; j < cap - 1; j++) l.Add(new Place(Kind.Item, j, X(j)));
        l.Add(new Place(Kind.More, items - (cap - 1), X(cap - 1)));
        return l;
    }

    /// <summary>The share of the tile the sweep darkens, clockwise from 12: what is not yet ready.</summary>
    public static float NotReady(double ready) => (float)Math.Clamp(1 - ready, 0, 1);

    /// <summary>It fired this frame: it was ready and the ready share fell (the seats' rule).</summary>
    public static bool Fired(double was, double now) => was >= 0.98 && now < was - 0.4;

    /// <summary>The brightening after it fires: 1 at once, 0 after.</summary>
    public const double FlashLen = FireLen;
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

    /// <summary>The weapon glyph of a stance (glyphs.json has no crossed blades: the nearest; the mace has its own).</summary>
    public static string Glyph(string? stanceId) => stanceId switch { "shield" => "shield", "twin_blades" => "twin_blades", "mace" => "mace", _ => "sword" };
}
