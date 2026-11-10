using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Zones;

/* The crowd's director (H6, the player must move; docs/team/hook/ H6). The owner, after demo-rc2: "i'm never really
 * surrounded. i'm never really kiting ... standing still letting everything come to me". The kit's marks are lethal
 * (Sim/Tells.cs), but a survivor who stands at the lamp and steps out of what she reads lived: nothing made standing
 * itself dangerous. The director does, as data (Content/Teeth.Director, data/content/teeth.json per tier; none: as it
 * was, and never on a story night):
 *   the pincer: two packs of the fastest kind from behind her on both sides, now and then (and sooner for the lamp's
 *     holder who will not leave its pool);
 *   the cut-off: a new group's leader runs for where she is going, not where she is;
 *   a surround closes: caught in a crowd, the kit's closing rises round her (the wall, and its gap the way out);
 *   packs close on a stander: still with them near, the nearest of them charges her;
 *   stuck foes recalled (N34: wolves stuck behind a rock, none coming again for a long time);
 *   the snuffer explained once, the first time one nears the lamp.
 * Its own dice (dirRng), so the night's other draws stay where they were. */
public sealed partial class ArenaRun
{
    Teeth.Director? Dir => teeth?.Director;
    Rng? dirRng;
    double flankAt = -1, surroundFor, closeReady, standReady, poolFor, poolNext, sampleT, stuckT;
    bool snufferTold, ironTold;
    double ironAt = -1;
    readonly Dictionary<int, double> slamReady = new();
    readonly List<(double X, double Z, double T, HashSet<int> Fed, bool Sounded)> corpses = new();
    readonly Queue<(double T, double X, double Z)> herTrail = new();
    readonly List<(Enemy E, double Seed)> leaders = new();
    readonly Dictionary<int, (double Seed, double X, double Z, double Since)> stuck = new();

    /// <summary>The director's pincers sent (two packs each), surrounds closed on her, stand charges cast, stuck foes recalled.</summary>
    public int Flanks { get; private set; }
    public int SurroundCloses { get; private set; }
    public int StandCharges { get; private set; }
    public int Recalls { get; private set; }
    /// <summary>Ironbacks sent, their ring slams cast, and times a wolf stopped to feed (H6 round 1).</summary>
    public int IronSpawns { get; private set; }
    public int IronSlams { get; private set; }
    public int Feeds { get; private set; }

    /// <summary>Ground from which the flow field leads to her (the director on): N34's wolves were spawned in pockets of the
    /// cover nothing leads out of, ran on the spot there and never came. Off: any standable ground, as it was.</summary>
    bool Reaches(double x, double z) => Dir is not { Recall: true } || !B!.Flow.Ready || !double.IsPositiveInfinity(B.Flow.DistanceAt(x, z));

    double DR() => (dirRng ??= new Rng((uint)(Spec.Seed * 9151 + 4271))).Next();

    /// <summary>A new group: its first is its leader, and cuts her off (Group's hook).</summary>
    void Led(List<Enemy> group)
    {
        if (Dir is not { CutOff: true } || group.Count == 0 || group[0].Boss) return;
        var e = group[0];
        e.Steer = true;
        e.SteerX = e.X; e.SteerZ = e.Z;
        leaders.Add((e, e.Seed));
    }

    void Direct(double dt)
    {
        if (Dir is not { } d || B == null || over) return;
        var p = B.Player;
        B.PackRoundCover = d.Recall;
        bool on = !won && !bossUp && p.Alive;
        // Her trail: where she was each quarter second over the last StandFor.
        if ((sampleT -= dt) <= 0)
        {
            sampleT = 0.25;
            StandClock.Sample(herTrail, Seconds, p.X, p.Z, d.StandFor);
        }
        CutOff(d);
        if (!on) { leaders.Clear(); return; }
        if (d.Flank) Flanking(d, dt);
        if (d.Surround) Surrounded(d, dt);
        if (d.Stand) Standing(d);
        if (d.Recall && (stuckT -= dt) <= 0) { stuckT = 1; Recall(d); }
        if (d.Explain && !snufferTold) Snuffer(d);
        if (d.Ironback) Ironbacks(d);
        if (d.Feed) Feeding(d);
    }

    /* ------------------------------------------------------ the ironback -- */

    void Ironbacks(Teeth.Director d)
    {
        var p = B!.Player;
        int alive = 0;
        foreach (var e in B.Enemies.Living())
        {
            if (e.Def.Id != "boar_ironback" || e.State == EnemyState.Dying) continue;
            alive++;
            if (e.State != EnemyState.Active || e.HoldUntil > B.Time || !TellsOn) continue;
            if (slamReady.TryGetValue(e.Id, out var rd) && rd > Seconds) continue;
            if (Dist(e.X, e.Z, p.X, p.Z) > d.SlamNear) continue;
            var k = Telegraphs.Get("ring");
            if (k == null) continue;
            slamReady[e.Id] = Seconds + d.SlamCooldown;
            IronSlams++;
            Cast("ring", e, e.X, e.Z, scale: d.SlamScale);
            e.Vx = e.Vz = 0;
            e.HoldUntil = B.Time + k.Windup;
        }
        if (ironAt < 0) ironAt = d.IronFrom;
        if (Seconds < ironAt) return;
        if (pacing.Hush(Seconds) || heraldAt > 0) { ironAt = Seconds + 2; return; }
        if (alive >= d.IronMax) { ironAt = Seconds + 5; return; }
        double sp = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz), heading = sp > 0.5 ? Math.Atan2(p.Vz, p.Vx) : p.Facing;
        double dist = d.IronDist[0] + DR() * (d.IronDist[1] - d.IronDist[0]);
        (double X, double Z)? at = FlankPoint(heading + Math.PI, dist);
        for (int t = 0; at == null && t < 6; t++) at = FlankPoint(DR() * Math.Tau, dist);
        if (at is not var (x, z)) { ironAt = Seconds + 3; return; }
        var ib = Spawn("boar_ironback", x, z, elite: true);
        if (ib == null) { ironAt = Seconds + 3; return; }
        ironAt = Seconds + d.IronEvery[0] + DR() * (d.IronEvery[1] - d.IronEvery[0]);
        IronSpawns++;
        if (ironTold) return;
        ironTold = true;
        B.Events.Emit(new Ev.Bark { X = ib.X, Z = ib.Z, Text = "Ironback. Don't stand and trade with it. Keep moving.", Speaker = null });
        double seed = ib.Seed;
        G.Teach(new Callout("ironback", CalloutKind.Freeze, "Ironback", "IRONBACK: too slow to catch you, too strong to stand beside. Keep moving and let your weapons work.",
            Aim.In(() => new[] { (ib.X, 1.0, ib.Z) }))
        { Urgent = true, Mark = "IRONBACK", Still = () => ib.Alive && ib.Seed == seed && ib.State != EnemyState.Dying });
    }

    /* ------------------------------------------------------- the pack feeds -- */

    /// <summary>A crowd wolf fell (OnKill): its spot is a corpse for CorpseLife s.</summary>
    void Corpse(Enemy e)
    {
        if (Dir is not { Feed: true } || e.Elite || e.Boss || e.Def.Family != Family.Wolf || B == null) return;
        corpses.Add((e.X, e.Z, Seconds, new HashSet<int>(), false));
    }

    readonly Dictionary<int, (double Seed, double T)> fedAt = new();

    void Feeding(Teeth.Director d)
    {
        var p = B!.Player;
        for (int i = corpses.Count - 1; i >= 0; i--)
        {
            var c = corpses[i];
            if (Seconds - c.T > d.CorpseLife) { corpses.RemoveAt(i); continue; }
            foreach (var e in B.HostilesInRadius(c.X, c.Z, d.FeedNear))
            {
                if (e.Elite || e.Boss || e.Scripted || e.Def.Family != Family.Wolf || e.State != EnemyState.Active || e.HoldUntil > B.Time || c.Fed.Contains(e.Id)) continue;
                if (Dist(e.X, e.Z, p.X, p.Z) < d.FeedFar) continue;
                // A wolf feeds once in FeedEvery, and a corpse feeds FeedMax at most: a pause bought by breaking away,
                // not a crowd that grazes its way across the field.
                if (c.Fed.Count >= d.FeedMax || fedAt.TryGetValue(e.Id, out var fa) && fa.Seed == e.Seed && Seconds - fa.T < d.FeedEvery) continue;
                fedAt[e.Id] = (e.Seed, Seconds);
                c.Fed.Add(e.Id);
                e.HoldUntil = B.Time + d.FeedFor;
                e.Vx = e.Vz = 0;
                Feeds++;
                if (!c.Sounded) { c.Sounded = true; corpses[i] = c; B.Events.Emit(new Ev.Sound { Id = "pack.feed", X = c.X, Z = c.Z }); }
            }
        }
    }

    /* ---------------------------------------------------- the pincer -- */

    void Flanking(Teeth.Director d, double dt)
    {
        if (flankAt < 0) flankAt = d.FlankFrom;
        // The lamp's holder draws one: PoolFor s in its lit pool, and each PoolEvery after while she stays.
        if (d.Pool && lamp != null)
        {
            if (lampLit && lampIn) poolFor += dt;
            else { poolFor = 0; poolNext = d.PoolFor; }
            if (poolNext <= 0) poolNext = d.PoolFor;
            if (poolFor >= poolNext) { poolNext += d.PoolEvery; flankAt = Math.Min(flankAt, Seconds); }
        }
        if (Seconds < flankAt) return;
        // (not in the hush before the boss, nor a herald's duel: it waits for them)
        if (pacing.Hush(Seconds) || heraldAt > 0) { flankAt = Seconds + 2; return; }
        flankAt = Seconds + d.FlankEvery[0] + DR() * (d.FlankEvery[1] - d.FlankEvery[0]);
        Flank(d);
    }

    void Flank(Teeth.Director d)
    {
        var p = B!.Player;
        double sp = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz), heading = sp > 0.5 ? Math.Atan2(p.Vz, p.Vx) : p.Facing;
        string def = Fastest();
        int n = (int)(d.FlankBase + Minute / d.FlankPerMinutes);
        double dist = d.FlankDist[0] + DR() * (d.FlankDist[1] - d.FlankDist[0]);
        bool sent = false;
        foreach (int side in new[] { 1, -1 })
        {
            if (FlankPoint(heading + side * d.FlankBearing * Math.PI / 180, dist) is not var (x, z)) continue;
            var g = Group(def, n, x, z, 2.5);
            sent |= g.Count > 0;
        }
        if (!sent) return;
        Flanks++;
        B.Events.Emit(new Ev.Sound { Id = "pack.flank", X = p.X, Z = p.Z });
    }

    /// <summary>Standable ground on this bearing from her, or on one near it (ten degrees at a time, either way).</summary>
    (double X, double Z)? FlankPoint(double angle, double dist)
    {
        var p = B!.Player;
        for (int t = 0; t < 9; t++)
        {
            double a = angle + (t + 1) / 2 * (t % 2 == 0 ? 1 : -1) * Math.PI / 18;
            double x = p.X + Math.Cos(a) * dist, z = p.Z + Math.Sin(a) * dist;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.7) && Reaches(x, z)) return (x, z);
        }
        return null;
    }

    /* ---------------------------------------------------- the cut-off -- */

    void CutOff(Teeth.Director d)
    {
        var p = B!.Player;
        double sp = Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        double ax = sp > 0.5 ? p.Vx / sp * d.Lead : 0, az = sp > 0.5 ? p.Vz / sp * d.Lead : 0;
        for (int i = leaders.Count - 1; i >= 0; i--)
        {
            var (e, seed) = leaders[i];
            bool gone = !e.Alive || e.Seed != seed || e.State == EnemyState.Dying;
            if (!gone && Dist(e.X, e.Z, p.X, p.Z) > d.LeadUntil && !bossUp && !won) { e.SteerX = p.X + ax; e.SteerZ = p.Z + az; continue; }
            if (!gone) e.Steer = false;
            leaders.RemoveAt(i);
        }
    }

    /* ------------------------------------------------ a surround closes -- */

    void Surrounded(Teeth.Director d, double dt)
    {
        var p = B!.Player;
        int mask = 0;
        foreach (var e in B.HostilesInRadius(p.X, p.Z, d.SurroundNear))
        {
            if (e.State == EnemyState.Dying) continue;
            double a = Math.Atan2(e.Z - p.Z, e.X - p.X) + Math.PI;
            mask |= 1 << Math.Min(5, (int)(a / (Math.PI / 3)));
        }
        int sectors = 0; for (int i = 0; i < 6; i++) if ((mask >> i & 1) != 0) sectors++;
        surroundFor = sectors >= d.SurroundSectors ? surroundFor + dt : 0;
        if (surroundFor < d.SurroundFor || Seconds < closeReady || !TellsOn) return;
        closeReady = Seconds + d.SurroundCooldown;
        surroundFor = 0;
        CloseOnHer(d, Pick(), (int)(d.CloseBase + Minute * d.ClosePerMinute));
    }

    /// <summary>The kit's closing round her (spaced as Close is): the foes already round her held in its ring with its own.</summary>
    void CloseOnHer(Teeth.Director d, string def, int n)
    {
        if (B == null || over || !TellsOn) return;
        double wait = B.KitWait("closing", null);
        if (wait > 0) { held.Add((Seconds + wait, () => CloseOnHer(d, def, n))); return; }
        var p = B.Player;
        var pts = B.TellClosing(p.X, p.Z, n);
        if (pts.Count == 0) return;
        SurroundCloses++;
        foreach (var e in B.HostilesInRadius(p.X, p.Z, d.SurroundNear + 1))
            if (!e.Boss && !e.Scripted && e.State == EnemyState.Active && e.HoldUntil <= B.Time) B.Closes(e);
        foreach (var (x, z) in pts)
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.6) && Reaches(x, z) && Spawn(def, x, z) is { } e) B.Closes(e);
        Shout("They close on you. Find the gap!");
    }

    /* --------------------------------------------- packs close on a stander -- */

    void Standing(Teeth.Director d)
    {
        if (Seconds < standReady || !TellsOn || herTrail.Count == 0) return;
        var p = B!.Player;
        // Held where she is (knocked down, rooted) is not standing: the clock starts again once she can move.
        if (p.RootT > 0) { standReady = Seconds + d.StandFor; return; }
        // (a full window behind her, all of it within StandMoved of where she is: StandClock, shared with the story fights)
        if (!StandClock.Still(herTrail, Seconds, p.X, p.Z, d)) return;
        var near = StandClock.First(B, d);
        if (near == null) return;
        standReady = Seconds + d.StandCooldown;
        StandCharges++;
        Cast("charge", near, p.X, p.Z, scale: d.StandScale);
        // A second from another side (StandPair): one step answers both lanes only if she reads both.
        var other = StandClock.Second(B, d, near);
        if (other != null) Cast("charge", other, p.X, p.Z, scale: d.StandScale);
    }

    /* ------------------------------------------------- stuck foes recalled -- */

    void Recall(Teeth.Director d)
    {
        var p = B!.Player;
        foreach (var e in B.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.Boss || e.Scripted || e.Decoy || e.State == EnemyState.Dying) { stuck.Remove(e.Id); continue; }
            if (!stuck.TryGetValue(e.Id, out var s) || s.Seed != e.Seed || Dist(e.X, e.Z, s.X, s.Z) >= d.StuckMoved
                || e.State != EnemyState.Active || e.HoldUntil > B.Time || e.Status.Has(StatusKind.Fear))
            {
                stuck[e.Id] = (e.Seed, e.X, e.Z, Seconds);
                continue;
            }
            if (Seconds - s.Since < d.StuckFor) continue;
            double her = Dist(e.X, e.Z, p.X, p.Z);
            // (one at her, one at the wick doing its job (or queued for it round its pool: the fold's snuffers were found queued, not stuck on its cover), one that shoots from where it stands: not stuck)
            bool atWick = e.Goal && lamp != null && lampDef != null && Dist(e.X, e.Z, lamp.X, lamp.Z) < lampDef.Pool + 2.5;
            bool shooting = e.Def.Ranged is { } rg && her < rg.Range + 1;
            if (her <= d.StuckNear || atWick || shooting || e.Def.Behavior == Behavior.Stationary) { stuck[e.Id] = (e.Seed, e.X, e.Z, Seconds); continue; }
            Recalls++;
            if (her > d.RecallFar && RecallPoint(d.RecallDist) is var (x, z))
            {
                e.X = x; e.Z = z;
                e.Vx = e.Vz = e.Kbx = e.Kbz = 0;
                e.Target = -1; e.RetargetT = 0;
            }
            else e.FlowUntil = B.Time + d.FlowFor;
            stuck[e.Id] = (e.Seed, e.X, e.Z, Seconds);
        }
    }

    (double X, double Z)? RecallPoint(double dist)
    {
        var p = B!.Player;
        // (at the map's rim most of the ring is off it: nearer rings after, never on the camera)
        for (int t = 0; t < 24; t++)
        {
            double a = DR() * Math.Tau, dd = dist * (t < 8 ? 1 : t < 16 ? 0.83 : 0.68);
            double x = p.X + Math.Cos(a) * dd, z = p.Z + Math.Sin(a) * dd;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.7) && Reaches(x, z)) return (x, z);
        }
        return null;
    }

    /* ------------------------------------------------- the snuffer explained -- */

    void Snuffer(Teeth.Director d)
    {
        if (lamp == null || !lampLit) return;
        foreach (var e in B!.Enemies.Living())
        {
            if (!e.Goal || e.State == EnemyState.Dying || Dist(e.X, e.Z, lamp.X, lamp.Z) > d.SnufferNear) continue;
            snufferTold = true;
            var p = B.Player;
            if (!G.Taught("snuffer")) B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = "They're putting out the lamp. Kill them at the wick." });
            double seed = e.Seed;
            G.Teach(new Callout("snuffer", CalloutKind.Freeze, "Snuffers", "SNUFFERS douse your lamp. Its light fills your Flare faster: kill them at the wick, then go.",
                Aim.In(() => new[] { (e.X, 1.0, e.Z) }))
            { Urgent = true, Mark = "SNUFFERS", Still = () => e.Alive && e.Seed == seed && e.State != EnemyState.Dying });
            return;
        }
    }
}
