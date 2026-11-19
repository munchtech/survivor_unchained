using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The den (hollow dungeon) has spots she cannot walk out of (a pocket between colliders narrower than her 0.84 m body).
/// A spot nobody can enter is harmless; one she can walk or dash into, from the start, would hold her there for good.
/// Reach is simulated the way the sim moves her: walking (5 m/s, Resolve each 1/60 s tick) and dashing (5.5 m in 0.2 s,
/// Resolve over gaps), on a 0.25 m grid flood from the start.</summary>
public class DenTrapTests
{
    readonly ITestOutputHelper _out;
    public DenTrapTests(ITestOutputHelper o) { _out = o; }

    const double R = 0.42, Speed = 5, Dt = 1 / 60.0, Cell = 0.25;
    const double DashSpeed = 5.5 / 0.2;

    static (double x, double z) Move(CollisionWorld cw, double x, double z, double dx, double dz, double sp, int ticks, bool gaps)
    {
        for (int s = 0; s < ticks; s++) { x += dx * sp * Dt; z += dz * sp * Dt; cw.Resolve(ref x, ref z, R, true, gaps); }
        return (x, z);
    }

    /// <summary>How far she can get from a spot by walking, or walking and dashing.</summary>
    static double Escape(CollisionWorld cw, double x0, double z0, bool dash)
    {
        double best = 0;
        for (int k = 0; k < 16; k++)
        {
            double a = k * Math.PI / 8, dx = Math.Cos(a), dz = Math.Sin(a);
            var (x, z) = Move(cw, x0, z0, dx, dz, Speed, 40, false);
            best = Math.Max(best, Math.Sqrt((x - x0) * (x - x0) + (z - z0) * (z - z0)));
            if (dash)
            {
                (x, z) = Move(cw, x0, z0, dx, dz, DashSpeed, 12, true);
                best = Math.Max(best, Math.Sqrt((x - x0) * (x - x0) + (z - z0) * (z - z0)));
            }
            if (best >= 0.5) return best; // free: nothing more to learn
        }
        return best;
    }

    public record Result(int Seed, int Spots, int WalkIn, int DashIn, List<string> Notes);

    public static Dictionary<long, (double x, double z)> Flood(CollisionWorld cw, double sx, double sz, bool dash)
    {
        double b = cw.Bound;
        int n = (int)(2 * b / Cell) + 3;
        long Key(double x, double z) => (long)Math.Round((x + b) / Cell) * n + (long)Math.Round((z + b) / Cell);
        var seen = new Dictionary<long, (double, double)>();
        var q = new Queue<(double x, double z)>();
        cw.Resolve(ref sx, ref sz, R, true);
        seen[Key(sx, sz)] = (sx, sz); q.Enqueue((sx, sz));
        while (q.Count > 0)
        {
            var (x, z) = q.Dequeue();
            for (int k = 0; k < 8; k++)
            {
                double a = k * Math.PI / 4, dx = Math.Cos(a), dz = Math.Sin(a);
                var p = Move(cw, x, z, dx, dz, Speed, 3, false);
                if (seen.TryAdd(Key(p.x, p.z), p)) q.Enqueue(p);
                if (!dash) continue;
                p = Move(cw, x, z, dx, dz, DashSpeed, 12, true);
                if (seen.TryAdd(Key(p.x, p.z), p)) q.Enqueue(p);
            }
        }
        return seen;
    }

    public static Result Analyse(int seed)
    {
        var hollow = DungeonGen.Get("hollow")!;
        var chart = Chart.ForDungeon(hollow, seed, 6);
        var map = MapGen.Generate(chart.Map);
        var cw = map.Meta.Collision();
        double b = cw.Bound;
        var spots = new List<(double x, double z)>();
        for (double x = -b; x <= b; x += 0.5)
            for (double z = -b; z <= b; z += 0.5)
            {
                if (((int)Math.Round(x * 2) + (int)Math.Round(z * 2)) % 2 != 0) continue;
                double px = x, pz = z;
                if (cw.Resolve(ref px, ref pz, R, true)) continue;
                if (Escape(cw, px, pz, false) < 0.5) spots.Add((px, pz));
            }
        var walk = Flood(cw, map.Meta.Start.X, map.Meta.Start.Z, false);
        var both = Flood(cw, map.Meta.Start.X, map.Meta.Start.Z, true);
        bool Near(Dictionary<long, (double x, double z)> f, (double x, double z) s) =>
            f.Values.Any(p => Math.Abs(p.x - s.x) < 0.3 && Math.Abs(p.z - s.z) < 0.3 && Escape(cw, p.x, p.z, true) < 0.5);
        Assert.True(walk.Count > 2000, $"seed {seed}: the flood from the start must cover the den (got {walk.Count} cells)");
        int w = 0, d = 0; var notes = new List<string>();
        foreach (var s in spots)
        {
            bool inW = Near(walk, s), inB = Near(both, s);
            if (inW) w++;
            if (inB) d++;
            if (inB && notes.Count < 10) notes.Add($"({s.x:0.0},{s.z:0.0}) walk {inW} walk+dash {inB}");
        }
        return new Result(seed, spots.Count, w, d, notes);
    }

    [Theory]
    [InlineData(1, 30)]
    public void NoTrapIsReachable(int from, int to)
    {
        int bad = 0;
        for (int seed = from; seed <= to; seed++)
        {
            var r = Analyse(seed);
            _out.WriteLine($"seed {r.Seed}: spots {r.Spots} reachableByWalk {r.WalkIn} reachableByWalkOrDash {r.DashIn}");
            foreach (var n in r.Notes) _out.WriteLine("   " + n);
            bad += r.DashIn;
        }
        Assert.Equal(0, bad);
    }
}
