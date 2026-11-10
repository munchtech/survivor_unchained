using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SurvivorUnchained.View;

/// <summary>(L1 lead 14, D and D2) The canopy's shade as ONE leaf field (no Godot here: plain numbers, so a tool can draw the
/// same tile; the prototype and its preview: survivorsunchained_inputs/look_l1/work/d_canopy). Target 09's ground is a canopy
/// grown together with moonlit FIELDS left open in it: the SHADE is the connected phase, the light is islands (compact,
/// about 2 x 1.3 m, leaf-shaped outlines), the shade between them bands under a meter with a few regions of 3-4 m.
/// So the tile is laid out from the lit side: fields thrown apart (each two or three leaning ovals grown together, most
/// lying along x, the outline broken by noise), none where a slow noise is low (the regions of whole shade); a field grows
/// to the level the lit share asks for but never into the band kept between it and its neighbor (the distance to the
/// nearest OTHER field), so the shade stays in one piece and the light never links into lanes. The shade is then built
/// of LEAVES: a pointed leaf of three to five wide points at every 0.17 m of it, pointing out of the mass at its own angle.
/// The tile holds a COVER per texel, not a rank: the cover at which that texel closes (a leaf is flat in it, so it is
/// whole or gone), and the way from the texel to its leaf's STEM (stemX, stemY, m). The shader's one threshold draws, at
/// <see cref="C0"/>, the tile as designed (every leaf of the mass whole: the rim is whole leaves); where the cover falls
/// (the canopy's opening over her fire: the cover falls toward her, read AT THE STEM, so a leaf goes whole) the mass pulls
/// back leaf by leaf, the rim first, the deep last and in clumps, and its edge there is its own leaves' outlines, never
/// an arc; over C0 leaves grow out into the fields.</summary>
public static class CanopyField
{
    /// <summary>The cover the tile is drawn for (rigs.json dapple "cover" at this: the layout as designed).</summary>
    public const float C0 = 0.5f;
    /// <summary>The furthest a texel lies from its leaf's stem (m): the range the stems' offsets are stored over.</summary>
    public const float Stem = 1f;
    const float A = 0.04f;       // a leaf's own span of cover, stem to whole (small: a leaf is whole or gone, so a mass that pulls back shows whole leaves at its edge and no fringe of half-grown ones)
    const float Kv = 3f;         // past whole: cover per leaf length (steep, so a whole leaf stays its size; not a cliff, so its edge stays straight under the texture's filter)
    const float Kd = 0.25f;      // cover per meter of depth into the mass ...
    const float Dsat = 0.4f;     // ... to this depth; deeper, only the clumps' noise orders the leaves
    const float Nz = 0.4f;       // the clumps: cover spread inside the mass (a slow noise, about 2 m: the opening over her fire takes its outline from it)
    const float Ko = 0.25f;      // cover per meter out into a field (what closes as the cover rises past C0)
    const float BodyLag = 0.06f;  // the mass's own fill closes this much after the leaves over it
    const float Pitch = 0.34f;   // a leaf every this far (m), jittered
    const float GapMin = 0.05f, GapMax = 0.25f; // the shade band kept between two fields (m), by a slow noise
    const float Lean = 0.7f;     // the share of fields that lie along x (the rest any way)
    const float Grow = 0.6f;     // a field never grows further than this past its ovals (m): where no field was thrown, the shade stays whole
    const float Rho0 = 0.4f;     // the slow noise under this: no field (a BOUGH: a region of whole shade, 2-4 m, lying along x; the densest clump too, so it is what still stands in the opening over her fire)
    const float RimLag = 0.4f, RimIn = 0.3f; // the mass's own fill closes this much later at its rim, falling to nothing this far in (m): the rim is whole leaves, their outlines
    const float RimThin = 0.35f; // the share of leaves left out along the rim (each one left reads as a leaf, not a tooth of a saw)
    const float Hang = 0.3f;     // the share of leaves just off the rim that stand whole (a leaf hanging out of the mass)
    const float Join = 0.25f;    // the share of throws that grow onto an earlier field (fields joined in twos and threes)
    const float Turn = 2.2f;     // a leaf turns this far in all (rad) off the way out of its clump
    const int Gn = 1024;         // the layout's grid over the tile

    struct Lobe { public float X, Y, Ca, Sa, Rx, Ry; }

    /// <summary>The tile: P x P covers (0..1; a texel is shade where its value is under the shader's cover).
    /// fMin, fMax: the lit fields' length (m); leafMin, leafMax: a leaf's length (m); lobesMin, lobesMax: its points;
    /// run: the random run; lit: the lit share of the tile at C0 (the fields are grown until it holds, or until they meet
    /// their bands); shade: what it came to; stemX, stemY: from each texel to its leaf's stem (m; 0 where the mass's own fill shows).</summary>
    public static float[] Build(int P, float tile, float fMin, float fMax, float leafMin, float leafMax, int lobesMin, int lobesMax, int run, float lit, out float shade, out float[] stemX, out float[] stemY, Action<string>? log = null)
    {
        var rnd = new Random(20261109 + run * 7919);
        float cell = tile / Gn;
        // --- the fields: ovals thrown apart, each with one or two leaning ovals grown into it; a field is its ovals' union ---
        int ln1 = 7, ln2 = 11;
        float[] rho1 = Lattice(rnd, ln1), rho2 = Lattice(rnd, ln2);
        // the slow noise, its cells twice as long (x) as deep: low = a bough, a region of whole shade no field is thrown in
        float Slow(float x, float y) => 0.6f * Noise(rho1, ln1, x / tile, 2f * y / tile) + 0.4f * Noise(rho2, ln2, x / tile, 2f * y / tile);
        const int On = 256;
        var occ = new bool[On * On];
        var lobes = new List<Lobe>(); var ids = new List<int>(); var mains = new List<int>(); var joined = new List<int>();
        int nfield = 0;
        for (int tr = 0; tr < 24000; tr++)
        {
            float x = (float)rnd.NextDouble() * tile, y = (float)rnd.NextDouble() * tile;
            // (most fields short, a few three times as long; the larger a field, the more shade it keeps round it)
            float len = fMin + (fMax - fMin) * (float)Math.Pow(rnd.NextDouble(), 2.2), wid = len * (0.5f + 0.24f * (float)rnd.NextDouble());
            float ang = (float)((rnd.NextDouble() < Lean ? (rnd.NextDouble() - 0.5) * 1.5 : rnd.NextDouble() * Math.PI)), gap = 0.2f + 0.12f * len + 0.5f * (float)Math.Pow(rnd.NextDouble(), 1.5);
            double r1 = rnd.NextDouble(), r3 = rnd.NextDouble(), r4 = rnd.NextDouble(), r5 = rnd.NextDouble(), r6 = rnd.NextDouble(), r7 = rnd.NextDouble(), r8 = rnd.NextDouble(), r9 = rnd.NextDouble(), r10 = rnd.NextDouble(), r11 = rnd.NextDouble();
            double rj = rnd.NextDouble(), rk = rnd.NextDouble(), rl = rnd.NextDouble();
            int id = nfield;
            bool join = rj < Join && mains.Count > 0;
            if (join)
            {
                // grown onto an earlier field: off its end, a quarter into it, and one field with it (no band between them)
                int pm = mains[(int)(rk * mains.Count * 0.9999)];
                var pl = lobes[pm]; id = ids[pm];
                if (joined[id] >= 2) continue;
                float ja = MathF.Atan2(pl.Sa, pl.Ca) + ((float)rl - 0.5f) * 1.2f + ((tr & 1) == 0 ? 0 : MathF.PI), jd = 0.75f * (pl.Rx + len * 0.5f);
                x = Mod(pl.X + MathF.Cos(ja) * jd, tile); y = Mod(pl.Y + MathF.Sin(ja) * jd, tile);
            }
            float rho = Slow(x, y);
            if (r1 > Smooth(Rho0, Rho0 + 0.08f, rho)) continue;
            var main = new Lobe { X = x, Y = y, Ca = MathF.Cos(ang), Sa = MathF.Sin(ang), Rx = len * 0.5f, Ry = wid * 0.5f };
            if (Claimed(occ, On, tile, main, join ? 0 : gap) > (join ? 0.45f : 0.02f)) continue;
            lobes.Add(main); ids.Add(id); mains.Add(lobes.Count - 1); Claim(occ, On, tile, main);
            int more = 1 + (r3 < 0.55 ? 1 : 0);
            for (int k = 0; k < more; k++)
            {
                double a = k == 0 ? r4 : r8, b = k == 0 ? r5 : r9, c = k == 0 ? r6 : r10, d = k == 0 ? r7 : r11;
                float t = (k == 0 ? 1 : -1) * (0.35f + 0.4f * (float)a) * main.Rx, s = ((float)b - 0.5f) * 0.9f * main.Ry;
                float a2 = ang + ((float)c - 0.5f) * 1.5f;
                var sub = new Lobe { X = x + main.Ca * t - main.Sa * s, Y = y + main.Sa * t + main.Ca * s, Ca = MathF.Cos(a2), Sa = MathF.Sin(a2), Rx = main.Rx * (0.45f + 0.25f * (float)d), Ry = main.Ry * (0.6f + 0.35f * (float)a) };
                lobes.Add(sub); ids.Add(id); Claim(occ, On, tile, sub);
            }
            if (join) joined[id]++; else { joined.Add(0); nfield++; }
        }
        log?.Invoke($"  {nfield} fields");
        // the distance (m, about) to the nearest field and to the nearest OTHER field: a field grows to the level the lit
        // share asks for, but never into the band that is kept between it and its neighbor, so the shade stays in one piece
        var d1 = new float[Gn * Gn]; var d2 = new float[Gn * Gn]; var id1 = new int[Gn * Gn];
        Array.Fill(d1, 1e9f); Array.Fill(d2, 1e9f); Array.Fill(id1, -1);
        for (int li = 0; li < lobes.Count; li++)
        {
            var l = lobes[li]; int id = ids[li];
            float reach = MathF.Max(l.Rx, l.Ry) + 3.2f;
            int r = (int)(reach / cell) + 1, cx = (int)(l.X / cell), cy = (int)(l.Y / cell);
            for (int j = -r; j <= r; j++)
                for (int i = -r; i <= r; i++)
                {
                    float dx = (cx + i + 0.5f) * cell - l.X, dy = (cy + j + 0.5f) * cell - l.Y;
                    float u = (dx * l.Ca + dy * l.Sa) / l.Rx, v = (-dx * l.Sa + dy * l.Ca) / l.Ry, q = MathF.Sqrt(u * u + v * v);
                    float gr = MathF.Sqrt(u * u / (l.Rx * l.Rx) + v * v / (l.Ry * l.Ry));
                    float d = q < 1e-3f ? -MathF.Min(l.Rx, l.Ry) : (q - 1) * q / gr;
                    int k = Wrap(cy + j, Gn) * Gn + Wrap(cx + i, Gn);
                    if (id == id1[k]) { if (d < d1[k]) d1[k] = d; }
                    else if (d < d1[k]) { d2[k] = d1[k]; d1[k] = d; id1[k] = id; }
                    else if (d < d2[k]) d2[k] = d;
                }
        }
        int na = 19, nb = 23, nc = 43, nd = 47, ne = 13, nf = 17, ng = 11;
        float[] la = Lattice(rnd, na), lb = Lattice(rnd, nb), lc = Lattice(rnd, nc), ld = Lattice(rnd, nd), le = Lattice(rnd, ne), lf = Lattice(rnd, nf), lg = Lattice(rnd, ng);
        var clump = new float[Gn * Gn];
        var ga = new float[Gn * Gn]; var gb = new float[Gn * Gn];   // lit where ga > the level and gb > 0
        Parallel.For(0, Gn, j =>
        {
            for (int i = 0; i < Gn; i++)
            {
                float u = (i + 0.5f) / Gn, v = (j + 0.5f) / Gn;
                int k = j * Gn + i;
                ga[k] = -d1[k] + 0.4f * (Noise(la, na, u, v) + Noise(lb, nb, u, v) - 1f) + 0.12f * (Noise(lc, nc, u, v) + Noise(ld, nd, u, v) - 1f);
                gb[k] = 0.5f * (d2[k] - d1[k]) - 0.5f * (GapMin + (GapMax - GapMin) * Noise(lg, ng, u, v)) + 0.06f * (Noise(lc, nc, v, u) + Noise(ld, nd, v, u) - 1f);
                // the clumps: a bough whole (the slow noise low), the rest by a small noise; what outlasts the opening over her fire is the boughs
                clump[k] = 0.8f * (1f - Smooth(Rho0 - 0.03f, Rho0 + 0.15f, Slow(u * tile, v * tile))) + 0.1f * (Noise(le, ne, u, v) + Noise(lf, nf, u, v));
            }
        });
        // --- the leaves' own numbers, drawn once (the same leaves whatever the fields' level and the tile's resolution) ---
        int ncell = (int)MathF.Round(tile / Pitch);
        float pitch = tile / ncell;
        var lr = new float[ncell * ncell * 16];
        for (int i = 0; i < lr.Length; i++) lr[i] = (float)rnd.NextDouble();
        // --- the fields grown until the lit share holds (the leaves round a field take some of it back) ---
        var open = new List<float>(Gn * Gn);
        for (int k = 0; k < ga.Length; k++) if (gb[k] > 0 && ga[k] > -Grow) open.Add(ga[k]);
        var sorted = open.ToArray();
        Array.Sort(sorted);
        float nominal = MathF.Min(lit + 0.1f, 0.9f);
        const int Pc = 512;
        shade = 0;
        for (int it = 0; it < 5; it++)
        {
            var c = Draw(Pc, tile, ga, gb, sorted, nominal, clump, lr, ncell, pitch, leafMin, leafMax, lobesMin, lobesMax, out float sh, null, null);
            log?.Invoke($"  nominal lit {nominal:0.000} -> lit {1 - sh:0.000}");
            float err = lit - (1 - sh);
            if (MathF.Abs(err) < 0.004f) break;
            nominal = Math.Clamp(nominal + err, 0.02f, 0.98f);
        }
        stemX = new float[P * P]; stemY = new float[P * P];
        return Draw(P, tile, ga, gb, sorted, nominal, clump, lr, ncell, pitch, leafMin, leafMax, lobesMin, lobesMax, out shade, stemX, stemY);
    }

    static float[] Draw(int P, float tile, float[] ga, float[] gb, float[] sorted, float nominal, float[] clump, float[] lr, int ncell, float pitch, float leafMin, float leafMax, int lobesMin, int lobesMax, out float shade, float[]? stemX, float[]? stemY)
    {
        float cell = tile / Gn, m = P / tile;
        float thr = sorted[Math.Clamp(sorted.Length - (int)(nominal * Gn * Gn), 0, sorted.Length - 1)];
        // signed distance to the fields' edge (m; under 0 in the shade), wrapped
        const int pad = 112;
        int n = Gn + 2 * pad;
        var inLit = new float[n * n]; var inShade = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                int gk = Wrap(j - pad, Gn) * Gn + Wrap(i - pad, Gn);
                bool litHere = gb[gk] > 0 && ga[gk] > thr && ga[gk] > -Grow;
                inLit[j * n + i] = litHere ? 0 : 1e12f; inShade[j * n + i] = litHere ? 1e12f : 0;
            }
        Edt(inLit, n); Edt(inShade, n);
        // the cover the mass itself closes at (v): in the shade from C0 down with depth and the clumps, in a field from C0 + A up
        var v = new float[Gn * Gn]; var sd = new float[Gn * Gn]; var vb = new float[Gn * Gn];
        for (int j = 0; j < Gn; j++)
            for (int i = 0; i < Gn; i++)
            {
                int k = (j + pad) * n + i + pad;
                float din = MathF.Sqrt(inLit[k]) * cell, dout = MathF.Sqrt(inShade[k]) * cell;
                bool litHere = inLit[k] == 0;
                sd[j * Gn + i] = litHere ? dout - 0.5f * cell : -(din - 0.5f * cell);
                v[j * Gn + i] = litHere ? MathF.Min(C0 + A + Ko * dout, 1f) : C0 - Kd * MathF.Min(din, Dsat) - Nz * clump[j * Gn + i];
                vb[j * Gn + i] = v[j * Gn + i] + BodyLag + (litHere ? 0 : RimLag * MathF.Max(0, 1 - din / RimIn));
            }
        var px = new float[P * P];
        Array.Fill(px, 1f);
        // the leaves
        var leaves = new List<(float X, float Y, float Full, float Reach, float[] K)>();
        for (int cj = 0; cj < ncell; cj++)
            for (int ci = 0; ci < ncell; ci++)
            {
                int o = (cj * ncell + ci) * 16;
                float x = (ci + lr[o]) * pitch, y = (cj + lr[o + 1]) * pitch;
                float gx = x / cell - 0.5f, gy = y / cell - 0.5f;
                float d = Bil(sd, Gn, gx, gy);
                if (d > 0.6f || (MathF.Abs(d) < RimIn && lr[o + 15] < RimThin)) continue;
                int gi = Wrap((int)MathF.Floor(gx + 0.5f), Gn), gj = Wrap((int)MathF.Floor(gy + 0.5f), Gn);
                float full = v[gj * Gn + gi] + (lr[o + 2] - 0.5f) * 0.02f;
                // (a loose leaf now and then, lying whole just off the mass)
                if (d > 0.25f && d < 0.55f && lr[o + 3] < 0.022f) full = C0 - 0.04f;
                // (and leaves hanging out of the rim: whole, and gone with the rim they hang from)
                if (d > 0 && d <= 0.25f && lr[o + 3] < Hang) full = C0 - 0.04f - Nz * clump[gj * Gn + gi];
                // its way: out of its clump (up the cover: out of the mass at its rim, out of what still stands where the canopy opens), turned as it likes
                float ex = Bil(v, Gn, gx + 3, gy) - Bil(v, Gn, gx - 3, gy), ey = Bil(v, Gn, gx, gy + 3) - Bil(v, Gn, gx, gy - 3);
                float way = (ex * ex + ey * ey > 1e-8f ? MathF.Atan2(ey, ex) : lr[o + 4] * MathF.Tau) + (lr[o + 4] - 0.5f) * Turn;
                float len = leafMin + (leafMax - leafMin) * MathF.Pow(lr[o + 5], 1.2f);
                int points = lobesMin + (int)(lr[o + 6] * (lobesMax - lobesMin + 1) * 0.9999f);
                // its points (kites from the stem's head): ca, sa, 1/length, 1/back, 1/half-width each
                int nk = Math.Clamp(points, 1, 5);
                var k = new float[nk * 5];
                float reach = 0;
                for (int q = 0; q < nk; q++)
                {
                    float a, l, back, hw;
                    if (q == 0) { a = way; l = len; back = len * 0.28f; hw = len * (0.5f + 0.1f * lr[o + 7]); }
                    else if (q <= 2) { a = way + (q == 1 ? 1 : -1) * (0.78f + 0.35f * lr[o + 7 + q]); l = len * (0.62f + 0.22f * lr[o + 9 + q]); back = len * 0.12f; hw = l * (0.5f + 0.1f * lr[o + 11 + q]); }
                    else { a = way + (q == 3 ? 1 : -1) * (1.75f + 0.3f * lr[o + 10 + q]); l = len * (0.36f + 0.16f * lr[o + 8 + q]); back = len * 0.1f; hw = l * 0.45f; }
                    k[q * 5] = MathF.Cos(a); k[q * 5 + 1] = MathF.Sin(a); k[q * 5 + 2] = 1 / l; k[q * 5 + 3] = 1 / back; k[q * 5 + 4] = 1 / hw;
                    reach = MathF.Max(reach, l);
                }
                float gmax = 1 + MathF.Max(1 - full, 0) / Kv;
                leaves.Add((x, y, full, reach * gmax + 1.5f / m, k));
            }
        // stamped in strips (each strip writes its own rows only)
        const int Strips = 32;
        int rows = P / Strips;
        var per = new List<int>[Strips];
        for (int s = 0; s < Strips; s++) per[s] = new List<int>();
        for (int li = 0; li < leaves.Count; li++)
        {
            var lf = leaves[li];
            int y0 = (int)MathF.Floor((lf.Y - lf.Reach) * m), y1 = (int)MathF.Ceiling((lf.Y + lf.Reach) * m);
            int s0 = (int)MathF.Floor((float)y0 / rows), s1 = (int)MathF.Floor((float)y1 / rows);
            for (int s = s0; s <= s1 && s - s0 < Strips; s++) per[Wrap(s, Strips)].Add(li);
        }
        Parallel.For(0, Strips, s =>
        {
            int top = s * rows, bottom = s == Strips - 1 ? P : top + rows;
            foreach (int li in per[s])
            {
                var (lx, ly, full, reach, k) = leaves[li];
                int x0 = (int)MathF.Floor((lx - reach) * m), x1 = (int)MathF.Ceiling((lx + reach) * m);
                int y0 = (int)MathF.Floor((ly - reach) * m), y1 = (int)MathF.Ceiling((ly + reach) * m);
                int nk = k.Length / 5;
                for (int yy = y0; yy <= y1; yy++)
                {
                    int wy = Wrap(yy, P);
                    if (wy < top || wy >= bottom) continue;
                    float dy = (yy + 0.5f) / m - ly;
                    for (int xx = x0; xx <= x1; xx++)
                    {
                        float dx = (xx + 0.5f) / m - lx, gg = float.MaxValue;
                        for (int q = 0; q < nk; q++)
                        {
                            float u = dx * k[q * 5] + dy * k[q * 5 + 1], w = MathF.Abs(-dx * k[q * 5 + 1] + dy * k[q * 5]);
                            float gq = (u >= 0 ? u * k[q * 5 + 2] : -u * k[q * 5 + 3]) + w * k[q * 5 + 4];
                            if (gq < gg) gg = gq;
                        }
                        float val = gg <= 1 ? full - A * (1 - gg) : full + Kv * (gg - 1);
                        int idx = wy * P + Wrap(xx, P);
                        if (val < px[idx]) { px[idx] = val; if (stemX != null) { stemX[idx] = -dx; stemY![idx] = -dy; } }
                    }
                }
            }
        });
        // the mass's own fill under the leaves, and the count
        long closed = 0;
        object gate = new();
        Parallel.For(0, P, () => 0L, (j, _, acc) =>
        {
            for (int i = 0; i < P; i++)
            {
                float b = Bil(vb, Gn, (i + 0.5f) / m / cell - 0.5f, (j + 0.5f) / m / cell - 0.5f);
                int idx = j * P + i;
                if (b < px[idx]) { px[idx] = b; if (stemX != null) { stemX[idx] = 0; stemY![idx] = 0; } }
                if (px[idx] < 0) px[idx] = 0;
                if (px[idx] < C0) acc++;
            }
            return acc;
        }, acc => { lock (gate) closed += acc; });
        shade = (float)closed / px.Length;
        return px;
    }

    static int Wrap(int i, int n) => ((i % n) + n) % n;
    static float Mod(float a, float n) => ((a % n) + n) % n;
    static float Smooth(float a, float b, float x) { float t = Math.Clamp((x - a) / (b - a), 0f, 1f); return t * t * (3 - 2 * t); }
    static float[] Lattice(Random r, int n) { var a = new float[n * n]; for (int i = 0; i < a.Length; i++) a[i] = (float)r.NextDouble(); return a; }
    // a wrapped value noise (u, v over the tile, 0..1)
    static float Noise(float[] lat, int n, float u, float v)
    {
        float x = u * n, y = v * n;
        int x0 = (int)MathF.Floor(x), y0 = (int)MathF.Floor(y);
        float fx = x - x0, fy = y - y0;
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
        int xa = Wrap(x0, n), xb = Wrap(x0 + 1, n), ya = Wrap(y0, n), yb = Wrap(y0 + 1, n);
        float a = lat[ya * n + xa] + (lat[ya * n + xb] - lat[ya * n + xa]) * fx, b = lat[yb * n + xa] + (lat[yb * n + xb] - lat[yb * n + xa]) * fx;
        return a + (b - a) * fy;
    }
    static float Bil(float[] a, int n, float x, float y)
    {
        int x0 = (int)MathF.Floor(x), y0 = (int)MathF.Floor(y);
        float fx = x - x0, fy = y - y0;
        int xa = Wrap(x0, n), xb = Wrap(x0 + 1, n), ya = Wrap(y0, n), yb = Wrap(y0 + 1, n);
        float p = a[ya * n + xa] + (a[ya * n + xb] - a[ya * n + xa]) * fx, q = a[yb * n + xa] + (a[yb * n + xb] - a[yb * n + xa]) * fx;
        return p + (q - p) * fy;
    }
    // how much of an oval (grown by gap) is claimed already, and claiming it
    static float Claimed(bool[] occ, int on, float tile, Lobe l, float gap)
    {
        float c = tile / on, rx = l.Rx + gap, ry = l.Ry + gap;
        int r = (int)(MathF.Max(rx, ry) / c) + 1, cx = (int)(l.X / c), cy = (int)(l.Y / c), all = 0, hit = 0;
        for (int j = -r; j <= r; j++)
            for (int i = -r; i <= r; i++)
            {
                float dx = (cx + i + 0.5f) * c - l.X, dy = (cy + j + 0.5f) * c - l.Y;
                float u = (dx * l.Ca + dy * l.Sa) / rx, v = (-dx * l.Sa + dy * l.Ca) / ry;
                if (u * u + v * v > 1) continue;
                all++; if (occ[Wrap(cy + j, on) * on + Wrap(cx + i, on)]) hit++;
            }
        return all > 0 ? (float)hit / all : 1;
    }
    static float Claim(bool[] occ, int on, float tile, Lobe l)
    {
        float c = tile / on;
        int r = (int)(MathF.Max(l.Rx, l.Ry) / c) + 1, cx = (int)(l.X / c), cy = (int)(l.Y / c), added = 0;
        for (int j = -r; j <= r; j++)
            for (int i = -r; i <= r; i++)
            {
                float dx = (cx + i + 0.5f) * c - l.X, dy = (cy + j + 0.5f) * c - l.Y;
                float u = (dx * l.Ca + dy * l.Sa) / l.Rx, v = (-dx * l.Sa + dy * l.Ca) / l.Ry;
                if (u * u + v * v > 1) continue;
                int k = Wrap(cy + j, on) * on + Wrap(cx + i, on);
                if (!occ[k]) { occ[k] = true; added++; }
            }
        return (float)added / (on * on);
    }
    // squared distance to the nearest zero cell, in place (Felzenszwalb and Huttenlocher), cells
    static void Edt(float[] f, int n)
    {
        Parallel.For(0, n, () => (new float[n], new float[n], new int[n], new float[n + 1]), (i, _, t) =>
        {
            var (src, dst, vv, zz) = t;
            for (int j = 0; j < n; j++) src[j] = f[j * n + i];
            Dt(src, dst, vv, zz, n);
            for (int j = 0; j < n; j++) f[j * n + i] = dst[j];
            return t;
        }, _ => { });
        Parallel.For(0, n, () => (new float[n], new float[n], new int[n], new float[n + 1]), (j, _, t) =>
        {
            var (src, dst, vv, zz) = t;
            Array.Copy(f, j * n, src, 0, n);
            Dt(src, dst, vv, zz, n);
            Array.Copy(dst, 0, f, j * n, n);
            return t;
        }, _ => { });
    }
    static void Dt(float[] f, float[] d, int[] v, float[] z, int n)
    {
        int k = 0; v[0] = 0; z[0] = float.NegativeInfinity; z[1] = float.PositiveInfinity;
        for (int q = 1; q < n; q++)
        {
            float s;
            while (true)
            {
                int p = v[k];
                s = ((f[q] + (float)q * q) - (f[p] + (float)p * p)) / (2f * q - 2f * p);
                if (s <= z[k] && k > 0) k--; else break;
            }
            k++; v[k] = q; z[k] = s; z[k + 1] = float.PositiveInfinity;
        }
        k = 0;
        for (int q = 0; q < n; q++)
        {
            while (z[k + 1] < q) k++;
            int p = v[k];
            d[q] = (q - p) * (float)(q - p) + f[p];
        }
    }
}
