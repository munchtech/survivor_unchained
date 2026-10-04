using System;
using System.Collections.Generic;
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
        // (No clock here: a busy machine made a 1 s map take 6. The work is bounded by what is made,
        // below: sixteen clearings, a few thousand colliders, the flora.)
        var m = MapGen.Generate(new MapSpec { Seed = seed, Tier = 1 });
        Assert.Equal(16, m.Areas.Count);
        Assert.Equal(AreaKind.Start, m.Start.Kind);
        Assert.Equal(AreaKind.Boss, m.Boss.Kind);
        Assert.Equal(3, m.Altars.Count());
        Assert.True(m.CanStand(m.Start.X, m.Start.Z));
        Assert.True(m.CanStand(m.Boss.X, m.Boss.Z));
        // Every clearing is reached from the start, on foot.
        var reached = Flood(m);
        foreach (var a in m.Areas) Assert.True(reached.Contains(Cell(m, a.X, a.Z)), $"area {a.Index} ({a.Kind}) cut off");
        // And for the fight's own paths (trees, boulders and walls as the creatures meet them).
        var col = m.Meta.Collision();
        var navReached = NavFlood(col, m.Start.X, m.Start.Z);
        foreach (var a in m.Areas) Assert.True(navReached.Contains(NavCell(col, a.X, a.Z)), $"area {a.Index} ({a.Kind}) cut off for the fight's paths");
        // Packs stand where they can be reached, many of them.
        Assert.True(m.Packs.Count >= 30, $"{m.Packs.Count} packs");
        foreach (var p in m.Packs) Assert.True(m.CanStand(p.X, p.Z), $"a pack at {p.X:0},{p.Z:0} in the trees");
        // The walls hold: a few thousand colliders at most.
        Assert.InRange(m.Meta.Colliders.Count, 50, 4000);
        Assert.True(m.Flora.Count > 2000, $"{m.Flora.Count} flora");
        if (Environment.GetEnvironmentVariable("MAP_DUMP") is { } dir) Dump(m, $"{dir}/map_{seed}.ppm");
    }

    [Theory]
    [InlineData(3)]
    [InlineData(77)]
    public void An_arena_is_one_great_clearing_with_cover(int seed)
    {
        var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true });
        Assert.Equal("arena", m.Meta.Id);
        Assert.Single(m.Areas);
        Assert.Empty(m.Packs);
        Assert.True(m.CanStand(0, 0));
        // Wide: open ground a long way out in every direction.
        for (int k = 0; k < 8; k++)
        {
            double a = k * Math.PI / 4;
            Assert.True(m.CanStand(Math.Cos(a) * 60, Math.Sin(a) * 60), $"closed at 60 m, {k * 45} degrees");
        }
        Assert.False(m.CanStand(140, 0));
        // Cover inside, and every bit of open ground reached from the middle.
        var col = m.Meta.Collision();
        int inside = m.Meta.Colliders.Count(c => c.Tag != "wall" && Math.Sqrt(c.X * c.X + c.Z * c.Z) < MapGen.ArenaR - 12);
        Assert.InRange(inside, 20, 120);
        var reached = NavFlood(col, 0, 0);
        int open = 0, cut = 0;
        for (int z = -70; z <= 70; z += 5)
            for (int x = -70; x <= 70; x += 5)
            {
                if (!m.CanStand(x, z) || col.Blocked(x, z, 0.5)) continue;
                open++;
                if (!reached.Contains(NavCell(col, x, z))) cut++;
            }
        Assert.True(cut <= open / 50, $"{cut} of {open} cut off");
    }

    [Theory]
    [InlineData("dead", "halloween/grave")]
    [InlineData("kerchiefs", "props/")]
    [InlineData("lamplings", "halloween/lantern_standing")]
    public void An_arena_is_dressed_as_its_people_keep_it(string people, string piece)
    {
        var m = MapGen.Generate(new MapSpec { Seed = 5, Arena = true, People = people });
        Assert.Contains(m.Pieces, p => p.Id.StartsWith(piece));
        // Lit where they keep a light (the ember's ring is lit all round), and every
        // piece stands inside the edge or, a landmark, just past it.
        Assert.True(m.Meta.Lights.Count > 12);
        Assert.All(m.Pieces, p => Assert.True(Math.Sqrt(p.X * p.X + p.Z * p.Z) < ArenaPlaceTests.Edge(m, p.X, p.Z) + 8, $"{p.Id} at {p.X:0},{p.Z:0}"));
        // The Pack's wood has bare trees for cover, not full crowns.
        var wood = MapGen.Generate(new MapSpec { Seed = 5, Arena = true, People = "pack" });
        Assert.DoesNotContain(wood.Flora, f => f.Kind is "pine" or "broadleaf" or "autumn" && Math.Sqrt(f.X * f.X + f.Z * f.Z) < MapGen.ArenaR - 14);
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

    static int NavCell(SurvivorUnchained.Sim.CollisionWorld c, double x, double z) =>
        (int)Math.Floor(z + c.Half) * c.NavSize + (int)Math.Floor(x + c.Half);

    static HashSet<int> NavFlood(SurvivorUnchained.Sim.CollisionWorld c, double x, double z)
    {
        int n = c.NavSize;
        var seen = new HashSet<int>();
        var todo = new Queue<int>();
        int s0 = NavCell(c, x, z);
        seen.Add(s0); todo.Enqueue(s0);
        while (todo.Count > 0)
        {
            int k = todo.Dequeue();
            int i = k % n, j = k / n;
            foreach (var (di, dj) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                int ni = i + di, nj = j + dj;
                if (c.IsNavBlocked(ni, nj)) continue;
                if (seen.Add(nj * n + ni)) todo.Enqueue(nj * n + ni);
            }
        }
        return seen;
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
