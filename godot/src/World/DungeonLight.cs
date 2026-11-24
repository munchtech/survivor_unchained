using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A dungeon's own light, placed by rule per room of its graph (ZoneData.Rooms). The den is lit from no sky: what light
/// there is falls in pale shafts through holes in the roof, one or two to a room (a spot on the floor and the shaft
/// itself in the air, shaders/dungeon_shaft.gdshader), all slanting one way as if from the one sun above the hill.
/// The ravine's light is its rig's low sun (rigs.json "ravine"); it places nothing here.
/// </summary>
public static class DungeonLight
{
    /// <summary>The shafts' slant, from straight down toward -x and +z (the one sun's side).</summary>
    static readonly Vector3 Axis = new Vector3(SurvivorUnchained.Args.Num("den-shaft-lean", 0.3f), -1f, 0.42f).Normalized();  // (the roof hole north of the pool: from the play camera the shaft climbs up the screen)
    const float Height = 15f;
    static readonly float PoolWide = SurvivorUnchained.Args.Num("den-pool-wide", 1.5f), PoolSoft = SurvivorUnchained.Args.Num("den-pool-soft", 0.7f), PoolEnergy = SurvivorUnchained.Args.Num("den-pool-energy", 8f), PackFill = SurvivorUnchained.Args.Num("den-pack-fill", 4.5f), BossPool = SurvivorUnchained.Args.Num("den-boss-pool", 1.5f);

    // (real light lane, 23 Nov 2026; the owner: "so use what real shipped games would use and stop trying to force the light.
    // it can have paint but an actual light too") --den-real-light 1: a pool is what a real light does to the floor. The shaft's
    // spot carries the roof gap as a projected texture (DenCookie) and casts shadows, so what stands in the pool throws one;
    // the air in the shaft is a cone of fog the same light scatters in (the volumetric fog the High tier already pays for).
    // The light is ADDED (the owner's check, 23 Nov: "the new lighting isn't coming at the cost of having other things painted
    // right?"): the rig, the rooms' wash and the painted fan rays stay as they are (--den-rl-wash, --den-rl-fan scale them); and so
    // does the floor's painted pool (sp_*; --den-rl-mask 0 drops it: the lair's floor then changes well outside the light).
    // (cool shade lane, 23 Nov: the owner said yes to the den's shade going cool violet) --den-shade 1 (DenShade) turns the real
    // light on with it, unless --den-real-light 0 says otherwise: the pool reads as sun by its temperature, not by its energy.
    static readonly bool Real = SurvivorUnchained.Args.Num("den-real-light", DenShade.On ? 1f : 0f) > 0f;
    static readonly float RlEnergy = DenShade.Num("den-rl-energy", 28f, 12f), RlR = DenShade.Num("den-rl-r", 2.1f, 1.65f), RlFog = SurvivorUnchained.Args.Num("den-rl-fog", 1f),
        RlWash = DenShade.Num("den-rl-wash", 0f, 1f), RlFan = SurvivorUnchained.Args.Num("den-rl-fan", 0.8f), RlShaft = SurvivorUnchained.Args.Num("den-rl-shaft", 0f), RlLair = DenShade.Num("den-rl-lair", 1.5f, 0.65f);   // (judge 3: 0.8 -> 0.65)
    // (cool shade lane) under the real light: today's soft spot x --den-rl-soft (the lair's x --den-rl-lair-soft) and the lair's
    // painted floor pool x --den-rl-lair-paint (judge 3: "the yellow comes from today's painted pool there, and the real light
    // multiplies it").
    static readonly float RlSoft = DenShade.Num("den-rl-soft", 0f, 1f), RlLairSoft = DenShade.Num("den-rl-lair-soft", 0f, 1f),   // (under the shade a warm soft glow on violet is a pink halo: none)
        RlLairPaint = DenShade.Num("den-rl-lair-paint", 0f, 0.5f),
        // (cool shade lane) --den-rl-paint 0: no painted pool on the floor under the real light (the decals still fade inside the
        // pools). Under the cool shade the painted pool is an albedo gain lit by violet: a pink-lilac halo round the gold.
        RlPaint = DenShade.Num("den-rl-paint", 0f, 1f);
    static int realN;
    static readonly System.Collections.Generic.List<Vector3> realFeet = new();

    public static Node3D? Build(ZoneData z)
    {
        if (z.DungeonTheme != "den" || z.Rooms.Count == 0) return null;
        Salt = z.Seed == 0 ? 0 : z.Seed * 40503 + 17;
        var root = new Node3D { Name = "DungeonLight" };
        var shader = GD.Load<Shader>("res://shaders/dungeon_shaft.gdshader");
        HoleTex = null;
        if (z.HoleField != null && SurvivorUnchained.Args.Num("den-shaft-pitmask", 1f) > 0f)   // (r15) the veil is masked off over pits
        {
            var px = new byte[z.Res * z.Res];
            for (int q = 0; q < px.Length; q++) px[q] = (byte)Mathf.Clamp(Mathf.Round((z.HoleField[q] + 4f) / 8f * 255f), 0f, 255f);
            HoleTex = ImageTexture.CreateFromImage(Image.CreateFromData(z.Res, z.Res, false, Image.Format.R8, px));
            HoleMap = new Vector3(-z.Half - 0.5f * z.Step, -z.Half - 0.5f * z.Step, 1f / (z.Res * z.Step));
        }
        int i = 0; fanN = 0; realN = 0; realFeet.Clear(); Pools.Clear();
        // (cool shade lane) the projected gap keeps its crisp stretch: linear, no mipmaps (with them every edge landed 20+ px soft
        // at the game camera). Only the den's pools use a light projector (--den-rl-proj-filter 3: the engine's default).
        if (Real) RenderingServer.LightProjectorsSetFilter((RenderingServer.LightProjectorFilter)(int)SurvivorUnchained.Args.Num("den-rl-proj-filter", 1f));
        // (den r16 B2, R15f item 2) the lair's painted hollows are no holes: the fans keep off them and mask them (--den-shaft-hollows 0: not)
        Hollows = Fan > 0f && SurvivorUnchained.Args.Num("den-shaft-hollows", 1f) > 0f ? DungeonDress.HollowsFor(z) : new();
        var feet = new System.Collections.Generic.List<Vector2>();   // (den r16 B) every shaft's foot: the corridors' spacing, the log
        foreach (var r in z.Rooms)
        {
            i++;
            if (r.Kind == "Bend") continue;
            // One shaft to a room, two in a big one, three in the boss lair; off its centre so the fight is not always in the spot.
            int count = SurvivorUnchained.Args.Num("den-shafts", 1f) <= 0f ? 0 : r.Kind == "Boss" ? (int)SurvivorUnchained.Args.Num("den-shaft-boss", 2f) : r.R > 11 ? 2 : 1;   // (den r16 B: the lair 3 -> 2, R15f "1-2 a screen")   // (the lair three: round 6, its open floor read as one empty stretch)
            for (int k = 0; k < count; k++)
            {
                // (clear of the pits and the walls: a shaft down a pit lit its roots bone-white)
                float x = r.X, zz = r.Z;
                if (r.Kind == "Boss" && LairOpen > 0f && LairFoot(z, r, i, k, feet, out x, out zz)) { }
                else for (int t = 0, tries = r.Kind == "Boss" && LairBeamClear > 0f ? 40 : 10; t < tries; t++)   // (den r19 L2, R18b item 4: 40 hashed tries in the lair, the beam clear of fires, crowns and tusks)
                {
                    float a = Hash(i, k + 7 * t, 1) * Mathf.Tau, d = (r.Kind == "Boss" ? 3f + 5f * Hash(i, k + 7 * t, 2) : r.R * ( 0.25f + 0.35f * Hash(i, k + 7 * t, 2)));   // (r11: the lair's pools in its middle frame)
                    x = r.X + Mathf.Cos(a) * d; zz = r.Z + Mathf.Sin(a) * d;
                    if (r.Kind == "Boss" && LairBeamClear > 0f && t < tries - 1 && FallbackFireInBeam(z, r, x, zz)) continue;   // (den r19 L, R18b item 4) no fire in the beam's quad (the last try is kept)
                    if (At(z, z.WallField!, x, zz) > 2.5f && (z.HoleField == null || At(z, z.HoleField, x, zz) > 3f) && !NearHollow(x, zz, 1.8f)) break;
                }
                float w = 1.6f + 1.4f * Hash(i, k, 3);   // (r11 judge: broad beams, 150-250 px; was 1.1 + 1.0)
                if (k == 0 && r.Kind != "Boss") AddWash(root, r.X, z.HeightAt(r.X, r.Z), r.Z, r.R, i);
                feet.Add(new Vector2(x, zz));
                AddShaft(root, shader, new Vector3(x, z.HeightAt(x, zz), zz), w, r.Kind == "Boss" ? BossPool : PoolWide, r.Kind == "Boss");
            }
        }
        int roomFans = feet.Count;
        AddCorridorFans(root, z, feet);
        var fl = new System.Text.StringBuilder(); foreach (var f in feet) fl.Append($" ({f.X:F1},{f.Y:F1})");
        GD.Print($"DungeonLight fans: {roomFans} in rooms, {feet.Count - roomFans} in corridors:{fl}");
        if (PoolFloor > 0f && Fan > 0f && (!Real || SurvivorUnchained.Args.Num("den-rl-mask", 1f) > 0f)) root.TreeEntered += () => FloorPools(root);
        // (round 8, 15 Nov) The pack reads in the den's light: the wolves' dark fur under a dim key read as black
        // silhouettes (round 7's "black fragments" by the big pit were the resting pack). A fill from the camera's side,
        // high, that reaches the crowd's own layer only (PlayerView.CrowdLayer): the floor, the banks and HER take none of
        // it (her merged skin light is untouched). --den-pack-fill sets its energy (0 off).
        // (r11) 4 -> 7.5: the Pack-Mother's fur read at 0.4 of the lair floor's value (p25 30 against 75), a dark cut-out; 9 gave 0.68.
        // (demo-look item 4: with the den rig's own pack look, rigs.json "foe_den", no pack fill: its cool light lifted the body to
        // L 0.40 at h 19 against the bar's 0.20-0.36 at 10-50; --den-pack-fill still sets it)
        float packFill = SurvivorUnchained.Args.Get("den-pack-fill") == null && SurvivorUnchained.Look.Rigs.Current["den"] is { FoeDen: not null } ? 0f : PackFill;
        if (packFill > 0f)
            root.AddChild(new DirectionalLight3D
            {
                Name = "pack_fill",
                Transform = new Transform3D(Basis.LookingAt(new Vector3(0.25f, -0.75f, -0.6f).Normalized(), Vector3.Up), Vector3.Zero),
                LightColor = new Color(SurvivorUnchained.Args.Get("den-pack-fill-colour") ?? "a8b8d8"),   // (r11 judge: her fur read in the floor's own hue at 0.78 of it; cool and lower)
                LightEnergy = packFill,
                LightCullMask = PlayerView.CrowdLayer,
                ShadowEnabled = false,
                LightSpecular = 0.3f,
            });
        DungeonDress.Placed.Clear(); DungeonDress.Tusks.Clear(); DungeonDress.Stones.Clear();   // (den r18 L3) read; the next zone starts empty
        GD.Print($"DungeonLight {z.DungeonTheme}: {root.GetChildCount() / 2} shafts over {z.Rooms.Count} rooms");
        return root;
    }

    static float At(ZoneData z, float[] f, float x, float zz)
    {
        int i = Mathf.Clamp((int)Mathf.Round((x + z.Half) / z.Step), 0, z.Res - 1), j = Mathf.Clamp((int)Mathf.Round((zz + z.Half) / z.Step), 0, z.Res - 1);
        return f[j * z.Res + i];
    }

    static ImageTexture? HoleTex;
    static Vector3 HoleMap;

    // (den r19 L2, R18b item 1) the pool's spot: its energy x --den-pool-spot (.6: the pools' dL was +.23-.29 against the target +.15-.18, most of it this light, not the floor albedo lift)
    static readonly float PoolSpot = SurvivorUnchained.Args.Num("den-pool-spot", 0.6f), CorrSpot = SurvivorUnchained.Args.Num("den-pool-corr-spot", 0.4f);
    static void AddSpot(Node3D root, Vector3 foot, float w, float pool, bool lair, float k)
    {
        var top = foot - Axis * Height;
        var basis = Basis.LookingAt(Axis, Mathf.Abs(Axis.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        // (judge 1) one gap, one projected light: the lair's two shafts land half a metre apart, and two outlines laid over each
        // other are a pool with no edge (115-170 px against a room's 25-55)
        if (Real && !realFeet.Exists(f => f.DistanceTo(foot) < SurvivorUnchained.Args.Num("den-rl-apart", 2f)))
        {
            realFeet.Add(foot);
            int v = ++realN;
            float r = RlR * (0.9f + 0.25f * Hash(v, 5, 41));
            root.AddChild(new SpotLight3D
            {
                Name = "shaft_light",
                Transform = new Transform3D(basis.Rotated(Axis, CookieTurn(basis, v, lair)), top),   // each pool's gap turned its own way, its crisp stretch where it is seen
                LightColor = new Color(SurvivorUnchained.Args.Get("den-rl-colour") ?? (DenShade.On ? "ff900c" : "fff4e6")),   // (under the shade the light carries the gold: near-white on the violet-lit floor landed pink, hue 358)
                LightEnergy = RlEnergy * (lair ? RlLair : 1f),
                SpotRange = Height + 12f,   // the floor well inside the range's roll-off: the pool is even
                SpotAngle = Mathf.RadToDeg(Mathf.Atan(r * 1.25f / Height)),
                SpotAngleAttenuation = 8f,   // flat across the cone: the cookie is the pool's edge
                SpotAttenuation = 0.2f,
                ShadowEnabled = true,   // (a projector needs it; and things in the pool cast a shadow)
                ShadowBias = SurvivorUnchained.Args.Num("den-rl-shadow-bias", 0.06f), ShadowNormalBias = 1f, ShadowBlur = SurvivorUnchained.Args.Num("den-rl-shadow-blur", 1f),
                LightProjector = SurvivorUnchained.Args.Num("den-rl-cookie", 1f) > 0f ? DenCookie.Get((int)(Hash(v, 7, 43) * DenCookie.Variants)) : null,
                LightSpecular = 0f,
                LightVolumetricFogEnergy = RlFog,
            });
            AddFogShaft(root, foot, r * 1.25f);
            // (no return: today's soft spot below stays, the broad glow round the pool is its; the gap's light is added to it)
        }
        var spot = new SpotLight3D
        {
            Name = "shaft_light",
            Transform = new Transform3D(basis, top),
            LightColor = new Color(SurvivorUnchained.Args.Get("den-pool-colour") ?? (lair ? "ffdc8a" : "ffdea0")),   // (r12: 13 / ffd2a0 -> 8 / ffc890 and the beams .22 -> .18: the room median 54 -> 51, lit (151,107,89) -> (133,98,83) against (134,95,73))   // (round 8: warmer, den_room.png's pools (134,95,73); ffe2b8 read pale beige)
            LightEnergy = k * PoolSpot * PoolEnergy * (lair ? SurvivorUnchained.Args.Num("den-lair-pool", 0.73f) : 1f) * (Real ? (lair ? RlLairSoft : RlSoft) : 1f),   // (r12) the lair's pools against its floor (lit/median 109/68 in den_boss.png)   // (round 8: --den-pool-energy) (lead 6: 12 lifted the boss frame to 85; 6 left rooms at 35; warm 9 in the pools only, round 6; 16 moved the room median 36 -> 36: the pools are too small a share of the frame)
            SpotRange = Height + 4f,
            SpotAngle = Mathf.RadToDeg(Mathf.Atan((w * 1.25f * pool) / Height)),
            SpotAngleAttenuation = pool > 1f ? PoolSoft : 1.2f,   // (round 7: the rooms' pools 1.5x wider and softer-edged, the room's centre warm mid-brown; the lair keeps its own)
            SpotAttenuation = 0.4f,
            ShadowEnabled = false,
            LightSpecular = 0.2f,
        };
        root.AddChild(spot);
    }

    /// <summary>(cool shade lane; judge 3: "one crisp stretch of edge", "the root crosses the middle") The turn of a light about its
    /// shaft that puts its cookie's +x (the crisp stretch; the trunk runs across it) toward --den-rl-turn-to on the floor (x,z;
    /// screen right and a little down: the painted rays land on the pool's upper left and would lie over the edge there), give or
    /// take --den-rl-turn-jit degrees a light; --den-rl-turn adds a turn to all, --den-rl-lair-turn to the lair's.</summary>
    static float CookieTurn(Basis basis, int v, bool lair)
    {
        var to = DungeonDress.V3("den-rl-turn-to", new Vector3(1f, 0f, 0.35f));
        var d = new Vector3(to.X, 0f, to.Z).Normalized();
        d = (d - Axis * d.Dot(Axis)).Normalized();   // onto the plane across the shaft
        float a = Mathf.Atan2(d.Dot(Axis.Cross(basis.X)), d.Dot(basis.X));
        float jit = Mathf.DegToRad(SurvivorUnchained.Args.Num("den-rl-turn-jit", 30f)) * (Hash(v, 6, 42) * 2f - 1f);
        return a + jit + Mathf.DegToRad(SurvivorUnchained.Args.Num("den-rl-turn", 0f) + (lair ? SurvivorUnchained.Args.Num("den-rl-lair-turn", 0f) : 0f));
    }

    static void AddShaft(Node3D root, Shader shader, Vector3 foot, float w, float pool, bool lair = false)
    {
        var top = foot - Axis * Height;
        var basis = Basis.LookingAt(Axis, Mathf.Abs(Axis.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        // The light: a spot from the roof's hole, its cone just the shaft's width on the floor.
        AddSpot(root, foot, w, pool, lair, 1f);
        if (Real && RlFan <= 0f) return;
        if (Fan > 0f) { AddFan(root, foot, lair); return; }
        // The shaft in the air: a soft cone, brightest a little above the floor and gone toward the roof.
        var mesh = new CylinderMesh { TopRadius = w * 0.55f, BottomRadius = w, Height = Height, RadialSegments = 20, Rings = 1, CapTop = false, CapBottom = false };
        var mat = new ShaderMaterial { Shader = shader };
        mat.SetShaderParameter("height", Height);
        if (lair) mat.SetShaderParameter("tint", new Color(SurvivorUnchained.Args.Get("den-lair-veil") ?? "c8dcf0"));   // (r15b: cool additive streaks)
        mat.SetShaderParameter("veil_cut", SurvivorUnchained.Args.Num("den-veil-cut", 0.75f));
        mat.SetShaderParameter("floor_fade", SurvivorUnchained.Args.Num("den-veil-floor", 1.0f));
        if (HoleTex != null) { mat.SetShaderParameter("hole_tex", HoleTex); mat.SetShaderParameter("hole_map", HoleMap); }
        if (!lair) mat.SetShaderParameter("tint", new Color(SurvivorUnchained.Args.Get("den-room-veil") ?? "c8dcf0"));   // (r15: yellow-white, h 60-70, so the room pools move toward ochre)
        // (den r15 lead: at .5 / x1.6 and b4ecff the streak cores were cyan lasers, +.24-.34 L at C .07-.09; now +.09-.15, C .03, h 216-245)
        mat.SetShaderParameter("strength", SurvivorUnchained.Args.Num("den-shaft-strength", 0.26f) * (lair ? DenShade.Num("den-lair-shaft", 0.66f, 1.1f) : 1f));   // (r12: the lair's beams did not read over its bright floor)
        var mid = foot - Axis * (Height * 0.5f);
        // CylinderMesh stands along +y: turn +y to the shaft's upward axis (-Axis).
        var up = -Axis;
        var side = up.Cross(Vector3.Back).Normalized();
        var b = new Basis(side, up, side.Cross(up).Normalized());
        root.AddChild(new MeshInstance3D { Name = "shaft", Mesh = mesh, MaterialOverride = mat, Transform = new Transform3D(b, mid), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
    }

    /// <summary>(real light lane) The air in the shaft: a cone of fog as wide as the spot's cone, its tip at the light, so the
    /// volumetric fog shows the beam there and nowhere else. --den-rl-shaft: its density (0: none); --den-rl-shaft-h: how far
    /// up from the floor it stands (m).</summary>
    static void AddFogShaft(Node3D root, Vector3 foot, float rFoot)
    {
        if (RlShaft <= 0f) return;
        float h = Mathf.Min(SurvivorUnchained.Args.Num("den-rl-shaft-h", 9f), Height);
        var up = -Axis;
        var side = up.Cross(Vector3.Back).Normalized();
        var b = new Basis(side, up, side.Cross(up).Normalized());
        var mat = new FogMaterial
        {
            Density = RlShaft, Albedo = new Color(SurvivorUnchained.Args.Get("den-rl-shaft-albedo") ?? "ffffff"),
            EdgeFade = SurvivorUnchained.Args.Num("den-rl-shaft-edge", 0.15f), HeightFalloff = SurvivorUnchained.Args.Num("den-rl-shaft-fall", 0f),
        };
        // (a cone of the full height, its tip at the light; cut short it would be a blunt cylinder end in the air)
        root.AddChild(new FogVolume
        {
            Name = "shaft_fog", Shape = RenderingServer.FogVolumeShape.Cone, Size = new Vector3(2f * rFoot, Height, 2f * rFoot) * new Vector3(1f, h / Height, 1f),
            Material = mat, Transform = new Transform3D(b, foot + up * (h * 0.5f)),
        });
    }

    // (den r16 B, R15f item 2) The shaft as den_room.png has it: a fan of 3-5 rays from a bright gap ~8 m up, landing in a soft
    // pool (shaders/dungeon_shaft_fan.gdshader). --den-shaft-fan 0: r15's cylinder veil. --den-shaft-corr 0: none in the corridors.
    static readonly float Fan = SurvivorUnchained.Args.Num("den-shaft-fan", 1f);
    static ArrayMesh? fanMesh;
    static int fanN;
    static System.Collections.Generic.List<(Vector2 p, float r, int v)> Hollows = new();
    static bool NearHollow(float x, float zz, float m) { foreach (var h in Hollows) if (h.p.DistanceTo(new Vector2(x, zz)) < h.r + m) return true; return false; }
    // (den r17 L, R16 item 2) The pools as light on the floor's albedo (dungeon_floor.gdshader sp_*), each at its fan's foot, in
    // place of the fan's additive sprite; --den-pool-floor 0: the r16 sprite. --den-shaft-foot 0: the rays fade out halfway down
    // (r16: each pool sat ~250 px below its shaft's end); 1: they run to the foot and end in the pool.
    static readonly float PoolFloor = SurvivorUnchained.Args.Num("den-pool-floor", 1f), ShaftFoot = SurvivorUnchained.Args.Num("den-shaft-foot", 1f);
    static readonly bool Smooth = SurvivorUnchained.Args.Num("den-pool-smooth", 1f) > 0f;
    static readonly float PoolR = SurvivorUnchained.Args.Num("den-pool-r", 1.25f);
    // (den r17 L, R16 item 4) the lair's shafts over its open floor, off her and the Pack-Mother in its middle (LairFoot);
    // 0: r16's hashed spots 3-8 m out (s11 a stub on a boulder, s23 one among the root spurs)
    static readonly float LairKeepOff = SurvivorUnchained.Args.Num("den-lair-keepoff", 2.2f);
    static readonly float LairOpen = SurvivorUnchained.Args.Num("den-lair-open", 1f);
    static readonly System.Collections.Generic.List<Vector4> Pools = new();

    static void FloorPools(Node3D root)
    {
        if (root.GetParent() is not Node p) return;
        foreach (var ch in p.GetChildren())
        {
            if (ch is not MeshInstance3D mi || mi.Mesh == null || mi.Mesh.GetSurfaceCount() == 0) continue;
            var m = mi.MaterialOverride as ShaderMaterial ?? mi.Mesh.SurfaceGetMaterial(0) as ShaderMaterial;
            if (m?.Shader != null && m.Shader.ResourcePath.EndsWith("dungeon_decal.gdshader"))   // (den r19 L, R18b item 3) the decals fade inside the pools: the floor's pool list and mask
            {
                var da = new Vector4[64]; int dn = System.Math.Min(64, Pools.Count);
                for (int q = 0; q < dn; q++) da[q] = Pools[q];
                m.SetShaderParameter("sp", da); m.SetShaderParameter("sp_n", dn);
                m.SetShaderParameter("sp_lean", new Vector2(-Axis.X, -Axis.Z).Normalized());
                m.SetShaderParameter("sp_soft", SurvivorUnchained.Args.Num("den-pool-soft2", 0.7f));
                m.SetShaderParameter("sp_lair", SurvivorUnchained.Args.Num("den-pool-lair", 0.6f));
                m.SetShaderParameter("sp_fade", SurvivorUnchained.Args.Num("den-pool-decal", 1f));   // (den r19 L) decal alpha x (1 - pool mask); 0: r18
                continue;
            }
            if (m?.Shader == null || !m.Shader.ResourcePath.EndsWith("dungeon_floor.gdshader")) continue;
            var arr = new Vector4[64]; int n = System.Math.Min(64, Pools.Count);
            for (int q = 0; q < n; q++) arr[q] = Pools[q];
            m.SetShaderParameter("sp", arr); m.SetShaderParameter("sp_n", Real && RlPaint <= 0f ? 0 : n);
            m.SetShaderParameter("sp_lean", new Vector2(-Axis.X, -Axis.Z).Normalized());
            m.SetShaderParameter("sp_gain", SurvivorUnchained.Args.Num("den-pool-gain", Smooth ? 2.0f : 2.1f));   // (den r17 lead, from l7c: 1.5 -> 1.95, pools dL +.11 at s11 room)   // (den r17 L2, R16 item 2: 2.1 with ref .09: l7f at 2.2 dL +.15-.28)
            m.SetShaderParameter("sp_edge", SurvivorUnchained.Args.Num("den-pool-edge", 0.3f));
            m.SetShaderParameter("sp_grain", SurvivorUnchained.Args.Num("den-pool-grain", Smooth ? 1.05f : 1.0f));   // (den r19 L, R18b item 3: .5 -> 1.05 with the blur off, the lit floor keeps its texture)   // (den r17 L2, R16 item 2: .5 -> 1, texture .9-1.2 at .9)
            m.SetShaderParameter("sp_lair", SurvivorUnchained.Args.Num("den-pool-lair", 0.6f) * (Real ? RlLairPaint : 1f));   // (den r17 L2: l7g's lair pools at full strength read as glowing yellow discs on its brighter floor)
            m.SetShaderParameter("sp_smooth", Smooth ? 1f : 0f);   // (den r18 L3, R17 items 2, 3: the pool mask, gain and cap, and the shaft tint h 205-225) a smooth multiplying mask, gain soft-capped; 0: r17
            m.SetShaderParameter("sp_cap", SurvivorUnchained.Args.Num("den-pool-cap", 0.14f));
            m.SetShaderParameter("sp_knee", SurvivorUnchained.Args.Num("den-pool-knee", 0.6f));
            m.SetShaderParameter("sp_blur", SurvivorUnchained.Args.Num("den-pool-blur", 0f));   // (den r19 L, R18b item 3: .5 -> 0) // (den r18 L4, R18 item 3) the grain toward its blurred self inside the pool; 0: r18 L3
            m.SetShaderParameter("sp_norm", SurvivorUnchained.Args.Num("den-pool-norm", 1f));   // (den r18 L4, R18 item 3) the gain per pool against its own floor, lifting it by den-pool-dl; 0: the flat gain
            m.SetShaderParameter("sp_gmin", SurvivorUnchained.Args.Num("den-pool-gmin", 1.3f));   // (den r19 L2) 1.3 = r19 wave 1
            m.SetShaderParameter("sp_dl", SurvivorUnchained.Args.Num("den-pool-dl", 0.15f));
            m.SetShaderParameter("sp_blur_lod", SurvivorUnchained.Args.Num("den-pool-blur-lod", 5f));
            m.SetShaderParameter("sp_soft", SurvivorUnchained.Args.Num("den-pool-soft2", 0.7f));
            m.SetShaderParameter("sp_ref", SurvivorUnchained.Args.Num("den-pool-ref", 0.09f));   // (den r17 L2, R16 item 2: .15 sat above the floor's albedo, so the grain term darkened the pools on the whole: s11 corr dL +.06)
            m.SetShaderParameter("sp_tint", DungeonDress.V3("den-pool-tint", new Vector3(1f, 0.97f, 0.76f)));   // (den r17 lead, l7c: warmer, dC +.02)
            GD.Print($"DungeonLight floor pools: {n} on {mi.Name}");
        }
    }

    /// <summary>(den r17 L) A lair shaft's foot: 5-9 m from its middle (her and the Pack-Mother), toward the frame's top half and
    /// its sides, on open floor, and the floor seen behind the shaft up to its gap clear of pits and hollows (the masks cut the
    /// rays over them); the second on the other side of the first.</summary>
    static bool LairFoot(ZoneData z, (float X, float Z, float R, string Kind) r, int i, int k, System.Collections.Generic.List<Vector2> feet, out float x, out float zz)
    {
        if (LairFrame > 0f) return LairFrameFoot(z, r, i, k, feet, out x, out zz);
        float pitch = Mathf.DegToRad((float)SurvivorUnchained.Play.Zones.MapRun.CamPitch), gapH = SurvivorUnchained.Args.Num("den-shaft-gap-h", 8.5f);
        var up = -Axis;
        float best = -1f; x = r.X; zz = r.Z;
        for (int t = 0; t < 48; t++)
        {
            float side = (k % 2 == 0 ? 1f : -1f) * (t % 2 == 0 ? 1f : -1f);
            float cx = r.X + side * (4.5f + 4.5f * Hash(i, k + 11 * t, 41)), cz = r.Z - 1f - 4.5f * Hash(i, k + 11 * t, 42);
            if (new Vector2(cx - r.X, cz - r.Z).Length() < 5f) continue;
            if (At(z, z.WallField!, cx, cz) < 3f || (z.HoleField != null && At(z, z.HoleField, cx, cz) < 3.5f) || NearHollow(cx, cz, 2.2f)) continue;
            bool near = false;
            foreach (var f in feet) if (f.DistanceTo(new Vector2(cx, cz)) < 8f) near = true;
            foreach (var sp in z.Spurs)   // (the root spurs' banks and the stones on them: s11's right shaft fell on one)
            {
                Vector2 a0 = new(sp.Seg.X, sp.Seg.Y), a1 = new(sp.Seg.Z, sp.Seg.W), pq = new(cx, cz), ab = a1 - a0;
                float tt = Mathf.Clamp((pq - a0).Dot(ab) / Mathf.Max(ab.LengthSquared(), 1e-4f), 0f, 1f);
                if ((a0 + ab * tt).DistanceTo(pq) < sp.R + 3f) near = true;
            }
            if (near) continue;
            float clear = 1f;
            for (float v = 0.5f; v <= gapH; v += 0.5f)
            {
                // the floor behind the shaft at v up it, seen down the camera's ray
                float h = v * up.Y, bx = cx + v * up.X, bz = cz + v * up.Z - h / Mathf.Tan(pitch);
                if (At(z, z.WallField!, bx, bz) < 0.5f) break;   // the bank behind: the rays fall over it unmasked
                if ((z.HoleField != null && At(z, z.HoleField, bx, bz) < 1.5f) || NearHollow(bx, bz, 0.8f)) { clear = 0f; break; }
            }
            float score = clear * (1f + Hash(i, k + 11 * t, 43));
            if (score > best) { best = score; x = cx; zz = cz; }
        }
        return best > 0f;
    }

    // (den r17 L2, R16 item 2) The lair's shafts composed in the boss frame (--at boss-mid: the camera over the lair's middle,
    // DungeonGen.LairScreen): each foot on open floor in the frame's upper half and sides (den_boss.png: two shafts, upper left
    // and right, their pools bright), its gap (gap-h up the axis) inside the frame's top, off her and the Pack-Mother, the pits,
    // the hollows and the spurs, and the whole shaft seen over open floor: no floor behind it within --den-lair-wallclear m of
    // the walls, where the boulders stand half into the bank (l7c: s11's top-left shaft over a boulder, its gap off-frame).
    // --den-lair-frame 0 (default): r17 L's LairFoot. 1 is a WIP: without the dress's boulders and root crowns (built after the
    // lights) it found no spot in s11 and put s23's over roots and a boulder (l7g).
    // --den-lair-gap-h: the lair's gaps lower than the rooms' (8.5 m stood 560 px over the foot: a gap in frame put the foot
    // below her; den_boss's shafts fall ~280 px from the frame's top to pools in its upper third).
    static readonly float LairFrame = SurvivorUnchained.Args.Num("den-lair-frame", 1f), LairWallClear = SurvivorUnchained.Args.Num("den-lair-wallclear", 2.5f), LairGapH = SurvivorUnchained.Args.Num("den-lair-gap-h", 9.5f);   // (den r19 L, R18b item 4: 4.8 -> 9.5 with --den-lair-top: the beam runs up out of the frame, as den_boss's do; --den-lair-top 999 --den-lair-gap-h 4.8 = r18)
    static readonly float LairTop = SurvivorUnchained.Args.Num("den-lair-top", -10f), LairBeamClear = SurvivorUnchained.Args.Num("den-lair-beam-clear", 120f), LairBeamHalf = SurvivorUnchained.Args.Num("den-lair-beam-half", 100f);   // (den r19 L, R18b item 4) the gap's screen y at most this (the frame's top is 0); fires and stones/tusk groups this many px (clear 0: off) outside the beam's quad (half width px)
    static (float X, float Y) LairPx(float dx, float h, float dz)
    {
        const float pitch = 62f * Mathf.Pi / 180f, dist = 24.3f, look = 0.8f;
        float sp = Mathf.Sin(pitch), cp = Mathf.Cos(pitch), f = 540f / Mathf.Tan(17f * Mathf.Pi / 180f);
        float vy = h - (look + sp * dist), vz = dz - cp * dist;
        float depth = -sp * vy - cp * vz, upv = cp * vy - sp * vz;
        return (960f + f * dx / depth, 540f - f * upv / depth);
    }
    static bool LairFrameFoot(ZoneData z, (float X, float Z, float R, string Kind) r, int i, int k, System.Collections.Generic.List<Vector2> feet, out float x, out float zz)
    {
        SetHard = SetClear > 0f;
        if (LairFrameFoot0(z, r, i, k, feet, LairBeamClear, LairTop, out x, out zz)) return true;
        if (LairBeamClear > 60f && LairFrameFoot0(z, r, i, k, feet, 60f, LairTop, out x, out zz)) return true;   // no spot at the full clearance: half of it
        SetHard = false;   // (den r19 L2) then the set items only cost score (as wave 1), the fires still reject
        if (LairFrameFoot0(z, r, i, k, feet, LairBeamClear, LairTop, out x, out zz)) return true;
        if (LairBeamClear > 60f && LairFrameFoot0(z, r, i, k, feet, 60f, LairTop, out x, out zz)) return true;
        return LairTop < 900f && LairFrameFoot0(z, r, i, k, feet, 60f, LairTop + 80f, out x, out zz);   // then the beam top may stop a little inside the frame
    }
    static bool SetHard;
    // (den r19 L, R18b item 4) true when a fire or a placed stone/crown/tusk group (floor px) lies within clear px of the beam's quad
    // (the segment foot -> gap in px, half width LairBeamHalf), where the camera sees the beam over it
    static bool FallbackFireInBeam(ZoneData z, (float X, float Z, float R, string Kind) r, float x, float zz)
    {
        SetHard = SetClear > 0f;
        var up = -Axis; var (sx, sy) = LairPx(x - r.X, 0f, zz - r.Z); var (gx, gy) = LairPx(x - r.X + up.X * LairGapH, z.HeightAt(x, zz) + up.Y * LairGapH, zz - r.Z + up.Z * LairGapH);
        return BeamNear(sx, sy, gx, gy, z, r, LairBeamClear, false) > 0;
    }
    static readonly float SetClear = SurvivorUnchained.Args.Num("den-lair-set-clear", 0f);   // (den r19 L2) 0: only the fires reject (wave 1)   // (den r19 lead: default 0, r19b: with the crowns and tusks rejected the hashed fallback kept its last try, short beams over the s11 carcass and the s23 fire)
    static int BeamNear(float sx, float sy, float gx, float gy, ZoneData z, (float X, float Z, float R, string Kind) r, float clear, bool placed)
    {
        var a = new Vector2(sx, sy); var ab = new Vector2(gx, gy) - a; float d2 = Mathf.Max(ab.LengthSquared(), 1e-4f);
        int n = 0;
        bool Near(float wx, float wz)
        {
            var (px, py) = LairPx(wx - r.X, 0f, wz - r.Z); var p = new Vector2(px, py);
            float t = Mathf.Clamp((p - a).Dot(ab) / d2, 0f, 1f);
            return (a + ab * t).DistanceTo(p) < LairBeamHalf + clear;
        }
        if (placed) foreach (var q in DungeonDress.Placed) if (Near(q.X, q.Z)) n++;
        if (!placed && z.Meta?.Fires != null) foreach (var f in z.Meta.Fires) if (Near((float)f.X, (float)f.Z)) n++;
        if (!placed && SetHard) foreach (var q in DungeonDress.Placed) if (!DungeonDress.Stones.Contains(q) && Near(q.X, q.Z)) n++;   // (den r19 L2, R18b item 4) the set items (B6 root crowns, O8 tusk groups, O1) clear of the beam too, as the fires
        return n;
    }
    static bool LairFrameFoot0(ZoneData z, (float X, float Z, float R, string Kind) r, int i, int k, System.Collections.Generic.List<Vector2> feet, float clearPx, float top, out float x, out float zz)
    {
        float pitch = Mathf.DegToRad((float)SurvivorUnchained.Play.Zones.MapRun.CamPitch), gapH = LairGapH;
        var up = -Axis;
        var why = new int[9];
        float best = -1e9f; x = r.X; zz = r.Z;
        Vector2? other = null; foreach (var f in feet) if (f.DistanceTo(new Vector2(r.X, r.Z)) < r.R + 6f) other = f;
        for (float u = -16f; u <= 16f; u += 0.5f)
            for (float v = -14f; v <= 8f; v += 0.5f)
            {
                float cx = r.X + u, cz = r.Z + v;
                var (sx, sy) = LairPx(u, 0f, v);
                if (sx < 140f || sx > 1780f || sy < 200f || sy > 830f || !SurvivorUnchained.Maps.DungeonGen.LairScreenClear(sx, sy)) continue;
                if (new Vector2(u, v).Length() < 5.5f || new Vector2(sx - 960f, (sy - 560f) * 1.4f).Length() < 330f) { why[0]++; continue; }   // her, the Pack-Mother, the fight
                var g = new Vector3(cx, z.HeightAt(cx, cz), cz) + up * gapH;
                var (gx, gy) = LairPx(g.X - r.X, g.Y, g.Z - r.Z);
                if (LairTop < 900f ? (gy > top || gx < 40f || gx > 1880f) : (gy < 25f || gy > 420f || gx < 40f || gx > 1880f || (gy < 95f && gx > 480f && gx < 1440f))) { why[1]++; continue; }   // the gap in frame, off the ruler's bar (den r19 L: or, with --den-lair-top, above the frame's top)
                if (clearPx > 0f && BeamNear(sx, sy, gx, gy, z, r, clearPx, false) > 0) { why[7]++; continue; }   // (den r19 L, R18b item 4) fires and stones/tusk groups clear of the beam's quad
                if (At(z, z.WallField!, cx, cz) < LairWallClear + 0.5f) { why[2]++; continue; }
                if (z.HoleField != null && At(z, z.HoleField, cx, cz) < 3.5f) { why[5]++; continue; }
                if (NearHollow(cx, cz, 2.2f)) { why[6]++; continue; }
                if (LairKeepOff > 0f && DungeonDress.Placed.Exists(q => new Vector2(q.X - cx, q.Z - cz).Length() < q.R + LairKeepOff)) { why[8]++; continue; }   // (den r18 L3, R17 item 3) the pool keeps off the boulders (--den-lair-keepoff m, 0: r17)
                bool bad = false;
                foreach (var f in feet) if (f.DistanceTo(new Vector2(cx, cz)) < 8f) bad = true;
                foreach (var spr in z.Spurs)
                {
                    Vector2 a0 = new(spr.Seg.X, spr.Seg.Y), a1 = new(spr.Seg.Z, spr.Seg.W), pq = new(cx, cz), ab = a1 - a0;
                    float tt = Mathf.Clamp((pq - a0).Dot(ab) / Mathf.Max(ab.LengthSquared(), 1e-4f), 0f, 1f);
                    if ((a0 + ab * tt).DistanceTo(pq) < spr.R + 3f) bad = true;
                }
                if (bad) { why[3]++; continue; }
                // the floor seen behind the shaft, foot to gap: open (no wall foot, pit, hollow or spur bank)
                for (float t = 0.5f; t <= gapH && !bad; t += 0.5f)
                {
                    float h = t * up.Y, bx = cx + t * up.X, bz = cz + t * up.Z - h / Mathf.Tan(pitch);
                    if (At(z, z.WallField!, bx, bz) < LairWallClear || (z.HoleField != null && At(z, z.HoleField, bx, bz) < 1.5f) || NearHollow(bx, bz, 0.8f)) bad = true;
                }
                if (bad) { why[4]++; continue; }
                // den_boss: high in the frame and out to the sides; the second across from the first
                float score = 1f - Mathf.Abs(sy - 450f) / 500f - (clearPx > 0f ? 0.25f * Mathf.Min(4, BeamNear(sx, sy, gx, gy, z, r, clearPx, true)) : 0f)   // (den r19 L: a placed stone, crown or tusk group in the beam's quad + clearance costs .25; the fires reject outright)
                     + 0.4f * Mathf.Min(1f, Mathf.Abs(sx - 960f) / 600f) + 0.15f * Hash(i, (int)(u * 2f) * 97 + (int)(v * 2f), 44 + k);
                if (other is Vector2 o) { var (ox, _) = LairPx(o.X - r.X, 0f, o.Y - r.Z); if ((ox - 960f) * (sx - 960f) < 0f) score += 0.6f; }
                if (score > best) { best = score; x = cx; zz = cz; }
            }
        GD.Print($"DungeonLight lair shaft {k}: " + (best > -1e8f ? $"({x:F1},{zz:F1}) px {LairPx(x - r.X, 0f, zz - r.Z)}" : "no open spot in frame") + $" (rejects: fight {why[0]}, gap {why[1]}, wall {why[2]}, pit {why[5]}, hollow {why[6]} ({Hollows.Count}), beam/fire {why[7]}, keepoff {why[8]}, spacing/spurs {why[3]}, behind {why[4]})");
        return best > -1e8f;
    }

    static void AddFan(Node3D root, Vector3 foot, bool lair)
    {
        if (fanMesh == null)
        {
            var arr = new Godot.Collections.Array(); arr.Resize((int)Mesh.ArrayType.Max);
            arr[(int)Mesh.ArrayType.Vertex] = new Vector3[] { new(-1, 0, 0), new(1, 0, 0), new(-1, 1, 0), new(1, 1, 0) };
            arr[(int)Mesh.ArrayType.TexUV] = new Vector2[] { new(-1, 0), new(1, 0), new(-1, 1), new(1, 1) };
            arr[(int)Mesh.ArrayType.Index] = new int[] { 0, 2, 1, 1, 2, 3 };
            fanMesh = new ArrayMesh(); fanMesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        }
        int s = ++fanN + 101;
        // 3-5 rays; widths and gaps in units, then scaled to the fan (bars ~10-25 px, gaps ~10-20 px over 100-150 px)
        int n = 3 + (Hash(s, 1, 21) < 0.3f ? 0 : Hash(s, 1, 22) < 0.6f ? 1 : 2);
        var w = new float[n]; var g = new float[n]; float sum = 0f;
        for (int k = 0; k < n; k++) { w[k] = 1f + 0.8f * Hash(s, k, 23); g[k] = k < n - 1 ? 1f + 0.5f * Hash(s, k, 24) : 0f; sum += w[k] + g[k]; }
        float unit = 0.92f / sum, at = 0.04f;
        var rays = new Vector4[5];
        for (int k = 0; k < n; k++) { rays[k] = new Vector4(at + 0.5f * w[k] * unit, 0.5f * w[k] * unit / 0.72f, 0.45f + 0.55f * Hash(s, k, 25), Hash(s, k, 26)); at += (w[k] + g[k]) * unit; }   // (den r16 B2: gains .7-1 -> .45-1, uneven)
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/dungeon_shaft_fan.gdshader") };
        mat.SetShaderParameter("axis_up", -Axis);
        mat.SetShaderParameter("src_h", lair && LairFrame > 0f ? LairGapH : SurvivorUnchained.Args.Num("den-shaft-gap-h", 8.5f));   // (den r17 L2: the lair's lower gaps)
        mat.SetShaderParameter("top_fade", SurvivorUnchained.Args.Num("den-shaft-topfade", 0.16f));   // (den r18 L3, R17 item 10) fade in from the frame's top; 0: r17
        mat.SetShaderParameter("w_foot", SurvivorUnchained.Args.Num("den-shaft-wfoot", 2.0f));
        mat.SetShaderParameter("w_src", SurvivorUnchained.Args.Num("den-shaft-wgap", 0.9f));
        mat.SetShaderParameter("pool_r", SurvivorUnchained.Args.Num("den-shaft-pool-r", 1.0f));
        mat.SetShaderParameter("rays", rays);
        mat.SetShaderParameter("ray_n", n);
        // (den r16 B2: B's c6dce6 at .3, ext .3 read as cyan lasers, cores +.30-.46 L, the gap a cyan blob; soft rays, near-neutral, lower)
        // (den r17 L, R16 item 2) the rays' added light neutral-cool and only added (ext 0): ext .12 took a share of the warm bank
        // behind them, so the shaft's change tracked the albedo (h 35-45, C .05); the old look: --den-shaft-tint d6dce2 --den-shaft-ext .12
        mat.SetShaderParameter("tint", new Color(SurvivorUnchained.Args.Get("den-shaft-tint") ?? (Real ? SurvivorUnchained.Args.Get("den-rl-fan-tint") ?? "ffe6c4" : Smooth ? (lair ? "a0dcea" : "a0e0ea") : "c8d8f0")));
        mat.SetShaderParameter("strength", SurvivorUnchained.Args.Num("den-shaft-fan-k", 0.15f) * (lair ? DenShade.Num("den-lair-shaft", 0.66f, 1.1f) : 1f) * (Real ? RlFan : 1f));
        mat.SetShaderParameter("ext", SurvivorUnchained.Args.Num("den-shaft-ext", 0f));
        mat.SetShaderParameter("haze", SurvivorUnchained.Args.Num("den-shaft-haze", 0.3f));
        mat.SetShaderParameter("gap_tint", new Color(SurvivorUnchained.Args.Get("den-shaft-gap-tint") ?? (Smooth ? "d4f0f2" : "eeeae2")));
        mat.SetShaderParameter("gap_gain", SurvivorUnchained.Args.Num("den-shaft-gap-k", 0.8f));
        mat.SetShaderParameter("gap_ext", SurvivorUnchained.Args.Num("den-shaft-gap-ext", 0.2f));
        var hl = new Vector4[8]; int hn = 0;
        foreach (var h in Hollows) if (hn < 8 && h.p.DistanceTo(new Vector2(foot.X, foot.Z)) < h.r + 16f) hl[hn++] = new Vector4(h.p.X, h.p.Y, h.r, 0f);
        mat.SetShaderParameter("holl", hl); mat.SetShaderParameter("holl_n", hn);
        mat.SetShaderParameter("pool_strength", SurvivorUnchained.Args.Num("den-shaft-pool-k", 0.16f));
        mat.SetShaderParameter("pool_ext", SurvivorUnchained.Args.Num("den-shaft-pool-ext", 0.15f));
        if (HoleTex != null) { mat.SetShaderParameter("hole_tex", HoleTex); mat.SetShaderParameter("hole_map", HoleMap); }
        if (PoolFloor > 0f)
        {
            // (den r17 L, R16 item 2) the pool is drawn on the floor's albedo (FloorPools): no sprite here
            mat.SetShaderParameter("pool_strength", 0f); mat.SetShaderParameter("pool_ext", 0f);
            Pools.Add(new Vector4(foot.X, foot.Z, PoolR * (0.9f + 0.25f * Hash(s, 2, 27)), Hash(s, 3, 28) * 100f + (lair ? 1000f : 0f)));   // (den r17 L2: a lair pool's seed + 1000, sp_lair)
        }
        if (ShaftFoot > 0f) { mat.SetShaderParameter("foot_k", ShaftFoot); mat.SetShaderParameter("soft_depth", SurvivorUnchained.Args.Num("den-shaft-soft", 0.35f)); }
        // (den r17 L2, R16 item 2) the rays carried down into their pools (r17 L: .6, they faded out over the lit floor ~240 px short)
        if (ShaftFoot > 0f) mat.SetShaderParameter("foot_low", SurvivorUnchained.Args.Num("den-shaft-foot-low", 1.8f));
        root.AddChild(new MeshInstance3D
        {
            Name = "shaft_fan", Mesh = fanMesh, MaterialOverride = mat, Transform = new Transform3D(Basis.Identity, foot),
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, CustomAabb = new Aabb(new Vector3(-8, -3, -8), new Vector3(16, 14, 16)),
        });
    }

    /// <summary>(den r16 B, R15f item 2) The corridors' shafts: on corridor floor (past every room's reach, 2 m in from the
    /// wall, clear of the pits), the deepest-in first, none nearer than --den-shaft-corr-gap metres to another shaft.</summary>
    static void AddCorridorFans(Node3D root, ZoneData z, System.Collections.Generic.List<Vector2> feet)
    {
        float gapM = SurvivorUnchained.Args.Num("den-shaft-corr-gap", 13f);
        if (SurvivorUnchained.Args.Num("den-shaft-corr", 1f) <= 0f || z.WallField == null || Fan <= 0f) return;
        var cand = new System.Collections.Generic.List<(float S, float X, float Z)>();
        for (float x = -z.Half + 2f; x < z.Half - 2f; x += 2f)
            for (float zz = -z.Half + 2f; zz < z.Half - 2f; zz += 2f)
            {
                float wf = At(z, z.WallField, x, zz);
                if (wf < 2f || DenRagged.Corridor(x, zz, z.Rooms) < 0.99f || (z.HoleField != null && At(z, z.HoleField, x, zz) <= 3f)) continue;
                cand.Add((wf + 1.5f * Hash((int)x * 3, (int)zz * 5, 31), x, zz));
            }
        cand.Sort((a, b) => b.S.CompareTo(a.S));
        foreach (var c in cand)
        {
            var p = new Vector2(c.X, c.Z);
            bool clear = true;
            foreach (var f in feet) if (f.DistanceTo(p) < gapM) { clear = false; break; }
            if (!clear) continue;
            feet.Add(p);
            if (!Real || RlFan > 0f) AddFan(root, new Vector3(c.X, z.HeightAt(c.X, c.Z), c.Z), false);
            if (CorrSpot > 0f) AddSpot(root, new Vector3(c.X, z.HeightAt(c.X, c.Z), c.Z), 2.2f, PoolWide, false, CorrSpot / PoolSpot);   // (den r19 L2, R18b item 1) the corridor pools had the floor lift only (s11 dL +.07)
        }
    }

    // (r14) The room's play floor read dim grey (ring by her L.31 C.028): where the room's light falls it pools warm,
    // a broad soft wash of two overlapping uneven spots (not a disc, not on her), light through the roots.
    static void AddWash(Node3D root, float x, float y, float zz, float rad, int i)
    {
        float e = SurvivorUnchained.Args.Num("den-wash", 4.8f) * (Real ? RlWash : 1f);
        if (e <= 0f) return;
        for (int n = 0; n < 2; n++)
        {
            float a = Hash(i, n, 11) * Mathf.Tau, d = rad * (0.1f + 0.2f * Hash(i, n, 12));
            var foot = new Vector3(x + Mathf.Cos(a) * d, y, zz + Mathf.Sin(a) * d);
            var top = foot - Axis * Height;
            float wide = rad * (n == 0 ? 0.75f : 0.5f);
            root.AddChild(new SpotLight3D
            {
                Name = "room_wash",
                Transform = new Transform3D(Basis.LookingAt(Axis, Vector3.Up), top),
                LightColor = new Color(SurvivorUnchained.Args.Get("den-wash-colour") ?? "ffd088"),
                LightEnergy = e * (n == 0 ? 1f : 0.8f),
                SpotRange = Height + 4f,
                SpotAngle = Mathf.RadToDeg(Mathf.Atan(wide / Height)),
                SpotAngleAttenuation = 0.5f,
                SpotAttenuation = 0.5f,
                ShadowEnabled = false,
                LightSpecular = 0.1f,
            });
            root.AddChild(new Node3D { Name = "wash_pad" });   // (keeps the child/2 shaft count in the log honest)
        }
    }

    static int Salt;
    static float Hash(int a, int b, int c)
    {
        unchecked
        {
            if (Salt != 0) a += Salt * 31 + b * 7;
            uint h = (uint)(a * 374761393 + b * 668265263 + c * 1274126177);
            h = (h ^ (h >> 13)) * 1274126177u;
            h ^= h >> 16;
            return (h & 0xFFFFFF) / (float)0x1000000;
        }
    }
}
