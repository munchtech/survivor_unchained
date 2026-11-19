using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Notches: two solid pieces standing closer than her body is wide (0.84 m), one behind the other's face, make a
/// V she walks into and cannot slide out of while she holds the way she was going (the owner, 18 Nov: "got stuck
/// approaching the wagon in tutorial"; the wagon's south end and its tipped barrel, 0.77 m apart, Low Ford 3.3, 58.4).
/// Her walk is Battle's: a step at her pace, then Collision.Resolve. A spot is a notch when a held heading leaves her
/// within 0.3 m of where she was after 3 s and she is against two pieces whose faces turn more than 60 degrees apart
/// (one flat face square on is not a notch: she slides along it once she turns a hair).</summary>
public class WalkNotchTests
{
    readonly ITestOutputHelper _out;
    public WalkNotchTests(ITestOutputHelper o) { _out = o; }

    const double R = 0.42, Speed = 5, Dt = 1 / 60.0;

    /// <summary>The outward normal of a piece at her centre if she touches it (null: clear of it).</summary>
    static (double X, double Z)? Contact(Collider c, double x, double z)
    {
        if (c.Kind == ColliderKind.Circle)
        {
            double dx = x - c.X, dz = z - c.Z, d = Math.Sqrt(dx * dx + dz * dz);
            return d < c.R + R + 0.03 && d > 1e-6 ? (dx / d, dz / d) : null;
        }
        double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
        double lx = (x - c.X) * cos - (z - c.Z) * sin, lz = (x - c.X) * sin + (z - c.Z) * cos;
        double qx = Math.Clamp(lx, -c.Hw, c.Hw), qz = Math.Clamp(lz, -c.Hd, c.Hd);
        double ex = lx - qx, ez = lz - qz, e = Math.Sqrt(ex * ex + ez * ez);
        if (e >= R + 0.03 || e < 1e-6) return null;
        double nx = ex / e, nz = ez / e, wc = Math.Cos(c.Rot), ws = Math.Sin(c.Rot);
        return (nx * wc - nz * ws, nx * ws + nz * wc);
    }

    /// <summary>Every notch in a stretch of the zone: (where she stopped, the heading), one per stopping place.</summary>
    static List<(double X, double Z, int Heading)> Notches(CollisionWorld cw, double x0, double x1, double z0, double z1, double step, Func<double, double, bool>? where = null)
    {
        var all = cw.All().Where(c => !c.Gap).ToList();
        var ext = all.Select(c => c.R + Math.Max(c.Hw, c.Hd) + R + 0.9).ToArray();
        var found = new List<(double X, double Z, int Heading)>();
        for (double x = x0; x <= x1; x += step)
            for (double z = z0; z <= z1; z += step)
            {
                if (where != null && !where(x, z)) continue;
                // (a notch needs two pieces within reach: skip open ground at once)
                int near = 0;
                for (int i = 0; i < all.Count && near < 2; i++)
                    if (Math.Abs(all[i].X - x) < ext[i] && Math.Abs(all[i].Z - z) < ext[i]) near++;
                if (near < 2) continue;
                double sx = x, sz = z;
                if (cw.Resolve(ref sx, ref sz, R, true)) continue;
                for (int k = 0; k < 16; k++)
                {
                    double a = k * Math.PI / 8, dx = Math.Cos(a), dz = Math.Sin(a), px = sx, pz = sz, lx = px, lz = pz;
                    for (int s = 0; s < 180; s++)
                    {
                        if (s == 120) { lx = px; lz = pz; }
                        px += dx * Speed * Dt; pz += dz * Speed * Dt;
                        cw.Resolve(ref px, ref pz, R, true);
                    }
                    // (stopped: the last second of the walk went nowhere)
                    if (Math.Sqrt((px - lx) * (px - lx) + (pz - lz) * (pz - lz)) > 0.05) continue;
                    var ns = all.Where(c => Math.Abs(c.X - px) < c.R + Math.Max(c.Hw, c.Hd) + 1.5 && Math.Abs(c.Z - pz) < c.R + Math.Max(c.Hw, c.Hd) + 1.5)
                        .Select(c => Contact(c, px, pz)).OfType<(double X, double Z)>().ToList();
                    bool notch = false;
                    for (int i = 0; i < ns.Count && !notch; i++)
                        for (int j = i + 1; j < ns.Count; j++)
                            if (ns[i].X * ns[j].X + ns[i].Z * ns[j].Z < 0.5) { notch = true; break; }
                    if (notch && !found.Any(f => Math.Abs(f.X - px) < 0.3 && Math.Abs(f.Z - pz) < 0.3)) found.Add((px, pz, k));
                }
            }
        return found;
    }

    /// <summary>Low Ford's ROAD (zone.json paths), the line she walks from the camp (z 90) to the exit (z -104).</summary>
    static readonly (double X, double Z)[] Road = { (-2, 88), (1, 70), (8, 52), (10, 36), (4, 18), (-3, 2), (-2, -16), (2, -30), (0, -44), (-1, -60), (2, -78), (0, -96), (0, -104) };

    static double RoadDist(double x, double z)
    {
        double best = 1e9;
        for (int i = 0; i + 1 < Road.Length; i++)
        {
            var (ax, az) = Road[i]; var (bx, bz) = Road[i + 1];
            double dx = bx - ax, dz = bz - az, t = Math.Clamp(((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz), 0, 1);
            best = Math.Min(best, Math.Sqrt((x - ax - t * dx) * (x - ax - t * dx) + (z - az - t * dz) * (z - az - t * dz)));
        }
        return best;
    }

    /// <summary>The whole prologue walk, start to the zone exit: everywhere within 20 m of the road (the camp, the post,
    /// the barrow and crypt, the ford all lie inside it), no notch anywhere (the owner, 18 Nov; playtest-bugs-2: four
    /// more off the road west of the wagon).</summary>
    [Fact]
    public void The_whole_Low_Ford_walk_has_no_notch()
    {
        var cw = ZoneMeta.Load("lowford").Collision();
        var n = Notches(cw, -35, 35, -104, 92, 0.25, (x, z) => RoadDist(x, z) < 20).Where(f => f.Z > -104).ToList();
        foreach (var f in n) _out.WriteLine($"notch ({f.X:0.00},{f.Z:0.00}) heading {f.Heading * 22.5:0}");
        Assert.Empty(n);
    }

    [Fact]
    public void The_wagon_on_the_Low_Ford_road_has_no_notch()
    {
        var cw = ZoneMeta.Load("lowford").Collision();
        var n = Notches(cw, 0, 10, 53, 67, 0.25).Where(f => f.X is > 0 and < 10 && f.Z is > 53 and < 67).ToList();
        foreach (var f in n) _out.WriteLine($"notch ({f.X:0.00},{f.Z:0.00}) heading {f.Heading * 22.5:0}");
        Assert.Empty(n);
    }

    /// <summary>Walking north up the road (W held, a little either way), she gets past the wagon or slides along it:
    /// never stopped dead against its end (the probe's line, held at 3.29, 58.41 for four minutes before the fix).</summary>
    [Fact]
    public void Holding_north_past_the_wagon_she_never_stops_dead()
    {
        var cw = ZoneMeta.Load("lowford").Collision();
        var stops = new List<string>();
        for (double x = 0; x <= 8; x += 0.25)
            for (int deg = -40; deg <= 40; deg += 5)
            {
                double a = deg * Math.PI / 180, dx = Math.Sin(a), dz = -Math.Cos(a), px = x, pz = 64, lx = px, lz = pz;
                cw.Resolve(ref px, ref pz, R, true);
                for (int s = 0; s < 300; s++)
                {
                    if (s == 240) { lx = px; lz = pz; }
                    px += dx * Speed * Dt; pz += dz * Speed * Dt;
                    cw.Resolve(ref px, ref pz, R, true);
                }
                if (pz > 52 && Math.Sqrt((px - lx) * (px - lx) + (pz - lz) * (pz - lz)) < 0.05)
                {
                    // (one flat face square on is not a stop: she turns a hair and slides; a V is)
                    var ns = cw.All().Select(c => Contact(c, px, pz)).OfType<(double X, double Z)>().ToList();
                    if (ns.Count >= 2 && ns.Any(p => ns.Any(q => p.X * q.X + p.Z * q.Z < 0.5))) stops.Add($"from x {x:0.00} heading {deg} stopped at ({px:0.00},{pz:0.00})");
                }
            }
        foreach (var s in stops.Take(20)) _out.WriteLine(s);
        Assert.Empty(stops);
    }
}
