using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.World;

/* Paths across a zone: roads, ruts, streams.
 *
 * Written by hand as a few key points, then made to wander (nothing that
 * water or wheels made runs dead straight for thirty metres), and indexed
 * on a grid so the terrain builder can ask "how far to the stream, and how
 * far along it" a million times without walking every segment. */

public static class Paths
{
    /// <summary>Wander between key points: the path still passes through every
    /// key, but swings side to side between them in two overlapping waves.</summary>
    public static List<(double X, double Z)> Meander(IReadOnlyList<(double X, double Z)> keys, double amp, double step = 2.5, double seed = 0)
    {
        var o = new List<(double, double)>();
        double run = 0;
        for (int i = 0; i < keys.Count - 1; i++)
        {
            var (ax, az) = keys[i];
            var (bx, bz) = keys[i + 1];
            double l = Math.Sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az));
            int n = Math.Max(1, (int)Math.Ceiling(l / step));
            double nx = -(bz - az) / l, nz = (bx - ax) / l;
            for (int k = 0; k < n; k++)
            {
                double t = (double)k / n, s = run + t * l;
                // Pinned at the keys, free in between.
                double pin = Math.Sin(Math.PI * t);
                double off = amp * pin * (Math.Sin(s * 0.21 + seed) * 0.65 + Math.Sin(s * 0.37 + seed * 2.3) * 0.35);
                o.Add((ax + (bx - ax) * t + nx * off, az + (bz - az) * t + nz * off));
            }
            run += l;
        }
        o.Add(keys[^1]);
        return o;
    }
}

/// <summary>Nearest point on a path, fast: exact within `reach`, the
/// key-point outline beyond (close enough for "is this far from the water").</summary>
public sealed class PathIndex
{
    readonly Dictionary<long, List<int>> cells = new();
    readonly List<double> runs = new();
    public readonly IReadOnlyList<(double X, double Z)> Pts;
    readonly double reach, cell;
    readonly IReadOnlyList<(double X, double Z)>? coarse;
    public readonly double Length;

    public PathIndex(IReadOnlyList<(double X, double Z)> pts, double reach = 14, double cell = 8, IReadOnlyList<(double X, double Z)>? coarse = null)
    {
        Pts = pts;
        this.reach = reach;
        this.cell = cell;
        this.coarse = coarse;
        double run = 0;
        for (int i = 0; i < pts.Count - 1; i++)
        {
            runs.Add(run);
            var (ax, az) = pts[i];
            var (bx, bz) = pts[i + 1];
            run += Math.Sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az));
            int x0 = (int)Math.Floor((Math.Min(ax, bx) - reach) / cell), x1 = (int)Math.Floor((Math.Max(ax, bx) + reach) / cell);
            int z0 = (int)Math.Floor((Math.Min(az, bz) - reach) / cell), z1 = (int)Math.Floor((Math.Max(az, bz) + reach) / cell);
            for (int cx = x0; cx <= x1; cx++)
                for (int cz = z0; cz <= z1; cz++)
                {
                    long k = Key(cx, cz);
                    if (!cells.TryGetValue(k, out var list)) cells[k] = list = new List<int>();
                    list.Add(i);
                }
        }
        Length = run;
    }

    static long Key(int cx, int cz) => (long)(cx + 2048) * 4096 + (cz + 2048);

    /// <summary>Distance to the path, and how far along it the nearest point lies.</summary>
    public (double D, double S) Nearest(double x, double z)
    {
        double best = double.PositiveInfinity, bestS = 0;
        if (cells.TryGetValue(Key((int)Math.Floor(x / cell), (int)Math.Floor(z / cell)), out var list))
            foreach (var i in list)
            {
                var (ax, az) = Pts[i];
                var (bx, bz) = Pts[i + 1];
                double dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
                double t = l2 > 0 ? Math.Max(0, Math.Min(1, ((x - ax) * dx + (z - az) * dz) / l2)) : 0;
                double d = MathX.Len(x - ax - dx * t, z - az - dz * t);
                if (d < best) { best = d; bestS = runs[i] + t * Math.Sqrt(l2); }
            }
        if (best <= reach) return (best, bestS);
        return (Math.Max(reach, Far(x, z)), bestS);
    }

    public double Dist(double x, double z) => Nearest(x, z).D;

    double Far(double x, double z)
    {
        var p = coarse ?? Pts;
        double d = double.PositiveInfinity;
        for (int i = 0; i < p.Count - 1; i++) d = Math.Min(d, MathX.DistToSegment(x, z, p[i].X, p[i].Z, p[i + 1].X, p[i + 1].Z));
        return d;
    }
}
