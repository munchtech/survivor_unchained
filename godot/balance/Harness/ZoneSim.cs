using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Balance;

/// <summary>One run of a real zone (M5-F): the Low Ford from the Wake to the gate, by one pair of hands at a world tier.</summary>
public sealed record ZoneRunSpec(int Seed, string Zone, string Bot, int Tier, string Calling = "warden", string[]? Features = null)
{
    public string Key => $"{Zone}/T{Tier}/{Bot}/s{Seed}";
}

public sealed class ZoneRunResult
{
    public ZoneRunSpec Spec = null!;
    public bool Reached, BossReached, WardenDown, Stuck;
    public string? StuckAt;
    public double Seconds, FilmFallback, Meters, MetersNight, MetersDay, Fighting, Gold, GoldDropped;
    public int LeftLying, Discarded, Unsticks, Fodder, Elite, Champion, Boss, Packs, Champions, Falls, Rises, GearShown, Upgrades;
    public int[] Gear = new int[7];
    public int WardenGear;
    /// <summary>(--features preview) The forced-on features' beats: packs placed, their foes, foes that landed on blocked ground, packs put down, packs left standing at the end.</summary>
    public int PocketPacks, PocketFoes, PocketBlocked, PocketDown, PocketLeft;
    public bool WardenLegendary;
    public int LevelAtWarden, LevelAtGate, PostsLit;
    /// <summary>(M3) The hands on the press plan (their presses by skill), and her damage by source.</summary>
    public PressHands? Hands;
    public Dictionary<string, double> DamageBy = new();
    public double ResolveSpent, ResolveFullSec, FlareFirst = -1, MarkGapMax;
    public int FlareCasts;
    /// <summary>(M3) The numbers round's measures (RunMeter: mark gap, Resolve, presses, shares, Flare, falls).</summary>
    public RunMeasures Measures = new();
    public readonly List<string> FallsAt = new(), RisesAt = new(), WardenDrops = new();
    /// <summary>Each beat put down: its seconds (woke to down) and her level then.</summary>
    public readonly Dictionary<string, (double Seconds, int Level)> Beats = new();
    /// <summary>(M5) Each beat's wake and down (game seconds), and the wakes made while a champion (not the pack's own) lived within 25 m of her.</summary>
    public readonly Dictionary<string, double> WokeT = new(), DownT = new();
    public readonly List<string> ChampWakes = new(), ChampWakesNear = new();
    /// <summary>Seconds in each stage of the zone (Prologue.Stage).</summary>
    public readonly Dictionary<string, double> Stages = new();
    public int Kills => Fodder + Elite + Champion + Boss;
    /// <summary>Sim seconds less the films' headless fallbacks (C02's captions, C03's): a player's time in play.</summary>
    public double PlaySeconds => Seconds - FilmFallback;
}

/// <summary>The zone sim (M5-F, ARPG.md 7.1): the real Prologue through HeadlessHost, from the Wake, its night's beats in order,
/// the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day
/// stretch to the gate. Falls go through the zone's own OnDeath (the rise at her last post), as Game.HookBattle routes them.
/// The bots are today's self-firing hands (the pressing bots are M3's).</summary>
public static class ZoneSim
{
    public const double Cap = 3600, StuckAfter = 300;

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    public static ZoneRunResult Play(ZoneRunSpec spec, bool quiet = false)
    {
        var dbg = new HashSet<string>();
        if (spec.Zone != "lowford") throw new ArgumentException($"zone sim: only lowford is built ({spec.Zone})");
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)spec.Seed);
        j.World.Facts[WorldTiers.Key] = spec.Tier;
        var meta = ZoneMeta.Load("lowford");
        if (spec.Features != null) meta.Features.AddRange(spec.Features);
        var pocketSeen = new HashSet<string>();
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new Prologue(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, ember: zone.Ember);
        var r = new ZoneRunResult { Spec = spec };
        double wardenDownAt = -1;
        // (as Game.HookBattle: the journey's kills and pickups, the zone's after; a fall the zone's hooks do not take goes to its OnDeath)
        var zh = zone.Hooks;
        var h = BattleHooks.Following(zh);
        h.OnKill = (e, by) =>
        {
            j.Killed(e, by);
            zh.OnKill?.Invoke(e, by);
            if (!by) return;
            if (e.Boss || e.Tag == "warden") { r.Boss++; if (e.Tag == "warden") wardenDownAt = b.Time; }
            else if (e.Named != null) r.Champion++;
            else if (e.Elite) r.Elite++;
            else r.Fodder++;
        };
        h.OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && j.PickedUp(p);
        h.OnPlayerDeath = killer =>
        {
            if (zh.OnPlayerDeath?.Invoke(killer) == true) return true;
            j.Ch.Stats.Deaths++;
            r.Falls++;
            r.FallsAt.Add($"{zone.Now}@({b.Player.X:0},{b.Player.Z:0}) by {killer?.Def.Id ?? "the dark"}");
            if (!zone.OnDeath(killer?.Def.Name ?? "the dark")) throw new InvalidOperationException("the zone let her go");
            return false;
        };
        b.Hooks = h;
        host.Battle = b;
        zone.Begin(b);

        var human = spec.Bot is "human" or "careless" or "idler" ? new Human(spec.Seed, spec.Bot == "careless") { Idle = spec.Bot == "idler" } : null;
        bool deft = spec.Bot == "deft", standing = spec.Bot == "standing";
        if (human == null && !standing && spec.Bot is not ("deft" or "plain")) throw new ArgumentException($"zone sim: unknown bot {spec.Bot}");
        // (M3: the bots on the one press plan; plain keeps the old hands)
        uint hs = (uint)spec.Seed;
        var hands = spec.Bot switch
        {
            "deft" => PressHands.Deft(hs),
            "human" => PressHands.Human(hs, human!.React),
            "careless" => PressHands.Careless(hs, human!.React),
            "standing" or "idler" => PressHands.Grip(hs),
            _ => null,
        };
        if (human != null) human.Hands = hands;
        r.Hands = hands;
        var meter = new RunMeter { Deaths = false };
        var road = meta.Paths.GetValueOrDefault("ROAD") ?? Array.Empty<double[]>();
        int wp = 0;
        var ford = meta.Place("LOWFORD", "ford");
        var gate = meta.Place("LOWFORD", "gate");
        var seenGear = new HashSet<ItemInstance>(ReferenceEqualityComparer.Instance);
        var goldUp = new HashSet<Pickup>(ReferenceEqualityComparer.Instance);
        var filter = new LootFilter { Preset = FilterPreset.Default };
        var best = new Dictionary<EquipSlot, double>();
        var night = zone.Night;
        double gold0 = j.Ch.Gold;
        double lastX = b.Player.X, lastZ = b.Player.Z, dt = ArenaSim.Dt, t0 = b.Time, tt = 0;
        string sig = ""; double sigAt = 0;
        var stage = zone.Now; double stageAt = 0;
        bool wasAlive = true;
        // (a wall between her and her goal, the bots' steering slides along it: after 8 s held in one spot with nothing
        // moving on, 2.5 s sideways round it, alternate sides; a lamp-post she cannot reach in 20 s is left: Unsticks counts them)
        double anchorX = b.Player.X, anchorZ = b.Player.Z, anchorAt = 0, sideUntil = -1; int side = 1;
        var postTried = new Dictionary<string, double>();
        var underfoot = new Dictionary<Pickup, double>(ReferenceEqualityComparer.Instance);
        // (the gear she walks to out of a fight: Pilot.Steer's nearest within 12 m, how near she has come and since when)
        Pickup? chase = null; double chaseBest = 0, chaseSince = 0, chaseX = 0, chaseZ = 0;

        while (tt < Cap)
        {
            var p = b.Player;
            var now = zone.Now;
            if (spec.Features != null)
                foreach (var enc in new[] { zone.Night, zone.Day })
                    if (enc != null)
                        foreach (var (id, foes) in enc.Packs)
                            if (enc.S.Get(id)?.Needs != null && pocketSeen.Add(enc.Phase + id))
                            {
                                r.PocketPacks++; r.PocketFoes += foes.Count;
                                r.PocketBlocked += foes.Count(f => b.Collision.Blocked(f.E.X, f.E.Z, 0.6));
                            }
            bool held = now is Prologue.Stage.Intro or Prologue.Stage.Victory;
            bool fight = b.Enemies.Living().Any(e => e.Roused && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) < 24);
            bool close = LampRise.Crowd(b, p.X, p.Z, 10) > 0;

            // Where she goes next.
            (double X, double Z) to = (p.X, p.Z);
            var day = zone.Day;
            if (now is Prologue.Stage.Dawn or Prologue.Stage.Exit)
                to = zone.DayGoal() is { } dg ? (dg.X, dg.Z) : (gate.X, gate.Z - 8);
            else if (now == Prologue.Stage.Boss)
            {
                var w = b.Enemies.Living().FirstOrDefault(e => e.Tag == "warden" && e.State != EnemyState.Dying);
                var lit = zone.LampPosts.Where(l => l.Lit).OrderBy(l => Dist(l.X, l.Z, p.X, p.Z)).ToList();
                if (w != null && lit.Count > 0)
                {
                    // (a lit lamp between her and him: his charge breaks it, her blows reach it)
                    var l = lit[0];
                    double dx = l.X - w.X, dz = l.Z - w.Z, dl = Math.Max(0.1, Math.Sqrt(dx * dx + dz * dz));
                    to = (l.X + dx / dl * 1.6, l.Z + dz / dl * 1.6);
                }
                else if (w != null) to = (w.X, w.Z);
            }
            else if (!held)
            {
                var knight = now == Prologue.Stage.Post ? b.Enemies.Living().FirstOrDefault(e => e.Tag == "knight" && e.State != EnemyState.Dying) : null;
                var caller = now == Prologue.Stage.Barrow ? b.Enemies.Living().FirstOrDefault(e => e.Tag == "caller" && e.State != EnemyState.Dying) : null;
                var chest = zone.Interactables.FirstOrDefault(i => i.Id == "chest" && (i.When?.Invoke() ?? true) && i.Locked?.Invoke() == null);
                var g = night?.Goal(_ => true, _ => null, gate.X);
                // (a player takes the road's packs in order: the Knight waits for the packs before the post, the Caller for those before the ford)
                int Idx(string id) => night == null ? 0 : night.S.Beats.FindIndex(x => x.Id == id);
                bool packFirst(string until) => g is { For: { Kind: "pack" } gf } && Idx(gf.Id) < Idx(until) && !night!.Done(gf.Id);
                if (knight != null && packFirst("n_post")) knight = null;
                if (caller != null && packFirst("n_ford")) caller = null;
                if (g is { } ng && (ng.For == null && night!.Fighting)) to = (ng.X, ng.Z);
                else if (knight != null) to = (knight.X, knight.Z);
                else if (caller != null) to = (caller.X, caller.Z);
                else if (chest != null && now == Prologue.Stage.Post && tt - (postTried.TryGetValue("chest", out var ct) ? ct : postTried["chest"] = tt) < 25) to = (chest.X, chest.Z);
                else if (g is { For: not null } gb) to = (gb.X, gb.Z);
                else
                {
                    // (the night's beats done: down the road to the ford)
                    while (wp < road.Length - 1 && road[wp][1] > p.Z - 3) wp++;
                    to = road.Length > 0 ? (road[wp][0], road[wp][1]) : (ford.X, ford.Z + 12);
                    if (p.Z < ford.Z + 25) to = (ford.X, ford.Z + 12);
                }
            }
            // A lamp-post she passes, out of a fight: lit, as a player would.
            if (!held && !fight && now != Prologue.Stage.Boss)
                foreach (var i in zone.Interactables)
                    if (i.Id.StartsWith("lamppost:") && (i.When?.Invoke() ?? true) && Dist(i.X, i.Z, p.X, p.Z) < 14)
                    {
                        double since = postTried.TryGetValue(i.Id, out var pt) ? pt : postTried[i.Id] = tt;
                        if (tt - since < 20) { to = (i.X, i.Z); break; }
                    }
            // Her hand on what is in reach (the posts, the Watch Chest, the road lamp).
            if (!held && p.Alive && !close)
                foreach (var i in zone.Interactables.ToList())
                {
                    if (!(i.Id is "chest" or "post" || i.Id.StartsWith("lamppost:")) || i.R <= 0) continue;
                    if (!(i.When?.Invoke() ?? true) || i.Locked?.Invoke() != null || Dist(i.X, i.Z, p.X, p.Z) > i.R) continue;
                    i.Act();
                    if (i.Id != "chest") r.PostsLit++;
                }

            double mx = 0, mz = 0;
            if (!held && p.Alive)
            {
                if (human is { Idle: true })
                {
                    // (M3: the idler walks the road as its goal, and stands where a foe is in reach, stepping only out of what it read)
                    double reach = Math.Max(1.5, Pilot.Reach(b));
                    bool inReach = b.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) < reach);
                    (mx, mz) = human.Steer(b, null, goal: inReach ? null : to);
                    human.Act(b, j, mx, mz, null);
                }
                else if (human != null) { (mx, mz) = human.Steer(b, null, onward: to); human.Act(b, j, mx, mz, null); }
                else if (standing)
                {
                    // (stands and takes it while a foe is in her reach, never stepping out of a blow; else walks on to the goal)
                    double reach = Math.Max(1.5, Pilot.Reach(b));
                    bool inReach = b.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) < reach);
                    if (!inReach) (mx, mz) = Pilot.Steer(b, false, null, goal: to, naive: true);
                    Pilot.Act(b, j, mx, mz, null, lunges: false, aimsFlare: true, rooted: false, crush: false, hands: hands);
                }
                else { (mx, mz) = Pilot.Steer(b, deft, null, onward: to); Pilot.Act(b, j, mx, mz, hands: hands); }
            }

            if (Dist(p.X, p.Z, anchorX, anchorZ) > 2.5 || held) { anchorX = p.X; anchorZ = p.Z; anchorAt = tt; }
            else if (tt - anchorAt > 8 && tt - sigAt > 8 && sideUntil < tt) { sideUntil = tt + 2.5 + (r.Unsticks % 4); side = -side; anchorAt = tt; r.Unsticks++; }
            if (sideUntil > tt && p.Alive && !held)
            {
                // (sideways round the wall; every third try backs off from the goal too, a doorway behind her)
                double gx = to.X - p.X, gz = to.Z - p.Z, gl = Math.Max(0.01, Math.Sqrt(gx * gx + gz * gz));
                double fwd = r.Unsticks % 3 == 0 ? -0.7 : 0.3;
                mx = -gz / gl * side * 0.9 + gx / gl * fwd; mz = gx / gl * side * 0.9 + gz / gl * fwd;
                if (b.Collision.Blocked(p.X + mx * 0.3, p.Z + mz * 0.3, p.Radius)) { mx = -mx; mz = -mz; }
            }
            // (a full pack leaves gear lying where the bots hover over it: what she carries is dropped, as a player sells it in town)
            if (j.Ch.Pack.Count(x => x == null) < 3)
                for (int i = 0; i < j.Ch.Pack.Count; i++)
                    if (j.Ch.Pack[i] is { } it && Items.SlotFor(Items.Get(it.Def)) != null) { j.Ch.Pack[i] = null; r.Discarded++; }
            // (what she stands on 3 s and does not take, the bots' feet hover over for good: left lying, LeftLying counts it)
            foreach (var k in underfoot.Keys.Where(k => !k.Alive || Dist(k.X, k.Z, p.X, p.Z) >= 1.5).ToList()) underfoot.Remove(k);
            foreach (var k in b.Pickups.Living().Where(k => Dist(k.X, k.Z, p.X, p.Z) < 1.5).ToList())
                if ((underfoot[k] = underfoot.GetValueOrDefault(k) + dt) > 3) { underfoot.Remove(k); b.Pickups.Release(k); r.LeftLying++; }
            // (gear she walks to and comes no nearer for 10 s, out of a fight: the bots' feet slide along a wall and do not route
            // round it, so a drop that scattered past a rock's edge held her in its corner for good: left lying, LeftLying counts it)
            if (!fight && p.Alive && !held)
            {
                var near = b.Pickups.Items.Where(k => k.Alive && k.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Gold or PickupKind.Chest)
                    .MinBy(k => Dist(k.X, k.Z, p.X, p.Z));
                double nd = near == null ? 99 : Dist(near.X, near.Z, p.X, p.Z);
                if (near == null || nd >= 12) chase = null;
                else if (!ReferenceEquals(near, chase) || Dist(near.X, near.Z, chaseX, chaseZ) > 1) { chase = near; chaseBest = nd; chaseSince = tt; chaseX = near.X; chaseZ = near.Z; }
                else if (nd < chaseBest - 0.3) { chaseBest = nd; chaseSince = tt; }
                else if (tt - chaseSince > 10) { b.Pickups.Release(near); r.LeftLying++; chase = null; }
            }
            zone.Step(dt);
            b.Tick(dt, mx, mz);
            meter.Step(b, tt, dt, b.Events.Drain(), fight);
            zone.Frame(dt);
            host.Pass(dt);
            tt += dt;

            // The measures.
            p = b.Player;
            double step = Dist(p.X, p.Z, lastX, lastZ);
            if (step < 2) { r.Meters += step; if (zone.Now >= Prologue.Stage.Dawn) r.MetersDay += step; else r.MetersNight += step; }
            lastX = p.X; lastZ = p.Z;
            if (fight) r.Fighting += dt;
            if (b.Resolve.On && b.Resolve.Value >= b.Resolve.Max) r.ResolveFullSec += dt;
            if (!wasAlive && p.Alive) { r.Rises++; r.RisesAt.Add($"{zone.Now}@({p.X:0},{p.Z:0}) {LampBook.LastPost(j.World, "lowford")?.Id ?? "checkpoint"}"); }
            wasAlive = p.Alive;
            if (zone.Now != stage)
            {
                r.Stages[stage.ToString()] = r.Stages.GetValueOrDefault(stage.ToString()) + (tt - stageAt);
                if (stage is Prologue.Stage.Intro or Prologue.Stage.Victory) r.FilmFallback += tt - stageAt;
                stage = zone.Now; stageAt = tt;
                if (stage == Prologue.Stage.Boss) { r.BossReached = true; r.LevelAtWarden = j.Ch.Level; }
            }
            foreach (var enc in new[] { night, zone.Day })
                if (enc != null)
                {
                    if (Environment.GetEnvironmentVariable("ZONE_DIAG") == "2")
                        foreach (var (cid, (ce, cseed)) in enc.Champions)
                            if (ce.Roused && ce.Seed == cseed && dbg.Add(spec.Key + cid)) Console.Error.WriteLine($"{spec.Key} champion {cid} roused t={b.Time:0.0} stage {zone.Now} her ({p.X:0},{p.Z:0}) it ({ce.X:0},{ce.Z:0}) wake {ce.Wake} woke={string.Join(",", enc.WokeAt.Keys)}");
                    foreach (var (id, wt) in enc.WokeAt)
                        if (r.WokeT.TryAdd(id, wt))
                            foreach (var (cid, (ce, cseed)) in enc.Champions)
                                if (cid != id && !(id == "n_post" && cid == "knight") && ce.Alive && ce.Seed == cseed && ce.State != EnemyState.Dying && Dist(ce.X, ce.Z, p.X, p.Z) <= 25)
                                {
                                    r.ChampWakesNear.Add($"{id}@{wt:0}s by {cid}");
                                    if (ce.Roused) { r.ChampWakes.Add($"{id}@{wt:0}s by {cid}"); if (Environment.GetEnvironmentVariable("ZONE_DIAG") == "2") Console.Error.WriteLine($"{spec.Key} {id} woke t={wt:0.0} by {cid} her ({p.X:0},{p.Z:0}) it ({ce.X:0},{ce.Z:0}) {zone.Now} states {string.Join(",", enc.Packs.Where(kv => !enc.DownAt.ContainsKey(kv.Key)).Select(kv => kv.Key + ":" + enc.Standing(kv.Key).Count))}"); }
                                }
                    foreach (var (id, dt0) in enc.DownAt) r.DownT.TryAdd(id, dt0);
                }
            foreach (var enc in new[] { night, zone.Day })
                if (enc != null)
                    foreach (var (id, down) in enc.DownAt)
                        if (!r.Beats.ContainsKey(id)) { r.Beats[id] = (down - enc.WokeAt.GetValueOrDefault(id, down), j.Ch.Level); r.Packs++; }
            goldUp.RemoveWhere(k => !k.Alive || k.Kind != PickupKind.Gold);
            foreach (var k in b.Pickups.Items)
            {
                if (k.Alive && k.Kind == PickupKind.Gold && goldUp.Add(k)) r.GoldDropped += k.Value;
                if (!k.Alive || k.Payload is not ItemInstance it || !seenGear.Add(it)) continue;
                var tier = Drops.TierOf(it);
                int ti = Math.Clamp((int)tier, 0, 6);
                r.Gear[ti]++;
                if (filter.Judge(it, j.Ch) != Verdict.Hidden) r.GearShown++;
                if (Items.SlotFor(Items.Get(it.Def)) is EquipSlot slot)
                {
                    // (an upgrade worth wearing: better than the best of its place yet, worn or fallen; not put on: her stats are the run's)
                    var worn = slot == EquipSlot.Ring1 ? j.Ch.Equipment.Ring1 : j.Ch.Equipment[slot];
                    double was = best.TryGetValue(slot, out var bv) ? bv : worn != null ? Drops.Power(worn) : 0;
                    bool sameKind = Items.Get(it.Def).Kind != ItemKind.Weapon || worn == null || Items.Get(worn.Def).Weapon?.Id == Items.Get(it.Def).Weapon?.Id;
                    if (sameKind && Drops.Power(it) > was * Drops.Rules.UpgradeMargin + 0.5) { r.Upgrades++; best[slot] = Drops.Power(it); }
                }
                if (wardenDownAt >= 0 && b.Time - wardenDownAt < 20)
                {
                    r.WardenGear++;
                    r.WardenDrops.Add($"{tier} {it.Def}");
                    if (tier is LootTier.Legendary or LootTier.Storied) r.WardenLegendary = true;
                }
            }
            if (wardenDownAt >= 0) r.WardenDown = true;
            if (j.World.Fact("prologue.done").Truthy || host.TravelledTo != null) { r.Reached = true; break; }
            // Stuck: nothing moves on for five minutes (no stage, beat, kill, post or lamp).
            string s = $"{zone.Now}|{r.Packs}|{r.Kills}|{r.PostsLit}|{zone.LitCount}|{r.Rises}";
            if (s != sig) { sig = s; sigAt = tt; }
            else if (tt - sigAt > StuckAfter)
            {
                r.Stuck = true;
                var nb = (zone.Now >= Prologue.Stage.Dawn ? zone.Day : night)?.Goal(_ => true, _ => null, gate.X);
                r.StuckAt = $"{zone.Now} beat {nb?.For?.Id ?? "-"} at ({p.X:0},{p.Z:0}) goal ({to.X:0},{to.Z:0})";
                if (Environment.GetEnvironmentVariable("ZONE_DIAG") == "1")
                    Console.Error.WriteLine($"{spec.Key} PROBE her ({p.X:0.00},{p.Z:0.00}) to ({to.X:0.00},{to.Z:0.00}) herBlk45 {b.Collision.Blocked(p.X, p.Z, 0.45)} herBlk80 {b.Collision.Blocked(p.X, p.Z, 0.8)} toBlk80 {b.Collision.Blocked(to.X, to.Z, 0.8)} toBlk45 {b.Collision.Blocked(to.X, to.Z, 0.45)} clear45 {SurvivorUnchained.Sim.GroundPath.Clear(b.Collision, (p.X, p.Z), to, 0.45)} path {(SurvivorUnchained.Sim.GroundPath.Find(b.Collision, p.X, p.Z, to.X, to.Z, 0.8) is { } fp ? string.Join(" ", fp.Select(c => $"({c.X:0.0},{c.Z:0.0})")) : "none")}"); Console.Error.WriteLine($"{spec.Key} STUCK {r.StuckAt} hp {p.Hp:0}/{b.MaxHp:0} alive {p.Alive} over {b.Over} foes " + string.Join(" ", b.Enemies.Living().Where(e => Dist(e.X, e.Z, p.X, p.Z) < 30).Select(e => $"{e.Def.Id}/{e.Tag}@({e.X:0},{e.Z:0}) {e.State} R{(e.Roused ? 1 : 0)} w{e.Wake:0} hp{e.Hp:0}/{e.HpFloor:0} {e.Disposition}"))
                        + " | offers " + string.Join(" ", zone.Interactables.Where(i => i.When?.Invoke() ?? true).Select(i => $"{i.Id}@({i.X:0},{i.Z:0}) R{i.R} lock:{i.Locked?.Invoke()}")) + " | picks " + string.Join(" ", b.Pickups.Living().Where(k => Dist(k.X, k.Z, p.X, p.Z) < 13).Select(k => $"{k.Kind}:{k.Ref}@({k.X:0.0},{k.Z:0.0})p{(k.Payload != null ? 1 : 0)}")) + $" packfree {j.Ch.Pack.Count(x => x == null)}" + $" | gate {zone.Day?.GateOpen} lit {zone.LitCount} debug {string.Join(",", zone.Debug().Select(kv => kv.Key + "=" + kv.Value))}");
                break;
            }
        }
        r.Stages[stage.ToString()] = r.Stages.GetValueOrDefault(stage.ToString()) + (tt - stageAt);
        if (!r.Reached && stage is Prologue.Stage.Intro or Prologue.Stage.Victory) r.FilmFallback += tt - stageAt;
        r.Seconds = tt;
        foreach (var (k, v) in b.DamageBy) r.DamageBy[k] = v;
        r.FlareCasts = b.FlareCasts; if (b.FlareTimes.Count > 0) r.FlareFirst = b.FlareTimes[0];
        meter.Finish(b, tt, r.Measures, hands);
        r.Measures.Falls.AddRange(r.FallsAt);
        if (spec.Features != null)
            foreach (var enc in new[] { zone.Night, zone.Day })
                if (enc != null)
                    foreach (var (id, _) in enc.Packs)
                        if (enc.S.Get(id)?.Needs != null) { if (enc.DownAt.ContainsKey(id) || enc.Done(id)) r.PocketDown++; else r.PocketLeft++; }
        r.Gold = j.Ch.Gold - gold0;
        r.LevelAtGate = j.Ch.Level;
        r.Champions = r.Champion;
        if (!quiet && !r.Reached) Console.Error.WriteLine($"{spec.Key}: not through at {tt:0}s: {(r.Stuck ? "stuck " + r.StuckAt : "capped")} {zone.Now}");
        return r;
    }

    /* ------------------------------------------------------------ the report -- */

    static double Median(IEnumerable<int> xs) => Median(xs.Select(x => (double)x));

    static double Median(IEnumerable<double> xs)
    {
        var s = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s.Count % 2 == 1 ? s[s.Count / 2] : (s[s.Count / 2 - 1] + s[s.Count / 2]) / 2;
    }

    /// <summary>The films a player's hour holds (headless, their captions stand in): each file's shots summed ("dur").</summary>
    public static (double Seconds, string Said) Films()
    {
        var parts = new List<string>();
        double total = 0;
        foreach (var id in new[] { "c01", "c02", "c03", "c04a" })
        {
            using var doc = System.Text.Json.JsonDocument.Parse(DataFiles.Text("cinematics/" + id + ".json"));
            double s = doc.RootElement.GetProperty("shots").EnumerateArray().Sum(x => x.TryGetProperty("dur", out var d) ? d.GetDouble() : 0);
            total += s;
            parts.Add($"{id.ToUpperInvariant()} {s:0.0} s");
        }
        return (total, string.Join(", ", parts) + $" (godot/data/cinematics/*.json, the shots' \"dur\" summed; C04 B plays in the Waystation, not here)");
    }

    static string F(double x, string f = "0") => double.IsNaN(x) ? "-" : x.ToString(f, CultureInfo.InvariantCulture);

    public static string Report(List<ZoneRunResult> rs, string cmd)
    {
        var (film, filmSaid) = Films();
        var sb = new StringBuilder();
        sb.AppendLine("# The Low Ford: zone sim (M5-F)");
        sb.AppendLine();
        sb.AppendLine("**Today's self-firing bots; the pressing bots are M3's.** The real Prologue zone through HeadlessHost, from the Wake to the gate: the night's placed beats, the Barrow Knight, the Grave-Caller, the Ford-Warden (the films fall back to their captions headless), the dawn and the day stretch. Falls go through the zone's own OnDeath (the rise at her last lamp-post). A warden (calling) on her first weapon, no gear worn beyond the Watch Chest's jerkin (left in the pack: the bots do not dress).");
        sb.AppendLine();
        sb.AppendLine($"Command: `{cmd}`");
        sb.AppendLine();
        sb.AppendLine($"Films: {filmSaid}; **{film:0.0} s** added to each run for the with-films hour. Play-only time is the sim's seconds less the headless fallbacks that stand in for C02 and C03 (the Intro and Victory stages).");
        sb.AppendLine();
        sb.AppendLine("Kills are hers (fodder / elite / champion / boss). Packs: night and day beats put down (pack, ambush, ring). Gear: ground drops (all of it rolled: carriers, champions, the strongbox, the Warden), by tier; shown = not Hidden by the Default preset (LootFilter.Judge with the toggles on; first sightings not counted). Upgrade: a drop better than the best of its slot so far (Drops.Power over the worn piece by the upgrade margin), not worn. Fighting: a roused foe within 24 m.");
        sb.AppendLine();
        string[] order = ["human", "careless", "deft", "plain", "standing", "idler"];
        var groups = rs.GroupBy(r => (r.Spec.Tier, r.Spec.Bot)).OrderByDescending(g => g.Key.Tier).ThenBy(g => Array.IndexOf(order, g.Key.Bot)).ToList();

        sb.AppendLine("## Per bot (medians; worst case in brackets)");
        sb.AppendLine();
        sb.AppendLine("| Tier | Bot | Runs | Through | Minutes play (worst) | Minutes with films | Kills f/e/c/b | Packs | Champions | Falls (worst) | Rises | Gear C/U/R/E/Set+L | Shown | Upgrades | Gold (taken / fell) | Lv Warden / gate (lowest) | Meters | Fighting % |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var g in groups)
        {
            var l = g.ToList();
            double M(Func<ZoneRunResult, double> f) => Median(l.Select(f));
            sb.AppendLine($"| {Roman(g.Key.Tier)} | {g.Key.Bot} | {l.Count} | {l.Count(r => r.Reached)} | {F(M(r => r.PlaySeconds / 60), "0.0")} ({F(l.Max(r => r.PlaySeconds) / 60, "0.0")}) | {F(M(r => (r.PlaySeconds + film) / 60), "0.0")} | " +
                $"{F(M(r => r.Fodder))}/{F(M(r => r.Elite))}/{F(M(r => r.Champion))}/{F(M(r => r.Boss))} | {F(M(r => r.Packs))} | {F(M(r => r.Champions))} | {F(M(r => r.Falls))} ({l.Max(r => r.Falls)}) | {F(M(r => r.Rises))} | " +
                $"{F(M(r => r.Gear[0]))}/{F(M(r => r.Gear[1]))}/{F(M(r => r.Gear[2]))}/{F(M(r => r.Gear[3]))}/{F(M(r => r.Gear[4] + r.Gear[5] + r.Gear[6]))} | {F(M(r => r.GearShown))} | {F(M(r => r.Upgrades))} | {F(M(r => r.Gold))} / {F(M(r => r.GoldDropped))} | " +
                $"{F(M(r => r.LevelAtWarden))} / {F(M(r => r.LevelAtGate))} ({l.Min(r => r.LevelAtGate)}) | {F(M(r => r.Meters))} | {F(M(r => 100 * r.Fighting / Math.Max(1, r.Seconds)))} |");
        }
        sb.AppendLine();

        sb.AppendLine("## The presses (M3; medians, presses and damage shares averaged over the runs)");
        sb.AppendLine();
        sb.AppendLine(RunMeasures.Header);
        foreach (var g in groups) sb.AppendLine(RunMeasures.Row($"T{g.Key.Tier} {g.Key.Bot}", g.Select(r => r.Measures).ToList()));
        sb.AppendLine();
        sb.AppendLine("## Per hour (medians of each run's rate; play-only / with films)");
        sb.AppendLine();
        sb.AppendLine("| Tier | Bot | Kills/hr | Packs/hr | Champions/hr | Gear shown/hr | Minutes per upgrade | Rises/hr |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|");
        foreach (var g in groups)
        {
            var l = g.ToList();
            string Rate(Func<ZoneRunResult, double> f) => $"{F(Median(l.Select(r => f(r) * 3600 / r.PlaySeconds)))} / {F(Median(l.Select(r => f(r) * 3600 / (r.PlaySeconds + film))))}";
            string PerUp() => $"{F(Median(l.Select(r => r.Upgrades > 0 ? r.PlaySeconds / 60 / r.Upgrades : double.NaN)), "0.0")} / {F(Median(l.Select(r => r.Upgrades > 0 ? (r.PlaySeconds + film) / 60 / r.Upgrades : double.NaN)), "0.0")}";
            sb.AppendLine($"| {Roman(g.Key.Tier)} | {g.Key.Bot} | {Rate(r => r.Kills)} | {Rate(r => r.Packs)} | {Rate(r => r.Champions)} | {Rate(r => r.GearShown)} | {PerUp()} | {Rate(r => r.Rises)} |");
        }
        sb.AppendLine();

        // The first hour's column (7.1), tier II's human as the player.
        var t2 = rs.Where(r => r.Spec.Tier == 2).ToList();
        var hum = t2.Where(r => r.Spec.Bot == "human").ToList();
        double HR(List<ZoneRunResult> l, Func<ZoneRunResult, double> f) => Median(l.Select(r => f(r) * 3600 / (r.PlaySeconds + film)));
        sb.AppendLine("## Against ARPG.md 7.1's first hour (tier II, the human bot, per hour with films)");
        sb.AppendLine();
        sb.AppendLine("| | Target | Measured (per hour) | In this zone (one run) | Verdict |");
        sb.AppendLine("|---|---|---|---|---|");
        if (hum.Count > 0)
        {
            double kh = HR(hum, r => r.Kills), ph = HR(hum, r => r.Packs), chh = HR(hum, r => r.Champions), gh = HR(hum, r => r.GearShown);
            double up = Median(hum.Select(r => r.Upgrades > 0 ? (r.PlaySeconds + film) / 60 / r.Upgrades : double.NaN));
            sb.AppendLine($"| Kills | ~500 | {F(kh)} | {F(Median(hum.Select(r => r.Kills)))} | {(Within(kh, 500) ? "on" : kh < 500 ? "short" : "over")} |");
            sb.AppendLine($"| Packs (each with a captain) | ~40 | {F(ph)} | {F(Median(hum.Select(r => r.Packs)))} | {(Within(ph, 40) ? "on" : ph < 40 ? "short" : "over")} |");
            sb.AppendLine($"| Champions | 4-6 | {F(chh, "0.0")} | {F(Median(hum.Select(r => r.Champions)))} | {(chh >= 4 && chh <= 6 ? "on" : chh < 4 ? "short" : "over")} |");
            sb.AppendLine($"| Gear shown (Default filter) | ~25 | {F(gh)} | {F(Median(hum.Select(r => r.GearShown)))} | {(Within(gh, 25) ? "on" : gh < 25 ? "short" : "over")} |");
            sb.AppendLine($"| An upgrade worth wearing | every ~8 min | every {F(up, "0.0")} min | {F(Median(hum.Select(r => r.Upgrades)))} | {(double.IsNaN(up) ? "none" : Within(up, 8) ? "on" : up > 8 ? "rarer" : "more often")} |");
            int leg = hum.Count(r => r.WardenLegendary);
            sb.AppendLine($"| The Legendary | 1, certain, from the Ford-Warden | {leg}/{hum.Count} runs | Warden's ground gear: {F(Median(hum.Select(r => r.WardenGear)))} | {(leg == hum.Count ? "on" : "missing")} |");
            sb.AppendLine($"| Levels | 1-5 in the hour | gate level {F(Median(hum.Select(r => r.LevelAtGate)))} | | {(Within(Median(hum.Select(r => r.LevelAtGate)), 5) ? "on" : "off")} |");
            var wd = t2.SelectMany(r => r.WardenDrops).GroupBy(x => x).OrderByDescending(x => x.Count()).Select(x => $"{x.Key} x{x.Count()}").ToList();
            sb.AppendLine();
            sb.AppendLine($"The Warden's drops, all tier II runs: {(wd.Count == 0 ? "none on the ground" : string.Join(", ", wd))}.");
        }
        sb.AppendLine();

        sb.AppendLine("## The campaign gates (7.1, tier II)");
        sb.AppendLine();
        sb.AppendLine("| Gate | Measured | Verdict |");
        sb.AppendLine("|---|---|---|");
        if (hum.Count > 0)
        {
            double rh = HR(hum, r => r.Rises);
            sb.AppendLine($"| The human rises 1-3 an hour | {F(rh, "0.0")}/hr (median; runs {string.Join(",", hum.Select(r => r.Rises))}) | {(rh >= 1 && rh <= 3 ? "pass" : "fail")} |");
        }
        var df = t2.Where(r => r.Spec.Bot == "deft").ToList();
        if (df.Count > 0)
        {
            double dh = HR(df, r => r.Rises);
            sb.AppendLine($"| The deft at most once an hour | {F(dh, "0.0")}/hr (worst run {F(df.Max(r => r.Rises * 3600 / (r.PlaySeconds + film)), "0.0")}) | {(df.All(r => r.Rises * 3600 / (r.PlaySeconds + film) <= 1.0001) ? "pass" : dh <= 1 ? "pass on the median" : "fail")} |");
        }
        var st = t2.Where(r => r.Spec.Bot == "standing").ToList();
        if (st.Count > 0)
        {
            // (a champion's pack: the day's three crowned beats, the Barrow Knight's post, the Grave-Caller's barrow)
            sb.AppendLine($"| The standing bot falls to every champion pack | falls {string.Join(",", st.Select(r => r.Falls))}; fell at the Post {st.Count(r => r.FallsAt.Any(f => f.StartsWith("Post")))}/{st.Count}, the Barrow {st.Count(r => r.FallsAt.Any(f => f.StartsWith("Barrow")))}/{st.Count}, by day {st.Count(r => r.FallsAt.Any(f => f.StartsWith("Exit") || f.StartsWith("Dawn")))}/{st.Count} | {(st.All(r => r.Falls >= 5) ? "pass" : "fail")} (5 champions: a fall each needs 5+) |");
        }
        if (hum.Count > 0)
        {
            double lv = Median(hum.Select(r => r.LevelAtGate)), gh = HR(hum, r => r.GearShown), kh = HR(hum, r => r.Kills);
            sb.AppendLine($"| Levels within ±20% (level 5 by the hour's end) | gate level {F(lv)} | {(Within(lv, 5) ? "pass" : "fail")} |");
            sb.AppendLine($"| Drops within ±20% (~25 shown an hour) | {F(gh)}/hr | {(Within(gh, 25) ? "pass" : "fail")} |");
            sb.AppendLine($"| (kills within ±20%, ~500 an hour) | {F(kh)}/hr | {(Within(kh, 500) ? "pass" : "fail")} |");
        }
        sb.AppendLine();

        if (hum.Count > 0)
        {
            double mins = Median(hum.Select(r => (r.PlaySeconds + film) / 60));
            sb.AppendLine($"**Read the rates with the zone's length:** the whole Low Ford plays in about {mins:0.0} minutes (with films), so every per-hour rate is that run scaled by about {60 / mins:0.0}x. One rise in a run reads as {60 / mins:0.0} an hour, so the rise gates cannot pass or fail fairly until the first hour is an hour of ground (see The ground). Per run, the totals (kills, packs, champions, gear, level 5 at the gate) are the numbers to set against the table's first hour: today's zone gives the first hour's levels and champions in an eighth of its time, and about a third of its kills, packs and gear.");
            sb.AppendLine();
            sb.AppendLine("Gold: the bots take only what they walk over (the coins are not pulled to her by day); the column gives what she took and what fell.");
            sb.AppendLine();
        }
        // The ground.
        sb.AppendLine("## The ground");
        sb.AppendLine();
        var meta = ZoneMeta.Load("lowford");
        var road = meta.Paths.GetValueOrDefault("ROAD") ?? Array.Empty<double[]>();
        double roadLen = 0;
        for (int i = 1; i < road.Length; i++) roadLen += Dist(road[i][0], road[i][1], road[i - 1][0], road[i - 1][1]);
        var spec = Encounters.For("lowford")!;
        var feats = rs.Select(r => r.Spec.Features).FirstOrDefault(f => f != null);
        int nightPacks = spec.In("night", feats).Count(x => x.Kind is "pack" or "ambush" or "ring"), dayPacks = spec.In("day", feats).Count(x => x.Kind is "pack" or "ambush" or "ring");
        // The zone's route as its goals walk it: the camp, the night's beats in order, the ford; the day's start, its beats in order
        // (the strongbox and the road lamp with them), the gate.
        var camp = meta.Place("LOWFORD", "camp"); var fordAt = meta.Place("LOWFORD", "ford"); var gateAt = meta.Place("LOWFORD", "gate");
        double Leg(IEnumerable<(double X, double Z)> pts) { var l = pts.ToList(); double s = 0; for (int i = 1; i < l.Count; i++) s += Dist(l[i].X, l[i].Z, l[i - 1].X, l[i - 1].Z); return s; }
        double routeN = Leg(new[] { (camp.X, camp.Z) }.Concat(spec.In("night", feats).Select(x => (x.X, x.Z))).Append((fordAt.X, fordAt.Z)));
        double routeD = Leg(new[] { (spec.From[0], spec.From[1]) }.Concat(spec.In("day", feats).Select(x => (x.X, x.Z))).Append((gateAt.X, gateAt.Z)));
        double route = routeN + routeD;
        if (hum.Count > 0)
        {
            double mN = Median(hum.Select(r => r.MetersNight)), mD = Median(hum.Select(r => r.MetersDay)), m = mN + mD;
            double playMin = Median(hum.Select(r => (r.PlaySeconds + film) / 60));
            int packs = nightPacks + dayPacks;
            double density = packs / route * 100;
            double for40 = 40 / density * 100, for45 = route * 45 / playMin;
            sb.AppendLine($"- The route (the goals' walk: the camp, the night's {spec.In("night", feats).Count()} beats, the ford; the day's start, its {spec.In("day", feats).Count()} beats, the gate): **{routeN:0} m by night + {routeD:0} m by day = {route:0} m**. (The meta's ROAD path, the camp to the ford: {roadLen:0} m.)");
            sb.AppendLine($"- Walked by the human bot (tier II median), fights' footwork included: {mN:0} m by night, {mD:0} m by day, {m:0} m in all ({m / route:0.0}x the route).");
            sb.AppendLine($"- Packs placed: {nightPacks} by night, {dayPacks} by day, {packs} in all: **{density:0.0} packs per 100 m of route** ({nightPacks * 100.0 / routeN:0.0} by night, {dayPacks * 100.0 / routeD:0.0} by day).");
            sb.AppendLine($"- The first hour's ~40 packs at today's density: **{for40:0} m** of route ({for40 - route:+0;-0} m, {40 - packs:+0;-0} packs more than today).");
            sb.AppendLine($"- The zone at about 45 minutes: today it plays in {playMin:0.0} min with films ({route / playMin:0} m of route a minute, everything in it). At today's pace and density, 45 minutes is **{for45:0} m** of route ({for45 / route:0.0}x today, {for45 - route:+0;-0} m more), holding **{for45 * density / 100:0} packs** ({for45 * density / 100 - packs:+0;-0} more).");
            sb.AppendLine($"- So ~40 packs fill about {40.0 / packs * playMin:0} minutes at today's pace; the extra minutes to 45 are walking, films, towns' worth of story, or denser fights (bigger packs, more per beat).");
        }
        sb.AppendLine();

        sb.AppendLine("## Seconds per beat (median; woke to down) and her level at its fall (median)");
        sb.AppendLine();
        var beats = spec.In("night", feats).Concat(spec.In("day", feats)).Where(x => x.Kind is "pack" or "ambush" or "ring").Select(x => x.Id).ToList();
        sb.AppendLine("| Beat | " + string.Join(" | ", groups.Select(g => $"{Roman(g.Key.Tier)} {g.Key.Bot}")) + " |");
        sb.AppendLine("|---|" + string.Concat(groups.Select(_ => "---|")));
        foreach (var id in beats)
            sb.AppendLine($"| {id} | " + string.Join(" | ", groups.Select(g =>
            {
                var bs = g.Where(r => r.Beats.ContainsKey(id)).Select(r => r.Beats[id]).ToList();
                return bs.Count == 0 ? "-" : $"{F(Median(bs.Select(x => x.Seconds)))} s, L{F(Median(bs.Select(x => (double)x.Level)))}";
            })) + " |");
        string[] stages = ["Wake", "Rising", "Road", "Ambush", "Road2", "Post", "Barrow", "ToFord", "Intro", "Boss", "Victory", "Dawn", "Exit"];
        foreach (var s in stages)
            sb.AppendLine($"| stage {s} | " + string.Join(" | ", groups.Select(g => $"{F(Median(g.Select(r => r.Stages.GetValueOrDefault(s, double.NaN))))} s")) + " |");
        sb.AppendLine();
        sb.AppendLine("## Quiet between beats (median seconds from the previous beat's down to this beat's wake; negative = woke before the last fell)");
        sb.AppendLine();
        sb.AppendLine("| Beat (after the one before it in the data) | " + string.Join(" | ", groups.Select(g => $"{Roman(g.Key.Tier)} {g.Key.Bot}")) + " |");
        sb.AppendLine("|---|" + string.Concat(groups.Select(_ => "---|")));
        for (int bi = 1; bi < beats.Count; bi++)
        {
            string cur = beats[bi], prev = beats[bi - 1];
            sb.AppendLine($"| {cur} (after {prev}) | " + string.Join(" | ", groups.Select(g =>
            {
                var q = g.Where(r => r.WokeT.ContainsKey(cur) && r.DownT.ContainsKey(prev)).Select(r => r.WokeT[cur] - r.DownT[prev]).ToList();
                return q.Count == 0 ? "-" : $"{F(Median(q), "0.0")} s ({q.Count})";
            })) + " |");
        }
        sb.AppendLine();
        sb.AppendLine("Pack wakes while a champion (not its own pack's, nor the Knight at its own escort) lived within 25 m of her and was **awake** (the count that matters): " + string.Join("; ", groups.Select(g =>
            $"{Roman(g.Key.Tier)} {g.Key.Bot}: {g.Sum(r => r.ChampWakes.Count)} in {g.Count()} runs" + (g.Any(r => r.ChampWakes.Count > 0) ? " (" + string.Join(", ", g.SelectMany(r => r.ChampWakes).GroupBy(x => x.Split('@')[0] + " by " + x.Split(' ')[^1]).Select(x => $"{x.Key} x{x.Count()}")) + ")" : ""))) + ".");
        sb.AppendLine();
        sb.AppendLine("The same counting a champion that is still resting (the Knight asleep at the post 12 m from n_road2, for one): " + string.Join("; ", groups.Select(g => $"{Roman(g.Key.Tier)} {g.Key.Bot}: {g.Sum(r => r.ChampWakesNear.Count)}")) + ".");
        sb.AppendLine();

        if (feats != null)
        {
            var pr = rs.Where(r => r.Spec.Features != null && r.Spec.Bot == "human").ToList();
            sb.AppendLine("## Pockets preview (features forced on: " + string.Join(", ", feats) + ")");
            sb.AppendLine();
            sb.AppendLine("PREVIEW ONLY: the ground is not there, the pockets' positions are provisional. Per run, human bot:");
            sb.AppendLine();
            sb.AppendLine("| Seed | Pocket packs placed | Pocket foes | Foes landed blocked | Packs put down | Packs left standing | Kills | Minutes | Meters | Stuck |");
            sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|");
            foreach (var r in pr.OrderBy(r => r.Spec.Seed))
                sb.AppendLine($"| {r.Spec.Seed} | {r.PocketPacks} | {r.PocketFoes} | {r.PocketBlocked} | {r.PocketDown} | {r.PocketLeft} | {r.Kills} | {(r.PlaySeconds + film) / 60:0.0} | {r.Meters:0} | {(r.Stuck ? "yes" : "no")} |");
            sb.AppendLine();
        }
        sb.AppendLine("## Falls, rises and runs that did not get through");
        sb.AppendLine();
        foreach (var g in groups)
        {
            var falls = g.SelectMany(r => r.FallsAt).Select(f => f.Split('@')[0]).GroupBy(x => x).Select(x => $"{x.Key} {x.Count()}");
            var rises = g.SelectMany(r => r.RisesAt).Select(f => f.Split(' ').Last()).GroupBy(x => x).Select(x => $"{x.Key} {x.Count()}");
            sb.AppendLine($"- {Roman(g.Key.Tier)} {g.Key.Bot}: falls by stage: {string.Join(", ", falls.DefaultIfEmpty("none"))}; risen at: {string.Join(", ", rises.DefaultIfEmpty("none"))}.");
            foreach (var r in g.Where(r => !r.Reached)) sb.AppendLine($"  - s{r.Spec.Seed}: {(r.Stuck ? "stuck: " + r.StuckAt : "capped at 60 min")} (after {r.Seconds / 60:0.0} min)");
        }
        return sb.ToString();
    }

    static bool Within(double x, double target) => !double.IsNaN(x) && x >= target * 0.8 && x <= target * 1.2;
    static string Roman(int t) => t switch { 1 => "I", 2 => "II", 3 => "III", 4 => "IV", _ => t.ToString() };
}
