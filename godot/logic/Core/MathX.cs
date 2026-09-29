using System;

namespace SurvivorUnchained.Core;

/// <summary>
/// Small numeric toolkit shared by the simulation and the view. Hashes are
/// computed the way the web game's JavaScript computes them (in doubles,
/// wrapped to 32 bits where it wraps), so places are laid out identically.
/// </summary>
public static class MathX
{
    public const double Tau = Math.PI * 2;

    public static double Clamp(double v, double lo, double hi) => v < lo ? lo : v > hi ? hi : v;
    public static double Clamp01(double v) => v < 0 ? 0 : v > 1 ? 1 : v;
    public static double Lerp(double a, double b, double t) => a + (b - a) * t;
    public static double InvLerp(double a, double b, double v) => a == b ? 0 : (v - a) / (b - a);
    public static double Remap(double a, double b, double c, double d, double v) => Lerp(c, d, Clamp01(InvLerp(a, b, v)));
    public static double Smoothstep(double a, double b, double v)
    {
        double t = Clamp01(InvLerp(a, b, v));
        return t * t * (3 - 2 * t);
    }

    /// <summary>Frame-rate independent exponential approach; higher sharpness
    /// is snappier.</summary>
    public static double Damp(double current, double target, double sharpness, double dt) =>
        Lerp(current, target, 1 - Math.Exp(-sharpness * dt));

    /// <summary>Shortest signed difference between two angles, in (-PI, PI].</summary>
    public static double AngleDelta(double from, double to)
    {
        double d = (to - from) % Tau;
        if (d > Math.PI) d -= Tau;
        else if (d <= -Math.PI) d += Tau;
        return d;
    }

    public static double DampAngle(double current, double target, double sharpness, double dt) =>
        current + AngleDelta(current, target) * (1 - Math.Exp(-sharpness * dt));

    /// <summary>Normalise an angle into (-PI, PI] (atan2 of its sine and cosine).</summary>
    public static double Wrap(double a) => Math.Atan2(Math.Sin(a), Math.Cos(a));

    public static double Dist2(double ax, double az, double bx, double bz)
    {
        double dx = bx - ax, dz = bz - az;
        return dx * dx + dz * dz;
    }
    public static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt(Dist2(ax, az, bx, bz));
    public static double Len(double x, double z) => Math.Sqrt(x * x + z * z);

    /// <summary>Distance from point p to segment ab, in the XZ plane.</summary>
    public static double DistToSegment(double px, double pz, double ax, double az, double bx, double bz)
    {
        double abx = bx - ax, abz = bz - az;
        double l2 = abx * abx + abz * abz;
        double t = l2 > 0 ? ((px - ax) * abx + (pz - az) * abz) / l2 : 0;
        t = Clamp01(t);
        return Dist(px, pz, ax + abx * t, az + abz * t);
    }

    /// <summary>JavaScript's Math.round: halves go up.</summary>
    public static double Round(double v) => Math.Floor(v + 0.5);
    public static int RoundInt(double v) => (int)Math.Floor(v + 0.5);

    /* ------------------------------------------- JavaScript integer semantics -- */

    /// <summary>JavaScript's ToInt32: truncate, wrap modulo 2^32.</summary>
    public static int JsInt32(double v)
    {
        if (double.IsNaN(v) || double.IsInfinity(v)) return 0;
        double t = Math.Truncate(v);
        double m = t % 4294967296.0;
        if (m < 0) m += 4294967296.0;
        return unchecked((int)(uint)m);
    }
    public static uint JsUint32(double v) => unchecked((uint)JsInt32(v));
    public static int Imul(int a, int b) => unchecked(a * b);

    /// <summary>Integer hash to [0,1). Stable across sessions, used for placement.</summary>
    public static double Hash2(double x, double y, double seed = 0)
    {
        double h = (double)JsInt32(x) * 374761393 + (double)JsInt32(y) * 668265263 + (double)JsInt32(seed) * 2147483647;
        int hi = JsInt32(h);
        double h2 = (double)(hi ^ (int)((uint)hi >> 13)) * 1274126177;
        int h3 = JsInt32(h2);
        h3 ^= (int)((uint)h3 >> 16);
        return (uint)h3 / 4294967296.0;
    }

    public static double Hash1(double x, double seed = 0) => Hash2(x, 0x5bd1e995, seed);

    public static uint HashString(string s)
    {
        uint h = 2166136261;
        foreach (char c in s)
        {
            h ^= c;
            h = unchecked(h * 16777619);
        }
        return h;
    }
}
