using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's painted floor decals (art/dungeon/den/floor_decals.png, tools/look/den_roots.py build floor): whole pits in
/// plan (never turned), a dark root frame along the camera-side walls, long floor roots running out from the other banks.
/// Same two shaders and mesh build as the bank decals; laid flat just over the floor.
/// </summary>
public static partial class DungeonDress
{
    sealed record FloorDecal(string Kind, Rect2 Uv, Vector2 Metres, Vector2 Anchor, float MouthR, float[] Harm, Vector2 Light);
    /// <summary>The painted pits own the den's holes: the floor (dungeon_floor.gdshader pit_decals) draws no hole of its own.</summary>
    internal const bool PitDecals = true;
    const bool FrameDecals = false, FloorRoots = true;   // (round 6: the camera-side frames never showed under the HUD: off; the floor roots repainted as the bank spilling onto the floor, on every bank, the camera side with its own lit set)
    static readonly float PitWarmLift = SurvivorUnchained.Args.Num("pit-warm-lift", 2.0f), HollowLift = SurvivorUnchained.Args.Num("den-hollow-lift", 1.0f);

    static void DenFloorDecals(Ctx c)
    {
        var z = c.Z;
        Decals();
        var all = LoadFloorDecals("res://art/dungeon/den/floor_decals.json");
        var pits = all.FindAll(d => d.Kind == "pit"); var frames = all.FindAll(d => d.Kind == "frame");
        var roots = all.FindAll(d => d.Kind == "floor"); var rootsS = all.FindAll(d => d.Kind == "floor_s");
        var big = PitArt().FindAll(d => d.Kind == "bigpit"); var hol = PitArt().FindAll(d => d.Kind == "hollow");
        var b = new DecalBuf(); var bp = new DecalBuf(); var bb = new DecalBuf(); var bhol = new DecalBuf();
        int nPit = 0, nFrame = 0, nRoot = 0, nBig = 0, nHol = 0, nBr = 0;
        float cos70 = Mathf.Cos(Mathf.DegToRad(70f));
        bool LightOk(Vector2 top, bool mirror, Vector2 dl)
        {
            var right = new Vector2(-top.Y, top.X) * (mirror ? -1f : 1f);
            return (right * dl.X + top * dl.Y).Normalized().Dot(decalLight) >= cos70;
        }

        var pitC = DenPits(c);
        if (PitDecals)
            foreach (var (p, rad, co) in pitC)
            {
                if (SetMode > 0 && SetIn(p.X, p.Y) && PlaceSetHole(c, "H2", p, co, 0)) continue;   // (r10d: the painted pit H2)
                // (round 7) a big hole (r over 4 m) takes a pit painted at its own size: the 2.6 m pit stretched 2.1-2.4x
                // read as a flat black disk ringed by jagged black fragments
                bool isBig = rad > 4f && big.Count > 0;
                var set = isBig ? big : pits;
                var d = set[(int)(Hash((int)(p.X * 10), (int)(p.Y * 10), 951) * set.Count) % set.Count];
                AddPit(c, isBig ? bb : bp, d, p, co);
                if (isBig) nBig++; else nPit++;
            }
        // the lair's shallow hollows: painted dishes, walkable, no hole (laid like a pit, scaled whole, never turned)
        foreach (var (hp, hr, vi) in DenHollows(c))
        {
            if (SetMode > 0 && SetIn(hp.X, hp.Y) && PlaceSetHole(c, "H1", hp, new[] { hr }, vi)) continue;   // (r10d: the painted hollows H1)
            AddPit(c, bhol, hol[vi], hp, new[] { hr }, hr / hol[vi].MouthR);
            nHol++;
        }
        bool NearPit(Vector2 p, float m)
        {
            foreach (var (pc, rad, _) in pitC) if (p.DistanceTo(pc) < rad + m) return true;
            return false;
        }

        // ---- frame and floor roots: along the walls' feet ----
        {
            const float scan = 0.5f;
            int n = (int)(z.Size / scan);
            var takenF = new List<(Vector2 p, float gap)>();
            var takenR = new List<(Vector2 p, float gap)>();
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    float x = -z.Half + (i + 0.5f) * scan, zz = -z.Half + (j + 0.5f) * scan;
                    float w = Wall(c, x, zz);
                    if (SetMode > 0 && SetIn(x, zz)) continue;   // (round 10: the painted set's spills own the banks' feet)
                    if (Mathf.Abs(w - 0.3f) > 0.12f || Hole(c, x, zz) < 1.2f) continue;
                    float gx = Wall(c, x + 0.4f, zz) - Wall(c, x - 0.4f, zz), gz = Wall(c, x, zz + 0.4f) - Wall(c, x, zz - 0.4f);
                    var g = new Vector2(gx, gz);
                    if (g.LengthSquared() < 1e-8f) continue;
                    var top = -g.Normalized();
                    var p = new Vector2(x, zz);
                    var edge = p + top * w;  // (the walkable edge: the foot of the bank)
                    bool south = top.Y > 0.64f;
                    if (south && FrameDecals)
                    {
                        float gap = 3.5f + 1.0f * Hash(i, j, 961);
                        bool near = false;
                        foreach (var t in takenF) { float g2 = Mathf.Max(gap, t.gap); if (t.p.DistanceSquaredTo(p) < g2 * g2) { near = true; break; } }
                        if (near) continue;
                        takenF.Add((p, gap));
                        if (Hole(c, x, zz) < 1.5f || NearPit(p, 1.5f)) continue;
                        var d = frames[(int)(Hash(i, j, 962) * frames.Count) % frames.Count];
                        AddFlat(c, b, d, edge + top * 0.2f, top, 1f, false, 0f, true);
                        nFrame++;
                    }
                    else if (FloorRoots)
                    {
                        // the bank spilling onto the floor: a root set every 3-4.5 m along every bank's foot (the camera
                        // side's painted for its own light), turned up to +-18 degrees, shortened (to 0.7) before it is
                        // dropped where its run would reach a pit or the far wall
                        float gap = 3.0f + 1.5f * Hash(i, j, 971);
                        bool near = false;
                        foreach (var t in takenR) { float g2 = Mathf.Max(gap, t.gap); if (t.p.DistanceSquaredTo(p) < g2 * g2) { near = true; break; } }
                        if (near) continue;
                        takenR.Add((p, gap));
                        if (Hash(i, j, 972) < 0.12f) continue;
                        var set = south && rootsS.Count > 0 ? rootsS : roots;
                        var d = set[(int)(Hash(i, j, 973) * set.Count) % set.Count];
                        var tp = top.Rotated((Hash(i, j, 975) - 0.5f) * Mathf.DegToRad(36f));
                        bool mirror;
                        if (LightOk(tp, false, d.Light)) mirror = false;
                        else if (LightOk(tp, true, d.Light)) mirror = true;
                        else if (LightOk(top, false, d.Light)) { tp = top; mirror = false; }
                        else if (LightOk(top, true, d.Light)) { tp = top; mirror = true; }
                        else continue;
                        float sc = 0.95f + 0.2f * Hash(i, j, 974);
                        bool fits = false;
                        for (int tries = 0; ; tries++)
                        {
                            float len = d.Metres.Y * sc * 0.9f;
                            fits = true;
                            for (int s = 0; s < 8 && fits; s++)
                            {
                                var sp = edge - tp * (len * (s + 0.5f) / 8f);
                                if (Hole(c, sp.X, sp.Y) < 0.4f || Wall(c, sp.X, sp.Y) < 0f) fits = false;
                            }
                            if (fits || tries == 3) break;
                            sc *= 0.88f;
                        }
                        if (!fits) continue;
                        AddFlat(c, b, d, edge, tp, sc, mirror, 0f, true);
                        nRoot++;
                    }
                }
        }

        // ---- (round 7) roots at the big boulders' feet: 1-3 of the floor set running out from under each ----
        int bi = 0;
        foreach (var (bp0, bh) in c.Boulders)
        {
            bi++;
            if (bh < 1.0f || roots.Count == 0 || (SetMode > 0 && SetIn(bp0.X, bp0.Y))) continue;
            var inw = new Vector2(Wall(c, bp0.X + 0.5f, bp0.Y) - Wall(c, bp0.X - 0.5f, bp0.Y), Wall(c, bp0.X, bp0.Y + 0.5f) - Wall(c, bp0.X, bp0.Y - 0.5f));
            inw = inw.LengthSquared() < 1e-8f ? Vector2.Down : inw.Normalized();
            int m = 1 + (int)(2.99f * Hash(bi, 1, 981));
            for (int k = 0; k < m; k++)
            {
                var outd = inw.Rotated((k - 0.5f * (m - 1)) * 0.9f + (Hash(bi, k, 982) - 0.5f) * 0.5f);
                var tp = -outd;   // (the rect's top against the stone, its run out over the floor)
                var d = roots[(int)(Hash(bi, k, 983) * roots.Count) % roots.Count];
                bool mirror;
                if (LightOk(tp, false, d.Light)) mirror = false; else if (LightOk(tp, true, d.Light)) mirror = true; else continue;
                var anchor = bp0 + outd * (bh * 0.55f);
                float sc = 0.55f + 0.2f * Hash(bi, k, 984);
                bool fits = true;
                for (int q = 0; q < 6 && fits; q++)
                {
                    var sp = anchor + outd * (d.Metres.Y * sc * (q + 0.5f) / 6f);
                    if (Hole(c, sp.X, sp.Y) < 0.4f || Wall(c, sp.X, sp.Y) < 0f) fits = false;
                }
                if (!fits) continue;
                AddFlat(c, b, d, anchor, tp, sc, mirror, 0f, true);
                nBr++;
            }
        }

        GD.Print($"DenFloorDecals: {nBig} big pits, {nHol} hollows, {nBr} boulder roots, {nPit} pits, {nFrame} frame, {nRoot} floor, {(b.I.Count + bp.I.Count) / 3} tris");
        var tex = GD.Load<Texture2D>("res://art/dungeon/den/floor_decals.png");
        void Emit(DecalBuf buf, string name, bool pit, Texture2D tex, float lift)
        {
            if (buf.Count == 0) return;
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Mesh.ArrayType.Max);
            var nrm = new Vector3[buf.V.Count];
            System.Array.Fill(nrm, Vector3.Up);
            arr[(int)Mesh.ArrayType.Vertex] = buf.V.ToArray();
            arr[(int)Mesh.ArrayType.Normal] = nrm;
            arr[(int)Mesh.ArrayType.TexUV] = buf.U.ToArray();
            arr[(int)Mesh.ArrayType.Index] = buf.I.ToArray();
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_bank_decal.gdshader") };
            mat.SetShaderParameter("atlas", tex);
            mat.SetShaderParameter("field", DungeonFloor.Field(z));
            mat.SetShaderParameter("half_size", z.Half);
            mat.SetShaderParameter("step", z.Step);
            mat.SetShaderParameter("res", (float)z.Res);
            // (a pit paints its own hole: the darkening toward the holes would black out its far wall and lip)
            // and its lip, painted against a floor (88, 58, 40) the game's is ~1.4x lighter than, lifted to stay lit
            if (pit) { mat.SetShaderParameter("hole_dark", 0f); mat.SetShaderParameter("warm_lift", lift); }
            var shade = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_bank_shadow.gdshader") };
            shade.SetShaderParameter("atlas", tex);
            mesh.SurfaceSetMaterial(0, mat);
            mesh.SurfaceSetMaterial(1, shade);
            c.Root.AddChild(new MeshInstance3D { Name = name, Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        Emit(b, "FloorDecals", false, tex, 1f);
        Emit(bp, "PitDecals", true, tex, PitWarmLift);
        var pitTex = GD.Load<Texture2D>("res://art/dungeon/den/pit_decals.png");
        Emit(bb, "BigPitDecals", true, pitTex, PitWarmLift);
        Emit(bhol, "HollowDecals", true, pitTex, HollowLift);   // (the hollows' bowls painted at the lair's own values: lifted x2 they read as pale tubs)
        c.Count["decal floor pit"] = nPit; c.Count["decal big pit"] = nBig; c.Count["decal hollow"] = nHol; c.Count["decal floor frame"] = nFrame; c.Count["decal floor root"] = nRoot;
    }

    static List<FloorDecal> LoadFloorDecals(string path)
    {
        var list = new List<FloorDecal>();
        if (!FileAccess.FileExists(path)) return list;
        using var f = FileAccess.Open(path, FileAccess.ModeFlags.Read);
        var doc = JsonDocument.Parse(f.GetAsText());
        var size = doc.RootElement.GetProperty("size");
        float AW = size[0].GetSingle(), AH = size[1].GetSingle();
        var l = doc.RootElement.GetProperty("light");
        float lx = l[0].GetSingle(), ly = -l[1].GetSingle();
        foreach (var d in doc.RootElement.GetProperty("decals").EnumerateArray())
        {
            var r = d.GetProperty("rect"); var m = d.GetProperty("metres"); var a = d.GetProperty("anchor");
            float mr = d.TryGetProperty("mouth_r", out var mrp) ? mrp.GetSingle() : 0f;
            var harm = new List<float>();
            if (d.TryGetProperty("mouth_harm", out var hp))
                foreach (var t in hp.EnumerateArray()) { harm.Add(t[0].GetSingle()); harm.Add(t[1].GetSingle()); harm.Add(t[2].GetSingle()); }
            var dl = d.TryGetProperty("light", out var lp) ? new Vector2(lp[0].GetSingle(), -lp[1].GetSingle()) : new Vector2(lx, ly);
            list.Add(new FloorDecal(d.GetProperty("kind").GetString()!, new Rect2(r[0].GetSingle() / AW, r[1].GetSingle() / AH, r[2].GetSingle() / AW, r[3].GetSingle() / AH),
                new Vector2(m[0].GetSingle(), m[1].GetSingle()), new Vector2(a[0].GetSingle(), a[1].GetSingle()), mr, harm.ToArray(), dl));
        }
        return list;
    }
    static List<FloorDecal>? pitArt;
    static List<FloorDecal> PitArt() => pitArt ??= LoadFloorDecals("res://art/dungeon/den/pit_decals.json");

    static ZoneData? hollowsFor;
    static List<(Vector2 p, float r, int v)> hollowsCache = new();

    /// <summary>(round 7) The lair's shallow hollows, as den_boss.png's floor has them: 4-6 painted dishes (dish radius
    /// 1.3-2.6 m) on its open floor, clear of the walls, the pits and each other; one in a clearing now and then. Cached per
    /// zone (the floor decals lay them; the litter heaps bones at their lips and keeps off their dishes).</summary>
    static List<(Vector2 p, float r, int v)> DenHollows(Ctx c)
    {
        var z = c.Z;
        if (hollowsFor == z) return hollowsCache;
        hollowsFor = z;
        var res = hollowsCache = new();
        var hol = PitArt().FindAll(d => d.Kind == "hollow");
        if (hol.Count == 0) return res;
        int ri = 0;
        foreach (var r in z.Rooms)
        {
            ri++;
            int want = r.Kind == "Boss" ? 4 + (int)(2.99f * Hash(ri, 1, 991)) : r.Kind == "Clearing" && Hash(ri, 2, 991) < 0.5f ? 1 : 0;
            for (int t = 0; t < 40 && want > 0; t++)
            {
                float a = Hash(ri, t, 992) * Mathf.Tau, dd = Mathf.Sqrt(Hash(ri, t, 993)) * r.R * 0.85f;
                var p = new Vector2(r.X + Mathf.Cos(a) * dd, r.Z + Mathf.Sin(a) * dd);
                int v = (int)(Hash(ri, t, 994) * hol.Count) % hol.Count;
                float hr = hol[v].MouthR * (0.95f + 0.15f * Hash(ri, t, 995));
                float reach = hr + 0.5f;   // (the rim and its shadow)
                if (Wall(c, p.X, p.Y) < reach + 0.8f || Hole(c, p.X, p.Y) < reach + 1.5f) continue;
                bool clash = false;
                foreach (var (q, qr, _) in res) if (q.DistanceTo(p) < qr + hr + 2.0f) { clash = true; break; }
                if (clash) continue;
                res.Add((p, hr, v));
                want--;
            }
        }
        return res;
    }

    static ZoneData? pitsFor;
    static List<(Vector2 p, float r, float[] co)> pitsCache = new();

    /// <summary>The den's pits (connected cells of Hole &lt; 0 over 2 m2): centre = centroid, the mouth's outline along
    /// 96 rays (to Hole = 0) as a Fourier series to the 6th; cached per zone (the floor decals and the litter's piles).</summary>
    static List<(Vector2 p, float r, float[] co)> DenPits(Ctx c)
    {
        var z = c.Z;
        if (pitsFor == z) return pitsCache;
        pitsFor = z;
        var pitC = pitsCache = new List<(Vector2 p, float r, float[] co)>();
        if (z.HoleField == null) return pitC;
        const float scan = 0.25f;
        int n = (int)(z.Size / scan);
        var id = new int[n * n];
        var q = new Queue<int>();
        int pid = 0;
        for (int k0 = 0; k0 < n * n; k0++)
        {
            if (id[k0] != 0) continue;
            int i0 = k0 % n, j0 = k0 / n;
            if (Hole(c, -z.Half + (i0 + 0.5f) * scan, -z.Half + (j0 + 0.5f) * scan) >= 0f) continue;
            pid++; id[k0] = pid; q.Enqueue(k0);
            int cnt = 0; double sx = 0, sz = 0;
            while (q.Count > 0)
            {
                int cur = q.Dequeue(); cnt++;
                int ci = cur % n, cj = cur / n;
                sx += -z.Half + (ci + 0.5f) * scan; sz += -z.Half + (cj + 0.5f) * scan;
                for (int dd = 0; dd < 4; dd++)
                {
                    int ni = ci + (dd == 0 ? 1 : dd == 1 ? -1 : 0), nj = cj + (dd == 2 ? 1 : dd == 3 ? -1 : 0);
                    if (ni < 0 || nj < 0 || ni >= n || nj >= n) continue;
                    int nk = nj * n + ni;
                    if (id[nk] != 0 || Hole(c, -z.Half + (ni + 0.5f) * scan, -z.Half + (nj + 0.5f) * scan) >= 0f) continue;
                    id[nk] = pid; q.Enqueue(nk);
                }
            }
            if (cnt < 32) continue;  // (under 2 m2: a dimple, not a pit)
            var ctr = new Vector2((float)(sx / cnt), (float)(sz / cnt));
            var rr = new float[96];
            float tot = 0;
            for (int a = 0; a < 96; a++)
            {
                var dir = new Vector2(Mathf.Cos(a * Mathf.Tau / 96f), Mathf.Sin(a * Mathf.Tau / 96f));
                float s = 0.05f;
                while (s < 20f && Hole(c, ctr.X + dir.X * s, ctr.Y + dir.Y * s) < 0f) s += 0.05f;
                float lo = s - 0.05f, hi = s;
                for (int it = 0; it < 6; it++) { float mm = 0.5f * (lo + hi); if (Hole(c, ctr.X + dir.X * mm, ctr.Y + dir.Y * mm) < 0f) lo = mm; else hi = mm; }
                rr[a] = 0.5f * (lo + hi); tot += rr[a];
            }
            pitC.Add((ctr, tot / 96f, Fourier(rr, 6)));
        }
        return pitC;
    }

    /// <summary>The den floor's drawn height: the ground's own with MapGen's pit sink undone, node by node, as
    /// dungeon_floor.gdshader's vertex() undoes it (the floor runs level to and over the mouth).</summary>
    static float FloorY(Ctx c, float x, float zz)
    {
        var z = c.Z;
        float u = Mathf.Clamp((x + z.Half) / z.Step, 0, z.Res - 1.001f), v = Mathf.Clamp((zz + z.Half) / z.Step, 0, z.Res - 1.001f);
        int i = (int)u, j = (int)v; float fu = u - i, fv = v - j;
        float N(int ii, int jj)
        {
            float nx = -z.Half + ii * z.Step, nz = -z.Half + jj * z.Step;
            return H(c, nx, nz) + 2.4f * (1f - Mathf.SmoothStep(-1.6f, 0.3f, Hole(c, nx, nz)));
        }
        return Mathf.Lerp(Mathf.Lerp(N(i, j), N(i + 1, j), fu), Mathf.Lerp(N(i, j + 1), N(i + 1, j + 1), fu), fv);
    }

    /// <summary>A closed outline's radii (evenly round from +x) as a Fourier series to the k-th: [a0, a1, b1, .., ak, bk].</summary>
    static float[] Fourier(float[] r, int k)
    {
        int n = r.Length;
        var co = new float[2 * k + 1];
        for (int i = 0; i < n; i++)
        {
            float th = i * Mathf.Tau / n;
            co[0] += r[i] / n;
            for (int h = 1; h <= k; h++) { co[2 * h - 1] += 2f / n * r[i] * Mathf.Cos(h * th); co[2 * h] += 2f / n * r[i] * Mathf.Sin(h * th); }
        }
        return co;
    }
    static float FourierAt(float[] co, float th)
    {
        float r = co[0];
        for (int h = 1; 2 * h < co.Length; h++) r += co[2 * h - 1] * Mathf.Cos(h * th) + co[2 * h] * Mathf.Sin(h * th);
        return r;
    }

    /// <summary>One pit decal, never turned: laid on the floor's drawn height (FloorY: a flat decal on a rolling floor
    /// was cut by it along a straight line), its painted mouth (mouth_harm) stretched, angle by angle, onto the hole's
    /// own outline `co` (Fourier, to the 6th), so the lip sits on the hole's edge all the way round.</summary>
    static void AddPit(Ctx c, DecalBuf b, FloorDecal d, Vector2 ctr, float[] co, float fixedScale = 0f)
    {
        float W = d.Metres.X, Hh = d.Metres.Y;
        int nx = Mathf.CeilToInt(W / 0.25f) + 1, ny = Mathf.CeilToInt(Hh / 0.25f) + 1;
        int base0 = b.V.Count;
        float gmin = 9f, gmax = 0f;
        for (int q = 0; q < ny; q++)
            for (int p = 0; p < nx; p++)
            {
                float s = (float)p / (nx - 1), t = (float)q / (ny - 1);  // (t 0 = the image's top: north)
                var l = new Vector2((s - d.Anchor.X) * W, (t - d.Anchor.Y) * Hh);  // painted metres from the mouth's centre (x east, y south)
                float th = Mathf.Atan2(l.Y, l.X), rp = d.MouthR;
                for (int h = 0; h + 2 < d.Harm.Length; h += 3) rp += d.MouthR * d.Harm[h + 1] * Mathf.Sin(d.Harm[h] * th + d.Harm[h + 2]);
                float g = fixedScale > 0f ? fixedScale : FourierAt(co, th) / rp;
                gmin = Mathf.Min(gmin, g); gmax = Mathf.Max(gmax, g);
                var w = ctr + l * g;
                b.V.Add(new Vector3(w.X, FloorY(c, w.X, w.Y) + 0.06f, w.Y));
                b.U.Add(new Vector2(d.Uv.Position.X + s * d.Uv.Size.X, d.Uv.Position.Y + t * d.Uv.Size.Y));
            }
        for (int q = 0; q < ny - 1; q++)
            for (int p = 0; p < nx - 1; p++)
            {
                int a = base0 + q * nx + p, e = a + 1, f = a + nx, g = f + 1;
                b.I.Add(a); b.I.Add(f); b.I.Add(e); b.I.Add(e); b.I.Add(f); b.I.Add(g);
            }
        b.Count++;
        // (the old flat lay, for the record: how far the rolling floor rose through it)
        float flat = H(c, ctr.X + co[0] + 0.3f, ctr.Y) + 0.06f, rise = -9f;
        for (int k = base0; k < b.V.Count; k++) rise = Mathf.Max(rise, b.V[k].Y - 0.06f - flat);
        GD.Print($"DenPit at {ctr.X:F1},{ctr.Y:F1}: r {co[0]:F2}, painted stretch x{gmin:F2}-{gmax:F2}, floor over the old flat lay by {rise:F2} m");
    }

    /// <summary>One floor decal: its anchor point (fraction of the rect) on `anchor`, the rect's top edge facing `top`.
    /// Flat at flatY when drape is false, else draped on the higher of floor and bank.</summary>
    static void AddFlat(Ctx c, DecalBuf b, FloorDecal d, Vector2 anchor, Vector2 top, float scale, bool mirror, float flatY, bool drape)
    {
        var right = new Vector2(-top.Y, top.X);
        float W = d.Metres.X * scale, Hh = d.Metres.Y * scale;
        int nx = Mathf.Max(2, Mathf.CeilToInt(W / 0.4f) + 1), ny = Mathf.Max(2, Mathf.CeilToInt(Hh / 0.3f) + 1);
        int base0 = b.V.Count;
        for (int q = 0; q < ny; q++)
            for (int p = 0; p < nx; p++)
            {
                float s = (float)p / (nx - 1), t = (float)q / (ny - 1);  // (t 0 = the image's top)
                var w = anchor + right * ((s - d.Anchor.X) * W) - top * ((t - d.Anchor.Y) * Hh);
                float y = flatY;
                if (drape) y = Mathf.Max(H(c, w.X, w.Y), DungeonWalls.BankY(c.Z, w.X, w.Y)) + 0.03f;
                b.V.Add(new Vector3(w.X, y, w.Y));
                float u = mirror ? 1f - s : s;
                b.U.Add(new Vector2(d.Uv.Position.X + u * d.Uv.Size.X, d.Uv.Position.Y + t * d.Uv.Size.Y));
            }
        for (int q = 0; q < ny - 1; q++)
            for (int p = 0; p < nx - 1; p++)
            {
                int a = base0 + q * nx + p, e = a + 1, f = a + nx, g = f + 1;
                b.I.Add(a); b.I.Add(f); b.I.Add(e); b.I.Add(e); b.I.Add(f); b.I.Add(g);
            }
        b.Count++;
    }
}
