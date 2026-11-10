using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Look;

namespace SurvivorUnchained.View;

/// <summary>(L1 B4) The moon through the canopy (bible rule 9: big leaf shapes in two values, cast, never painted into the
/// ground maps). Godot 4.5's light projectors take omni and spot lights only, so the cookie lives in cel.gdshaderinc's
/// directional path (cel_dapple_at): a world-space leaf tile projected along the key, masked to where the canopy stands.
/// The mask comes from the zone's trees (their kinds' crowns, rigs.json "crowns") and, in an arena whose air has a canopy,
/// from the place's own cover (splat3 A: its clearings open). The leaf tile: leaf clusters (a fan of three to five pointed
/// leaves, 0.8-2.4 m) dropped over a 32 m tile, each with its own rank; a pixel holds the lowest rank over it (1: none), so
/// the shader's cover picks how many clusters close the sky, and each one is drawn whole with a hard edge.</summary>
public static class CanopyCookie
{
    public const float Tile = 32f;
    // (L1 lead 9, B1: 1024 stepped 6-8 px at 1:1 under the arena's 80 m tile; 4096 steps under 2 px)
    const int TilePx = 4096;
    static ImageTexture? leaf;
    /// <summary>A canopy mask stands for this zone (the dapple can show).</summary>
    public static bool Shown { get; private set; }
    /// <summary>The ground's mean height under the mask (the crowns' height is over it).</summary>
    public static float PlaneY { get; private set; }
    /// <summary>(S2b-N3) The rig's cover floor holds here: off in an arena whose air has no canopy (the barrow's open sky, the
    /// ruts, the dig), so the floor never roofs a place the H2 places left open.</summary>
    public static bool Floored { get; private set; } = true;

    // (L1 lead 11) The leaf shapes as knobs (rigs.json dapple "clusters", "leaf", "leaves"; --air-tune dclusters, dleaf, dleaves):
    // the defaults draw the tile as it was (the same random run).
    // (L1 lead 12, F4) Leaf MASSES (rigs.json dapple "mass" [narrowest, widest, m]; --air-tune dmass): a cluster is a lobed mass
    // that wide (a middle lobe and "leaves" more round it, filled) with small pointed leaves ("leaf" long) all round its rim,
    // (a third number in "mass": the masses' random run, 0 the first; another run lays the same masses out elsewhere)
    // tips out: shade reads as serrated masses of foliage, and no single leaf is big enough to read as a leaf on the ground
    // (the fans' 0.8-2.4 m leaves did, and bit her pool in scoops). No mass: the fans, as they were.
    static (int Clusters, float LenMin, float LenMax, int LeavesMin, int LeavesMax, float MassMin, float MassMax, int Run) shape = (420, 0.8f, 2.4f, 3, 5, 0f, 0f, 0), built;
    /// <summary>The cookie's shapes (0 or null: the default); the tile is redrawn, and set again where it is in use, when they change.</summary>
    public static void Shape(int clusters, double[]? leafLen, double[]? leaves, double[]? mass = null)
    {
        bool lenOk = leafLen is { Length: 2 } && leafLen[0] > 0 && leafLen[1] >= leafLen[0];
        bool numOk = leaves is { Length: 2 } && leaves[0] >= 1 && leaves[1] >= leaves[0];
        bool massOk = mass is { Length: 2 or 3 } && mass[0] > 0 && mass[1] >= mass[0];
        var s = (clusters > 0 ? Math.Min(clusters, 4000) : 420, lenOk ? (float)leafLen![0] : 0.8f, lenOk ? (float)Math.Min(leafLen![1], 12) : 2.4f,
            numOk ? (int)leaves![0] : 3, numOk ? (int)Math.Min(leaves![1], 12) : 5,
            massOk ? (float)mass![0] : 0f, massOk ? (float)Math.Min(mass![1], 12) : 0f, massOk && mass!.Length == 3 ? (int)mass[2] : 0);
        if (s == shape) return;
        shape = s;
        GD.Print($"canopy cookie: {s.Item1} clusters, leaves {s.Item4}-{s.Item5} of {s.Item2:0.##}-{s.Item3:0.##} m" + (s.Item6 > 0 ? $", masses {s.Item6:0.##}-{s.Item7:0.##} m, run {s.Item8}" : ""));
        if (leaf == null) return;
        RenderingServer.GlobalShaderParameterSet("cel_cookie", Leaf());
    }

    static Texture2D Leaf()
    {
        if (leaf != null && built == shape) return leaf;
        built = shape;
        var px = new byte[TilePx * TilePx];
        Array.Fill(px, (byte)255);
        var rnd = new Random(20261104);
        float m = TilePx / Tile;
        int clusters = shape.Clusters;
        if (shape.MassMin > 0) Masses(px, shape.Run == 0 ? rnd : new Random(20261104 + shape.Run), m);
        else for (int c = 0; c < clusters; c++)
        {
            byte rank = (byte)(4 + c * 247 / clusters);
            float cx = (float)rnd.NextDouble() * TilePx, cy = (float)rnd.NextDouble() * TilePx;
            float baseA = (float)(rnd.NextDouble() * Math.PI * 2);
            int leaves = shape.LeavesMin + rnd.Next(shape.LeavesMax - shape.LeavesMin + 1);
            for (int l = 0; l < leaves; l++)
            {
                float a = baseA + (l - (leaves - 1) * 0.5f) * (0.55f + (float)rnd.NextDouble() * 0.25f);
                float len = (shape.LenMin + (float)rnd.NextDouble() * (shape.LenMax - shape.LenMin)) * m, wid = len * (0.32f + (float)rnd.NextDouble() * 0.12f);
                float ox = cx + MathF.Cos(a) * len * 0.45f, oy = cy + MathF.Sin(a) * len * 0.45f;
                float ca = MathF.Cos(a), sa = MathF.Sin(a);
                int r = (int)(len * 0.6f) + 2;
                for (int y = -r; y <= r; y++)
                    for (int x = -r; x <= r; x++)
                    {
                        // a pointed leaf (a vesica): along u in -1..1, half-width w(1 - u^2)
                        float u = (x * ca + y * sa) / (len * 0.5f), v = (-x * sa + y * ca) / (wid * 0.5f);
                        if (MathF.Abs(u) > 1 || MathF.Abs(v) > 1 - u * u) continue;
                        int ix = ((int)(ox + x) % TilePx + TilePx) % TilePx, iy = ((int)(oy + y) % TilePx + TilePx) % TilePx;
                        int i = iy * TilePx + ix;
                        if (rank < px[i]) px[i] = rank;
                    }
            }
        }
        var img = Image.CreateFromData(TilePx, TilePx, false, Image.Format.R8, px);
        img.GenerateMipmaps();
        leaf = ImageTexture.CreateFromImage(img);
        return leaf;
    }

    // (L1 lead 12, F4) The tile as leaf masses: see shape.
    // (round 5) Each mass keeps clear of the ones ranked under it (the best of a few throws: those close the sky before it, so
    // at a thin cover the masses stand apart instead of fusing into shapes over 4 m). Its rim: POINTED leaves, tips out
    // ("leaf": how far a tooth stands out, and its foot is about as wide; straight-sided points of about 58 degrees, some with a shorter point
    // at their side, foot to foot along the rim: the target's shade edge reads as maple points, where round 4's fat overlapping leaves read as scallops),
    // and now and then a loose leaf lying just off it.
    static void Masses(byte[] px, Random rnd, float m)
    {
        int clusters = shape.Clusters;
        var placed = new List<(float X, float Y, float R)>();
        for (int c = 0; c < clusters; c++)
        {
            byte rank = (byte)(4 + c * 247 / clusters);
            float rad = (shape.MassMin + (float)rnd.NextDouble() * (shape.MassMax - shape.MassMin)) * 0.5f * m;
            float cx = 0, cy = 0, best = float.NegativeInfinity;
            for (int tr = 0; tr < 24 && best < 0; tr++)
            {
                float x = (float)rnd.NextDouble() * TilePx, y = (float)rnd.NextDouble() * TilePx, clear = float.MaxValue;
                foreach (var (qx, qy, qr) in placed)
                {
                    float dx = MathF.Abs(x - qx), dy = MathF.Abs(y - qy);
                    dx = MathF.Min(dx, TilePx - dx); dy = MathF.Min(dy, TilePx - dy);
                    clear = MathF.Min(clear, MathF.Sqrt(dx * dx + dy * dy) - (rad + qr) * 0.95f);
                }
                if (clear > best) { best = clear; cx = x; cy = y; }
            }
            placed.Add((cx, cy, rad));
            int lobes = 1 + shape.LeavesMin + rnd.Next(shape.LeavesMax - shape.LeavesMin + 1);
            var lx = new float[lobes]; var ly = new float[lobes]; var lr = new float[lobes];
            // (the middle lobe, the others round it and into it: one lump about 2 rad across, never a circle)
            float turn = (float)(rnd.NextDouble() * Math.PI * 2);
            for (int l = 0; l < lobes; l++)
            {
                float a = turn + (l - 1) * (float)(Math.PI * 2) / Math.Max(lobes - 1, 1) + ((float)rnd.NextDouble() - 0.5f) * 0.9f;
                float d = l == 0 ? 0 : rad * (0.38f + 0.3f * (float)rnd.NextDouble());
                lr[l] = rad * (l == 0 ? 0.5f + 0.1f * (float)rnd.NextDouble() : 0.26f + 0.26f * (float)rnd.NextDouble());
                lx[l] = cx + MathF.Cos(a) * d; ly[l] = cy + MathF.Sin(a) * d;
            }
            for (int l = 0; l < lobes; l++)
            {
                int r = (int)lr[l] + 1; float r2 = lr[l] * lr[l];
                for (int y = -r; y <= r; y++)
                {
                    int iy = ((int)(ly[l] + y) % TilePx + TilePx) % TilePx;
                    int w = (int)MathF.Sqrt(MathF.Max(r2 - y * y, 0));
                    for (int x = -w; x <= w; x++)
                    {
                        int i = iy * TilePx + (((int)(lx[l] + x) % TilePx + TilePx) % TilePx);
                        if (rank < px[i]) px[i] = rank;
                    }
                }
                // its rim's teeth, tips out (none where the rim runs inside another lobe)
                float at = (float)(rnd.NextDouble() * Math.PI * 2), end = at + (float)(Math.PI * 2);
                while (at < end)
                {
                    float len = (shape.LenMin + (float)rnd.NextDouble() * (shape.LenMax - shape.LenMin)) * m;
                    float step = len * 1.1f * (0.75f + 0.25f * (float)rnd.NextDouble()) / MathF.Max(lr[l], 1f);
                    float th = at + step * 0.5f; at += step;
                    float a = th + ((float)rnd.NextDouble() - 0.5f) * 0.8f;
                    float side = (float)rnd.NextDouble(), sa = 0.7f + 0.3f * (float)rnd.NextDouble(), sl = 0.55f + 0.15f * (float)rnd.NextDouble();
                    float bx = lx[l] + MathF.Cos(th) * lr[l], by = ly[l] + MathF.Sin(th) * lr[l];
                    bool inside = false;
                    for (int k = 0; k < lobes && !inside; k++)
                        if (k != l) { float ex = bx - lx[k], ey = by - ly[k], rk = MathF.Max(lr[k] - len * 0.2f, 0); inside = ex * ex + ey * ey < rk * rk; }
                    if (inside) continue;
                    Point(px, rank, bx, by, a, len, len * 0.55f);
                    if (side < 0.36f) Point(px, rank, bx, by, a + (side < 0.18f ? sa : -sa), len * sl, len * sl * 0.4f);
                }
            }
            // a loose leaf or two off the mass (three points and a stub)
            for (int n = rnd.Next(3); n > 0; n--)
            {
                float fa = (float)(rnd.NextDouble() * Math.PI * 2), fd = rad * (1.3f + 0.35f * (float)rnd.NextDouble());
                float len = shape.LenMin * (0.8f + 0.5f * (float)rnd.NextDouble()) * m, a = (float)(rnd.NextDouble() * Math.PI * 2);
                float bx = cx + MathF.Cos(fa) * fd, by = cy + MathF.Sin(fa) * fd;
                Point(px, rank, bx, by, a, len, len * 0.36f);
                Point(px, rank, bx, by, a + 0.95f, len * 0.7f, len * 0.26f);
                Point(px, rank, bx, by, a - 0.95f, len * 0.7f, len * 0.26f);
                Point(px, rank, bx, by, a + MathF.PI, len * 0.3f, len * 0.3f);
            }
        }
        // (for the log: what the masses ranked under half close of the tile, and all of them)
        long shade = 0, half = 0;
        foreach (byte b in px) { if (b < 255) shade++; if (b < 128) half++; }
        GD.Print($"canopy cookie: masses close {100.0 * half / px.Length:0.0}% of the tile at cover 0.5, {100.0 * shade / px.Length:0.0}% at 1");
    }

    // One point of a leaf: from (bx, by) along a, len long, hw its half-width at the foot (straight sides to a sharp tip;
    // the foot runs a quarter of its length back into the mass).
    static void Point(byte[] px, byte rank, float bx, float by, float a, float len, float hw)
    {
        float ca = MathF.Cos(a), sa = MathF.Sin(a);
        float mx = bx + ca * len * 0.375f, my = by + sa * len * 0.375f;
        int r = (int)(len * 0.625f + hw) + 2;
        for (int y = -r; y <= r; y++)
            for (int x = -r; x <= r; x++)
            {
                float qx = mx + x - bx, qy = my + y - by;
                float u = (qx * ca + qy * sa) / len, v = MathF.Abs(-qx * sa + qy * ca);
                if (u < -0.25f || u > 1 || v > hw * (u < 0 ? 1 : 1 - u)) continue;
                int i = (((int)(my + y) % TilePx + TilePx) % TilePx) * TilePx + (((int)(mx + x) % TilePx + TilePx) % TilePx);
                if (rank < px[i]) px[i] = rank;
            }
    }

    /// <summary>The canopy for a zone: its mask and the leaf tile into the globals (ZoneView, as the zone is built).</summary>
    public static void For(ZoneData z)
    {
        Shown = false;
        Floored = z.Place is not { } pl0 || pl0.Air.Dapple > 0;
        if (!Atmosphere.CelRigs) return;
        Atmosphere.RigsLoad();
        var set = Rigs.Current;
        var trees = new List<(double X, double Z, string Kind, double Scale)>();
        foreach (var g in z.Flora)
            if (set.Crowns.ContainsKey(g.Kind))
                foreach (var t in g.At) trees.Add((t.Origin.X, t.Origin.Z, g.Kind, t.Basis.Scale.Y));
        foreach (var (id, at) in z.Props)
        {
            string k = id.Contains('/') ? id[(id.LastIndexOf('/') + 1)..] : id;
            foreach (var c in set.Crowns.Keys)
                if (k.StartsWith(c, StringComparison.OrdinalIgnoreCase)) { trees.Add((at.Origin.X, at.Origin.Z, c, at.Basis.Scale.Y)); break; }
        }
        float size = z.Size;
        int res = Math.Clamp((int)(size / 0.5f), 64, 1024);
        var mask = Rigs.CanopyMask(trees, set, size, res);
        // An arena whose air has a canopy (ArenaPlace.Air.Dapple): the place's cover where its clearings are not (splat3 A).
        if (z.Place is { } place && place.Air.Dapple > 0 && z.Splat3 is { } s3)
        {
            int sw = s3.GetWidth(), sh = s3.GetHeight();
            for (int j = 0; j < res; j++)
                for (int i = 0; i < res; i++)
                {
                    float open = s3.GetPixel(Math.Min(sw - 1, i * sw / res), Math.Min(sh - 1, j * sh / res)).A;
                    byte v = (byte)Math.Round(255 * Math.Clamp(place.Air.Dapple, 0, 1) * Mathf.SmoothStep(0.6f, 0.3f, open));
                    if (v > mask[j * res + i]) mask[j * res + i] = v;
                }
        }
        long sum = 0; foreach (var b in mask) sum += b;
        GD.Print($"canopy: {trees.Count} trees, mask {res}px over {size:0} m, cover mean {sum / (255.0 * mask.Length):0.000}");
        if (sum == 0) return;
        var img = Image.CreateFromData(res, res, false, Image.Format.R8, mask);
        RenderingServer.GlobalShaderParameterSet("cel_canopy", ImageTexture.CreateFromImage(img));
        RenderingServer.GlobalShaderParameterSet("cel_cookie", Leaf());
        RenderingServer.GlobalShaderParameterSet("cel_canopy_r", new Vector4(-size / 2, -size / 2, 1 / size, 1 / size));
        PlaneY = z.HeightAt(0, 0);
        Shown = !Args.Has("cel-dapple-off");
    }
}
