using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;

using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Zones;

/// <summary>The bots' hold of a board's lamp (H1 item 6B; Play/Zones/ArenaRun.Lamp.cs). Each night (its own dice, so the
/// sim's are never touched) the hands hold it or not, by bot (Content/Boards.LampDef.Hold: deft 1, human 0.6, careless
/// 0.3, plain 0.7). A holder goes to the fold when the lamp catches, down the ground's way (NavField: through the nearest
/// gap), keeps inside its pool when nothing is at her throat, goes at snuffers at the lamp first, and lights it again when
/// it is out. A non-holder plays as before. Its counts are the night's report (RunResult.Lamp*).</summary>
public sealed class LampHold
{
    public readonly bool Holds;
    readonly ArenaRun zone;
    readonly BoardLamp lamp;
    readonly NavField? nav;
    /// <summary>Seconds she stood in its lit pool.</summary>
    public double InPool;

    LampHold(ArenaRun zone, BoardLamp lamp, NavField? nav, bool holds) { this.zone = zone; this.lamp = lamp; this.nav = nav; Holds = holds; }

    /// <summary>The night's hold, or null (no lamp tonight). bot: deft, human, careless or plain.</summary>
    public static LampHold? For(ArenaRun zone, MapBuild map, Battle b, int seed, string bot)
    {
        if (zone.Lamp is not { } lamp) return null;
        var rng = new Rng((uint)(seed * 40503 + 911));
        bool holds = rng.Next() < lamp.Def.Hold.GetValueOrDefault(bot, 0);
        double r = (zone.Board?.Radius ?? 60) + 10;
        var nav = holds ? new NavField(map, b, lamp.X, lamp.Z, (-r, -r, r, r)) : null;
        return new LampHold(zone, lamp, nav, holds);
    }

    /// <summary>Count this step (dt seconds).</summary>
    public void Tick(double dt) { if (zone.InLampPool) InPool += dt; }

    /// <summary>Where the holder wants her now, or null (play as the hands would: she is where she should be).</summary>
    public (double X, double Z)? Goal(Battle b)
    {
        if (!Holds || b.HeldLamp is not { Caught: true }) return null;
        var p = b.Player;
        var d = lamp.Def;
        double her = Dist(p.X, p.Z, lamp.X, lamp.Z);
        bool snuffed = false;
        foreach (var e in b.Enemies.Living())
            if (e.Goal && e.State != EnemyState.Dying && Dist(e.X, e.Z, lamp.X, lamp.Z) <= d.AtLamp + 1) { snuffed = true; break; }
        // Out, or snuffers at it: to the wick itself (within reach of them, and of the relight).
        if (!zone.LampLit || snuffed) return her > 1.0 ? Way(p.X, p.Z, her) : (lamp.X, lamp.Z);
        // Lit, and she is near its pool's edge or out of it: back in.
        if (her > d.Pool - 2) return Way(p.X, p.Z, her);
        return null;
    }

    /// <summary>Whether a move this step would carry her out past the pool's edge (the holder turns it back).</summary>
    public bool Leaving(Battle b, double mx, double mz)
    {
        if (!Holds || b.HeldLamp is not { Caught: true }) return false;
        var p = b.Player;
        double ox = p.X - lamp.X, oz = p.Z - lamp.Z, her = Math.Sqrt(ox * ox + oz * oz);
        return her > lamp.Def.Pool - 3 && ox * mx + oz * mz > 0;
    }

    (double X, double Z) Way(double x, double z, double her)
    {
        // Inside the fold, straight; outside it, down the ground's way (round the wall to a gap).
        if (nav == null || her < (zone.Board?.Fold.InnerR ?? 0) - 1) return (lamp.X, lamp.Z);
        return nav.Onward(x, z);
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
