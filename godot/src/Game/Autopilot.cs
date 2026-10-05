using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>
/// A crude player, for testing and for pictures (the web game's
/// game/autopilot.ts): walks the prologue from the fire down the road, fights
/// on the way, opens the watchman's chest, takes the first card of every
/// draft, and out in a fight circles a patch of ground keeping the crowd in
/// front of it. It is not good at the game; it shows the game runs.
/// </summary>
public sealed class Autopilot
{
    readonly Game g;
    readonly HashSet<Act> pressed = new();
    int wp = 1;
    double t, orbit, dashT, abilityT, drinkT, stuckT, sideT, lastX, lastZ, postT, resultT;
    int side = 1;
    (double X, double Z, double R)? territory;
    /// <summary>Take the drafts and otherwise stand still (--auto idle): the worst player.</summary>
    public bool Idle;
    public (double X, double Z) Move { get; private set; }
    public readonly List<string> Log = new();
    string lastStage = "";

    public Autopilot(Game game) { g = game; }

    /// <summary>A press the survivor makes this step (taken once).</summary>
    public bool Take(Act a) => pressed.Remove(a);
    void Press(Act a) => pressed.Add(a);

    public void Drive(double dt)
    {
        t += dt;
        Move = (0, 0);
        if (g.Overlay == "draft") { g.Pick(0); return; }
        if (g.Overlay == "dialogue") { g.Advance(); return; }
        // A chest opening is watched to its end (pictures of it).
        if (g.Overlay == "chest") return;
        // A night's result is read, then left as a player leaves it (closing it as a screen
        // stranded the survivor on the empty field).
        if (g.Overlay == "arena") { if ((resultT += dt) > 5) { resultT = 0; Controls.Instance.Press(Act.Confirm); } return; }
        if (g.Overlay != null) { g.CloseOverlay(); return; }
        var b = g.Battle;
        var z = g.Zone;
        if (b == null || z == null || !b.Player.Alive || g.InTransit || Idle) return;
        if (z.Id != "lowford") { Field(dt, b); return; }
        Prologue(dt, b, z);
    }

    void Prologue(double dt, Battle b, ZoneRuntime z)
    {
        var d = z.Debug();
        var stage = d.GetValueOrDefault("stage")?.ToString() ?? "";
        if (stage != lastStage) { Log.Add($"{t:0}s {stage} lvl{b.EmberLevel} hp{Math.Round(b.Player.Hp)} kills{b.KillCount}"); lastStage = stage; }
        var p = b.Player;
        var meta = g.Scene!.Data.Meta;
        XZ Place(string n) => meta.Place("LOWFORD", n);
        double tx = p.X, tz = p.Z;
        switch (stage)
        {
            case "Wake" or "Rising" or "Ambush":
            {
                var c = stage == "Ambush" ? Place("cart") : Place("camp");
                orbit += dt * 0.35;
                tx = c.X + Math.Cos(orbit) * 7 - (stage == "Ambush" ? 4 : 0);
                tz = c.Z + Math.Sin(orbit) * 6 + (stage == "Ambush" ? 6 : 0);
                break;
            }
            case "Post" when d.GetValueOrDefault("chestOpened") is false && postT < 25:
            {
                // From the chest's far side from the dead watchman, so the prompt is the chest's
                // (standing between them, the watchman's book was read over and over).
                postT += dt;
                var c = Place("chest");
                var m = Place("watchman");
                double ax = c.X - m.X, az = c.Z - m.Z, al = Math.Max(0.01, Math.Sqrt(ax * ax + az * az));
                tx = c.X + ax / al * 1.2; tz = c.Z + az / al * 1.2;
                if (Math.Sqrt((p.X - tx) * (p.X - tx) + (p.Z - tz) * (p.Z - tz)) < 1.0 && g.Prompted == "chest") Controls.Instance.Press(Act.Interact);
                break;
            }
            case "Boss" or "Intro":
            {
                var f = Place("ford");
                orbit += dt * 0.3;
                tx = f.X + Math.Cos(orbit) * 9; tz = f.Z + 10 + Math.Sin(orbit) * 5;
                break;
            }
            case "Victory" or "Dawn":
                break;
            default:
            {
                // Down the road.
                var road = meta.Paths.GetValueOrDefault("ROAD") ?? Array.Empty<double[]>();
                while (wp < road.Length - 1 && road[wp][1] > p.Z - 3) wp++;
                if (road.Length > 0) { tx = road[Math.Min(wp, road.Length - 1)][0]; tz = road[Math.Min(wp, road.Length - 1)][1]; }
                break;
            }
        }
        // Keep off the crowd.
        double rx = 0, rz = 0;
        int near = 0;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State == EnemyState.Dying || e.Disposition != Disposition.Hostile) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z, dd = Math.Sqrt(dx * dx + dz * dz);
            if (dd < 4.5 && dd > 0.01) { rx += dx / dd * (4.5 - dd); rz += dz / dd * (4.5 - dd); }
            if (dd < 2.2) near++;
        }
        Steer(dt, tx - p.X + rx * 1.4, tz - p.Z + rz * 1.4, p, tx, tz);
        dashT -= dt; abilityT -= dt; drinkT -= dt;
        if (near >= 5 && dashT <= 0) { Press(Act.Dash); dashT = 1.2; }
        if (near >= 3 && abilityT <= 0) { Press(Act.Ability); abilityT = 2; }
        if (p.Hp < b.MaxHp * 0.35 && drinkT <= 0) { Controls.Instance.Press(Act.Ultimate); drinkT = 1.5; }
    }

    /// <summary>Out in a fight with no script: circle a patch of ground, keep
    /// the crowd in front and moving, step out of marked ground and lunges,
    /// pick up ember when nothing is close, bash when mobbed, drink when low.
    /// An arena's boss up, it circles the boss instead and reads its fight as a
    /// practised player does (BossSense), so pictures show a fight fought.</summary>
    void Field(double dt, Battle b)
    {
        var p = b.Player;
        var script = g.Zone switch { ArenaRun a => a.BossScript, MapRun m => m.BossScript, _ => null };
        var boss = script is { } s && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;
        (double X, double Z, double R) home = boss != null ? (boss.E.X, boss.E.Z, 10.0) : territory ??= (p.X, p.Z, 18);
        double rx = 0, rz = 0;
        int close = 0;
        var sectors = new bool[8];
        foreach (var e in b.Enemies.Living())
        {
            if (e.State is EnemyState.Dying or EnemyState.Burrowed || !b.HostileToPlayer(e)) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z, dd = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            if (dd > 14) continue;
            if (dd < 3) close++;
            if (dd < 7) sectors[(int)((Math.Atan2(dz, dx) + Math.PI) / (Math.PI * 2) * 8) % 8] = true;
            double w = (e.Boss ? 0.8 : e.Elite ? 2.2 : 1) * Math.Max(0, 7 - dd) / 7;
            rx += dx / dd * w; rz += dz / dd * w;
            if (e.State is EnemyState.Windup or EnemyState.Lunging && dd < 6) { rx += -dz / dd * 2.5; rz += dx / dd * 2.5; }
        }
        int ring = sectors.Count(s => s);
        foreach (var zn in b.Zones.Living())
        {
            if (zn.Owner is Side.Player or Side.Ally) continue;
            double dx = p.X - zn.X, dz = p.Z - zn.Z, dd = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            if (dd < zn.Radius + 0.8) { rx += dx / dd * 3; rz += dz / dd * 3; }
        }
        orbit += dt * 0.32;
        double tx = home.X + Math.Cos(orbit) * home.R * 0.6, tz = home.Z + Math.Sin(orbit) * home.R * 0.6;
        if (close == 0 && p.Hp > b.MaxHp * 0.4)
        {
            double best = 9;
            foreach (var k in b.Pickups.Living())
            {
                double dd = Math.Sqrt((k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z));
                if (dd < best && Math.Sqrt((k.X - home.X) * (k.X - home.X) + (k.Z - home.Z) * (k.Z - home.Z)) < home.R * 1.4) { best = dd; tx = k.X; tz = k.Z; }
            }
        }
        double mx = (tx - p.X) * 0.25 + rx * 1.6, mz = (tz - p.Z) * 0.25 + rz * 1.6;
        double hd = Math.Sqrt((p.X - home.X) * (p.X - home.X) + (p.Z - home.Z) * (p.Z - home.Z));
        if (hd > home.R * 1.5) { mx += (home.X - p.X) / hd * 2; mz += (home.Z - p.Z) / hd * 2; }
        if (boss != null) BossSense.Steer(b, boss, true, 5, ref mx, ref mz);
        Steer(dt, mx, mz, p, tx, tz);
        dashT -= dt; abilityT -= dt; drinkT -= dt;
        if ((ring >= 6 || close >= 4) && dashT <= 0 && p.DashCharges > 0) { Press(Act.Dash); dashT = 0.8; }
        if (close >= 3 && abilityT <= 0) { Press(Act.Ability); abilityT = 1.5; }
        if (p.Hp < b.MaxHp * 0.33 && drinkT <= 0) { Controls.Instance.Press(Act.Ultimate); drinkT = 1.5; }
    }

    /// <summary>Go that way; wedged on something, sidestep for a moment.</summary>
    void Steer(double dt, double mx, double mz, PlayerState p, double tx, double tz)
    {
        stuckT += dt;
        if (stuckT > 2.5)
        {
            if (Math.Sqrt((p.X - lastX) * (p.X - lastX) + (p.Z - lastZ) * (p.Z - lastZ)) < 0.8 && Math.Sqrt((tx - p.X) * (tx - p.X) + (tz - p.Z) * (tz - p.Z)) > 2) { sideT = 1.3; side = -side; }
            stuckT = 0; lastX = p.X; lastZ = p.Z;
        }
        if (sideT > 0)
        {
            sideT -= dt;
            double l = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz)), ox = mx / l, oz = mz / l;
            mx = ox - oz * 1.5 * side; mz = oz + ox * 1.5 * side;
        }
        double m = Math.Sqrt(mx * mx + mz * mz);
        Move = m > 0.3 ? (mx / m, mz / m) : (0, 0);
    }
}
