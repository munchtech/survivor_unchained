using System;

namespace SurvivorUnchained.Sim;

/// <summary>
/// Per-copy variety for a kind drawn many at once (EnemyDef.Spread, Size, Weave): the Low Ford's risen read as six
/// clones walking single file in one stride. Every pick is symmetric about 1 (or 0), so a pack's mean pace, size and
/// heading are the kind's own: the fight's balance is unchanged, only who is ahead and who lags.
/// </summary>
public static class Vary
{
    /// <summary>A copy's pace multiplier from a uniform draw r in [0, 1): 1 +- spread, evenly.</summary>
    public static double Pace(double r, double spread) => 1 - spread + Math.Clamp(r, 0, 1) * 2 * spread;

    /// <summary>A copy's size multiplier from its seed (in [0, 1)): 1 +- spread, from a hash of the seed so it does not
    /// track its pace (both read from the same fight stream).</summary>
    public static double Size(double seed, double spread) => spread <= 0 ? 1 : 1 + (Hash(seed, 0x51ED) * 2 - 1) * spread;

    /// <summary>How far (radians) a copy's heading weaves off its line at time t: up to deg degrees, slow (a period of
    /// 6-10 s, its own), so a file of them on one flow line fans out into a loose pack.</summary>
    public static double Weave(double t, double seed, double deg)
    {
        double rate = 2 * Math.PI / (6 + 4 * Hash(seed, 0x7A3)), ph = Hash(seed, 0x2C1) * 2 * Math.PI;
        return deg * Math.PI / 180 * (0.65 * Math.Sin(t * rate + ph) + 0.35 * Math.Sin(t * rate * 2.3 + ph * 1.7));
    }

    /// <summary>A uniform [0, 1) value from a seed and a salt.</summary>
    public static double Hash(double seed, int salt)
    {
        ulong x = (ulong)(seed * 4294967296.0) ^ ((ulong)salt * 0x9E3779B97F4A7C15UL);
        x ^= x >> 33; x *= 0xFF51AFD7ED558CCDUL; x ^= x >> 33; x *= 0xC4CEB93FE53A1C2DUL; x ^= x >> 33;
        return (x >> 11) * (1.0 / 9007199254740992.0);
    }
}
