using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* Ledge kills (the owner, 15 Nov 2026: "I see enemies being knocked off the edge in this dungeon testing. thats AWESOME. that
 * should make them die, with any loot they would have dropped spawning up near the ledge. it cannot kill elites or bosses (they
 * will just get knocked to the ledge)").
 *
 * The ground's end is a collider flagged Drop (a dungeon's wall boxes, MapGen) or Gap (a crack, a sinkhole). A normal foe whose
 * FORCED move (every knockback, pull, haul and shove is a slide of its Kbx/Kbz, Ai.Update, or a direct Shove) carries its centre
 * over such a piece dies of it: a real kill (credit, experience, on-kill effects, pack and objective counts: KillEnemy as if she
 * had cut it down), its loot rolled as normal and laid on open ground at the ledge nearest where it went over, spread so the drops
 * do not stack. An elite, a miniboss, a boss and anything a run cannot finish without (a scripted or quest foe, a goal) are never
 * taken over: the slide stops against the piece as every slide has (at the brink, on the ground), and the view is told (Ev.Brink).
 * A foe's own movement (a walk, a charge, a lunge, a leap, a burrow) is not a forced move and never takes it over; a flier
 * (EnemyDef.Flies) has no ground to fall from. She cannot fall: her moves are resolved against every piece, always.
 *
 * Deterministic: no random draws of its own (the pickups' own scatter draws as ever). */
public sealed partial class Battle
{
    /// <summary>The rule is on (a harness can turn it off to measure what it changes).</summary>
    public bool LedgeKills = true;
    /// <summary>Foes that went over an edge and died of it, this fight.</summary>
    public int LedgeKillCount;
    /// <summary>A slide's remaining length is |Kb| / 9 (knockback settles at e^-9t); the look-ahead takes this share of it, so a foe
    /// the test calls over really crosses.</summary>
    const double SlideShare = 0.92;

    /// <summary>The foe whose death is laying its loot now (SpawnPickup puts each drop on ground at the ledge), and the spots taken.</summary>
    Enemy? ledgeLoot;
    readonly List<(double X, double Z)> ledgeUsed = new();

    /// <summary>May a forced move take this foe over an edge? A normal one only: hostile, not an elite, miniboss or boss, not
    /// scripted, a goal, named for a quest, a reflection or a flier, and on its feet (not rising or underground).</summary>
    public bool MayFall(Enemy e) =>
        LedgeKills && Collision != null && e.Disposition == Disposition.Hostile && !e.Elite && !e.Boss && !e.Scripted && !e.Goal && !e.Decoy
        && e.Tag == null && !e.Def.Elite && !e.Def.Boss && !e.Def.Miniboss && !e.Def.Flies && e.Def.Behavior is not (Behavior.Boss or Behavior.Stationary)
        && e.State is not (EnemyState.Rising or EnemyState.Burrowed or EnemyState.Surfacing or EnemyState.Dying or EnemyState.Dead);

    /// <summary>One tick of a foe's knockback slide (Ai.Update): looks ahead along what is left of it, lets a foe that is going over
    /// slide on to the edge, and kills it as its centre crosses. True if it fell (nothing else of its step runs).</summary>
    internal bool SlideStep(Enemy e, double dt)
    {
        var col = Collision;
        if (!e.Edge)
        {
            double rx = e.Kbx / 9 * SlideShare, rz = e.Kbz / 9 * SlideShare;
            if (rx * rx + rz * rz > 1e-4 && col.EdgeAhead(e.X, e.Z, rx, rz, CollisionWorld.WallRadius(e.Radius), out double cx, out double cz))
            {
                if (MayFall(e)) { e.Edge = true; e.FellX = cx; e.FellZ = cz; }
                else { e.AtBrink = true; double rl = Math.Sqrt(rx * rx + rz * rz); e.FellDx = rx / rl; e.FellDz = rz / rl; }
            }
        }
        col.IgnoreDrops = e.Edge;
        e.X += e.Kbx * dt;
        e.Z += e.Kbz * dt;
        // Knocked into a wall, it stops at the wall (a scripted boss's own step never resolved it, and Grimtunnel was knocked out
        // through the shut gate behind her, where she could not reach him). A foe going over meets no wall but the ground's own props.
        col.Resolve(ref e.X, ref e.Z, e.Radius);
        if (e.Edge && col.InDrop(e.X, e.Z))
        {
            double d = Math.Sqrt(e.Kbx * e.Kbx + e.Kbz * e.Kbz);
            FallOver(e, d > 1e-6 ? e.Kbx / d : 0, d > 1e-6 ? e.Kbz / d : 1);
            return true;
        }
        double k = Math.Exp(-dt * 9);
        e.Kbx *= k; e.Kbz *= k;
        if (Math.Abs(e.Kbx) + Math.Abs(e.Kbz) < 0.05)
        {
            e.Kbx = e.Kbz = 0;
            e.Edge = false;
            if (e.AtBrink)
            {
                e.AtBrink = false;
                if (e.State != EnemyState.Dying) Events.Emit(new Ev.Brink { X = e.X, Z = e.Z, Dx = e.FellDx, Dz = e.FellDz, Enemy = e.Id, Boss = e.Boss });
            }
        }
        return false;
    }

    /// <summary>A direct forced move (a shove, a drag) to (nx, nz): a normal foe it carries over an edge falls; any other is
    /// stopped by the walls as it was.</summary>
    public void ForceTo(Enemy e, double nx, double nz, string? by = null)
    {
        double dx = nx - e.X, dz = nz - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        e.KbBy = by ?? credit;
        if (d > 1e-6 && MayFall(e) && Collision.EdgeAhead(e.X, e.Z, dx, dz, CollisionWorld.WallRadius(e.Radius), out double cx, out double cz))
        {
            e.X = cx; e.Z = cz;
            e.Kbx = e.Kbz = 0;
            FallOver(e, dx / d, dz / d);
            return;
        }
        e.X = nx; e.Z = nz;
        Collision.Resolve(ref e.X, ref e.Z, e.Radius);
    }

    /// <summary>It went over: dead of it, credited, its loot at the ledge (KillEnemy lays it there), and the view told.</summary>
    void FallOver(Enemy e, double ux, double uz)
    {
        e.Edge = false;
        e.Fell = true;
        e.FellX = e.X; e.FellZ = e.Z; e.FellDx = ux; e.FellDz = uz;
        (e.LedgeX, e.LedgeZ) = LedgePoint(e.X, e.Z, ux, uz);
        // It slides on over the drop as it dies (Ai's dying branch), a little further than the edge.
        if (e.Kbx == 0 && e.Kbz == 0) { e.Kbx = ux * 2.5; e.Kbz = uz * 2.5; }
        LedgeKillCount++;
        Events.Emit(new Ev.Fell { X = e.X, Z = e.Z, Dx = ux, Dz = uz, LedgeX = e.LedgeX, LedgeZ = e.LedgeZ, Enemy = e.Id, Def = e.Def.Id, Scale = e.Def.Scale ?? 1 });
        e.LastDx = ux; e.LastDz = uz;
        // The kill is the forced move's: the skill (or the Flare, or the trigger) that gave it, for its kill, its on-kill effects
        // and the life the fall took (the shares of damage and kills stay true).
        var weapon = WeaponById(e.KbBy);
        string by = e.KbBy ?? "other";
        double left = Math.Max(0, e.Hp);
        DamageBy[by] = DamageBy.GetValueOrDefault(by) + left;
        if (weapon != null) weapon.DamageDealt += left;
        var was = credit;
        credit = e.KbBy ?? credit;
        KillEnemy(e, true, weapon);
        credit = was;
    }

    /// <summary>The ledge: open ground, back along the way it went from where its centre crossed (0.45 m of clear ground round the
    /// point, so a drop lying there is taken by her standing at the brink). Failing that, the nearest open ground.</summary>
    (double X, double Z) LedgePoint(double cx, double cz, double ux, double uz)
    {
        for (double back = 0.1; back <= 5; back += 0.1)
        {
            double px = cx - ux * back, pz = cz - uz * back;
            if (OpenGround(px, pz)) return (px, pz);
        }
        return NearestOpen(cx, cz, 0, 0.45);
    }

    bool OpenGround(double x, double z) => !Collision.InDrop(x, z) && !Collision.Blocked(x, z, 0.45) && Math.Abs(x) < Collision.Bound && Math.Abs(z) < Collision.Bound;

    (double X, double Z) NearestOpen(double x, double z, double avoidR, double apart)
    {
        for (int ring = 0; ring <= 40; ring++)
            for (int k = 0; k < (ring == 0 ? 1 : 12); k++)
            {
                double a = k * Math.Tau / 12 + ring * 0.37, px = x + Math.Cos(a) * ring * 0.3, pz = z + Math.Sin(a) * ring * 0.3;
                if (!OpenGround(px, pz)) continue;
                bool clear = true;
                foreach (var u in ledgeUsed) if ((u.X - px) * (u.X - px) + (u.Z - pz) * (u.Z - pz) < apart * apart * (avoidR > 0 ? 1 : 0)) { clear = false; break; }
                if (clear) return (px, pz);
            }
        return (x, z);
    }

    /// <summary>The next spot a fallen foe's loot lies on: the ledge itself, then open ground round it, each clear of the others
    /// (0.5 m apart).</summary>
    (double X, double Z) LedgeSpot(Enemy e)
    {
        const double Apart = 0.5;
        (double X, double Z) at = (e.LedgeX, e.LedgeZ);
        if (ledgeUsed.Count > 0) at = NearestOpen(e.LedgeX, e.LedgeZ, 1, Apart);
        ledgeUsed.Add(at);
        return at;
    }
}
