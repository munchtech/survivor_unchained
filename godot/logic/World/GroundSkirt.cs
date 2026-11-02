namespace SurvivorUnchained.World;

/// <summary>
/// The ground's skirt (Env 23): a ring of quads round a zone's heightfield, out `Margin` metres past its edge, so the
/// play camera at the bound never sees past the ground (the Verge's start showed a void and grass over it). Its inner
/// row is the heightfield's own edge vertices (shared, so no seam); its outer row stands at the edge's height straight
/// out (the grass reads the heights clamped, so it stands on the skirt too). Four corner vertices close it. The
/// heightfield's vertices are indexed j * n + i (i along x, j along z), at -half + i * step.
/// </summary>
public static class GroundSkirt
{
    /// <summary>Far enough that the play camera (56 degrees down, 23 m back, at 1920x1080 about 30-40 m past her) at
    /// the bound sees ground to the frame's corners, zoomed out.</summary>
    public const float Margin = 64;

    /// <summary>The skirt's new vertices (x, y, z; 4n + 4 of them, after the field's n * n) and its triangles, indexed
    /// into the field's vertices then these, wound as the field's (clockwise from above in Godot's sense).</summary>
    public static (float[] Xyz, int[] Idx) Build(int n, float half, float step, float[] heights, float margin = Margin)
    {
        int nv = 4 * n + 4;
        var xyz = new float[nv * 3];
        int baseW = n * n, baseE = baseW + n, baseN = baseE + n, baseS = baseN + n, baseC = baseS + n;
        float far = half + margin;
        void Put(int v, float x, float y, float z) { int k = (v - n * n) * 3; xyz[k] = x; xyz[k + 1] = y; xyz[k + 2] = z; }
        for (int t = 0; t < n; t++)
        {
            float c = -half + t * step;
            Put(baseW + t, -far, heights[t * n], c);
            Put(baseE + t, far, heights[t * n + n - 1], c);
            Put(baseN + t, c, heights[t], -far);
            Put(baseS + t, c, heights[(n - 1) * n + t], far);
        }
        Put(baseC + 0, -far, heights[0], -far);                    // NW
        Put(baseC + 1, far, heights[n - 1], -far);                 // NE
        Put(baseC + 2, -far, heights[(n - 1) * n], far);           // SW
        Put(baseC + 3, far, heights[n * n - 1], far);              // SE

        var idx = new int[(4 * (n - 1) + 4) * 6];
        int p = 0;
        // a (min x, min z), b (max x, min z), c (min x, max z), d (max x, max z): as the field's quads.
        void Quad(int a, int b, int c, int d) { idx[p++] = a; idx[p++] = b; idx[p++] = c; idx[p++] = b; idx[p++] = d; idx[p++] = c; }
        for (int t = 0; t < n - 1; t++)
        {
            Quad(baseW + t, t * n, baseW + t + 1, (t + 1) * n);                                   // west
            Quad(t * n + n - 1, baseE + t, (t + 1) * n + n - 1, baseE + t + 1);                   // east
            Quad(baseN + t, baseN + t + 1, t, t + 1);                                            // north
            Quad((n - 1) * n + t, (n - 1) * n + t + 1, baseS + t, baseS + t + 1);                // south
        }
        Quad(baseC + 0, baseN + 0, baseW + 0, 0);                                                // NW
        Quad(baseN + n - 1, baseC + 1, n - 1, baseE + 0);                                        // NE
        Quad(baseW + n - 1, (n - 1) * n, baseC + 2, baseS + 0);                                  // SW
        Quad(n * n - 1, baseE + n - 1, baseS + n - 1, baseC + 3);                                // SE
        return (xyz, idx);
    }

    /// <summary>How deep the flora's mirror reaches past the edge (MirrorOut): whole for the first `FloraFull` metres,
    /// thinning to none at `FloraBand`, so the trees past the edge fade out rather than stop in a line.</summary>
    public const float FloraBand = 30, FloraFull = 8;

    /// <summary>No copy stands nearer the edge line than this (the edge's own plants and their copies would pair up
    /// across it as a planted row: judge, e23v2 vergeedge_02), and each is pushed out up to `Push` more and slid
    /// along the edge up to `Slide` either way, so no copy faces its original.</summary>
    public const float Gap = 3, Push = 3, Slide = 4;

    /// <summary>Only living, soft things are mirrored (trees, bushes, ferns, grasses, flowers): a stone, a dead tree or a
    /// mushroom copied reads as placed (judge, e23v2).</summary>
    public static bool Mirrors(string kind) => kind is "pine" or "broadleaf" or "autumn" or "bush" or "bramble" or "berry"
        or "fern" or "plant" or "clover" or "flowers" or "grass";

    /// <summary>A plant at (x, z) within FloraBand of an edge, mirrored out across it onto the skirt (as the ground's
    /// paint is mirrored there), then pushed out and slid along (Gap, Push, Slide) and turned (Yaw, radians): each
    /// copy, or none. Across both edges near a corner (three copies). A copy is kept by a hash of where it stands,
    /// likelier the nearer the edge, so the band's far side frays.</summary>
    public static System.Collections.Generic.List<(float X, float Z, float Yaw)> MirrorOut(float x, float z, float half)
    {
        var outs = new System.Collections.Generic.List<(float, float, float)>(3);
        bool nx = x < -half + FloraBand, px = x > half - FloraBand, nz = z < -half + FloraBand, pz = z > half - FloraBand;
        float h1 = Hash(x, z), h2 = Hash(x + 17.3f, z - 5.1f), h3 = Hash(x - 3.7f, z + 11.9f);
        // out past the edge by the original's depth inside it, at least Gap, plus up to Push
        float Out(float inside) => System.Math.Max(inside, Gap) + Push * h1;
        float? mx = nx ? -half - Out(x + half) : px ? half + Out(half - x) : null;
        float? mz = nz ? -half - Out(z + half) : pz ? half + Out(half - z) : null;
        float slide = (h2 * 2 - 1) * Slide;
        void Try(float cx, float cz)
        {
            float d = System.Math.Max(System.Math.Abs(cx), System.Math.Abs(cz)) - half;   // how far past the edge
            float t = System.Math.Clamp((d - FloraFull) / (FloraBand - FloraFull), 0, 1);
            float keep = 1 - t * t * (3 - 2 * t);
            if (keep > 0 && Hash(cx, cz) < keep) outs.Add((cx, cz, h3 * 6.2831853f));
        }
        if (mx is float a) Try(a, z + slide);
        if (mz is float b) Try(x + slide, b);
        if (mx is float c && mz is float e) Try(c, e);
        return outs;
    }

    static float Hash(float x, float z)
    {
        uint h = (uint)(int)System.Math.Floor(x * 7.31f) * 73856093u ^ (uint)(int)System.Math.Floor(z * 5.17f) * 19349663u;
        h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
        return (h & 0xFFFFFF) / (float)0x1000000;
    }
}
