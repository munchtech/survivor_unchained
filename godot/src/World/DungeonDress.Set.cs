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
    static readonly float SetCool = SurvivorUnchained.Args.Num("den-set-cool", 0.4f);   // (r13 1 -> 0.4 with shade-tint 1,.95,.85: the banks' darks h 233-331 (mauve) -> 7-17, lane E Banks band warm umber)   // (r10b) the paintings' shade to cool grey (den_set.gdshader shade_k)

    static readonly float SetRockGain = SurvivorUnchained.Args.Num("den-rock-gain", 0.45f);   // (den r13 rooms) the O1 boulders: their brightest 10 % at luminance <= 85
    static readonly float SetVary = SurvivorUnchained.Args.Num("den-set-vary", 1f);   // (den r14 objects, item 4) caps, mirror and turn on bone piles and logs
    static readonly float SetRockLit = SurvivorUnchained.Args.Num("den-rock-lit", 1f);   // (den r14 objects, item 3) open-floor boulders: round, lit, mossed (sheet O1r); 0 the r13 stones
    static readonly float SetRockBig = SurvivorUnchained.Args.Num("den-rock-big", 1.45f);   // their scale
    static readonly float SetRockGainLit = SurvivorUnchained.Args.Num("den-rock-gain-lit", 1f);
    // (den r15 A, R14 judge item 1: r14's O1r blurred O1 to a mip and painted a procedural top: 24 px blocks, no ink) O1r drawn
    // from its own sheet (tools/look/den_rocks.py: O1's stones at 2x in the target's value band, inked), no blur branch; 0 r14's
    static readonly float SetRockPaint = SurvivorUnchained.Args.Num("den-rock-paint", 1f);
    static readonly float SetRockDome = SurvivorUnchained.Args.Num("den-rock-dome", 0f);   // (den r15 G) plain O1 stones cast on their own dome over the floor, not the bank surface
    static readonly float SetRockLanePaint = SurvivorUnchained.Args.Num("den-rock-lanepaint", 0f);   // (den r15 G) the lane/alcove stones drawn from the painted round sheet O1r too
    static string? LaneRockKey => SetRockLanePaint > 0f && SetRockPaint > 0f && SetRockLit > 0f ? "O1r" : null;
    static readonly float SetRockNoCube = SurvivorUnchained.Args.Num("den-rock-nocube", 0f);   // (den r15 A) 1: plain O1 stones never the flat-topped block (PlaceSetObj). Off: a1 showed the s11 pale cube is not that piece (the cast over the bank's rise makes the cube)
    static readonly int SetLairCrowns = (int)SurvivorUnchained.Args.Num("den-lair-crowns", 3f);   // (den r13 rooms) root-crowns (B6) a lair may hold (0: no cap)
    static int lairPits;   // (den r13 rooms) lair holes met so far
    static Vector3 setBossC;   // (r12) the lair's centre x, z and radius for the set's gloom (0: none), taken where the set is built
    internal static readonly float SetBossGloom = SurvivorUnchained.Args.Num("den-boss-gloom", 1.2f);

    static ShaderMaterial SetMat(string sheet, float gain)
    {
        // (r10d) the hole paintings (H1, H2) lie on the floor blended (their surround fades into it); the rest cut at alpha 0.5
        var mat = new ShaderMaterial { Shader = sheet[0] == 'H' ? setSoftShader : setShader };
        bool rockPaint = sheet == "O1r" && SetRockPaint > 0f;   // (den r15 A) the round boulders' own painted sheet
        mat.SetShaderParameter("paint_tex", GD.Load<Texture2D>(SetDir + (sheet == "O1r" && !rockPaint ? "O1" : sheet) + ".png"));
        if (rockPaint) gain *= SurvivorUnchained.Args.Num("den-rock-paint-gain", 1.5f);   // (a1: the stones Lp90 .25-.40, the target lit .45-.60)
        if (sheet == "O1r" && !rockPaint)
        {
            mat.SetShaderParameter("rock_k", SurvivorUnchained.Args.Num("den-rock-k", 1f));
            mat.SetShaderParameter("rock_lod", SurvivorUnchained.Args.Num("den-rock-lod", 2.2f));
            mat.SetShaderParameter("rock_lit", V3("den-rock-col", new Vector3(0.23f, 0.155f, 0.085f)));
            mat.SetShaderParameter("rock_moss", V3("den-rock-moss", new Vector3(0.1f, 0.13f, 0.04f)));
            mat.SetShaderParameter("rock_moss_k", SurvivorUnchained.Args.Num("den-rock-moss-k", 0.6f));
        }
        if (sheet == "B6" && SetRootK != 1f) gain *= SetRootK * SetRootK * SetRootK;
        mat.SetShaderParameter("gain", gain);
        mat.SetShaderParameter("sat", SetSat);
        mat.SetShaderParameter("shade_k", SetCool);
        mat.SetShaderParameter("dark_floor", SetDark);
        mat.SetShaderParameter("amb_floor", SetAmb);
        // (r11) the roots and shade read pink-mauve: the paintings' mids warmed (less blue), the shade's cool narrowed to the
        // deepest darks and turned blue-teal (den_room.png: warm brown in the light, cool only down in the hollows)
        mat.SetShaderParameter("tint", V3("den-set-tint", new Vector3(1f, 0.98f, 0.81f)));
        mat.SetShaderParameter("shade_tint", V3("den-set-shade-tint", new Vector3(1.0f, 0.95f, 0.85f)));
        mat.SetShaderParameter("shade_hi", SurvivorUnchained.Args.Num("den-set-shade-hi", 0.15f));
        // (den r15 helper D) the bone piles' shade warm umber (hue 40-60), not the grey-violet the judge measured (hue ~210, C .02)
        if (sheet == "O3") mat.SetShaderParameter("shade_tint", V3("den-bone-shade", new Vector3(1.0f, 0.80f, 0.55f)));
        // (den r14 corr, item 9) the camera-side banks (near class) are the frame's nearest roots: their lit tops read bleached
        // (seed-23 corridor L .45, room L .51 against den_room.png's foreground .33-.41): their highlights rolled off and warmed
        if (sheet is "B2" or "B2b") mat.SetShaderParameter("hi_roll", SurvivorUnchained.Args.Num("den-near-hi", 0.72f));
        if (sheet == "O5")
        {
            // (r12 judge: the seed-23 room's blood read magenta) the set's half saturation and its grey-violet shade turned the
            // painted blood pink-mauve: blood keeps its own red, a touch darker and browner
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-blood-sat", 0.6f));
            mat.SetShaderParameter("tint", V3("den-blood-tint", new Vector3(1.45f, 1.3f, 1.1f)));
            mat.SetShaderParameter("blood_rust", SurvivorUnchained.Args.Num("den-blood-rust", 0.45f));   // (den r15 C) crimson h 15-22 into rust 33-37
            mat.SetShaderParameter("blood_dir", V3("den-blood-dir", new Vector3(1.5f, 0.9f, 0.45f)));
            mat.SetShaderParameter("shade_k", 0f);
        }
        if (rockPaint)   // (den r15 A) den_rocks.py paints O1r's hue and chroma in the target's band: the set's half saturation and warm tint off
        {
            mat.SetShaderParameter("sat", SurvivorUnchained.Args.Num("den-rock-sat", 1f));
            mat.SetShaderParameter("tint", V3("den-rock-tint", new Vector3(1f, 1f, 1f)));
        }
        mat.SetShaderParameter("occ_k", SetOcclude);   // (den r15 F, lane A judge) the occlusion cut-out round her: roots and banks nearer the camera fade to 20 % over her
        mat.SetShaderParameter("occ_a", SurvivorUnchained.Args.Num("den-occlude-a", 0.2f));
        mat.SetShaderParameter("bank_gloom", SetGloom);   // (den r13 corr) COLOR.b's depth gloom (bank modules only: objects carry 0)
        mat.SetShaderParameter("gloom_m", SetGloomM);
        mat.SetShaderParameter("boss_c", setBossC);   // (r12) the lair's gloom, as the floor's
        mat.SetShaderParameter("boss_gloom", SetBossGloom);
        mat.SetShaderParameter("mush_glow", SurvivorUnchained.Args.Num("den-mush-glow", 0.35f));   // (r12 judge) teal on the ground under the painted caps
        mat.SetShaderParameter("fungus_sat", SurvivorUnchained.Args.Num("den-fungus-sat", 0.4f));   // (den r14, lane E) the painted caps' cyan into its band
        if (sheet[0] == 'H')
        {
            mat.SetShaderParameter("pit_glow", SurvivorUnchained.Args.Num("den-pit-glow", 0.8f));
        mat.SetShaderParameter("pit_dark", SurvivorUnchained.Args.Num("den-pit-dark", 0.35f));
        mat.SetShaderParameter("pit_col", new Color(SurvivorUnchained.Args.Num("den-pit-r", 0.5f), SurvivorUnchained.Args.Num("den-pit-g", 0.8f), SurvivorUnchained.Args.Num("den-pit-b", 0.4f)));   // (den r13 rooms) less neon   // (r12) den_boss.png's green pits
            mat.SetShaderParameter("pit_net", SurvivorUnchained.Args.Num("den-pit-net", 0.6f));
            mat.SetShaderParameter("pit_floor", SurvivorUnchained.Args.Num("den-pit-floor", 0.3f));
            mat.SetShaderParameter("pit_sat",SurvivorUnchained.Args.Num("den-pit-sat", 0.3f));
            mat.SetShaderParameter("pit_halo", SurvivorUnchained.Args.Num("den-pit-halo", 0.14f));
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
    static readonly float SetRowJit = SurvivorUnchained.Args.Num("den-set-row-jit", 2.5f);   // (r13) metres a row behind's depth varies by module
    static readonly int SetRows = (int)SurvivorUnchained.Args.Num("den-set-rows", 3f);       // (r10c) side walls: rows of modules deeper in the bank
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
    static readonly float SetRaggedEnds = SurvivorUnchained.Args.Num("den-set-ragged-ends", 0.6f);   // (den r13 corr) a module's unfaded end cut ragged by this share of SetRagged (0: straight)
    static readonly float SetGloom = SurvivorUnchained.Args.Num("den-set-gloom", 0f);   // (den r13 corr) corridor banks' roots darken with depth into the bank (0 off; 0.8 tried, k2_corr: card-space depth disagrees between classes, so a near module gloomed over a lit side one drew hard dark wedges: it needs a world depth field that does not saturate)
    static readonly Vector2 SetGloomM = new(SurvivorUnchained.Args.Num("den-set-gloom-a", 2.5f), SurvivorUnchained.Args.Num("den-set-gloom-b", 6.5f));   // metres in: from, full
    static readonly float SetLayerStep =SurvivorUnchained.Args.Num("den-set-layer", 0.04f);   // (r12) metres between modules' depth layers
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
        if (SetAlcoveK > 0f && c.Z.WalkField != null && c.Z.WalkField != c.Z.WallField) SetAlcoves(c);
        setBossC = Vector3.Zero; lairPits = 0;
        foreach (var rb in c.Z.Rooms) if (rb.Kind == "Boss") setBossC = new Vector3(rb.X, rb.Z, rb.R);
        if (SetOpenK > 0f) SetOpen(c, rooms.FindAll(q => q.Kind != "Bend"));
        int tris = 0;
        foreach (var (name, b) in bufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            var bm = SetMat(name, SetGain);
            if (SetDbgMod > 0f) bm.SetShaderParameter("dbg_mod", SetDbgMod);   // (den r15 E, diagnosis)
            if (SetCutNoise > 0f || SetCutLum > 0f)   // (den r15 E, judge r14 item 4) the bank cards' cut wanders finely and follows the roots
            { bm.SetShaderParameter("cut_noise", SetCutNoise); bm.SetShaderParameter("cut_lum", SetCutLum); bm.SetShaderParameter("cut_scale", SetCutScale); }
            c.Root.AddChild(new MeshInstance3D { Name = "Set_" + name, Mesh = SetMesh(b), MaterialOverride = bm, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            tris += b.I.Count / 3;
        }
        // (r10c) the objects (boulders, logs, bones, spills): one mesh a sheet; the boulders' shadow hulls in one
        int otris = 0;
        foreach (var (name, b) in objBufs)
        {
            if (b.I.Count == 0 || (SetOnly != null && System.Array.IndexOf(SetOnly, name) < 0)) continue;
            c.Root.AddChild(new MeshInstance3D { Name = "SetObj_" + name, Mesh = SetMesh(b), MaterialOverride = SetMat(name, SetGain * SetObjGain * (name is "O1" ? SetRockGain : name is "O1r" ? SetRockGainLit : 1f)), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
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
        laidHollows.Clear();
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
        // (r13) the corridors dressed as thin rooms: den_room.png has things IN the floor, the corridors were bare earth. A
        // stone, a short log or a bone pile now and then off the lane's middle (wall field 0.9-2.0 m in: never its middle
        // 1.5 m), 4.5 m apart at least, about half the lattice's chances skipped; cards, she walks through them.
        int dressed = 0;
        if (SetLaneDress > 0f)
        {
            var taken = new List<Vector2>();
            foreach (var m in laneMid)
            {
                int hx = Mathf.FloorToInt(m.X * 1.7f), hz = Mathf.FloorToInt(m.Y * 1.7f);
                if (Hash(hx, hz, 861) > 0.5f * SetLaneDress) continue;
                float a = Hash(hx, hz, 862) * Mathf.Tau, d = 1.0f + 1.5f * Hash(hx, hz, 863);
                var p = m + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * d;
                float w = Wall(c, p.X, p.Y);
                if (w < 0.9f || w > 2.0f || Hole(c, p.X, p.Y) < 2.2f || InRoom(p.X, p.Y, 2f)) continue;
                bool near = false;
                foreach (var t in taken) if (t.DistanceTo(p) < 4.5f) { near = true; break; }
                if (near) continue;
                float u = Hash(hx, hz, 864), q = Hash(hx, hz, 865), k = Hash(hx, hz, 866);
                string sheet = u < 0.4f ? "O1" : u < 0.6f ? "O2" : "O3";
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((x, y) => x.Metres.X.CompareTo(y.Metres.X));
                int hf = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet == "O3" ? sorted[(int)(q * sorted.Count) % sorted.Count] : sorted[(int)(q * hf) % hf];
                if (sheet == "O1") PlaceSetObj(c, "O1", pc, p.X, p.Y, Mathf.Min(1f, (1.1f + 0.6f * k) / pc.Metres.X), 0.62f, true, -1f, LaneRockKey);
                else if (sheet == "O2") PlaceSetObj(c, "O2", pc, p.X, p.Y, 0.75f + 0.2f * k, 0.18f, false);
                else PlaceSetObj(c, "O3", pc, p.X, p.Y, 0.9f + 0.3f * k, 0.1f, false);
                taken.Add(p); dressed++;
            }
        }
        laneMid.Clear();
        GD.Print($"DenSet lanes: {rings} rings, {lanes} runs, {pools} lane pools, {dressed} lane pieces");
    }
    static readonly List<Vector2> laneMid = new();
    static readonly float SetLaneDress = SurvivorUnchained.Args.Num("den-lane-dress", 1f);   // (r13) the corridors' floor pieces (0 off)

    // (r13) The alcoves: ground the drawn wall line bares outside the walkable edge (DenRagged: the corridors' banks pushed
    // outward), which she cannot walk on, is never open floor: a root spill (B6), a stone (O1) or a bone pile (O3) on it,
    // greedy on a 0.6 m lattice where the bared ground is at least 0.3 m deep, 1.4 m apart, the spill most often.
    static readonly float SetAlcoveK = SurvivorUnchained.Args.Num("den-alcove", 1f);
    static void SetAlcoves(Ctx c)
    {
        float half = c.Z.Half;
        var taken = new List<Vector2>();
        int n = 0, sp = 0, st = 0, bo = 0;
        for (float zz = -half + 1f; zz < half - 1f; zz += 0.6f)
            for (float x = -half + 1f; x < half - 1f; x += 0.6f)
            {
                float walk = Bil(c.Z, c.Z.WalkField!, x, zz), drawn = Wall(c, x, zz);
                if (walk > -0.3f || drawn < 0.3f || Hole(c, x, zz) < 1.5f) continue;
                var p = new Vector2(x, zz);
                bool near = false;
                foreach (var t in taken) if (t.DistanceTo(p) < 1.4f) { near = true; break; }
                if (near) continue;
                taken.Add(p);
                int hx = Mathf.FloorToInt(x * 3.1f), hz = Mathf.FloorToInt(zz * 3.1f);
                float u = Hash(hx, hz, 851), q = Hash(hx, hz, 852), k = Hash(hx, hz, 853);
                string sheet = u < 0.62f ? "B6" : u < 0.88f ? "O1" : "O3";
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((a, b) => a.Metres.X.CompareTo(b.Metres.X));
                int hf = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet == "O1" ? sorted[(int)(q * hf) % hf] : sorted[(int)(q * sorted.Count) % sorted.Count];
                if (sheet == "B6") { PlaceSetObj(c, "B6", pc, x, zz, SetAlcoveK * (0.55f + 0.3f * k), 0f, false, 0f); sp++; }
                else if (sheet == "O1") { PlaceSetObj(c, "O1", pc, x, zz, Mathf.Min(1f, (0.9f + 0.7f * k) / pc.Metres.X), 0.62f, true, -1f, LaneRockKey); st++; }
                else { PlaceSetObj(c, "O3", pc, x, zz, 0.8f + 0.3f * k, 0.1f, false); bo++; }
                n++;
            }
        c.Count["set alcoves"] = n;
        GD.Print($"DenSet alcoves: {n} ({sp} spills, {st} stones, {bo} bones)");
    }
    static readonly float LanePoolEnergy = SurvivorUnchained.Args.Num("den-lane-pool", 3.2f), LanePoolGap = SurvivorUnchained.Args.Num("den-lane-pool-gap", 6.5f),
        LanePoolRange = SurvivorUnchained.Args.Num("den-lane-pool-range", 6.5f), LanePoolHigh = SurvivorUnchained.Args.Num("den-lane-pool-high", 2.4f);

    // One run of a class: modules end to end along it, each laid in the camera's plane with its foot on the edge and cast
    // onto the bank and floor. Returns the modules laid.
    static readonly float SetBankLift = SurvivorUnchained.Args.Num("den-set-banklift", 1f);   // (den r14 corr r3; d14g_L: a 1 m lift lit 1b .26 -> .32, 1c box .25 -> .39) metres the cards over the bank come toward the camera
    static readonly float SetShearMax = SurvivorUnchained.Args.Num("den-set-shear", 0.5f);   // (den r14 corr r3) a far/near run's steepest foot slope (0: all laid)
    static readonly float SetDbgMod = SurvivorUnchained.Args.Num("den-set-dbgmod", 0f);   // (den r15 E, diagnosis) every bank module its own false colour (rows behind striped)
    // (den r15 E, judge r14 item 4: ruled card seams) the cut's fine wander and root-following in the shader (den_set cut_noise,
    // cut_lum, cut_scale), over a wider ramp (SetCutW metres: the ragged border's g from 0 to 1; 0.3 was a 24 px step), and
    // the ragged field unsharpened (SetRagSharp 0: its smoothstep held the cut at 0 or 1 over a fifth of a border, straight)
    static readonly float SetOcclude = SurvivorUnchained.Args.Num("den-occlude", 0f);   // (den r15 F) default 0 until a den_set card is proven over her (the roots that cover her in the film are kit scenes, other shaders); 1 on: set pieces between the camera and her fade round her (den_set.gdshaderinc occ_cut); 0 off
    static readonly float SetCutNoise = SurvivorUnchained.Args.Num("den-set-cut-noise", 0.4f);
    static readonly float SetCutLum = SurvivorUnchained.Args.Num("den-set-cut-lum", 0.5f);
    static readonly float SetCutScale = SurvivorUnchained.Args.Num("den-set-cut-scale", 2.2f);
    static readonly float SetCutW = SurvivorUnchained.Args.Num("den-set-cut-w", 0.8f);
    static readonly float SetRagSharp = SurvivorUnchained.Args.Num("den-set-rag-sharp", 0f);
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
        // (den r14 corr r3, items 1 slab/1c) a far or near run along a wall that climbs steeply on screen shears its modules:
        // each column shifted by the foot, the painting's lying roots drawn as diagonal planks and its deep cut a ruled
        // diagonal (seed 11's corridor: room 2's far runs up the corridor mouth's diagonal walls, slopes .84 and .56, laid B1
        // as two dark wedges over the corridor banks' B3/B3R). Past SetShearMax (screen metres per metre, least squares)
        // the run is not laid: the side classes' overlap (40-50 degrees) covers those walls.
        if (alongX && SetShearMax > 0f && pts.Count >= 2)
        {
            float ma = 0f, mf = 0f;
            foreach (var (pa, pf) in pts) { ma += pa; mf += pf; }
            ma /= pts.Count; mf /= pts.Count;
            float sxy = 0f, sxx = 0f;
            foreach (var (pa, pf) in pts) { sxy += (pa - ma) * (pf - mf); sxx += (pa - ma) * (pa - ma); }
            if (sxx > 1e-4f && Mathf.Abs(sxy / sxx) > SetShearMax) { if (SetLog > 0f) GD.Print($"DenSet run dropped: cls {cls} slope {sxy / sxx:0.00}"); return 0; }
        }
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
        SetBank? prev1 = null, prev2 = null;
        var first = choices[(int)(Hash(seed, 61, 0) * choices.Count) % choices.Count];
        float L0 = (alongX ? first.Metres.X : first.Metres.Y) * SetScale;
        float span = a1 - a0 + 2 * ext;
        float s = a0 - ext - Hash(seed, 62, 0) * (L0 > span ? L0 - span : 0.35f * L0);
        while (s < a1 + ext && k < 40)
        {
            var b = k == 0 ? first : choices[(int)(Hash(seed, 63, k) * choices.Count) % choices.Count];
            // (den r15 R, R15 judge item 7: the same mossy rock twice in the s11 corridor) a run's next card is never one of the last two laid
            for (int t = 1; SetNoRepeat > 0f && k > 0 && choices.Count > 2 && t < 8 && (b == prev1 || b == prev2); t++)
                b = choices[(int)(Hash(seed, 63 + 7 * t, k) * choices.Count) % choices.Count];
            prev2 = prev1; prev1 = b;
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
                        for (int t = 1; SetNoRepeat > 0f && choices.Count > 2 && t < 8 && b2 == b; t++) b2 = choices[(int)(Hash(seed + 97 * row, 64 + 7 * t, k) * choices.Count) % choices.Count];   // (den r15 R) a row behind is never its own front's card
                        float deep = row * Mathf.Max(1.5f, (cls == 3 ? b2.FootU : 1f - b2.FootU) * b2.Metres.X * SetScale - 1f);
                        // (r13) each module's row behind its own depth: at one depth the cards' far border ran parallel to the
                        // corridor down the whole frame (the seed-11 vertical at x ~200)
                        deep += SetRowJit * (Hash(seed + 97 * row, 68, k) - 0.35f);
                        float sh = cls == 3 ? -deep : deep;
                        if (!bufs.TryGetValue(b2.Name, out var buf2)) bufs[b2.Name] = buf2 = new SetBuf();
                        SetModule(c, buf2, b2, false, s, L, from, to, a => FootAt(a) + sh, true, s + L > a1 + ext, 0.0f - 0.01f * row, top, true, deep);
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
                        SetModule(c, buf, b, true, s2, L, from, to, a => FootAt(a) + 4f, true, s2 + L > a1 + e2, -0.01f, top, true, 4f);
                    }
                }
                else
                    foreach (var (f0, t0) in new[] { (from, Mathf.Min(to, a0 + 1.5f)), (Mathf.Max(from, a1 - 1.5f), to) })
                        if (t0 - f0 > 0.5f)
                        {
                            if (!bufs.TryGetValue(b.Name, out var buf)) bufs[b.Name] = buf = new SetBuf();
                            SetModule(c, buf, b, true, s2, L, f0, t0, a => FootAt(a) + 4f, true, true, -0.01f, top, true, 4f);
                        }
                s2 += L - ov;
            }
        }
        return laid;
    }

    // (den r14 corr) the ragged cut's field: isotropic 2-octave value noise in the world (0..1, sharpened); 0 keeps the sines
    static readonly float SetRaggedIso = SurvivorUnchained.Args.Num("den-set-ragged-iso", 1.6f);
    static float SetRagNoise(float x, float zz)
    {
        static float Vn(float px, float pz, int s)
        {
            int i = Mathf.FloorToInt(px), j = Mathf.FloorToInt(pz);
            float fx = px - i, fz = pz - j;
            fx = fx * fx * (3 - 2 * fx); fz = fz * fz * (3 - 2 * fz);
            return Mathf.Lerp(Mathf.Lerp(Hash(i, j, s), Hash(i + 1, j, s), fx), Mathf.Lerp(Hash(i, j + 1, s), Hash(i + 1, j + 1, s), fx), fz);
        }
        float n = 0.65f * Vn(x / 2.4f, zz / 2.4f, 871) + 0.35f * Vn(x / 0.9f, zz / 0.9f, 872);
        return SetRagSharp > 0f ? SetSm(0.25f, 0.75f, n) : Mathf.Clamp((n - 0.15f) / 0.7f, 0f, 1f);
    }

    static void SetModule(Ctx c, SetBuf buf, SetBank b, bool alongX, float s, float L, float from, float to,
        System.Func<float, float> footAt, bool fadeIn, bool fadeOut, float lift, float top, bool bankOnly = false, float deepAdd = 0f)
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
                    // (den r13 corr) its floor-side cut ragged too: at d > 1.2 it was a straight column of the card (u fixed),
                    // a ruled vertical down the seed-11 left bank; now 0.15 + up to SetRagged metres short of 1.2 by a world field
                    if (SetFootFade > 0f && SetRagged > 0f)
                    {
                        float nb = 0.5f + 0.3f * Mathf.Sin(q.Z * 1.9f + 1.1f * Mathf.Sin(q.X * 1.3f + 2.2f)) + 0.2f * Mathf.Sin(q.X * 2.7f - q.Z * 0.9f + 1.4f);
                        g = Mathf.Min(g, SetSm(0.15f, 0.45f, 1.2f - d - SetRagged * nb));
                        if (d > 0f) fe = Mathf.Min(fe, 1f - d / 1.0f);
                    }
                    else if (SetFootFade > 0f) { if (d > 1.2f) keep = false; else if (d > 0f) fe = Mathf.Min(fe, 1f - d / 1.0f); }
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
                    // (den r14 corr, item 1a) that field is a sine of X: along a north-south border (a corridor's side bank) X
                    // hardly changes, so the cut wandered +-0.2 m (the seed-11 left bank's vertical at x ~206, IQR 24 px). An
                    // isotropic value noise (2.4 m and 0.9 m) wanders the full 0..1 along any border.
                    if (SetRaggedIso > 0f) nz = SetRagNoise(q.X, q.Z);
                    g = Mathf.Min(g, SetSm(0.15f, 0.15f + SetCutW, Mathf.Min(dEdge, dEnd) - SetRagged * (SetRaggedIso > 0f ? SetRaggedIso : 1f) * nz));
                    // (den r13 corr) the module's end under its neighbour (no fade: the next one's faded start lies over it) was
                    // cut at the painting's own end, a ruled line where the neighbour shows only its bright masses (the seed-11
                    // left bank's horizontal at y 590); ragged too, by a share of SetRagged (it must still meet the neighbour)
                    if (!fadeOut && SetRaggedEnds > 0f)
                        g = Mathf.Min(g, SetSm(0.05f, 0.05f + 0.667f * SetCutW, to - a - SetRaggedEnds * SetRagged * nz));
                    if (!fadeIn && SetRaggedEnds > 0f)
                        g = Mathf.Min(g, SetSm(0.05f, 0.05f + 0.667f * SetCutW, a - from - SetRaggedEnds * SetRagged * nz));
                }
                if (g <= 0.01f) keep = false;
                if (!keep) g = 0f;
                keepv[i * nc + j] = keep;
                // (den r14 corr r3, items 1a/1b/1c) the wall mesh's lumps poked through the cards where the blurred proxy sank under
                // them (the dark mass in front: 1b's black slab, 1c's black box, half of 1a's ruled edge; hidden walls, those boxes
                // lit .26 -> .32, .25 -> .35). Over the bank (never over walkable floor, where she and the floor's things stand) every
                // card is pulled toward the camera by up to SetBankLift metres, the same at a point for all modules (their order holds)
                float bl = SetBankLift > 0f ? SetBankLift * SetSm(0.3f, 1.5f, -Wall(c, q.X, q.Z)) : 0f;
                buf.V.Add(q - CamView * (lift + lay + SetLiftAdd + bl));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(Mathf.Clamp(u, 0f, 1f), Mathf.Clamp(v, 0f, 1f)));
                // (den r13 corr) COLOR.b: metres into the drawn bank / 10, in the corridors only (DenRagged's weight): the
                // shader's bank gloom takes the roots dark as they go deeper, so the deep rows' borders and the mass behind
                // meet in the dark (the seed-11 far left's ruled vertical where the cards ended against the mound)
                // (the card's own metres from its foot plus its row's: the wall field saturates a little way into the bank)
                float dIn = deepAdd + (alongX ? (b.Kind == "far" ? b.FootV - v : v - b.FootV) * Hm : (b.Kind == "left" ? b.FootU - u : u - b.FootU) * Wm);
                float gb = SetGloom > 0f ? Mathf.Clamp(dIn * DenRagged.Corridor(q.X, q.Z, c.Z.Rooms) / 10f, 0f, 1f) : 0f;
                buf.C.Add(new Color(Mathf.Clamp(Mathf.Min(fa, fe), 0f, 1f), g, gb, SetDbgMod > 0f ? 0.5f * Mathf.PosMod(setLayer * 0.618034f, 1f) + (bankOnly ? 0.5f : 0f) : 1f));
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
        bool lit = SetRockLit > 0f;   // (den r14 objects, item 3) the wall groups' stones: bigger, round, lit and mossed
        float rx = PlaceSetObj(c, "O1", pc, x, zz, scale * SetBoulderScale * (big ? 1f : 0.8f) * (lit ? (big ? 1.05f : SetRockBig) : 1f), 0.62f, true, -1f, lit ? "O1r" : null);
        c.Tick("set boulders");
        c.Boulders.Add((new Vector2(x, zz), rx));
        return rx;
    }

    /// <summary>(round 10b) A painted object from a sheet (O1 boulders, O2 logs, O3 bone piles) on its half-ellipsoid
    /// proxy: ry is its height as a share of its half width (a boulder 0.62, a log 0.18, bones 0.1); the shadow-only hull
    /// for the tall ones. Returns the proxy's half width.</summary>
    static readonly float SetNoRepeat = SurvivorUnchained.Args.Num("den-set-norepeat", 1f);   // (den r15 R) 0: bank runs may lay one card twice in a row
    static readonly float SetRockVary = SurvivorUnchained.Args.Num("den-rock-vary", 1f);   // (den r15 R) 0: stones near each other may repeat one piece
    static readonly float SetRootK = SurvivorUnchained.Args.Num("den-root-k", 0.8f);   // (den r15 R, judge item 9) the 3D root tendrils (B6) read salmon: albedo L and C x this (linear scale this^3)
    static readonly int BigBoneCap = (int)SurvivorUnchained.Args.Num("den-bigbone-cap", 1f), SkullCap = (int)SurvivorUnchained.Args.Num("den-skull-cap", 1f);   // (den r15 Q) per camera footprint
    static readonly float BigBoneR = SurvivorUnchained.Args.Num("den-bigbone-r", 11f);
    static float PlaceSetObj(Ctx c, string sheet, SetPiece pc, float x, float zz, float k, float ryk, bool hull, float contact = -1f, string? key = null)
    {
        // (den r14 objects, item 4) the bone piles and logs vary: at most 2 deer skulls and 3 rib cages in a camera footprint
        // (DenCaps, ~9 m, the decals' kinds), never two of one log within 8 m; each mirrored, the piles turned about the card's middle
        bool mirror = false; float rot = 0f;
        // (den r15 helper D) a bone drift (O4) is a whole skeleton, skull and ribs: it takes from the same rib cage budget
        if (SetVary > 0f && sheet == "O4" && !(DenCaps.Take("bigbone", new Vector2(x, zz), BigBoneCap, BigBoneR) && DenCaps.Take("ribcage", new Vector2(x, zz), 3, 15f))) return 0f;   // (den r15 Q) one budget across kinds: BigBoneCap large bone pieces (rib cage, heap, drift) within BigBoneR
        if (SetVary > 0f && sheet is "O3" or "O2" && setSheets!.TryGetValue(sheet, out var vall))
        {
            var pp = new Vector2(x, zz);
            int ix = vall.IndexOf(pc);
            if (sheet == "O3")
            {
                // (den r15 helper D) every pile card is a skeleton: skull (ix 3) 2, rib cages (0, 2) 3, heaps (1, 4) 3 within a camera
                // footprint (DenCaps, shared with the decals' kinds); the rest is not laid here (flat litter takes its place)
                string? kind = ix == 3 ? "deer_skull" : ix is 0 or 2 ? "ribcage" : "pile";
                if (kind != "deer_skull" && !DenCaps.Take("bigbone", pp, BigBoneCap, BigBoneR)) return 0f;   // (den r15 Q) the large pieces share one budget
                if (!DenCaps.Take(kind == "deer_skull" ? "skull" : kind, pp, kind == "deer_skull" ? SkullCap : kind == "pile" ? 2 : 3, kind == "pile" ? 8f : 15f)) return 0f;
                float rr = Hash((int)(x * 17f), (int)(zz * 17f), 2202);
                rot = ix == 3 ? (rr - 0.5f) * 1.4f : ix == 0 ? (rr - 0.5f) * 3.4f : rr * Mathf.Tau;
            }
            else
            {
                for (int t = 0; t < vall.Count && !DenCaps.Take("log" + ix, pp, 1, 8f); t++) { ix = (ix + 1) % vall.Count; pc = vall[ix]; }
            }
            mirror = Hash((int)(x * 19f), (int)(zz * 19f), 2203) < 0.5f;
            k *= 0.88f + 0.3f * Hash((int)(x * 23f), (int)(zz * 23f), 2204);
        }
        // (den r15 R, R15 judge item 7: one stone twice, s11 corr) stones near each other (12 m) take different pieces of their size
        // class (big 0 and 3, small 1 and 2); a third is the same piece mirrored and 0.8 the size
        if (SetRockVary > 0f && sheet == "O1" && setSheets!.TryGetValue("O1", out var oall) && oall.Count == 4)
        {
            var pp = new Vector2(x, zz);
            int ix = oall.IndexOf(pc);
            if (ix >= 0)
            {
                int alt = ix switch { 0 => 3, 3 => 0, 1 => 2, _ => 1 };
                if (DenCaps.Take("rock" + ix, pp, 1, 12f)) { }
                else if (DenCaps.Take("rock" + alt, pp, 1, 12f)) { pc = oall[alt]; k *= oall[ix].Metres.X / pc.Metres.X; }
                else k *= 0.8f;
                mirror = Hash((int)(x * 19f), (int)(zz * 19f), 2213) < 0.5f;
            }
        }
        // (den r15 A, R14 judge item 6 "the pale cube rock") O1's flat-topped block (piece 2), cast on its proxy at the banks'
        // feet, drew a pale cube (s11 room 1790-1920,620-800): the plain O1 stones (lanes, alcoves) take the round mossed piece 1
        if (SetRockNoCube > 0f && sheet == "O1" && key == null && setSheets!["O1"].Count > 2 && setSheets["O1"].IndexOf(pc) == 2) pc = setSheets["O1"][1];
        float W = pc.Metres.X * k, Hr = pc.Metres.Y * k;
        float rx = 0.46f * W, ry = ryk * rx;
        float aa = CamUp.Y * ry, hm = 0.94f * Hr;
        float bb = Mathf.Max((hm * hm - aa * aa) / (2f * hm), 0.25f * rx);
        float rz = bb / -CamUp.Z;
        float y0 = H(c, x, zz);
        float yFront = new Vector3(x, y0, zz + rz).Dot(CamUp);
        bool domeOnly = SetRockDome > 0f && sheet == "O1";
        System.Func<float, float, float> surf = (px, pz) =>
        {
            float ex = (px - x) / rx, ez = (pz - zz) / rz;
            float e = 1f - ex * ex - ez * ez;
            float s = e > 0f && ry > 0f ? y0 + ry * Mathf.Sqrt(e) : -99f;
            // (r11) never more than 1.5 m under its own foot: over a pit's mouth the cast missed the floor and ran 120 m
            // down the view (seed 23's lair: a fan of streaks to the vanishing point)
            if (domeOnly) return Mathf.Max(Mathf.Max(s, H(c, px, pz)), y0 - 1.5f);   // (den r15 G) plain O1 stones: their own dome over the floor, never the rising bank (the pale cube)
            return Mathf.Max(Mathf.Max(s, SurfBank(c, px, pz)), y0 - 1.5f);
        };
        key ??= sheet;
        if (!objBufs.TryGetValue(key, out var buf)) objBufs[key] = buf = new SetBuf();
        int ob = buf.V.Count;
        const int nu = 16, nv = 14;
        float crot = Mathf.Cos(rot), srot = Mathf.Sin(rot), cyc = yFront + (pc.FootV - 0.5f) * Hr;
        float top = y0 + ry + 10f;
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float X = x + (u - 0.5f) * W, Y = yFront + (pc.FootV - v) * Hr;
                if (rot != 0f) { float ox = X - x, oy = Y - cyc; X = x + ox * crot - oy * srot; Y = cyc + ox * srot + oy * crot; }
                var q = SetCast(new Vector3(X, 0f, 0f) + CamUp * Y, surf, top);
                buf.V.Add(q - CamView * (ry > 0f ? 0.04f : 0.03f));
                buf.N.Add(Vector3.Up);
                float uu = mirror ? 1f - u : u;
                buf.U.Add(new Vector2(pc.Uv.Position.X + uu * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                buf.C.Add(new Color(1f, 1f, key == "O1r" && SetRockPaint <= 0f ? v : 0f, 1f));   // (den r14 objects) the lit boulders' shader wants the card's v
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
        // (den r14 objects, item 11) the cracked-mud hollows were stamps: clear of each other by two diameters, each its own size,
        // turned, its rim a noise outline (Fourier lobes 2-5)
        float hrot = 0f;
        if (sheet == "H1" && co.Length == 1 && SetHollowVary > 0f)
        {
            int hx = (int)(ctr.X * 11f), hz = (int)(ctr.Y * 11f);
            float hr0 = co[0] * (0.75f + 0.4f * Hash(hx, hz, 2401));
            foreach (var (q, qr) in laidHollows) if (q.DistanceTo(ctr) < 2f * (hr0 + qr) * SetHollowGap) return true;   // too near its neighbour: left out
            laidHollows.Add((ctr, hr0));
            var nc = new float[9]; nc[0] = hr0;
            for (int h = 2; h <= 5; h++) { float am = hr0 * (0.2f / h) * (0.5f + Hash(hx, hz, 2410 + h)); float ph = Hash(hx, hz, 2420 + h) * Mathf.Tau; nc[2 * h - 3] = am * Mathf.Cos(ph); nc[2 * h - 2] = am * Mathf.Sin(ph); }
            co = nc;
            hrot = Hash(hx, hz, 2402) * Mathf.Tau;
        }
        float sn = -CamUp.Z;   // a floor metre north draws this many metres up the camera's plane
        float W = pc.Metres.X, Hr = pc.Metres.Y, ma = pc.Mouth.Z * W, mb = pc.Mouth.W * Hr / sn;
        if (!objBufs.TryGetValue(sheet, out var buf)) objBufs[sheet] = buf = new SetBuf();
        int ob = buf.V.Count;
        // (r12) a hole in the boss lair glows green (den_boss.png): COLOR.a 0.5 marks it, and a green light low in it
        bool lairHole = false;
        foreach (var rr in c.Z.Rooms) if (rr.Kind == "Boss" && new Vector2(rr.X, rr.Z).DistanceTo(ctr) < rr.R + 4f) lairHole = true;
        // (den r13 rooms) one or two pits of the lair dark and empty (no glow, no light): the first, and the third on a seed-salted coin
        bool pitEmpty = false;
        if (lairHole && SurvivorUnchained.Args.Num("den-pit-empty", 0f) > 0f)
        {
            int pn = lairPits++;
            pitEmpty = pn == 0 || (pn == 2 && Hash((int)(ctr.X * 7f), (int)(ctr.Y * 7f), 1313) < 0.5f);
            GD.Print($"[den-lair] pit {pn} at {ctr.X:0.0},{ctr.Y:0.0} empty={pitEmpty}");
        }
        if (lairHole && !pitEmpty && SurvivorUnchained.Args.Num("den-pit-glow", 0.8f) > 0f)
            c.Root.AddChild(new OmniLight3D { Name = "PitGlow", Position = new Vector3(ctr.X, FloorY(c, ctr.X, ctr.Y) + 0.6f, ctr.Y),
                LightColor = new Color(0.62f, 0.95f, 0.5f), LightEnergy = SurvivorUnchained.Args.Num("den-pit-light", 0.7f), OmniRange = 4.5f, OmniAttenuation = 1.6f, ShadowEnabled = false });
        int nu = Mathf.Clamp(Mathf.CeilToInt(W / 0.3f) + 1, 8, 48), nv = Mathf.Clamp(Mathf.CeilToInt(Hr / 0.3f) + 1, 8, 48);
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                float u = (float)i / (nu - 1), v = (float)j / (nv - 1);
                float dx = (u - pc.Mouth.X) * W, dz = (v - pc.Mouth.Y) * Hr / sn;   // floor metres from the lip's centre (x east, z south)
                float th = Mathf.Atan2(dz, dx), cs = Mathf.Cos(th), si = Mathf.Sin(th);
                float rp = ma * mb / Mathf.Sqrt(mb * mb * cs * cs + ma * ma * si * si);
                float g = Mathf.Clamp(FourierAt(co, th) / Mathf.Max(rp, 0.05f), 0.15f, 4f);
                var off = new Vector2(dx, dz) * g;
                if (hrot != 0f) off = new Vector2(off.X * Mathf.Cos(hrot) - off.Y * Mathf.Sin(hrot), off.X * Mathf.Sin(hrot) + off.Y * Mathf.Cos(hrot));
                var w = ctr + off;
                buf.V.Add(new Vector3(w.X, FloorY(c, w.X, w.Y) + 0.05f, w.Y));
                buf.N.Add(Vector3.Up);
                buf.U.Add(new Vector2(pc.Uv.Position.X + u * pc.Uv.Size.X, pc.Uv.Position.Y + v * pc.Uv.Size.Y));
                // (r11) COLOR.b: half the painted point's distance from the lip's centre in lip radii (1 at the lip), so
                // den_set_soft fades the painting's own earth surround out past the rim (it read as a pink stamped ring)
                float ell = Mathf.Sqrt(dx * dx / Mathf.Max(ma * ma, 1e-4f) + dz * dz / Mathf.Max(mb * mb, 1e-4f));
                buf.C.Add(new Color(1f, 1f, Mathf.Clamp(0.5f * ell, 0f, 1f), lairHole && !pitEmpty ? 0.5f : 1f));
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
            int rw = 0, rl = 0, rn = 0, crowns = 0;   // (den r13 rooms) the lair's root-crowns (B6 spills) so far
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
                bool litRock = SetRockLit > 0f;
                string sheet = lair ? (got == 0 ? "O1" : u < (litRock ? 0.035f : 0.09f) ? "O1" : u < 0.16f ? "O2" : u < 0.42f ? "B6" : u < 0.56f ? "O4" : "O3") : u < (litRock ? 0.13f : 0.35f) ? "O1" : u < 0.5f ? "O2" : "O3";   // (r11: boulders and logs anywhere in the open, as den_room.png)
                if (lair && sheet == "B6" && SetLairCrowns > 0 && ++crowns > SetLairCrowns) { sheet = "O3"; crowns--; }   // (den r13 rooms) at most this many root-crowns in a lair, the rest small scatter
                if (!setSheets!.TryGetValue(sheet, out var all) || all.Count == 0) continue;
                var sorted = new List<SetPiece>(all);
                sorted.Sort((a, b) => a.Metres.X.CompareTo(b.Metres.X));
                // (stones and logs from the sheet's smaller half, a stone at most 1.6 m across: she walks through them)
                int half = Mathf.Max(1, sorted.Count / 2);
                var pc = sheet is "O3" or "B6" or "O4" ? sorted[(int)(q * sorted.Count) % sorted.Count] : sorted[(int)(q * half) % half];
                // (r11: a stone up to 2.4 m across, a log 3-4 m: they are cards, she walks through them; the room's
                // fight was tuned without them, so none has a body)
                if (lair && got == 0) pc = sorted[sorted.Count - 1];   // (the lair's hero stone: the sheet's biggest)
                float k2 = sheet == "O4" ? 0.55f + 0.25f * Hash(ri, k, 994) : sheet == "B6" ? 0.6f + 0.25f * Hash(ri, k, 994) : lair && got == 0 ? Mathf.Min(litRock ? 1.6f : 1.2f, (2.8f + 0.6f * Hash(ri, k, 994)) / pc.Metres.X) : sheet == "O1" ? Mathf.Min(litRock ? 1.6f : 1f, (1.6f + 0.8f * Hash(ri, k, 994)) * (litRock ? 1.5f : 1f) / pc.Metres.X) : sheet == "O2" ? 0.8f + 0.2f * Hash(ri, k, 994) : 0.9f + 0.3f * Hash(ri, k, 994);
                // (r11) the lair's roots over its floor, as den_boss.png's: a spill under the hero stone, more through the open
                if (lair && got == 0 && SetPick("B6", Hash(ri, k, 988)) is SetPiece hs && ++crowns > 0)
                    PlaceSetObj(c, "B6", hs, p.X, p.Y + 0.4f, 0.85f, 0f, false, 0f);
                if (sheet is "B6" or "O4") PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O4" ? 0.1f : 0f, false, sheet == "O4" ? 0.3f : 0f);
                else PlaceSetObj(c, sheet, pc, p.X, p.Y, k2, sheet == "O1" ? 0.62f : sheet == "O2" ? 0.18f : 0.1f, sheet == "O1", -1f, sheet == "O1" && litRock ? "O1r" : null);
                taken.Add(p); got++; n++;
                // (r11) blood (O5) by a kill's bones, and now and then on its own nearby (den_room.png's splashes and drags)
                if (lair ? Hash(ri, k, 995) < SetLairBlood : Hash(ri, k, 995) < SetRoomBlood)   // (den r15 S: the room's O3 pile always dragged a flat puddle; now by chance)
                {
                    float ba = Hash(ri, k, 996) * Mathf.Tau, bd = 0.9f + 0.8f * Hash(ri, k, 997);
                    var bp = p + new Vector2(Mathf.Cos(ba), Mathf.Sin(ba)) * bd;
                    if (Wall(c, bp.X, bp.Y) > 1.0f && Hole(c, bp.X, bp.Y) > 1.5f && SetPick("O5", Hash(ri, k, 998)) is SetPiece bpc)
                    { PlaceSetObj(c, "O5", bpc, bp.X, bp.Y, SetBloodK * (1.1f + 0.5f * Hash(ri, k, 999)), 0f, false, 0f); c.Tick("set blood"); }
                }
            }
            if (lair && SetLairFungus > 0f) SetLairDress(c, r, ri, taken);
            GD.Print($"SetOpen {r.Kind} room ({r.X:0.0}, {r.Z:0.0}) R {r.R:0.0}: {got}/{want}{(lair ? $", root-crowns {crowns}" : "")}, off the floor {rw}, in a lane {rl}, crowded {rn}");
        }
        c.Count["set open"] = n;
    }

    static readonly float SetHollowVary = SurvivorUnchained.Args.Num("den-hollow-vary", 1f);   // (den r14 objects, item 11) hollows: noise outline, size, turn
    static readonly float SetHollowGap = SurvivorUnchained.Args.Num("den-hollow-gap", 1f);     // (1 = two diameters between centres)
    static readonly List<(Vector2 P, float R)> laidHollows = new();
    static readonly float SetRoomBlood = SurvivorUnchained.Args.Num("den-room-blood", 0.3f);   // (den r15 S) a room pick's chance of a blood splash
    static readonly float SetBloodK = SurvivorUnchained.Args.Num("den-blood-k", 0.7f);   // (den r15 S) splash size x: smaller cores, not flat puddles
    static readonly float SetLairBlood = SurvivorUnchained.Args.Num("den-lair-blood", 0.12f);   // (den r15 lead) a lair pick's chance of a blood splash (was: every bone pile plus 0.6 of the rest: red smears all over the s23 lair)
    static readonly float SetLairFungus = SurvivorUnchained.Args.Num("den-lair-fungus", 0f);   // (den r15 Q, judge r15 item 1) off: the 3D clusters read as toppled teal pills; the root crowns carry painted glow caps.    // (den r14 objects, item 13) glow-fungus clusters on the lair's pit rims (0 off)
    static readonly float SetLairRoots = SurvivorUnchained.Args.Num("den-lair-roots", 3f);     // root tendrils (B6) laid between its pits

    /// <summary>(den r14 objects, item 13) The lair's middle had no fungus and its pits stood bare: root tendrils (B6, cards
    /// that block nothing) laid between the pits and glow-fungus clusters on the pit rims (the Fungus() mushrooms and cool light).</summary>
    static void SetLairDress(Ctx c, (float X, float Z, float R, string Kind) r, int ri, List<Vector2> taken)
    {
        var rc = new Vector2(r.X, r.Z);
        var pits = new List<(Vector2 P, float R)>();
        foreach (var (p, rad, _) in DenPits(c)) if (p.DistanceTo(rc) < r.R + 4f) pits.Add((p, rad));
        int roots = 0, fung = 0;
        for (int i = 0; i < pits.Count && roots < (int)SetLairRoots; i++)
            for (int j = i + 1; j < pits.Count && roots < (int)SetLairRoots; j++)
            {
                float d = pits[i].P.DistanceTo(pits[j].P);
                if (d > 30f) continue;
                var m = pits[i].P.Lerp(pits[j].P, 0.4f + 0.2f * Hash(ri, i, 2315)) + new Vector2(Hash(ri, i * 9 + j, 2301) - 0.5f, Hash(ri, i * 9 + j, 2302) - 0.5f) * 1.5f;
                if (Wall(c, m.X, m.Y) < 1.8f || Hole(c, m.X, m.Y) < 1.0f || SetPick("B6", Hash(ri, i * 9 + j, 2303)) is not SetPiece bp) continue;
                PlaceSetObj(c, "B6", bp, m.X, m.Y, 0.5f + 0.2f * Hash(ri, i, 2304), 0f, false, 0f);
                roots++;
            }
        int want = Mathf.RoundToInt(SetLairFungus);
        for (int k = 0; k < 40 && fung < want && pits.Count > 0; k++)
        {
            var (pp, pr) = pits[k % pits.Count];
            float a = Hash(ri, k, 2305) * Mathf.Tau, dd = pr * (1.2f + 0.3f * Hash(ri, k, 2306)) + 0.6f;
            var cp = pp + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * dd;
            if (Wall(c, cp.X, cp.Y) < 1.5f || Hole(c, cp.X, cp.Y) < 0.3f) continue;
            bool near = false;
            foreach (var t in taken) if (t.DistanceTo(cp) < 1.5f) near = true;
            if (near) continue;
            int mn = 7 + (int)(Hash(ri, k, 2307) * 5);
            for (int q = 0; q < mn; q++)
            {
                float ma = Hash(ri, k * 13 + q, 2308) * Mathf.Tau, md = Mathf.Sqrt(Hash(ri, k * 13 + q, 2309)) * 0.55f;
                float x = cp.X + Mathf.Cos(ma) * md, zz = cp.Y + Mathf.Sin(ma) * md;
                if (Wall(c, x, zz) < 0.05f || Hole(c, x, zz) < 0.2f) continue;
                float sh = 0.12f + 0.24f * Hash(ri, k * 13 + q, 2310), sr = 0.025f + 0.025f * Hash(ri, k * 13 + q, 2311), cr = (0.07f + 0.11f * Hash(ri, k * 13 + q, 2312)) * FungCapK;   // (den r15 Q) the room fungus's small upright caps (was tall stems, big caps: toppled teal pills)
                var basis = Basis.Identity;   // (den r15 Q) upright
                var t = new Transform3D(basis, new Vector3(x, H(c, x, zz), zz));
                c.Shrooms.AppendFrom(new CylinderMesh { TopRadius = sr, BottomRadius = sr, Height = sh, RadialSegments = 6, Rings = 1 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh / 2, 0)));
                c.Shrooms.AppendFrom(new SphereMesh { Radius = cr, Height = cr * (0.8f + 0.5f * Hash(ri, k * 13 + q, 2315)), IsHemisphere = true, RadialSegments = 16, Rings = 6 }, 0, t * new Transform3D(Basis.Identity, new Vector3(0, sh, 0)));
            }
            c.Root.AddChild(new OmniLight3D { Name = "FungusLight", LightColor = FungLightCol, LightEnergy = FungLightE, OmniRange = 2.6f, ShadowEnabled = false, Position = new Vector3(cp.X, H(c, cp.X, cp.Y) + 0.5f, cp.Y) });
            c.Clusters++; fung++; taken.Add(cp);
        }
        GD.Print($"SetLairDress: {pits.Count} pits (dist {(pits.Count > 1 ? pits[0].P.DistanceTo(pits[1].P) : 0f):0.0}), {roots} root tendrils, {fung} fungus clusters");
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
