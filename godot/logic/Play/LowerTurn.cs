using System;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her lower-body turn (A1 motion lead 19): while she faces her aim, her legs walk toward her travel and the chest stays on the aim.
/// Pure math. theta = her travel's signed angle from her facing, degrees, left positive (Move2D: 90 is her left).
/// FORWARD mode (|theta| under 90, hysteresis +-10): delta = clamp(theta, +-60), the node fed (0, +speed cos(theta-delta)).
/// BACK mode: she backpedals along the reverse line, phi = theta - 180 sign(theta), delta = clamp(phi, +-60),
/// the node fed (0, -speed |cos(phi-delta)|). delta is the yaw the pelvis takes (positive = to her left, a yaw about her up).
/// </summary>
public static class LowerTurn
{
    public const double MaxDeg = 60, SwitchDeg = 90, Hysteresis = 10, TimeConstant = 0.12;
    /// <summary>Below this ground speed (m/s) the turn eases to 0.</summary>
    public const double IdleSpeed = 0.15;
    /// <summary>How the spine takes the turn back out: spine_01, spine_02, spine_03 (each a yaw of share * delta; they sum to -1).</summary>
    public static readonly double[] SpineShares = { -0.4, -0.3, -0.3 };

    /// <summary>Wraps degrees to (-180, 180].</summary>
    public static double Wrap(double d)
    {
        d %= 360; if (d > 180) d -= 360; else if (d <= -180) d += 360;
        return d;
    }

    /// <summary>The mode after theta, given the mode before (back = true): the switch has a +-10 deg band around 90.</summary>
    public static bool IsBack(double thetaDeg, bool wasBack)
    {
        double a = Math.Abs(Wrap(thetaDeg));
        return wasBack ? a >= SwitchDeg - Hysteresis : a > SwitchDeg + Hysteresis;
    }

    /// <summary>The target turn (deg) and the node's (0, y) feed, y in m/s (negative back), for travel theta at speed.</summary>
    public static (double Delta, double FeedY, bool Back) Solve(double thetaDeg, double speed, bool wasBack)
    {
        double t = Wrap(thetaDeg);
        bool back = IsBack(t, wasBack);
        if (!back)
        {
            double d = Math.Clamp(t, -MaxDeg, MaxDeg);
            return (d, speed * Math.Cos((t - d) * Math.PI / 180), false);
        }
        double phi = t - 180 * (t >= 0 ? 1 : -1);
        double dd = Math.Clamp(phi, -MaxDeg, MaxDeg);
        return (dd, -speed * Math.Abs(Math.Cos((phi - dd) * Math.PI / 180)), true);
    }

    /// <summary>The back walk's play rate (moveBack mode): her backward ground speed over the clip's own, within [0.3, 2].</summary>
    public static double BackScale(double feedY, double clipSpeed) => clipSpeed < 0.05 ? 1 : Math.Clamp(Math.Abs(feedY) / clipSpeed, 0.3, 2);

    /// <summary>delta eased toward its target over dt seconds (time constant 0.12 s).</summary>
    public static double Ease(double delta, double target, double dt) => delta + (target - delta) * (1 - Math.Exp(-dt / TimeConstant));

    /// <summary>The spine bones' yaws (deg) for a turn delta: share * delta each.</summary>
    public static double[] SpineYaws(double deltaDeg) => new[] { SpineShares[0] * deltaDeg, SpineShares[1] * deltaDeg, SpineShares[2] * deltaDeg };
}
