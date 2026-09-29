using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Things made in code, as a woodturner, a smith or a tailor would make
/// them: a profile turned on a lathe, a wire or a root swept along a path, a
/// strip of cloth, a hide or a petal cut out and draped, a plate cut out and
/// its edges bevelled; and the painted sheets they wear (woven cloth, fur,
/// parchment, wood). Every triangle faces the way its normals say, so a
/// piece never comes out inside out whichever way its points run.
/// </summary>
public static class Shapes
{
    /// <summary>A mesh built up piece by piece.</summary>
    public sealed class Build
    {
        public readonly List<Vector3> P = new(), N = new();
        public readonly List<Vector2> U = new();
        public readonly List<int> I = new();

        public int V(Vector3 p, Vector3 n, Vector2 uv = default) { P.Add(p); N.Add(n); U.Add(uv); return P.Count - 1; }

        /// <summary>A triangle, turned to face the way its vertices' normals
        /// point (Godot's front faces wind clockwise).</summary>
        public void Tri(int a, int b, int c)
        {
            var face = (P[c] - P[a]).Cross(P[b] - P[a]);
            if (face.Dot(N[a] + N[b] + N[c]) < 0) (b, c) = (c, b);
            I.Add(a); I.Add(b); I.Add(c);
        }

        public void Quad(int a, int b, int c, int d) { Tri(a, b, c); Tri(a, c, d); }

        /// <summary>Moves what was built since (v0, i0) and shades it smooth
        /// again; welded, vertices in the same place (a seam) shade as one.</summary>
        public void Warp(int v0, int i0, Func<Vector3, Vector3> f, bool weld = false)
        {
            for (int k = v0; k < P.Count; k++) { P[k] = f(P[k]); N[k] = Vector3.Zero; }
            for (int k = i0; k < I.Count; k += 3)
            {
                int a = I[k], b = I[k + 1], c = I[k + 2];
                var n = (P[c] - P[a]).Cross(P[b] - P[a]);
                N[a] += n; N[b] += n; N[c] += n;
            }
            if (weld)
            {
                static Vector3I Key(Vector3 p) => new((int)Mathf.Round(p.X * 1e4f), (int)Mathf.Round(p.Y * 1e4f), (int)Mathf.Round(p.Z * 1e4f));
                var sum = new Dictionary<Vector3I, Vector3>();
                for (int k = v0; k < P.Count; k++) sum[Key(P[k])] = sum.GetValueOrDefault(Key(P[k])) + N[k];
                for (int k = v0; k < P.Count; k++) N[k] = sum[Key(P[k])];
            }
            for (int k = v0; k < P.Count; k++) N[k] = N[k].LengthSquared() > 1e-14f ? N[k].Normalized() : Vector3.Up;
        }

        /// <summary>Another build's pieces, moved.</summary>
        public void Append(Build o, Transform3D t)
        {
            int v0 = P.Count;
            for (int k = 0; k < o.P.Count; k++) V(t * o.P[k], (t.Basis * o.N[k]).Normalized(), o.U[k]);
            foreach (var i in o.I) I.Add(v0 + i);
        }

        /// <summary>Flat faces: every triangle its own three vertices.</summary>
        public Build Faceted()
        {
            var f = new Build();
            for (int k = 0; k < I.Count; k += 3)
            {
                Vector3 a = P[I[k]], b = P[I[k + 1]], c = P[I[k + 2]];
                var n = (c - a).Cross(b - a);
                n = n.LengthSquared() > 1e-14f ? n.Normalized() : Vector3.Up;
                int i0 = f.V(a, n, U[I[k]]), i1 = f.V(b, n, U[I[k + 1]]), i2 = f.V(c, n, U[I[k + 2]]);
                f.I.Add(i0); f.I.Add(i1); f.I.Add(i2);
            }
            return f;
        }

        public ArrayMesh Mesh(bool tangents = false)
        {
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Godot.Mesh.ArrayType.Max);
            arr[(int)Godot.Mesh.ArrayType.Vertex] = P.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Normal] = N.ToArray();
            arr[(int)Godot.Mesh.ArrayType.TexUV] = U.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Index] = I.ToArray();
            var m = new ArrayMesh();
            m.AddSurfaceFromArrays(Godot.Mesh.PrimitiveType.Triangles, arr);
            if (!tangents) return m;
            var st = new SurfaceTool();
            st.CreateFrom(m, 0);
            st.GenerateTangents();
            return st.Commit();
        }
    }

    /// <summary>Points as (x, y) pairs.</summary>
    public static Vector2[] Pts(params float[] xy)
    {
        var p = new Vector2[xy.Length / 2];
        for (int i = 0; i < p.Length; i++) p[i] = new Vector2(xy[i * 2], xy[i * 2 + 1]);
        return p;
    }

    /// <summary>A path of n points along f(t), t from 0 to 1 (closed: 1 is
    /// left out, being 0 again).</summary>
    public static List<Vector3> Path(int n, Func<float, Vector3> f, bool closed = false)
    {
        var l = new List<Vector3>(n);
        for (int i = 0; i < n; i++) l.Add(f(closed ? (float)i / n : (float)i / (n - 1)));
        return l;
    }

    /// <summary>A circle of radius r round a centre, in the plane of two axes.</summary>
    public static List<Vector3> Circle(Vector3 at, float r, Vector3 a, Vector3 b, int n = 32) =>
        Path(n, t => at + a * (r * Mathf.Cos(t * Mathf.Tau)) + b * (r * Mathf.Sin(t * Mathf.Tau)), true);

    /* -------------------------------------------------------------- lathe -- */

    /// <summary>A profile of (radius, height) points, bottom to top, turned
    /// round the Y axis. Repeat a point for a sharp edge there. Textured:
    /// the seam keeps its own vertices, so a sheet wraps once round.</summary>
    public static void Lathe(Build b, IReadOnlyList<Vector2> prof, int seg = 32, Transform3D? at = null, Func<Vector3, Vector3>? warp = null, bool textured = false, float turns = 1)
    {
        int n = prof.Count, v0 = b.P.Count, i0 = b.I.Count, cols = textured || turns < 1 ? seg + 1 : seg;
        var t = at ?? Transform3D.Identity;
        var len = new float[n];
        for (int j = 1; j < n; j++) len[j] = len[j - 1] + prof[j].DistanceTo(prof[j - 1]);
        float total = Mathf.Max(len[n - 1], 1e-5f);
        for (int i = 0; i < cols; i++)
        {
            float a = Mathf.Tau * turns * i / seg, c = Mathf.Cos(a), s = Mathf.Sin(a);
            for (int j = 0; j < n; j++)
            {
                var prev = j > 0 && prof[j - 1] != prof[j] ? prof[j - 1] : prof[j];
                var next = j < n - 1 && prof[j + 1] != prof[j] ? prof[j + 1] : prof[j];
                var d = next - prev;
                var n2 = new Vector2(d.Y, -d.X).Normalized();
                var p = new Vector3(prof[j].X * c, prof[j].Y, prof[j].X * s);
                var nn = new Vector3(n2.X * c, n2.Y, n2.X * s);
                b.V(t * p, (t.Basis * nn).Normalized(), new Vector2((float)i / seg * turns, 1 - len[j] / total));
            }
        }
        for (int i = 0; i < seg; i++)
        {
            int i1 = (i + 1) % cols;
            for (int j = 0; j < n - 1; j++)
                b.Quad(v0 + i * n + j, v0 + i1 * n + j, v0 + i1 * n + j + 1, v0 + i * n + j + 1);
        }
        if (warp != null) b.Warp(v0, i0, warp, weld: cols > seg);
    }

    /* --------------------------------------------------------------- tube -- */

    /// <summary>A tube swept along a path, its radius at each point along
    /// it (0 to 1); open ends capped.</summary>
    public static void Tube(Build b, IReadOnlyList<Vector3> path, Func<float, float> radius, int sides = 8, bool closed = false, Transform3D? at = null)
    {
        int n = path.Count;
        var t = at ?? Transform3D.Identity;
        var T = new Vector3[n];
        for (int k = 0; k < n; k++)
        {
            Vector3 a = closed ? path[(k - 1 + n) % n] : path[Math.Max(0, k - 1)], c = closed ? path[(k + 1) % n] : path[Math.Min(n - 1, k + 1)];
            T[k] = (c - a).Normalized();
        }
        var N = T[0].Cross(Mathf.Abs(T[0].Y) < 0.9f ? Vector3.Up : Vector3.Right).Normalized();
        var ringStart = new int[n];
        var rad = new float[n];
        for (int k = 0; k < n; k++)
        {
            if (k > 0) N = (N - T[k] * N.Dot(T[k])).Normalized();
            var B = T[k].Cross(N);
            float u = closed ? (float)k / n : (float)k / (n - 1);
            rad[k] = radius(u);
            ringStart[k] = b.P.Count;
            for (int s = 0; s < sides; s++)
            {
                float a = Mathf.Tau * s / sides;
                var dir = N * Mathf.Cos(a) + B * Mathf.Sin(a);
                b.V(t * (path[k] + dir * rad[k]), (t.Basis * dir).Normalized(), new Vector2((float)s / sides, u));
            }
        }
        int rings = closed ? n : n - 1;
        for (int k = 0; k < rings; k++)
        {
            int r0 = ringStart[k], r1 = ringStart[(k + 1) % n];
            for (int s = 0; s < sides; s++)
            {
                int s1 = (s + 1) % sides;
                b.Quad(r0 + s, r0 + s1, r1 + s1, r1 + s);
            }
        }
        if (closed) return;
        foreach (var (k, dir) in new[] { (0, -T[0]), (n - 1, T[n - 1]) })
        {
            if (rad[k] < 1e-4f) continue;
            var nd = (t.Basis * dir).Normalized();
            int c = b.V(t * path[k], nd, new Vector2(0.5f, 0.5f)), first = b.P.Count;
            for (int s = 0; s < sides; s++) b.V(b.P[ringStart[k] + s], nd);
            for (int s = 0; s < sides; s++) b.Tri(c, first + s, first + (s + 1) % sides);
        }
    }

    public static void Tube(Build b, IReadOnlyList<Vector3> path, float radius, int sides = 8, bool closed = false, Transform3D? at = null) =>
        Tube(b, path, _ => radius, sides, closed, at);

    /* ------------------------------------------------------------- ribbon -- */

    /// <summary>A strip along a path, as wide as asked across it (a bandage's
    /// tail, a strap). Draw it two-sided.</summary>
    public static void Ribbon(Build b, IReadOnlyList<Vector3> path, Vector3 across, Func<float, float> width, Transform3D? at = null)
    {
        int n = path.Count, v0 = b.P.Count;
        var t = at ?? Transform3D.Identity;
        for (int k = 0; k < n; k++)
        {
            var d = (path[Math.Min(n - 1, k + 1)] - path[Math.Max(0, k - 1)]).Normalized();
            var side = (across - d * across.Dot(d)).Normalized();
            var nn = (t.Basis * d.Cross(side)).Normalized();
            float u = (float)k / (n - 1), w = width(u) / 2;
            b.V(t * (path[k] - side * w), nn, new Vector2(0, u));
            b.V(t * (path[k] + side * w), nn, new Vector2(1, u));
        }
        for (int k = 0; k < n - 1; k++) b.Quad(v0 + k * 2, v0 + k * 2 + 1, v0 + k * 2 + 3, v0 + k * 2 + 2);
    }

    /* -------------------------------------------------------------- sheet -- */

    static Vector2[] Resample(Vector2[] ring, float step)
    {
        var l = new List<Vector2>();
        for (int i = 0; i < ring.Length; i++)
        {
            Vector2 a = ring[i], c = ring[(i + 1) % ring.Length];
            int parts = Math.Max(1, (int)Mathf.Ceil(a.DistanceTo(c) / step));
            for (int k = 0; k < parts; k++) l.Add(a.Lerp(c, (float)k / parts));
        }
        return l.ToArray();
    }

    static float SignedArea(Vector2[] ring)
    {
        float a = 0;
        for (int i = 0; i < ring.Length; i++) { var p = ring[i]; var q = ring[(i + 1) % ring.Length]; a += p.X * q.Y - q.X * p.Y; }
        return a / 2;
    }

    /// <summary>A flat cut-out (a hide, a petal, a sheet of paper) filled with
    /// points so it can bend, then draped by warp. Its face looks toward +Z;
    /// a back and edge are built too, thick apart, if asked for.</summary>
    public static void Sheet(Build face, Build? back, Vector2[] outline, float step, float thick, Func<Vector3, Vector3>? warp = null)
    {
        var ring = Resample(outline, step);
        var pts = new List<Vector2>(ring);
        Vector2 lo = ring[0], hi = ring[0];
        foreach (var p in ring) { lo = lo.Min(p); hi = hi.Max(p); }
        int row = 0;
        for (float y = lo.Y + step * 0.5f; y < hi.Y; y += step * 0.87f, row++)
            for (float x = lo.X + step * (row % 2 == 0 ? 0.5f : 1f); x < hi.X; x += step)
            {
                var p = new Vector2(x, y);
                if (!Geometry2D.IsPointInPolygon(p, ring)) continue;
                float near = float.MaxValue;
                for (int i = 0; i < ring.Length; i++) near = Mathf.Min(near, p.DistanceTo(Geometry2D.GetClosestPointToSegment(p, ring[i], ring[(i + 1) % ring.Length])));
                if (near > step * 0.45f) pts.Add(p);
            }
        var tris = Geometry2D.TriangulateDelaunay(pts.ToArray());
        var span = (hi - lo).Max(new Vector2(1e-4f, 1e-4f));
        Vector2 Uv(Vector2 p) => new((p.X - lo.X) / span.X, 1 - (p.Y - lo.Y) / span.Y);
        void Side(Build b, float z, Vector3 n)
        {
            int v0 = b.P.Count, i0 = b.I.Count;
            foreach (var p in pts) b.V(new Vector3(p.X, p.Y, z), n, Uv(p));
            for (int k = 0; k < tris.Length; k += 3)
            {
                var mid = (pts[tris[k]] + pts[tris[k + 1]] + pts[tris[k + 2]]) / 3;
                if (Geometry2D.IsPointInPolygon(mid, ring)) b.Tri(v0 + tris[k], v0 + tris[k + 1], v0 + tris[k + 2]);
            }
            if (warp != null) b.Warp(v0, i0, warp);
        }
        Side(face, thick / 2, Vector3.Back);
        if (back == null) return;
        Side(back, -thick / 2, Vector3.Forward);
        // The edge: a band round the outline between face and back.
        int e0 = back.P.Count, ei = back.I.Count;
        bool ccw = SignedArea(ring) > 0;
        for (int i = 0; i < ring.Length; i++)
        {
            Vector2 a = ring[i], c = ring[(i + 1) % ring.Length], d = c - a;
            var o = (ccw ? new Vector3(d.Y, -d.X, 0) : new Vector3(-d.Y, d.X, 0)).Normalized();
            int q = back.V(new Vector3(a.X, a.Y, thick / 2), o), r = back.V(new Vector3(c.X, c.Y, thick / 2), o);
            int s = back.V(new Vector3(c.X, c.Y, -thick / 2), o), u = back.V(new Vector3(a.X, a.Y, -thick / 2), o);
            back.Quad(q, r, s, u);
        }
        // The edge moves as the face and back do, each strip of it shaded flat.
        if (warp != null) back.Warp(e0, ei, warp);
    }

    /* ------------------------------------------------------------ extrude -- */

    /// <summary>A plate cut to an outline (in XY), deep in Z, its edges
    /// bevelled so they catch the light.</summary>
    public static void Extrude(Build b, Vector2[] outline, float depth, float bevel = 0, Transform3D? at = null)
    {
        var t = at ?? Transform3D.Identity;
        int n = outline.Length;
        bool ccw = SignedArea(outline) > 0;
        // Each corner moved in along its bisector (a miter, held short at sharp corners).
        var inset = new Vector2[n];
        for (int i = 0; i < n; i++)
        {
            Vector2 p = outline[i], a = outline[(i - 1 + n) % n], c = outline[(i + 1) % n];
            Vector2 d0 = (p - a).Normalized(), d1 = (c - p).Normalized();
            Vector2 n0 = ccw ? new(-d0.Y, d0.X) : new(d0.Y, -d0.X), n1 = ccw ? new(-d1.Y, d1.X) : new(d1.Y, -d1.X);
            var m = (n0 + n1).Normalized();
            float k = Mathf.Min(bevel / Mathf.Max(m.Dot(n0), 0.35f), bevel * 2.5f);
            inset[i] = p + m * k;
        }
        var cap = Geometry2D.TriangulatePolygon(inset);
        float zf = depth / 2, zs = depth / 2 - bevel;
        foreach (var (z, nz) in new[] { (zf, 1f), (-zf, -1f) })
        {
            int v0 = b.P.Count;
            var nn = (t.Basis * new Vector3(0, 0, nz)).Normalized();
            foreach (var p in inset) b.V(t * new Vector3(p.X, p.Y, z), nn, p);
            for (int k = 0; k < cap.Length; k += 3) b.Tri(v0 + cap[k], v0 + cap[k + 1], v0 + cap[k + 2]);
        }
        for (int i = 0; i < n; i++)
        {
            int j = (i + 1) % n;
            Vector2 a = outline[i], c = outline[j], d = c - a;
            var o = ccw ? new Vector3(d.Y, -d.X, 0).Normalized() : new Vector3(-d.Y, d.X, 0).Normalized();
            var on = (t.Basis * o).Normalized();
            b.Quad(b.V(t * new Vector3(a.X, a.Y, zs), on), b.V(t * new Vector3(c.X, c.Y, zs), on), b.V(t * new Vector3(c.X, c.Y, -zs), on), b.V(t * new Vector3(a.X, a.Y, -zs), on));
            if (bevel <= 0) continue;
            foreach (float sz in new[] { 1f, -1f })
            {
                var bn = (t.Basis * (o + new Vector3(0, 0, sz)).Normalized()).Normalized();
                b.Quad(b.V(t * new Vector3(a.X, a.Y, zs * sz), bn), b.V(t * new Vector3(c.X, c.Y, zs * sz), bn),
                    b.V(t * new Vector3(inset[j].X, inset[j].Y, zf * sz), bn), b.V(t * new Vector3(inset[i].X, inset[i].Y, zf * sz), bn));
            }
        }
    }

    /* ----------------------------------------------------------- textures -- */

    static readonly FastNoiseLite noise = new() { NoiseType = FastNoiseLite.NoiseTypeEnum.Simplex, Seed = 11, Frequency = 1 };

    /// <summary>Simplex noise from 0 to 1.</summary>
    public static float Noise(float x, float y) => noise.GetNoise2D(x, y) * 0.5f + 0.5f;

    /// <summary>A sheet painted a pixel at a time (u, v from 0 to 1).</summary>
    public static Image Paint(int w, int h, Func<float, float, Color> f)
    {
        var img = Image.CreateEmpty(w, h, false, Image.Format.Rgba8);
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) img.SetPixel(x, y, f((x + 0.5f) / w, (y + 0.5f) / h));
        return img;
    }

    public static ImageTexture Tex(Image img) { img.GenerateMipmaps(); return ImageTexture.CreateFromImage(img); }

    static ImageTexture? weave;

    /// <summary>Plain-woven cloth, grey, to be tinted (repeats).</summary>
    public static ImageTexture Weave() => weave ??= Tex(Paint(64, 64, (u, v) =>
    {
        float x = u * 16, y = v * 16;
        bool over = ((int)x + (int)y) % 2 == 0;
        float across = over ? y - Mathf.Floor(y) : x - Mathf.Floor(x);
        float k = 0.72f + 0.28f * Mathf.Sin(across * Mathf.Pi);
        return new Color(k, k, k);
    }));

    /// <summary>A hide's fur: strands lying along it (v), clumped, darker
    /// down the spine; and the strands' relief, as a normal map.</summary>
    public static (ImageTexture Albedo, ImageTexture Normal) Fur(Color light, Color dark, float coarse)
    {
        const int S = 256;
        var bump = Image.CreateEmpty(S, S, false, Image.Format.Rgba8);
        var img = Paint(S, S, (u, v) =>
        {
            float strand = Noise(u * 70 / coarse, v * 7 / coarse), clump = Noise(u * 7 + 40, v * 5);
            float k = Mathf.Clamp(0.6f * strand + 0.55f * clump - 0.1f, 0, 1);
            float spine = Mathf.Exp(-Mathf.Pow((u - 0.5f) / 0.13f, 2));
            var c = dark.Lerp(light, k).Darkened(0.45f * spine);
            bump.SetPixel(Mathf.Min(S - 1, (int)(u * S)), Mathf.Min(S - 1, (int)(v * S)), new Color(strand, strand, strand));
            return c;
        });
        bump.BumpMapToNormalMap(6);
        return (Tex(img), Tex(bump));
    }

    static float Frac(float x) => x - Mathf.Floor(x);

    /// <summary>Riveted mail, eight rings to a repeat, each row lying over
    /// the one above; and its relief.</summary>
    public static (ImageTexture Albedo, ImageTexture Normal) Mail()
    {
        const int S = 128;
        var bump = Image.CreateEmpty(S, S, false, Image.Format.Rgba8);
        var img = Paint(S, S, (u, v) =>
        {
            float best = 0;
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++)
                {
                    float cy = Mathf.Floor(v * 8) + dy, off = ((int)cy & 1) * 0.5f;
                    float cx = Mathf.Floor(u * 8 - off) + dx + off;
                    float px = u * 8 - (cx + 0.5f), py = v * 8 - (cy + 0.5f);
                    float h = 1 - Mathf.Abs(Mathf.Sqrt(px * px + py * py) - 0.44f) / 0.14f;
                    if (h > 0) best = Mathf.Max(best, h * (1 - 0.25f * (dy + 1)));
                }
            bump.SetPixel(Mathf.Min(S - 1, (int)(u * S)), Mathf.Min(S - 1, (int)(v * S)), new Color(best, best, best));
            float k = best > 0 ? 0.35f + 0.65f * best : 0.06f;
            return new Color(k, k, k);
        });
        bump.BumpMapToNormalMap(5);
        return (Tex(img), Tex(bump));
    }

    /// <summary>Quilted cloth: diamonds stitched down, each puffed up; and its relief.</summary>
    public static (ImageTexture Albedo, ImageTexture Normal) Quilt()
    {
        const int S = 128;
        var bump = Image.CreateEmpty(S, S, false, Image.Format.Rgba8);
        var img = Paint(S, S, (u, v) =>
        {
            float a = Frac((u + v) * 4), b = Frac((u - v) * 4);
            float e = Mathf.Min(Mathf.Min(a, 1 - a), Mathf.Min(b, 1 - b));
            float puff = Mathf.Sqrt(Mathf.Clamp(e / 0.5f, 0, 1));
            bump.SetPixel(Mathf.Min(S - 1, (int)(u * S)), Mathf.Min(S - 1, (int)(v * S)), new Color(puff, puff, puff));
            float x = u * 64, y = v * 64;
            float thread = 0.9f + 0.1f * Mathf.Sin(((((int)x + (int)y) & 1) == 0 ? y - Mathf.Floor(y) : x - Mathf.Floor(x)) * Mathf.Pi);
            float k = e < 0.025f ? 0.35f : (0.7f + 0.3f * puff) * thread;
            return new Color(k, k, k);
        });
        bump.BumpMapToNormalMap(3);
        return (Tex(img), Tex(bump));
    }

    /// <summary>Old paper: mottled, darker toward its edges.</summary>
    public static Image Parchment(Color c, int w = 256, int h = 192) => Paint(w, h, (u, v) =>
    {
        float mottle = Noise(u * 6, v * 6) * 0.6f + Noise(u * 30, v * 30) * 0.4f;
        float edge = Mathf.Min(Mathf.Min(u, 1 - u), Mathf.Min(v, 1 - v));
        return c.Darkened(0.18f * (1 - mottle) + 0.35f * Mathf.Clamp(1 - edge * 12, 0, 1));
    });

    /// <summary>Wood grain running along u, in planks count across v.</summary>
    public static ImageTexture Wood(Color light, Color dark, int planks = 1) => Tex(Paint(256, 256, (u, v) =>
    {
        float w = u * 5 + Noise(u * 2, v * 9) * 1.4f;
        float grain = Mathf.Pow(Mathf.Abs(Mathf.Sin(w * Mathf.Pi * 3)), 0.6f) * 0.5f + Noise(u * 3, v * 80) * 0.5f;
        var c = dark.Lerp(light, grain * 0.8f + 0.1f);
        float gap = planks > 1 ? Mathf.Abs(v * planks - Mathf.Round(v * planks)) : 1;
        return gap < 0.03f ? c.Darkened(0.6f) : c;
    }));

    /// <summary>Ink on a sheet: a line through points (in pixels), solid or dashed.</summary>
    public static void Stroke(Image img, IReadOnlyList<Vector2> pts, float width, Color ink, float dash = 0)
    {
        float run = 0;
        for (int i = 0; i < pts.Count - 1; i++)
        {
            Vector2 a = pts[i], c = pts[i + 1];
            float len = a.DistanceTo(c);
            for (float s = 0; s < len; s += 0.5f, run += 0.5f)
            {
                if (dash > 0 && (int)(run / dash) % 2 == 1) continue;
                var p = a.Lerp(c, s / Mathf.Max(len, 1e-3f));
                int r = (int)Mathf.Ceil(width / 2);
                for (int dy = -r; dy <= r; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int x = (int)p.X + dx, y = (int)p.Y + dy;
                        if (x < 0 || y < 0 || x >= img.GetWidth() || y >= img.GetHeight() || dx * dx + dy * dy > r * r) continue;
                        img.SetPixel(x, y, img.GetPixel(x, y).Lerp(ink, ink.A));
                    }
            }
        }
    }

    /// <summary>A curve through three points (a quadratic Bézier), as points.</summary>
    public static List<Vector2> Curve(Vector2 a, Vector2 c, Vector2 b, int n = 24)
    {
        var l = new List<Vector2>(n);
        for (int i = 0; i < n; i++) { float t = (float)i / (n - 1); l.Add(a * (1 - t) * (1 - t) + c * 2 * t * (1 - t) + b * t * t); }
        return l;
    }
}
