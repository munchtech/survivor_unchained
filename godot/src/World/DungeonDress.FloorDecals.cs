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
    sealed record FloorDecal(string Kind, Rect2 Uv, Vector2 Metres, Vector2 Anchor, float MouthR);
    const bool PitDecals = true, FrameDecals = true, FloorRoots = true;

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
            var fd = new FloorDecal(kind, new Rect2(r[0].GetSingle() / AW, r[1].GetSingle() / AH, r[2].GetSingle() / AW, r[3].GetSingle() / AH),
                new Vector2(m[0].GetSingle(), m[1].GetSingle()), new Vector2(a[0].GetSingle(), a[1].GetSingle()), mr);
            (kind == "pit" ? pits : kind == "frame" ? frames : roots).Add(fd);
        }
        var b = new DecalBuf();
        int nPit = 0, nFrame = 0, nRoot = 0;
        float cos70 = Mathf.Cos(Mathf.DegToRad(70f));
        bool LightOk(Vector2 top, bool mirror)
        {
            var right = new Vector2(-top.Y, top.X) * (mirror ? -1f : 1f);
            return (right * lx + top * ly).Normalized().Dot(decalLight) >= cos70;
        }

        // ---- pits: connected cells of Hole < 0; centre = centroid, radius = mean zero-crossing distance ----
        var pitC = new List<(Vector2 p, float r)>();
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
                float tot = 0; int rays = 0;
                for (int a = 0; a < 48; a++)
                {
                    var dir = new Vector2(Mathf.Cos(a * Mathf.Tau / 48f), Mathf.Sin(a * Mathf.Tau / 48f));
                    float s = 0;
                    for (; s < 20f; s += 0.05f)
                    {
                        var w = ctr + dir * (s + 0.05f);
                        if (Hole(c, w.X, w.Y) >= 0f) break;
                    }
                    tot += s + 0.025f; rays++;
                }
                pitC.Add((ctr, tot / rays));
            }
        }
        if (PitDecals)
            foreach (var (p, rad) in pitC)
            {
                var d = pits[(int)(Hash((int)(p.X * 10), (int)(p.Y * 10), 951) * pits.Count) % pits.Count];
                float sc = rad / d.MouthR;
                // level to the mouth: the floor's height just outside the mouth
                float y = H(c, p.X + rad + 0.3f, p.Y);
                AddFlat(c, b, d, p, new Vector2(0, -1), sc, false, y + 0.06f, false);
                nPit++;
            }
        bool NearPit(Vector2 p, float m)
        {
            foreach (var (pc, rad) in pitC) if (p.DistanceTo(pc) < rad + m) return true;
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

        GD.Print($"DenFloorDecals: {nPit} pits, {nFrame} frame, {nRoot} floor, {b.I.Count / 3} tris");
        if (b.Count == 0) return;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        var nrm = new Vector3[b.V.Count];
        System.Array.Fill(nrm, Vector3.Up);
        arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = nrm;
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        var tex = GD.Load<Texture2D>("res://art/dungeon/den/floor_decals.png");
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_bank_decal.gdshader") };
        mat.SetShaderParameter("atlas", tex);
        mat.SetShaderParameter("field", DungeonFloor.Field(z));
        mat.SetShaderParameter("half_size", z.Half);
        mat.SetShaderParameter("step", z.Step);
        mat.SetShaderParameter("res", (float)z.Res);
        var shade = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_bank_shadow.gdshader") };
        shade.SetShaderParameter("atlas", tex);
        mesh.SurfaceSetMaterial(0, mat);
        mesh.SurfaceSetMaterial(1, shade);
        c.Root.AddChild(new MeshInstance3D { Name = "FloorDecals", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        c.Count["decal floor pit"] = nPit; c.Count["decal floor frame"] = nFrame; c.Count["decal floor root"] = nRoot;
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
