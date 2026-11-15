using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A dungeon's walls as mass, built by rule from the walkable field (MapBuild.WallField): a solid wall following the
/// edge on a 0.5 m height grid (smooth outline, lumpy face, never the 1 m cells' steps), a continuous top beyond it, and
/// for the den roots hanging down its face and over its pits' rims. shaders/dungeon_wall.gdshader shades it all.
/// </summary>
public static partial class DungeonWalls
{
    static bool UseRoots = false;
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
        public int Add(Vector3 v, Vector3 n, float kind, float floorY, float s = 0, float along = 0, float round = 0, float id = 1)
        {
            V.Add(v); N.Add(n); C.Add(new Color(kind, Mathf.Clamp((s + 1) / 8f, 0, 1), round, id)); U.Add(new Vector2(floorY, along));
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

    /// <summary>The den's distance in from a WALL only: where the nearest edge is a pit's (WallField within a few
    /// tenths of HoleField) the wall is far as far as the floor and the banks care (8 m).
    /// (The room's edge round a pit wanders by the room's noise, 1.5 m either way, so near a pit WallField = HoleField
    /// - 1.5 n: up to 1.5 under it (1.50 at worst over seeds 1-40). The old 0.6-0.15 band let a quarter of every pit's
    /// ring through as wall: bank lumps inside the pit, the floor discarded, the wall-foot dark ring. A genuine wall's
    /// foot stands 2.15 m or more from any pit, so 1.95-1.6 parts them; pit solver, 15 Nov.)</summary>
    public static float WallOnly(float wf, float hf) => Mathf.Lerp(wf, 8f, Sm(1.95f, 1.6f, hf - wf));

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
        // (The den's pits are holes, never walls: its room shapes leave a pit outside them, so WallField alone raised
        // a bank over every pit, the "raised black tub" of rounds 1-3; lead 6, 15 Nov.)
        public float S(float x, float z) => Ravine ? -Mathf.Min(Bil(Wf, x, z), Bil(Hf, x, z)) : -WallOnly(Bil(Wf, x, z), Bil(Hf, x, z));
        // The wall's height by rule of which way it faces the play camera (south of her, looking north): a wall that
        // stands between her and the lens (its outside toward +z) would hide her and the floor, so the den keeps it low
        // and the ravine turns it into a drop, the shelf's edge falling away into shade (as do the ravine's holes);
        // the back and side walls stand full height. Seen only: the walkable ground is the same.
        public float Near(float x, float z) => Sm(0.3f, 0.65f, Grad(null, x, z, true).Y);
        public float HLoc(float x, float z)
        {
            float k = 1 + 0.2f * (2 * N2(x * 0.06f + 7.3f, z * 0.06f - 2.1f) - 1);
            if (!Ravine) return Hb * k * Mathf.Lerp(1f, 0.55f, Near(x, z));
            // The ravine is a shelf on the canyon's side: only the back (north) rises, as the cliff; the near and side
            // edges fall away (a side wall standing 13 m between two halls hid the next hall and half the frame).
            // And the cliff rises only where nothing walkable lies behind it (a room's back wall seen from the hall
            // north of it stood 13 m over that hall): probed 18 m on north, the rock must keep going.
            var g = Grad(null, x, z, true);
            float open = Sm(10f, 16f, S(x, z - 18f) - S(x, z));
            float drop = Mathf.Max(Mathf.Max(Near(x, z), Sm(0.45f, 0.8f, Mathf.Abs(g.X))), Sm(-1.5f, 1.5f, Bil(Wf, x, z) - Bil(Hf, x, z)));
            drop = Mathf.Max(drop, 1 - open);
            return Mathf.Lerp(Hb * k, -Drop * k, drop);
        }
        public const float Drop = 14f;
        public float Rise(float s) => Sm(-0.4f, 1.4f, s) * (1 - 0.03f * Sm(1.4f, Hi, s));
        // The wall's surface height at x, z (before the face's lumps): floor, tucked 0.1 under, up to the top.
        public float SurfY(float x, float z) { float s = S(x, z); return Ravine ? Floor(x, z) - 0.1f + (HLoc(x, z) + 0.1f) * Rise(s) : BankY(x, z, s, false); }
        // The den's bank (15 Nov): ground rising unevenly from the floor to a rounded crest sc metres out, then falling away to
        // floor - 3 by sc + 2.5. Crest distance and height are slow noise (near walls lower, the camera sees their top).
        public float BankSc(float x, float z) => 1.5f + 1.5f * Mathf.Clamp(0.7f * N2(x * 0.12f + 11.3f, z * 0.12f - 4.7f) + 0.3f * N2(x * 0.5f - 2.2f, z * 0.5f + 6.9f), 0f, 1f);
        public float BankHc(float x, float z)
        {
            float t = N2(x * 0.05f + 3.3f, z * 0.05f + 9.1f);
            return Mathf.Lerp(Mathf.Lerp(1.6f, 2.8f, t), Mathf.Lerp(0.9f, 1.5f, t), Near(x, z));
        }
        // (round 8, 15 Nov) The back (far) banks no longer fall away past their crest: they climb on as the cave's wall face,
        // BackRise metres more over BackRun, so the top of the play frame reads as a wall (den_room.png's top row) and never
        // as void; the near and side banks still fall to floor - 3 (the camera sees their top).
        public static readonly float BackRise = Args.Num("den-back-rise", 4.5f), BackRun = Args.Num("den-back-run", 4f);
        public float Back(float x, float z) => Mathf.Clamp(1f - 1.6f * Near(x, z), 0f, 1f);
        public float BankTop(float x, float z) => BankSc(x, z) + BackRun * Back(x, z);
        public float BankY(float x, float z, float s, bool lumps = true)
        {
            float sc = BankSc(x, z), hc = BankHc(x, z), fl = Floor(x, z), bk = Back(x, z);
            float fall = fl - 0.1f + hc * Sm(-0.3f, sc, s) - (hc + 2.9f) * Sm(sc, sc + 2.5f, s);
            float climb = fl - 0.1f + hc * Sm(-0.3f, sc, s) + BackRise * Sm(sc - 0.5f, sc + BackRun, s);
            float y = Mathf.Lerp(fall, climb, bk);
            if (lumps) y += 0.25f * (2 * N3(x * 1.0f + 5.7f, 0.3f, z * 1.0f - 1.9f) - 1) * Mathf.Sin(Mathf.Pi * Mathf.Clamp(s / sc, 0f, 1f));
            return y;
        }
        public Vector2 Grad(float[]? f, float x, float z, bool sField)
        {
            float e = 0.25f;
            float F(float px, float pz) => sField ? S(px, pz) : Bil(f!, px, pz);
            var g = new Vector2(F(x + e, z) - F(x - e, z), F(x, z + e) - F(x, z - e));
            return g.LengthSquared() < 1e-8f ? new Vector2(0, 1) : g.Normalized();
        }
    }

    static Ctx? bankCtx;
    /// <summary>The den's bank surface height at x, z (the mesh profile's SurfY, without the face's lumps); the Ctx is built once per zone.</summary>
    public static float BankY(ZoneData z, float x, float zz)
    {
        if (bankCtx == null || bankCtx.Z != z)
        {
            bankCtx = new Ctx { Z = z, Wf = z.WallField!, Hf = z.HoleField ?? new float[z.WallField!.Length], Ravine = z.DungeonTheme == "ravine", Half = z.Half, Step = z.Step, Res = z.Res };
            if (z.HoleField == null) System.Array.Fill(bankCtx.Hf, 8f);
            bankCtx.Hb = bankCtx.Ravine ? 13f : 4f;
        }
        return bankCtx.SurfY(x, zz);
    }

    public static Node3D? Build(ZoneData z)
    {
        if (z.WallField == null) return null;
        var c = new Ctx { Z = z, Wf = z.WallField, Hf = z.HoleField ?? new float[z.WallField.Length], Ravine = z.DungeonTheme == "ravine", Half = z.Half, Step = z.Step, Res = z.Res };
        if (z.HoleField == null) System.Array.Fill(c.Hf, 8f);
        c.Hb = c.Ravine ? 13f : 4f;
        float size = z.Size;
        int n = (int)(size / Cell) + 1;

        float hi = c.Ravine ? Hi : 6.5f + Ctx.BackRun;   // the den's bank band runs to its fall-off (sc + 3 at most 6), and on up the back banks' climb (round 8)
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
                if (sv < Lo - 1.6f || sv > hi + 1.6f) continue;
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
            float bt = 0f;
            if (!c.Ravine) { float sx = c.BankTop(pos[k].X, pos[k].Z); bt = Sm(sx - 0.2f, sx + 1f, s[k]); }
            return map[k] = wall.Add(pos[k], nrm, 0f, fly[k], s[k], bt);
        }
        bool In(int i, int j) { float v = s[j * n + i]; return v >= Lo && v <= hi; }
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
            return cmap[k] = wall.Add(new Vector3(x, c.Ravine ? fl + 0.97f * c.HLoc(x, zz) - 0.04f : c.BankY(x, zz, sc[k], false) - 0.06f, zz), Vector3.Up, 0.5f, fl, sc[k], c.Ravine ? 0f : 1f);
        }
        for (int j = 0; j < nc - 1; j++)
            for (int i = 0; i < nc - 1; i++)
            {
                float capS = c.Ravine ? 3.5f : hi - 0.6f;
                if (sc[j * nc + i] < capS || sc[j * nc + i + 1] < capS || sc[(j + 1) * nc + i] < capS || sc[(j + 1) * nc + i + 1] < capS) continue;
                int a = CVtx(i, j), b = CVtx(i + 1, j), cc = CVtx(i, j + 1), d = CVtx(i + 1, j + 1);
                wall.Tri(a, b, cc); wall.Tri(b, d, cc);
            }

        var mesh = new ArrayMesh();
        wall.ToMesh(mesh);
        int wallTris = wall.I.Count / 3, rootTris = 0;
        if (!c.Ravine && UseRoots)   // den roots: replaced by painted banks, 15 Nov (Roots() kept, unused)
        {
            var roots = new Buf();
            Roots(c, roots, s, n);
            if (roots.V.Count > 0) { roots.ToMesh(mesh); rootTris = roots.I.Count / 3; }
        }
        var mat = Material(c);
        for (int k = 0; k < mesh.GetSurfaceCount(); k++) mesh.SurfaceSetMaterial(k, mat);
        GD.Print($"DungeonWalls {z.DungeonTheme}: {wallTris} wall tris, {rootTris} root tris");
        var walls = new MeshInstance3D { Name = "DungeonWalls", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.On };
        if (!c.Ravine && BigRoots) BankRoots(c, s, n, walls, mat);   // (den round 9: the banks' big roots, DungeonWalls.BankRoots.cs)
        return walls;
    }

    // One wall vertex: on the height profile, with the face's lumps (and the ravine's strata) pushed sideways.
    static Vector3 Place(Ctx c, float x, float z, float s, out float floorY)
    {
        floorY = c.Floor(x, z);
        float y = c.Ravine ? floorY - 0.1f + (c.HLoc(x, z) + 0.1f) * c.Rise(s) : c.BankY(x, z, s);
        float w = Sm(-0.1f, 0.4f, s) * (1 - Sm(1.4f, 2.4f, s));
        if (w > 0 && (c.Ravine || !BigRoots))   // (den round 9: the big roots lie on the bank's own surface, BankY, unjittered)
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

    // The den's roots, grown by rule toward the concept pictures (den_room, den_boss): few big roots and their forks,
    // never a comb of like sticks. Along every wall a big root comes out of the dark over the top and down the face in
    // a long S, forking as it goes, its forks splaying out flat over the floor; loops run along the face (along a low
    // near wall's top, which is what the camera sees of it) and lift off it in arches with dark hollows under them;
    // thin rootlets hang from the crest; medium roots lie out over the top, sinking into the dark. Round a pit the
    // roots hug the rim, fork into the throat and out over the floor, and some curl over the lip and down. Each root
    // walks the surface it lies on (Walk), so it follows the edge wherever it bends.
    const float Spread = 1.7f;   // the wall clusters' spacing (the tri budget's knob)

    static void Roots(Ctx c, Buf b, float[] s, int n)
    {
        float lim = c.Half - 8;
        var wall = new Walk(c, true);
        float acc = 0, next = 1.5f;
        foreach (var (a, e) in Contour(s, n, 0.2f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = (3f + 1.6f * Hash01(hx, hz, 5)) * Spread;
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                WallCluster(wall, b, p, hx, hz);
            }
            acc += len - at;
        }
        var pit = new Walk(c, false);
        var hn = new float[n * n];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++) hn[j * n + i] = c.Bil(c.Hf, -c.Half + i * Cell, -c.Half + j * Cell);
        acc = 0; next = 0.8f;
        foreach (var (a, e) in Contour(hn, n, 0f, c.Half))
        {
            float len = a.DistanceTo(e), at = 0;
            while (acc + len - at >= next)
            {
                at += next - acc; acc = 0;
                var p = a.Lerp(e, len > 0 ? at / len : 0);
                int hx = Mathf.RoundToInt(p.X * 4), hz = Mathf.RoundToInt(p.Y * 4);
                next = 1.2f + 0.8f * Hash01(hx, hz, 9);
                if (Mathf.Abs(p.X) > lim || Mathf.Abs(p.Y) > lim) continue;
                PitCluster(pit, b, p, hx, hz);
            }
            acc += len - at;
        }
    }

    static void WallCluster(Walk w, Buf b, Vector2 p, int hx, int hz)
    {
        var c = w.C;
        float H(int k) => Hash01(hx, hz, k);
        var g = c.Grad(null, p.X, p.Y, true);
        // The roots along a stretch of wall lean one way (by a slow noise, not per root): a braid, not crossed sticks.
        var t = new Vector2(-g.Y, g.X) * (N2(p.X * 0.07f + 3.3f, p.Y * 0.07f - 8.1f) < 0.5f ? -1 : 1);
        float vt = FaceLen(c.HLoc(p.X, p.Y)), fy = c.Floor(p.X, p.Y);
        bool low = c.Near(p.X, p.Y) > 0.5f;   // a near wall: the camera sees its top, never its face
        int sd = hx * 7919 + hz * 104729;
        // A big root: out of the dark on the top, over the crest and down the face in an S, forking, the forks on out
        // over the floor.
        if (H(1) < 0.9f)
        {
            float v0 = vt + 0.4f + 1.2f * H(2);
            var q = p + t * (1.4f * (2 * H(3) - 1));
            if (w.Snap(ref q, v0))
            {
                var sp = new Spec { Pull = 0.55f, PullFloor = 0.3f, Wander = 1.1f, VMin = -0.5f - 0.7f * H(4), VMax = vt + 4f, Depth = low ? 1 : 2, ForkEvery = 1.8f, ForkShare = 0.58f, ForkSpread = 0.75f, ForkLen = 0.7f };
                if (H(6) < 0.45f) sp.Arches = new[] { (v0 - vt + 0.3f * vt, 1.5f + 0.9f * H(7), 0.22f + 0.3f * H(8)) };
                Grow(w, b, q, v0, t, -Mathf.Pi / 2 + 0.9f * (2 * H(9) - 1), 0.25f + 0.25f * H(5) * H(5), v0 + 3f, sp, sd + 1, fy);
            }
        }
        // Loops: big roots running along the face (along a low wall's top), lifting off it in arches, forking.
        int loops = low ? (H(20) < 0.85f ? 1 : 0) + (H(21) < 0.45f ? 1 : 0) : (H(20) < 0.5f ? 1 : 0);
        for (int l = 0; l < loops; l++)
        {
            float len = 4.5f + 3f * H(26 + l);
            float v0 = low ? vt + 0.3f + 2f * H(22 + l) : vt * (0.35f + 0.4f * H(22 + l));
            var dir = H(28 + l) < 0.5f ? t : -t;
            var q = p - dir * (0.4f * len);
            if (!w.Snap(ref q, v0)) continue;
            float lh = low ? 0.35f + 0.5f * H(30 + l) : 0.1f + 0.15f * H(30 + l);
            var sp = new Spec
            {
                Band = v0, Pull = 0.4f, Wander = 0.8f, VMax = vt + 4f, Depth = 1, ForkEvery = 2.2f, ForkShare = 0.45f, ForkSpread = 0.9f, ForkLen = 0.5f,
                Arches = new[] { (0.1f * len, 0.42f * len, lh), (0.56f * len, 0.32f * len, lh * 0.7f) },
            };
            if (!low && H(32 + l) < 0.5f) { sp.TurnAt = 0.62f * len; sp.VMin = -0.6f; }
            Grow(w, b, q, v0, dir, 0.25f * (2 * H(34 + l) - 1), low ? 0.22f + 0.3f * H(24 + l) * H(24 + l) : 0.18f + 0.18f * H(24 + l), len, sp, sd + 10 + l, fy);
        }
        // Rootlets hanging from the crest (only the back and side walls show their face).
        if (!low)
        {
            int k = 2 + (int)(1.99f * H(40));
            for (int i = 0; i < k; i++)
            {
                float Q(int m) => Hash01(hx + 31 * i, hz, m);
                var o = p + t * (2.2f * (2 * Q(41) - 1));
                float v0 = vt - 0.1f;
                if (!w.Snap(ref o, v0)) continue;
                var sp = new Spec { Pull = 1.2f, Wander = 0.9f, FreeTip = Q(45) < 0.65f, VMin = -0.8f, VMax = vt + 1f, MinStand = 0.1f };
                Grow(w, b, o, v0, t, -Mathf.Pi / 2 + 0.5f * (2 * Q(46) - 1), 0.028f + 0.035f * Q(47), 1.2f + 2.2f * Q(48), sp, sd + 40 + i, fy);
            }
        }
        // A medium root lying out over the top, sinking into the dark there.
        if (H(70) < 0.65f)
        {
            float len = 3f + 3f * H(72), v0 = vt + 1.1f + 2.4f * H(71);
            var dir = H(74) < 0.5f ? t : -t;
            var q = p - dir * (0.4f * len);
            if (w.Snap(ref q, v0))
                Grow(w, b, q, v0, dir, 0.3f * (2 * H(75) - 1), 0.14f + 0.16f * H(73), len,
                    new Spec { Band = v0, Pull = 0.5f, Wander = 0.5f, VMax = vt + 4.5f, Depth = 1, ForkEvery = 1.8f, ForkShare = 0.5f, ForkLen = 0.5f, Arches = new[] { (0.3f * len, 0.4f * len, 0.2f * H(76)) } }, sd + 70, fy);
        }
        // Thin ones from the wall's foot out over the floor, forking.
        if (H(80) < 0.45f)
        {
            var q = p + t * (2f * (2 * H(81) - 1));
            if (w.Snap(ref q, 0.5f))
                Grow(w, b, q, 0.5f, t, -Mathf.Pi / 2 + 0.7f * (2 * H(82) - 1), 0.05f + 0.06f * H(83), 2.2f + 1.6f * H(84),
                    new Spec { Pull = 0.4f, PullFloor = 0.12f, Wander = 0.9f, FreeTip = true, VMin = -2.8f, Depth = 1, ForkEvery = 0.9f, ForkShare = 0.55f, ForkSpread = 0.7f, ForkLen = 0.6f }, sd + 80, fy);
        }
    }

    static void PitCluster(Walk w, Buf b, Vector2 p, int hx, int hz)
    {
        var c = w.C;
        float H(int k) => Hash01(hx, hz, k);
        var g = c.Grad(c.Hf, p.X, p.Y, false);
        var t = new Vector2(-g.Y, g.X) * (H(1) < 0.5f ? -1 : 1);
        // the floor outside the rim: what is below it is the throat, and goes dark
        float fy = c.Floor(p.X + g.X * 0.8f, p.Y + g.Y * 0.8f);
        int sd = hx * 7919 + hz * 104729 + 17;
        // A root hugging the rim on the lip, forking into the throat and out over the floor; some curl over and down.
        if (H(2) < 0.85f)
        {
            float band = 0.15f + 0.4f * H(3), len = 1.8f + 1.8f * H(4);
            var q = p;
            if (w.Snap(ref q, band))
            {
                var sp = new Spec { Band = band, Pull = 1f, Wander = 0.5f, VMin = -1.0f, VMax = 3.5f, Depth = 1, ForkEvery = 0.75f, ForkShare = 0.5f, ForkSpread = 0.9f, ForkLen = 0.6f, Kind = 0.9f };
                if (H(6) < 0.55f) { sp.TurnAt = 0.6f * len; sp.FreeTip = true; len += 0.9f; }
                Grow(w, b, q, band, t, -0.35f, 0.04f + 0.06f * H(5) * H(5), len, sp, sd, fy);
            }
        }
        // A thin one out over the floor from the lip, forking.
        if (H(10) < 0.5f)
        {
            var q = p + t * (0.6f * (2 * H(11) - 1));
            if (w.Snap(ref q, 0.1f))
                Grow(w, b, q, 0.1f, t, Mathf.Pi / 2 + 0.8f * (2 * H(12) - 1), 0.035f + 0.04f * H(13), 1.4f + 1.6f * H(14),
                    new Spec { Aim = Mathf.Pi / 2, Pull = 0.35f, Wander = 0.9f, FreeTip = true, VMin = -1.6f, VMax = 4f, Depth = 1, ForkEvery = 0.7f, ForkShare = 0.55f, ForkSpread = 0.7f, ForkLen = 0.6f, Kind = 0.9f }, sd + 5, fy);
        }
    }

    // ------------------------------------------------- what a root walks on --
    const float F0 = -0.4f, F1 = 1.4f;   // the face's foot and crest in s (Ctx.Rise)
    static float RiseD(float s)
    {
        float t = (s - F0) / (F1 - F0);
        return t <= 0 || t >= 1 ? 0 : 6 * t * (1 - t) / (F1 - F0);
    }
    // The wall unrolled: s at v metres over its surface from the foot (s = F0), up the face of a wall hh tall and on
    // over its top; the floor below 0 (v metres in from the foot). Drawn so, a curve keeps its shape on the steep face.
    static float SofV(float v, float hh)
    {
        if (v <= 0) return F0 + v;
        const int N = 20; const float ds = (F1 - F0) / N;
        float k = hh + 0.1f, acc = 0, s = F0;
        for (int i = 0; i < N; i++, s += ds)
        {
            float d = k * RiseD(s + 0.5f * ds), seg = ds * Mathf.Sqrt(1 + d * d);
            if (acc + seg >= v) return s + ds * (v - acc) / seg;
            acc += seg;
        }
        return F1 + (v - acc);
    }
    static float FaceLen(float hh)
    {
        const int N = 20; const float ds = (F1 - F0) / N;
        float k = hh + 0.1f, acc = 0;
        for (int i = 0; i < N; i++) { float d = k * RiseD(F0 + (i + 0.5f) * ds); acc += ds * Mathf.Sqrt(1 + d * d); }
        return acc;
    }

    // A surface a root walks: the wall unrolled (v as SofV's) or the floor round a pit (v the hole field: metres out
    // from the pit's edge, into it below 0).
    sealed class Walk
    {
        public readonly Ctx C;
        public readonly bool Wall;
        public Walk(Ctx c, bool wall) { C = c; Wall = wall; }
        float Field(Vector2 h) => Wall ? C.S(h.X, h.Y) : C.Bil(C.Hf, h.X, h.Y);
        // The way v grows: out from the walkable floor and up the wall; out from the pit over the floor.
        public Vector2 Up(Vector2 h) => Wall ? C.Grad(null, h.X, h.Y, true) : C.Grad(C.Hf, h.X, h.Y, false);
        // Onto the line where the field is v's; false where it cannot get there (a hall narrower than the root's run).
        public bool Snap(ref Vector2 h, float v)
        {
            float want = Wall ? SofV(v, C.HLoc(h.X, h.Y)) : v;
            for (int it = 0; it < 3; it++) h += Up(h) * (want - Field(h));
            return Mathf.Abs(Field(h) - want) < 0.3f;
        }
        // The surface there: its point, its normal, and s (metres outside the walkable edge; the pits' -1).
        public (Vector3 P, Vector3 N, float S) At(Vector2 h)
        {
            float fl = C.Floor(h.X, h.Y);
            float s = Wall ? C.S(h.X, h.Y) : -1f;
            if (Wall && s > F0)
            {
                var g = C.Grad(null, h.X, h.Y, true);
                float d = (C.HLoc(h.X, h.Y) + 0.1f) * RiseD(s);
                return (new Vector3(h.X, Mathf.Max(C.SurfY(h.X, h.Y), fl), h.Y), new Vector3(-g.X * d, 1, -g.Y * d).Normalized(), s);
            }
            const float e = 0.3f;
            var nf = new Vector3(C.Floor(h.X - e, h.Y) - C.Floor(h.X + e, h.Y), 2 * e, C.Floor(h.X, h.Y - e) - C.Floor(h.X, h.Y + e)).Normalized();
            return (new Vector3(h.X, fl, h.Y), nf, s);
        }
    }

    // How a root grows: its aim (a heading in the surface's (along, v) plane: -pi/2 straight down the face and on out
    // over the floor; 0 along) and how hard it is pulled to it (on the floor more loosely, so the forks splay), its
    // wander, a band of v it keeps to (a runner) and where it turns from that to TurnAim, its arches (lifts off the
    // surface: from how far along, how long, how high), its forks, and its ends (sunk into the surface, or a free tip).
    sealed class Spec
    {
        public float Aim = -Mathf.Pi / 2, Pull = 0.9f, PullFloor = 0.3f, Wander = 0.6f;
        public float Band = float.NaN, TurnAt = 1e9f, TurnAim = -Mathf.Pi / 2;
        public float VMin = -1.2f, VMax = 1e9f, MinStand;
        public bool SinkStart = true, FreeTip;
        public int Depth;
        public float ForkEvery = 2f, ForkShare = 0.55f, ForkSpread = 0.75f, ForkLen = 0.6f;
        public (float At, float W, float H)[] Arches = System.Array.Empty<(float, float, float)>();
        public float Kind = 1f;   // COLOR.r: 1 a wall's root, 0.9 a pit's (the throat darkens it)
        public Spec Child(float aim, bool wall) => new()
        {
            Aim = aim, Pull = 0.45f, PullFloor = 0.2f, Wander = Wander * 1.2f, VMin = wall ? Mathf.Max(VMin - 1.1f, -2.8f) : VMin,
            VMax = VMax, MinStand = MinStand, SinkStart = false, FreeTip = true, Depth = Depth - 1,
            ForkEvery = ForkEvery * 0.7f, ForkShare = ForkShare, ForkSpread = ForkSpread, ForkLen = ForkLen, Kind = Kind,
        };
    }

    static float Wrap(float a) => Mathf.PosMod(a + Mathf.Pi, Mathf.Tau) - Mathf.Pi;

    // Grows one root from h (at v) heading ang in the surface's plane (tl along it), r0 thick, len long at most: a
    // smooth wandering path pulled to its aim, a little thicker at knots, tapering, forking on alternate hands (each
    // fork grown the same way, a size down), standing off the surface by its own thickness and its arches.
    static void Grow(Walk w, Buf b, Vector2 h, float v, Vector2 tl, float ang, float r0, float len, Spec sp, int seed, float floorY)
    {
        var pts = new List<Vector3>(); var rs = new List<float>(); var ss = new List<float>(); var lie = new List<Vector3>(); var press = new List<float>();
        float ds = Mathf.Clamp(0.16f + 0.6f * r0, 0.2f, 0.42f);
        int steps = Mathf.Max(3, Mathf.CeilToInt(len / ds));
        ds = len / steps;
        float fs = Hash01(seed, 7, 2) * 50f, rb = r0;
        float fork = sp.Depth > 0 ? sp.ForkEvery * (0.5f + 0.6f * Hash01(seed, 3, 1)) : 1e9f;
        int side = Hash01(seed, 9, 4) < 0.5f ? -1 : 1;
        for (int k = 0; k <= steps; k++)
        {
            float a = k * ds, done = a / len;
            if (k > 0)
            {
                float aim = a > sp.TurnAt ? sp.TurnAim : sp.Aim;
                if (!float.IsNaN(sp.Band) && a <= sp.TurnAt) aim = Mathf.Clamp(1.1f * (sp.Band - v), -0.9f, 0.9f);
                float pull = w.Wall && v < 0 ? sp.PullFloor : sp.Pull;
                ang += (sp.Wander * (2 * N2(a * 0.45f + fs, fs * 0.37f) - 1) + pull * Wrap(aim - ang)) * ds;
                h += tl * (Mathf.Cos(ang) * ds);
                v = Mathf.Min(v + Mathf.Sin(ang) * ds, sp.VMax);
                if (!w.Snap(ref h, v)) break;
                var g = w.Up(h);
                var nt = new Vector2(-g.Y, g.X);
                tl = nt.Dot(tl) < 0 ? -nt : nt;
            }
            var (P, Nm, S) = w.At(h);
            float r = rb * (sp.FreeTip ? Mathf.Lerp(1f, 0.16f, Sm(0.5f, 1f, done)) : Mathf.Lerp(1f, 0.6f, Sm(0.6f, 1f, done)));
            r *= (1 + 0.14f * (2 * N3(a * 1.3f, fs, 1.7f) - 1)) * (1 + 0.3f * Sm(0.7f, 0.88f, N3(a * 1.9f + 11f, fs * 1.3f, 3f)));
            float lift = 0;
            foreach (var (at, wd, hh) in sp.Arches)
                if (a > at && a < at + wd) lift += hh * Mathf.Sin(Mathf.Pi * (a - at) / wd);
            float pr = Mathf.Lerp(Flat, 1f, Sm(0.04f, 0.3f, lift));
            float stand = r * pr * 0.7f + lift;
            if (w.Wall && S > F0 + 0.15f) stand = Mathf.Max(stand, sp.MinStand + r * pr * 0.7f);
            pts.Add(P + Nm * stand); rs.Add(r); ss.Add(S); lie.Add(Nm); press.Add(pr);
            if (a >= fork && done < 0.8f)
            {
                fork += sp.ForkEvery * (0.6f + 0.8f * Hash01(seed, k, 5));
                float cr = rb * sp.ForkShare * (0.8f + 0.4f * Hash01(seed, k, 6));
                if (cr >= 0.026f)
                {
                    float ca = ang + side * sp.ForkSpread * (0.7f + 0.6f * Hash01(seed, k, 7));
                    side = -side;
                    float cl = Mathf.Max(0.8f, (len - a) * sp.ForkLen * (0.7f + 0.6f * Hash01(seed, k, 8)));
                    Grow(w, b, h, v, tl, ca, cr, cl, sp.Child(ca, w.Wall), seed * 31 + k * 7 + 1, floorY);
                    rb *= 0.86f;
                }
            }
            if (v < sp.VMin) break;
        }
        if (pts.Count < 2) return;
        if (sp.SinkStart) pts[0] -= lie[0] * (rs[0] * 1.3f);
        if (!sp.FreeTip)
        {
            pts[^1] -= lie[^1] * (rs[^1] * 1.4f);
            if (pts.Count > 2) pts[^2] -= lie[^2] * (rs[^2] * 0.5f);
        }
        Tube(b, pts, rs, ss, lie, press, floorY, sp.Kind, Hash01(seed, 1, 99), Sides(r0));
    }

    // A root lies pressed to what it rides on: its section flattened along that surface's normal to Flat of round,
    // round where it lifts off in an arch.
    const float Flat = 0.62f;
    static int Sides(float r) => r >= 0.27f ? 8 : r >= 0.1f ? 6 : r >= 0.045f ? 5 : 4;

    // A tube round the centre line, its rings carried along without twisting (parallel transport), the bark's
    // coordinates in metres along it and the share round it; COLOR.a the root's own shade.
    static void Tube(Buf b, List<Vector3> p, List<float> r, List<float> s, List<Vector3> lie, List<float> press, float floorY, float kind, float id, int sides)
    {
        if (p.Count < 2) return;
        var rings = new int[p.Count][];
        var t0 = (p[1] - p[0]).Normalized();
        var n1 = t0.Cross(Mathf.Abs(t0.Y) > 0.9f ? Vector3.Right : Vector3.Up).Normalized();
        float along = 0;
        for (int q = 0; q < p.Count; q++)
        {
            var t = (p[Mathf.Min(q + 1, p.Count - 1)] - p[Mathf.Max(q - 1, 0)]).Normalized();
            if (q > 0) along += p[q].DistanceTo(p[q - 1]);
            var m = n1 - t * n1.Dot(t);
            n1 = m.LengthSquared() > 1e-6f ? m.Normalized() : t.Cross(Mathf.Abs(t.Y) > 0.9f ? Vector3.Right : Vector3.Up).Normalized();
            var n2 = t.Cross(n1);
            var ln = lie[q] - t * lie[q].Dot(t);
            ln = ln.LengthSquared() > 1e-6f ? ln.Normalized() : n1;
            float f = press[q];
            rings[q] = new int[sides + 1];
            for (int a = 0; a <= sides; a++)
            {
                float ang = a * Mathf.Tau / sides;
                var dir = n1 * Mathf.Cos(ang) + n2 * Mathf.Sin(ang);
                float d = dir.Dot(ln);
                var off = dir - ln * (d * (1 - f));
                var nn = (dir - ln * d + ln * (d / f)).Normalized();
                rings[q][a] = b.Add(p[q] + off * r[q], nn, kind, floorY, s[q], along, a / (float)sides, id);
            }
        }
        for (int q = 0; q + 1 < p.Count; q++)
            for (int a = 0; a < sides; a++)
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
        if (!c.Ravine)
        {
            mat.SetShaderParameter("den_alb", GD.Load<TextureLayered>("res://art/dungeon/den/albedo.png"));
            mat.SetShaderParameter("bank_alb", GD.Load<TextureLayered>("res://art/dungeon/den/bank_albedo.png"));
            mat.SetShaderParameter("bank_nrm", GD.Load<TextureLayered>("res://art/dungeon/den/bank_normal.png"));
            // (den round 9, bank lane) With the big roots: the painted bank is the dark tangle between them, its hollows
            // near black and cool (hollow 0.1 lifted every dark of the painting to a mid grey: the round-8 scrim), its
            // normal map softer (its painted edges drew ink fringes), the far wall receding into the dark.
            bool r9 = BigRoots;
            mat.SetShaderParameter("beyond_k", Args.Num("den-beyond", r9 ? 0.3f : 0.45f));
            mat.SetShaderParameter("bank_gain", Args.Num("den-bank-gain", r9 ? 0.9f : 1.6f));
            mat.SetShaderParameter("hollow_min", Args.Num("den-hollow", r9 ? 0.02f : 0.1f));
            mat.SetShaderParameter("bank_nk", Args.Num("den-bank-nk", r9 ? 0.25f : 0.6f));
            mat.SetShaderParameter("r9", r9 ? 1f : 0f);
            mat.SetShaderParameter("broot_col", Args.Get("den-root-col") is string rc ? new Color(rc).SrgbToLinear() : new Color(0.2f, 0.12f, 0.075f));
            mat.SetShaderParameter("wall_top_k", Args.Num("den-wall-top", 0.55f));
        }
        return mat;
    }
}
