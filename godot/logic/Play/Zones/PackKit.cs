using System;
using System.Collections.Generic;
using SurvivorUnchained.Sim;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/// <summary>
/// The app can now press any zone's woken packs with the story fights' kit by world tier (M3): a pack's foes cast its
/// kit kind at her (their waits x Battle.KitEveryMul, its blows x KitDamageMul), and the stand clock (StandClock, the
/// tier's `stand` numbers in Battle.StoryStand) charges a stander from a woken pack. Encounters (the story fights) and
/// MapRun (the Wayfinder's maps) share it: one rule, the world tier's rows (world_tiers.json), no second copy.
/// </summary>
public sealed class PackKit(Battle b)
{
    /// <summary>A pack's tell waits (s, uniform in [min, max], x KitEveryMul) and its first after it woke: Encounters.Beat's defaults.</summary>
    public static readonly double[] Every = [5, 7];
    public const double FirstAfter = 1.2;

    readonly Dictionary<double, double> nextTell = new();
    readonly Queue<(double T, double X, double Z)> herTrail = new();
    double trailT, standReady;
    /// <summary>(M3 round 5) Where she last moved StandMoved from, and when (the stand's length, for StandGrow).</summary>
    double stillX, stillZ, stillAt = -1;
    /// <summary>The second charger, held its kit's spacing as the arena's Cast holds it (then cast at her).</summary>
    (Enemy E, double Seed, double At)? standSecond;
    /// <summary>(M3) Stand charges cast this run (the harness's tally).</summary>
    public int StandCharges { get; private set; }

    /// <summary>One woken pack's tells: each of its foes `may` lets (null: all) casts `kind` at her when in its reach and
    /// sight, FirstAfter s after the pack woke (each next foe 0.9 s on), then each Every x KitEveryMul; the kit's spacing
    /// (Battle.KitWait) holds it. Its own charge is the kit's: a teller's own shot waits.</summary>
    public void Tells(string kind, List<(Enemy E, double Seed)> up, double woke, double firstAfter, double[] every,
        Func<Enemy, bool>? may, Func<bool>? held, Action<Enemy, Battle.EnemyBlow>? told)
    {
        var p = b.Player;
        var k = Content.Telegraphs.Get(kind);
        double reach = k is { Length: > 0 } ? k.Length - 2 : 12;
        foreach (var (e, seed) in up)
        {
            if (may != null && !may(e)) continue;
            // Its charge is the kit's (marked, held, dashed), never its own.
            e.RangedT = Math.Max(e.RangedT, 5);
            if (!nextTell.TryGetValue(seed, out var at)) nextTell[seed] = at = woke + firstAfter + 0.9 * up.IndexOf((e, seed));
            if (b.Time < at || e.State != EnemyState.Active || e.HoldUntil > b.Time || held?.Invoke() == true) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d > reach || d < 2.5 || b.Collision.Raycast(e.X, e.Z, p.X, p.Z, 0.3) != null) { nextTell[seed] = b.Time + 0.4; continue; }
            double wait = b.KitWait(kind, e);
            if (wait > 0) { nextTell[seed] = b.Time + wait; continue; }
            var blow = b.Tell(kind, e, p.X, p.Z);
            nextTell[seed] = b.Time + (every[0] + b.Rng.Next() * (every[1] - every[0])) * b.KitEveryMul;
            if (blow != null) told?.Invoke(e, blow);
        }
    }

    /// <summary>(M3) The stand clock (H6's rule, StandClock, the arena director's): with the campaign on and the world tier's
    /// `stand` numbers (Battle.StoryStand), a woken pack's foe within StandNear charges her (the kit's charge, marked,
    /// at StandScale; a second from another side with StandPair 2) when she has not moved StandMoved in StandFor s, at most
    /// once each StandCooldown. Champions, bosses and the scripted never do. `awake`: the woken packs' live foes (asked
    /// only once she has stood). Off (no numbers, or the campaign off): nothing.</summary>
    public void Stand(double dt, Func<bool>? held, Func<HashSet<Enemy>> awake)
    {
        if (!b.Campaign || b.StoryStand is not { Stand: true } d) return;
        var p = b.Player;
        if ((trailT -= dt) <= 0) { trailT = 0.25; StandClock.Sample(herTrail, b.Time, p.X, p.Z, d.StandFor); }
        if (stillAt < 0 || p.RootT > 0 || Math.Sqrt((p.X - stillX) * (p.X - stillX) + (p.Z - stillZ) * (p.Z - stillZ)) >= d.StandMoved)
            { stillX = p.X; stillZ = p.Z; stillAt = b.Time; }
        double bite = d.StandDamage * (1 + Math.Min(d.StandGrowMax, d.StandGrow * Math.Max(0, b.Time - stillAt - d.StandFor)));
        if (standSecond is var (se, ss, sat) && b.Time >= sat && held?.Invoke() != true)
        {
            if (!se.Alive || se.Seed != ss || se.State != EnemyState.Active || !p.Alive) standSecond = null;
            else if (b.KitWait("charge", se) is var sw && sw > 0) standSecond = (se, ss, b.Time + sw);
            else { standSecond = null; b.Tell("charge", se, p.X, p.Z, d.StandScale, damageMul: bite); }
        }
        if (b.Time < standReady || !p.Alive || held?.Invoke() == true) return;
        // Held where she is (knocked down, rooted) is not standing: the clock starts again once she can move.
        if (p.RootT > 0) { standReady = b.Time + d.StandFor; return; }
        if (!StandClock.Still(herTrail, b.Time, p.X, p.Z, d)) return;
        var set = awake();
        if (set.Count == 0) return;
        Func<Enemy, bool> may = set.Contains;
        var near = StandClock.First(b, d, may);
        if (near == null) return;
        // (spaced as the packs' tells are: the kit's own wait, then the clock tries again)
        double wait = b.KitWait("charge", near);
        if (wait > 0) { standReady = b.Time + Math.Min(wait, 0.5); return; }
        standReady = b.Time + d.StandCooldown;
        StandCharges++;
        b.Tell("charge", near, p.X, p.Z, d.StandScale, damageMul: bite);
        if (StandClock.Second(b, d, near, may) is { } other) standSecond = (other, other.Seed, b.Time);
    }
}
