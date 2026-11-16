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
/// --den-set: 0 off (round 9), 1 the entry room only (the prototype gate), 2 every room (r10c: the default).
/// </summary>
public static partial class DungeonDress
{
    public static readonly int SetMode = (int)SurvivorUnchained.Args.Num("den-set", 2f);
    static readonly float SetScale = SurvivorUnchained.Args.Num("den-set-scale", 1f);
    static readonly float SetGain = SurvivorUnchained.Args.Num("den-set-gain", 0.85f);   // (r11 1.1 -> 1.0: lit tone 156 against 134)   // (r10d 1.25 -> 1.1: the lit root tops measured (166,122,100) against (134,95,73))
    static readonly float SetObjGain = SurvivorUnchained.Args.Num("den-set-obj-gain", 1f);
    static readonly float SetSat = SurvivorUnchained.Args.Num("den-set-sat", 0.5f);   // (r11 0.7 -> 0.5 with shade-hi 0.15: satShade .34 -> .18, cool 15 -> 25 %, as den_room.png)
    static readonly float SetBoulderScale = SurvivorUnchained.Args.Num("den-set-boulder", 1f);
    static readonly float SetCool = SurvivorUnchained.Args.Num("den-set-cool", 1f);   // (r10b) the paintings' shade to cool grey (den_set.gdshader shade_k)

    static Vector3 setBossC;   // (r12) the lair's centre x, z and radius for the set's gloom (0: none), taken where the set is built
    internal static readonly float SetBossGloom = SurvivorUnchained.Args.Num("den-boss-gloom", 1.2f);

    static ShaderMaterial SetMat(string sheet, float gain)
    {
        // (r10d) the hole paintings (H1, H2) lie on the floor blended (their surround fades into it); the rest cut at alpha 0.5
        var mat = new ShaderMaterial { Shader = sheet[0] == 'H' ? setSoftShader : setShader };
        mat.SetShaderParameter("paint_tex", GD.Load<Texture2D>(SetDir + sheet + ".png"));
        mat.SetShaderParameter("gain", gain);
        mat.SetShaderParameter("sat", SetSat);
        mat.SetShaderParameter("shade_k", SetCool);
        mat.SetShaderParameter("dark_floor", SetDark);
        mat.SetShaderParameter("amb_floor", SetAmb);
        // (r11) the roots and shade read pink-mauve: the paintings' mids warmed (less blue), the shade's cool narrowed to the
        // deepest darks and turned blue-teal (den_room.png: warm brown in the light, cool only down in the hollows)
        mat.SetShaderParameter("tint", V3("den-set-tint", new Vector3(1f, 0.98f, 0.81f)));
        mat.SetShaderParameter("shade_tint", V3("den-set-shade-tint", new Vector3(0.84f, 0.93f, 1.0f)));
        mat.SetShaderParameter("shade_hi", SurvivorUnchained.Args.Num("den-set-shade-hi", 0.15f));
        if (sheet == "O5")
        {
            // (r12 judge: the seed-23 room's blood read magenta) the set's half saturation and its grey-violet shade turned the
            // painted blood pink-mauve: blood keeps its own red, a touch darker and browner
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-blood-sat", 0.7f));
            mat.SetShaderParameter("tint", V3("den-blood-tint", new Vector3(0.66f, 0.6f, 0.5f)));
            mat.SetShaderParameter("shade_k", 0f);
        }
        mat.SetShaderParameter("boss_c", setBossC);   // (r12) the lair's gloom, as the floor's
        mat.SetShaderParameter("boss_gloom", SetBossGloom);
        mat.SetShaderParameter("mush_glow", SurvivorUnchained.Args.Num("den-mush-glow", 0.35f));   // (r12 judge) teal on the ground under the painted caps
        if (sheet[0] == 'H')
        {
            mat.SetShaderParameter("pit_glow", SurvivorUnchained.Args.Num("den-pit-glow", 0.8f));   // (r12) den_boss.png's green pits
            mat.SetShaderParameter("rim_in", SurvivorUnchained.Args.Num("den-hole-rim-in", 1.15f));
            mat.SetShaderParameter("rim_out", SurvivorUnchained.Args.Num("den-hole-rim-out", 1.45f));
        }
        return mat;
    }
    internal static Vector3 V3(string flag, Vector3 dflt)
    {
        if (SurvivorUnchained.Args.Get(flag) is string t && t.Split(',') is { Length: 3 } p)
        {
            var ci = System.Globalization.CultureInfo.InvariantCulture;
            return new Vector3(float.Parse(p[0], ci), float.Parse(p[1], ci), float.Parse(p[2], ci));
        }
        return dflt;
    }
    const string SetDir = "res://art/dungeon/den/set/";
    // the play camera's basis in a dungeon (it never turns: it looks north at the map's pitch, MapRun.CamPitch 62; r10c: it
    // was cast at 56, the road's, so every painting drew 6% tall on the floor and its raised parts sank)
    static readonly float CamPitchR = Mathf.DegToRad((float)SurvivorUnchained.Play.Zones.MapRun.CamPitch);
    static readonly Vector3 CamUp = new(0f, Mathf.Cos(CamPitchR), -Mathf.Sin(CamPitchR)), CamView = new(0f, -Mathf.Sin(CamPitchR), -Mathf.Cos(CamPitchR));
    static readonly int SetRows = (int)SurvivorUnchained.Args.Num("den-set-rows", 2f);       // (r10c) side walls: rows of modules deeper in the bank
    static readonly float SetCorners = SurvivorUnchained.Args.Num("den-set-corners", 0f);    // (r10c) B4/B4R_2 where a far run meets a wall's (r11 1 -> 0: the corner's arm drew a straight seam and a dark band across the room's top, c_p13)
    static readonly float SetSpills = SurvivorUnchained.Args.Num("den-set-spills", 1f);      // (r10c) B6 spills on the floor at the banks' feet and pits
    static readonly float SetDark = SurvivorUnchained.Args.Num("den-set-dark", 0.02f); // (r11 0.008 -> 0.02)      // (r10c) the paintings' darks lit at least this (cool)
    static readonly float SetAmb = SurvivorUnchained.Args.Num("den-set-amb", 0.25f); // (r11 0.2 -> 0.25)        // (r10c) and at least this share of their painted value
    // (r10c) the objects in one mesh per sheet (they were a node each: ~137 draws) and the boulders' shadow hulls in one
    static readonly Dictionary<string, SetBuf> objBufs = new();
    static readonly List<Transform3D> hulls = new();

    sealed record SetBank(string Name, string Kind, Vector2 Metres, float FootV, float FootU);
    sealed record SetPiece(string Sheet, Rect2 Uv, Vector2 Metres, float FootV, Vector4 Mouth);
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
    static Shader? setShader, setSoftShader;
    static readonly float SetHoles = SurvivorUnchained.Args.Num("den-set-holes", 1f);   // (r10d) H2 over the pits, H1 over the hollows
    static readonly float SetOpenK = SurvivorUnchained.Args.Num("den-set-open", 1f);    // (r10d) things in the rooms' open floor
    static readonly float SetDrifts = SurvivorUnchained.Args.Num("den-set-drifts", 1f);   // (r11) bone drifts (O4) at the far banks' feet: their scale (0 off)
    static readonly float SetStretch = SurvivorUnchained.Args.Num("den-set-stretch", 4f);  // (r11) a module cell cast longer than this many cells is dropped (0 keeps all)
    static readonly float SetBackRow = SurvivorUnchained.Args.Num("den-set-backrow", 2f);  // (r11) a far run's row behind: 0 none, 1 whole, 2 past the run's ends only
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
                    new Vector2(m[0].GetSingle(), m[1].GetSingle()), p.GetProperty("foot_v").GetSingle(),
                    p.TryGetProperty("mouth", out var mo) ? new Vector4(mo[0].GetSingle(), mo[1].GetSingle(), mo[2].GetSingle(), mo[3].GetSingle()) : Vector4.Zero));
            }
            setSheets[name] = list;
        }
        setShader = GD.Load<Shader>("res://shaders/den_set.gdshader");
        setSoftShader = GD.Load<Shader>("res://shaders/den_set_soft.gdshader");
        return setBanks.Count > 0;
    }

    /// <summary>True where the painted set dresses the den (mode 1: the entry room and its banks; mode 2: everywhere).</summary>
    static bool SetIn(float x, float zz) =>
        SetMode >= 2 || (SetMode == 1 && new Vector2(x - setRoom.X, zz - setRoom.Z).Length() < setRoom.R + 9f);

    /// <summary>Where the set dresses, for the mound's shader (dungeon_wall.gdshader set_area): the prototype room's x, z and
    /// radius; w the mode (0 off, 1 that room, 2 everywhere).</summary>
    public static Vector4 SetArea(ZoneData z)
    {
        if (SetMode <= 0 || z.DungeonTheme != "den" || z.Rooms.Count == 0) return Vector4.Zero;
        var r = z.Rooms[0];
        foreach (var q in z.Rooms) if (q.Kind == "Start") { r = q; break; }
        return new Vector4(r.X, r.Z, r.R, SetMode >= 2 ? 2f : 1f);
    }

    static void PickSetRoom(ZoneData z)
    {
        setRoom = z.Rooms[0];
        foreach (var r in z.Rooms) if (r.Kind == "Start") { setRoom = r; break; }
        setLayer = 0; setCov.Clear(); surfCache.Clear(); foreach (var d in smCache) d.Clear(); objBufs.Clear(); hulls.Clear();
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
        static long K(int i, int j) => ((long)i << 32) ^ (uint)j;
        float Raw(int i, int j)
        {
            long k = K(i, j);
            if (surfCache.TryGetValue(k, out float v)) return v;
            float px = i * q, pz = j * q;
            float s = -Wall(c, px, pz);
            float bank = SetProxy > 0f ? DungeonWalls.BankHoldY(c.Z, px, pz) : DungeonWalls.BankY(c.Z, px, pz);
            v = Mathf.Max(H(c, px, pz), bank + 0.3f * SetSm(0.05f, 0.6f, s));
            surfCache[k] = v;
            return v;
        }
        // (den r12) the proxy box-blurred twice over +-SetSmooth metres (separable): no crease left for a card to span
        int r = SetProxy > 0f ? Mathf.RoundToInt(SetSmooth / q) : 0;
        float Bz(int i, int j, Dictionary<long, float> cache, System.Func<int, int, float> f)
        {
            long k = K(i, j);
            if (cache.TryGetValue(k, out float v)) return v;
            float acc = 0f;
            for (int d = -r; d <= r; d++) acc += f(i, j + d);
            v = acc / (2 * r + 1); cache[k] = v; return v;
        }
        float Bx(int i, int j, Dictionary<long, float> cache, System.Func<int, int, float> f)
        {
            long k = K(i, j);
            if (cache.TryGetValue(k, out float v)) return v;
            float acc = 0f;
            for (int d = -r; d <= r; d++) acc += f(i + d, j);
            v = acc / (2 * r + 1); cache[k] = v; return v;
        }
        float L1(int i, int j) => Bx(i, j, smCache[1], (a, b) => Bz(a, b, smCache[0], Raw));
        float L(int i, int j) => r <= 0 ? Raw(i, j) : Bx(i, j, smCache[3], (a, b) => Bz(a, b, smCache[2], L1));
        return Mathf.Lerp(Mathf.Lerp(L(ix, iz), L(ix + 1, iz), tx), Mathf.Lerp(L(ix, iz + 1), L(ix + 1, iz + 1), tx), tz);
    }
    static readonly float SetLiftAdd = SurvivorUnchained.Args.Num("den-set-lift", 0f);   // (r12 diagnosis) every bank card pulled this much more toward the camera
    static readonly float SetKeepAll = SurvivorUnchained.Args.Num("den-set-keepall", 0f);   // (r12 diagnosis)
    static readonly float SetLog = SurvivorUnchained.Args.Num("den-set-log", 0f);   // (r13 diagnosis) every ring's runs printed
    static readonly string[]? SetOnly = SurvivorUnchained.Args.Get("den-set-only")?.Split(',');   // (r13 diagnosis) only these sheets drawn (B3,B3R,...)
    static int setLayer;
    static readonly float SetLairWant = SurvivorUnchained.Args.Num("den-lair-want", 70f), SetLairRing = SurvivorUnchained.Args.Num("den-lair-ring", 13f);   // (r12) the lair's open pieces and their ring (3 m + this)
    static readonly float SetEdgeWave = SurvivorUnchained.Args.Num("den-set-wave", 0f);   // (r12) metres
    static readonly float SetBends = SurvivorUnchained.Args.Num("den-set-bends", 0f);
    static readonly float SetFootFade = SurvivorUnchained.Args.Num("den-set-footfade", 1f);   // (r12) a bank card's floor-side border fades to its bright masses
    static readonly float SetRagged = SurvivorUnchained.Args.Num("den-set-ragged", 1f);   // (r14) metres a module's border cut wanders in (0: its straight rectangle)
    static readonly float SetLayerStep = SurvivorUnchained.Args.Num("den-set-layer", 0.04f);   // (r12) metres between modules' depth layers
    static readonly Dictionary<long, float>[] smCache = { new(), new(), new(), new() };
    static readonly float SetProxy = SurvivorUnchained.Args.Num("den-set-proxy", 1f);    // (r12) 0: the bank's own profile (crest and fall); 1: its rise held at the crest, smoothed
    static readonly float SetSmooth = SurvivorUnchained.Args.Num("den-set-smooth", 1.25f); // (r12) the proxy's blur half-width, metres (twice, box)

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
        if (SetMode >= 2) { foreach (var r in c.Z.Rooms) if (r.Kind != "Bend" || SetBends > 0f) rooms.Add(r); }   // (r12 --den-set-bends: the corridors' bends ring too)
        else rooms.Add(setRoom);
        int modules = 0, runs = 0, corners = 0, spills = 0;
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
            var ends = new List<(int cls, List<Vector3> pts)>();
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
                        if (SetLog > 0f) GD.Print($"DenSet run: room {ri} ({r.X:0.0},{r.Z:0.0}) cls {cls} n {run.Count} from ({run[0].X:0.0},{run[0].Z:0.0}) to ({run[^1].X:0.0},{run[^1].Z:0.0})");
                        if (run.Count >= 6) { modules += SetRun(c, bufs, run, cls, ri * 16 + cls * 4 + runs, top); runs++; ends.Add((cls, new List<Vector3>(run))); foreach (var q in run) SetCover(q); }
                        run.Clear();
                        if (!open[k] && SetClassOf(th[k], cls) == 1) run.Add(P[k]);
                    }
                }
            }
            // (r10c) the inner corners: where a far run's end meets a wall run's north end, the corner painting (B4 back-left,
            // B4R_2 back-right) with its inner point on the meeting, over both runs' ends; its arms fade to their bright roots
            if (SetCorners > 0f)
                foreach (var (fc, fp) in ends)
                {
                    if (fc != 0) continue;
                    var w = fp[0]; var e = fp[0];
                    foreach (var p in fp) { if (p.X < w.X) w = p; if (p.X > e.X) e = p; }
                    foreach (var (sc, sp) in ends)
                    {
                        if (sc != 1 && sc != 3) continue;
                        var nth = sp[0];
                        foreach (var p in sp) if (p.Z < nth.Z) nth = p;
                        var at = sc == 3 ? w : e;
                        if (new Vector2(nth.X - at.X, nth.Z - at.Z).Length() > 5f) continue;
                        string nm = sc == 3 ? "B4" : "B4R_2";
                        var b = setBanks!.Find(q => q.Name == nm);
                        if (b == null) continue;
                        if (!bufs.TryGetValue(nm, out var cb)) bufs[nm] = cb = new SetBuf();
                        SetCorner(c, cb, b, nth.X, at.Dot(CamUp), top);
                        corners++;
                    }
                }
            // (r10c) root spills lying on the floor at the far and side banks' feet, every 6-9 m, now and then skipped
            if (SetSpills > 0f)
                foreach (var (sc, sp) in ends)
                {
                    if (sc == 2) continue;
                    float acc = 0f, next = 2f + 4f * Hash(ri, sc, 811);
                    for (int i = 1; i < sp.Count; i++)
                    {
                        acc += sp[i].DistanceTo(sp[i - 1]);
                        if (acc < next) continue;
                        next = acc + 6f + 3f * Hash(ri * 31 + i, sc, 812);
                        if (Hash(ri * 31 + i, sc, 813) < 0.3f) continue;
                        var dir = new Vector2(r.X - sp[i].X, r.Z - sp[i].Z).Normalized();
                        var at = new Vector2(sp[i].X, sp[i].Z) + dir * (1.2f + 1.0f * Hash(ri * 31 + i, sc, 814));
                        if (SetPick("B6", Hash(ri * 31 + i, sc, 815)) is SetPiece pc && Wall(c, at.X, at.Y) > 0.5f)
                        { PlaceSetObj(c, "B6", pc, at.X, at.Y, 0.5f + 0.25f * Hash(ri * 31 + i, sc, 816), 0f, false, 0f); spills++; }
                    }
                }
            // (r11) bone drifts (O4) along the far banks' feet: every 5-8 m in the boss lair (den_boss.png's ribs and bone
            // drifts along its far wall), now and then in a room; only on far runs (a card's long axis runs east-west)
            if (SetDrifts > 0f && setSheets!.ContainsKey("O4"))
                foreach (var (sc, sp) in ends)
                {
                    if (sc != 0) continue;
                    bool boss = r.Kind == "Boss";
                    float acc = 0f, next = 1.5f + 3f * Hash(ri, sc, 821);
                    for (int i = 1; i < sp.Count; i++)
                    {
                        acc += sp[i].DistanceTo(sp[i - 1]);
                        if (acc < next) continue;
                        next = acc + (boss ? 5f : 12f) + 3f * Hash(ri * 37 + i, sc, 822);
                        if (!boss && Hash(ri * 37 + i, sc, 823) < 0.5f) continue;
                        var dir = new Vector2(r.X - sp[i].X, r.Z - sp[i].Z).Normalized();
                        var at = new Vector2(sp[i].X, sp[i].Z) + dir * (0.9f + 0.6f * Hash(ri * 37 + i, sc, 824));
                        if (Wall(c, at.X, at.Y) < 0.5f || Hole(c, at.X, at.Y) < 1.5f) continue;
                        if (SetPick("O4", Hash(ri * 37 + i, sc, 825)) is SetPiece pc)
                        { PlaceSetObj(c, "O4", pc, at.X, at.Y, SetDrifts * (0.8f + 0.3f * Hash(ri * 37 + i, sc, 826)), 0.1f, false, 0.3f); c.Tick("set drifts"); }
                    }
                }
        }
        if (SetLanes > 0f && SetMode >= 2) SetLaneRings(c, bufs, ref modules, ref runs, ref spills);
        setBossC = Vector3.Zero;
        foreach (var rb in c.Z.Rooms) if (rb.Kind == "Boss") setBossC = new Vector3(rb.X, rb.Z, rb.R);
        if (SetOpenK > 0f) SetOpen(c, rooms.FindAll(q => q.Kind != "Bend"));
        int tris = 0;
        foreach (var (name, b) in bufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            c.Root.AddChild(new MeshInstance3D { Name = "Set_" + name, Mesh = SetMesh(b), MaterialOverride = SetMat(name, SetGain), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            tris += b.I.Count / 3;
        }
        // (r10c) the objects (boulders, logs, bones, spills): one mesh a sheet; the boulders' shadow hulls in one
        int otris = 0;
        foreach (var (name, b) in objBufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            c.Root.AddChild(new MeshInstance3D { Name = "SetObj_" + name, Mesh = SetMesh(b), MaterialOverride = SetMat(name, SetGain * SetObjGain), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            otris += b.I.Count / 3;
        }
        if (hulls.Count > 0)
        {
            var sph = new SphereMesh { Radius = 1f, Height = 2f, RadialSegments = 16, Rings = 8 }.GetMeshArrays();
            var sv = (Vector3[])sph[(int)Mesh.ArrayType.Vertex]; var si = (int[])sph[(int)Mesh.ArrayType.Index];
            var hb = new SetBuf();
            foreach (var t in hulls)
            {
                int b0 = hb.V.Count;
                foreach (var v in sv) { hb.V.Add(t * v); hb.N.Add(Vector3.Up); hb.U.Add(Vector2.Zero); hb.C.Add(Colors.White); }
                foreach (int ix in si) hb.I.Add(b0 + ix);
            }
            c.Root.AddChild(new MeshInstance3D { Name = "SetObjShadows", Mesh = SetMesh(hb), CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly });
        }
        c.Count["set modules"] = modules; c.Count["set tris"] = tris; c.Count["set corners"] = corners; c.Count["set spills"] = spills;
        GD.Print($"DenSet: mode {SetMode}, {rooms.Count} rooms, {runs} runs, {modules} modules, {corners} corners, {spills} spills, {tris} bank tris, {otris} object tris, {bufs.Count + objBufs.Count + (hulls.Count > 0 ? 1 : 0)} draws");
    }

    // (r13) The lanes. A room's ring sees a corridor's walls only at grazing angles, and a wall in line with the room's middle
    // never: seed 11's corridor north of its first clearing had no card on its west bank (the Start ring's 4 points there
    // fell under a run's 6), so the wall mesh's dark mound and its foot along the generator's straight capsule showed (the
    // ruled edge and the muddy left bank, r12 judge). Rings from the corridors' own middles (a 2 m lattice where the floor
    // is open round the point, outside every room's circle) gather the edge points no room's run dressed, outside the rooms'
    // circles; each class's points joined where they lie within 1.5 m make one run (one long run a bank, not a short run a
    // ring: every run's ends fade), laid by the rooms' own SetRun, with root spills at its feet. Cards only: nothing collides.
    static readonly float SetLanes = SurvivorUnchained.Args.Num("den-set-lanes", 1f);
    static readonly HashSet<long> setCov = new();
    static long CovK(int i, int j) => ((long)i << 32) ^ (uint)j;
    static void SetCover(Vector3 p)
    {
        const float cs = 0.5f; const int rad = 2;   // (1 m round every dressed edge point)
        int ci = Mathf.FloorToInt(p.X / cs), cj = Mathf.FloorToInt(p.Z / cs);
        for (int i = -rad; i <= rad; i++) for (int j = -rad; j <= rad; j++) if (i * i + j * j <= rad * rad) setCov.Add(CovK(ci + i, cj + j));
    }
    static bool SetCovered(Vector3 p) => setCov.Contains(CovK(Mathf.FloorToInt(p.X / 0.5f), Mathf.FloorToInt(p.Z / 0.5f)));

    static void SetLaneRings(Ctx c, Dictionary<string, SetBuf> bufs, ref int modules, ref int runs, ref int spills)
    {
        const int n = 360;
        const float reach = 9f, lat = 2f, cs = 0.4f;
        bool InRoom(float x, float zz, float pad)
        {
            foreach (var r in c.Z.Rooms) if (r.Kind != "Bend" && new Vector2(x - r.X, zz - r.Z).Length() < r.R + pad) return true;
            return false;
        }
        var P = new Vector3[n]; var open = new bool[n];
        var pool = new Dictionary<long, Vector3>[4];
        for (int q = 0; q < 4; q++) pool[q] = new();
        int rings = 0, lanes = 0;
        float half = c.Z.Half;
        for (float cz = -half + lat; cz < half; cz += lat)
            for (float cx = -half + lat; cx < half; cx += lat)
            {
                if (!SetIn(cx, cz) || Wall(c, cx, cz) < 1.5f || InRoom(cx, cz, 0f)) continue;
                rings++;
                if (Wall(c, cx, cz) >= 1.8f && !InRoom(cx, cz, 3f) && Hole(c, cx, cz) > 2.5f) laneMid.Add(new Vector2(cx, cz));
                for (int k = 0; k < n; k++)
                {
                    float a = k * Mathf.Tau / n;
                    var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                    float t = 0.5f;
                    while (t < reach && Wall(c, cx + d.X * t, cz + d.Y * t) >= 0f) t += 0.1f;
                    open[k] = t >= reach;
                    if (open[k]) continue;
                    float lo = t - 0.1f, hi = t;
                    for (int b = 0; b < 10; b++) { float m = 0.5f * (lo + hi); if (Wall(c, cx + d.X * m, cz + d.Y * m) < 0f) hi = m; else lo = m; }
                    float x = cx + d.X * lo, zz = cz + d.Y * lo;
                    P[k] = new Vector3(x, H(c, x, zz), zz);
                }
                for (int k = 0; k < n; k++)
                {
                    if (open[k] || SetCovered(P[k]) || InRoom(P[k].X, P[k].Z, 0.5f)) continue;
                    // the outward normal smoothed over the neighbours' +-3 degrees, as the rooms' rings (their +-1.5 m of edge)
                    var g = Vector2.Zero;
                    for (int j = -3; j <= 3; j++)
                    {
                        int kk = (k + j + n) % n;
                        if (open[kk]) continue;
                        var p = P[kk];
                        g += new Vector2(Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f));
                    }
                    var o = -g.Normalized();
                    float th = Mathf.RadToDeg(Mathf.Atan2(o.X, -o.Y));
                    long key = CovK(Mathf.FloorToInt(P[k].X / cs), Mathf.FloorToInt(P[k].Z / cs));
                    for (int cls = 0; cls < 4; cls++)
                        if (SetClassOf(th, cls) == 1) pool[cls].TryAdd(key, P[k]);
                }
            }
        // each class's points joined where within 1.5 m (cells of 0.4 m, +-4), a component a run
        for (int cls = 0; cls < 4; cls++)
        {
            var left = new HashSet<long>(pool[cls].Keys);
            var keys = new List<long>(pool[cls].Keys);
            keys.Sort();
            foreach (long k0 in keys)
            {
                if (!left.Remove(k0)) continue;
                var run = new List<Vector3>();
                var todo = new Stack<long>(); todo.Push(k0);
                while (todo.Count > 0)
                {
                    long k = todo.Pop();
                    var p = pool[cls][k];
                    run.Add(p);
                    int ci = Mathf.FloorToInt(p.X / cs), cj = Mathf.FloorToInt(p.Z / cs);
                    for (int i = -4; i <= 4; i++)
                        for (int j = -4; j <= 4; j++)
                        {
                            long kk = CovK(ci + i, cj + j);
                            if (left.Contains(kk) && pool[cls][kk].DistanceTo(p) < 1.5f) { left.Remove(kk); todo.Push(kk); }
                        }
                }
                bool alongX = cls == 0 || cls == 2;
                run.Sort((u, v) => alongX ? u.X.CompareTo(v.X) : u.Dot(CamUp).CompareTo(v.Dot(CamUp)));
                if (run.Count < 6 || run[0].DistanceTo(run[^1]) < 3f) continue;
                float top = -1e9f;
                foreach (var p in run) top = Mathf.Max(top, p.Y);
                int seed = 7919 + (int)(k0 & 0xffff) * 7 + (int)((k0 >> 32) & 0xffff) * 13 + cls;
                if (SetLog > 0f) GD.Print($"DenSet lane: cls {cls} n {run.Count} from ({run[0].X:0.0},{run[0].Z:0.0}) to ({run[^1].X:0.0},{run[^1].Z:0.0})");
                modules += SetRun(c, bufs, run, cls, seed, top + 14f); runs++; lanes++;
                foreach (var q in run) SetCover(q);
                // the rooms' root spills at these feet too (far and side banks), toward the floor (the wall field's rise)
                if (SetSpills > 0f && cls != 2)
                {
                    float acc = 0f, next = 1f + 3f * Hash(seed, cls, 831);
                    for (int i = 1; i < run.Count; i++)
                    {
                        acc += run[i].DistanceTo(run[i - 1]);
                        if (acc < next) continue;
                        next = acc + 4f + 3f * Hash(seed + i, cls, 832);
                        var p = run[i];
                        var dir = new Vector2(Wall(c, p.X + 0.3f, p.Z) - Wall(c, p.X - 0.3f, p.Z), Wall(c, p.X, p.Z + 0.3f) - Wall(c, p.X, p.Z - 0.3f)).Normalized();
                        var at = new Vector2(p.X, p.Z) + dir * (1.0f + 0.8f * Hash(seed + i, cls, 834));
                        if (SetPick("B6", Hash(seed + i, cls, 835)) is SetPiece pc && Wall(c, at.X, at.Y) > 0.5f)
                        { PlaceSetObj(c, "B6", pc, at.X, at.Y, 0.5f + 0.25f * Hash(seed + i, cls, 836), 0f, false, 0f); spills++; }
                    }
                }
            }
        }
        // (r14, F2) warm pools along the lanes: the corridors had no light of their own (the shafts are the rooms'), their
        // floor a near-black trench (median ~39 against den_room.png's lit floor 79-109). A warm omni over the lane's middle
        // every LanePoolGap metres (greedy, outside the rooms' circles + 3 m), low and soft, no shadow: light only.
        int pools = 0;
        if (LanePoolEnergy > 0f)
        {
            var at = new List<Vector2>();
            foreach (var m in laneMid)
            {
                bool far = true;
                foreach (var q in at) if (q.DistanceTo(m) < LanePoolGap) { far = false; break; }
                if (!far) continue;
                at.Add(m);
                float e = LanePoolEnergy * (0.8f + 0.4f * Hash((int)(m.X * 7f), (int)(m.Y * 7f), 841));
                c.Root.AddChild(new OmniLight3D
                {
                    Name = "lane_pool", Position = new Vector3(m.X, H(c, m.X, m.Y) + LanePoolHigh, m.Y),
                    LightColor = new Color(SurvivorUnchained.Args.Get("den-lane-pool-colour") ?? "ffc08a"), LightEnergy = e,
                    OmniRange = LanePoolRange, OmniAttenuation = 1.3f, ShadowEnabled = false, LightSpecular = 0.1f,
                });
                pools++;
            }
        }
        laneMid.Clear();
        GD.Print($"DenSet lanes: {rings} rings, {lanes} runs, {pools} lane pools");
    }
    static readonly List<Vector2> laneMid = new();
    static readonly float LanePoolEnergy = SurvivorUnchained.Args.Num("den-lane-pool", 3.2f), LanePoolGap = SurvivorUnchained.Args.Num("den-lane-pool-gap", 6.5f),
        LanePoolRange = SurvivorUnchained.Args.Num("den-lane-pool-range", 6.5f), LanePoolHigh = SurvivorUnchained.Args.Num("den-lane-pool-high", 2.4f);

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
                // (r10c) a wall's bank part is 3.8-5.4 m deep: rows behind it, each its bank part 1 m into the one before,
                // drawn under it, so the frame's sides are root tangle to their edges and not the mound's dark mass
                if (!alongX)
                    for (int row = 1; row < SetRows; row++)
                    {
                        var b2 = choices[(int)(Hash(seed + 97 * row, 64, k) * choices.Count) % choices.Count];
                        float deep = row * Mathf.Max(1.5f, (cls == 3 ? b2.FootU : 1f - b2.FootU) * b2.Metres.X * SetScale - 1f);
                        float sh = cls == 3 ? -deep : deep;
                        if (!bufs.TryGetValue(b2.Name, out var buf2)) bufs[b2.Name] = buf2 = new SetBuf();
                        SetModule(c, buf2, b2, false, s, L, from, to, a => FootAt(a) + sh, true, s + L > a1 + ext, 0.0f - 0.01f * row, top, true);
                    }
            }
            s += L - ov;
            k++;
        }
        // (r10c) a far run's row behind, its foot 4 m up the bank and 7 m past the run's ends, its bank part only (under the
        // front row and the corners): the deep bank beyond the corners was the mound's flat black
        if (cls == 0 && SetRows >= 2 && SetBackRow > 0f)
        {
            float e2 = 7f, s2 = a0 - e2 - Hash(seed, 66, 0) * 4f;
            for (int k2 = 0; s2 < a1 + e2 && k2 < 40; k2++)
            {
                var b = choices[(int)(Hash(seed, 67, k2) * choices.Count) % choices.Count];
                float L = b.Metres.X * SetScale;
                float from = Mathf.Max(s2, a0 - e2), to = Mathf.Min(s2 + L, a1 + e2);
                // (r11) only past the front run's ends (behind the corners): over the run's middle its flat earth middle
                // drew a hard dark rectangle across the frame's top (c_p13); --den-set-backrow 1 lays the whole row again
                if (SetBackRow < 1.5f)
                {
                    if (to - from > 0.5f)
                    {
                        if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                        SetModule(c, buf, b, true, s2, L, from, to, a => FootAt(a) + 4f, true, s2 + L > a1 + e2, -0.01f, top, true);
                    }
                }
                else
                    foreach (var (f0, t0) in new[] { (from, Mathf.Min(to, a0 + 1.5f)), (Mathf.Max(from, a1 - 1.5f), to) })
                        if (t0 - f0 > 0.5f)
                        {
                            if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                            SetModule(c, buf, b, true, s2, L, f0, t0, a => FootAt(a) + 4f, true, true, -0.01f, top, true);
                        }
                s2 += L - ov;
            }
        }
        return laid;
    }

    static void SetModule(Ctx c, SetBuf buf, SetBank b, bool alongX, float s, float L, float from, float to,
        System.Func<float, float> footAt, bool fadeIn, bool fadeOut, float lift, float top, bool bankOnly = false)
    {
        float Wm = b.Metres.X * SetScale, Hm = b.Metres.Y * SetScale, ov = 2.0f;
        const float cell = 0.35f;
        int na = Mathf.Max(2, Mathf.CeilToInt((to - from) / cell) + 1);
        int nc = Mathf.Max(2, Mathf.CeilToInt((alongX ? Hm : Wm) / cell) + 1);
        int base0 = buf.V.Count;
        // (r12) every module its own depth layer: two rooms' rings both laid cards over one corridor bank at the same lift,
        // and the two coplanar casts took the depth test a triangle each (the corridor's checkerboard facets, c_p15)
        float lay = bankOnly ? -0.03f * (setLayer % 5) : SetLayerStep * (setLayer % 10);
        setLayer++;
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
                    if (SetFootFade > 0f) fe = Mathf.Min(fe, (b.Kind == "far" ? 1f - v : v) / 0.08f);   // (r12) and its straight cut out on the floor
                }
                else
                {
                    v = 1f - (a - s) / L; u = t;
                    Y = a; X = foot + (u - b.FootU) * Wm;
                    bankSide = b.Kind == "left" ? u < b.FootU - 0.02f : u > b.FootU + 0.02f;
                    fe = b.Kind == "left" ? u / 0.1f : (1f - u) / 0.1f;
                    if (SetFootFade > 0f) fe = Mathf.Min(fe, (b.Kind == "left" ? 1f - u : u) / 0.1f);   // (r12: the corridor's straight floor edge)
                }
                var pc = new Vector3(X, 0f, 0f) + CamUp * Y;
                var q = SetCast(pc, surf, top);
                // (r12) the bank side hidden where its cast lands on walkable floor, by a smooth measure (its 0.5 contour follows
                // the edge's own curve; a flag per vertex cut grid-aligned steps: the pale square cut-outs)
                // (r12) its 0.5 contour wanders up to SetEdgeWave out onto the floor (a slow two-sine field in the world): the
                // corridors' edges ran dead straight (the generator's capsules), a ruled cut down both sides of the frame
                float wv = SetEdgeWave * (0.5f + 0.25f * Mathf.Sin(q.X * 0.83f + 1.7f * Mathf.Sin(q.Z * 0.61f + 0.4f)) + 0.25f * Mathf.Sin(q.Z * 1.37f - q.X * 0.29f + 2.1f));
                float g = SetKeepAll > 0f || !bankSide ? 1f : 1f - SetSm(0.05f, 0.55f, Wall(c, q.X, q.Z) - wv);
                bool keep = g > 0.01f;
                // (r10c) a row behind: its bank part only (its pour would double the front row's on the floor)
                // (r12) its cut fades first (only its brightest masses past it, gone 1.2 m on): the hard cut's straight lines and
                // corners drew pale square cut-outs at a corridor's edge
                if (bankOnly)
                {
                    float d = !alongX ? (b.Kind == "left" ? u - b.FootU - 1f / Wm : b.FootU - 1f / Wm - u) * Wm
                                      : (b.Kind == "far" ? v - b.FootV - 1f / Hm : b.FootV - 1f / Hm - v) * Hm;
                    if (SetFootFade > 0f) { if (d > 1.2f) keep = false; else if (d > 0f) fe = Mathf.Min(fe, 1f - d / 1.0f); }
                    else if (d > 0f) keep = false;
                }
                // (r12) a row behind never reaches the floor's edge (its cut there followed a straight corridor edge: pale slabs)
                if (bankOnly && SetFootFade > 0f) g = Mathf.Min(g, SetSm(0.8f, 1.6f, -Wall(c, q.X, q.Z)));
                // (r14, B1-B2) a module's borders cut ragged: its rectangle's edges are straight lines on screen (the camera's
                // plane), and the fade still shows the brightest masses up to them (the far left's straight-sided cards, the
                // right foot's ruled edge). The cut wanders 0.3 to 0.3 + SetRagged metres in from every border by a slow world
                // field, so a module ends in an organic line of roots against the mass behind it.
                if (SetRagged > 0f)
                {
                    // (the deep border only: the floor side's pour is SetFootFade's, and cut it bared the mesh's foot)
                    float dEdge = alongX ? (b.Kind == "far" ? v : 1f - v) * Hm : (b.Kind == "left" ? u : 1f - u) * Wm;
                    float dEnd = Mathf.Min(fadeIn ? a - from : 99f, fadeOut ? to - a : 99f);
                    float nz = 0.5f + 0.3f * Mathf.Sin(q.X * 2.1f + 1.3f * Mathf.Sin(q.Z * 1.7f + 0.4f)) + 0.2f * Mathf.Sin(q.Z * 2.9f - q.X * 1.1f + 0.7f);
                    g = Mathf.Min(g, SetSm(0.15f, 0.45f, Mathf.Min(dEdge, dEnd) - SetRagged * nz));
                }
                if (g <= 0.01f) keep = false;
                if (!keep) g = 0f;
                keepv[i * nc + j] = keep;
                buf.V.Add(q - CamView * (lift + lay + SetLiftAdd));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(Mathf.Clamp(u, 0f, 1f), Mathf.Clamp(v, 0f, 1f)));
                buf.C.Add(new Color(Mathf.Clamp(Mathf.Min(fa, fe), 0f, 1f), g, 0f, 1f));
            }
        }
        for (int i = 0; i < na - 1; i++)
            for (int j = 0; j < nc - 1; j++)
            {
                int k0 = i * nc + j, k1 = k0 + 1, k2 = k0 + nc, k3 = k2 + 1;
                if (!keepv[k0] && !keepv[k1] && !keepv[k2] && !keepv[k3]) continue;
                // (r11) a cell whose cast jumped (the view ray fell off a ledge of the proxy) stretched the painting into a
                // long shard: the black shard on the right and the pale plank strips top left (c_p13). Such cells are dropped.
                if (SetStretch > 0f)
                {
                    float cellM = Mathf.Max((to - from) / (na - 1), (alongX ? Hm : Wm) / (nc - 1));
                    var v0 = buf.V[base0 + k0]; var v1 = buf.V[base0 + k1]; var v2 = buf.V[base0 + k2]; var v3 = buf.V[base0 + k3];
                    float me = Mathf.Max(Mathf.Max(v0.DistanceTo(v1), v0.DistanceTo(v2)), Mathf.Max(v3.DistanceTo(v1), v3.DistanceTo(v2)));
                    if (me > SetStretch * cellM) continue;
                }
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
        float rx = PlaceSetObj(c, "O1", pc, x, zz, scale * SetBoulderScale * (big ? 1f : 0.8f), 0.62f, true);
        c.Tick("set boulders");
        c.Boulders.Add((new Vector2(x, zz), rx));
        return rx;
    }

    /// <summary>(round 10b) A painted object from a sheet (O1 boulders, O2 logs, O3 bone piles) on its half-ellipsoid
    /// proxy: ry is its height as a share of its half width (a boulder 0.62, a log 0.18, bones 0.1); the shadow-only hull
    /// for the tall ones. Returns the proxy's half width.</summary>
    static float PlaceSetObj(Ctx c, string sheet, SetPiece pc, float x, float zz, float k, float ryk, bool hull, float contact = -1f)
    {
        float W = pc.Metres.X * k, Hr = pc.Metres.Y * k;
        float rx = 0.46f * W, ry = ryk * rx;
        float aa = CamUp.Y * ry, hm = 0.94f * Hr;
        float bb = Mathf.Max((hm * hm - aa * aa) / (2f * hm), 0.25f * rx);
        float rz = bb / -CamUp.Z;
        float y0 = H(c, x, zz);
        float yFront = new Vector3(x, y0, zz + rz).Dot(CamUp);
        System.Func<float, float, float> surf = (px, pz) =>
        {
            float ex = (px - x) / rx, ez = (pz - zz) / rz;
            float e = 1f - ex * ex - ez * ez;
            float s = e > 0f && ry > 0f ? y0 + ry * Mathf.Sqrt(e) : -99f;
            // (r11) never more than 1.5 m under its own foot: over a pit's mouth the cast missed the floor and ran 120 m
            // down the view (seed 23's lair: a fan of streaks to the vanishing point)
            return Mathf.Max(Mathf.Max(s, SurfBank(c, px, pz)), y0 - 1.5f);
        };
        if (!objBufs.TryGetValue(sheet, out var buf)) objBufs[sheet] = buf = new SetBuf();
        int ob = buf.V.Count;
        const int nu = 16, nv = 14;
        float top = y0 + ry + 10f;
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float X = x + (u - 0.5f) * W, Y = yFront + (pc.FootV - v) * Hr;
                var q = SetCast(new Vector3(X, 0f, 0f) + CamUp * Y, surf, top);
                buf.V.Add(q - CamView * (ry > 0f ? 0.04f : 0.03f));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(pc.Uv.Position.X + u * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                buf.C.Add(new Color(1f, 1f, 0f, 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                buf.I.Add(ob + k0); buf.I.Add(ob + k2); buf.I.Add(ob + k1); buf.I.Add(ob + k1); buf.I.Add(ob + k2); buf.I.Add(ob + k3);
            }
        if (hull) hulls.Add(new Transform3D(Basis.FromScale(new Vector3(rx, ry, rz)), new Vector3(x, y0, zz)));
        float ca = contact >= 0f ? contact : hull ? 0.6f : 0.35f;
        if (ca <= 0f) return rx;
        blob ??= new GradientTexture2D
        {
            Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
            Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 1f }, Colors = new[] { new Color(0, 0, 0, 1), new Color(0, 0, 0, 0.7f), new Color(0, 0, 0, 0) } },
        };
        c.Root.AddChild(new Godot.Decal
        {
            Name = "SetContact", TextureAlbedo = blob, Modulate = new Color(1, 1, 1, ca), AlbedoMix = 1f,
            Size = new Vector3(2.5f * rx, 1.2f, 2.5f * rz), Position = new Vector3(x, y0, zz),
        });
        return rx;
    }

    /// <summary>(r10d) A hole painting (H2 a pit, H1 a hollow) over a hole of the floor: laid in the camera's plane, each
    /// painted point's offset from the painted lip's centre (the piece's mouth) taken to the floor and scaled by the hole's
    /// radius over the painted lip's at its bearing (as the old pit decals were fitted to the outline), then laid on the
    /// level floor; blended at its fading surround. False when there is no such painting.</summary>
    static bool PlaceSetHole(Ctx c, string sheet, Vector2 ctr, float[] co, int pick)
    {
        if (SetHoles <= 0f || !LoadSet() || !setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) return false;
        var pc = all[pick % all.Count];
        if (pc.Mouth.Z <= 0f) return false;
        float sn = -CamUp.Z;   // a floor metre north draws this many metres up the camera's plane
        float W = pc.Metres.X, Hr = pc.Metres.Y, ma = pc.Mouth.Z * W, mb = pc.Mouth.W * Hr / sn;
        if (!objBufs.TryGetValue(sheet, out var buf)) objBufs[sheet] = buf = new SetBuf();
        int ob = buf.V.Count;
        // (r12) a hole in the boss lair glows green (den_boss.png): COLOR.a 0.5 marks it, and a green light low in it
        bool lairHole = false;
        foreach (var rr in c.Z.Rooms) if (rr.Kind == "Boss" && new Vector2(rr.X, rr.Z).DistanceTo(ctr) < rr.R + 4f) lairHole = true;
        if (lairHole && SurvivorUnchained.Args.Num("den-pit-glow", 0.8f) > 0f)
            c.Root.AddChild(new OmniLight3D { Name = "PitGlow", Position = new Vector3(ctr.X, FloorY(c, ctr.X, ctr.Y) + 0.6f, ctr.Y),
                LightColor = new Color(0.45f, 1f, 0.3f), LightEnergy = SurvivorUnchained.Args.Num("den-pit-light", 1.2f), OmniRange = 4.5f, OmniAttenuation = 1.6f, ShadowEnabled = false });
        int nu = Mathf.Clamp(Mathf.CeilToInt(W / 0.3f) + 1, 8, 48), nv = Mathf.Clamp(Mathf.CeilToInt(Hr / 0.3f) + 1, 8, 48);
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float dx = (u - pc.Mouth.X) * W, dz = (v - pc.Mouth.Y) * Hr / sn;   // floor metres from the lip's centre (x east, z south)
                float th = Mathf.Atan2(dz, dx), cs = Mathf.Cos(th), si = Mathf.Sin(th);
                float rp = ma * mb / Mathf.Sqrt(mb * mb * cs * cs + ma * ma * si * si);
                float g = Mathf.Clamp(FourierAt(co, th) / Mathf.Max(rp, 0.05f), 0.15f, 4f);
                var w = ctr + new Vector2(dx, dz) * g;
                buf.V.Add(new Vector3(w.X, FloorY(c, w.X, w.Y) + 0.05f, w.Y));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(pc.Uv.Position.X + u * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                // (r11) COLOR.b: half the painted point's distance from the lip's centre in lip radii (1 at the lip), so
                // den_set_soft fades the painting's own earth surround out past the rim (it read as a pink stamped ring)
                float ell = Mathf.Sqrt(dx * dx / Mathf.Max(ma * ma, 1e-4f) + dz * dz / Mathf.Max(mb * mb, 1e-4f));
                buf.C.Add(new Color(1f, 1f, Mathf.Clamp(0.5f * ell, 0f, 1f), lairHole ? 0.5f : 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                buf.I.Add(ob + k0); buf.I.Add(ob + k2); buf.I.Add(ob + k1); buf.I.Add(ob + k1); buf.I.Add(ob + k2); buf.I.Add(ob + k3);
            }
        c.Tick("set " + sheet);
        return true;
    }

    /// <summary>(r10d) The rooms' open floor dressed, as den_room.png has things IN the room: bone piles (O3) through it, a
    /// small stone (O1) or a short log (O2) a few metres off the banks; seed-salted (Hash), clear of the room's middle (her
    /// start and the fight), the walls' feet, the pits and hollows, the boulders and each other (the decals' Ok() rule).
    /// (r11) The boss lair too, as den_boss.png: one hero boulder (about 3 m) first, then kills' bone piles and blood
    /// through its open floor, a stone or log now and then; all cards, she and the pack walk through them.</summary>
    static void SetOpen(Ctx c, List<(float X, float Z, float R, string Kind)> rooms)
    {
        var hollows = DenHollows(c);
        var taken = new List<Vector2>();
        foreach (var (bp, _) in c.Boulders) taken.Add(bp);
        int ri = 0, n = 0;
        foreach (var r in rooms)
        {
            ri++;
            bool lair = r.Kind == "Boss";
            int want = Mathf.RoundToInt(SetOpenK * (lair ? SetLairWant : 3f + r.R / 2.5f)), got = 0;   // (r12 judge: den_boss.png ~80 pieces; 35 -> --den-lair-want)   // (r11 judge: the lair ~a third of den_boss.png's dressing)   // (r11 1.5 + R/4 -> 3 + R/3: den_room.png has a handful IN the room)
            float a0 = Hash(ri, 21, 990) * Mathf.Tau;
            int rw = 0, rl = 0, rn = 0;
            for (int k = 0; k < (lair ? 900 : 96) && got < want; k++)
            {
                float rad = lair ? (got == 0 ? 4f + 5f * Hash(ri, k, 991) : 3f + SetLairRing * Mathf.Sqrt(Hash(ri, k, 991))) : 2.8f + Mathf.Max(0.8f * r.R - 2.8f, 0.5f) * Mathf.Sqrt(Hash(ri, k, 991)), ang = a0 + k * 2.39996f;
                // (the hero stone on the lair's far side, up the frame from the fight: below, it stands behind the HUD)
                if (lair && got == 0) ang = Mathf.Pi * (1.15f + 0.7f * Hash(ri, k, 989));   // (r11: from 2.8 m off her start to 0.8 R: the room's R overreaches its floor)
                var p = new Vector2(r.X + Mathf.Cos(ang) * rad, r.Z + Mathf.Sin(ang) * rad);
                float w = Wall(c, p.X, p.Y);
                if (w < 1.8f || Hole(c, p.X, p.Y) < 2.2f || p.DistanceTo(new Vector2(r.X, r.Z)) < 2.6f) { rw++; continue; }
                // (r11) never in an exit's lane: a ray from the room's middle past this point (and 15 degrees either side)
                // that meets no wall within R + 8 m runs out through a door
                bool lane = false;
                for (int e = -1; e <= 1 && !lane; e++)
                {
                    float ea = ang + e * 0.26f;
                    var d = new Vector2(Mathf.Cos(ea), Mathf.Sin(ea));
                    float t = 0.5f;
                    while (t < r.R + 8f && Wall(c, r.X + d.X * t, r.Z + d.Y * t) >= 0f) t += 0.5f;
                    if (t >= r.R + 8f) lane = true;
                }
                if (lane) { rl++; continue; }
                bool near = false;
                foreach (var (hp, hr, _) in hollows) if (hp.DistanceTo(p) < hr + 1.2f) near = true;
                foreach (var t in taken) if (t.DistanceTo(p) < (lair ? 1.8f : 2.6f)) near = true;
                if (near) { rn++; continue; }
                float u = Hash(ri, k, 992), q = Hash(ri, k, 993);
                string sheet = lair ? (got == 0 ? "O1" : u < 0.09f ? "O1" : u < 0.16f ? "O2" : u < 0.42f ? "B6" : u < 0.56f ? "O4" : "O3") : u < 0.35f ? "O1" : u < 0.5f ? "O2" : "O3";   // (r11: boulders and logs anywhere in the open, as den_room.png)
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((a, b) => a.Metres.X.CompareTo(b.Metres.X));
                // (stones and logs from the sheet's smaller half, a stone at most 1.6 m across: she walks through them)
                int half = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet is "O3" or "B6" or "O4" ? sorted[(int)(q * sorted.Count) % sorted.Count] : sorted[(int)(q * half) % half];
                // (r11: a stone up to 2.4 m across, a log 3-4 m: they are cards, she walks through them; the room's
                // fight was tuned without them, so none has a body)
                if (lair && got == 0) pc = sorted[sorted.Count - 1];   // (the lair's hero stone: the sheet's biggest)
                float k2 = sheet == "O4" ? 0.55f + 0.25f * Hash(ri, k, 994) : sheet == "B6" ? 0.6f + 0.25f * Hash(ri, k, 994) : lair && got == 0 ? Mathf.Min(1.2f, (2.8f + 0.6f * Hash(ri, k, 994)) / pc.Metres.X) : sheet == "O1" ? Mathf.Min(1f, (1.6f + 0.8f * Hash(ri, k, 994)) / pc.Metres.X) : sheet == "O2" ? 0.8f + 0.2f * Hash(ri, k, 994) : 0.9f + 0.3f * Hash(ri, k, 994);
                // (r11) the lair's roots over its floor, as den_boss.png's: a spill under the hero stone, more through the open
                if (lair && got == 0 && SetPick("B6", Hash(ri, k, 988)) is SetPiece hs)
                    PlaceSetObj(c, "B6", hs, p.X, p.Y + 0.4f, 0.85f, 0f, false, 0f);
                if (sheet is "B6" or "O4") PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O4" ? 0.1f : 0f, false, sheet == "O4" ? 0.3f : 0f);
                else PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O1" ? 0.62f : sheet == "O2" ? 0.18f : 0.1f, sheet == "O1");
                taken.Add(p); got++; n++;
                // (r11) blood (O5) by a kill's bones, and now and then on its own nearby (den_room.png's splashes and drags)
                if (sheet == "O3" || Hash(ri, k, 995) < (lair ? 0.6f : 0.35f))
                {
                    float ba = Hash(ri, k, 996) * Mathf.Tau, bd = 0.9f + 0.8f * Hash(ri, k, 997);
                    var bp = p + new Vector2(Mathf.Cos(ba), Mathf.Sin(ba)) * bd;
                    if (Wall(c, bp.X, bp.Y) > 1.0f && Hole(c, bp.X, bp.Y) > 1.5f && SetPick("O5", Hash(ri, k, 998)) is SetPiece bpc)
                    { PlaceSetObj(c, "O5", bpc, bp.X, bp.Y, 1.1f + 0.5f * Hash(ri, k, 999), 0f, false, 0f); c.Tick("set blood"); }
                }
            }
            GD.Print($"SetOpen {r.Kind} room ({r.X:0.0}, {r.Z:0.0}) R {r.R:0.0}: {got}/{want}, off the floor {rw}, in a lane {rl}, crowded {rn}");
        }
        c.Count["set open"] = n;
    }

    /// <summary>(round 10b) One piece of a set sheet by a hash, or null.</summary>
    static SetPiece? SetPick(string sheet, float u)
    {
        if (!LoadSet() || !setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) return null;
        return all[(int)(u * all.Count) % all.Count];
    }

    /// <summary>(round 10b) The kills' leavings where the set dresses: a painted bone pile (O3) at a pile's seed in place
    /// of the old decal bones, rib cages, skulls, fur and blood; by a bank's foot now and then a painted log (O2).</summary>
    static void SetLitter(Ctx c, Vector2 p, int si, float wall)
    {
        if (wall < 2.2f && Hash(si, 7, 971) < 0.22f && SetPick("O2", Hash(si, 7, 972)) is SetPiece lg)
        {
            PlaceSetObj(c, "O2", lg, p.X, p.Y, 0.7f + 0.2f * Hash(si, 7, 973), 0.18f, false);
            c.Tick("set logs");
            return;
        }
        if (Hash(si, 7, 974) < 0.7f && SetPick("O3", Hash(si, 7, 975)) is SetPiece bn)
        {
            PlaceSetObj(c, "O3", bn, p.X, p.Y, 0.85f + 0.3f * Hash(si, 7, 976), 0.1f, false);
            c.Tick("set bones");
        }
    }

    /// <summary>(round 10b) Decal kinds the set's paintings replace where it dresses (off-style beside them).</summary>
    static bool SetDrops(string kind) => kind is "bone" or "ribcage" or "wolf_skull" or "deer_skull" or "blood" or "hide" or "drag" or "fur";

    static ArrayMesh SetMesh(SetBuf b)
    {
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = b.V.ToArray();
        arr[(int)Mesh.ArrayType.Normal] = b.N.ToArray();
        arr[(int)Mesh.ArrayType.TexUV] = b.U.ToArray();
        arr[(int)Mesh.ArrayType.Color] = b.C.ToArray();
        arr[(int)Mesh.ArrayType.Index] = b.I.ToArray();
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        return mesh;
    }

    /// <summary>(r10c) An inner corner (B4 back-left, B4R_2 back-right) laid in the camera's plane with its inner point (the
    /// image's foot_u, foot_v: where its far arm's foot meets its wall arm's) on the plane point (X, Y), cast onto the bank
    /// and floor under the two runs' front rows: it shows where they end, in the corner between them.</summary>
    static void SetCorner(Ctx c, SetBuf buf, SetBank b, float X, float Y, float top)
    {
        float W = b.Metres.X * SetScale, Hm = b.Metres.Y * SetScale;
        const float cell = 0.35f;
        int nu = Mathf.CeilToInt(W / cell) + 1, nv = Mathf.CeilToInt(Hm / cell) + 1;
        int base0 = buf.V.Count;
        var keepv = new bool[nu * nv];
        bool left = b.Kind == "corner_l";
        System.Func<float, float, float> surf = (x, zz) => SurfBank(c, x, zz);
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float PX = X + (u - b.FootU) * W, PY = Y + (b.FootV - v) * Hm;
                var q = SetCast(new Vector3(PX, 0f, 0f) + CamUp * PY, surf, top);
                // along the arms from the inner point (the far arm runs away from the wall, the wall arm down the frame)
                // under the runs' front rows (they carry on over its arms), over the rows behind; toward its image's edges only its
                // bright roots, as a module over its neighbour
                float fa = Mathf.Min(Mathf.Min(u * W, (1f - u) * W), Mathf.Min(v * Hm, (1f - v) * Hm)) / 2f;
                bool bankSide = (left ? u < b.FootU - 0.02f : u > b.FootU + 0.02f) || v < b.FootV - 0.02f;
                bool keep = !(bankSide && Wall(c, q.X, q.Z) > 0.3f);
                keepv[j * nu + i] = keep;
                buf.V.Add(q - CamView * 0.02f);
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(u, v));
                buf.C.Add(new Color(fa, keep ? 1f : 0f, 0f, 1f));
            }
        for (int j = 0; j < nv - 1; j++)
            for (int i = 0; i < nu - 1; i++)
            {
                int k0 = j * nu + i, k1 = k0 + 1, k2 = k0 + nu, k3 = k2 + 1;
                if (!keepv[k0] && !keepv[k1] && !keepv[k2] && !keepv[k3]) continue;
                buf.I.Add(base0 + k0); buf.I.Add(base0 + k2); buf.I.Add(base0 + k1);
                buf.I.Add(base0 + k1); buf.I.Add(base0 + k2); buf.I.Add(base0 + k3);
            }
    }
}
