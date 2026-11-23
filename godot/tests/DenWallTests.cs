using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(den-wall; the owner, 22 Nov: "strongboxes load in before they appear causing an invisible wall." / "in the den" /
/// "basically the box spawns after some event it looks like, like clearing a wave. but its "there" even before you do you just
/// cant open it and it blocks you") She walks the den's event room before, during and after the event; every step where she is
/// stopped or pushed is logged with what held her and whether the den draws it.</summary>
[Collection("Balance")]
public class DenWallTests
{
    readonly ITestOutputHelper log;
    public DenWallTests(ITestOutputHelper log) { this.log = log; }

    const double Dt = 1 / 60.0;

    static (MapRun Zone, Battle B, HeadlessHost Host, MapBuild Map) Den(int seed, int level = 9)
    {
        var chart = Chart.ForDungeon(DungeonGen.Get("hollow")!, seed * 7919 + 1, level);
        var j = MapSim.Survivor("warden", level, 2, seed);
        var map = MapGen.Generate(chart.Map);
        var host = new HeadlessHost(j, seed);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, worldTier: false);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        var zh = zone.Hooks;
        b.Hooks.OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && j.PickedUp(p);
        host.Battle = b;
        zone.Begin(b);
        return (zone, b, host, map);
    }

    /// <summary>What a static piece is, as the den draws it: its wall mesh, a pit, a prop of the set, or nothing drawn
    /// (flora: the den grows none, ZoneView.cs "The den grows nothing under its roof").</summary>
    static string Seen(MapBuild map, Collider c)
    {
        if (c.Tag == "wall") return "wall";
        if (c.Falls) return "pit";
        double reach = c.Kind == ColliderKind.Circle ? c.R : Math.Max(c.Hw, c.Hd);
        var prop = map.Props.Where(p => MathX.Dist(p.X, p.Z, c.X, c.Z) < reach + 0.3).Select(p => p.Id).FirstOrDefault();
        if (prop != null) return "prop:" + prop;
        var fl = map.Flora.Where(f => MathX.Dist(f.X, f.Z, c.X, c.Z) < reach + 0.3).Select(f => f.Kind).FirstOrDefault();
        if (fl != null && DungeonDef.GrowsFlora(map.Dungeon?.Def.Theme)) return "flora:" + fl;
        return fl != null ? "UNDRAWN flora:" + fl : "UNDRAWN none";
    }

    static double Gap(Collider c, double x, double z)
    {
        if (c.Kind == ColliderKind.Circle) return MathX.Dist(x, z, c.X, c.Z) - c.R;
        double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
        double lx = (x - c.X) * cos - (z - c.Z) * sin, lz = (x - c.X) * sin + (z - c.Z) * cos;
        double qx = Math.Clamp(lx, -c.Hw, c.Hw), qz = Math.Clamp(lz, -c.Hd, c.Hd);
        return Math.Sqrt((lx - qx) * (lx - qx) + (lz - qz) * (lz - qz));
    }

    sealed record Stop(string Phase, double X, double Z, double Made, string What);

    /// <summary>One walk across the room: from a point to another, her keys held on it; every step made less than half of
    /// what she asked (past the start's ramp) or pushed sideways by more than half is a stop, with what touched her.</summary>
    static void Walk(MapRun zone, Battle b, HeadlessHost host, MapBuild map, double x0, double z0, double x1, double z1, List<Stop> stops, Func<string> phase, bool stepZone, bool spareKeepers = false)
    {
        var p = b.Player;
        p.X = x0; p.Z = z0; p.Vx = p.Vz = 0;
        if (b.Collision.Blocked(x0, z0, p.Radius)) return;   // a start inside a piece: not a walk
        double len = MathX.Dist(x0, z0, x1, z1), ux = (x1 - x0) / len, uz = (z1 - z0) / len;
        double t = 0;
        while (t < len / 3 + 3)
        {
            p.Hp = b.MaxHp; p.Iframes = 1;
            // (a clearing hand: a drawn foe that reaches her is put down, so what is left is what she walks into)
            foreach (var e in b.Enemies.Items)
                if (e.Alive && !(spareKeepers && e.Named != null) && e.State is not (EnemyState.Dying or EnemyState.Burrowed or EnemyState.Rising or EnemyState.Surfacing) && MathX.Dist(e.X, e.Z, p.X, p.Z) < 4)
                    b.KillEnemy(e, true, null);
            double wx = p.X, wz = p.Z;
            if (stepZone) { zone.Step(Dt); zone.Frame(Dt); }
            b.Tick(Dt, ux, uz);
            host.Pass(Dt);
            b.Events.Drain();
            t += Dt;
            string now = phase();
            double asked = b.Stats.Get(Stat.MoveSpeed) * Dt, dx = p.X - wx, dz = p.Z - wz;
            double made = dx * ux + dz * uz, side = Math.Abs(-dx * uz + dz * ux);
            if ((p.X - x0) * ux + (p.Z - z0) * uz >= len) break;
            if (t < 0.25 || p.RootT > 0 || p.CastT > 0) continue;
            if (made >= 0.5 * asked && side <= 0.5 * asked) continue;
            var what = new List<string>();
            double mx = x0 + ux * len / 2, mz = z0 + uz * len / 2;
            foreach (var c in b.Collision.All())
                if (Gap(c, p.X, p.Z) < p.Radius + 0.06) what.Add($"piece {c.Kind} r{c.R:0.0} {MathX.Dist(c.X, c.Z, mx, mz):0.0} m from the altar{(c.PlayerOnly ? " playerOnly" : "")}{(c.Soft ? " soft" : "")} [{Seen(map, c)}]");
            foreach (var e in b.Enemies.Items)
                if (e.Alive && MathX.Dist(e.X, e.Z, p.X, p.Z) < p.Radius + e.Radius + 0.06)
                    what.Add($"foe {e.Def.Id} {e.State} elite {e.Elite}{(e.State is EnemyState.Burrowed ? " UNDRAWN" : "")}");
            foreach (var k in b.Pickups.Items)
                if (k.Alive && MathX.Dist(k.X, k.Z, p.X, p.Z) < 1.2) what.Add($"pickup {k.Kind}");
            if (what.Count == 0) what.Add($"none found (slow {p.SlowF:0.00})");
            stops.Add(new Stop(now, p.X, p.Z, made / asked, string.Join("; ", what)));
        }
    }

    /// <summary>The rule, over the whole den: every solid piece is a wall, a pit, or a thing the den draws on it (seeds 1-30).
    /// Before the fix the altar's six ring stones failed it on every seed (flora the den never draws).</summary>
    [Fact]
    public void Nothing_solid_in_the_den_goes_undrawn()
    {
        var bad = new List<string>();
        int pieces = 0;
        for (int seed = 1; seed <= 30; seed++)
        {
            var chart = Chart.ForDungeon(DungeonGen.Get("hollow")!, seed * 7919 + 1, 9);
            var map = MapGen.Generate(chart.Map);
            foreach (var c in map.Meta.Collision().All())
            {
                pieces++;
                if (Seen(map, c) is { } w && w.StartsWith("UNDRAWN")) bad.Add($"seed {seed}: {c.Kind} r {c.R:0.0} at ({c.X:0.0},{c.Z:0.0}) [{w}]");
            }
        }
        log.WriteLine($"{pieces} solid pieces over 30 dens, {bad.Count} undrawn");
        Assert.True(bad.Count == 0, $"{bad.Count} undrawn solid pieces, e.g. {string.Join(" | ", bad.Take(4))}");
    }

    /// <summary>(item 4) The den's caches and its hoard (laid at the start, MapRun.Begin) on open, standing ground: no solid piece
    /// within her reach of the spot and no drop under it (seeds 1-30). Their reach from the way is DungeonTests' own.</summary>
    [Fact]
    public void The_den_caches_and_hoard_lie_open()
    {
        var bad = new List<string>();
        int n = 0;
        for (int seed = 1; seed <= 30; seed++)
        {
            var chart = Chart.ForDungeon(DungeonGen.Get("hollow")!, seed * 7919 + 1, 9);
            var map = MapGen.Generate(chart.Map);
            var col = map.Meta.Collision();
            foreach (var c in map.Dungeon!.Caches)
            {
                n++;
                if (col.Blocked(c.X, c.Z, 0.42 + 0.5) || col.InDrop(c.X, c.Z) || !map.CanStand(c.X, c.Z))
                    bad.Add($"seed {seed}: {(c.Rich ? "hoard" : "cache")} at ({c.X:0.0},{c.Z:0.0}) blocked {col.Blocked(c.X, c.Z, 0.92)} drop {col.InDrop(c.X, c.Z)} stand {map.CanStand(c.X, c.Z)}");
            }
        }
        log.WriteLine($"{n} caches and hoards over 30 dens, {bad.Count} not open");
        Assert.True(bad.Count == 0, string.Join(" | ", bad.Take(5)));
    }

    /// <summary>The owner's walk: she crosses the event room's altar on twelve lines before anything is set down (seeds 1-3);
    /// nothing she cannot see holds her. Before the fix: 30-36 held steps a seed, all on the ring's undrawn stones.</summary>
    [Theory]
    [InlineData(1)] [InlineData(2)] [InlineData(3)]
    public void She_crosses_the_den_altar_held_by_nothing_unseen(int seed)
    {
        var (zone, b, host, map) = Den(seed);
        var alt = map.Altars.First();
        var stops = new List<Stop>();
        for (int k = 0; k < 12; k++)
        {
            double a = k * Math.PI / 6 + 0.13;
            Walk(zone, b, host, map, alt.X + Math.Cos(a) * 9, alt.Z + Math.Sin(a) * 9, alt.X - Math.Cos(a) * 9, alt.Z - Math.Sin(a) * 9, stops, () => "before", false);
        }
        var un = stops.Where(s => s.What.Contains("UNDRAWN")).ToList();
        log.WriteLine($"seed {seed}: {stops.Count} held steps, {un.Count} by an undrawn thing");
        Assert.True(un.Count == 0, $"{un.Count} steps held by an undrawn thing, e.g. {un.FirstOrDefault()?.What}");
    }

    /// <summary>The probe (DENWALL_PROBE=1, measuring only): the event room walked before, with its keepers up, during the event
    /// and after, every held step logged with what held her. `dotnet test --filter DenWallTests.Probe` with the env set.</summary>
    [Theory]
    [InlineData(1)] [InlineData(2)] [InlineData(3)] [InlineData(4)] [InlineData(5)] [InlineData(6)]
    public void Probe_the_den_event_room(int seed)
    {
        if (Environment.GetEnvironmentVariable("DENWALL_PROBE") != "1") return;
        var (zone, b, host, map) = Den(seed);
        var alt = map.Altars.First();
        var room = map.Dungeon!.Rooms.First(r => r.Role == RoomRole.Event);
        log.WriteLine($"seed {seed}: altar ({alt.X:0.0},{alt.Z:0.0}) R {alt.R:0.0}; room {room.Plan.Id} at ({room.X:0.0},{room.Z:0.0})");
        foreach (var c in b.Collision.All().Where(c => MathX.Dist(c.X, c.Z, alt.X, alt.Z) < 12 && c.Tag != "wall" && !c.Falls))
            log.WriteLine($"  piece #{c.Id} {c.Kind} r {c.R:0.0} {MathX.Dist(c.X, c.Z, alt.X, alt.Z):0.0} m from the altar: {Seen(map, c)}");
        var stops = new List<Stop>();
        bool on = false, done = false, boxed = false;
        string Phase()
        {
            if (b.Charges.Spikes) on = true; else if (on) done = true;
            boxed |= b.Pickups.Items.Any(k => k.Alive && k.Kind == PickupKind.Chest && MathX.Dist(k.X, k.Z, alt.X, alt.Z) < 1);
            return done ? "after" : on ? "during" : b.Enemies.Items.Any(e => e.Alive && e.Named != null) ? "keepers" : "before";
        }
        void Lines(bool stepZone, bool spare = false)
        {
            for (int k = 0; k < 12; k++)
            {
                double a = k * Math.PI / 6 + 0.13;
                Walk(zone, b, host, map, alt.X + Math.Cos(a) * 9, alt.Z + Math.Sin(a) * 9, alt.X - Math.Cos(a) * 9, alt.Z - Math.Sin(a) * 9, stops, Phase, stepZone, spare);
            }
        }
        // Before: twelve lines across the altar, 9 m out to 9 m out, nothing set down yet (the zone not stepped).
        Lines(false);
        // Its keepers up (set down as she nears): the lines again, the keepers spared.
        Lines(true, spare: true);
        foreach (var e in b.Enemies.Items.Where(e => e.Alive && e.Named != null)) log.WriteLine($"  keeper {e.Def.Id} {e.State} {MathX.Dist(e.X, e.Z, alt.X, alt.Z):0.0} m from the altar");
        // Its keepers set down and put down: the altar lit, the event on.
        var p = b.Player;
        p.X = alt.X + 5; p.Z = alt.Z;
        for (int i = 0; i < 30 && !b.Charges.Spikes; i++)
        {
            zone.Step(Dt); zone.Frame(Dt); b.Tick(Dt, 0, 0); host.Pass(Dt); b.Events.Drain();
            foreach (var e in b.Enemies.Items.Where(e => e.Alive && e.Named != null && e.State != EnemyState.Dying).ToList()) b.KillEnemy(e, true, null);
        }
        log.WriteLine($"  event on: {b.Charges.Spikes}");
        // During, then after: lines again until the box is out, then once more.
        for (int round = 0; round < 12 && !done; round++) Lines(true);
        log.WriteLine($"  event done: {done}, box seen: {boxed}, at {b.Time:0} s");
        Lines(true);
        foreach (var ph in new[] { "before", "keepers", "during", "after" })
        {
            var at = stops.Where(s => s.Phase == ph).ToList();
            var un = at.Where(s => s.What.Contains("UNDRAWN")).ToList();
            log.WriteLine($"  {ph}: {at.Count} stopped steps, {un.Count} by an undrawn thing, {at.Count(s => s.What.StartsWith("none"))} by nothing found");
            foreach (var g in un.GroupBy(s => s.What)) log.WriteLine($"    x{g.Count()} min made {g.Min(s => s.Made):0.00}: {g.Key}");
            if (Environment.GetEnvironmentVariable("DENWALL_ALL") == "1") foreach (var g in at.Except(un).GroupBy(s => s.What)) log.WriteLine($"    (seen) x{g.Count()}: {g.Key}");
        }
    }
}
