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
    sealed record FloorDecal(string Kind, Rect2 Uv, Vector2 Metres, Vector2 Anchor, float MouthR, float[] Harm);
    /// <summary>The painted pits own the den's holes: the floor (dungeon_floor.gdshader pit_decals) draws no hole of its own.</summary>
    internal const bool PitDecals = true;
    const bool FrameDecals = false, FloorRoots = false;   // (round 6: the camera-side frames never showed under the HUD; the thin floor roots read as scratches: both off)
    static readonly float PitWarmLift = SurvivorUnchained.Args.Num("pit-warm-lift", 2.0f);

    static void DenFloorDecals(Ctx c)
    {
        var z = c.Z;
        Decals();
        using var f = FileAccess.Open("res://art/dungeon/den/floor_decals.json", FileAccess.ModeFlags.Read);
        var doc = JsonDocument.Parse(f.GetAsText());
        var size = doc.RootElement.GetProperty("size");
        float AW = size[0].GetSingle(), AH = size[1].GetSingle();
        var l = doc.RootElement.GetProperty("light");
        float lx = l[0].GetSingle(), ly = -l[1].GetSingle();
        var pits = new List<FloorDecal>(); var frames = new List<FloorDecal>(); var roots = new List<FloorDecal>();
        foreach (var d in doc.RootElement.GetProperty("decals").EnumerateArray())
        {
            var r = d.GetProperty("rect"); var m = d.GetProperty("metres"); var a = d.GetProperty("anchor");
            string kind = d.GetProperty("kind").GetString()!;
            float mr = d.TryGetProperty("mouth_r", out var mrp) ? mrp.GetSingle() : 0f;
            var harm = new List<float>();
            if (d.TryGetProperty("mouth_harm", out var hp))
                foreach (var t in hp.EnumerateArray()) { harm.Add(t[0].GetSingle()); harm.Add(t[1].GetSingle()); harm.Add(t[2].GetSingle()); }
            var fd = new FloorDecal(kind, new Rect2(r[0].GetSingle() / AW, r[1].GetSingle() / AH, r[2].GetSingle() / AW, r[3].GetSingle() / AH),
                new Vector2(m[0].GetSingle(), m[1].GetSingle()), new Vector2(a[0].GetSingle(), a[1].GetSingle()), mr, harm.ToArray());
            (kind == "pit" ? pits : kind == "frame" ? frames : roots).Add(fd);
        }
        var b = new DecalBuf(); var bp = new DecalBuf();
        int nPit = 0, nFrame = 0, nRoot = 0;
        float cos70 = Mathf.Cos(Mathf.DegToRad(70f));
        bool LightOk(Vector2 top, bool mirror)
        {
            var right = new Vector2(-top.Y, top.X) * (mirror ? -1f : 1f);
            return (right * lx + top * ly).Normalized().Dot(decalLight) >= cos70;
        }

        // ---- pits: connected cells of Hole < 0; centre = centroid, the mouth's outline along 96 rays (to Hole = 0) ----
        var pitC = new List<(Vector2 p, float r, float[] co)>();
        if (z.HoleField != null)
        {
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
        }
        if (PitDecals)
            foreach (var (p, rad, co) in pitC)
            {
                var d = pits[(int)(Hash((int)(p.X * 10), (int)(p.Y * 10), 951) * pits.Count) % pits.Count];
                AddPit(c, bp, d, p, co);
                nPit++;
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
                    if (Mathf.Abs(w - 0.3f) > 0.12f || Hole(c, x, zz) < 1.2f) continue;
                    float gx = Wall(c, x + 0.4f, zz) - Wall(c, x - 0.4f, zz), gz = Wall(c, x, zz + 0.4f) - Wall(c, x, zz - 0.4f);
                    var g = new Vector2(gx, gz);
                    if (g.LengthSquared() < 1e-8f) continue;
                    var top = -g.Normalized();
                    var p = new Vector2(x, zz);
                    var edge = p + top * w;  // (the walkable edge: the foot of the bank)
                    if (top.Y > 0.64f)
                    {
                        if (!FrameDecals) continue;
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
                    else
                    {
                        if (!FloorRoots) continue;
                        float gap = 5f + 3f * Hash(i, j, 971);
                        bool near = false;
                        foreach (var t in takenR) { float g2 = Mathf.Max(gap, t.gap); if (t.p.DistanceSquaredTo(p) < g2 * g2) { near = true; break; } }
                        if (near) continue;
                        takenR.Add((p, gap));
                        if (Hash(i, j, 972) < 0.4f) continue;
                        bool mirror = false;
                        if (!LightOk(top, false)) { if (!LightOk(top, true)) continue; mirror = true; }
                        var d = roots[(int)(Hash(i, j, 973) * roots.Count) % roots.Count];
                        float sc = 0.9f + 0.25f * Hash(i, j, 974);
                        float len = d.Metres.Y * sc;
                        bool bad = false;
                        for (int s = 0; s < 6 && !bad; s++)
                        {
                            var sp = edge - top * (len * (s + 0.5f) / 6f);
                            if (Hole(c, sp.X, sp.Y) < 0.5f || Wall(c, sp.X, sp.Y) < 0f) bad = true;
                        }
                        if (bad) continue;
                        AddFlat(c, b, d, edge, top, sc, mirror, 0f, true);
                        nRoot++;
                    }
                }
        }

        GD.Print($"DenFloorDecals: {nPit} pits, {nFrame} frame, {nRoot} floor, {(b.I.Count + bp.I.Count) / 3} tris");
        var tex = GD.Load<Texture2D>("res://art/dungeon/den/floor_decals.png");
        var shade = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_bank_shadow.gdshader") };
        shade.SetShaderParameter("atlas", tex);
        void Emit(DecalBuf buf, string name, bool pit)
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
            if (pit) { mat.SetShaderParameter("hole_dark", 0f); mat.SetShaderParameter("warm_lift", PitWarmLift); }
            mesh.SurfaceSetMaterial(0, mat);
            mesh.SurfaceSetMaterial(1, shade);
            c.Root.AddChild(new MeshInstance3D { Name = name, Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        Emit(b, "FloorDecals", false);
        Emit(bp, "PitDecals", true);
        c.Count["decal floor pit"] = nPit; c.Count["decal floor frame"] = nFrame; c.Count["decal floor root"] = nRoot;
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
    static void AddPit(Ctx c, DecalBuf b, FloorDecal d, Vector2 ctr, float[] co)
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
                float g = FourierAt(co, th) / rp;
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
