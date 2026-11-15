using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's painted root clusters (art/dungeon/den/bank_decals.png, tools/look/den_roots.py): "wall" decals at the walls'
/// feet, their top edge up the bank where the roots come from; "rim" decals round every pit, their bottom edge just over
/// the lip so the drops hang into the throat. Placed by rule, deterministic by position; draped (wall: over the higher of
/// floor and bank). Two surfaces of one mesh: the roots (scissor) and the soft contact shadow (multiplied over the ground).
/// </summary>
public static partial class DungeonDress
{
    sealed record BankDecal(bool Rim, Rect2 Uv, Vector2 Metres);

    static void DenBankDecals(Ctx c)
    {
        var z = c.Z;
        Decals();  // (decalLight)
        using var f = FileAccess.Open("res://art/dungeon/den/bank_decals.json", FileAccess.ModeFlags.Read);
        var doc = JsonDocument.Parse(f.GetAsText());
        var size = doc.RootElement.GetProperty("size");
        float AW = size[0].GetSingle(), AH = size[1].GetSingle();
        var l = doc.RootElement.GetProperty("light");
        float lx = l[0].GetSingle(), ly = -l[1].GetSingle();  // (the painted light in the image's own axes: right, up)
        var walls = new List<BankDecal>();
        var rims = new List<BankDecal>();
        foreach (var d in doc.RootElement.GetProperty("decals").EnumerateArray())
        {
            var r = d.GetProperty("rect"); var m = d.GetProperty("metres");
            bool rim = d.GetProperty("kind").GetString() == "rim";
            (rim ? rims : walls).Add(new BankDecal(rim, new Rect2(r[0].GetSingle() / AW, r[1].GetSingle() / AH, r[2].GetSingle() / AW, r[3].GetSingle() / AH), new Vector2(m[0].GetSingle(), m[1].GetSingle())));
        }
        var b = new DecalBuf();
        int nWall = 0, nRim = 0;
        float cos70 = Mathf.Cos(Mathf.DegToRad(70f));

        // True when the painted light (lx along the image's right, ly along its top) lies within 70 deg of the rig's.
        bool LightOk(Vector2 top, bool mirror)
        {
            var right = new Vector2(-top.Y, top.X) * (mirror ? -1f : 1f);
            return (right * lx + top * ly).Normalized().Dot(decalLight) >= cos70;
        }

        // ---- wall decals: along the walls' feet ----
        {
            const float scan = 0.5f;
            int n = (int)(z.Size / scan);
            var taken = new List<(Vector2 p, float gap)>();
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    float x = -z.Half + (i + 0.5f) * scan, zz = -z.Half + (j + 0.5f) * scan;
                    float w = Wall(c, x, zz);
                    if (Mathf.Abs(w - 0.3f) > 0.12f || Hole(c, x, zz) < 1.2f) continue;
                    var p = new Vector2(x, zz);
                    float gap = 2.6f + 1.0f * Hash(i, j, 931);
                    bool near = false;
                    foreach (var t in taken) { float g2 = Mathf.Max(gap, t.gap); if (t.p.DistanceSquaredTo(p) < g2 * g2) { near = true; break; } }
                    if (near) continue;
                    taken.Add((p, gap));  // (a skipped spot still holds its room: the wall is not every spot)
                    if (Hash(i, j, 932) < 0.25f) continue;
                    float gx = Wall(c, x + 0.4f, zz) - Wall(c, x - 0.4f, zz), gz = Wall(c, x, zz + 0.4f) - Wall(c, x, zz - 0.4f);
                    var g = new Vector2(gx, gz);
                    if (g.LengthSquared() < 1e-8f) continue;
                    var top = -g.Normalized();  // (toward the wall: the roots' side)
                    bool mirror = false;
                    if (!LightOk(top, false)) { if (!LightOk(top, true)) continue; mirror = true; }
                    var d = walls[(int)(Hash(i, j, 933) * walls.Count) % walls.Count];
                    float sc = 0.9f + 0.25f * Hash(i, j, 934);
                    float up = 0.6f + 0.3f * Hash(i, j, 935);  // (the top edge's metres up the bank, outside the walkable edge)
                    var anchor = p + top * (w + up);
                    AddBank(c, b, d, anchor, top, sc, mirror, true);
                    nWall++;
                }
        }

        // ---- rim decals: round the pits ----
        if (z.HoleField != null)
        {
            const float scan = 0.25f;
            int n = (int)(z.Size / scan);
            var hv = new float[n * n];
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++) hv[j * n + i] = Hole(c, -z.Half + (i + 0.5f) * scan, -z.Half + (j + 0.5f) * scan);
            var id = new int[n * n];
            var q = new Queue<int>();
            int pits = 0;
            var area = new List<int>();
            for (int k = 0; k < hv.Length; k++)
            {
                if (hv[k] >= -0.5f || id[k] != 0) continue;
                pits++; int cnt = 0;
                id[k] = pits; q.Enqueue(k);
                while (q.Count > 0)
                {
                    int cur = q.Dequeue(); cnt++;
                    int ci = cur % n, cj = cur / n;
                    for (int dd = 0; dd < 4; dd++)
                    {
                        int ni = ci + (dd == 0 ? 1 : dd == 1 ? -1 : 0), nj = cj + (dd == 2 ? 1 : dd == 3 ? -1 : 0);
                        if (ni < 0 || nj < 0 || ni >= n || nj >= n) continue;
                        int nk = nj * n + ni;
                        if (id[nk] != 0 || hv[nk] >= -0.5f) continue;
                        id[nk] = pits; q.Enqueue(nk);
                    }
                }
                area.Add(cnt);
            }
            // grow each pit's label out to its rim (Hole < 0.1), multi-source so a cell takes its nearest pit's
            for (int k = 0; k < hv.Length; k++) if (id[k] != 0) q.Enqueue(k);
            while (q.Count > 0)
            {
                int cur = q.Dequeue();
                int ci = cur % n, cj = cur / n;
                for (int dd = 0; dd < 4; dd++)
                {
                    int ni = ci + (dd == 0 ? 1 : dd == 1 ? -1 : 0), nj = cj + (dd == 2 ? 1 : dd == 3 ? -1 : 0);
                    if (ni < 0 || nj < 0 || ni >= n || nj >= n) continue;
                    int nk = nj * n + ni;
                    if (id[nk] != 0 || hv[nk] >= 0.1f) continue;
                    id[nk] = id[cur]; q.Enqueue(nk);
                }
            }
            for (int pid = 1; pid <= pits; pid++)
            {
                if (area[pid - 1] < 32) continue;  // (under 2 m2: a dimple, not a pit)
                var taken = new List<(Vector2 p, float gap)>();
                for (int j = 1; j < n - 1; j++)
                    for (int i = 1; i < n - 1; i++)
                    {
                        int k = j * n + i;
                        if (id[k] != pid || Mathf.Abs(hv[k]) > 0.08f) continue;
                        var p = new Vector2(-z.Half + (i + 0.5f) * scan, -z.Half + (j + 0.5f) * scan);
                        float gap = 2.2f + 0.8f * Hash(i, j, 941);
                        bool near = false;
                        foreach (var t in taken) if (t.p.DistanceSquaredTo(p) < gap * gap) { near = true; break; }
                        if (near) continue;
                        taken.Add((p, gap));
                        var g = new Vector2(hv[k + 1] - hv[k - 1], hv[k + n] - hv[k - n]);
                        if (g.LengthSquared() < 1e-8f) continue;
                        var top = g.Normalized();  // (away from the pit)
                        bool mirror = false;
                        if (!LightOk(top, false)) { if (!LightOk(top, true)) continue; mirror = true; }
                        // the bottom edge where Hole = -0.35: walk in from the rim
                        var a = p;
                        for (int st = 0; st < 24 && Hole(c, a.X, a.Y) > -0.35f; st++) a -= top * 0.05f;
                        var d = rims[(int)(Hash(i, j, 942) * rims.Count) % rims.Count];
                        AddBank(c, b, d, a, top, 0.9f + 0.25f * Hash(i, j, 943), mirror, false);
                        nRim++;
                    }
            }
        }

        GD.Print($"DenBankDecals: {nWall} wall, {nRim} rim, {b.I.Count / 3} tris");
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
        var tex = GD.Load<Texture2D>("res://art/dungeon/den/bank_decals.png");
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
        c.Root.AddChild(new MeshInstance3D { Name = "BankDecals", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        c.Count["decal bank wall"] = nWall; c.Count["decal bank rim"] = nRim;
    }

    /// <summary>One bank decal: anchor is the middle of its top edge (wall) or bottom edge (rim); top is the image's top
    /// edge's direction in the world. Wall: draped on the higher of floor and bank; rim: on the floor.</summary>
    static void AddBank(Ctx c, DecalBuf b, BankDecal d, Vector2 anchor, Vector2 top, float scale, bool mirror, bool wall)
    {
        var right = new Vector2(-top.Y, top.X);
        float W = d.Metres.X * scale, Hh = d.Metres.Y * scale;
        int nx = Mathf.Max(2, Mathf.CeilToInt(W / 0.4f) + 1), ny = Mathf.Max(2, Mathf.CeilToInt(Hh / 0.3f) + 1);
        int base0 = b.V.Count;
        for (int q = 0; q < ny; q++)
            for (int p = 0; p < nx; p++)
            {
                float s = (float)p / (nx - 1), t = (float)q / (ny - 1);  // (t 0 = the image's top)
                var w = anchor + right * ((s - 0.5f) * W) + top * (wall ? -t * Hh : (1f - t) * Hh);
                float y = H(c, w.X, w.Y);
                if (wall) y = Mathf.Max(y, DungeonWalls.BankY(c.Z, w.X, w.Y));
                b.V.Add(new Vector3(w.X, y + 0.03f, w.Y));
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
