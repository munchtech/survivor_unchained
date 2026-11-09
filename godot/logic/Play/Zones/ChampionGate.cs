using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Zones;

/// <summary>
/// (M5 r3) No tutorial card on a champion's wake. The judge, round 2: BY DAY came 2.5 s before Red Tolly woke, THE LAMP BOARD
/// 6 s before Mother Mire. A card waits while a champion (a named foe, not a boss) is awake near her, or while her walk will
/// wake a resting champion's pack within Ahead seconds (the pack's waking distance against how fast she closes on it); one
/// already up comes down as the wake comes (Prologue.Tip). Engine-free: the fight's foes and her movement.
/// </summary>
public static class ChampionGate
{
    /// <summary>Seconds ahead a resting champion's wake holds the cards.</summary>
    public const double Ahead = 6;
    /// <summary>An awake champion within this of her (m) holds the cards.</summary>
    public const double AwakeNear = 30;
    /// <summary>Within this of a champion pack's waking distance (m), she is at its wake whatever her pace.</summary>
    public const double Close = 4;

    /// <summary>Seconds until she is within `wake` of a foe `dist` away, closing at `closing` m/s (0: she is in reach;
    /// infinity: not closing).</summary>
    public static double WakeIn(double dist, double wake, double closing)
    {
        double gap = dist - wake;
        if (gap <= 0) return 0;
        return closing > 0.3 ? gap / closing : double.PositiveInfinity;
    }

    /// <summary>A champion is awake near her, or its pack wakes within `ahead` seconds.</summary>
    public static bool Due(Battle b, double ahead = Ahead)
    {
        var p = b.Player;
        var foes = b.Enemies.Living().Where(e => e.State != EnemyState.Dying && e.Disposition == Disposition.Hostile).ToList();
        var homes = new List<(double X, double Z)>();
        foreach (var e in foes)
        {
            if (e.Named == null || e.Boss) continue;
            double d = Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z));
            if (e.Roused || e.Wake <= 0) { if (d < AwakeNear) return true; }
            else homes.Add((e.HomeX, e.HomeZ));
        }
        if (homes.Count == 0) return false;
        foreach (var e in foes)
        {
            if (e.Roused || e.Wake <= 0 || !homes.Any(h => Math.Abs(h.X - e.HomeX) + Math.Abs(h.Z - e.HomeZ) <= 1)) continue;
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d - e.Wake <= Close) return true;
            double closing = d > 1e-6 ? (dx * p.Vx + dz * p.Vz) / d : 0;
            if (WakeIn(d, e.Wake, closing) < ahead) return true;
        }
        return false;
    }
}
