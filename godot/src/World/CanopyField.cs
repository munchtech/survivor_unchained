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
    /// <summary>The furthest a texel lies from its ANCHOR (m): the range the offsets are stored over. (L1 lead 16, D3) The
    /// anchor is the center of the leaf's CLUSTER, not its stem: the shade is laid out in clusters (a center every
    /// <see cref="ClusterPitch"/>, the mass cut along the lines between them), a cluster's cover lowest at its heart and
    /// rising to the lines, and the shader reads her fire's distance at the anchor. So over her fire a cluster is whole or
    /// gone (never cut by an arc), stands small where the cover is low and grows leaf by leaf until it meets its neighbors:
    /// between the unbroken core and the whole canopy the shade is leaf clusters with her fire between them, a bough too.</summary>
    public const float Stem = 3f;
    const float A = 0.04f;       // a leaf's own span of cover, stem to whole (small: a leaf is whole or gone, so a mass that pulls back shows whole leaves at its edge and no fringe of half-grown ones)
    const float Kv = 3f;         // past whole: cover per leaf length (steep, so a whole leaf stays its size; not a cliff, so its edge stays straight under the texture's filter)
    const float Kd = 0.1f;       // cover per meter of depth into the mass ...
    const float Dsat = 0.4f;     // ... to this depth (on the lines between clusters: the mass's rim closes last there)
    const float ClusterPitch = 2.2f; // a leaf cluster's center every this far (m), jittered
    const float ClusterJit = 0.7f;   // ... by this share of the pitch
    const float Wg = 0.75f;      // a cluster's cover rises from its heart's to the top over this far in from the line between two clusters (m)
    const float Vlo = 0.12f, Vhi = 0.3f; // a cluster's own cover at its heart (each its own: which stand nearest her fire)
    const float Vtop = C0 - 0.08f;   // the cover on the line between two clusters (the mass is whole from here up)
    const float Ko = 0.25f;      // cover per meter out into a field (what closes as the cover rises past C0)
    const float BodyLag = 0.06f;  // the mass's own fill closes this much after the leaves over it
    const float Pitch = 0.34f;   // a leaf every this far (m), jittered
    const float GapMin = 0.05f, GapMax = 0.25f; // the shade band kept between two fields (m), by a slow noise
    const float Lean = 0.7f;     // the share of fields that lie along x (the rest any way)
    const float Grow = 0.6f;     // a field never grows further than this past its ovals (m): where no field was thrown, the shade stays whole
    const float Rho0 = 0.4f;     // the slow noise under this: no field (a BOUGH: a region of whole shade, 2-4 m, lying along x; the densest clump too, so it is what still stands in the opening over her fire)
    const float RimLag = 0.4f, RimIn = 0.3f; // the mass's own fill closes this much later at its rim, falling to nothing this far in (m): the rim is whole leaves, their outlines
    const float RimThin = 0.35f; // the share of leaves left out along the rim (each one left reads as a leaf, not a tooth of a saw)
    const float Hang = 0.12f;    // the share of leaves just off the rim that stand whole (a leaf hanging out of the mass)
    const float Join = 0.25f;    // the share of throws that grow onto an earlier field (fields joined in twos and threes)
    const float Turn = 2.2f;     // a leaf turns this far in all (rad) off the way out of its clump
    const int Gn = 1024;         // the layout's grid over the tile

    struct Lobe { public float X, Y, Ca, Sa, Rx, Ry; }

    /// <summary>The tile: P x P covers (0..1; a texel is shade where its value is under the shader's cover).
    /// fMin, fMax: the lit fields' length (m); leafMin, leafMax: a leaf's length (m); lobesMin, lobesMax: its points;
    /// run: the random run; lit: the lit share of the tile at C0 (the fields are grown until it holds, or until they meet
    /// their bands); shade: what it came to; stemX, stemY: from each texel to its leaf's stem (m; 0 where the mass's own fill shows).</summary>
    public static float[] Build(int P, float tile, float fMin, float fMax, float leafMin, float leafMax, int lobesMin, int lobesMax, int run, float lit, out float shade, out float[] stemX, out float[] stemY, Action<string>? log = null)
        => run >= MassesRun ? BuildMasses(P, tile, fMin, fMax, leafMin, leafMax, lobesMin, lobesMax, run - MassesRun, lit, out shade, out stemX, out stemY, log)
            : BuildFields(P, tile, fMin, fMax, leafMin, leafMax, lobesMin, lobesMax, run, lit, out shade, out stemX, out stemY, log);

    /// <summary>The layout of lead 14 to 16 (lit fields thrown into one shade, clusters): a run under <see cref="MassesRun"/>.</summary>
    static float[] BuildFields(int P, float tile, float fMin, float fMax, float leafMin, float leafMax, int lobesMin, int lobesMax, int run, float lit, out float shade, out float[] stemX, out float[] stemY, Action<string>? log = null)
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
        // the clusters: centers on a jittered grid, each its own cover; a grid point belongs to the nearest (its place bent
        // by a noise, so the lines between clusters are not straight)
        int cn = Math.Max(3, (int)MathF.Round(tile / ClusterPitch));
        float cp = tile / cn;
        var ccx = new float[cn * cn]; var ccy = new float[cn * cn]; var ccv = new float[cn * cn];
        for (int j = 0; j < cn; j++)
            for (int i = 0; i < cn; i++)
            {
                ccx[j * cn + i] = (i + 0.5f + ((float)rnd.NextDouble() - 0.5f) * ClusterJit) * cp;
                ccy[j * cn + i] = (j + 0.5f + ((float)rnd.NextDouble() - 0.5f) * ClusterJit) * cp;
                ccv[j * cn + i] = Vlo + (Vhi - Vlo) * MathF.Pow((float)rnd.NextDouble(), 1.4f);
            }
        var cid = new int[Gn * Gn];       // the cluster a grid point belongs to
        var vs = new float[Gn * Gn];      // the cover it closes at as shade, before the mass's rim (Draw)
        var gl = new float[Gn * Gn];      // 1 on the line between two clusters, 0 at a cluster's heart
        var ga = new float[Gn * Gn]; var gb = new float[Gn * Gn];   // lit where ga > the level and gb > 0
        Parallel.For(0, Gn, j =>
        {
            for (int i = 0; i < Gn; i++)
            {
                float u = (i + 0.5f) / Gn, v = (j + 0.5f) / Gn;
                int k = j * Gn + i;
                ga[k] = -d1[k] + 0.4f * (Noise(la, na, u, v) + Noise(lb, nb, u, v) - 1f) + 0.12f * (Noise(lc, nc, u, v) + Noise(ld, nd, u, v) - 1f);
                gb[k] = 0.5f * (d2[k] - d1[k]) - 0.5f * (GapMin + (GapMax - GapMin) * Noise(lg, ng, u, v)) + 0.06f * (Noise(lc, nc, v, u) + Noise(ld, nd, v, u) - 1f);
                float qx = u * tile + 0.5f * (Noise(le, ne, u, v) - 0.5f) + 0.2f * (Noise(lc, nc, u, v) - 0.5f), qy = v * tile + 0.5f * (Noise(lf, nf, u, v) - 0.5f) + 0.2f * (Noise(ld, nd, u, v) - 0.5f);
                int ci0 = (int)MathF.Floor(qx / cp), cj0 = (int)MathF.Floor(qy / cp), best = 0;
                float f1 = 1e9f, f2 = 1e9f, bx = 0, by = 0, sx2 = 0, sy2 = 0;
                for (int cj = cj0 - 2; cj <= cj0 + 2; cj++)
                    for (int ci = ci0 - 2; ci <= ci0 + 2; ci++)
                    {
                        int c = Wrap(cj, cn) * cn + Wrap(ci, cn);
                        float ddx = Md(ccx[c] - qx, tile), ddy = Md(ccy[c] - qy, tile), dd = ddx * ddx + ddy * ddy;
                        if (dd < f1) { f2 = f1; sx2 = bx; sy2 = by; f1 = dd; bx = ddx; by = ddy; best = c; }
                        else if (dd < f2) { f2 = dd; sx2 = ddx; sy2 = ddy; }
                    }
                // (the distance to the line between the nearest two)
                float edge = (f2 - f1) / (2f * MathF.Max(MathF.Sqrt((sx2 - bx) * (sx2 - bx) + (sy2 - by) * (sy2 - by)), 1e-3f));
                cid[k] = best;
                gl[k] = 1f - Smooth(0f, Wg, edge);
                vs[k] = ccv[best] + (Vtop - ccv[best]) * gl[k];
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
            var c = Draw(Pc, tile, ga, gb, sorted, nominal, vs, gl, cid, ccx, ccy, lr, ncell, pitch, leafMin, leafMax, lobesMin, lobesMax, out float sh, null, null);
            log?.Invoke($"  nominal lit {nominal:0.000} -> lit {1 - sh:0.000}");
            float err = lit - (1 - sh);
            if (MathF.Abs(err) < 0.004f) break;
            nominal = Math.Clamp(nominal + err, 0.02f, 0.98f);
        }
        stemX = new float[P * P]; stemY = new float[P * P];
        return Draw(P, tile, ga, gb, sorted, nominal, vs, gl, cid, ccx, ccy, lr, ncell, pitch, leafMin, leafMax, lobesMin, lobesMax, out shade, stemX, stemY);
    }

    static float[] Draw(int P, float tile, float[] ga, float[] gb, float[] sorted, float nominal, float[] vs, float[] gl, int[] cid, float[] ccx, float[] ccy, float[] lr, int ncell, float pitch, float leafMin, float leafMax, int lobesMin, int lobesMax, out float shade, float[]? stemX, float[]? stemY)
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
        // the cover the mass itself closes at (v): in the shade its cluster's (low at the heart, the top on the lines between
        // clusters, where the mass's rim closes last), in a field from C0 + A up
        var v = new float[Gn * Gn]; var sd = new float[Gn * Gn]; var vb = new float[Gn * Gn];
        for (int j = 0; j < Gn; j++)
            for (int i = 0; i < Gn; i++)
            {
                int k = (j + pad) * n + i + pad;
                float din = MathF.Sqrt(inLit[k]) * cell, dout = MathF.Sqrt(inShade[k]) * cell;
                bool litHere = inLit[k] == 0;
                sd[j * Gn + i] = litHere ? dout - 0.5f * cell : -(din - 0.5f * cell);
                v[j * Gn + i] = litHere ? MathF.Min(C0 + A + Ko * dout, 1f) : vs[j * Gn + i] + gl[j * Gn + i] * Kd * (Dsat - MathF.Min(din, Dsat));
                vb[j * Gn + i] = v[j * Gn + i] + BodyLag + (litHere ? 0 : RimLag * MathF.Max(0, 1 - din / RimIn));
            }
        var px = new float[P * P];
        Array.Fill(px, 1f);
        // the leaves
        var leaves = new List<(float X, float Y, float Full, float Reach, float[] K, float Cx, float Cy)>();
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
                if (d > 0 && d <= 0.25f && lr[o + 3] < Hang) full = vs[gj * Gn + gi];
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
                leaves.Add((x, y, full, reach * gmax + 1.5f / m, k, ccx[cid[gj * Gn + gi]], ccy[cid[gj * Gn + gi]]));
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
                var (lx, ly, full, reach, k, acx, acy) = leaves[li];
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
                        if (val < px[idx]) { px[idx] = val; if (stemX != null) { stemX[idx] = Md(acx - (xx + 0.5f) / m, tile); stemY![idx] = Md(acy - (yy + 0.5f) / m, tile); } }
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
                if (b < px[idx])
                {
                    px[idx] = b;
                    if (stemX != null)
                    {
                        int c = cid[Math.Clamp((int)((j + 0.5f) / m / cell), 0, Gn - 1) * Gn + Math.Clamp((int)((i + 0.5f) / m / cell), 0, Gn - 1)];
                        stemX[idx] = Md(ccx[c] - (i + 0.5f) / m, tile); stemY![idx] = Md(ccy[c] - (j + 0.5f) / m, tile);
                    }
                }
                if (px[idx] < 0) px[idx] = 0;
                if (px[idx] < C0) acc++;
            }
            return acc;
        }, acc => { lock (gate) closed += acc; });
        shade = (float)closed / px.Length;
        return px;
    }

    // ---- (L1 lead 17, F) THE MASSES: a few broad calm masses of shade, the leaves only along their borders ----
    /// <summary>A rig's dapple "mass" run from here up asks for the MASSES layout (run - MassesRun is its random run; "mass" min
    /// and max are then a mass's size across, m): the shade is a slow field cut at one level (masses and lit fields of the
    /// same order, both whole inside, longer along x than deep), no piece of either under <see cref="MSmall"/>; the leaf
    /// drawing lives on the borders (leaves pointing out of the mass, stretches of them dense, stretches nearly plain, a
    /// lone leaf now and then just off an edge). The mass itself is leaves too, each with the cover of its own depth into
    /// the mass and anchored at itself, and what no leaf covers goes with the nearest leaf: so where the canopy opens over
    /// her fire a mass pulls back to its core leaf by leaf and its edge there is a leafy border like any other.</summary>
    public const int MassesRun = 100;
    const float MAniso = 1.4f;    // a mass is this much longer along x than it is deep
    const float MCell = 0.75f;    // the slow field's cell (m) per meter of the mean mass size
    const float MOct = 0.35f;     // the weight of the second, finer field (the masses' lobes and necks)
    const float MWarp = 1.3f;     // the slow field's ground is bent this far (m): no outline follows the lattice
    const float MWob = 0.08f;     // the weight of the outline's own small wobble (what a plain stretch of border shows)
    const float MSmall = 1.6f;    // a piece of shade or of light under this (m2) is given to the other phase
    const float MKd = 0.2f;       // cover per meter of depth into a mass: over her fire a mass stands from its core out
    const float MVlo = 0.1f, MVtop = C0 - 0.06f; // the cover deep in a mass and at its outline
    const float MPitch = 0.3f;    // a leaf every this far (m), jittered
    const float MOut = 0.45f;     // a border leaf's center lies at most this far outside the outline (a dense stretch)
    const float MDense = 0.34f;   // the border noise under this: a plain stretch (few leaves, small, the outline itself shows)
    const float MLone = 0.05f;    // the share of sites 0.4-0.9 m off a border that hold a lone leaf
    const float MKr = 3f;         // the fill's cover per meter across the outline (its edge under the texture's filter)
    const float MTurn = 3.0f;     // a leaf turns this far in all (rad) off the way out of its mass

    static float[] BuildMasses(int P, float tile, float mMin, float mMax, float leafMin, float leafMax, int lobesMin, int lobesMax, int run, float lit, out float shade, out float[] stemX, out float[] stemY, Action<string>? log)
    {
        var rnd = new Random(20261110 + run * 7919);
        float mean = 0.5f * (mMin + mMax);
        int n1x = Math.Max(3, (int)MathF.Round(tile / (MCell * mean))), n1y = Math.Max(3, (int)MathF.Round(n1x * MAniso));
        int n2x = Math.Max(5, (int)MathF.Round(tile / (MCell * mMin * 0.55f))), n2y = Math.Max(5, (int)MathF.Round(n2x * MAniso));
        const int nw = 9, n3 = 40, nb = 13;
        float[] l1 = Lattice2(rnd, n1x, n1y), l2 = Lattice2(rnd, n2x, n2y), wa = Lattice(rnd, nw), wb = Lattice(rnd, nw), l3 = Lattice(rnd, n3), lb = Lattice(rnd, nb);
        var f = new float[Gn * Gn];
        Parallel.For(0, Gn, j =>
        {
            for (int i = 0; i < Gn; i++)
            {
                float u = (i + 0.5f) / Gn, w = (j + 0.5f) / Gn;
                float uw = u + MWarp / tile * (2 * Noise(wa, nw, u, w) - 1), ww = w + MWarp / tile / MAniso * (2 * Noise(wb, nw, u, w) - 1);
                f[j * Gn + i] = Noise2(l1, n1x, n1y, uw, ww) + MOct * Noise2(l2, n2x, n2y, uw, ww) + MWob * Noise(l3, n3, u, w);
            }
        });
        var sorted = (float[])f.Clone(); Array.Sort(sorted);
        int ncell = (int)MathF.Round(tile / MPitch); float pitch = tile / ncell;
        var lr = new float[ncell * ncell * 16];
        for (int i = 0; i < lr.Length; i++) lr[i] = (float)rnd.NextDouble();
        // the level: the lit share is counted on the drawn tile (the leaves hang over the outline), the level moved to it
        float nominal = lit + 0.06f; float[]? px = null; shade = 0;
        stemX = new float[P * P]; stemY = new float[P * P];
        for (int pass = 0; pass < 3; pass++)
        {
            bool last = pass == 2;
            int Pp = last ? P : Math.Min(P, 1024);
            px = DrawMasses(Pp, tile, f, sorted[Math.Clamp((int)((1 - nominal) * Gn * Gn), 0, sorted.Length - 1)], lb, nb, lr, ncell, pitch, leafMin, leafMax, lobesMin, lobesMax, out shade, last ? stemX : null, last ? stemY : null, out int pieces, out int fields);
            log?.Invoke($"  masses pass {pass}: level for lit {nominal:0.000}, drawn lit {1 - shade:0.000}, {pieces} masses, {fields} lit fields");
            if (!last) nominal = Math.Clamp(nominal + (lit - (1 - shade)), 0.05f, 0.95f);
        }
        return px!;
    }

    static float[] DrawMasses(int P, float tile, float[] f, float thr, float[] lb, int nb, float[] lr, int ncell, float pitch, float leafMin, float leafMax, int lobesMin, int lobesMax, out float shade, float[]? stemX, float[]? stemY, out int pieces, out int fields)
    {
        float cell = tile / Gn, m = P / tile;
        var sh = new bool[Gn * Gn];
        for (int k = 0; k < sh.Length; k++) sh[k] = f[k] < thr;
        int minCells = (int)(MSmall / (cell * cell));
        pieces = DropSmall(sh, Gn, true, minCells); fields = DropSmall(sh, Gn, false, minCells);
        // signed distance to the outline (m; under 0 in the shade), wrapped
        const int pad = 112;
        int n = Gn + 2 * pad;
        var inLit = new float[n * n]; var inShade = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                bool s = sh[Wrap(j - pad, Gn) * Gn + Wrap(i - pad, Gn)];
                inLit[j * n + i] = s ? 1e12f : 0; inShade[j * n + i] = s ? 0 : 1e12f;
            }
        Edt(inLit, n); Edt(inShade, n);
        var sd = new float[Gn * Gn];
        for (int j = 0; j < Gn; j++)
            for (int i = 0; i < Gn; i++)
            {
                int k = (j + pad) * n + i + pad;
                sd[j * Gn + i] = sh[j * Gn + i] ? -(MathF.Sqrt(inLit[k]) * cell - 0.5f * cell) : MathF.Sqrt(inShade[k]) * cell - 0.5f * cell;
            }
        var px = new float[P * P]; Array.Fill(px, 1f);
        var gbest = new float[P * P]; Array.Fill(gbest, float.MaxValue);
        var fbest = new float[P * P]; var bx = new float[P * P]; var by = new float[P * P];
        var leaves = new List<(float X, float Y, float Full, float Reach, float[] K)>();
        for (int cj = 0; cj < ncell; cj++)
            for (int ci = 0; ci < ncell; ci++)
            {
                int o = (cj * ncell + ci) * 16;
                float x = (ci + lr[o]) * pitch, y = (cj + lr[o + 1]) * pitch;
                float gx = x / cell - 0.5f, gy = y / cell - 0.5f;
                float d = Bil(sd, Gn, gx, gy);
                if (d > 0.9f) continue;
                bool dense = Noise(lb, nb, x / tile, y / tile) > MDense, lone = false;
                if (d > (dense ? MOut : 0.02f)) { if (d > 0.4f && lr[o + 3] < MLone) lone = true; else continue; }
                else if (d > -0.14f && lr[o + 15] < (dense ? (d > 0.2f ? 0.6f : d > 0.05f ? 0.3f : 0.1f) : 0.55f)) continue;
                float full = (lone ? C0 - 0.04f : d > 0 ? MVtop + 0.03f * d / MOut : MathF.Max(MVlo, MVtop + MKd * d)) + (lr[o + 2] - 0.5f) * 0.02f;
                // its way: out of its mass, turned as it likes
                float ex = Bil(sd, Gn, gx + 3, gy) - Bil(sd, Gn, gx - 3, gy), ey = Bil(sd, Gn, gx, gy + 3) - Bil(sd, Gn, gx, gy - 3);
                float way = (ex * ex + ey * ey > 1e-8f && !lone ? MathF.Atan2(ey, ex) : lr[o + 4] * MathF.Tau) + (lr[o + 4] - 0.5f) * MTurn;
                float len = (leafMin + (leafMax - leafMin) * MathF.Pow(lr[o + 5], 1.2f)) * (dense || d < -0.14f ? 1f : 0.75f);
                int points = lobesMin + (int)(lr[o + 6] * (lobesMax - lobesMin + 1) * 0.9999f);
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
                leaves.Add((x, y, full, reach + 1.3f * pitch, k));
            }
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
                        // (the nearest leaf by its own shape: what no leaf covers goes with it)
                        if (gg < gbest[idx]) { gbest[idx] = gg; fbest[idx] = full; bx[idx] = -dx; by[idx] = -dy; }
                    }
                }
            }
        });
        // the mass's own fill: what no leaf covers stands and goes with its nearest leaf; the outline itself where no leaf hangs over it
        long closed = 0;
        object gate = new();
        Parallel.For(0, P, () => 0L, (j, _, acc) =>
        {
            for (int i = 0; i < P; i++)
            {
                float sdp = Bil(sd, Gn, (i + 0.5f) / m / cell - 0.5f, (j + 0.5f) / m / cell - 0.5f);
                int idx = j * P + i;
                bool has = gbest[idx] < float.MaxValue;
                float b = MathF.Max(has ? fbest[idx] : MathF.Max(MVlo, MVtop + MKd * MathF.Min(sdp, 0)), C0 + MKr * sdp);
                if (b < px[idx])
                {
                    px[idx] = b;
                    if (stemX != null) { stemX[idx] = has ? bx[idx] : 0; stemY![idx] = has ? by[idx] : 0; }
                }
                if (px[idx] < 0) px[idx] = 0;
                if (px[idx] < C0) acc++;
            }
            return acc;
        }, acc => { lock (gate) closed += acc; });
        shade = (float)closed / px.Length;
        return px;
    }

    // pieces of one phase (wrapped, 4 ways) under minCells go to the other phase; the count of those kept
    static int DropSmall(bool[] sh, int n, bool phase, int minCells)
    {
        var seen = new bool[n * n]; var stack = new int[n * n]; var comp = new List<int>();
        int kept = 0;
        for (int s = 0; s < n * n; s++)
        {
            if (seen[s] || sh[s] != phase) continue;
            int sp = 0; stack[sp++] = s; seen[s] = true; comp.Clear();
            while (sp > 0)
            {
                int k = stack[--sp]; comp.Add(k);
                int i = k % n, j = k / n;
                for (int q = 0; q < 4; q++)
                {
                    int nk = Wrap(j + (q == 2 ? 1 : q == 3 ? -1 : 0), n) * n + Wrap(i + (q == 0 ? 1 : q == 1 ? -1 : 0), n);
                    if (!seen[nk] && sh[nk] == phase) { seen[nk] = true; stack[sp++] = nk; }
                }
            }
            if (comp.Count < minCells) { foreach (int k in comp) sh[k] = !phase; } else kept++;
        }
        return kept;
    }
    static float[] Lattice2(Random r, int nx, int ny) { var a = new float[nx * ny]; for (int i = 0; i < a.Length; i++) a[i] = (float)r.NextDouble(); return a; }
    // a wrapped value noise on an nx by ny lattice (u, v over the tile, 0..1), quintic steps
    static float Noise2(float[] lat, int nx, int ny, float u, float v)
    {
        float x = u * nx, y = v * ny;
        int x0 = (int)MathF.Floor(x), y0 = (int)MathF.Floor(y);
        float fx = x - x0, fy = y - y0;
        fx = fx * fx * fx * (fx * (fx * 6 - 15) + 10); fy = fy * fy * fy * (fy * (fy * 6 - 15) + 10);
        int xa = Wrap(x0, nx), xb = Wrap(x0 + 1, nx), ya = Wrap(y0, ny), yb = Wrap(y0 + 1, ny);
        float a = lat[ya * nx + xa] + (lat[ya * nx + xb] - lat[ya * nx + xa]) * fx, b = lat[yb * nx + xa] + (lat[yb * nx + xb] - lat[yb * nx + xa]) * fx;
        return a + (b - a) * fy;
    }

    static int Wrap(int i, int n) => ((i % n) + n) % n;
    static float Mod(float a, float n) => ((a % n) + n) % n;
    static float Md(float d, float n) => d - n * MathF.Round(d / n);   // the short way round the tile
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
