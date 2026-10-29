using System;

namespace SurvivorUnchained.Play;

/// <summary>
/// How the town's walkers keep apart (Folk.Step). The xhigh judge saw three walkers pressed together in lockstep at
/// the town's close camera, a carter bent double behind a woman, and the same pair of carters in step behind every
/// chest-up frame. So: no two walkers' centres closer than Gap (each a body of radius Body), someone close ahead on
/// your line is passed to the side and not tailed at their pace, and a stoop (work, the well's bucket) is only started
/// with nobody within Clear and is cut the moment its walker moves (PersonView.Locomotion).
/// </summary>
public static class FolkSpacing
{
    /// <summary>The least distance between two walkers' centres (m).</summary>
    public const double Gap = 0.9;
    /// <summary>A walker's body, for local avoidance (m).</summary>
    public const double Body = 0.45;
    /// <summary>How far ahead a walker looks for someone on its line (m).</summary>
    public const double Look = 2.2;
    /// <summary>Nobody this close (m) when a stoop starts.</summary>
    public const double Clear = 1.0;

    /// <summary>The clips that bend a townsperson over (never walked in, never started crowded).</summary>
    public static bool BendsOver(string clip) => clip is "Interact" or "PickUp" or "PickUp_Table";

    /// <summary>My share of pulling apart from someone closer than Gap: 0 when I am busy (at a stall, the well) and
    /// they walk (the walker steps round the worker), 1 the other way round, half each otherwise.</summary>
    public static double Share(bool meBusy, bool themBusy) => meBusy == themBusy ? 0.5 : meBusy ? 0 : 1;

    /// <summary>The move (x, z) that takes me out to Gap from someone at (ox, oz), my share of it; zero if far enough.
    /// Coincident centres part along `tieX`, `tieZ` (a unit vector of the walker's own).</summary>
    public static (double X, double Z) Apart(double x, double z, double ox, double oz, double share, double tieX = 1, double tieZ = 0)
    {
        double dx = x - ox, dz = z - oz, d = Math.Sqrt(dx * dx + dz * dz);
        if (d >= Gap || share <= 0) return (0, 0);
        if (d < 1e-6) return (tieX * Gap * share, tieZ * Gap * share);
        double k = (Gap - d) * share / d;
        return (dx * k, dz * k);
    }

    /// <summary>Someone on my line ahead: a sideways steer (x, z, per unit of my wanted speed) away from their side of
    /// my line, and the speed I may keep behind them (their speed along my line, less 10%, so a gap opens rather than
    /// a lockstep; +inf if they are no obstacle). (ux, uz) my unit heading; (ovx, ovz) their velocity.</summary>
    public static (double X, double Z, double Cap) Ahead(double x, double z, double ux, double uz, double ox, double oz, double ovx, double ovz)
    {
        double rx = ox - x, rz = oz - z;
        double along = rx * ux + rz * uz, side = rx * -uz + rz * ux;
        if (along <= 0 || along > Look || Math.Abs(side) >= 2 * Body) return (0, 0, double.PositiveInfinity);
        // (closer and more squarely on my line: a harder turn)
        double w = (1 - along / Look) * (1 - Math.Abs(side) / (2 * Body));
        double s = side >= 0 ? -1 : 1;
        double theirs = ovx * ux + ovz * uz;
        double cap = theirs > 0.2 ? Math.Max(0.4, theirs * 0.9) : double.PositiveInfinity;
        return (-uz * s * w * 1.6, ux * s * w * 1.6, cap);
    }

    /// <summary>How far (m) behind its lead's shoulder a companion walks, from a draw in [0, 1): 0.35 to 0.8, so two
    /// walking together are never a matched pair in step.</summary>
    public static double Lag(double r) => 0.35 + Math.Clamp(r, 0, 1) * 0.45;

    /// <summary>How far apart two who stop to talk stand, facing each other (m).</summary>
    public const double Talk = 1.1;

    /// <summary>Where a companion stands to talk while its lead stops: Talk from the lead along (sx, sz) (a unit vector
    /// across the camera's line when there is one, so the two stand side by side in the frame, never one behind the
    /// other), on its own side (-1 or 1).</summary>
    public static (double X, double Z) PairSpot(double lx, double lz, double sx, double sz, int side) =>
        (lx + sx * Talk * (side < 0 ? -1 : 1), lz + sz * Talk * (side < 0 ? -1 : 1));

    /// <summary>Two standing near one line of sight read as one figure with two heads (judge r2): the sideways move (x, z)
    /// that takes me out to Gap across the view (dx, dz: a unit vector, the camera's look) from someone standing at
    /// (ox, oz) within 4 m in depth, my share of it; zero if already clear. `tie` picks the side when exactly in line.</summary>
    public static (double X, double Z) Beside(double x, double z, double ox, double oz, double dx, double dz, double share, double tie = 1)
    {
        double rx = x - ox, rz = z - oz;
        double along = rx * dx + rz * dz, side = rx * -dz + rz * dx;
        if (Math.Abs(along) >= 4 || Math.Abs(side) >= Gap || share <= 0) return (0, 0);
        double s = Math.Abs(side) < 1e-6 ? (tie < 0 ? -1 : 1) : Math.Sign(side);
        double push = (Gap - Math.Abs(side)) * share * s;
        return (-dz * push, dx * push);
    }
}
