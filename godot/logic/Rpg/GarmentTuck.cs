using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace SurvivorUnchained.Rpg;

/* The garment tuck (docs/armor/PIECE_SCHEMA.md "Garment tuck"): a worn piece lies down onto her skin wherever a
 * worn piece outside it (later in Order) covers it, and is removed where that piece fully hides it, as her skin is
 * tucked under her pieces. Pieces of one outfit are fitted together and never tuck each other. The pure math:
 * HerWear (src/Actors) reads the meshes and records and lays the result. */

/// <summary>Her body's bind points (one a place: her split skin's copies merged) and their normals, in a spatial hash.</summary>
public sealed class SkinPoints
{
    public const float Cell = 0.01f;
    public readonly float[] P, N;
    public readonly long[] Keys;
    public readonly Dictionary<long, int> ByKey = new();
    // (a dense grid of Cell cells over her box: each cell's points, cellStart[c]..cellStart[c + 1] in cellPts)
    readonly int nx, ny, nz;
    readonly float ox, oy, oz;
    readonly int[] cellStart, cellPts;

    public int Count => Keys.Length;

    /// <summary>Points p and normals n (xyz a vertex) keyed by `keys` (their quantized bind positions); copies of a key are
    /// one point (their normals averaged).</summary>
    public SkinPoints(IReadOnlyList<float> p, IReadOnlyList<float> n, IReadOnlyList<long> keys)
    {
        var pos = new List<float>();
        var nrm = new List<float>();
        var ks = new List<long>();
        for (int i = 0; i < keys.Count; i++)
        {
            if (ByKey.TryGetValue(keys[i], out int j))
            {
                for (int c = 0; c < 3; c++) nrm[j * 3 + c] += n[i * 3 + c];
                continue;
            }
            ByKey[keys[i]] = ks.Count;
            ks.Add(keys[i]);
            for (int c = 0; c < 3; c++) { pos.Add(p[i * 3 + c]); nrm.Add(n[i * 3 + c]); }
        }
        P = pos.ToArray();
        N = nrm.ToArray();
        Keys = ks.ToArray();
        float x0 = float.MaxValue, y0 = float.MaxValue, z0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue, z1 = float.MinValue;
        for (int i = 0; i < Keys.Length; i++)
        {
            float l = MathF.Sqrt(N[i * 3] * N[i * 3] + N[i * 3 + 1] * N[i * 3 + 1] + N[i * 3 + 2] * N[i * 3 + 2]);
            if (l > 1e-12f) for (int c = 0; c < 3; c++) N[i * 3 + c] /= l;
            x0 = MathF.Min(x0, P[i * 3]); y0 = MathF.Min(y0, P[i * 3 + 1]); z0 = MathF.Min(z0, P[i * 3 + 2]);
            x1 = MathF.Max(x1, P[i * 3]); y1 = MathF.Max(y1, P[i * 3 + 1]); z1 = MathF.Max(z1, P[i * 3 + 2]);
        }
        if (Keys.Length == 0) { x0 = y0 = z0 = x1 = y1 = z1 = 0; }
        ox = x0; oy = y0; oz = z0;
        nx = (int)((x1 - x0) / Cell) + 1; ny = (int)((y1 - y0) / Cell) + 1; nz = (int)((z1 - z0) / Cell) + 1;
        var cnt = new int[nx * ny * nz + 1];
        var at = new int[Keys.Length];
        for (int i = 0; i < Keys.Length; i++) cnt[at[i] = CellOf(P[i * 3], P[i * 3 + 1], P[i * 3 + 2])]++;
        cellStart = new int[cnt.Length];
        for (int c = 0, sum = 0; c < cnt.Length; c++) { cellStart[c] = sum; sum += cnt[c]; }
        cellPts = new int[Keys.Length];
        var fill = (int[])cellStart.Clone();
        for (int i = 0; i < Keys.Length; i++) cellPts[fill[at[i]]++] = i;
    }

    int CellOf(float x, float y, float z) =>
        (Math.Clamp((int)((z - oz) / Cell), 0, nz - 1) * ny + Math.Clamp((int)((y - oy) / Cell), 0, ny - 1)) * nx + Math.Clamp((int)((x - ox) / Cell), 0, nx - 1);

    float D2(int i, float x, float y, float z)
    {
        float dx = P[i * 3] - x, dy = P[i * 3 + 1] - y, dz = P[i * 3 + 2] - z;
        return dx * dx + dy * dy + dz * dz;
    }

    void Cell1(int cx, int cy, int cz, float x, float y, float z, ref int best, ref float bd)
    {
        if (cx < 0 || cy < 0 || cz < 0 || cx >= nx || cy >= ny || cz >= nz) return;
        int c = (cz * ny + cy) * nx + cx;
        for (int e = cellStart[c]; e < cellStart[c + 1]; e++)
        {
            int i = cellPts[e];
            float d = D2(i, x, y, z);
            if (d < bd) { bd = d; best = i; }
        }
    }

    /// <summary>The nearest point to (x, y, z) within `max` m, or -1.</summary>
    public int Nearest(float x, float y, float z, float max = 0.08f)
    {
        int cx = (int)MathF.Floor((x - ox) / Cell), cy = (int)MathF.Floor((y - oy) / Cell), cz = (int)MathF.Floor((z - oz) / Cell);
        int best = -1;
        float bd = max * max;
        int rings = (int)MathF.Ceiling(max / Cell);
        for (int k = 0; k <= rings; k++)
        {
            // (ring k's cells are all at least (k - 1) cells away: done once the best is nearer)
            float lo = (k - 1) * Cell;
            if (k > 1 && lo * lo >= bd) break;
            for (int ix = -k; ix <= k; ix++)
                for (int iy = -k; iy <= k; iy++)
                {
                    bool edge = ix == -k || ix == k || iy == -k || iy == k;
                    if (edge) for (int iz = -k; iz <= k; iz++) Cell1(cx + ix, cy + iy, cz + iz, x, y, z, ref best, ref bd);
                    else
                    {
                        Cell1(cx + ix, cy + iy, cz - k, x, y, z, ref best, ref bd);
                        if (k > 0) Cell1(cx + ix, cy + iy, cz + k, x, y, z, ref best, ref bd);
                    }
                }
        }
        return best;
    }

    /// <summary>The points within r of point i (itself too), into `into` (cleared).</summary>
    public void Within(int i, float r, List<int> into) => Within(P[i * 3], P[i * 3 + 1], P[i * 3 + 2], r, into);

    /// <summary>The points within r of (x, y, z), into `into` (cleared).</summary>
    public void Within(float x, float y, float z, float r, List<int> into)
    {
        into.Clear();
        int ax = Math.Max((int)MathF.Floor((x - r - ox) / Cell), 0), bx = Math.Min((int)MathF.Floor((x + r - ox) / Cell), nx - 1);
        int ay = Math.Max((int)MathF.Floor((y - r - oy) / Cell), 0), by = Math.Min((int)MathF.Floor((y + r - oy) / Cell), ny - 1);
        int az = Math.Max((int)MathF.Floor((z - r - oz) / Cell), 0), bz = Math.Min((int)MathF.Floor((z + r - oz) / Cell), nz - 1);
        for (int cz = az; cz <= bz; cz++)
            for (int cy = ay; cy <= by; cy++)
                for (int cx = ax; cx <= bx; cx++)
                {
                    int c = (cz * ny + cy) * nx + cx;
                    for (int e = cellStart[c]; e < cellStart[c + 1]; e++)
                        if (D2(cellPts[e], x, y, z) <= r * r) into.Add(cellPts[e]);
                }
    }
}

public static class GarmentTuck
{
    /// <summary>How far outside her skin a lain-down vertex rests, m.</summary>
    public const float Offset = 0.0003f;
    /// <summary>A value this high lies all the way down (as her skin's tuck reads it).</summary>
    public const float Full = 0.973f;
    /// <summary>A triangle whose three vertices read this or more is removed (hidden under what covers it).</summary>
    public const float Gone = 0.995f;
    /// <summary>The footprint's spread over her body, m (motion: the outer piece's edge moves over the inner).</summary>
    public const float Spread = 0.020f;
    /// <summary>The radius her footprint, surface and normal are smoothed over under a vertex, m.</summary>
    public const float Smooth = 0.010f;
    /// <summary>A vertex farther than this from her body has no anchor (and never moves), m.</summary>
    public const float Reach = 0.08f;

    /// <summary>The slots from innermost to outermost (tools/armor/slot_map.json "order"; ink takes no part).</summary>
    public static readonly string[] Order = ["bottom", "top", "legwear", "gloves", "boots", "skirt", "collar", "bracers", "greaves", "belt", "pauldrons", "cloak", "head"];

    public static int OrderOf(string slot) => Array.IndexOf(Order, slot);

    /// <summary>Whether `outer` lies over `inner` (and tucks it): later in Order, and not built with it (one outfit's
    /// pieces are fitted together).</summary>
    public static bool Over(ArmorPiece outer, ArmorPiece inner)
    {
        int o = OrderOf(outer.Slot), i = OrderOf(inner.Slot);
        if (o < 0 || i < 0 || o <= i || outer.Id == inner.Id) return false;
        return !(outer.Outfit != null && outer.Outfit == inner.Outfit);
    }

    /// <summary>The footprint on her points of the pieces over one: the largest of their values a point (records: her bind
    /// key, value), spread out by `spread` m (falling off linearly to 0 there). Null if none of them covers any of her.</summary>
    public static float[]? Field(SkinPoints s, IEnumerable<IReadOnlyList<(long Key, float T)>> outer, float spread = Spread)
    {
        var f = new float[s.Count];
        bool any = false;
        foreach (var recs in outer)
            foreach (var (k, t) in recs)
                if (t > 0 && s.ByKey.TryGetValue(k, out int i) && t > f[i]) { f[i] = t; any = true; }
        if (!any) return null;
        if (spread <= 0) return f;
        var g = (float[])f.Clone();
        var near = new List<int>();
        for (int i = 0; i < f.Length; i++)
        {
            if (f[i] <= 0) continue;
            s.Within(i, spread, near);
            foreach (int j in near)
            {
                float dx = s.P[j * 3] - s.P[i * 3], dy = s.P[j * 3 + 1] - s.P[i * 3 + 1], dz = s.P[j * 3 + 2] - s.P[i * 3 + 2];
                float v = f[i] * (1 - MathF.Sqrt(dx * dx + dy * dy + dz * dz) / spread);
                if (v > g[j]) g[j] = v;
            }
        }
        return g;
    }

    /// <summary>A footprint value as it moves a vertex: all of it past Full.</summary>
    public static float Amount(float t) => t > Full ? 1f : Math.Clamp(t, 0f, 1f);

    /// <summary>Lays one surface down: each vertex (pos, xyz, changed in place) toward her body by the footprint under
    /// it, to Offset outside her (along her normal; never lifted), and its triangles (index) whose three vertices read
    /// Gone or more removed. Under a vertex: its anchor (her nearest point), the vertex's foot on the anchor's tangent
    /// plane, and her points within Smooth of that foot, weighted (1 - d^2/Smooth^2)^2: the footprint, her surface point
    /// and normal there their weighted means (so a piece's edge over it ramps, not steps, at her points' spacing).
    /// Returns the kept index (null: the surface unchanged), and each vertex's anchor (-1: none) and value.</summary>
    public static int[]? Lay(SkinPoints s, float[] field, float[] pos, int[] index, out int[] anchor, out float[] t) =>
        Lay(s, field, Near(s, field), pos, index, out anchor, out t);

    /// <summary>Her points a footprint can reach a vertex through (within 2 Smooth + a cell of its nonzero points): a vertex
    /// anchored elsewhere reads 0, unsearched (Lay's cost stays with what is covered).</summary>
    public static bool[] Near(SkinPoints s, float[] field)
    {
        var near = new bool[s.Count];
        var l = new List<int>();
        for (int i = 0; i < field.Length; i++)
        {
            if (field[i] <= 0 || near[i]) continue;
            s.Within(i, 2 * Smooth + SkinPoints.Cell, l);
            foreach (int j in l) near[j] = true;
        }
        return near;
    }

    public static int[]? Lay(SkinPoints s, float[] field, bool[] reach, float[] pos, int[] index, out int[] anchor, out float[] t)
    {
        int n = pos.Length / 3;
        anchor = new int[n];
        t = new float[n];
        int moved = 0;
        var anc = anchor;
        var tv = t;
        // (her covered points' box, out by Reach: a vertex past it has no anchor that reads)
        float x0 = float.MaxValue, y0 = float.MaxValue, z0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue, z1 = float.MinValue;
        for (int i = 0; i < field.Length; i++)
        {
            if (field[i] <= 0) continue;
            x0 = MathF.Min(x0, s.P[i * 3]); y0 = MathF.Min(y0, s.P[i * 3 + 1]); z0 = MathF.Min(z0, s.P[i * 3 + 2]);
            x1 = MathF.Max(x1, s.P[i * 3]); y1 = MathF.Max(y1, s.P[i * 3 + 1]); z1 = MathF.Max(z1, s.P[i * 3 + 2]);
        }
        float m = Reach + 2 * Smooth;
        // (each vertex alone: in parallel, a list of her near points a worker)
        Parallel.For(0, n, () => new List<int>(), (v, _, near) =>
        {
            Vertex(v, near);
            return near;
        }, _ => { });
        void Vertex(int v, List<int> near)
        {
            anc[v] = -1;
            float x = pos[v * 3], y = pos[v * 3 + 1], z = pos[v * 3 + 2];
            if (x < x0 - m || y < y0 - m || z < z0 - m || x > x1 + m || y > y1 + m || z > z1 + m) return;
            int a = s.Nearest(x, y, z, Reach);
            anc[v] = a;
            if (a < 0 || !reach[a]) return;
            float ha = (x - s.P[a * 3]) * s.N[a * 3] + (y - s.P[a * 3 + 1]) * s.N[a * 3 + 1] + (z - s.P[a * 3 + 2]) * s.N[a * 3 + 2];
            float fx = x - s.N[a * 3] * ha, fy = y - s.N[a * 3 + 1] * ha, fz = z - s.N[a * 3 + 2] * ha;
            s.Within(fx, fy, fz, Smooth, near);
            if (near.Count == 0) near.Add(a);
            double sw = 0, sf = 0, px = 0, py = 0, pz = 0, nx = 0, ny = 0, nz = 0;
            foreach (int j in near)
            {
                float dx = s.P[j * 3] - fx, dy = s.P[j * 3 + 1] - fy, dz = s.P[j * 3 + 2] - fz;
                float q = 1 - (dx * dx + dy * dy + dz * dz) / (Smooth * Smooth);
                double w = near.Count == 1 ? 1 : Math.Max(q, 0) * Math.Max(q, 0) + 1e-9;
                sw += w; sf += w * field[j];
                px += w * s.P[j * 3]; py += w * s.P[j * 3 + 1]; pz += w * s.P[j * 3 + 2];
                nx += w * s.N[j * 3]; ny += w * s.N[j * 3 + 1]; nz += w * s.N[j * 3 + 2];
            }
            tv[v] = (float)(sf / sw);
            if (tv[v] <= 0) return;
            double nl = Math.Sqrt(nx * nx + ny * ny + nz * nz);
            if (nl < 1e-9) return;
            nx /= nl; ny /= nl; nz /= nl;
            double h = (x - px / sw) * nx + (y - py / sw) * ny + (z - pz / sw) * nz;
            if (h <= Offset) return;
            double d = (h - Offset) * Amount(tv[v]);
            pos[v * 3] = (float)(x - nx * d);
            pos[v * 3 + 1] = (float)(y - ny * d);
            pos[v * 3 + 2] = (float)(z - nz * d);
            Interlocked.Exchange(ref moved, 1);
        }
        var kept = new List<int>(index.Length);
        for (int i = 0; i + 2 < index.Length; i += 3)
            if (!(t[index[i]] >= Gone && t[index[i + 1]] >= Gone && t[index[i + 2]] >= Gone))
            {
                kept.Add(index[i]); kept.Add(index[i + 1]); kept.Add(index[i + 2]);
            }
        if (moved == 0 && kept.Count == index.Length) return null;
        // (nothing of it shows: one degenerate triangle keeps the surface, and its material's place)
        if (kept.Count == 0 && index.Length > 0) kept.AddRange(new[] { index[0], index[0], index[0] });
        return kept.ToArray();
    }
}
