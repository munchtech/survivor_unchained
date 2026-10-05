using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// What anyone does after dying to a boss once ("a relaxed human does each of
/// these after one death"): reads its marked blows by their shape and walks to
/// where it will not be when they land, dashing through when walking will not
/// do; leaves ground about to close; stands in ground marked for standing (the
/// Barrow Lord laid down); runs down the thief who took a weapon; closes on
/// Grimtunnel while a lamp flares.
///
/// One sense for every pair of hands that is not a player's: the balance
/// harness's bots (without it a sweep measures their ignorance of the fight,
/// not the fight) and the game's autopilot (pictures of a fight fought).
/// </summary>
public static class BossSense
{
    /// <summary>How long a marked blow is on the ground before the hands answer it:
    /// a relaxed player's reaction, and a practised one's.</summary>
    public const double ReactPlain = 0.45, ReactDeft = 0.25;
    /// <summary>The share of marked blows noticed at all: in a crowd at the half hour a
    /// relaxed player misses one in five, a practised one one in twenty.</summary>
    public const double NoticePlain = 0.8, NoticeDeft = 0.95;

    /// <summary>Turns the way the hands were going (mx, mz) into the way a player who
    /// knows the boss goes, and dashes when only a dash will do. `reach`: how close
    /// its weapons want to be.</summary>
    /// <param name="aim">A story night's stage: where it wants her (a fire to light, a foe to find),
    /// gone to when nothing of the boss's asks otherwise.</param>
    public static void Steer(Battle b, ArenaBoss? boss, bool deft, double reach, ref double mx, ref double mz, (double X, double Z)? aim = null)
    {
        var p = b.Player;
        // Where it wants to be, by the fight's own question.
        (double X, double Z, double Near)? goal = null;
        switch (boss)
        {
            case RedHand { Thief: { Alive: true } thief } when thief.State != EnemyState.Dying:
                goal = (thief.X, thief.Z, Math.Max(1.5, Math.Min(reach * 0.6, 5)));
                break;
            case BarrowLord { Laying: true } bl:
                goal = (bl.E.X, bl.E.Z, 1.6);
                break;
            case Grimtunnel { Flaring: >= 0 } g when g.E.Alive:
                goal = (g.E.X, g.E.Z, Math.Max(2.2, Math.Min(reach * 0.7, 6)));
                break;
            // Caged: to the post furthest from the door (and from him at it), and stand by it till it gives.
            case Redcowl { InCage: true } rc:
            {
                var (cx, cz) = rc.CageAt;
                var (doorX, doorZ) = rc.Door;
                var post = rc.Posts.Where(q => !q.Broken).OrderByDescending(q => Dist(q.X, q.Z, doorX, doorZ)).FirstOrDefault();
                if (post != null) goal = (post.X + (cx - post.X) * 0.3, post.Z + (cz - post.Z) * 0.3, 0.4);
                break;
            }
            // The cold closing in: into a fed fire's light, or to the nearest deadfall to light it.
            case Greymuzzle { Cold: true } gm:
            {
                var lit = gm.Fires.Where(f => f.Burning).OrderBy(f => Dist(f.X, f.Z, p.X, p.Z)).FirstOrDefault();
                var any = gm.Fires.Where(f => gm.Inside(f.X, f.Z, 0)).OrderBy(f => Dist(f.X, f.Z, p.X, p.Z)).FirstOrDefault();
                if (lit != null) goal = (lit.X, lit.Z, lit.Reach * 0.6);
                else if (any != null) goal = (any.X, any.Z, 1.0);
                break;
            }
        }
        foreach (var bl in b.Blows)
            if (bl.Kind == TelegraphKind.Safe && bl.Shape == TelegraphShape.Circle) { goal ??= (bl.X, bl.Z, bl.Radius * 0.5); break; }
        if (goal == null && aim is var (ax, az) && b.Blows.Count == 0) goal = (ax, az, 1.2);
        if (goal is var (gx, gz, gn))
        {
            double d = Dist(gx, gz, p.X, p.Z);
            if (d > gn) { mx = (gx - p.X) / d; mz = (gz - p.Z) / d; }
            else { mx = 0; mz = 0; }
        }

        // A living wall (the Pack's ring): along it rather than into it.
        if (boss is Greymuzzle wall && (mx != 0 || mz != 0) && !wall.Inside(p.X + mx * 1.5, p.Z + mz * 1.5, 1.0))
        {
            var (cx, cz) = wall.Middle;
            double rx = cx - p.X, rz = cz - p.Z, rl = Math.Max(0.01, Math.Sqrt(rx * rx + rz * rz));
            double tx = -rz / rl, tz = rx / rl;
            if (tx * mx + tz * mz < 0) { tx = -tx; tz = -tz; }
            mx = tx * 0.7 + rx / rl * 0.7; mz = tz * 0.7 + rz / rl * 0.7;
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
            // A living wall (the Pack's ring) is a wall: a step out of it is a shove.
            if (boss is Greymuzzle ring && !ring.Inside(p.X + cx * 1.2, p.Z + cz * 1.2, 1.0)) score -= 6;
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
            if (boss is Greymuzzle ring && !ring.Inside(ex, ez, 1.0)) continue;
            double hurt = Caught(b, ex, ez, 0, 0, deft, out _);
            if (hurt < dashBest) { dashBest = hurt; dx = cx; dz = cz; }
        }
        if (dashBest <= 0 && soonest < 0.6) { b.Dash(dx, dz); mx = dx; mz = dz; }
        else if (soonest < Abilities.Dash.Iframes - 0.05) b.Dash(dx == 0 && dz == 0 ? mx : dx, dx == 0 && dz == 0 ? mz : dz);
    }

    /// <summary>A blow the hands answer: one that hurts, takes or traps (not the safe
    /// ground, nor a cage's standing posts), marked long enough to have been seen, and
    /// noticed at all (decided by the blow itself, so a run replays).</summary>
    public static bool Threat(Battle.EnemyBlow bl, bool deft) =>
        (bl.Kind == TelegraphKind.Blow || (bl.Kind == TelegraphKind.Wall && bl.Shape == TelegraphShape.Circle)) &&
        bl.Delay - bl.T >= Math.Min(deft ? ReactDeft : ReactPlain, bl.Delay * 0.6) &&
        Noticed(bl) < (deft ? NoticeDeft : NoticePlain);

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
    /// (each scored by what it does), and how soon the first lands.</summary>
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
