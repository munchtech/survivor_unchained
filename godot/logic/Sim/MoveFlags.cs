using System;

namespace SurvivorUnchained.Sim;

/// <summary>The movement fixes of GAME_PLAN tasks 3 and 4 (the Path of Exile 2 benchmark), one switch each, so the measuring
/// harness (--moves12) and the owner can run old against new on the same takes. All on by default since 23 November (the
/// owner played the A/B and picked the new, with the dash, not the roll): the game, the sim and every harness run what ships.
/// --move-old turns every fix off (the game as it was before); MoveFlagsTests turn them off to pin each fix alone.</summary>
public static class MoveFlags
{
    static MoveFlags() { Shipped(); }

    /// <summary>What ships: every fix on, the dash (no roll).</summary>
    public static void Shipped() { All(true); RollTime = RollLength = 0; }

    /// <summary>The camera rides her own motion exactly: no lead ahead of her run, no trail after a stop.</summary>
    public static bool CamLock;
    /// <summary>Steps (1/60 s) from rest to her full run, and from a full run to rest. 0: the old eased ramp (14/s).</summary>
    public static int StartFrames, StopFrames;
    /// <summary>A hit-stop on her holds her feet as well as her pose (the frozen pose no longer skates).</summary>
    public static bool StopHold;
    /// <summary>The dash goes where the keys or the stick are held; nothing held, to the cursor; a pad, her facing.</summary>
    public static bool DashHeld;
    /// <summary>She leaves a dash moving the way the keys are held (still, if none are) instead of along the dash.</summary>
    public static bool DashExit;

    /// <summary>The roll (its own switch, --move-roll, not part of --move-new: the reference is one clip, and the owner picks
    /// it): seconds it lasts (0: the old dash, 0.2 s at one speed) and metres it covers (0: the dash's own 5.5).</summary>
    public static double RollTime, RollLength;

    /// <summary>The roll's speed over this step: a straight fall from its opening speed to her run speed at its end (the shape
    /// the reference clip shows), covering length in RollTime. left: seconds of roll left after this step.</summary>
    public static double Roll(double length, double left, double dt, double run)
    {
        double mean = length / RollTime, end = Math.Min(run, mean), first = 2 * mean - end;
        double u = Math.Clamp((RollTime - left - dt / 2) / RollTime, 0, 1);
        return first + (end - first) * u;
    }

    /// <summary>Every fix on (--move-new) or off.</summary>
    public static void All(bool on)
    {
        CamLock = StopHold = DashHeld = DashExit = on;
        StartFrames = StopFrames = on ? 2 : 0;
    }

    /// <summary>Her velocity toward what the keys ask, at a fixed rate: her top speed gained over StartFrames steps, shed over
    /// StopFrames. False: that ramp is off, the caller eases as before.</summary>
    public static bool Step(ref double vx, ref double vz, double tx, double tz, double top, double dt)
    {
        int n = tx == 0 && tz == 0 ? StopFrames : StartFrames;
        if (n <= 0) return false;
        double dx = tx - vx, dz = tz - vz, d = Math.Sqrt(dx * dx + dz * dz), max = Math.Max(top, 0.01) * dt * 60 / n;
        if (d <= max) { vx = tx; vz = tz; }
        else { vx += dx * max / d; vz += dz * max / d; }
        return true;
    }
}
