using System;
using System.Linq;
using SurvivorUnchained.Content;
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

    public static (double X, double Z) Steer(Battle b, bool deft = false, ArenaBoss? boss = null)
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
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }
        }
        Pickup? stone = null;
        double sd = 144;
        foreach (var k in b.Pickups.Items)
        {
            if (!k.Alive || k.Kind != PickupKind.Ember) continue;
            double d = (k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z);
            if (d < sd) { sd = d; stone = k; }
        }
        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
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
        else if (stone != null && near > engage + 1) { mx = stone.X - p.X; mz = stone.Z - p.Z; }
        else if (nearest != null && near > engage) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
        else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
        else { mx = -p.X; mz = -p.Z; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
        if (deft) Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) (mx, mz) = (-mz, mx);
        // The boss's own fight, read last: it overrules the crowd.
        if (ReadsBosses && (boss != null || b.Blows.Count > 0)) Boss(b, boss, deft, ref mx, ref mz);
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
            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < sd) { sd = d; shooter = e; }
        }
        if (shooter != null && sd > 1.8 && b.HostilesInRadius(p.X, p.Z, 4.5).Count < 3) { mx = shooter.X - p.X; mz = shooter.Z - p.Z; }
    }

    /// <summary>Off (--bossread 0) for the numbers of the hands before they knew the bosses.</summary>
    public static bool ReadsBosses = true;

    /// <summary>How long a marked blow is on the ground before the hands answer it:
    /// a relaxed player's reaction, and a practised one's.</summary>
    public const double ReactPlain = 0.45, ReactDeft = 0.25;

    /// <summary>What anyone does after dying to a boss once (docs/handoff/combat.md:
    /// "a relaxed human does each of these after one death"): reads its marked blows
    /// by their shape and walks to where it will not be when they land, dashing
    /// through when walking will not do; leaves ground about to close; stands in
    /// ground marked for standing (the Barrow Lord laid down); runs down the thief
    /// who took a weapon; closes on Grimtunnel while a lamp flares. Without it a
    /// sweep measures the bot's ignorance of the fight, not the fight.</summary>
    public static void Boss(Battle b, ArenaBoss? boss, bool deft, ref double mx, ref double mz)
    {
        var p = b.Player;
        // Where it wants to be, by the fight's own question.
        (double X, double Z, double Near)? goal = null;
        switch (boss)
        {
            case RedHand { Thief: { Alive: true } thief } when thief.State != EnemyState.Dying:
                goal = (thief.X, thief.Z, Math.Max(1.5, Math.Min(Reach(b) * 0.6, 5)));
                break;
            case BarrowLord { Laying: true } bl:
                goal = (bl.E.X, bl.E.Z, 1.6);
                break;
            case Grimtunnel { Flaring: >= 0 } g when g.E.Alive:
                goal = (g.E.X, g.E.Z, Math.Max(2.2, Math.Min(Reach(b) * 0.7, 6)));
                break;
        }
        foreach (var bl in b.Blows)
            if (bl.Kind == TelegraphKind.Safe && bl.Shape == TelegraphShape.Circle) { goal ??= (bl.X, bl.Z, bl.Radius * 0.5); break; }
        if (goal is var (gx, gz, gn))
        {
            double d = Dist(gx, gz, p.X, p.Z);
            if (d > gn) { mx = (gx - p.X) / d; mz = (gz - p.Z) / d; }
            else { mx = 0; mz = 0; }
        }

        // The blows it has seen long enough to answer, and the ground about to close.
        int n = 0;
        foreach (var bl in b.Blows)
            if (Threat(bl, deft)) n++;
        if (n == 0) return;
        double speed = Math.Max(1, b.Stats.Get(Stat.MoveSpeed) * p.SlowF);
        // Candidates: the way it was going, standing, and sixteen bearings.
        double want = Math.Sqrt(mx * mx + mz * mz);
        double bestScore = double.MinValue, bx = mx, bz = mz;
        double soonest = double.MaxValue;
        for (int c = -2; c < 16; c++)
        {
            double cx, cz;
            if (c == -2) { cx = want > 1e-6 ? mx / want : 0; cz = want > 1e-6 ? mz / want : 0; }
            else if (c == -1) { cx = 0; cz = 0; }
            else { cx = Math.Cos(c * Math.PI / 8); cz = Math.Sin(c * Math.PI / 8); }
            double score = want > 1e-6 ? (cx * mx + cz * mz) / want : 0;
            if ((cx != 0 || cz != 0) && b.Collision.Blocked(p.X + cx * 0.8, p.Z + cz * 0.8, p.Radius)) score -= 5;
            double hurt = Caught(b, p.X, p.Z, cx * speed, cz * speed, deft, out double first);
            score -= hurt;
            if (score > bestScore) { bestScore = score; bx = cx; bz = cz; soonest = hurt > 0 ? first : double.MaxValue; }
        }
        mx = bx; mz = bz;
        // Walking will not clear it: a dash, timed so its moment of grace covers the blow
        // (or at once, for ground that closes: a cage is left, not survived).
        if (soonest == double.MaxValue || p.DashCharges <= 0) return;
        double dashBest = double.MaxValue, dx = 0, dz = 0;
        for (int c = 0; c < 16; c++)
        {
            double cx = Math.Cos(c * Math.PI / 8), cz = Math.Sin(c * Math.PI / 8);
            double ex = p.X + cx * Abilities.Dash.Distance, ez = p.Z + cz * Abilities.Dash.Distance;
            if (b.InBounds != null && !b.InBounds(ex, ez)) continue;
            double hurt = Caught(b, ex, ez, 0, 0, deft, out _);
            if (hurt < dashBest) { dashBest = hurt; dx = cx; dz = cz; }
        }
        if (dashBest <= 0 && soonest < 0.6) { b.Dash(dx, dz); mx = dx; mz = dz; }
        else if (soonest < Abilities.Dash.Iframes - 0.05) b.Dash(dx == 0 && dz == 0 ? mx : dx, dx == 0 && dz == 0 ? mz : dz);
    }

    /// <summary>A blow the hands answer: one that hurts, takes or traps (not the safe
    /// ground, nor a cage's standing posts), marked long enough to have been seen, and
    /// noticed at all: in a crowd at the half hour a relaxed player misses one in five,
    /// a practised one one in twenty (decided by the blow itself, so a run replays).</summary>
    static bool Threat(Battle.EnemyBlow bl, bool deft) =>
        (bl.Kind == TelegraphKind.Blow || (bl.Kind == TelegraphKind.Wall && bl.Shape == TelegraphShape.Circle)) &&
        bl.Delay - bl.T >= Math.Min(deft ? ReactDeft : ReactPlain, bl.Delay * 0.6) &&
        Noticed(bl) < (deft ? NoticeDeft : NoticePlain);

    public const double NoticePlain = 0.8, NoticeDeft = 0.95;

    /// <summary>A number in [0, 1) that is the blow's own (where, when and what it is).</summary>
    static double Noticed(Battle.EnemyBlow bl)
    {
        unchecked
        {
            uint h = (uint)(long)Math.Round(bl.X * 97) * 73856093u ^ (uint)(long)Math.Round(bl.Z * 89) * 19349663u
                ^ (uint)(long)Math.Round(bl.Delay * 1000) * 83492791u ^ (uint)bl.Shape * 2654435761u ^ (uint)(long)Math.Round(bl.Radius * 31) * 40503u;
            h ^= h >> 13; h *= 0x5bd1e995; h ^= h >> 15;
            return (h % 10000) / 10000.0;
        }
    }

    /// <summary>How badly walking at (vx, vz) from (x, z) is caught by the blows marked
    /// (each scored by when it lands and what it does), and how soon the first lands.</summary>
    static double Caught(Battle b, double x, double z, double vx, double vz, bool deft, out double first)
    {
        double sum = 0;
        first = double.MaxValue;
        var p = b.Player;
        foreach (var bl in b.Blows)
        {
            if (!Threat(bl, deft)) continue;
            double t = Math.Min(bl.T, 1.2);
            // A little margin: the edge of a mark is where a player stops, not where they stand.
            if (!bl.Hit(x + vx * t, z + vz * t, p.Radius + 0.5)) continue;
            sum += 10 + bl.Damage / Math.Max(1, b.MaxHp) * 40 + (bl.Kind == TelegraphKind.Wall ? 8 : 0);
            first = Math.Min(first, bl.T);
        }
        return sum;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
