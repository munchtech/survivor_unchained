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

    public sealed class Beat
    {
        public string Id = "", Kind = "";
        public double X, Z, Spread = 3, Wake = 9, Leash = 20, R = 2.4, ArmZ, FlareTo = 1, FirstAfter = 1.2;
        public List<Foe> Foes = new();
        public string? Tell, Captain, Post, Def, FollowElite;
        /// <summary>A ring's second wave: the rest of the pack, out of the trees toward the gate, FollowAfter s on.</summary>
        public List<Foe> Follow = new();
        public double FollowAfter = 3;
        public double[] Every = [5, 7];
        public int N, Light = -1, Gold, LevelUp;
    }

    public sealed class Spec
    {
        public double[] From = [0, 0];
        public double GateZ;
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

    /// <summary>Some pack is awake and on its feet (a fight is on), or the ring's foes still stand.</summary>
    public bool Fighting => Packs.Any(kv => WokeAt.ContainsKey(kv.Key) && !DownAt.ContainsKey(kv.Key));

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
                        list.Add((o, o.Seed)); up.Add((o, o.Seed));
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
        foreach (var bt in Of("ring"))
        {
            if (RingAt >= 0 && !followed && b.Time - RingAt >= bt.FollowAfter && (bt.Follow.Count > 0 || bt.FollowElite != null)) { followed = true; Follow(bt); }
            if (Done(bt.Id) || RingAt >= 0) continue;
            if (p.Z > bt.ArmZ) armed = true;
            if (!armed || p.Z > bt.Z || Held?.Invoke() == true) continue;
            Ring(bt);
        }
    }

    bool followed;

    /// <summary>The rest of the ring's pack: out of the trees 12 m on toward the gate, hunting her.</summary>
    void Follow(Beat bt)
    {
        var p = b.Player;
        int lv = Level(level, day, bt);
        var list = Packs.TryGetValue(bt.Id, out var l) ? l : Packs[bt.Id] = new();
        Enemy? One(string def, bool elite, int i, int n)
        {
            for (int t = 0; t < 10; t++)
            {
                double a = -Math.PI / 2 + (n <= 1 ? 0 : (i / (double)(n - 1) - 0.5) * 1.6) + (b.Rng.Next() - 0.5) * 0.4, d = 11 + b.Rng.Next() * 3;
                double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
                if (b.Collision.Blocked(x, z, 0.6) && t < 9) continue;
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
