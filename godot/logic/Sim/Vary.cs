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

    /// <summary>A copy's offset (x, z) from where its pack was asked to stand, uniform over a disc of radius r (judge r2:
    /// a block of them marched in a grid): from a hash of its seed, so no new draws from the fight's stream.</summary>
    public static (double X, double Z) Jitter(double seed, double r)
    {
        double a = Hash(seed, 0x3D1) * 2 * Math.PI, d = r * Math.Sqrt(Hash(seed, 0x6B5));
        return (Math.Cos(a) * d, Math.Sin(a) * d);
    }

    /// <summary>How long (s, 0 to max) a copy stands after it has risen before it comes on: a pack does not start as one.</summary>
    public static double Delay(double seed, double max) => max * Hash(seed, 0x1F7);

    /// <summary>A copy's coat (CrowdView): its value (lo to 1, evenly) and whether it is caked in mud (share of them).</summary>
    public static (double Value, bool Mud) Coat(double seed, double lo, double mudShare) =>
        (lo + (1 - lo) * Hash(seed, 0x5A9), Hash(seed, 0x2E3) < mudShare);

    /// <summary>A kind's second bodies: the visual a share of its copies wear instead (NPC 18: the plain risen's drowned
    /// woman, so a pack isn't one man cloned). Looks only: the kind's balance and hitbox are its own.</summary>
    public static readonly System.Collections.Generic.IReadOnlyDictionary<string, (string Visual, double Share)> Bodies =
        new System.Collections.Generic.Dictionary<string, (string, double)> { ["risen_shroud"] = ("risen_shroud_w", 0.4) };

    /// <summary>The visual a copy wears: its kind's, or for a share of them (from its seed, everywhere it spawns) the
    /// kind's second body.</summary>
    public static string Body(string visual, double seed) =>
        Bodies.TryGetValue(visual, out var alt) && Hash(seed, 0x6B1) < alt.Share ? alt.Visual : visual;

    /// <summary>Whether a copy walks its kind's second gait (the mirror reach), share of them.</summary>
    public static bool Second(double seed, double share) => Hash(seed, 0x4C7) < share;

    /// <summary>The sideways steer (x, z, per unit of wanted speed) round a thing to keep clear of (a lamp post, a camp
    /// fire): circle (ox, oz) of radius r plus `margin`, for one at (x, z) heading (ux, uz). Zero unless it is ahead
    /// and the line passes within the margin; stronger the nearer. Also a push straight out if already inside.</summary>
    public static (double X, double Z) Avoid(double x, double z, double ux, double uz, double ox, double oz, double r, double margin)
    {
        double rx = ox - x, rz = oz - z, d = Math.Sqrt(rx * rx + rz * rz), clear = r + margin;
        if (d < 1e-6) return (-uz, ux);
        if (d < clear) { double k = (clear - d) / clear * 2.5; return (-rx / d * k, -rz / d * k); }
        double along = rx * ux + rz * uz, side = rx * -uz + rz * ux;
        if (along <= 0 || along > clear + 2.5 || Math.Abs(side) >= clear) return (0, 0);
        double w = (1 - Math.Abs(side) / clear) * (1 - Math.Max(0, along - clear) / 2.5) * 1.8;
        double s = side >= 0 ? -1 : 1;
        return (-uz * s * w, ux * s * w);
    }

    /// <summary>A uniform [0, 1) value from a seed and a salt.</summary>
    public static double Hash(double seed, int salt)
    {
        ulong x = (ulong)(seed * 4294967296.0) ^ ((ulong)salt * 0x9E3779B97F4A7C15UL);
        x ^= x >> 33; x *= 0xFF51AFD7ED558CCDUL; x ^= x >> 33; x *= 0xC4CEB93FE53A1C2DUL; x ^= x >> 33;
        return (x >> 11) * (1.0 / 9007199254740992.0);
    }
}
