using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// What the ground shader and the grass read besides the zone's own paint,
/// made once per zone at load (look bible 1f, "The trick" 4 and 5):
///
/// <para>The paint, reconciled: thin mud strokes (the web game's ruts, a texel
/// or two wide, which read as black slashes) are opened away, and along each
/// road the dirt is repainted as the road's own soft verge.</para>
///
/// <para>A mask over the zone, as the paint is laid: R the road's made
/// surface (its centre strip held back so sparse grass shows), G the wheel
/// ruts (depth, 0-1), B wetness (concave ground from the heights' curvature,
/// the ruts, the gutters at wall bases), A where puddles may stand.</para>
/// </summary>
public sealed class GroundPaint
{
    public readonly Image Splat;
    public readonly Image Mask;

    static readonly ConditionalWeakTable<ZoneData, GroundPaint> Made = new();

    public static GroundPaint Of(ZoneData z) => Made.GetValue(z, k => new GroundPaint(k));

    // Tunable from the command line for sweeps (SurvivorUnchained.Args).
    static readonly float RoadHalf = Args.Num("road-half", 1.55f);      // the made surface, half its width
    static readonly float VergeW = Args.Num("road-verge", 1.5f);        // trodden earth beyond it
    static readonly float RutOff = Args.Num("road-rut-off", 0.75f);     // each rut from the centre
    static readonly float RutW = Args.Num("road-rut-w", 0.2f);          // a rut's half width

    GroundPaint(ZoneData z)
    {
        float size = z.Size, half = z.Half;
        var paths = new List<(Vector2[] P, float Half)>();
        foreach (var (key, pts) in z.Meta.Paths)
        {
            // The roads; their keys and the streams are not.
            if (key.EndsWith("_KEYS") || key.Contains("STREAM") || pts.Length < 2) continue;
            var p = new Vector2[pts.Length];
            for (int i = 0; i < pts.Length; i++) p[i] = new Vector2((float)pts[i][0], (float)pts[i][1]);
            paths.Add((p, key.Contains("RUT") ? RoadHalf * 0.75f : RoadHalf));
        }

        int mr = paths.Count > 0 ? 2048 : 1024;
        float mt = size / mr;
        // Distance to the nearest road's centre line (signed: left negative),
        // the distance along it, and that road's half width.
        var dist = new float[mr * mr];
        var side = new float[mr * mr];
        var along = new float[mr * mr];
        var hwOf = new float[mr * mr];
        Array.Fill(dist, 1e9f);
        float reach = RoadHalf + VergeW + 3f;
        foreach (var (p, hw0) in paths)
        {
            float s0 = 0;
            for (int k = 0; k < p.Length - 1; k++)
            {
                Vector2 a = p[k], b = p[k + 1], ab = b - a;
                float len = ab.Length();
                if (len < 1e-4f) continue;
                Vector2 dir = ab / len;
                int i0 = Math.Max(0, (int)((Math.Min(a.X, b.X) - reach + half) / mt)), i1 = Math.Min(mr - 1, (int)((Math.Max(a.X, b.X) + reach + half) / mt));
                int j0 = Math.Max(0, (int)((Math.Min(a.Y, b.Y) - reach + half) / mt)), j1 = Math.Min(mr - 1, (int)((Math.Max(a.Y, b.Y) + reach + half) / mt));
                for (int j = j0; j <= j1; j++)
                    for (int i = i0; i <= i1; i++)
                    {
                        var w = new Vector2(-half + (i + 0.5f) * mt, -half + (j + 0.5f) * mt);
                        Vector2 ap = w - a;
                        float t = Math.Clamp(ap.Dot(dir), 0, len);
                        Vector2 q = ap - dir * t;
                        float d = q.Length();
                        int at = j * mr + i;
                        if (d >= dist[at]) continue;
                        dist[at] = d;
                        side[at] = dir.X * ap.Y - dir.Y * ap.X;
                        along[at] = s0 + t;
                        hwOf[at] = hw0;
                    }
                s0 += len;
            }
        }

        // Concave ground from the heights (one sample a metre), blurred.
        int n = z.Res;
        float st = z.Step;
        var lap = new float[n * n];
        var h = z.Heights;
        for (int j = 1; j < n - 1; j++)
            for (int i = 1; i < n - 1; i++)
            {
                int c = j * n + i;
                lap[c] = (h[c - 1] + h[c + 1] + h[c - n] + h[c + n] - 4 * h[c]) / (st * st);
            }
        lap = Blur(Blur(lap, n, 2), n, 2);

        // The gutters: wall and building bases.
        var boxes = new List<ColliderDef>();
        foreach (var c in z.Meta.Colliders)
            if (c.Kind == ColliderKind.Box && !c.Soft && Math.Min(c.Hw, c.Hd) >= 0.4) boxes.Add(c);
        var gut = new float[mr * mr];
        foreach (var c in boxes)
        {
            float rr = (float)Math.Sqrt(c.Hw * c.Hw + c.Hd * c.Hd) + 1.4f;
            int i0 = Math.Max(0, (int)(((float)c.X - rr + half) / mt)), i1 = Math.Min(mr - 1, (int)(((float)c.X + rr + half) / mt));
            int j0 = Math.Max(0, (int)(((float)c.Z - rr + half) / mt)), j1 = Math.Min(mr - 1, (int)(((float)c.Z + rr + half) / mt));
            double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    double x = -half + (i + 0.5) * mt - c.X, zz = -half + (j + 0.5) * mt - c.Z;
                    double lx = Math.Abs(x * cos - zz * sin) - c.Hw, lz = Math.Abs(x * sin + zz * cos) - c.Hd;
                    double o = Math.Sqrt(Math.Max(lx, 0) * Math.Max(lx, 0) + Math.Max(lz, 0) * Math.Max(lz, 0));
                    if (lx < 0 && lz < 0) continue;
                    float g = 1f - Mathf.SmoothStep(0.15f, 1.1f, (float)o);
                    int at = j * mr + i;
                    if (g > gut[at]) gut[at] = g;
                }
        }

        var mask = new byte[mr * mr * 4];
        var core = new float[mr * mr];
        var verge = new float[mr * mr];
        for (int j = 0; j < mr; j++)
            for (int i = 0; i < mr; i++)
            {
                int at = j * mr + i;
                float wx = -half + (i + 0.5f) * mt, wz = -half + (j + 0.5f) * mt;
                float r = 0, rut = 0, wet, pud;
                if (dist[at] < 1e8f)
                {
                    float s = along[at], hw = hwOf[at];
                    // The width wanders, as a road worn by use does.
                    hw *= 1f + 0.16f * Mathf.Sin(s * 0.093f + 1.3f) + 0.08f * Mathf.Sin(s * 0.41f);
                    float d = dist[at];
                    float c = 1f - Mathf.SmoothStep(hw - 0.35f, hw + 0.45f, d);
                    float v = 1f - Mathf.SmoothStep(hw, hw + VergeW, d);
                    // The ruts wander a little off the centre line, the left and right together.
                    float off = side[at] - 0.18f * Mathf.Sin(s * 0.057f + 0.4f);
                    float ro = RutOff * (hw / RoadHalf > 0.9f ? 1f : 0.8f);
                    float e = (Mathf.Abs(off) - ro) / RutW;
                    rut = Mathf.Exp(-e * e) * c * (0.75f + 0.25f * Mathf.Sin(s * 0.23f + side[at]));
                    float centre = Mathf.Exp(-(off / 0.38f) * (off / 0.38f));
                    r = c * (1f - 0.5f * centre);
                    core[at] = c;
                    verge[at] = v;
                }
                float cv = Sample(lap, n, st, half, wx, wz);
                // (The blurred Laplacian: the zones' 80th percentile is about 0.045, the 95th about 0.1.)
                float hollow = Mathf.SmoothStep(0.06f, 0.15f, cv), deep = Mathf.SmoothStep(0.11f, 0.24f, cv);
                wet = Mathf.Max(Mathf.Max(hollow * 0.8f, rut * 0.8f), Mathf.Max(gut[at] * 0.75f, core[at] * 0.12f));
                pud = Mathf.Max(rut * (0.62f + 0.2f * hollow), Mathf.Max(deep * 0.8f, gut[at] * 0.4f));
                mask[at * 4] = (byte)(Mathf.Clamp(r, 0, 1) * 255);
                mask[at * 4 + 1] = (byte)(Mathf.Clamp(rut, 0, 1) * 255);
                mask[at * 4 + 2] = (byte)(Mathf.Clamp(wet, 0, 1) * 255);
                mask[at * 4 + 3] = (byte)(Mathf.Clamp(pud, 0, 1) * 255);
            }
        Mask = Image.CreateFromData(mr, mr, false, Image.Format.Rgba8, mask);
        Mask.GenerateMipmaps();

        // The paint: mud opened (strokes under ~1.2 m wide go), the road's
        // band repainted as its verge, dirt and mud at the wall bases.
        var sp = (Image)z.Splat.Duplicate();
        sp.Convert(Image.Format.Rgba8);
        int sr = sp.GetWidth();
        var px = sp.GetData();
        var mud = new float[sr * sr];
        for (int k = 0; k < mud.Length; k++) mud[k] = px[k * 4 + 3] / 255f;
        mud = Dilate(Erode(mud, sr, 2), sr, 2);
        // The old paint's road band, softened (about 1 m), so it meets the verge and the camps beside it without an edge.
        var dirt = new float[sr * sr];
        for (int k = 0; k < dirt.Length; k++) dirt[k] = px[k * 4] / 255f;
        var soft = Blur(Blur(dirt, sr, 3), sr, 3);
        float smt = size / sr;
        for (int j = 0; j < sr; j++)
            for (int i = 0; i < sr; i++)
            {
                int k = j * sr + i;
                float wx = -half + (i + 0.5f) * smt, wz = -half + (j + 0.5f) * smt;
                int mi = Math.Clamp((int)((wx + half) / mt), 0, mr - 1), mj = Math.Clamp((int)((wz + half) / mt), 0, mr - 1);
                int at = mj * mr + mi;
                float rr = px[k * 4] / 255f, a = Math.Min(px[k * 4 + 3] / 255f, mud[k]);
                if (dist[at] < 1e8f)
                {
                    float hw = hwOf[at];
                    float infl = 1f - Mathf.SmoothStep(hw + VergeW * 0.8f, hw + VergeW + 1.6f, dist[at]);
                    rr = Mathf.Lerp(rr, Mathf.Max(verge[at], soft[k] * 0.85f), infl);
                }
                float g = gut[at];
                rr = Mathf.Max(rr, g * 0.7f);
                a = Mathf.Max(a, g * g * 0.45f);
                px[k * 4] = (byte)(Mathf.Clamp(rr, 0, 1) * 255);
                px[k * 4 + 3] = (byte)(Mathf.Clamp(a, 0, 1) * 255);
            }
        Splat = Image.CreateFromData(sr, sr, false, Image.Format.Rgba8, px);
        // --ground-dump DIR: both as PNGs, to check them by eye.
        if (Args.Get("ground-dump") is { } dumpDir)
        {
            Mask.SavePng($"{dumpDir}/{z.Id}_mask.png");
            Splat.SavePng($"{dumpDir}/{z.Id}_splat.png");
        }
    }

    static float Sample(float[] g, int n, float st, float half, float x, float z)
    {
        float fx = Math.Clamp((x + half) / st, 0, n - 1.001f), fz = Math.Clamp((z + half) / st, 0, n - 1.001f);
        int i = (int)fx, j = (int)fz;
        float tx = fx - i, tz = fz - j;
        float a = g[j * n + i] + (g[j * n + i + 1] - g[j * n + i]) * tx;
        float b = g[(j + 1) * n + i] + (g[(j + 1) * n + i + 1] - g[(j + 1) * n + i]) * tx;
        return a + (b - a) * tz;
    }

    static float[] Blur(float[] a, int n, int r)
    {
        var t = new float[a.Length];
        var o = new float[a.Length];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float s = 0; int c = 0;
                for (int k = Math.Max(0, i - r); k <= Math.Min(n - 1, i + r); k++) { s += a[j * n + k]; c++; }
                t[j * n + i] = s / c;
            }
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float s = 0; int c = 0;
                for (int k = Math.Max(0, j - r); k <= Math.Min(n - 1, j + r); k++) { s += t[k * n + i]; c++; }
                o[j * n + i] = s / c;
            }
        return o;
    }

    static float[] Erode(float[] a, int n, int r) => MinMax(a, n, r, true);
    static float[] Dilate(float[] a, int n, int r) => MinMax(a, n, r, false);

    static float[] MinMax(float[] a, int n, int r, bool min)
    {
        var t = new float[a.Length];
        var o = new float[a.Length];
        for (int pass = 0; pass < 2; pass++)
        {
            var src = pass == 0 ? a : t;
            var dst = pass == 0 ? t : o;
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    float v = min ? 1e9f : -1e9f;
                    for (int k = -r; k <= r; k++)
                    {
                        int x = pass == 0 ? Math.Clamp(i + k, 0, n - 1) : i, y = pass == 0 ? j : Math.Clamp(j + k, 0, n - 1);
                        float s = src[y * n + x];
                        v = min ? Math.Min(v, s) : Math.Max(v, s);
                    }
                    dst[j * n + i] = v;
                }
        }
        return o;
    }
}
