using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Sim;

/* Static geometry the fight happens around, and how the horde gets around it.
 *
 * Colliders are circles (trunks, rocks, posts) and oriented boxes (walls,
 * houses, wagons). Movers are circles; Resolve pushes a mover out of
 * whatever it overlaps so it slides along walls instead of sticking.
 *
 * The flow field is what lets two hundred creatures find their way around a
 * forest to you without two hundred path searches: one flood from the
 * survivor's cell across a window of the navigation grid, whenever the
 * survivor changes cell, and each creature reads the downhill direction
 * under its feet.
 *
 * Colliders can be tagged and removed at runtime (a bramble wall burned
 * away, a gate opened), which rebakes the navigation grid locally. */

public enum ColliderKind { Circle, Box }

public sealed class Collider
{
    public int Id;
    public ColliderKind Kind;
    public double X, Z;
    /// <summary>Circle radius, or bounding radius for a box.</summary>
    public double R;
    /// <summary>Box half-width, half-depth, rotation (radians).</summary>
    public double Hw, Hd, Rot;
    public string? Tag;
    /// <summary>Blocks movement but not projectiles (a hedge, a fence).</summary>
    public bool Soft;
    /// <summary>Blocks the survivor only (an invisible edge of the zone).</summary>
    public bool PlayerOnly;
}

public readonly record struct RayHit(double T, Collider Collider);

/// <summary>Options for a new collider.</summary>
public readonly record struct ColliderOpts(string? Tag = null, bool Soft = false, bool PlayerOnly = false);

public sealed class CollisionWorld
{
    public readonly double Size, Half;
    readonly double bucket;
    readonly Dictionary<int, Collider> colliders = new();
    readonly Dictionary<long, List<int>> buckets = new();
    int nextId = 1;
    public const double NavCell = 1;
    public readonly int NavSize;
    public byte[] NavBlocked;
    /// <summary>Playable bounds (square, centred).</summary>
    public double Bound;
    readonly List<Collider> scratch = new();
    readonly HashSet<int> seen = new();

    public CollisionWorld(double size, double bucket = 6)
    {
        Size = size;
        this.bucket = bucket;
        Half = size / 2;
        Bound = Half - 2;
        NavSize = (int)Math.Ceiling(size / NavCell);
        NavBlocked = new byte[NavSize * NavSize];
    }

    static long BKey(int bx, int bz) => (long)bz * 4096 + bx;

    void BucketsFor(Collider c, Action<long> fn)
    {
        int b0x = (int)Math.Floor((c.X - c.R + Half) / bucket), b1x = (int)Math.Floor((c.X + c.R + Half) / bucket);
        int b0z = (int)Math.Floor((c.Z - c.R + Half) / bucket), b1z = (int)Math.Floor((c.Z + c.R + Half) / bucket);
        for (int bz = b0z; bz <= b1z; bz++)
            for (int bx = b0x; bx <= b1x; bx++) fn(BKey(bx, bz));
    }

    public Collider AddCircle(double x, double z, double r, ColliderOpts o = default) =>
        Insert(new Collider { Id = nextId++, Kind = ColliderKind.Circle, X = x, Z = z, R = r, Hw = r, Hd = r, Tag = o.Tag, Soft = o.Soft, PlayerOnly = o.PlayerOnly });

    public Collider AddBox(double x, double z, double hw, double hd, double rot = 0, ColliderOpts o = default) =>
        Insert(new Collider { Id = nextId++, Kind = ColliderKind.Box, X = x, Z = z, R = Math.Sqrt(hw * hw + hd * hd), Hw = hw, Hd = hd, Rot = rot, Tag = o.Tag, Soft = o.Soft, PlayerOnly = o.PlayerOnly });

    /// <summary>A collider as another world had it, its id kept (a zone
    /// loaded from data: the runtime refers to some colliders by id).</summary>
    public Collider Restore(Collider c)
    {
        if (colliders.ContainsKey(c.Id)) throw new ArgumentException($"collider {c.Id} is already there");
        nextId = Math.Max(nextId, c.Id + 1);
        return Insert(c);
    }

    Collider Insert(Collider c)
    {
        colliders[c.Id] = c;
        BucketsFor(c, k =>
        {
            if (!buckets.TryGetValue(k, out var b)) buckets[k] = b = new List<int>();
            b.Add(c.Id);
        });
        if (!c.PlayerOnly) BakeNav(c.X - c.R - 1, c.Z - c.R - 1, c.X + c.R + 1, c.Z + c.R + 1);
        return c;
    }

    public void Remove(int id)
    {
        if (!colliders.Remove(id, out var c)) return;
        BucketsFor(c, k => { if (buckets.TryGetValue(k, out var b)) b.Remove(id); });
        BakeNav(c.X - c.R - 1, c.Z - c.R - 1, c.X + c.R + 1, c.Z + c.R + 1);
    }

    public void RemoveTagged(string tag)
    {
        foreach (var c in colliders.Values.Where(c => c.Tag == tag).ToList()) Remove(c.Id);
    }

    public List<Collider> ByTag(string tag) => colliders.Values.Where(c => c.Tag == tag).ToList();
    /// <summary>Every collider (the map draws the walls and houses from these).</summary>
    public List<Collider> All() => colliders.Values.ToList();

    List<Collider> Near(double x, double z, double r, List<Collider> output)
    {
        output.Clear();
        int b0x = (int)Math.Floor((x - r + Half) / bucket), b1x = (int)Math.Floor((x + r + Half) / bucket);
        int b0z = (int)Math.Floor((z - r + Half) / bucket), b1z = (int)Math.Floor((z + r + Half) / bucket);
        bool many = b0x != b1x || b0z != b1z;
        if (many) seen.Clear();
        for (int bz = b0z; bz <= b1z; bz++)
            for (int bx = b0x; bx <= b1x; bx++)
            {
                if (!buckets.TryGetValue(BKey(bx, bz), out var b)) continue;
                foreach (var id in b)
                {
                    if (many && !seen.Add(id)) continue;
                    output.Add(colliders[id]);
                }
            }
        return output;
    }

    /// <summary>Push a circle out of every collider it overlaps. True if it
    /// touched anything. isPlayer lets player-only edges apply.</summary>
    public bool Resolve(ref double px, ref double pz, double r, bool isPlayer = false)
    {
        bool touched = false;
        for (int iter = 0; iter < 3; iter++)
        {
            bool moved = false;
            foreach (var c in Near(px, pz, r + 0.5, scratch))
            {
                if (c.PlayerOnly && !isPlayer) continue;
                if (c.Kind == ColliderKind.Circle)
                {
                    double dx = px - c.X, dz = pz - c.Z;
                    double d2 = dx * dx + dz * dz, min = c.R + r;
                    if (d2 < min * min)
                    {
                        double d = Math.Sqrt(d2);
                        if (d == 0) d = 0.0001;
                        double push = min - d;
                        px += dx / d * push;
                        pz += dz / d * push;
                        moved = touched = true;
                    }
                }
                else
                {
                    // Into box space.
                    double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
                    double lx = (px - c.X) * cos - (pz - c.Z) * sin;
                    double lz = (px - c.X) * sin + (pz - c.Z) * cos;
                    double qx = Math.Max(-c.Hw, Math.Min(c.Hw, lx));
                    double qz = Math.Max(-c.Hd, Math.Min(c.Hd, lz));
                    double dx = lx - qx, dz = lz - qz;
                    double d2 = dx * dx + dz * dz;
                    if (d2 < r * r)
                    {
                        double nx, nz, push;
                        if (d2 < 1e-8)
                        {
                            // Centre inside the box: leave by the nearest face.
                            double fx = c.Hw - Math.Abs(lx), fz = c.Hd - Math.Abs(lz);
                            if (fx < fz) { nx = lx < 0 ? -1 : 1; nz = 0; push = fx + r; }
                            else { nx = 0; nz = lz < 0 ? -1 : 1; push = fz + r; }
                        }
                        else
                        {
                            double d = Math.Sqrt(d2);
                            nx = dx / d; nz = dz / d; push = r - d;
                        }
                        // Back to world space.
                        double wc = Math.Cos(c.Rot), ws = Math.Sin(c.Rot);
                        px += (nx * wc - nz * ws) * push;
                        pz += (nx * ws + nz * wc) * push;
                        moved = touched = true;
                    }
                }
            }
            if (!moved) break;
        }
        double b = Bound;
        if (px < -b) { px = -b; touched = true; } else if (px > b) { px = b; touched = true; }
        if (pz < -b) { pz = -b; touched = true; } else if (pz > b) { pz = b; touched = true; }
        return touched;
    }

    /// <summary>Is a circle at (x, z) overlapping anything solid?</summary>
    public bool Blocked(double x, double z, double r, bool includeSoft = true)
    {
        foreach (var c in Near(x, z, r + 0.5, scratch))
        {
            if (c.PlayerOnly || (!includeSoft && c.Soft)) continue;
            if (Overlaps(c, x, z, r)) return true;
        }
        return false;
    }

    static bool Overlaps(Collider c, double x, double z, double r)
    {
        if (c.Kind == ColliderKind.Circle)
        {
            double dx = x - c.X, dz = z - c.Z;
            return dx * dx + dz * dz < (c.R + r) * (c.R + r);
        }
        double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
        double lx = (x - c.X) * cos - (z - c.Z) * sin;
        double lz = (x - c.X) * sin + (z - c.Z) * cos;
        double qx = Math.Max(-c.Hw, Math.Min(c.Hw, lx)), qz = Math.Max(-c.Hd, Math.Min(c.Hd, lz));
        return (lx - qx) * (lx - qx) + (lz - qz) * (lz - qz) < r * r;
    }

    /// <summary>First solid collider along a segment (projectiles, charges, sight).</summary>
    public RayHit? Raycast(double x0, double z0, double x1, double z1, double r = 0, bool solidOnly = true)
    {
        double len = Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
        if (len < 1e-6) return null;
        int steps = (int)Math.Ceiling(len / 0.35);
        for (int i = 1; i <= steps; i++)
        {
            double t = (double)i / steps;
            double x = x0 + (x1 - x0) * t, z = z0 + (z1 - z0) * t;
            foreach (var c in Near(x, z, r + 0.5, scratch))
            {
                if (c.PlayerOnly || (solidOnly && c.Soft)) continue;
                if (Overlaps(c, x, z, r)) return new RayHit(t, c);
            }
        }
        return null;
    }

    /// <summary>Colliders whose centre lies within a radius (what an explosion
    /// touched: barrels, bramble walls, braziers).</summary>
    public List<Collider> Within(double x, double z, double r)
    {
        var list = Near(x, z, r, new List<Collider>());
        list.RemoveAll(c => (c.X - x) * (c.X - x) + (c.Z - z) * (c.Z - z) > (r + c.R) * (r + c.R));
        return list;
    }

    /* ---------------------------------------------------------- nav grid -- */
    void BakeNav(double x0, double z0, double x1, double z1)
    {
        int n = NavSize;
        double h = Half;
        int i0 = Math.Max(0, (int)Math.Floor(x0 + h)), i1 = Math.Min(n - 1, (int)Math.Ceiling(x1 + h));
        int j0 = Math.Max(0, (int)Math.Floor(z0 + h)), j1 = Math.Min(n - 1, (int)Math.Ceiling(z1 + h));
        for (int j = j0; j <= j1; j++)
            for (int i = i0; i <= i1; i++)
            {
                double x = -h + i + 0.5, z = -h + j + 0.5;
                NavBlocked[j * n + i] = (byte)(Blocked(x, z, 0.42, true) ? 1 : 0);
            }
    }

    public bool IsNavBlocked(int i, int j)
    {
        if (i < 0 || j < 0 || i >= NavSize || j >= NavSize) return true;
        return NavBlocked[j * NavSize + i] == 1;
    }
}

/// <summary>Downhill directions toward a target over a window of the nav grid.</summary>
public sealed class FlowField
{
    public readonly int Win, Radius;
    readonly ushort[] dist;
    readonly CollisionWorld world;
    int ox, oz, tx = int.MaxValue, tz = int.MaxValue;
    readonly List<List<int>> bucketsByDist = new();
    public bool Ready;

    public FlowField(CollisionWorld world, int radius = 44)
    {
        this.world = world;
        Radius = radius;
        Win = radius * 2 + 1;
        dist = new ushort[Win * Win];
    }

    /// <summary>Re-flood if the target has moved to another cell.</summary>
    public void Update(double x, double z, bool force = false)
    {
        double h = world.Half;
        int ti = (int)Math.Floor(x + h), tj = (int)Math.Floor(z + h);
        if (!force && ti == tx && tj == tz) return;
        tx = ti; tz = tj;
        ox = ti - Radius;
        oz = tj - Radius;
        int W = Win;
        Array.Fill(dist, ushort.MaxValue);
        // Dial's algorithm: small integer costs, bucketed by distance.
        foreach (var b in bucketsByDist) b.Clear();
        void Push(int idx, int d)
        {
            while (bucketsByDist.Count <= d) bucketsByDist.Add(new List<int>());
            bucketsByDist[d].Add(idx);
        }
        int start = Radius * W + Radius;
        dist[start] = 0;
        Push(start, 0);
        for (int d = 0; d < bucketsByDist.Count; d++)
        {
            var b = bucketsByDist[d];
            for (int k = 0; k < b.Count; k++)
            {
                int idx = b[k];
                if (dist[idx] != d) continue;
                int li = idx % W, lj = idx / W;
                for (int dj = -1; dj <= 1; dj++)
                    for (int di = -1; di <= 1; di++)
                    {
                        if (di == 0 && dj == 0) continue;
                        int ni = li + di, nj = lj + dj;
                        if (ni < 0 || nj < 0 || ni >= W || nj >= W) continue;
                        if (world.IsNavBlocked(ox + ni, oz + nj)) continue;
                        // No cutting corners past a blocked orthogonal neighbour.
                        if (di != 0 && dj != 0 && (world.IsNavBlocked(ox + li + di, oz + lj) || world.IsNavBlocked(ox + li, oz + lj + dj))) continue;
                        int nd = d + (di != 0 && dj != 0 ? 14 : 10);
                        int nidx = nj * W + ni;
                        if (nd < dist[nidx]) { dist[nidx] = (ushort)nd; Push(nidx, nd); }
                    }
            }
        }
        Ready = true;
    }

    /// <summary>The downhill direction at (x, z). False outside the window or
    /// on an unreachable cell.</summary>
    public bool Dir(double x, double z, out double dx, out double dz)
    {
        dx = dz = 0;
        if (!Ready) return false;
        double h = world.Half;
        int li = (int)Math.Floor(x + h) - ox, lj = (int)Math.Floor(z + h) - oz;
        int W = Win;
        if (li < 1 || lj < 1 || li >= W - 1 || lj >= W - 1) return false;
        int here = dist[lj * W + li];
        // Pressed against a tree or a wall, the cell underfoot can read as
        // blocked: step toward the nearest open one that leads there.
        int best = here, bx = 0, bz = 0;
        for (int dj = -1; dj <= 1; dj++)
            for (int di = -1; di <= 1; di++)
            {
                if (di == 0 && dj == 0) continue;
                int d = dist[(lj + dj) * W + li + di];
                if (d < best) { best = d; bx = di; bz = dj; }
            }
        if (bx == 0 && bz == 0) return false;
        double m = Math.Sqrt(bx * bx + bz * bz);
        dx = bx / m;
        dz = bz / m;
        return true;
    }

    /// <summary>Path distance to the target in metres, or infinity.</summary>
    public double DistanceAt(double x, double z)
    {
        double h = world.Half;
        int li = (int)Math.Floor(x + h) - ox, lj = (int)Math.Floor(z + h) - oz;
        if (li < 0 || lj < 0 || li >= Win || lj >= Win) return double.PositiveInfinity;
        int d = dist[lj * Win + li];
        return d == ushort.MaxValue ? double.PositiveInfinity : d / 10.0;
    }
}
