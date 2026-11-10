using System;

namespace SurvivorUnchained.Ui;

/* M4 lead 13 (judge r3b M1, M2), the cost seat's pure side (no Godot: the tests compile it). One rule for the three looks:
 * no arc = affordable (Resolve at or above the cost); a partial amber arc = short; a full ring never stands. The arc reads
 * the same Resolve the hair reads, quantized to 1/96 of the circle, and is drawn at most MaxArc of the circle so a short
 * seat always shows its gap (at 39.9 of 40 she is short, and the seat says "almost", never "full"). Held while short
 * keeps the short interior (veil, dull glyph, arc) under the held ring: the key is down, nothing is armed. */
public static class SeatCost
{
    /// <summary>The most of the circle a short seat's arc may cover (7/8: a 45 degree gap at 12 o'clock always shows).</summary>
    public const float MaxArc = 0.875f;

    /// <summary>Short of its cost (a cost of 0 or less never is).</summary>
    public static bool Short(double value, double cost) => cost > 0 && value < cost;

    /// <summary>The arc's share of the circle: -1 when not short (no arc), else value / cost quantized down to 1/96 and
    /// held under MaxArc.</summary>
    public static float Arc(double value, double cost) =>
        Short(value, cost) ? Shown((float)(Math.Max(0, value) / cost)) : -1;

    /// <summary>A fraction already of the cost (a picture's pin, or Arc's own): quantized and held under MaxArc; -1 stays -1.</summary>
    public static float Shown(float fraction) =>
        fraction < 0 ? -1 : Math.Min(MathF.Floor(Math.Clamp(fraction, 0, 1) * 96) / 96, MaxArc);

    /* M4 lead 14 (judge r3c M3): a key's press floor. A kindled "now" key heaves from half its cost at Value/cost strength
     * (logic/Sim/Resolve.cs KindledPress: `Resolve.Value < cost / 2` returns), every other spender from its full cost.
     * Below the floor: the short look. From the floor to the cost: the fourth look, "it fires, not at full": the glyph
     * lit, no veil, the amber arc kept as the strength, an ink tick on the groove at the floor, no warm well. */

    /// <summary>A kindled "now" key's press floor as a share of its cost.</summary>
    public const float KindledFloor = 0.5f;

    /// <summary>The press floor as a share of the cost (1: the full cost).</summary>
    public static float FloorShare(bool kindledNow) => kindledNow ? KindledFloor : 1f;

    /// <summary>Short of the press floor: a press does nothing (a cost of 0 or less never is).</summary>
    public static bool ShortOfFloor(double value, double cost, float floorShare) => cost > 0 && value < cost * Floor(floorShare);

    /// <summary>Short of the floor, read from a shown arc (Arc's or a picture's pin): exact, since the arc is quantized
    /// down to 1/96 and the floor sits on a 1/96 step (48/96).</summary>
    public static bool ShortShown(float arc, float floorShare) => arc >= 0 && arc < Floor(floorShare);

    /// <summary>The floor's tick on the groove, as a share of the circle; -1 when the floor is the full cost (no tick).</summary>
    public static float Tick(float floorShare) => Floor(floorShare) < 1 ? Floor(floorShare) : -1;

    static float Floor(float share) => share > 0 && share < 1 ? share : 1f;

    /// <summary>The short interior (veil, dull glyph) shows whenever short, held or not; only a long wait's number hides it.</summary>
    public static bool ShortLook(bool shortOfCost, bool numbered) => shortOfCost && !numbered;

    /// <summary>The key down's warm well (the "press" light) only when the whole cost is in hand (above the floor and below
    /// the cost it fires, but not at full: no warm well).</summary>
    public static bool WarmWell(bool held, bool shortOfCost) => held && !shortOfCost;
}
