using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using SurvivorUnchained.Maps;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Maps made from seeds (Maps/MapGen.cs).</summary>
public class MapGenTests
{
    [Theory]
    [InlineData(1)]
    [InlineData(7)]
    [InlineData(42)]
    [InlineData(1234)]
    [InlineData(99991)]
    public void A_map_can_be_walked_from_its_start_to_its_boss(int seed)
    {
        var sw = Stopwatch.StartNew();
        var m = MapGen.Generate(new MapSpec { Seed = seed, Tier = 1 });
        sw.Stop();
        Assert.True(sw.ElapsedMilliseconds < 4000, $"made in {sw.ElapsedMilliseconds} ms");
        Assert.Equal(9, m.Areas.Count);
        Assert.Equal(AreaKind.Start, m.Start.Kind);
        Assert.Equal(AreaKind.Boss, m.Boss.Kind);
        Assert.Equal(2, m.Altars.Count());
        Assert.True(m.CanStand(m.Start.X, m.Start.Z));
        Assert.True(m.CanStand(m.Boss.X, m.Boss.Z));
        // Every clearing is reached from the start, on foot.
        var reached = Flood(m);
        foreach (var a in m.Areas) Assert.True(reached.Contains(Cell(m, a.X, a.Z)), $"area {a.Index} ({a.Kind}) cut off");
        // Packs stand where they can be reached, many of them.
        Assert.True(m.Packs.Count >= 30, $"{m.Packs.Count} packs");
        foreach (var p in m.Packs) Assert.True(m.CanStand(p.X, p.Z), $"a pack at {p.X:0},{p.Z:0} in the trees");
        // The walls hold: a few thousand colliders at most.
        Assert.InRange(m.Meta.Colliders.Count, 50, 4000);
        Assert.True(m.Flora.Count > 2000, $"{m.Flora.Count} flora");
        if (Environment.GetEnvironmentVariable("MAP_DUMP") is { } dir) Dump(m, $"{dir}/map_{seed}.ppm");
    }

    [Fact]
    public void The_same_seed_makes_the_same_map()
    {
        var a = MapGen.Generate(new MapSpec { Seed = 5 });
        var b = MapGen.Generate(new MapSpec { Seed = 5 });
        Assert.Equal(a.Areas, b.Areas);
        Assert.Equal(a.Packs, b.Packs);
        Assert.Equal(a.Ground.Heights, b.Ground.Heights);
    }

    static int Cell(MapBuild m, double x, double z) =>
        (int)Math.Round(z + MapGen.Size / 2) * m.Meta.Res + (int)Math.Round(x + MapGen.Size / 2);

    static HashSet<int> Flood(MapBuild m)
    {
        int res = m.Meta.Res;
        var seen = new HashSet<int>();
        var todo = new Queue<int>();
        int s = Cell(m, m.Start.X, m.Start.Z);
        seen.Add(s); todo.Enqueue(s);
        while (todo.Count > 0)
        {
            int k = todo.Dequeue();
            int i = k % res, j = k / res;
            foreach (var (di, dj) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int ni = i + di, nj = j + dj;
                if (ni < 0 || nj < 0 || ni >= res || nj >= res) continue;
                int n = nj * res + ni;
                if (m.Walkable[n] && seen.Add(n)) todo.Enqueue(n);
            }
        }
        return seen;
    }

    /// <summary>A picture of the layout (MAP_DUMP=dir): walkable ground,
    /// packs, clearings, the walls' boxes.</summary>
    static void Dump(MapBuild m, string path)
    {
        int res = m.Meta.Res;
        var px = new byte[res * res * 3];
        for (int k = 0; k < res * res; k++)
        {
            byte v = m.Walkable[k] ? (byte)170 : (byte)30;
            px[k * 3] = px[k * 3 + 1] = px[k * 3 + 2] = v;
        }
        void Dot(double x, double z, int r, byte R, byte G, byte B)
        {
            for (int dz = -r; dz <= r; dz++)
                for (int dx = -r; dx <= r; dx++)
                {
                    int i = (int)Math.Round(x + MapGen.Size / 2) + dx, j = (int)Math.Round(z + MapGen.Size / 2) + dz;
                    if (i < 0 || j < 0 || i >= res || j >= res) continue;
                    int k = (j * res + i) * 3;
                    px[k] = R; px[k + 1] = G; px[k + 2] = B;
                }
        }
        foreach (var c in m.Meta.Colliders.Where(c => c.Tag == "wall"))
            for (double z = c.Z - c.Hd; z < c.Z + c.Hd; z += 1)
                for (double x = c.X - c.Hw; x < c.X + c.Hw; x += 1) Dot(x + 0.5, z + 0.5, 0, 90, 50, 40);
        foreach (var t in m.Flora.Where(t => t.Kind is "pine" or "broadleaf" or "autumn" or "dead")) Dot(t.X, t.Z, 0, 20, 80, 30);
        foreach (var p in m.Packs) Dot(p.X, p.Z, 1, 220, 40, 40);
        foreach (var a in m.Areas) Dot(a.X, a.Z, 2, a.Kind == AreaKind.Boss ? (byte)255 : (byte)40, a.Kind == AreaKind.Altar ? (byte)200 : (byte)120, 255);
        using var f = System.IO.File.Create(path);
        var head = System.Text.Encoding.ASCII.GetBytes($"P6\n{res} {res}\n255\n");
        f.Write(head);
        f.Write(px);
    }
}

/// <summary>A map, run without a screen (Play/Zones/MapRun.cs).</summary>
public class MapRunTests
{
    sealed record Setup(SurvivorUnchained.Play.Journey J, FakeHost Host, SurvivorUnchained.Play.Zones.MapRun Zone, SurvivorUnchained.Sim.Battle B, MapBuild Map);

    static Setup Make(string people = "pack", params string[] oaths)
    {
        var a = SurvivorUnchained.Rpg.Callings.Archetype("warden");
        var j = SurvivorUnchained.Play.Journey.Begin(new SurvivorUnchained.Rpg.CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0], StartBoon = SurvivorUnchained.Content.Boons.StartBlessings[0],
        }, 42);
        var offer = new MapOffer(new MapSpec { Seed = 42, Tier = 1, Name = "The Test Wood", Oaths = oaths.ToList() }, people);
        MapOffers.Remember(j.World, offer);
        var map = MapGen.Generate(offer.Spec);
        var host = new FakeHost(j, map.Meta, map.Ground);
        var zone = new SurvivorUnchained.Play.Zones.MapRun(host, map, people);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, map);
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.Zone.Step(1 / 60.0);
            s.Zone.Frame(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Host.Pass(1 / 60.0);
        }
    }

    [Fact]
    public void Packs_wait_until_you_come_to_them()
    {
        var s = Make();
        Assert.Contains(s.Host.Tracked, t => t.Id == "map");
        Run(s, 1);
        int near = s.B.Enemies.Living().Count();
        // Walk to the far clearing (the boss's): what was there is waiting, and more woke on the way.
        var mid = s.Map.Areas[4];
        s.B.Player.X = mid.X; s.B.Player.Z = mid.Z;
        Run(s, 1);
        Assert.True(s.B.Enemies.Living().Count() > near, $"{near} -> {s.B.Enemies.Living().Count()}");
    }

    [Fact]
    public void An_altar_calls_waves_and_its_hoard_is_yours_when_they_are_spent()
    {
        var s = Make();
        var altar = s.Map.Altars.First();
        s.B.Player.X = altar.X; s.B.Player.Z = altar.Z;
        s.B.Player.Iframes = 1e9;
        var wake = s.Zone.Interactables.First(i => i.Id == $"altar{altar.Index}");
        Assert.True(wake.When!());
        wake.Act();
        Assert.False(wake.When!());
        Run(s, 3);
        Assert.Contains(s.Host.Announced, a => a.Title.StartsWith("Wave 1"));
        // Everything it calls, struck down, wave after wave.
        for (int k = 0; k < 40 && !s.Host.Announced.Any(a => a.Title == "The altar is spent"); k++)
        {
            foreach (var e in s.B.Enemies.Living().ToList()) s.B.HitEnemy(e, 1e6, SurvivorUnchained.Sim.School.Physical, [SurvivorUnchained.Sim.Tag.Physical]);
            Run(s, 2);
        }
        Assert.Contains(s.Host.Announced, a => a.Title == "The altar is spent");
    }

    [Fact]
    public void Killing_what_rules_the_map_takes_it_and_opens_the_way_home()
    {
        var s = Make("dead");
        var boss = s.Map.Boss;
        s.B.Player.X = boss.X; s.B.Player.Z = boss.Z + boss.R;
        s.B.Player.Iframes = 1e9;
        Run(s, 1);
        Assert.NotNull(s.Host.Boss);
        var exit = s.Zone.Interactables.Single(i => i.Id == "exit");
        Assert.False(exit.When!());
        var lord = s.B.Enemies.Living().Single(e => e.Def.Id == "barrow_knight");
        s.B.HitEnemy(lord, 1e7, SurvivorUnchained.Sim.School.Holy, [SurvivorUnchained.Sim.Tag.Physical]);
        Run(s, 3);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "Map complete");
        // What rules a map keeps a manual: an art the survivor has not learned.
        var manual = s.B.Pickups.Living().FirstOrDefault(p => p.Ref?.StartsWith("manual_") == true);
        Assert.NotNull(manual);
        Assert.False(SurvivorUnchained.Rpg.ArtBook.Knows(s.J.Ch, manual!.Ref![7..]));
        Assert.True(exit.When!());
        Assert.Equal(1, s.J.World.Fact("map.best").Number);
        exit.Act();
        Assert.Equal("waystation", s.Host.Travelled?.Zone);
    }
}
