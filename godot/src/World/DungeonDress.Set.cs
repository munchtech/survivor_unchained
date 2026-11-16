using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The den's painted set (den round 10, 15 Nov): paintings by an image model (tools/look/den_set.py: art/dungeon/den/set/)
/// laid by rule along the walkable edge and cast along the fixed play camera's view onto their proxies (the bank's surface
/// and the floor for the banks; a half-ellipsoid on the floor for a boulder), drawn by shaders/den_set.gdshader as the
/// painting times the room's light. The camera never turns in a dungeon, so a painting laid in its plane and cast along its
/// view shows exactly as painted, and every pixel sits at the depth of the ground it shows (she stands in front of the far
/// bank, behind the near bank's crest, on the roots spilled over the floor; nothing collides).
/// The rule: the room's edge by rays from its middle; each edge station classed by which way its bank faces (far: the bank
/// north of the floor, its face to the camera, B1/B1b; near: south, seen from above and behind, B2/B2b; left and right
/// walls, B3/B3R), runs of a class laid with modules end to end (2 m overlaps; a module over its neighbour shows only its
/// brightest masses at first, roots crossing roots, never a seam), the module's foot following the edge.
/// --den-set: 0 off (round 9 unchanged, the default), 1 the entry room only (the prototype gate), 2 every room.
/// </summary>
public static partial class DungeonDress
{
    public static readonly int SetMode = (int)SurvivorUnchained.Args.Num("den-set", 0f);
    static readonly float SetScale = SurvivorUnchained.Args.Num("den-set-scale", 1f);
    static readonly float SetGain = SurvivorUnchained.Args.Num("den-set-gain", 1f);
    static readonly float SetObjGain = SurvivorUnchained.Args.Num("den-set-obj-gain", 1f);
    static readonly float SetSat = SurvivorUnchained.Args.Num("den-set-sat", 1f);
    static readonly float SetBoulderScale = SurvivorUnchained.Args.Num("den-set-boulder", 1f);
    const string SetDir = "res://art/dungeon/den/set/";
    // the play camera's basis in a dungeon (it never turns: it looks north, pitch 56)
    static readonly Vector3 CamUp = new(0f, 0.55919f, -0.82904f), CamView = new(0f, -0.82904f, -0.55919f);

    sealed record SetBank(string Name, string Kind, Vector2 Metres, float FootV, float FootU);
    sealed record SetPiece(string Sheet, Rect2 Uv, Vector2 Metres, float FootV);
    sealed class SetBuf
    {
        public readonly List<Vector3> V = new(), N = new();
        public readonly List<Vector2> U = new();
        public readonly List<Color> C = new();
        public readonly List<int> I = new();
    }

    static List<SetBank>? setBanks;
    static Dictionary<string, List<SetPiece>>? setSheets;
    static (float X, float Z, float R, string Kind) setRoom;
    static Shader? setShader;
    static readonly Dictionary<long, float> surfCache = new();

    static bool LoadSet()
    {
        if (setBanks != null) return setBanks.Count > 0;
        setBanks = new(); setSheets = new();
        if (!FileAccess.FileExists(SetDir + "set.json")) return false;
        using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(SetDir + "set.json"));
        var r = doc.RootElement;
        foreach (var b in r.GetProperty("banks").EnumerateArray())
        {
            var m = b.GetProperty("metres");
            setBanks.Add(new SetBank(b.GetProperty("name").GetString()!, b.GetProperty("kind").GetString()!, new Vector2(m[0].GetSingle(), m[1].GetSingle()),
                b.TryGetProperty("foot_v", out var fv) ? fv.GetSingle() : 1f, b.TryGetProperty("foot_u", out var fu) ? fu.GetSingle() : 0f));
        }
        foreach (var s in r.GetProperty("sheets").EnumerateArray())
        {
            string name = s.GetProperty("name").GetString()!;
            var px = s.GetProperty("px");
            float aw = px[0].GetSingle(), ah = px[1].GetSingle();
            var list = new List<SetPiece>();
            foreach (var p in s.GetProperty("pieces").EnumerateArray())
            {
                var rc = p.GetProperty("rect"); var m = p.GetProperty("metres");
                list.Add(new SetPiece(name, new Rect2(rc[0].GetSingle() / aw, rc[1].GetSingle() / ah, rc[2].GetSingle() / aw, rc[3].GetSingle() / ah),
                    new Vector2(m[0].GetSingle(), m[1].GetSingle()), p.GetProperty("foot_v").GetSingle()));
            }
            setSheets[name] = list;
        }
        setShader = GD.Load<Shader>("res://shaders/den_set.gdshader");
        return setBanks.Count > 0;
    }

    /// <summary>True where the painted set dresses the den (mode 1: the entry room and its banks; mode 2: everywhere).</summary>
    static bool SetIn(float x, float zz) =>
        SetMode >= 2 || (SetMode == 1 && new Vector2(x - setRoom.X, zz - setRoom.Z).Length() < setRoom.R + 9f);

    static void PickSetRoom(ZoneData z)
    {
        setRoom = z.Rooms[0];
        foreach (var r in z.Rooms) if (r.Kind == "Start") { setRoom = r; break; }
        surfCache.Clear();
    }

    static float SetSm(float a, float b, float x) { float t = Mathf.Clamp((x - a) / (b - a), 0f, 1f); return t * t * (3 - 2 * t); }

    // The banks' proxy: the floor, and over the bank its surface (DungeonWalls' profile) raised 0.3 m clear of the mesh's
    // lumps, cached on a 0.25 m lattice and read bilinear.
    static float SurfBank(Ctx c, float x, float zz)
    {
        const float q = 0.25f;
        float fx = x / q, fz = zz / q;
        int ix = Mathf.FloorToInt(fx), iz = Mathf.FloorToInt(fz);
        float tx = fx - ix, tz = fz - iz;
        float L(int i, int j)
        {
            long k = ((long)i << 32) ^ (uint)j;
            if (surfCache.TryGetValue(k, out float v)) return v;
            float px = i * q, pz = j * q;
            float s = -Wall(c, px, pz);
            v = Mathf.Max(H(c, px, pz), DungeonWalls.BankY(c.Z, px, pz) + 0.3f * SetSm(0.05f, 0.6f, s));
            surfCache[k] = v;
            return v;
        }
        return Mathf.Lerp(Mathf.Lerp(L(ix, iz), L(ix + 1, iz), tx), Mathf.Lerp(L(ix, iz + 1), L(ix + 1, iz + 1), tx), tz);
    }

    /// <summary>The point where the view ray through p (any point on it) meets the surface: marched down from the height top.</summary>
    static Vector3 SetCast(Vector3 p, System.Func<float, float, float> surf, float top)
    {
        var o = p + CamView * ((top - p.Y) / CamView.Y);
        const float stepT = 0.2f;
        for (int i = 0; i < 600; i++)
        {
            var q = o + CamView * (i * stepT);
            if (q.Y > surf(q.X, q.Z)) continue;
            float lo = Mathf.Max(0f, (i - 1) * stepT), hi = i * stepT;
            for (int b = 0; b < 8; b++)
            {
                float m = 0.5f * (lo + hi);
                var qm = o + CamView * m;
                if (qm.Y <= surf(qm.X, qm.Z)) hi = m; else lo = m;
            }
            return o + CamView * hi;
        }
        return o + CamView * (600 * stepT);
    }

    static int SetClassOf(float th, int cls) => cls switch
    {
        0 => Mathf.Abs(th) <= 50f ? 1 : 0,               // far: the bank north of the floor, its face to the camera
        1 => th >= 40f && th <= 140f ? 1 : 0,            // right wall (east of the floor)
        2 => Mathf.Abs(th) >= 130f ? 1 : 0,              // near: south, seen from above and behind
        _ => th <= -40f && th >= -140f ? 1 : 0,          // left wall (west)
    };

    static void DenSet(Ctx c)
    {
        if (!LoadSet()) { GD.Print("DenSet: no set.json"); return; }
        var bufs = new Dictionary<string, SetBuf>();
        var rooms = new List<(float X, float Z, float R, string Kind)>();
        if (SetMode >= 2) { foreach (var r in c.Z.Rooms) if (r.Kind != "Bend") rooms.Add(r); }
        else rooms.Add(setRoom);
        int modules = 0, runs = 0;
        int ri = 0;
        foreach (var r in rooms)
        {
            ri++;
            // the room's edge: a ray from its middle every half degree to the first wall (pits are not walls)
            const int n = 720;
            var P = new Vector3[n]; var th = new float[n]; var open = new bool[n];
            for (int k = 0; k < n; k++)
            {
                float a = k * Mathf.Tau / n;
                var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                float t = 0.5f, lim = r.R + 8f;
                while (t < lim && Wall(c, r.X + d.X * t, r.Z + d.Y * t) >= 0f) t += 0.1f;
                if (t >= lim) { open[k] = true; continue; }
                float lo = t - 0.1f, hi = t;
                for (int b = 0; b < 10; b++) { float m = 0.5f * (lo + hi); if (Wall(c, r.X + d.X * m, r.Z + d.Y * m) < 0f) hi = m; else lo = m; }
                float x = r.X + d.X * lo, zz = r.Z + d.Y * lo;
                P[k] = new Vector3(x, H(c, x, zz), zz);
            }
            // outward normals smoothed over +-2 m of edge, then the class angle (0 north, 90 east, 180 south)
            for (int k = 0; k < n; k++)
            {
                if (open[k]) continue;
                var g = Vector2.Zero;
                for (int j = -6; j <= 6; j++)
                {
                    int kk = (k + j + n) % n;
                    if (open[kk]) continue;
                    var p = P[kk];
                    float gx = Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), gz = Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f);
                    g += new Vector2(gx, gz);
                }
                var o = -g.Normalized();
                th[k] = Mathf.RadToDeg(Mathf.Atan2(o.X, -o.Y));
            }
            float top = H(c, r.X, r.Z) + 14f;
            for (int cls = 0; cls < 4; cls++)
            {
                // runs of the class round the ring (cut at openings and jumps of the edge)
                int start = -1;
                for (int k = 0; k < n; k++) if (open[k] || SetClassOf(th[k], cls) == 0) { start = k; break; }
                if (start < 0) start = 0;
                var run = new List<Vector3>();
                for (int s = 1; s <= n; s++)
                {
                    int k = (start + s) % n;
                    bool inRun = !open[k] && SetClassOf(th[k], cls) == 1 && (run.Count == 0 || run[^1].DistanceTo(P[k]) < 2.5f);
                    if (inRun) run.Add(P[k]);
                    if ((!inRun || s == n) && run.Count > 0)
                    {
                        if (run.Count >= 6) { modules += SetRun(c, bufs, run, cls, ri * 16 + cls * 4 + runs, top); runs++; }
                        run.Clear();
                        if (!open[k] && SetClassOf(th[k], cls) == 1) run.Add(P[k]);
                    }
                }
            }
        }
        int tris = 0;
        foreach (var (name, b) in bufs)
        {
            if (b.I.Count == 0) continue;
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Mesh.ArrayType.Max);
            arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
            arr[(int)Mesh.ArrayType.Normal] = b.N.ToArray();
            arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
            arr[(int)Mesh.ArrayType.Color] = b.C.ToArray();
            arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
            var mat = new ShaderMaterial { Shader = setShader };
            mat.SetShaderParameter("paint_tex", GD.Load<Texture2D>(SetDir + name + ".png"));
            mat.SetShaderParameter("gain", SetGain);
            mat.SetShaderParameter("sat", SetSat);
            c.Root.AddChild(new MeshInstance3D { Name = "Set_" + name, Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            tris += b.I.Count / 3;
        }
        c.Count["set modules"] = modules; c.Count["set tris"] = tris;
        GD.Print($"DenSet: mode {SetMode}, {rooms.Count} rooms, {runs} runs, {modules} modules, {tris} tris, {bufs.Count} draws");
    }

    // One run of a class: modules end to end along it, each laid in the camera's plane with its foot on the edge and cast
    // onto the bank and floor. Returns the modules laid.
    static int SetRun(Ctx c, Dictionary<string, SetBuf> bufs, List<Vector3> run, int cls, int seed, float top)
    {
        bool alongX = cls == 0 || cls == 2;
        string kind = cls switch { 0 => "far", 1 => "right", 2 => "near", _ => "left" };
        var choices = setBanks!.FindAll(b => b.Kind == kind);
        if (choices.Count == 0) return 0;
        // the foot as a function of the along coordinate (X for far and near, the plane's Y for the walls)
        var pts = new List<(float a, float f)>();
        foreach (var p in run)
        {
            float X = p.X, Y = p.Dot(CamUp);
            pts.Add(alongX ? (X, Y) : (Y, X));
        }
        pts.Sort((u, v) => u.a.CompareTo(v.a));
        float FootAt(float a)
        {
            if (a <= pts[0].a) return pts[0].f;
            if (a >= pts[^1].a) return pts[^1].f;
            int lo = 0, hi = pts.Count - 1;
            while (hi - lo > 1) { int m = (lo + hi) / 2; if (pts[m].a <= a) lo = m; else hi = m; }
            float t = (a - pts[lo].a) / Mathf.Max(pts[hi].a - pts[lo].a, 1e-4f);
            return Mathf.Lerp(pts[lo].f, pts[hi].f, t);
        }
        float a0 = pts[0].a, a1 = pts[^1].a, ext = 1.0f, ov = 2.0f;
        int k = 0, laid = 0;
        var first = choices[(int)(Hash(seed, 61, 0) * choices.Count) % choices.Count];
        float L0 = (alongX ? first.Metres.X : first.Metres.Y) * SetScale;
        float span = a1 - a0 + 2 * ext;
        float s = a0 - ext - Hash(seed, 62, 0) * (L0 > span ? L0 - span : 0.35f * L0);
        while (s < a1 + ext && k < 40)
        {
            var b = k == 0 ? first : choices[(int)(Hash(seed, 63, k) * choices.Count) % choices.Count];
            float L = (alongX ? b.Metres.X : b.Metres.Y) * SetScale;
            float from = Mathf.Max(s, a0 - ext), to = Mathf.Min(s + L, a1 + ext);
            if (to - from > 0.5f)
            {
                if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                SetModule(c, buf, b, alongX, s, L, from, to, FootAt, true, s + L > a1 + ext, 0.05f + 0.03f * (k % 2), top);
                laid++;
            }
            s += L - ov;
            k++;
        }
        return laid;
    }

    static void SetModule(Ctx c, SetBuf buf, SetBank b, bool alongX, float s, float L, float from, float to,
        System.Func<float, float> footAt, bool fadeIn, bool fadeOut, float lift, float top)
    {
        float Wm = b.Metres.X * SetScale, Hm = b.Metres.Y * SetScale, ov = 2.0f;
        const float cell = 0.35f;
        int na = Mathf.Max(2, Mathf.CeilToInt((to - from) / cell) + 1);
        int nc = Mathf.Max(2, Mathf.CeilToInt((alongX ? Hm : Wm) / cell) + 1);
        int base0 = buf.V.Count;
        var keepv = new bool[na * nc];
        System.Func<float, float, float> surf = (x, zz) => SurfBank(c, x, zz);
        for (int i = 0; i < na; i++)
        {
            float a = Mathf.Lerp(from, to, (float)i / (na - 1));
            float foot = footAt(a);
            float fa = 1f;
            if (fadeIn) fa = Mathf.Min(fa, (a - from) / ov);
            if (fadeOut) fa = Mathf.Min(fa, (to - a) / ov);
            for (int j = 0; j < nc; j++)
            {
                float t = (float)j / (nc - 1);
                float u, v, X, Y;
                bool bankSide;
                float fe;
                if (alongX)
                {
                    u = (a - s) / L; v = t;
                    X = a; Y = foot + (b.FootV - v) * Hm;
                    bankSide = b.Kind == "far" ? v < b.FootV - 0.02f : v > b.FootV + 0.02f;
                    fe = b.Kind == "far" ? v / 0.08f : (1f - v) / 0.08f;   // (the image's straight cut deep in the bank)
                }
                else
                {
                    v = 1f - (a - s) / L; u = t;
                    Y = a; X = foot + (u - b.FootU) * Wm;
                    bankSide = b.Kind == "left" ? u < b.FootU - 0.02f : u > b.FootU + 0.02f;
                    fe = b.Kind == "left" ? u / 0.1f : (1f - u) / 0.1f;
                }
                var pc = new Vector3(X, 0f, 0f) + CamUp * Y;
                var q = SetCast(pc, surf, top);
                bool keep = !(bankSide && Wall(c, q.X, q.Z) > 0.3f);
                keepv[i * nc + j] = keep;
                buf.V.Add(q - CamView * lift);
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(Mathf.Clamp(u, 0f, 1f), Mathf.Clamp(v, 0f, 1f)));
                buf.C.Add(new Color(Mathf.Clamp(Mathf.Min(fa, fe), 0f, 1f), keep ? 1f : 0f, 0f, 1f));
            }
        }
        for (int i = 0; i < na - 1; i++)
            for (int j = 0; j < nc - 1; j++)
            {
                int k0 = i * nc + j, k1 = k0 + 1, k2 = k0 + nc, k3 = k2 + 1;
                if (!keepv[k0] && !keepv[k1] && !keepv[k2] && !keepv[k3]) continue;
                buf.I.Add(base0 + k0); buf.I.Add(base0 + k2); buf.I.Add(base0 + k1);
                buf.I.Add(base0 + k1); buf.I.Add(base0 + k2); buf.I.Add(base0 + k3);
            }
    }

    /// <summary>A painted boulder (O1) on its half-ellipsoid proxy, in the round 6 boulders' place: the painting cast onto
    /// the stone's own form, a shadow-only hull and a contact blob. Returns its footprint's half width (m).</summary>
    static float PlaceSetBoulder(Ctx c, int pick, float x, float zz, float scale, bool big)
    {
        if (!LoadSet() || !setSheets!.TryGetValue("O1", out var all) || all.Count == 0) return 0f;
        var sorted = new List<SetPiece>(all);
        sorted.Sort((p, q) => q.Metres.X.CompareTo(p.Metres.X));
        var pool = sorted.GetRange(big ? 0 : sorted.Count / 2, Mathf.Max(1, sorted.Count / 2));
        var pc = pool[pick % pool.Count];
        float k = scale * SetBoulderScale * (big ? 1f : 0.8f);
        float W = pc.Metres.X * k, Hr = pc.Metres.Y * k;
        float rx = 0.46f * W, ry = 0.62f * rx;
        float aa = CamUp.Y * ry, hm = 0.94f * Hr;
        float bb = Mathf.Max((hm * hm - aa * aa) / (2f * hm), 0.25f * rx);
        float rz = bb / -CamUp.Z;
        float y0 = H(c, x, zz);
        var n = new Node3D { Name = "SetBoulder" };
        float yFront = new Vector3(x, y0, zz + rz).Dot(CamUp);
        System.Func<float, float, float> surf = (px, pz) =>
        {
            float ex = (px - x) / rx, ez = (pz - zz) / rz;
            float e = 1f - ex * ex - ez * ez;
            float s = e > 0f ? y0 + ry * Mathf.Sqrt(e) : -99f;
            return Mathf.Max(s, SurfBank(c, px, pz));
        };
        var buf = new SetBuf();
        const int nu = 16, nv = 14;
        float top = y0 + ry + 10f;
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float X = x + (u - 0.5f) * W, Y = yFront + (pc.FootV - v) * Hr;
                var q = SetCast(new Vector3(X, 0f, 0f) + CamUp * Y, surf, top);
                buf.V.Add(q - CamView * 0.04f);
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(pc.Uv.Position.X + u * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                buf.C.Add(new Color(1f, 1f, 0f, 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                buf.I.Add(k0); buf.I.Add(k2); buf.I.Add(k1); buf.I.Add(k1); buf.I.Add(k2); buf.I.Add(k3);
            }
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = buf.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = buf.N.ToArray();
        arr[(int)Mesh.ArrayType.TexUV] = buf.U.ToArray();
        arr[(int)Mesh.ArrayType.Color] = buf.C.ToArray();
        arr[(int)Mesh.ArrayType.Index] = buf.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        var mat = new ShaderMaterial { Shader = setShader };
        mat.SetShaderParameter("paint_tex", GD.Load<Texture2D>(SetDir + "O1.png"));
        mat.SetShaderParameter("gain", SetGain * SetObjGain);
        mat.SetShaderParameter("sat", SetSat);
        n.AddChild(new MeshInstance3D { Name = "Painting", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        n.AddChild(new MeshInstance3D
        {
            Name = "Shadow", Mesh = new SphereMesh { Radius = 1f, Height = 2f, RadialSegments = 16, Rings = 8 },
            Transform = new Transform3D(Basis.FromScale(new Vector3(rx, ry, rz)), new Vector3(x, y0, zz)),
            CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly,
        });
        blob ??= new GradientTexture2D
        {
            Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
            Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 1f }, Colors = new[] { new Color(0, 0, 0, 1), new Color(0, 0, 0, 0.7f), new Color(0, 0, 0, 0) } },
        };
        n.AddChild(new Godot.Decal
        {
            Name = "Contact", TextureAlbedo = blob, Modulate = new Color(1, 1, 1, 0.6f), AlbedoMix = 1f,
            Size = new Vector3(2.5f * rx, 1.2f, 2.5f * rz), Position = new Vector3(x, y0, zz),
        });
        c.Root.AddChild(n);
        c.Tick("set boulders");
        c.Boulders.Add((new Vector2(x, zz), rx));
        return rx;
    }
}
