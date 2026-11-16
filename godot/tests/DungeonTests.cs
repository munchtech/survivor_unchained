using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Maps;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Seeded dungeons (Maps/DungeonGen.cs, MapGen's dungeon branch).</summary>
public class DungeonTests
{
    readonly ITestOutputHelper _out;
    public DungeonTests(ITestOutputHelper o) { _out = o; }

    static MapBuild Make(string id, int seed) => MapGen.Generate(new MapSpec { Seed = seed, Dungeon = id, Tier = 1, Night = false });

    static bool NearNav(SurvivorUnchained.Sim.CollisionWorld c, HashSet<int> reached, double x, double z)
    {
        for (double r = 0; r <= 1.5; r += 0.5)
            for (int k = 0; k < (r == 0 ? 1 : 16); k++)
            {
                double a = k * Math.PI / 8;
                if (reached.Contains(MapGenTests.NavCell(c, x + Math.Cos(a) * r, z + Math.Sin(a) * r))) return true;
            }
        return false;
    }

    static string Line(string name, List<double> v) => $"{name}: min {v.Min():0.##} mean {v.Average():0.##} max {v.Max():0.##}";

    [Theory]
    [InlineData("hollow")]
    [InlineData("roost")]
    public void Every_seed_lays_a_dungeon_that_can_be_walked_from_door_to_ruler(string id)
    {
        var sigs = new HashSet<string>(); var graphs = new HashSet<string>();
        var rooms = new List<double>(); var route = new List<double>(); var branches = new List<double>();
        var loops = new List<double>(); var packs = new List<double>(); var caches = new List<double>();
        for (int seed = 1; seed <= 50; seed++)
        {
            var m = Make(id, seed);
            string w = $"{id} seed {seed}";
            var d = m.Dungeon; Assert.NotNull(d);
            Assert.Equal(AreaKind.Start, m.Areas[0].Kind);
            Assert.Equal(AreaKind.Boss, m.Areas[^1].Kind);
            var reached = MapGenTests.Flood(m);
            Assert.True(reached.Contains(MapGenTests.Cell(m, m.Boss.X, m.Boss.Z)), $"{w}: ruler cut off");
            Assert.True(reached.Contains(MapGenTests.Cell(m, d!.Exit.X, d.Exit.Z)), $"{w}: exit cut off");
            foreach (var c in d.Caches) Assert.True(reached.Contains(MapGenTests.Cell(m, c.X, c.Z)), $"{w}: cache in area {c.Area} cut off");
            foreach (var p in m.Packs) Assert.True(reached.Contains(MapGenTests.Cell(m, p.X, p.Z)), $"{w}: pack at {p.X:0},{p.Z:0} cut off");
            foreach (var r in d.Rooms)
            {
                bool any = false;
                double reach = r.Plan.Reach * r.Scale + 2;
                for (int x = (int)(r.X - reach); x <= r.X + reach && !any; x++)
                    for (int z = (int)(r.Z - reach); z <= r.Z + reach && !any; z++)
                        if (r.Dist(x, z) < -1.5 && reached.Contains(MapGenTests.Cell(m, x, z))) any = true;
                Assert.True(any, $"{w}: room {r.Area} ({r.Plan.Id}) has no ground reached");
            }
            var col = m.Meta.Collision();
            var nav = MapGenTests.NavFlood(col, m.Start.X, m.Start.Z);
            Assert.True(NearNav(col, nav, m.Boss.X, m.Boss.Z), $"{w}: ruler cut off for the fight's paths");
            Assert.True(NearNav(col, nav, d.Exit.X, d.Exit.Z), $"{w}: exit cut off for the fight's paths");
            foreach (var c in d.Caches) Assert.True(NearNav(col, nav, c.X, c.Z), $"{w}: cache in area {c.Area} cut off for the fight's paths");
            foreach (var p in m.Packs) Assert.True(m.CanStand(p.X, p.Z), $"{w}: pack at {p.X:0},{p.Z:0} in the walls");
            Assert.InRange(m.Meta.Colliders.Count, 50, 4000);
            sigs.Add(d.Signature); graphs.Add(d.Graph);
            rooms.Add(d.Rooms.Count); route.Add(d.Route.Count); branches.Add(d.Rooms.Count(r => !r.OnRoute));
            loops.Add(d.Edges.Count(e => e.Loop)); packs.Add(m.Packs.Count); caches.Add(d.Caches.Count);
        }
        _out.WriteLine($"MEASURED {id}: signatures {sigs.Count}, graphs {graphs.Count}");
        foreach (var (n, v) in new[] { ("rooms", rooms), ("route", route), ("branches", branches), ("loops", loops), ("packs", packs), ("caches", caches) })
            _out.WriteLine("MEASURED " + Line(n, v));
        Assert.Equal(50, sigs.Count);
        Assert.True(graphs.Count >= GraphFloor, $"{graphs.Count} graphs");
        Assert.InRange(rooms.Min(), RoomsLo, 99); Assert.InRange(rooms.Max(), 0, RoomsHi);
        Assert.InRange(route.Min(), 8, 99); Assert.InRange(route.Max(), 0, 10);
        Assert.InRange(branches.Min(), BranchLo, 99); Assert.InRange(branches.Max(), 0, BranchHi);
        Assert.InRange(packs.Min(), PackLo, 9999); Assert.InRange(packs.Max(), 0, PackHi);
        Assert.InRange(caches.Min(), 2, 99); Assert.InRange(caches.Max(), 0, CacheHi);
    }

    // Measured over seeds 1..50 (both dungeons): rooms 9-16, branches 2-7, packs 19-50, caches 2-4, 50 distinct graphs; bands +-15%.
    const int GraphFloor = 45, RoomsLo = 8, RoomsHi = 20, BranchLo = 1, BranchHi = 8, PackLo = 16, PackHi = 64, CacheHi = 5;

    [Fact]
    public void The_same_seed_lays_the_same_dungeon_and_another_seed_another()
    {
        var a = Make("hollow", 9); var b = Make("hollow", 9);
        Assert.Equal(a.Dungeon!.Signature, b.Dungeon!.Signature);
        Assert.Equal(a.Packs.Count, b.Packs.Count);
        Assert.NotEqual(Make("hollow", 1).Dungeon!.Signature, Make("hollow", 2).Dungeon!.Signature);
        Assert.NotEqual(Make("roost", 1).Dungeon!.Signature, Make("roost", 2).Dungeon!.Signature);
    }

    [Theory]
    [InlineData("hollow", 3)]
    [InlineData("hollow", 17)]
    [InlineData("roost", 5)]
    public void A_deft_bot_clears_a_dungeon(string id, int seed)
    {
        var def = DungeonGen.Get(id)!;
        var r = SurvivorUnchained.Balance.MapSim.Play(new SurvivorUnchained.Balance.MapRunSpec(seed, "warden", 1, def.People, id == "roost" ? 7 : 6, 1, [], "deft", 25, id));
        _out.WriteLine($"{id} {seed}: {r.Minutes:0.0} min, packs {r.PacksCleared}/{r.Packs}, items {r.Items}, falls {r.Falls}");
        Assert.True(r.Cleared, $"{id} seed {seed} not cleared (closed {r.Closed}, falls {r.Falls}, packs {r.PacksCleared}/{r.Packs})");
    }
    /// <summary>(Ledge view, 15 Nov) Where a wall is a drop follows what the play camera sees (data/content/ledge.json "edges"): the
    /// den's banks rise and stop a foe, only its pits drop; the ravine's back cliff stops it and its near and side edges drop.</summary>
    [Theory]
    [InlineData(1)]
    [InlineData(7)]
    [InlineData(23)]
    public void A_dungeons_drops_are_where_its_view_falls_away(int seed)
    {
        var den = Make("hollow", seed);
        var walls = den.Meta.Colliders.Where(c => c.Tag == "wall").ToList();
        Assert.Contains(walls, c => !c.Drop);
        var holes = den.Dungeon!.Rooms.SelectMany(r => r.Holes).ToList();
        foreach (var c in walls.Where(c => c.Drop))
            Assert.True(holes.Any(h => h.Dist(c.X, c.Z) < 1.5 + Math.Max(c.Hw, c.Hd)), $"hollow {seed}: a drop at ({c.X:0},{c.Z:0}) is no pit");
        var ravine = Make("roost", seed);
        var rw = ravine.Meta.Colliders.Where(c => c.Tag == "wall").ToList();
        double dropA = rw.Where(c => c.Drop).Sum(c => c.Hw * c.Hd), riseA = rw.Where(c => !c.Drop).Sum(c => c.Hw * c.Hd);
        _out.WriteLine($"seed {seed}: hollow drops {walls.Count(c => c.Drop)} of {walls.Count}; roost drop area {dropA * 4:0} m2, cliff {riseA * 4:0} m2");
        Assert.True(dropA > 0 && riseA > 0, "the ravine has both its drops and its cliff");
        // The cliff stands at the back: every rising box has walkable ground to its south (toward the lens), none to its north.
        var walk = ravine.Walkable; int res = (int)Math.Round(Math.Sqrt(walk.Length)), half = res / 2;
        bool W(double x, double z) { int i = (int)Math.Round(x) + half, j = (int)Math.Round(z) + half; return i >= 0 && j >= 0 && i < res && j < res && walk[j * res + i]; }
        int faced = 0, total = 0;
        foreach (var c in rw.Where(c => !c.Drop))
        {
            bool south = false, north = false;
            for (double x = c.X - c.Hw; x <= c.X + c.Hw; x += 1) { south |= W(x, c.Z + c.Hd + 1); north |= W(x, c.Z - c.Hd - 1); }
            if (south || north) total++;
            if (south && !north) faced++;
        }
        _out.WriteLine($"roost {seed}: cliff boxes on the way {total}, from the back {faced}");
        Assert.True(faced >= total * 0.6, $"roost {seed}: {faced} of {total} cliff boxes face the lens from the back");
    }
}
