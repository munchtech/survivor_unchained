using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/// <summary>
/// The app can now lay a day stretch into a zone from data (data/content/day_stretch.json, H4 item 10): resting packs
/// that wake as she comes near, their foes' kit telegraphs (a boar's charge), a champion who rallies its pack, a
/// lamp-post, a strongbox and the Flare's save (a closing ring round her), each beat's "down" kept in the zone's state
/// (WorldState.Zone, reset by ZoneReset's rule). The zone (Prologue) wraps it with its words and callouts; the balance
/// harness (godot/balance, lowford-day) plays the same fights from the same data. Its dice are the fight's (Battle.Rng).
/// </summary>
public sealed class DayStretch
{
    public sealed class Foe { public string Def = ""; public int N = 1; }

    /// <summary>A pack's next wave: out of the trees round its ground (Out m from it) once Under or fewer of it stand,
    /// with Elite one more of that kind as a champion.</summary>
    public sealed class Wave
    {
        public List<Foe> Foes = new(); public string? Elite; public int Under = 2; public double Out = 11;
        /// <summary>(r3, pulses) set: the wave comes this many seconds after the pack is all down (a breath), not at Under.</summary>
        public double? After;
        /// <summary>(r3) its foes' leash round the pack's ground; unset, the pack's own plus 4 (a camp's waves keep
        /// the camp's tight leash, so the fight stays on its ground).</summary>
        public double? Leash;
    }

    public sealed class Beat
    {
        public string Id = "", Kind = "";
        public double X, Z, Spread = 3, Wake = 9, Leash = 20, R = 2.4, ArmZ, FlareTo = 1, FirstAfter = 1.2;
        public List<Foe> Foes = new();
        public string? Tell, Captain, Post, Def, FollowElite;
        /// <summary>Only this kind casts the pack's tell (null: all of it); a chest's keepers (a pack's id).</summary>
        public string? TellBy, Guard;
        /// <summary>A ring springs only within this of its x (a fight off the road that strays north does not).</summary>
        public double HalfWidth = 999;
        /// <summary>A ring's second wave: the rest of the pack, out of the trees toward the gate, FollowAfter s on.</summary>
        public List<Foe> Follow = new();
        public double FollowAfter = 3;
        /// <summary>An ambush's foes come out of the trees this far round her (and never within 5 m).</summary>
        public double Out = 8;
        /// <summary>A pack's waves after the first (the camp's sleepers out of the tents, the wallow's from the reeds).</summary>
        public List<Wave> Waves = new();
        public double[] Every = [5, 7];
        public int N, Light = -1, Gold, LevelUp;
    }

    public sealed class Spec
    {
        public double[] From = [0, 0];
        public double GateZ;
        /// <summary>(H8 N22) The portcullis's line (z), where the shut gate bars her (0: none, the bar on the exit line).</summary>
        public double PortcullisZ;
        public List<Beat> Beats = new();
        public Beat? Get(string id) => Beats.FirstOrDefault(b => b.Id == id);
    }

    sealed class File { public Dictionary<string, Spec> Zones = new(); }
    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("day_stretch.json"));

    /// <summary>The zone's stretch, or null for a zone without one.</summary>
    public static Spec? For(string zone) => F.Zones.GetValueOrDefault(zone);

    /// <summary>The key in the zone's state that says a beat is done for the day (its pack down, its chest opened).</summary>
    public static string DoneKey(string beat) => "day." + beat;

    /// <summary>A day foe's level, as the Verge's: 1 + (her level + the day) / 2, and the beat's own step up.</summary>
    public static int Level(int herLevel, int day, Beat bt) => Math.Max(1, 1 + (herLevel + day) / 2 + bt.LevelUp);

    public readonly Spec S;
    readonly Battle b;
    readonly Dictionary<string, Fact> state;
    readonly int level, day;

    /// <summary>Each pack's foes, as spawned (a pooled foe is its own while its Seed holds).</summary>
    public readonly Dictionary<string, List<(Enemy E, double Seed)>> Packs = new();
    /// <summary>When each pack woke (game seconds), and when it was put down.</summary>
    public readonly Dictionary<string, double> WokeAt = new(), DownAt = new();
    /// <summary>Each beat's champion (the captain), while it stands.</summary>
    public readonly Dictionary<string, (Enemy E, double Seed)> Captains = new();
    readonly Dictionary<double, double> nextTell = new();
    /// <summary>The ring: armed (she has been south of its armZ this visit), sprung (game seconds; -1 not yet).</summary>
    bool armed;
    public double RingAt = -1;

    /// <summary>A pack woke (its first foe roused).</summary>
    public Action<Beat>? Woke;
    /// <summary>A beat's foes are all down (marked done for the day).</summary>
    public Action<Beat>? Down;
    /// <summary>A foe of a beat cast its kit tell (its blow on the ground).</summary>
    public Action<Beat, Enemy, Battle.EnemyBlow>? Told;
    /// <summary>The ring closed round her (its band on the ground, its foes held on it).</summary>
    public Action<Beat>? Ringed;
    /// <summary>Whether casts wait (a freeze up): none ask while it holds.</summary>
    public Func<bool>? Held;

    public DayStretch(Spec s, Battle battle, Dictionary<string, Fact> zoneState, int herLevel, int day)
    {
        S = s; b = battle; state = zoneState; level = herLevel; this.day = day;
    }

    public bool Done(string beat) => state.TryGetValue(DoneKey(beat), out var f) && f.Truthy;
    public void MarkDone(string beat) => state[DoneKey(beat)] = true;

    public IEnumerable<Beat> Of(string kind) => S.Beats.Where(x => x.Kind == kind);

    /// <summary>The packs not yet down today, resting where the data puts them.</summary>
    public void Place()
    {
        b.ClosingTeeth = true;
        foreach (var bt in Of("pack"))
        {
            if (Done(bt.Id)) continue;
            var list = new List<(Enemy, double)>();
            int lv = Level(level, day, bt);
            foreach (var f in bt.Foes)
                for (int i = 0; i < f.N; i++)
                    if (Spawn(f.Def, bt, lv, false) is { } e) list.Add((e, e.Seed));
            if (bt.Captain != null && Spawn(bt.Captain, bt, lv + 1, true, near: 1) is { } c)
            {
                list.Add((c, c.Seed));
                Captains[bt.Id] = (c, c.Seed);
            }
            Packs[bt.Id] = list;
        }
    }

    Enemy? Spawn(string def, Beat bt, int lv, bool elite, double? near = null)
    {
        double spread = near ?? bt.Spread;
        for (int t = 0; t < 12; t++)
        {
            double a = b.Rng.Next() * Math.Tau, d = Math.Sqrt(b.Rng.Next()) * spread;
            double x = bt.X + Math.Cos(a) * d, z = bt.Z + Math.Sin(a) * d;
            if (b.Collision.Blocked(x, z, 0.7) && t < 11) continue;
            var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts
            {
                Level = lv, Elite = elite, Style = SpawnStyle.Walk, Tag = "day:" + bt.Id, Home = (bt.X, bt.Z, bt.Leash), Wake = bt.Wake,
            });
            if (e != null) e.Facing = b.Rng.Next() * Math.Tau;
            return e;
        }
        return null;
    }

    static bool Live((Enemy E, double Seed) f) => f.E.Alive && f.E.Seed == f.Seed && f.E.State != EnemyState.Dying;

    /// <summary>The pack's foes still standing.</summary>
    public List<Enemy> Standing(string beat) => Packs.TryGetValue(beat, out var l) ? l.Where(Live).Select(f => f.E).ToList() : new();

    /// <summary>The beat's champion while it stands.</summary>
    public Enemy? Captain(string beat) => Captains.TryGetValue(beat, out var c) && Live(c) ? c.E : null;

    /// <summary>Some pack is awake and on its feet (a fight is on), or the ring's foes still stand. Only foes within
    /// FightNear of her count once a pack has been up FightGrace (H4 lead 3: j08 run g3 soft-locked at the ring for
    /// 4 minutes on one track-ambush foe left standing far off in the trees; the gate held for good).</summary>
    public bool Fighting => Packs.Any(kv => WokeAt.TryGetValue(kv.Key, out var w) && !DownAt.ContainsKey(kv.Key)
        && (b.Time - w < FightGrace || kv.Value.Any(f => Live(f) && Dist(f.E.X, f.E.Z, b.Player.X, b.Player.Z) < FightNear)));
    public const double FightNear = 24, FightGrace = 6;

    public void Tick(double dt)
    {
        var p = b.Player;
        foreach (var (id, list) in Packs)
        {
            var bt = S.Get(id)!;
            if (DownAt.ContainsKey(id)) continue;
            var up = list.Where(Live).ToList();
            if (!WokeAt.ContainsKey(id) && (up.Any(f => f.E.Roused || f.E.Wake <= 0) || bt.Kind == "ring"))
            {
                WokeAt[id] = b.Time;
                // A roused foe wakes its whole pack: they came together.
                foreach (var f in up) f.E.Roused = true;
                Woke?.Invoke(bt);
            }
            // Those a captain calls out of the trees are the pack's too.
            if (Captains.TryGetValue(id, out var cap) && Live(cap) && cap.E.Def.Summon is { } su)
                foreach (var o in b.Enemies.Living())
                    if (o.Tag == null && o.LifeT < 0.5 && o.Faction == cap.E.Faction && o.State != EnemyState.Dying && Dist(o.X, o.Z, cap.E.X, cap.E.Z) < su.Range + 2)
                    {
                        o.Tag = "day:" + id; o.Roused = true;
                        // (on the pack's leash, round its ground: a called foe had none, and drew her 40 m off the camp)
                        o.HomeX = bt.X; o.HomeZ = bt.Z; o.Leash = bt.Leash;
                        list.Add((o, o.Seed)); up.Add((o, o.Seed));
                    }
            // (its next wave, out of the trees round its ground, when it is thinned to Under)
            // (a pulse: the pack down, its next wave After s on; the pack is not down till it has come)
            bool pulse = WokeAt.ContainsKey(id) && Sent(id) < bt.Waves.Count && bt.Waves[Sent(id)].After is { } aft;
            if (pulse && up.Count == 0)
            {
                if (!quietAt.ContainsKey(id)) quietAt[id] = b.Time;
                if (b.Time - quietAt[id] < bt.Waves[Sent(id)].After!.Value) continue;
                quietAt.Remove(id);
            }
            if (WokeAt.ContainsKey(id) && Sent(id) < bt.Waves.Count && (pulse ? up.Count == 0 : up.Count <= bt.Waves[Sent(id)].Under))
            {
                var w = bt.Waves[Sent(id)];
                sent[id] = Sent(id) + 1;
                foreach (var e in SendWave(bt, w)) { list.Add((e, e.Seed)); up.Add((e, e.Seed)); }
                Waved?.Invoke(bt, sent[id]);
            }
            if (up.Count == 0)
            {
                DownAt[id] = b.Time;
                MarkDone(id);
                Down?.Invoke(bt);
                continue;
            }
            if (bt.Tell is not { } kind || !WokeAt.TryGetValue(id, out var woke)) continue;
            var k = Telegraphs.Get(kind);
            double reach = k is { Length: > 0 } ? k.Length - 2 : 12;
            foreach (var (e, seed) in up)
            {
                if (bt.TellBy != null && e.Def.Id != bt.TellBy) continue;
                // Its charge is the kit's (marked, held, dashed), never its own.
                e.RangedT = Math.Max(e.RangedT, 5);
                if (!nextTell.TryGetValue(seed, out var at)) nextTell[seed] = at = woke + bt.FirstAfter + 0.9 * up.IndexOf((e, seed));
                if (b.Time < at || e.State != EnemyState.Active || e.HoldUntil > b.Time || Held?.Invoke() == true) continue;
                double d = Dist(e.X, e.Z, p.X, p.Z);
                if (d > reach || d < 2.5 || b.Collision.Raycast(e.X, e.Z, p.X, p.Z, 0.3) != null) { nextTell[seed] = b.Time + 0.4; continue; }
                double wait = b.KitWait(kind, e);
                if (wait > 0) { nextTell[seed] = b.Time + wait; continue; }
                var blow = b.Tell(kind, e, p.X, p.Z);
                nextTell[seed] = b.Time + bt.Every[0] + b.Rng.Next() * (bt.Every[1] - bt.Every[0]);
                if (blow != null) Told?.Invoke(bt, e, blow);
            }
        }
        foreach (var bt in Of("ambush"))
            if (!Done(bt.Id) && !Packs.ContainsKey(bt.Id) && (bt.Guard == null || Done(bt.Guard)) && !Fighting && Held?.Invoke() != true
                && Dist(p.X, p.Z, bt.X, bt.Z) < bt.R)
                Spring(bt);
        foreach (var bt in Of("ring"))
        {
            // (r3: the rest of the pack after a breath, FollowAfter s once the ring's own foes are down: two pulses, not one press)
            if (RingAt >= 0 && !followed && DownAt.TryGetValue(bt.Id, out var rd) && b.Time - rd >= bt.FollowAfter && (bt.Follow.Count > 0 || bt.FollowElite != null)) { followed = true; Follow(bt); }
            if (Done(bt.Id) || RingAt >= 0) continue;
            // (armed on the road south of its line; off the road it disarms, so she comes back to the road to spring it,
            // with the gate ahead: j08 r2 came along the wall from the wallow and sprang it in the trees)
            if (Math.Abs(p.X - bt.X) > bt.HalfWidth) armed = false;
            else if (p.Z > bt.ArmZ) armed = true;
            // (H8, N22: on the road a metre past its line it springs armed or not: she came round by the wall onto the
            // gate's apron, and the wolves come out there, the gate ahead of her)
            if (!(armed || p.Z < bt.Z - 1) || p.Z > bt.Z || Math.Abs(p.X - bt.X) > bt.HalfWidth || Fighting || Held?.Invoke() == true) continue;
            Ring(bt);
        }
    }

    /// <summary>The way out is open: every ring sprung, and its second wave come and down (the wolves hold the gate;
    /// r3: a player at the ring's line is 7 m from the exit and would walk out in the breath). Shut before the ring is
    /// sprung too (H8, N22, the owner: "we are able to just run up to the waystation and skip the whole day time
    /// tutorial"). The last one standing does not hold it (the harness's bots were held for good by a howler that kept
    /// off behind a tree).</summary>
    /// (Not sprung this run but done: put down before a reload, the save after its wave.)
    public bool GateOpen => Of("ring").All(bt => RingAt < 0 ? Done(bt.Id)
        : (bt.Follow.Count > 0 || bt.FollowElite != null ? followed : true) && Standing(bt.Id).Count(e => Dist(e.X, e.Z, b.Player.X, b.Player.Z) < 25) <= 1);

    /// <summary>The gate is shut and no ring has been sprung: what holds it is the ring still to come (its line on the road).</summary>
    public Beat? RingOwed => RingAt < 0 ? Of("ring").FirstOrDefault(bt => !Done(bt.Id)) : null;

    /// <summary>An ambush springs: its foes out of the trees round her, a fight where she stands.</summary>
    void Spring(Beat bt)
    {
        var p = b.Player;
        int lv = Level(level, day, bt);
        var list = new List<(Enemy, double)>();
        var kinds = bt.Foes.SelectMany(f => Enumerable.Repeat(f.Def, f.N)).ToList();
        double a0 = b.Rng.Next() * Math.Tau;
        for (int i = 0; i < kinds.Count; i++)
            for (int t = 0; t < 12; t++)
            {
                double a = a0 + i * 2.39996 + (b.Rng.Next() - 0.5) * 0.5, d = bt.Out + b.Rng.Next() * 2.5;
                double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
                if (b.Collision.Blocked(x, z, 0.7) && t < 11) continue;
                var e = b.SpawnEnemy(kinds[i], x, z, new Battle.SpawnOpts
                {
                    Level = lv, Style = SpawnStyle.Walk, Tag = "day:" + bt.Id, Home = (bt.X, bt.Z, bt.Leash),
                });
                if (e != null) { e.Roused = true; list.Add((e, e.Seed)); }
                break;
            }
        Packs[bt.Id] = list;
        WokeAt[bt.Id] = b.Time;
        Woke?.Invoke(bt);
    }

    readonly Dictionary<string, double> quietAt = new();
    /// <summary>A pack between its pulses (all down, its next wave still to come): she holds its ground.</summary>
    public bool Breath(string beat) => quietAt.ContainsKey(beat);

    bool followed;
    readonly Dictionary<string, int> sent = new();
    /// <summary>How many of a pack's waves have come.</summary>
    public int Sent(string beat) => sent.GetValueOrDefault(beat);
    /// <summary>A pack's next wave came out of the trees (its number, from 1).</summary>
    public Action<Beat, int>? Waved;

    /// <summary>A wave round the pack's ground, Out m from it (a clearing's edge, the tree line), its champion the last.</summary>
    List<Enemy> SendWave(Beat bt, Wave w)
    {
        var p = b.Player;
        int lv = Level(level, day, bt);
        var got = new List<Enemy>();
        var kinds = w.Foes.SelectMany(f => Enumerable.Repeat(f.Def, f.N)).Select(d => (d, false)).ToList();
        if (w.Elite != null) kinds.Add((w.Elite, true));
        double a0 = b.Rng.Next() * Math.Tau;
        for (int i = 0; i < kinds.Count; i++)
        {
            var (def, elite) = kinds[i];
            for (int t = 0; t < 12; t++)
            {
                double a = a0 + i * 2.39996 + (b.Rng.Next() - 0.5) * 0.5, d = w.Out + b.Rng.Next() * 2.5;
                double x = bt.X + Math.Cos(a) * d, z = bt.Z + Math.Sin(a) * d;
                if ((b.Collision.Blocked(x, z, 0.7) || Dist(x, z, p.X, p.Z) < 5) && t < 11) continue;
                var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts
                {
                    Level = elite ? lv + 1 : lv, Elite = elite, Style = SpawnStyle.Walk, Tag = "day:" + bt.Id, Home = (bt.X, bt.Z, w.Leash ?? bt.Leash + 4),
                });
                if (e != null) { e.Roused = true; got.Add(e); }
                break;
            }
        }
        return got;
    }

    /// <summary>Where a sensible player goes next (the autopilot's day and the harness's, one route): a waking pack's
    /// nearest foe, fought where it stands; else the beats in the data's order, each pack's ground, a chest once its
    /// keepers are down (chestAt: where it lies, null while it is not on the ground), a dark post, the ring's line
    /// (south of its arming line first); then the gate. A place across the ground comes back as the next corner of a
    /// route round the trees (GroundPath), a foe straight. For: the beat it is for (null: the gate or a fight).</summary>
    public (double X, double Z, Beat? For) Goal(Func<Beat, bool> postLit, Func<Beat, (double X, double Z)?> chestAt, double gateX)
    {
        var p = b.Player;
        Enemy? near = null; double nd = 16;
        foreach (var (id, _) in Packs)
        {
            if (!WokeAt.ContainsKey(id) || DownAt.ContainsKey(id)) continue;
            foreach (var e in Standing(id)) { double d = Dist(e.X, e.Z, p.X, p.Z); if (d < nd) { nd = d; near = e; } }
        }
        // (round the trees to it: a footpad's bowman backs into the wood)
        if (near != null) return nd < 4 ? (near.X, near.Z, null) : Route(near.X, near.Z, null);
        foreach (var bt in S.Beats)
        {
            switch (bt.Kind)
            {
                case "pack" when Packs.ContainsKey(bt.Id) && !DownAt.ContainsKey(bt.Id):
                {
                    // (woke, its foes strayed: the nearest of them; resting: its ground)
                    var up = Standing(bt.Id);
                    if (WokeAt.ContainsKey(bt.Id) && up.Count > 0) { var f = up.MinBy(e => Dist(e.X, e.Z, p.X, p.Z))!; return Route(f.X, f.Z, bt); }
                    return Route(bt.X, bt.Z, bt);
                }
                case "chest" when !Done(bt.Id) && (bt.Guard == null || Done(bt.Guard)) && chestAt(bt) is { } c:
                    return Route(c.X, c.Z, bt);
                // (an ambush lies on her way: through its ground, once what it waits on is done)
                case "ambush" when !Done(bt.Id) && !Packs.ContainsKey(bt.Id) && (bt.Guard == null || Done(bt.Guard)):
                    return Route(bt.X, bt.Z, bt);
                case "post" when !postLit(bt):
                    return Route(bt.X + 1.4, bt.Z, bt);
                case "ring" when !Done(bt.Id) && RingAt < 0:
                    return armed ? Route(bt.X, bt.Z - 3, bt) : Route(bt.X, bt.ArmZ + 2.5, bt);
                // (sprung, its second wave still to come: she holds the road and gets her breath)
                case "ring" when RingAt >= 0 && !GateOpen:
                    return Route(bt.X, bt.Z - 2, bt);
            }
        }
        return Route(gateX, S.GateZ - 6, null);
    }

    List<(double X, double Z)>? route;
    (double X, double Z) routeTo;
    double routeAt = -99;

    /// <summary>The next corner of a route round what is solid to (x, z), found again every 2 s or when the goal moves.</summary>
    (double X, double Z, Beat? For) Route(double x, double z, Beat? bt)
    {
        var p = b.Player;
        if (route == null || b.Time - routeAt > 2 || Dist(routeTo.X, routeTo.Z, x, z) > 1.5)
        {
            routeAt = b.Time; routeTo = (x, z);
            route = GroundPath.Find(b.Collision, p.X, p.Z, x, z, 0.8);
        }
        while (route is { Count: > 1 } && Dist(route[0].X, route[0].Z, p.X, p.Z) < 0.9) route.RemoveAt(0);
        var (wx, wz) = route is { Count: > 0 } ? route[0] : (x, z);
        // Wedged (no nearer the corner for 1.2 s): a step aside, to whichever hand is open, and the route found again.
        if (b.Time < sideUntil) return (side.X, side.Z, bt);
        double d = Dist(wx, wz, p.X, p.Z);
        if (Dist(wx, wz, lastW.X, lastW.Z) > 0.5) { lastW = (wx, wz); lastD = d; stuckSince = b.Time; }
        else if (d < lastD - 0.3) { lastD = d; stuckSince = b.Time; }
        else if (b.Time - stuckSince > 1.2 && d > 0.3)
        {
            double ux = (wx - p.X) / d, uz = (wz - p.Z) / d;
            int hand = b.Collision.Blocked(p.X - uz * 1.5, p.Z + ux * 1.5, 0.4) ? -1 : 1;
            side = (p.X - uz * 1.8 * hand - ux * 0.6, p.Z + ux * 1.8 * hand - uz * 0.6);
            sideUntil = b.Time + 0.6; stuckSince = b.Time + 0.6; lastD = 1e9; route = null;
            return (side.X, side.Z, bt);
        }
        return (wx, wz, bt);
    }

    (double X, double Z) side, lastW;
    double sideUntil = -1, stuckSince, lastD = 1e9;

    /// <summary>The rest of the ring's pack: out of the trees 12 m on toward the gate, hunting her.</summary>
    void Follow(Beat bt)
    {
        var p = b.Player;
        int lv = Level(level, day, bt);
        var list = Packs.TryGetValue(bt.Id, out var l) ? l : Packs[bt.Id] = new();
        Enemy? One(string def, bool elite, int i, int n)
        {
            for (int t = 0; t < 16; t++)
            {
                // (r3: on this side of the wall, never in it: j08's harness had four stuck in the stones, holding the gate)
                double a = -Math.PI / 2 + (n <= 1 ? 0 : (i / (double)(n - 1) - 0.5) * (1.6 + t * 0.12)) + (b.Rng.Next() - 0.5) * 0.4, d = Math.Max(7, 11 + b.Rng.Next() * 3 - t * 0.3);
                double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
                if (b.Collision.Blocked(x, z, 0.6) || z < S.GateZ - 6) continue;
                var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = elite ? lv + 1 : lv, Elite = elite, Style = SpawnStyle.Walk, Tag = "day:" + bt.Id });
                if (e != null) { e.Roused = true; list.Add((e, e.Seed)); }
                return e;
            }
            return null;
        }
        int all = bt.Follow.Sum(f => f.N) + (bt.FollowElite != null ? 1 : 0), k = 0;
        foreach (var f in bt.Follow) for (int i = 0; i < f.N; i++) One(f.Def, false, k++, all);
        if (bt.FollowElite != null && One(bt.FollowElite, true, k++, all) is { } c) Captains[bt.Id] = (c, c.Seed);
        // (a pack put down before its second wave came is up again until the wave is down)
        DownAt.Remove(bt.Id);
        state.Remove(DoneKey(bt.Id));
    }

    /// <summary>The Flare's save: the closing round her, its foes on the band's points, her Flare filled if short.</summary>
    public void Ring(Beat bt)
    {
        var p = b.Player;
        RingAt = b.Time;
        if (b.Flare != null) b.FlareMeter = Math.Max(b.FlareMeter, Battle.FlareFull * bt.FlareTo);
        var list = new List<(Enemy, double)>();
        int lv = Level(level, day, bt);
        foreach (var (x, z) in b.TellClosing(p.X, p.Z, bt.N))
        {
            if (b.Collision.Blocked(x, z, 0.6)) continue;
            var e = b.SpawnEnemy(bt.Def ?? "wolf", x, z, new Battle.SpawnOpts { Level = lv, Style = SpawnStyle.Walk, Tag = "day:" + bt.Id });
            if (e == null) continue;
            b.Closes(e);
            e.Roused = true;
            list.Add((e, e.Seed));
        }
        Packs[bt.Id] = list;
        WokeAt[bt.Id] = b.Time;
        Ringed?.Invoke(bt);
    }
}
