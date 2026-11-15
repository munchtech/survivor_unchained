using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A dungeon's walls as mass, built by rule from the walkable field (MapBuild.WallField): a solid wall following the
/// edge on a 0.5 m height grid (smooth outline, lumpy face, never the 1 m cells' steps), a continuous top beyond it, and
/// for the den roots hanging down its face and over its pits' rims. shaders/dungeon_wall.gdshader shades it all.
/// </summary>
public static class DungeonWalls
{
    const float Cell = 0.5f, CapCell = 2f, Lo = -0.6f, Hi = 5f;

    sealed class Buf
    {
        public readonly List<Vector3> V = new(), N = new();
        public readonly List<Color> C = new();
        public readonly List<Vector2> U = new();
        public readonly List<int> I = new();
        // kind: 0 wall, 0.5 top, 1 root (COLOR.r); COLOR.g the metres outside the walkable edge over 8 (the dark beyond
        // goes by it, not by height, so the top and the coarse cap meet black on black); a root's bark coordinates ride
        // UV2.y (metres along it) and COLOR.b (round it); floorY rides UV2.x for the cutaway's footing.
        public int Add(Vector3 v, Vector3 n, float kind, float floorY, float s = 0, float along = 0, float round = 0)
        {
            V.Add(v); N.Add(n); C.Add(new Color(kind, Mathf.Clamp((s + 1) / 8f, 0, 1), round)); U.Add(new Vector2(floorY, along));
            return V.Count - 1;
        }
        // A triangle wound so its front face looks along the vertex normal (Godot draws clockwise as front).
        public void Tri(int a, int b, int c)
        {
            var cr = (V[b] - V[a]).Cross(V[c] - V[a]);
            if (cr.Dot(N[a] + N[b] + N[c]) > 0) (b, c) = (c, b);
            I.Add(a); I.Add(b); I.Add(c);
        }
        public ArrayMesh ToMesh(ArrayMesh m)
        {
            var arrays = new Godot.Collections.Array();
            arrays.Resize((int)Mesh.ArrayType.Max);
            arrays[(int)Mesh.ArrayType.Vertex] = V.ToArray();
            arrays[(int)Mesh.ArrayType.Normal] = N.ToArray();
            arrays[(int)Mesh.ArrayType.Color] = C.ToArray();
            arrays[(int)Mesh.ArrayType.TexUV2] = U.ToArray();
            arrays[(int)Mesh.ArrayType.Index] = I.ToArray();
            m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
            return m;
        }
    }

    // ---------------------------------------------------------------- noise --
    static float Hash01(int x, int y, int z)
    {
        unchecked
        {
            uint h = (uint)(x * 374761393 + y * 668265263 + z * 1274126177);
            h = (h ^ (h >> 13)) * 1274126177u;
            h ^= h >> 16;
            return (h & 0xFFFFFF) / (float)0x1000000;
        }
    }
    static float Sm(float a, float b, float x) { float t = Mathf.Clamp((x - a) / (b - a), 0f, 1f); return t * t * (3 - 2 * t); }
    static float N3(float x, float y, float z)
    {
        int xi = Mathf.FloorToInt(x), yi = Mathf.FloorToInt(y), zi = Mathf.FloorToInt(z);
        float fx = x - xi, fy = y - yi, fz = z - zi;
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy); fz = fz * fz * (3 - 2 * fz);
        float L(int dx, int dy, int dz) => Hash01(xi + dx, yi + dy, zi + dz);
        float a = Mathf.Lerp(Mathf.Lerp(L(0, 0, 0), L(1, 0, 0), fx), Mathf.Lerp(L(0, 1, 0), L(1, 1, 0), fx), fy);
        float b = Mathf.Lerp(Mathf.Lerp(L(0, 0, 1), L(1, 0, 1), fx), Mathf.Lerp(L(0, 1, 1), L(1, 1, 1), fx), fy);
        return Mathf.Lerp(a, b, fz);
    }
    static float N2(float x, float z) => N3(x, 0.5f, z);

    // ------------------------------------------------------------- the zone --
    sealed class Ctx
    {
        public ZoneData Z = null!;
        public float[] Wf = null!, Hf = null!;
        public bool Ravine;
        public float Hb, Half, Step;
        public int Res;

        public float Bil(float[] f, float x, float z)
        {
            float u = Mathf.Clamp((x + Half) / Step, 0, Res - 1.001f), v = Mathf.Clamp((z + Half) / Step, 0, Res - 1.001f);
            int i = (int)u, j = (int)v; float fu = u - i, fv = v - j;
            return Mathf.Lerp(Mathf.Lerp(f[j * Res + i], f[j * Res + i + 1], fu), Mathf.Lerp(f[(j + 1) * Res + i], f[(j + 1) * Res + i + 1], fu), fv);
        }
        public float Floor(float x, float z) => Bil(Z.Heights, x, z);
        // Metres outside the walkable edge; the ravine takes its holes as rock too.
        public float S(float x, float z) => Ravine ? -Mathf.Min(Bil(Wf, x, z), Bil(Hf, x, z)) : -Bil(Wf, x, z);
        // The wall's height by rule of which way it faces the play camera (south of her, looking north): a wall that
        // stands between her and the lens (its outside toward +z) would hide her and the floor, so the den keeps it low
        // and the ravine turns it into a drop, the shelf's edge falling away into shade (as do the ravine's holes);
        // the back and side walls stand full height. Seen only: the walkable ground is the same.
        public float Near(float x, float z) => Sm(0.3f, 0.65f, Grad(null, x, z, true).Y);
        public float HLoc(float x, float z)
        {
            float k = 1 + 0.2f * (2 * N2(x * 0.06f + 7.3f, z * 0.06f - 2.1f) - 1);
            if (!Ravine) return Hb * k * Mathf.Lerp(1f, 0.55f, Near(x, z));
            float drop = Mathf.Max(Near(x, z), Sm(-1.5f, 1.5f, Bil(Wf, x, z) - Bil(Hf, x, z)));
            return Mathf.Lerp(Hb * k, -Drop * k, drop);
        }
        public const float Drop = 14f;
        public float Rise(float s) => Sm(-0.4f, 1.4f, s) * (1 - 0.03f * Sm(1.4f, Hi, s));
        // The wall's surface height at x, z (before the face's lumps): floor, tucked 0.1 under, up to the top.
        public float SurfY(float x, float z) { float s = S(x, z); return Floor(x, z) - 0.1f + (HLoc(x, z) + 0.1f) * Rise(s); }
        public Vector2 Grad(float[]? f, float x, float z, bool sField)
        {
            float e = 0.25f;
            float F(float px, float pz) => sField ? S(px, pz) : Bil(f!, px, pz);
            var g = new Vector2(F(x + e, z) - F(x - e, z), F(x, z + e) - F(x, z - e));
            return g.LengthSquared() < 1e-8f ? new Vector2(0, 1) : g.Normalized();
        }
    }

    public static Node3D? Build(ZoneData z)
    {
        if (z.WallField == null) return null;
        var c = new Ctx { Z = z, Wf = z.WallField, Hf = z.HoleField ?? new float[z.WallField.Length], Ravine = z.DungeonTheme == "ravine", Half = z.Half, Step = z.Step, Res = z.Res };
        if (z.HoleField == null) System.Array.Fill(c.Hf, 8f);
        c.Hb = c.Ravine ? 13f : 4f;
        float size = z.Size;
        int n = (int)(size / Cell) + 1;

        // s at every grid vertex; the band and its dilation get positions.
        var s = new float[n * n];
        var pos = new Vector3[n * n];
        var fly = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float x = -c.Half + i * Cell, zz = -c.Half + j * Cell;
                float sv = c.S(x, zz);
                s[j * n + i] = sv;
                if (sv < Lo - 1.6f || sv > Hi + 1.6f) continue;
                pos[j * n + i] = Place(c, x, zz, sv, out fly[j * n + i]);
            }

        var wall = new Buf();
        var map = new int[n * n];
        System.Array.Fill(map, -1);
        int Vtx(int i, int j)
        {
            int k = j * n + i;
            if (map[k] >= 0) return map[k];
            // Normal by central differences on the displaced grid (as the ground's).
            Vector3 P(int a, int b) => pos[Mathf.Clamp(b, 0, n - 1) * n + Mathf.Clamp(a, 0, n - 1)];
            var nrm = (P(i, j + 1) - P(i, j - 1)).Cross(P(i + 1, j) - P(i - 1, j));
            nrm = nrm.LengthSquared() < 1e-10f ? Vector3.Up : nrm.Normalized();
            return map[k] = wall.Add(pos[k], nrm, 0f, fly[k], s[k]);
        }
        bool In(int i, int j) { float v = s[j * n + i]; return v >= Lo && v <= Hi; }
        for (int j = 0; j < n - 1; j++)
            for (int i = 0; i < n - 1; i++)
            {
                if (!(In(i, j) || In(i + 1, j) || In(i, j + 1) || In(i + 1, j + 1))) continue;
                int a = Vtx(i, j), b = Vtx(i + 1, j), cc = Vtx(i, j + 1), d = Vtx(i + 1, j + 1);
                if (((i + j) & 1) == 1) { wall.Tri(a, b, cc); wall.Tri(b, d, cc); }
                else { wall.Tri(a, d, cc); wall.Tri(a, b, d); }
            }

        // The top beyond: a coarse grid of the same rule, a hair under the fine band's where they overlap, wherever all
        // four corners stand well outside (so no thin hall slips under a cell).
        int nc = (int)(size / CapCell) + 1;
        var sc = new float[nc * nc];
        for (int j = 0; j < nc; j++)
            for (int i = 0; i < nc; i++) sc[j * nc + i] = c.S(-c.Half + i * CapCell, -c.Half + j * CapCell);
        var cmap = new int[nc * nc];
        System.Array.Fill(cmap, -1);
        int CVtx(int i, int j)
        {
            int k = j * nc + i;
            if (cmap[k] >= 0) return cmap[k];
            float x = -c.Half + i * CapCell, zz = -c.Half + j * CapCell, fl = c.Floor(x, zz);
            return cmap[k] = wall.Add(new Vector3(x, fl + 0.97f * c.HLoc(x, zz) - 0.04f, zz), Vector3.Up, 0.5f, fl, sc[k]);
        }
        for (int j = 0; j < nc - 1; j++)
            for (int i = 0; i < nc - 1; i++)
            {
                if (sc[j * nc + i] < 3.5f || sc[j * nc + i + 1] < 3.5f || sc[(j + 1) * nc + i] < 3.5f || sc[(j + 1) * nc + i + 1] < 3.5f) continue;
                int a = CVtx(i, j), b = CVtx(i + 1, j), cc = CVtx(i, j + 1), d = CVtx(i + 1, j + 1);
                wall.Tri(a, b, cc); wall.Tri(b, d, cc);
            }

        var mesh = new ArrayMesh();
        wall.ToMesh(mesh);
        int wallTris = wall.I.Count / 3, rootTris = 0;
        if (!c.Ravine)
        {
            var roots = new Buf();
            Roots(c, roots, s, n);
            if (roots.V.Count > 0) { roots.ToMesh(mesh); rootTris = roots.I.Count / 3; }
        }
        var mat = Material(c);
        for (int k = 0; k < mesh.GetSurfaceCount(); k++) mesh.SurfaceSetMaterial(k, mat);
        GD.Print($"DungeonWalls {z.DungeonTheme}: {wallTris} wall tris, {rootTris} root tris");
        return new MeshInstance3D { Name = "DungeonWalls", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.On };
    }

    // One wall vertex: on the height profile, with the face's lumps (and the ravine's strata) pushed sideways.
    static Vector3 Place(Ctx c, float x, float z, float s, out float floorY)
    {
        floorY = c.Floor(x, z);
        float y = floorY - 0.1f + (c.HLoc(x, z) + 0.1f) * c.Rise(s);
        float w = Sm(-0.1f, 0.4f, s) * (1 - Sm(1.4f, 2.4f, s));
        if (w > 0)
        {
            float dx = 0.35f * w * (2 * N3(x * 0.9f + 3.1f, y * 0.6f, z * 0.9f) - 1);
            float dz = 0.35f * w * (2 * N3(x * 0.9f - 8.7f, y * 0.6f + 5f, z * 0.9f + 1.3f) - 1);
            x += dx; z += dz;
            if (c.Ravine)
            {
                // Strata: bands 1.2-2 m tall stepping in and out a quarter metre.
                var g = c.Grad(null, x, z, true);
                float hh = y - floorY, sp = 1.6f + 0.4f * (2 * N2(x * 0.05f, z * 0.05f) - 1);
                int band = Mathf.FloorToInt(hh / sp + 0.3f * N2(x * 0.2f, z * 0.2f));
                float off = 0.25f * (Hash01(band, 17, 3) * 2 - 1) * Sm(0f, 0.6f, s) * (1 - Sm(1.4f, 2f, s));
                x += g.X * off; z += g.Y * off;
            }
        }
        return new Vector3(x, y, z);
    }

    // ---------------------------------------------------------------- roots --
    // Contour points of v at a level on the grid: line segments across the cells (linear along the edges).
    static List<(Vector2 A, Vector2 B)> Contour(float[] v, int n, float level, float half)
    {
        var segs = new List<(Vector2, Vector2)>();
        var pts = new Vector2[4];
        for (int j = 0; j < n - 1; j++)
            for (int i = 0; i < n - 1; i++)
            {
                float v00 = v[j * n + i], v10 = v[j * n + i + 1], v01 = v[(j + 1) * n + i], v11 = v[(j + 1) * n + i + 1];
                float x0 = -half + i * Cell, z0 = -half + j * Cell;
                int k = 0;
                void Edge(float va, float vb, Vector2 pa, Vector2 pb)
                {
                    if ((va > level) == (vb > level)) return;
                    pts[k++] = pa.Lerp(pb, (level - va) / (vb - va));
                }
                Edge(v00, v10, new Vector2(x0, z0), new Vector2(x0 + Cell, z0));
                Edge(v10, v11, new Vector2(x0 + Cell, z0), new Vector2(x0 + Cell, z0 + Cell));
                Edge(v01, v11, new Vector2(x0, z0 + Cell), new Vector2(x0 + Cell, z0 + Cell));
                Edge(v00, v01, new Vector2(x0, z0), new Vector2(x0, z0 + Cell));
                if (k == 2) segs.Add((pts[0], pts[1]));
                else if (k == 4) { segs.Add((pts[0], pts[1])); segs.Add((pts[2], pts[3])); }
            }
        return segs;
    }

    // The den's roots, a tangle by rule along every edge (never a comb of parallel spokes): runners that lie along the
    // face and come down to the floor at one end, drops that cross the face on a slant and crawl a little way over the
    // floor, and thin rootlets hanging from the top. Each is drawn in (metres along the edge, metres outside it) and
    // laid back onto the wall, so it rides the face wherever the edge bends.
    static void Roots(Ctx c, Buf b, float[] s, int n)
    {
        float lim = c.Half - 8;
        float acc = 0, next = 0.6f;
        foreach (var (a, e) in Contour(s, n, 0.2f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 0.8f + 1.0f * Hash01(hx, hz, 5);
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                WallRoot(c, b, p, hx, hz);
            }
            acc += len - at;
        }
        // The pits' roots: along the rim, dipping over the lip and down into the pit.
        if (c.Hf.Length == 0) return;
        var hn = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) hn[j * n + i] = c.Bil(c.Hf, -c.Half + i * Cell, -c.Half + j * Cell);
        acc = 0; next = 1.0f;
        foreach (var (a, e) in Contour(hn, n, 0f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 1.1f + 0.9f * Hash01(hx, hz, 9);
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                PitRoot(c, b, p, hx, hz);
            }
            acc += len - at;
        }
    }

    // A control point of a root: metres along the edge, metres outside it (the pit's: metres into it), radius share.
    readonly record struct Cp(float U, float S, float R);

    static void WallRoot(Ctx c, Buf b, Vector2 p, int hx, int hz)
    {
        float H(int k) => Hash01(hx, hz, k);
        var g = c.Grad(null, p.X, p.Y, true);
        var t = new Vector2(-g.Y, g.X) * (H(20) < 0.5f ? -1 : 1);
        float kind = H(21);
        var cps = new List<Cp>();
        float r0;
        if (kind < 0.4f)
        {
            // A runner: high on the face, along it, down to the floor and under.
            float L = 3f + 4f * H(22);
            r0 = 0.15f + 0.3f * H(23) * H(23);
            cps.Add(new(0, 1.3f + 0.7f * H(24), 0.55f));
            cps.Add(new(0.3f * L, 0.8f + 0.5f * H(25), 1f));
            cps.Add(new(0.6f * L, 0.35f + 0.35f * H(26), 0.9f));
            cps.Add(new(0.82f * L, -0.25f, 0.7f));
            cps.Add(new(L, -0.8f - 0.9f * H(27), 0.35f));
        }
        else if (kind < 0.78f)
        {
            // A drop: from beyond the top, on a slant across the face, then a crawl over the floor.
            float U = 0.8f + 2.2f * H(22), C = 0.6f + 1.4f * H(28);
            r0 = 0.1f + 0.22f * H(23);
            cps.Add(new(0, 2.2f + 0.8f * H(24), 0.8f));
            cps.Add(new(0.4f * U, 1.1f, 1f));
            cps.Add(new(0.75f * U, 0.35f, 0.9f));
            cps.Add(new(U, -0.45f, 0.75f));
            cps.Add(new(U + C, -0.9f - 1.0f * H(27), 0.3f));
        }
        else
        {
            // Rootlets: two or three thin ones hanging from the top, their tips free on the face.
            int k = 2 + (int)(1.99f * H(29));
            for (int q = 0; q < k; q++)
            {
                var pq = p + t * (0.4f * q);
                float rr = 0.035f + 0.045f * Hash01(hx, hz, 40 + q), dr = 0.3f + 0.9f * Hash01(hx, hz, 50 + q);
                var cl = new List<Cp> { new(0, 1.7f, 1f), new(0.5f * dr, 1.05f, 0.8f), new(dr, 0.3f + 0.4f * Hash01(hx, hz, 60 + q), 0.15f) };
                Lay(c, b, pq, t, cl, rr, hx + 101 * q, hz, false, true);
            }
            return;
        }
        Lay(c, b, p, t, cps, r0, hx, hz, true, true);
        // A thick one sometimes forks: a thinner branch off its first third, down to the floor on the other hand.
        if (kind < 0.78f && r0 > 0.2f && H(30) < 0.5f)
        {
            float u0 = cps[1].U, s0 = cps[1].S;
            var br = new List<Cp> { new(u0, s0, 0.45f), new(u0 - 0.6f, s0 - 0.5f, 0.4f), new(u0 - 1.1f, -0.2f, 0.3f), new(u0 - 1.6f - H(31), -0.7f - 0.6f * H(32), 0.15f) };
            Lay(c, b, p, t, br, r0, hx + 7, hz + 13, true, true);
        }
    }

    static void PitRoot(Ctx c, Buf b, Vector2 p, int hx, int hz)
    {
        float H(int k) => Hash01(hx, hz, k);
        var g = c.Grad(c.Hf, p.X, p.Y, false);
        var t = new Vector2(-g.Y, g.X) * (H(20) < 0.5f ? -1 : 1);
        float L = 2f + 2.5f * H(22), dip = 0.6f + 1.2f * H(24);
        float r0 = 0.1f + 0.22f * H(23) * H(23);
        var cps = new List<Cp> { new(0, -0.9f, 0.4f), new(0.25f * L, -0.1f, 0.9f), new(0.5f * L, dip, 1f), new(0.78f * L, 0.1f, 0.85f), new(L, -0.8f - 0.6f * H(25), 0.3f) };
        Lay(c, b, p, t, cps, r0, hx, hz, true, false);
    }

    // Lays a root's control points onto the wall (or the pit's floor): a smooth curve in (along, outside), every sample
    // put back at its own distance from the edge, riding the surface; the end sinks if it is meant to.
    static void Lay(Ctx c, Buf b, Vector2 p, Vector2 t, List<Cp> cps, float r0, int hx, int hz, bool sink, bool wall)
    {
        float span = 0;
        for (int i = 1; i < cps.Count; i++) span += new Vector2(cps[i].U - cps[i - 1].U, cps[i].S - cps[i - 1].S).Length();
        int per = Mathf.Max(3, Mathf.CeilToInt(span / 0.28f / (cps.Count - 1)));
        var pts = new List<Vector3>(); var rs = new List<float>(); var ss = new List<float>();
        float seed = Hash01(hx, hz, 77) * 40f;
        for (int i = 0; i < cps.Count - 1; i++)
        {
            var p0 = cps[Mathf.Max(i - 1, 0)]; var p1 = cps[i]; var p2 = cps[i + 1]; var p3 = cps[Mathf.Min(i + 2, cps.Count - 1)];
            int last = i == cps.Count - 2 ? per : per - 1;
            for (int k = 0; k <= last; k++)
            {
                float u = k / (float)per;
                float CR(float a0, float a1, float a2, float a3) => 0.5f * (2 * a1 + (-a0 + a2) * u + (2 * a0 - 5 * a1 + 4 * a2 - a3) * u * u + (-a0 + 3 * a1 - 3 * a2 + a3) * u * u * u);
                float U = CR(p0.U, p1.U, p2.U, p3.U), S = CR(p0.S, p1.S, p2.S, p3.S), R = CR(p0.R, p1.R, p2.R, p3.R);
                // A slow sideways wander and knots along the length.
                S += 0.14f * (2 * N3(U * 0.8f + seed, S * 0.5f, seed) - 1);
                float r = Mathf.Max(0.008f, r0 * R * (1 + 0.22f * (2 * N3(U * 1.7f, seed, S * 1.3f) - 1)));
                var h = p + t * U;
                // Back to the wanted distance from the edge, along the field's own slope.
                for (int it = 0; it < 3; it++)
                {
                    var gg = wall ? c.Grad(null, h.X, h.Y, true) : c.Grad(c.Hf, h.X, h.Y, false);
                    float now = wall ? c.S(h.X, h.Y) : -c.Bil(c.Hf, h.X, h.Y);
                    h += (wall ? gg : -gg) * (S - now);
                }
                float y;
                if (wall)
                {
                    // On the face a root stands off it by its radius; over the top and on the floor it lies on them.
                    var gg = c.Grad(null, h.X, h.Y, true);
                    float top = Sm(1.1f, 1.7f, S), face = Sm(-0.3f, 0.2f, S) * (1 - top);
                    y = Mathf.Max(c.SurfY(h.X, h.Y), c.Floor(h.X, h.Y)) + r * (0.3f + 0.4f * top + 0.15f * (1 - face));
                    h -= gg * (r * 1.0f * face);
                }
                else y = c.Floor(h.X, h.Y) + r * 0.45f;
                pts.Add(new Vector3(h.X, y, h.Y)); rs.Add(r); ss.Add(wall ? S : -2f);
            }
        }
        if (sink && pts.Count > 1) pts[^1] = pts[^1] with { Y = c.Floor(pts[^1].X, pts[^1].Z) - rs[^1] * 1.2f };
        Tube(b, pts, rs, ss, c.Floor(p.X, p.Y));
    }

    // A tube round the centre line, its rings carried along without twisting (parallel transport), the bark's
    // coordinates in metres along it and the share round it.
    static void Tube(Buf b, List<Vector3> p, List<float> r, List<float> s, float floorY)
    {
        const int Sides = 7;
        if (p.Count < 2) return;
        var rings = new int[p.Count][];
        Vector3 prevT = (p[1] - p[0]).Normalized();
        var n1 = prevT.Cross(Mathf.Abs(prevT.Y) > 0.9f ? Vector3.Right : Vector3.Up).Normalized();
        float along = 0;
        for (int q = 0; q < p.Count; q++)
        {
            var t = (p[Mathf.Min(q + 1, p.Count - 1)] - p[Mathf.Max(q - 1, 0)]).Normalized();
            if (q > 0) along += p[q].DistanceTo(p[q - 1]);
            n1 = (n1 - t * n1.Dot(t)).Normalized();
            var n2 = t.Cross(n1);
            rings[q] = new int[Sides + 1];
            for (int a = 0; a <= Sides; a++)
            {
                float ang = a * Mathf.Tau / Sides;
                var dir = n1 * Mathf.Cos(ang) + n2 * Mathf.Sin(ang);
                rings[q][a] = b.Add(p[q] + dir * r[q], dir, 1f, floorY, s[q], along, a / (float)Sides);
            }
        }
        for (int q = 0; q + 1 < p.Count; q++)
            for (int a = 0; a < Sides; a++)
            {
                b.Tri(rings[q][a], rings[q][a + 1], rings[q + 1][a]);
                b.Tri(rings[q][a + 1], rings[q + 1][a + 1], rings[q + 1][a]);
            }
    }

    static ShaderMaterial Material(Ctx c)
    {
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_wall.gdshader") };
        string dir = c.Ravine ? "res://art/arena/barrow" : "res://art/arena/hollow";
        mat.SetShaderParameter("sheet", GD.Load<TextureLayered>(ArenaGround.Sheet(dir, "albedo")));
        // hollow: 1 rot, 2 roots; barrow: 6 face (ArenaGround's layer order).
        mat.SetShaderParameter("layer_a", c.Ravine ? 6f : 1f);
        mat.SetShaderParameter("layer_b", c.Ravine ? 6f : 2f);
        mat.SetShaderParameter("ravine", c.Ravine ? 1f : 0f);
        mat.SetShaderParameter("wall_h", c.Hb);
        return mat;
    }
}
