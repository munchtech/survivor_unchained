using System;

namespace SurvivorUnchained.Core;

/// <summary>
/// How far a hanging front panel (the Reaver's loincloth: a "panels" bone in
/// art/people/rig_helpers.json) swings forward with her leading thigh. The
/// law is tools/anim/helpers.py's panel_turn, number for number; HerJoints
/// turns the bone by it. Plain C#, so the tests hold it to the tools'.
/// </summary>
public static class PanelSwing
{
    public readonly record struct Law(double Amount, double Soft, double SpreadFrom, double SpreadTo, double SpreadDamp);

    /// <summary>Polynomial smooth max, <paramref name="k"/> wide (max + k/4 where a == b).</summary>
    public static double SmoothMax(double a, double b, double k)
    {
        double h = Math.Max(k - Math.Abs(a - b), 0) / k;
        return Math.Max(a, b) + h * h * k / 4;
    }

    /// <summary>0 below 0, x - k/2 above k, a quadratic between (smooth, never below 0).</summary>
    public static double SoftRelu(double x, double k) => x <= 0 ? 0 : x < k ? x * x / (2 * k) : x - k / 2;

    static double Smooth(double t)
    {
        t = Math.Clamp(t, 0, 1);
        return t * t * (3 - 2 * t);
    }

    /// <summary>Degrees the panel turns forward from each thigh's forward swing
    /// (fl, fr) and spread (al, ar), degrees from rest: the leading thigh's
    /// swing (a smooth max, so no pop as the legs cross), never back, damped
    /// as the thighs spread (on a seat with the knees apart it lifts less).</summary>
    public static double Turn(in Law law, double fl, double fr, double al, double ar)
    {
        double k = law.Soft;
        double lead = SmoothMax(fl, fr, k) - k / 4;
        double damp = 1 - law.SpreadDamp * Smooth(((al + ar) / 2 - law.SpreadFrom) / (law.SpreadTo - law.SpreadFrom));
        return law.Amount * SoftRelu(lead, k) * damp;
    }

    /// <summary>A thigh's line (its +Y in her rest axes carried with the
    /// pelvis: +Y up, +Z her front) against its rest line: (forward swing in
    /// her side plane, spread out to <paramref name="side"/>, +1 her left, -1
    /// her right), degrees.</summary>
    public static (double Swing, double Spread) SwingSpread(double x, double y, double z, double x0, double y0, double z0, int side)
    {
        static double Fwd(double y, double z) => Math.Atan2(z, -y) * 180 / Math.PI;
        static double Out(double x, int s) => Math.Asin(Math.Clamp(x * s, -1, 1)) * 180 / Math.PI;
        return (Fwd(y, z) - Fwd(y0, z0), Out(x, side) - Out(x0, side));
    }
}
