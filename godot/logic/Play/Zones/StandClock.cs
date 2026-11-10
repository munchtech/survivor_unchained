using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/// <summary>
/// The app can now charge a stander from any zone with one rule (H6's stand clock, Teeth.Director's stand fields): her
/// trail over the last StandFor s, all of it within StandMoved of where she is, and the pack's nearest foe at least
/// StandFrom off (the nearest if none is) charges her, with a second from another side (StandPair 2). The arena's
/// director (ArenaRun.Director.cs) and the story fights (Encounters, by world tier: world_tiers.json `stand`, M3) share it.
/// </summary>
public static class StandClock
{
    /// <summary>Her place now on the trail (the caller samples it each quarter second); older than StandFor + 0.3 s drops.</summary>
    public static void Sample(Queue<(double T, double X, double Z)> trail, double now, double x, double z, double standFor)
    {
        trail.Enqueue((now, x, z));
        while (trail.Count > 0 && trail.Peek().T < now - standFor - 0.3) trail.Dequeue();
    }

    /// <summary>She has stood: a full window behind her, all of it within StandMoved of where she is.</summary>
    public static bool Still(Queue<(double T, double X, double Z)> trail, double now, double x, double z, Teeth.Director d)
    {
        if (trail.Count == 0 || trail.Peek().T > now - d.StandFor) return false;
        foreach (var (_, tx, tz) in trail) if (Dist(tx, tz, x, z) >= d.StandMoved) return false;
        return true;
    }

    static bool Can(Battle b, Enemy e, Func<Enemy, bool>? may) =>
        !(e.Boss || e.Elite || e.Scripted || e.HoldUntil > b.Time || e.State != EnemyState.Active) && (may == null || may(e));

    /// <summary>The first charger: the nearest foe within StandNear at least StandFrom off (one at her elbow dies in its
    /// windup to the stander's own weapons, and a felled charger's lane is called off); none that far, the nearest.
    /// `may`: which foes the zone lets charge (null: any hostile).</summary>
    public static Enemy? First(Battle b, Teeth.Director d, Func<Enemy, bool>? may = null)
    {
        var p = b.Player;
        Enemy? near = null, close = null;
        double nd = double.MaxValue, cd = double.MaxValue;
        foreach (var e in b.HostilesInRadius(p.X, p.Z, d.StandNear))
        {
            if (!Can(b, e, may)) continue;
            double dd = Dist(e.X, e.Z, p.X, p.Z);
            if (dd >= d.StandFrom && dd < nd) { nd = dd; near = e; }
            if (dd < cd) { cd = dd; close = e; }
        }
        return near ?? close;
    }

    /// <summary>The second (StandPair 2): from at least a quarter turn round from the first, the nearest at least StandFrom off.</summary>
    public static Enemy? Second(Battle b, Teeth.Director d, Enemy near, Func<Enemy, bool>? may = null)
    {
        if (d.StandPair < 2) return null;
        var p = b.Player;
        double a0 = Math.Atan2(near.Z - p.Z, near.X - p.X);
        Enemy? other = null; double od = double.MaxValue;
        foreach (var e in b.HostilesInRadius(p.X, p.Z, d.StandNear))
        {
            if (e == near || !Can(b, e, may)) continue;
            double da = Math.Abs(Math.Atan2(Math.Sin(Math.Atan2(e.Z - p.Z, e.X - p.X) - a0), Math.Cos(Math.Atan2(e.Z - p.Z, e.X - p.X) - a0)));
            if (da < Math.PI / 2) continue;
            double dd = Dist(e.X, e.Z, p.X, p.Z);
            if (dd < d.StandFrom) dd += 1000;
            if (dd < od) { od = dd; other = e; }
        }
        return other;
    }
}
