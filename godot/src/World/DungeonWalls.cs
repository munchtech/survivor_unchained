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
        // kind: 0 wall, 0.5 top, 1 root (COLOR.r); floorY rides UV2.x for the cutaway's footing.
        public int Add(Vector3 v, Vector3 n, float kind, float floorY) { V.Add(v); N.Add(n); C.Add(new Color(kind, 0, 0)); U.Add(new Vector2(floorY, 0)); return V.Count - 1; }
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
        public float HLoc(float x, float z) => Hb * (1 + 0.2f * (2 * N2(x * 0.06f + 7.3f, z * 0.06f - 2.1f) - 1));
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
            return map[k] = wall.Add(pos[k], nrm, 0f, fly[k]);
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
            return cmap[k] = wall.Add(new Vector3(x, fl + 0.97f * c.HLoc(x, zz) - 0.04f, zz), Vector3.Up, 0.5f, fl);
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

    static void Roots(Ctx c, Buf b, float[] s, int n)
    {
        float lim = c.Half - 8;
        // The wall's roots: from the top over the face to the floor.
        float acc = 0, next = 1.4f;
        foreach (var (a, e) in Contour(s, n, 0.2f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 1.1f + 0.7f * Hash01(hx, hz, 5);
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                WallRoot(c, b, p, hx, hz);
            }
            acc += len - at;
        }
        // The pits' roots: from the rim down into the pit.
        if (c.Hf.Length == 0) return;
        var hn = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) hn[j * n + i] = c.Bil(c.Hf, -c.Half + i * Cell, -c.Half + j * Cell);
        acc = 0; next = 1.4f;
        foreach (var (a, e) in Contour(hn, n, 0f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 1.4f + 0.8f * Hash01(hx, hz, 9);
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                var g = c.Grad(c.Hf, p.X, p.Y, false);
                float r0 = 0.12f + 0.25f * Hash01(hx, hz, 11);
                var A = p + g * 0.6f; var B = p - g * 0.8f;
                var pathP = new List<Vector3>(); var pathR = new List<float>();
                Path(c, A, B, g, r0, r0 * 0.5f, 10, 0.35f * Hash01(hx, hz, 12), Hash01(hx, hz, 13) * 6.28f, false, pathP, pathR);
                Tube(b, pathP, pathR, c.Floor(A.X, A.Y));
            }
            acc += len - at;
        }
    }

    static void WallRoot(Ctx c, Buf b, Vector2 p, int hx, int hz)
    {
        var g = c.Grad(null, p.X, p.Y, true);
        float sTop = 1.6f + 1.4f * Hash01(hx, hz, 21), sFoot = -0.2f - 0.7f * Hash01(hx, hz, 22);
        var A = p + g * (sTop - 0.2f); var B = p + g * (sFoot - 0.2f);
        float r0 = 0.12f + 0.3f * Hash01(hx, hz, 23);
        int k = 10 + (int)(4.99f * Hash01(hx, hz, 24));
        var pts = new List<Vector3>(); var rs = new List<float>();
        float ph = Hash01(hx, hz, 25) * 6.28f, wig = 0.6f * Hash01(hx, hz, 26);
        Path(c, A, B, g, r0, r0 * 0.4f, k, wig, ph, true, pts, rs);
        float fl = c.Floor(B.X, B.Y);
        Tube(b, pts, rs, fl);
        if (Hash01(hx, hz, 27) < 0.34f)
        {
            // One branch peels off along the face and goes to the floor to the side.
            int k0 = (int)(k * (0.3f + 0.2f * Hash01(hx, hz, 28)));
            var perp = new Vector2(-g.Y, g.X) * (Hash01(hx, hz, 29) < 0.5f ? -1 : 1);
            var A2 = new Vector2(pts[k0].X, pts[k0].Z);
            var B2 = B + perp * (1.2f + 1.2f * Hash01(hx, hz, 30));
            var p2 = new List<Vector3>(); var r2 = new List<float>();
            Path(c, A2, B2, g, rs[k0] * 0.6f, rs[k0] * 0.25f, 8, 0.25f, ph + 2f, true, p2, r2);
            Tube(b, p2, r2, c.Floor(B2.X, B2.Y));
        }
    }

    // A root's centre line from A to B across the wall's surface (or the pit's), wiggling sideways, standing off the
    // face in the middle (a sag between its holds); the last point sinks into the ground.
    static void Path(Ctx c, Vector2 A, Vector2 B, Vector2 g, float r0, float r1, int k, float wig, float phase, bool wall, List<Vector3> pts, List<float> rs)
    {
        var perp = new Vector2(-g.Y, g.X);
        for (int q = 0; q <= k; q++)
        {
            float t = (float)q / k, arc = Mathf.Sin(Mathf.Pi * t);
            var h = A.Lerp(B, t) + perp * (wig * arc * Mathf.Sin(t * 4.7f + phase));
            float r = Mathf.Lerp(r0, r1, t);
            float y;
            if (wall)
            {
                y = c.SurfY(h.X, h.Y) + r * 0.7f + 0.1f + (q == 0 ? 0.1f : 0);
                h -= g * (0.2f * arc);
                if (q == k) y = c.Floor(h.X, h.Y) - r * 0.4f;
            }
            else
            {
                y = c.Floor(h.X, h.Y) + r * 0.7f + 0.3f * arc;
                if (q == k) y = c.Floor(h.X, h.Y) - r * 0.4f;
            }
            pts.Add(new Vector3(h.X, y, h.Y)); rs.Add(r);
        }
    }

    static void Tube(Buf b, List<Vector3> p, List<float> r, float floorY)
    {
        const int Sides = 6;
        var rings = new int[p.Count][];
        for (int q = 0; q < p.Count; q++)
        {
            var t = (p[Mathf.Min(q + 1, p.Count - 1)] - p[Mathf.Max(q - 1, 0)]).Normalized();
            var refv = Mathf.Abs(t.Y) > 0.9f ? Vector3.Right : Vector3.Up;
            var n1 = t.Cross(refv).Normalized(); var n2 = t.Cross(n1);
            rings[q] = new int[Sides];
            for (int a = 0; a < Sides; a++)
            {
                float ang = a * Mathf.Tau / Sides;
                var dir = n1 * Mathf.Cos(ang) + n2 * Mathf.Sin(ang);
                rings[q][a] = b.Add(p[q] + dir * r[q], dir, 1f, floorY);
            }
        }
        for (int q = 0; q + 1 < p.Count; q++)
            for (int a = 0; a < Sides; a++)
            {
                int a2 = (a + 1) % Sides;
                b.Tri(rings[q][a], rings[q][a2], rings[q + 1][a]);
                b.Tri(rings[q][a2], rings[q + 1][a2], rings[q + 1][a]);
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
