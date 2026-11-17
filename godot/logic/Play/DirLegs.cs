using System;

namespace SurvivorUnchained.Play;

/// <summary>
/// (aim-move) Directional legs, pure math. Alpha = her travel heading minus her facing (degrees, left positive).
/// The pelvis yaws by Delta so the clip's heading H stays inside the authored 45-degree band; the legs blend the
/// run clip set (f, fl, fr, b, bl, br at headings 0, 45, -45, 180, 135, -135) by H. Back mode has hysteresis.
/// </summary>
public static class DirLegs
{
    public const int F = 0, FL = 1, FR = 2, B = 3, BL = 4, BR = 5;
    public const double EnterBack = 110, LeaveBack = 70, MaxHalf = 45;

    public readonly record struct Result(double Delta, bool Back, double[] W, double H);

    static double Clamp(double v, double lo, double hi) => v < lo ? lo : v > hi ? hi : v;

    public static Result Solve(double alphaDeg, double speed, bool wasBack)
    {
        var w = new double[6];
        if (speed < LowerTurn.IdleSpeed) { w[F] = 1; return new Result(0, false, w, 0); }
        double a = LowerTurn.Wrap(alphaDeg);
        bool back = wasBack ? Math.Abs(a) >= LeaveBack : Math.Abs(a) > EnterBack;
        if (!back)
        {
            double r = Clamp(a / 2, -MaxHalf, MaxHalf);
            double h = r;
            if (h >= 0) { w[FL] = h / 45; w[F] = 1 - w[FL]; }
            else { w[FR] = -h / 45; w[F] = 1 - w[FR]; }
            return new Result(a - r, false, w, h);
        }
        double sign = a < 0 ? -1 : 1;
        double phi = a - 180 * sign;
        double rb = Clamp(phi / 2, -MaxHalf, MaxHalf);
        double delta = phi - rb;
        double hb = LowerTurn.Wrap(a - delta);
        double t = Clamp((Math.Abs(hb) - 135) / 45, 0, 1);
        w[B] = t;
        if (hb >= 0) w[BL] = 1 - t; else w[BR] = 1 - t;
        return new Result(delta, true, w, hb);
    }

    /// <summary>Exponential ease toward target over time constant tc (seconds).</summary>
    public static double Ease(double cur, double target, double dt, double tc)
        => tc <= 1e-6 ? target : cur + (target - cur) * (1 - Math.Exp(-dt / tc));
}
