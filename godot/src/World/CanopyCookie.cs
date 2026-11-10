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
    static (int Clusters, float LenMin, float LenMax, int LeavesMin, int LeavesMax) shape = (420, 0.8f, 2.4f, 3, 5), built;
    /// <summary>The cookie's shapes (0 or null: the default); the tile is redrawn, and set again where it is in use, when they change.</summary>
    public static void Shape(int clusters, double[]? leafLen, double[]? leaves)
    {
        bool lenOk = leafLen is { Length: 2 } && leafLen[0] > 0 && leafLen[1] >= leafLen[0];
        bool numOk = leaves is { Length: 2 } && leaves[0] >= 1 && leaves[1] >= leaves[0];
        var s = (clusters > 0 ? Math.Min(clusters, 4000) : 420, lenOk ? (float)leafLen![0] : 0.8f, lenOk ? (float)Math.Min(leafLen![1], 12) : 2.4f,
            numOk ? (int)leaves![0] : 3, numOk ? (int)Math.Min(leaves![1], 12) : 5);
        if (s == shape) return;
        shape = s;
        GD.Print($"canopy cookie: {s.Item1} clusters, leaves {s.Item4}-{s.Item5} of {s.Item2:0.##}-{s.Item3:0.##} m");
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
        for (int c = 0; c < clusters; c++)
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
