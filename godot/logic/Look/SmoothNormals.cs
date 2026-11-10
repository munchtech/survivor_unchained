using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Look;

/// <summary>(L1 lead 23, NORM2) SMOOTH SHADING NORMALS for any hero-scale mesh, fast: a Gaussian (sigma, m) of the
/// welded vertex normals over space, kept to the vertex's own connected surface (welded at 0.1 mm, joined by the
/// triangles) and to its own normal hemisphere (a neighbour counts by (1 + n.m) / 2: 1 for the same normal, 0 for the
/// opposite one), so touching thighs or an arm on the torso never bleed.
/// A surface of more than <see cref="BruteMax"/> welded vertices goes through a grid (cells sigma / 2, four lobes
/// x 3 channels, trilinear splat, a separable Gaussian, trilinear read); a smaller one is summed pair by pair. Linear in
/// the vertex count; no per-mesh constants. <see cref="Diffuse"/> is lead 22's graph diffusion, kept as the reference.</summary>
public static class SmoothNormals
{
    public static int BruteMax = 384;

    /// <summary>Per vertex (xyz each, the mesh's own vertices; tri = triangle list into them): the smoothed unit normal.</summary>
    public static float[] Smooth(float[] pos, float[] nrm, int[] tri, float sigma)
    {
        int n = pos.Length / 3;
        var outv = new float[n * 3];
        if (n == 0) return outv;
        var wid = Weld(pos, n, out int W);
        var P = new float[W * 3]; var S = new float[W * 3];
        for (int v = 0; v < n; v++)
        {
            int w = wid[v];
            P[3 * w] = pos[3 * v]; P[3 * w + 1] = pos[3 * v + 1]; P[3 * w + 2] = pos[3 * v + 2];
            S[3 * w] += nrm[3 * v]; S[3 * w + 1] += nrm[3 * v + 1]; S[3 * w + 2] += nrm[3 * v + 2];
        }
        for (int w = 0; w < W; w++) Unit(S, w);
        // connected surfaces
        var par = new int[W]; for (int i = 0; i < W; i++) par[i] = i;
        var Ar = new float[W];   // (each welded vertex weighs a third of its triangles' area: the density never shows)
        for (int t = 0; t + 2 < tri.Length; t += 3)
        {
            int a = wid[tri[t]], b = wid[tri[t + 1]], c = wid[tri[t + 2]];
            Union(par, a, b); Union(par, a, c);
            float ux = P[3 * b] - P[3 * a], uy = P[3 * b + 1] - P[3 * a + 1], uz = P[3 * b + 2] - P[3 * a + 2];
            float vx = P[3 * c] - P[3 * a], vy = P[3 * c + 1] - P[3 * a + 1], vz = P[3 * c + 2] - P[3 * a + 2];
            float cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx;
            float ar = MathF.Sqrt(cx * cx + cy * cy + cz * cz) / 6f;
            Ar[a] += ar; Ar[b] += ar; Ar[c] += ar;
        }
        var compOf = new int[W]; var count = new List<int>(); var map = new Dictionary<int, int>();
        for (int w = 0; w < W; w++)
        {
            int r = Find(par, w);
            if (!map.TryGetValue(r, out int c)) { map[r] = c = count.Count; count.Add(0); }
            compOf[w] = c; count[c]++;
        }
        var start = new int[count.Count + 1];
        for (int c = 0; c < count.Count; c++) start[c + 1] = start[c] + count[c];
        var members = new int[W]; var fill = (int[])start.Clone();
        for (int w = 0; w < W; w++) members[fill[compOf[w]]++] = w;
        var R = new float[W * 3];
        for (int c = 0; c < count.Count; c++)
        {
            var seg = new ArraySegment<int>(members, start[c], count[c]);
            if (count[c] <= BruteMax) Brute(seg, P, S, Ar, sigma, R); else Grid(seg, P, S, Ar, sigma, R);
        }
        for (int v = 0; v < n; v++)
        {
            int w = wid[v];
            float x = R[3 * w], y = R[3 * w + 1], z = R[3 * w + 2], l = x * x + y * y + z * z;
            if (l < 1e-20f) { x = S[3 * w]; y = S[3 * w + 1]; z = S[3 * w + 2]; l = x * x + y * y + z * z; }
            float k = l > 1e-20f ? 1f / MathF.Sqrt(l) : 0f;
            outv[3 * v] = x * k; outv[3 * v + 1] = y * k; outv[3 * v + 2] = z * k;
        }
        return outv;
    }

    /// <summary>Welded id per vertex (positions at 0.1 mm), W the welded count.</summary>
    public static int[] Weld(float[] pos, int n, out int W)
    {
        float mx = float.MaxValue, my = float.MaxValue, mz = float.MaxValue;
        for (int v = 0; v < n; v++) { mx = MathF.Min(mx, pos[3 * v]); my = MathF.Min(my, pos[3 * v + 1]); mz = MathF.Min(mz, pos[3 * v + 2]); }
        var d = new Dictionary<long, int>(n);
        var wid = new int[n]; W = 0;
        for (int v = 0; v < n; v++)
        {
            long qx = (long)MathF.Round((pos[3 * v] - mx) * 1e4f), qy = (long)MathF.Round((pos[3 * v + 1] - my) * 1e4f), qz = (long)MathF.Round((pos[3 * v + 2] - mz) * 1e4f);
            long key = (qx & 0x1FFFFF) | ((qy & 0x1FFFFF) << 21) | ((qz & 0x1FFFFF) << 42);
            if (!d.TryGetValue(key, out int w)) { d[key] = w = W++; }
            wid[v] = w;
        }
        return wid;
    }

    static void Unit(float[] a, int w)
    {
        float x = a[3 * w], y = a[3 * w + 1], z = a[3 * w + 2], l = x * x + y * y + z * z;
        if (l > 1e-20f) { float k = 1f / MathF.Sqrt(l); a[3 * w] = x * k; a[3 * w + 1] = y * k; a[3 * w + 2] = z * k; }
        else { a[3 * w] = 0; a[3 * w + 1] = 1; a[3 * w + 2] = 0; }
    }
    static int Find(int[] p, int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }
    static void Union(int[] p, int a, int b) { a = Find(p, a); b = Find(p, b); if (a != b) { if (a < b) p[b] = a; else p[a] = b; } }

    /// <summary>The hemisphere affinity of two unit normals, (1 + n.m) / 2: 1 for the same normal, 0 for the opposite one;
    /// a function of their angle only (so no axis of the mesh's frame shows), and separable (1, n) . (1, m) for the grid.</summary>
    public static float Affinity(float ax, float ay, float az, float bx, float by, float bz) => 0.5f * (1f + ax * bx + ay * by + az * bz);

    static void Brute(ArraySegment<int> m, float[] P, float[] S, float[] Ar, float sigma, float[] R)
    {
        float inv = -0.5f / (sigma * sigma);
        for (int i = 0; i < m.Count; i++)
        {
            int a = m[i]; float x = 0, y = 0, z = 0;
            for (int j = 0; j < m.Count; j++)
            {
                int b = m[j];
                float dx = P[3 * a] - P[3 * b], dy = P[3 * a + 1] - P[3 * b + 1], dz = P[3 * a + 2] - P[3 * b + 2];
                float g = Ar[b] * MathF.Exp((dx * dx + dy * dy + dz * dz) * inv) * Affinity(S[3 * a], S[3 * a + 1], S[3 * a + 2], S[3 * b], S[3 * b + 1], S[3 * b + 2]);
                x += g * S[3 * b]; y += g * S[3 * b + 1]; z += g * S[3 * b + 2];
            }
            R[3 * a] = x; R[3 * a + 1] = y; R[3 * a + 2] = z;
        }
    }

    const int C = 12;   // the affinity's four lobes (1, n.x, n.y, n.z) x the normal's three channels

    static void Grid(ArraySegment<int> m, float[] P, float[] S, float[] Ar, float sigma, float[] R)
    {
        float h = sigma * 0.5f;
        float x0 = float.MaxValue, y0 = float.MaxValue, z0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue, z1 = float.MinValue;
        foreach (int a in m)
        {
            x0 = MathF.Min(x0, P[3 * a]); y0 = MathF.Min(y0, P[3 * a + 1]); z0 = MathF.Min(z0, P[3 * a + 2]);
            x1 = MathF.Max(x1, P[3 * a]); y1 = MathF.Max(y1, P[3 * a + 1]); z1 = MathF.Max(z1, P[3 * a + 2]);
        }
        int nx = (int)((x1 - x0) / h) + 2, ny = (int)((y1 - y0) / h) + 2, nz = (int)((z1 - z0) / h) + 2;
        var g = new float[(long)nx * ny * nz * C];
        Span<float> lob = stackalloc float[4];
        foreach (int a in m)
        {
            float sx = S[3 * a], sy = S[3 * a + 1], sz = S[3 * a + 2];
            Lobes(sx, sy, sz, lob);
            for (int k = 0; k < 4; k++) lob[k] *= Ar[a];
            Cell(P, a, x0, y0, z0, h, nx, ny, nz, out int ix, out int iy, out int iz, out float fx, out float fy, out float fz);
            for (int c = 0; c < 8; c++)
            {
                int cx = ix + (c & 1), cy = iy + ((c >> 1) & 1), cz = iz + (c >> 2);
                float wt = ((c & 1) != 0 ? fx : 1 - fx) * (((c >> 1) & 1) != 0 ? fy : 1 - fy) * ((c >> 2) != 0 ? fz : 1 - fz);
                if (wt == 0f) continue;
                long o = (((long)cz * ny + cy) * nx + cx) * C;
                for (int k = 0; k < 4; k++)
                {
                    float q = lob[k] * wt;
                    g[o + 3 * k] += q * sx; g[o + 3 * k + 1] += q * sy; g[o + 3 * k + 2] += q * sz;
                }
            }
        }
        // (the trilinear splat and read add sigma^2 / 12 of their own)
        float sc = sigma * MathF.Sqrt(11f / 12f) / h;
        int rr = (int)MathF.Ceiling(3f * sc);
        var tap = new float[2 * rr + 1];
        for (int i = -rr; i <= rr; i++) tap[i + rr] = MathF.Exp(-0.5f * i * i / (sc * sc));
        var tmp = new float[g.Length];
        Blur(g, tmp, nx, ny, nz, 0, tap, rr);
        Blur(tmp, g, nx, ny, nz, 1, tap, rr);
        Blur(g, tmp, nx, ny, nz, 2, tap, rr);
        foreach (int a in m)
        {
            float sx = S[3 * a], sy = S[3 * a + 1], sz = S[3 * a + 2];
            Lobes(sx, sy, sz, lob);
            Cell(P, a, x0, y0, z0, h, nx, ny, nz, out int ix, out int iy, out int iz, out float fx, out float fy, out float fz);
            float rx = 0, ry = 0, rz = 0;
            for (int c = 0; c < 8; c++)
            {
                int cx = ix + (c & 1), cy = iy + ((c >> 1) & 1), cz = iz + (c >> 2);
                float wt = ((c & 1) != 0 ? fx : 1 - fx) * (((c >> 1) & 1) != 0 ? fy : 1 - fy) * ((c >> 2) != 0 ? fz : 1 - fz);
                if (wt == 0f) continue;
                long o = (((long)cz * ny + cy) * nx + cx) * C;
                for (int k = 0; k < 4; k++)
                {
                    float q = lob[k] * wt;
                    rx += q * tmp[o + 3 * k]; ry += q * tmp[o + 3 * k + 1]; rz += q * tmp[o + 3 * k + 2];
                }
            }
            R[3 * a] = rx; R[3 * a + 1] = ry; R[3 * a + 2] = rz;
        }
    }

    static void Lobes(float x, float y, float z, Span<float> l)
    {
        const float r = 0.70710678f; l[0] = r; l[1] = r * x; l[2] = r * y; l[3] = r * z;
    }

    static void Cell(float[] P, int a, float x0, float y0, float z0, float h, int nx, int ny, int nz, out int ix, out int iy, out int iz, out float fx, out float fy, out float fz)
    {
        float gx = (P[3 * a] - x0) / h, gy = (P[3 * a + 1] - y0) / h, gz = (P[3 * a + 2] - z0) / h;
        ix = Math.Clamp((int)gx, 0, nx - 2); iy = Math.Clamp((int)gy, 0, ny - 2); iz = Math.Clamp((int)gz, 0, nz - 2);
        fx = Math.Clamp(gx - ix, 0f, 1f); fy = Math.Clamp(gy - iy, 0f, 1f); fz = Math.Clamp(gz - iz, 0f, 1f);
    }

    /// <summary>One axis (0 x, 1 y, 2 z) of the separable Gaussian over the node grid; a line that is all zero is skipped.</summary>
    static void Blur(float[] src, float[] dst, int nx, int ny, int nz, int axis, float[] tap, int rr)
    {
        int len = axis == 0 ? nx : axis == 1 ? ny : nz;
        long st = axis == 0 ? 1 : axis == 1 ? nx : (long)nx * ny;
        int na = axis == 0 ? ny : nx, nb = axis == 2 ? ny : nz;
        Span<float> acc = stackalloc float[C];
        var line = new float[len * C];
        for (int ib = 0; ib < nb; ib++)
            for (int ia = 0; ia < na; ia++)
            {
                long n0 = axis == 0 ? ((long)ib * ny + ia) * nx : axis == 1 ? (long)ib * nx * ny + ia : (long)ib * nx + ia;
                bool any = false;
                for (int i = 0; i < len; i++)
                {
                    long o = (n0 + i * st) * C;
                    for (int c = 0; c < C; c++) { float v = src[o + c]; line[i * C + c] = v; any |= v != 0f; }
                }
                if (!any) { for (int i = 0; i < len; i++) Array.Clear(dst, (int)((n0 + i * st) * C), C); continue; }
                for (int i = 0; i < len; i++)
                {
                    acc.Clear();
                    int lo = Math.Max(0, i - rr), hi = Math.Min(len - 1, i + rr);
                    for (int j = lo; j <= hi; j++)
                    {
                        float t = tap[j - i + rr]; int o = j * C;
                        for (int c = 0; c < C; c++) acc[c] += t * line[o + c];
                    }
                    long od = (n0 + i * st) * C;
                    for (int c = 0; c < C; c++) dst[od + c] = acc[c];
                }
            }
    }

    /// <summary>(Reference: lead 22's HeroNormals bake) welded normals diffused over the edge graph, self + neighbours,
    /// renormalized, K = 2 (radius / mean edge)^2 passes clamped to 1..400. Per vertex xyz.</summary>
    public static float[] Diffuse(float[] pos, float[] nrm, int[] tri, float radius)
    {
        int n = pos.Length / 3;
        var wid = Weld(pos, n, out int W);
        var P = new float[W * 3]; var S = new float[W * 3];
        for (int v = 0; v < n; v++)
        {
            int w = wid[v];
            for (int c = 0; c < 3; c++) { P[3 * w + c] = pos[3 * v + c]; S[3 * w + c] += nrm[3 * v + c]; }
        }
        for (int w = 0; w < W; w++) Unit(S, w);
        var edges = new HashSet<long>(); double el = 0; long ec = 0;
        for (int t = 0; t + 2 < tri.Length; t += 3)
            for (int e = 0; e < 3; e++)
            {
                int a = wid[tri[t + e]], b = wid[tri[t + (e + 1) % 3]];
                if (a == b) continue;
                if (edges.Add(((long)Math.Min(a, b) << 32) | (uint)Math.Max(a, b)))
                {
                    float dx = P[3 * a] - P[3 * b], dy = P[3 * a + 1] - P[3 * b + 1], dz = P[3 * a + 2] - P[3 * b + 2];
                    el += MathF.Sqrt(dx * dx + dy * dy + dz * dz); ec++;
                }
            }
        var deg = new int[W + 1];
        foreach (var e in edges) { deg[(int)(e >> 32) + 1]++; deg[(int)(e & 0xFFFFFFFF) + 1]++; }
        for (int i = 0; i < W; i++) deg[i + 1] += deg[i];
        var adj = new int[deg[W]]; var fill = (int[])deg.Clone();
        foreach (var e in edges) { int a = (int)(e >> 32), b = (int)(e & 0xFFFFFFFF); adj[fill[a]++] = b; adj[fill[b]++] = a; }
        float mean = ec > 0 ? (float)(el / ec) : 0.01f, q = radius / Math.Max(mean, 1e-4f);
        int K = Math.Clamp((int)MathF.Round(2f * q * q), 1, 400);
        var n0 = S; var n1 = new float[W * 3];
        for (int it = 0; it < K; it++)
        {
            for (int i = 0; i < W; i++)
            {
                float x = n0[3 * i], y = n0[3 * i + 1], z = n0[3 * i + 2];
                for (int j = deg[i]; j < deg[i + 1]; j++) { int b = adj[j]; x += n0[3 * b]; y += n0[3 * b + 1]; z += n0[3 * b + 2]; }
                float l = x * x + y * y + z * z;
                if (l > 1e-20f) { float k = 1f / MathF.Sqrt(l); n1[3 * i] = x * k; n1[3 * i + 1] = y * k; n1[3 * i + 2] = z * k; }
                else { n1[3 * i] = n0[3 * i]; n1[3 * i + 1] = n0[3 * i + 1]; n1[3 * i + 2] = n0[3 * i + 2]; }
            }
            (n0, n1) = (n1, n0);
        }
        var o = new float[n * 3];
        for (int v = 0; v < n; v++) for (int c = 0; c < 3; c++) o[3 * v + c] = n0[3 * wid[v] + c];
        return o;
    }

    /// <summary>Angles in degrees between two per-vertex normal sets (xyz), sorted ascending (median = [n / 2]).</summary>
    public static float[] AnglesDeg(float[] a, float[] b)
    {
        int n = a.Length / 3; var d = new float[n];
        for (int v = 0; v < n; v++)
        {
            float c = a[3 * v] * b[3 * v] + a[3 * v + 1] * b[3 * v + 1] + a[3 * v + 2] * b[3 * v + 2];
            d[v] = MathF.Acos(Math.Clamp(c, -1f, 1f)) * 57.29578f;
        }
        Array.Sort(d); return d;
    }
}
