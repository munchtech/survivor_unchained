using System;
using System.Collections.Generic;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Signed distance from a point to a posed, smooth-normalled surface (the in-game measure of armor inside her skin,
/// View/WearInside): a uniform grid over the triangles, the nearest triangle found by searching rings of cells outward
/// until the best distance is inside the ring's radius or the cap (beyond it the point counts as outside). The sign
/// comes from the smooth normal interpolated at the closest point, so a fold in the flat triangles cannot flip it.
/// </summary>
public sealed class InsideTest
{
    readonly Vector3[] pos, nrm;
    readonly int[] tris;
    readonly float cell;
    readonly Dictionary<long, int[]> grid = new();

    public InsideTest(Vector3[] positions, Vector3[] normals, int[] triangles, float cellSize = 0.02f)
    {
        pos = positions; nrm = normals; tris = triangles; cell = cellSize;
        var lists = new Dictionary<long, List<int>>();
        for (int t = 0; t < tris.Length / 3; t++)
        {
            var a = pos[tris[t * 3]]; var b = pos[tris[t * 3 + 1]]; var c = pos[tris[t * 3 + 2]];
            var lo = Vector3.Min(a, Vector3.Min(b, c)); var hi = Vector3.Max(a, Vector3.Max(b, c));
            int x0 = Cell(lo.X), y0 = Cell(lo.Y), z0 = Cell(lo.Z), x1 = Cell(hi.X), y1 = Cell(hi.Y), z1 = Cell(hi.Z);
            for (int x = x0; x <= x1; x++) for (int y = y0; y <= y1; y++) for (int z = z0; z <= z1; z++)
            {
                long k = Key(x, y, z);
                if (!lists.TryGetValue(k, out var l)) lists[k] = l = new List<int>();
                l.Add(t);
            }
        }
        foreach (var kv in lists) grid[kv.Key] = kv.Value.ToArray();
    }

    int Cell(float v) => (int)MathF.Floor(v / cell);
    static long Key(int x, int y, int z) => ((long)(x + (1 << 20)) << 42) | ((long)(y + (1 << 20)) << 21) | (long)(z + (1 << 20));

    /// <summary>Signed distance (negative inside) to the nearest surface and the vertex of that triangle nearest the closest point;
    /// farther than the cap: (+cap, -1).</summary>
    public (float Dist, int Vertex) Query(Vector3 p, float cap = 0.12f)
    {
        int cx = Cell(p.X), cy = Cell(p.Y), cz = Cell(p.Z);
        float best = float.MaxValue; int bt = -1; Vector3 bc = default;
        int maxRing = (int)MathF.Ceiling(cap / cell) + 1;
        for (int r = 0; r <= maxRing; r++)
        {
            for (int x = cx - r; x <= cx + r; x++) for (int y = cy - r; y <= cy + r; y++)
            {
                bool edge = x == cx - r || x == cx + r || y == cy - r || y == cy + r;
                int step = edge ? 1 : Math.Max(1, 2 * r);   // inside the ring's shell only its two z faces
                for (int z = cz - r; z <= cz + r; z += step)
                {
                    if (!grid.TryGetValue(Key(x, y, z), out var list)) continue;
                    foreach (int t in list)
                    {
                        var q = Closest(p, pos[tris[t * 3]], pos[tris[t * 3 + 1]], pos[tris[t * 3 + 2]], out var bary);
                        float d = Vector3.Distance(p, q);
                        if (d < best) { best = d; bt = t; bc = bary; }
                    }
                }
            }
            if (best <= r * cell) break;
        }
        if (bt < 0 || best > cap) return (cap, -1);
        int i0 = tris[bt * 3], i1 = tris[bt * 3 + 1], i2 = tris[bt * 3 + 2];
        var n = nrm[i0] * bc.X + nrm[i1] * bc.Y + nrm[i2] * bc.Z;
        var cp = pos[i0] * bc.X + pos[i1] * bc.Y + pos[i2] * bc.Z;
        float sign = Vector3.Dot(p - cp, n) < 0 ? -1 : 1;
        int near = bc.X >= bc.Y && bc.X >= bc.Z ? i0 : bc.Y >= bc.Z ? i1 : i2;
        return (sign * best, near);
    }

    /// <summary>Closest point on triangle abc to p (Ericson, Real-Time Collision Detection), with its barycentrics.</summary>
    static Vector3 Closest(Vector3 p, Vector3 a, Vector3 b, Vector3 c, out Vector3 bary)
    {
        var ab = b - a; var ac = c - a; var ap = p - a;
        float d1 = Vector3.Dot(ab, ap), d2 = Vector3.Dot(ac, ap);
        if (d1 <= 0 && d2 <= 0) { bary = new(1, 0, 0); return a; }
        var bp = p - b; float d3 = Vector3.Dot(ab, bp), d4 = Vector3.Dot(ac, bp);
        if (d3 >= 0 && d4 <= d3) { bary = new(0, 1, 0); return b; }
        float vc = d1 * d4 - d3 * d2;
        if (vc <= 0 && d1 >= 0 && d3 <= 0) { float v = d1 / (d1 - d3); bary = new(1 - v, v, 0); return a + v * ab; }
        var cpv = p - c; float d5 = Vector3.Dot(ab, cpv), d6 = Vector3.Dot(ac, cpv);
        if (d6 >= 0 && d5 <= d6) { bary = new(0, 0, 1); return c; }
        float vb = d5 * d2 - d1 * d6;
        if (vb <= 0 && d2 >= 0 && d6 <= 0) { float w = d2 / (d2 - d6); bary = new(1 - w, 0, w); return a + w * ac; }
        float va = d3 * d6 - d5 * d4;
        if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) { float w = (d4 - d3) / ((d4 - d3) + (d5 - d6)); bary = new(0, 1 - w, w); return b + w * (c - b); }
        float den = 1f / (va + vb + vc); float vv = vb * den, ww = vc * den;
        bary = new(1 - vv - ww, vv, ww);
        return a + ab * vv + ac * ww;
    }
}
