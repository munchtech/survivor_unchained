using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>A plain-minded survivor's hands (the tests' ArenaPlay bot, kept
/// as it was so the numbers mean the same): give ground when pressed, go to
/// the fight or the ember lying about when it is quiet, keep off the arena's
/// edge, dash out of a crush, use the art on a crowd, drink when low.</summary>
public static class Pilot
{
    /// <summary>How far its weapons reach, the median of them: a build of blades
    /// and rings fights close, one of bolts and arrows from further off.</summary>
    public static double Reach(Battle b)
    {
        if (b.Weapons.Count == 0) return 10;
        var r = b.Weapons.Select(w => w.Behavior switch
        {
            Content.WeaponBehavior.Slash or Content.WeaponBehavior.Palm => (w.Num(s => s.Reach) ?? 2.6) * Math.Sqrt(b.Stats.Get(Stat.Area)),
            Content.WeaponBehavior.Nova => w.Num(s => s.Radius) ?? 3.5,
            Content.WeaponBehavior.Orbit => (w.Num(s => s.OrbitRadius) ?? 2) + 0.5,
            Content.WeaponBehavior.Zone when !w.Flag(s => s.AtTarget) => w.Num(s => s.Radius) ?? 3,
            _ => w.Num(s => s.Range) ?? 12,
        }).OrderBy(x => x).ToList();
        return r[(r.Count - 1) / 2];
    }

    /// <param name="onward">On a map: where the way goes on. Resting packs are left to rest, what
    /// lies about is picked up, and with nothing roused near, the hands walk on.</param>
    /// <param name="goal">A story night's stage: where it wants her (a fire to light, a foe to find). With no
    /// crush round her, the hands go there.</param>
    /// <param name="strikes">Read the crowd's own marked circles too (a story night's way in: its named foes'
    /// slams are its lessons, and a relaxed player steps out of a brute's marked circle as of a boss's).</param>
    /// <param name="first">The boss met for the first time (BossSense.Meeting): its new moves answered less.</param>
    public static (double X, double Z) Steer(Battle b, bool deft = false, ArenaBoss? boss = null, (double X, double Z)? onward = null, (double X, double Z)? goal = null, bool naive = false, bool strikes = false, BossSense.Meeting? first = null)
    {
        var p = b.Player;
        double mx, mz;
        // Close fighters stand in the press and give ground only to a crush.
        double reach = Reach(b);
        bool close = reach < 4.5;
        var press = b.HostilesInRadius(p.X, p.Z, close ? 2.0 : 3.4);
        int crowded = close ? 4 : 2;
        double engage = close ? Math.Max(1.6, reach * 0.7) : 6;
        Enemy? nearest = null;
        double nd = double.MaxValue;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            if (onward != null && (e.Wake > 0 && !e.Roused || e.State == EnemyState.Burrowed)) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }
        }
        Pickup? stone = null;
        double sd = 144;
        foreach (var k in b.Pickups.Items)
        {
            if (!k.Alive || !(k.Kind == PickupKind.Ember || onward != null && k.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Gold or PickupKind.Chest)) continue;
            double d = (k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z);
            if (d < sd) { sd = d; stone = k; }
        }
        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        // On a map, one that has wandered far off is not followed into the trees.
        if (onward != null && near > 22) { nearest = null; near = double.MaxValue; }
        // A champion or the boss at arm's length: give ground round it, as anyone does who
        // has been hit by one twice (a ranged build kites it; a blade fights it only with
        // the health to). Without this the bot stood in a boss's combo and fell.
        Enemy? big = null;
        double bigD = close ? 2.2 : 4.5;
        foreach (var e in b.HostilesInRadius(p.X, p.Z, bigD))
            if ((e.Boss || e.Elite) && (!close || p.Hp < b.MaxHp * 0.5)) { big = e; break; }
        if (big != null)
        {
            double cx = big.X - p.X, cz = big.Z - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            mx = -cx / cl * 0.8 - cz / cl * 0.6; mz = -cz / cl * 0.8 + cx / cl * 0.6;
        }
        else if (press.Count >= crowded)
        {
            double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            // Away and round: a quarter turn off straight back.
            mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
        }
        // The stage's goal when nothing is at her throat: a player with a thing to do does it, and lets
        // the weapons fire on the way (a fire takes two seconds of standing to light).
        else if (goal is var (gx, gz))
        {
            if (Dist(gx, gz, p.X, p.Z) > 1.2) { mx = gx - p.X; mz = gz - p.Z; } else { mx = 0; mz = 0; }
        }
        else if (stone != null && near > engage + 1) { mx = stone.X - p.X; mz = stone.Z - p.Z; }
        else if (nearest != null && near > engage) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
        else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
        else if (onward is var (ox, oz)) { mx = ox - p.X; mz = oz - p.Z; }
        else { mx = -p.X; mz = -p.Z; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60 && onward == null && goal == null) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
        if (deft) Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius))
        {
            // On a story night's way: the nearest turn that is clear, either hand, or straight on and
            // let the wall slide her (a quarter turn left, always, pressed her into a wall's corner).
            if (goal != null) (mx, mz) = Clearest(b, mx, mz);
            else (mx, mz) = (-mz, mx);
        }
        // The boss's own fight, read last: it overrules the crowd.
        // Naive hands read only a boss's marks: the way in's (a drive's lane) they walk into, as a first-timer does.
        double hx = mx, hz = mz;
        if (ReadsBosses && (boss != null || (b.Blows.Count > 0 || strikes && b.EnemyStrikes().Any()) && !naive)) Boss(b, boss, deft, ref mx, ref mz, goal, strikes && !naive, first);
        if (Debug) Console.Error.WriteLine($"   PILOT near {(nearest == null ? "-" : $"{nearest.Def.Id} {near:0.0}")} big {big != null} press {press.Count} goal {goal} stone {stone != null} hands ({hx:0.00},{hz:0.00}) after boss ({mx:0.00},{mz:0.00})");
        double ml = Math.Sqrt(mx * mx + mz * mz);
        if (ml > 1e-6) { mx /= ml; mz /= ml; }
        return (mx, mz);
    }

    /// <summary>The hands that are not the feet: a dash out of a crush, the art
    /// on a crowd, a draught when low.</summary>
    /// <returns>Whether a draught was drunk.</returns>
    public static bool Act(Battle b, Journey j, double mx, double mz)
    {
        var p = b.Player;
        // A champion winding up a lunge close by: dash across its line, as anyone with a dash learns to.
        // (Not a boss: its blows are marked on the ground, and Boss reads them by their shape.)
        if (p.DashCharges > 0)
            foreach (var e in b.HostilesInRadius(p.X, p.Z, 7))
                if (e.Elite && (!e.Boss || !ReadsBosses) && e.State == EnemyState.Windup)
                {
                    double dx = p.X - e.X, dz = p.Z - e.Z, l = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
                    b.Dash(-dz / l, dx / l);
                    break;
                }
        if (p.DashCharges > 0 && b.HostilesInRadius(p.X, p.Z, 2.2).Count >= 3) b.Dash(mx, mz);
        if (p.AbilityCd <= 0 && b.HostilesInRadius(p.X, p.Z, 6).Count >= 5) b.UseAbility(mx, mz);
        if (p.Hp >= b.MaxHp * 0.33) return false;
        double before = p.Hp;
        j.Quaff(b);
        return p.Hp > before;
    }

    /// <summary>What a player who knows the fight does over the plain hands'
    /// choice, the worst danger first (from the balance lab's deft bot, which
    /// the tests' ArenaPlay shares): off the line of a marked lunge, dashing
    /// across it if late; out from under a lobbed pot and off burning ground;
    /// and, with nothing pressing and no ember near, in on the nearest thrower.</summary>
    public static void Deft(Battle b, bool busy, ref double mx, ref double mz)
    {
        var p = b.Player;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Windup || e.Disposition != Disposition.Hostile) continue;
            var lunge = e.Def.Charge ?? e.Def.Lunge;
            if (lunge == null) continue;
            double reach = lunge.Speed * lunge.Time + e.Radius + 1;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < -1 || along > reach || Math.Abs(across) > e.Radius * 1.1 + p.Radius + 0.9) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            if (e.StateT < 0.3 && p.DashCharges > 0) b.Dash(mx, mz);
            return;
        }
        // A crossbow knelt and aiming down its fixed line: off the line, as from a lunge.
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Casting || e.Cast != CastKind.Aim || e.Disposition != Disposition.Hostile) continue;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < 0 || along > e.AimReach + 3 || Math.Abs(across) > 1.2 + along * 0.2) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            return;
        }
        foreach (var pr in b.Projectiles.Living())
        {
            if (!pr.Lob || pr.Owner != Side.Enemy) continue;
            double d = Dist(pr.LandX, pr.LandZ, p.X, p.Z);
            if (d < 2.2) { mx = (p.X - pr.LandX) / Math.Max(0.1, d); mz = (p.Z - pr.LandZ) / Math.Max(0.1, d); return; }
        }
        foreach (var z in b.Zones.Living())
        {
            if (z.Owner is not (Side.Enemy or Side.World)) continue;
            double d = Dist(z.X, z.Z, p.X, p.Z);
            if (d < z.Radius + p.Radius) { mx = (p.X - z.X) / Math.Max(0.1, d); mz = (p.Z - z.Z) / Math.Max(0.1, d); return; }
        }
        if (busy) return;
        Enemy? shooter = null;
        double sd = 11;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying || e.Wake > 0 && !e.Roused) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < sd) { sd = d; shooter = e; }
        }
        if (shooter != null && sd > 1.8 && b.HostilesInRadius(p.X, p.Z, 4.5).Count < 3) { mx = shooter.X - p.X; mz = shooter.Z - p.Z; return; }
        // The Kindling's core: stood beside, as anyone does who has read what breaking it gives.
        foreach (var e in b.Enemies.Living())
            if (e.Def.Id == "ember_core" && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) > 2.5) { mx = e.X - p.X; mz = e.Z - p.Z; return; }
    }

    /// <summary>A trace of the hands' choices, each step (one traced run, single-threaded).</summary>
    [ThreadStatic] public static bool Debug;

    /// <summary>Off (--bossread 0) for the numbers of the hands before they knew the bosses.</summary>
    public static bool ReadsBosses = true;

    /// <summary>The boss read as a player who has died to it once (Play/Bosses/BossSense.cs,
    /// shared with the game's autopilot).</summary>
    public static void Boss(Battle b, ArenaBoss? boss, bool deft, ref double mx, ref double mz, (double X, double Z)? goal = null, bool strikes = false, BossSense.Meeting? first = null) =>
        BossSense.Steer(b, boss, deft, Reach(b), ref mx, ref mz, goal, strikes, first);

    /// <summary>The way on nearest the one wanted that a step down it is clear; straight on if none is.</summary>
    static (double X, double Z) Clearest(Battle b, double mx, double mz)
    {
        var p = b.Player;
        double ml = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz));
        mx /= ml; mz /= ml;
        foreach (double deg in (double[])[30, -30, 60, -60, 90, -90])
        {
            double a = deg * Math.PI / 180, c = Math.Cos(a), s = Math.Sin(a);
            double rx = mx * c - mz * s, rz = mx * s + mz * c;
            if (!b.Collision.Blocked(p.X + rx * 0.25, p.Z + rz * 0.25, p.Radius * 0.9)) return (rx, rz);
        }
        return (mx, mz);
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
