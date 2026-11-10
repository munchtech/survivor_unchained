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

    /// <summary>The short interior (veil, dull glyph) shows whenever short, held or not; only a long wait's number hides it.</summary>
    public static bool ShortLook(bool shortOfCost, bool numbered) => shortOfCost && !numbered;

    /// <summary>The key down's warm well (the "press" light) only when the cost is in hand.</summary>
    public static bool WarmWell(bool held, bool shortOfCost) => held && !shortOfCost;
}
