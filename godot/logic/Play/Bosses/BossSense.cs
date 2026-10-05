using System;
using System.Collections.Generic;
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
/// not the fight) and the game's autopilot (pictures of a fight fought). Before
/// it has killed her once, a Meeting says what the hands do not yet know.
/// </summary>
/// <summary>A boss whose ground has a moving edge (the Pack's ring, a floor caving in from the edge): a wall
/// to the hands, a step past it a shove.</summary>
public interface IBound
{
    bool Inside(double x, double z, double margin);
    (double X, double Z) Middle { get; }
}

public static class BossSense
{
    /// <summary>How long a marked blow is on the ground before the hands answer it:
    /// a relaxed player's reaction, and a practised one's.</summary>
    public const double ReactPlain = 0.45, ReactDeft = 0.25;
    /// <summary>The share of marked blows noticed at all: in a crowd at the half hour a
    /// relaxed player misses one in five, a practised one one in twenty.</summary>
    public const double NoticePlain = 0.8, NoticeDeft = 0.95;

    /// <summary>
    /// A first meeting with a boss, before it has killed her: what these hands lack until then. Each of
    /// its named moves is new the first two times it is marked, and a new move is answered half as often
    /// (a lane on the ground is read at once; how far he runs it and when is learned by seeing it land).
    /// Its own answers (a fire's light in the cold, the far post of a cage) wait on the bar's words for a
    /// few seconds' reading. Without this, the boss's first life was measured with hands that had already
    /// died to it once, and a fall at it was decided by the build: the rise changed nothing.
    /// </summary>
    public sealed class Meeting
    {
        /// <summary>How many times a move is new, and how much less often a new one is answered.</summary>
        public const int Lessons = 2;
        public const double NewNotice = 0.5;
        /// <summary>How long the bar's words take to read before its answer is acted on.</summary>
        public const double ReadFor = 3;
        readonly Dictionary<Battle.EnemyBlow, bool> blows = new(ReferenceEqualityComparer.Instance);
        readonly Dictionary<string, int> times = new();
        readonly Dictionary<string, double> since = new();

        /// <summary>The blows marked now, each counted against its move the first time it is seen.</summary>
        public void See(Battle b)
        {
            foreach (var k in blows.Keys.Where(k => !b.Blows.Contains(k)).ToList()) blows.Remove(k);
            foreach (var bl in b.Blows)
            {
                if (blows.ContainsKey(bl) || bl.Label is not { } label || bl.Kind != TelegraphKind.Blow) continue;
                int n = times[label] = times.GetValueOrDefault(label) + 1;
                blows[bl] = n <= Lessons;
            }
        }

        /// <summary>Still new to her when it was marked.</summary>
        public bool New(Battle.EnemyBlow bl) => blows.TryGetValue(bl, out var n) && n;

        /// <summary>A question of the fight's own (the cold, the cage) asked, and not yet asked long enough to
        /// have been read.</summary>
        public bool Reading(string question, bool asked, double now)
        {
            if (!asked) { since.Remove(question); return false; }
            if (!since.TryGetValue(question, out var t)) since[question] = t = now;
            return now - t < ReadFor;
        }
    }

    /// <summary>Turns the way the hands were going (mx, mz) into the way a player who
    /// knows the boss goes, and dashes when only a dash will do. `reach`: how close
    /// its weapons want to be.</summary>
    /// <param name="aim">A story night's stage: where it wants her (a fire to light, a foe to find),
    /// gone to when nothing of the boss's asks otherwise.</param>
    /// <param name="strikes">Read the crowd's own marked circles too (a brute's slam, a burst's fuse): a story
    /// night's way in, where its named foes' marked moves are the lesson. (The table's nights are measured
    /// without, as they always were.)</param>
    /// <param name="first">A first meeting (before it has killed her): new moves answered less, its own answers
    /// read first. Null: the hands know it.</param>
    public static void Steer(Battle b, ArenaBoss? boss, bool deft, double reach, ref double mx, ref double mz, (double X, double Z)? aim = null, bool strikes = false, Meeting? first = null)
    {
        var p = b.Player;
        first?.See(b);
        // Where it wants to be, by the fight's own question (on a first meeting, once the bar has been read).
        (double X, double Z, double Near)? goal = null;
        bool reading = first != null && (first.Reading("cold", boss is Greymuzzle { Cold: true }, b.Time) | first.Reading("cage", boss is Redcowl { InCage: true }, b.Time)
            | first.Reading("barrel", boss is GrimtunnelStory { BarrelStill: true }, b.Time));
        if (!reading) switch (boss)
        {
            // Grimtunnel: in on him while a lamp flares (to break it), then Snib's barrel kicked at him from the
            // side away from him, walked through.
            case GrimtunnelStory { Flaring: >= 0, Under: false } gl when gl.E.Alive:
                goal = (gl.E.X, gl.E.Z, Math.Max(2.2, Math.Min(reach * 0.7, 6)));
                break;
            case GrimtunnelStory { BarrelStill: true, BarrelAt: var (brx, brz), Under: false } gb when gb.E.Alive:
            {
                double ux = brx - gb.E.X, uz = brz - gb.E.Z, ul = Math.Max(0.01, Math.Sqrt(ux * ux + uz * uz));
                ux /= ul; uz /= ul;
                double bhx = brx + ux * 1.4, bhz = brz + uz * 1.4;
                goal = Dist(bhx, bhz, p.X, p.Z) > 0.8 && Dist(brx, brz, p.X, p.Z) > 1.2 ? (bhx, bhz, 0.4) : (brx - ux * 1.5, brz - uz * 1.5, 0.2);
                break;
            }
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

        // A living wall (the Pack's ring): along it rather than into it. (The step looked at is a metre and a
        // half her way: the way given is not always a unit, and a way of thirteen metres toward him beyond the
        // ring read every step as into the wall, and turned her round its middle on the spot.)
        double wl = Math.Sqrt(mx * mx + mz * mz);
        if (boss is IBound wall && wl > 1e-6 && !wall.Inside(p.X + mx / wl * 1.5, p.Z + mz / wl * 1.5, 1.0))
        {
            var (cx, cz) = wall.Middle;
            double rx = cx - p.X, rz = cz - p.Z, rl = Math.Max(0.01, Math.Sqrt(rx * rx + rz * rz));
            double tx = -rz / rl, tz = rx / rl;
            if (tx * mx + tz * mz < 0) { tx = -tx; tz = -tz; }
            mx = tx * 0.7 + rx / rl * 0.7; mz = tz * 0.7 + rz / rl * 0.7;
        }
        // The guard before his den is a wall of the Pack too: round its ends to him, not into it (a shove and a
        // bite each time; once is enough to learn it).
        wl = Math.Sqrt(mx * mx + mz * mz);
        if (boss is Greymuzzle gw && wl > 1e-6)
        {
            var guards = gw.Guarding.ToList();
            double sx = p.X + mx / wl * 1.5, sz = p.Z + mz / wl * 1.5;
            if (guards.Count > 0 && guards.Min(q => Dist(q.X, q.Z, sx, sz)) < 2.6)
            {
                var w = guards.OrderBy(q => Dist(q.X, q.Z, sx, sz)).First();
                double mgx = guards.Average(q => q.X), mgz = guards.Average(q => q.Z);
                double wx = w.X - p.X, wz = w.Z - p.Z, al = Math.Max(0.01, Math.Sqrt(wx * wx + wz * wz));
                double tx = -wz / al, tz = wx / al;
                if (tx * (w.X - mgx) + tz * (w.Z - mgz) < 0) { tx = -tx; tz = -tz; }
                mx = tx; mz = tz;
            }
        }

        // A gap in the ground right ahead (the crack, a sinkhole) with ground past it: over it with a dash.
        double ml = Math.Sqrt(mx * mx + mz * mz);
        if (ml > 1e-6 && p.DashCharges > 0 && p.DashT <= 0)
        {
            double ux = mx / ml, uz = mz / ml;
            double lx = p.X + ux * Abilities.Dash.Distance, lz = p.Z + uz * Abilities.Dash.Distance;
            if (b.Collision.Within(p.X + ux * 0.9, p.Z + uz * 0.9, p.Radius).Any(c => c.Gap)
                && !b.Collision.Blocked(lx, lz, p.Radius) && (b.InBounds == null || b.InBounds(lx, lz)))
                b.Dash(ux, uz);
        }

        // The blows it has seen long enough to answer, and the ground about to close.
        int n = 0;
        foreach (var bl in b.Blows)
            if (Threat(bl, deft, first)) n++;
        if (strikes)
            foreach (var s in b.EnemyStrikes())
                if (Threat(s, deft)) n++;
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
            // A living wall (the Pack's ring, the guard at his den) is a wall: a step into it is a shove.
            if (boss is IBound ring && (!ring.Inside(p.X + cx * 1.2, p.Z + cz * 1.2, 1.0)
                || boss is Greymuzzle gm2 && gm2.Guarding.Any(q => Dist(q.X, q.Z, p.X + cx * 1.2, p.Z + cz * 1.2) < 2.2))) score -= 6;
            double hurt = Caught(b, p.X, p.Z, cx * speed, cz * speed, deft, strikes, first, out double lands);
            score -= hurt;
            if (score > bestScore) { bestScore = score; bx = cx; bz = cz; soonest = hurt > 0 ? lands : double.MaxValue; }
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
            if (boss is IBound ring && !ring.Inside(ex, ez, 1.0)) continue;
            double hurt = Caught(b, ex, ez, 0, 0, deft, strikes, first, out _);
            if (hurt < dashBest) { dashBest = hurt; dx = cx; dz = cz; }
        }
        if (dashBest <= 0 && soonest < 0.6) { b.Dash(dx, dz); mx = dx; mz = dz; }
        else if (soonest < Abilities.Dash.Iframes - 0.05) b.Dash(dx == 0 && dz == 0 ? mx : dx, dx == 0 && dz == 0 ? mz : dz);
    }

    /// <summary>A blow the hands answer: one that hurts, takes or traps (not the safe
    /// ground, nor a cage's standing posts), marked long enough to have been seen, and
    /// noticed at all (decided by the blow itself, so a run replays).</summary>
    public static bool Threat(Battle.EnemyBlow bl, bool deft, Meeting? meeting = null) =>
        (bl.Kind == TelegraphKind.Blow || (bl.Kind == TelegraphKind.Wall && bl.Shape == TelegraphShape.Circle)) &&
        bl.Delay - bl.T >= Math.Min(deft ? ReactDeft : ReactPlain, bl.Delay * 0.6) &&
        Noticed(bl) < (deft ? NoticeDeft : NoticePlain) * (meeting?.New(bl) == true ? Meeting.NewNotice : 1);

    /// <summary>A number in [0, 1) that is the blow's own (where, when and what it is).</summary>
    /// <remarks>When it was marked is in it: a boss's opening lunge leaves from the same spot at the same delay
    /// every time, so without its moment a blow missed once was missed again after every rise, and in every run.</remarks>
    static double Noticed(Battle.EnemyBlow bl) => Noticed(bl.X, bl.Z, bl.Delay, bl.Shape, bl.Radius, bl.At);

    static double Noticed(double x, double z, double delay, TelegraphShape shape, double radius, double at = 0)
    {
        unchecked
        {
            uint h = (uint)(long)Math.Round(x * 97) * 73856093u ^ (uint)(long)Math.Round(z * 89) * 19349663u
                ^ (uint)(long)Math.Round(delay * 1000) * 83492791u ^ (uint)shape * 2654435761u ^ (uint)(long)Math.Round(radius * 31) * 40503u
                ^ (uint)(long)Math.Round(at * 60) * 2246822519u;
            h ^= h >> 13; h *= 0x5bd1e995; h ^= h >> 15;
            return (h % 10000) / 10000.0;
        }
    }

    /// <summary>How badly walking at (vx, vz) from (x, z) is caught by the blows marked
    /// (each scored by what it does), and how soon the first lands.</summary>
    static double Caught(Battle b, double x, double z, double vx, double vz, bool deft, bool strikes, Meeting? meeting, out double first)
    {
        double sum = 0;
        first = double.MaxValue;
        var p = b.Player;
        foreach (var bl in b.Blows)
        {
            if (!Threat(bl, deft, meeting)) continue;
            double t = Math.Min(bl.T, 1.2);
            // A little margin: the edge of a mark is where a player stops, not where they stand.
            if (!bl.Hit(x + vx * t, z + vz * t, p.Radius + 0.5)) continue;
            sum += 10 + bl.Damage / Math.Max(1, b.MaxHp) * 40 + (bl.Kind == TelegraphKind.Wall ? 8 : 0);
            first = Math.Min(first, bl.T);
        }
        if (strikes)
            foreach (var s in b.EnemyStrikes())
            {
                if (!Threat(s, deft)) continue;
                double t = Math.Min(s.Left, 1.2), dx = x + vx * t - s.X, dz = z + vz * t - s.Z;
                // As the strike itself measures her: her middle half inside its edge.
                if (dx * dx + dz * dz >= (s.R + p.Radius * 0.5 + 0.5) * (s.R + p.Radius * 0.5 + 0.5)) continue;
                sum += 10 + s.Damage / Math.Max(1, b.MaxHp) * 40;
                first = Math.Min(first, s.Left);
            }
        return sum;
    }

    /// <summary>A creature's marked circle the hands answer: marked long enough to have been seen, and noticed
    /// at all, as a boss's blow is.</summary>
    static bool Threat((double X, double Z, double R, double Marked, double Left, double Damage) s, bool deft) =>
        s.Marked - s.Left >= Math.Min(deft ? ReactDeft : ReactPlain, s.Marked * 0.6) &&
        Noticed(s.X, s.Z, s.Marked, TelegraphShape.Circle, s.R) < (deft ? NoticeDeft : NoticePlain);

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
