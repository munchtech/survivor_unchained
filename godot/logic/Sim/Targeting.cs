using System;

namespace SurvivorUnchained.Sim;

/// <summary>Picking her priority target (H1 combat teeth, item 4; Battle.Priority): the foe under the pointer, or on a pad
/// the nearest foe in the right stick's direction. A champion or a boss under the pointer wins over fodder beside it, so a
/// hover meant for the big one is not stolen by the crowd round its feet.</summary>
public static class Targeting
{
    /// <summary>How far from the pointer's ground point a foe may stand and still be the one hovered (beyond its radius).</summary>
    public const double Slop = 0.9;
    /// <summary>The pad's pick: within this half-angle of the stick and this reach.</summary>
    public const double PadHalfAngle = 0.45, PadReach = 16;

    /// <summary>The foe hovered at a ground point: the nearest within its radius plus Slop, champions and bosses first.</summary>
    public static Enemy? AtPointer(Battle b, double x, double z)
    {
        Enemy? best = null;
        double bestScore = double.MaxValue;
        foreach (var e in b.HostilesInRadius(x, z, 3))
        {
            double d = Math.Sqrt((e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z)) - e.Radius;
            if (d > Slop) continue;
            double score = d - (e.Boss ? 2 : e.Elite ? 1 : 0);
            if (score < bestScore) { bestScore = score; best = e; }
        }
        return best;
    }

    /// <summary>The pad's pick: the foe nearest her within PadHalfAngle of the stick's direction, champions weighed as
    /// a third nearer. Null when the stick rests.</summary>
    public static Enemy? AlongStick(Battle b, double sx, double sz)
    {
        double l = Math.Sqrt(sx * sx + sz * sz);
        if (l < 0.35) return null;
        sx /= l; sz /= l;
        var p = b.Player;
        Enemy? best = null;
        double bestScore = double.MaxValue, cos = Math.Cos(PadHalfAngle);
        foreach (var e in b.HostilesInRadius(p.X, p.Z, PadReach))
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d < 0.01) continue;
            if ((dx * sx + dz * sz) / d < cos) continue;
            double score = d * (e.Boss || e.Elite ? 0.67 : 1);
            if (score < bestScore) { bestScore = score; best = e; }
        }
        return best;
    }
}
