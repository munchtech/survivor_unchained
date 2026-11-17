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
        int i = 0; fanN = 0;
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
                for (int t = 0; t < 10; t++)
                {
                    float a = Hash(i, k + 7 * t, 1) * Mathf.Tau, d = (r.Kind == "Boss" ? 3f + 5f * Hash(i, k + 7 * t, 2) : r.R * ( 0.25f + 0.35f * Hash(i, k + 7 * t, 2)));   // (r11: the lair's pools in its middle frame)
                    x = r.X + Mathf.Cos(a) * d; zz = r.Z + Mathf.Sin(a) * d;
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

    static void AddShaft(Node3D root, Shader shader, Vector3 foot, float w, float pool, bool lair = false)
    {
        var top = foot - Axis * Height;
        var basis = Basis.LookingAt(Axis, Mathf.Abs(Axis.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        // The light: a spot from the roof's hole, its cone just the shaft's width on the floor.
        var spot = new SpotLight3D
        {
            Name = "shaft_light",
            Transform = new Transform3D(basis, top),
            LightColor = new Color(SurvivorUnchained.Args.Get("den-pool-colour") ?? (lair ? "ffdc8a" : "ffdea0")),   // (r12: 13 / ffd2a0 -> 8 / ffc890 and the beams .22 -> .18: the room median 54 -> 51, lit (151,107,89) -> (133,98,83) against (134,95,73))   // (round 8: warmer, den_room.png's pools (134,95,73); ffe2b8 read pale beige)
            LightEnergy = PoolEnergy * (lair ? SurvivorUnchained.Args.Num("den-lair-pool", 0.73f) : 1f),   // (r12) the lair's pools against its floor (lit/median 109/68 in den_boss.png)   // (round 8: --den-pool-energy) (lead 6: 12 lifted the boss frame to 85; 6 left rooms at 35; warm 9 in the pools only, round 6; 16 moved the room median 36 -> 36: the pools are too small a share of the frame)
            SpotRange = Height + 4f,
            SpotAngle = Mathf.RadToDeg(Mathf.Atan((w * 1.25f * pool) / Height)),
            SpotAngleAttenuation = pool > 1f ? PoolSoft : 1.2f,   // (round 7: the rooms' pools 1.5x wider and softer-edged, the room's centre warm mid-brown; the lair keeps its own)
            SpotAttenuation = 0.4f,
            ShadowEnabled = false,
            LightSpecular = 0.2f,
        };
        root.AddChild(spot);
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
        mat.SetShaderParameter("strength", SurvivorUnchained.Args.Num("den-shaft-strength", 0.26f) * (lair ? SurvivorUnchained.Args.Num("den-lair-shaft", 1.1f) : 1f));   // (r12: the lair's beams did not read over its bright floor)
        var mid = foot - Axis * (Height * 0.5f);
        // CylinderMesh stands along +y: turn +y to the shaft's upward axis (-Axis).
        var up = -Axis;
        var side = up.Cross(Vector3.Back).Normalized();
        var b = new Basis(side, up, side.Cross(up).Normalized());
        root.AddChild(new MeshInstance3D { Name = "shaft", Mesh = mesh, MaterialOverride = mat, Transform = new Transform3D(b, mid), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
    }

    // (den r16 B, R15f item 2) The shaft as den_room.png has it: a fan of 3-5 rays from a bright gap ~8 m up, landing in a soft
    // pool (shaders/dungeon_shaft_fan.gdshader). --den-shaft-fan 0: r15's cylinder veil. --den-shaft-corr 0: none in the corridors.
    static readonly float Fan = SurvivorUnchained.Args.Num("den-shaft-fan", 1f);
    static ArrayMesh? fanMesh;
    static int fanN;
    static System.Collections.Generic.List<(Vector2 p, float r, int v)> Hollows = new();
    static bool NearHollow(float x, float zz, float m) { foreach (var h in Hollows) if (h.p.DistanceTo(new Vector2(x, zz)) < h.r + m) return true; return false; }
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
        mat.SetShaderParameter("src_h", SurvivorUnchained.Args.Num("den-shaft-gap-h", 8.5f));
        mat.SetShaderParameter("w_foot", SurvivorUnchained.Args.Num("den-shaft-wfoot", 2.0f));
        mat.SetShaderParameter("w_src", SurvivorUnchained.Args.Num("den-shaft-wgap", 0.9f));
        mat.SetShaderParameter("pool_r", SurvivorUnchained.Args.Num("den-shaft-pool-r", 1.0f));
        mat.SetShaderParameter("rays", rays);
        mat.SetShaderParameter("ray_n", n);
        // (den r16 B2: B's c6dce6 at .3, ext .3 read as cyan lasers, cores +.30-.46 L, the gap a cyan blob; soft rays, near-neutral, lower)
        mat.SetShaderParameter("tint", new Color(SurvivorUnchained.Args.Get("den-shaft-tint") ?? "d6dce2"));
        mat.SetShaderParameter("strength", SurvivorUnchained.Args.Num("den-shaft-fan-k", 0.07f) * (lair ? SurvivorUnchained.Args.Num("den-lair-shaft", 1.1f) : 1f));
        mat.SetShaderParameter("ext", SurvivorUnchained.Args.Num("den-shaft-ext", 0.12f));
        mat.SetShaderParameter("haze", SurvivorUnchained.Args.Num("den-shaft-haze", 0.3f));
        mat.SetShaderParameter("gap_tint", new Color(SurvivorUnchained.Args.Get("den-shaft-gap-tint") ?? "eeeae2"));
        mat.SetShaderParameter("gap_gain", SurvivorUnchained.Args.Num("den-shaft-gap-k", 1.6f));
        mat.SetShaderParameter("gap_ext", SurvivorUnchained.Args.Num("den-shaft-gap-ext", 0.2f));
        var hl = new Vector4[8]; int hn = 0;
        foreach (var h in Hollows) if (hn < 8 && h.p.DistanceTo(new Vector2(foot.X, foot.Z)) < h.r + 16f) hl[hn++] = new Vector4(h.p.X, h.p.Y, h.r, 0f);
        mat.SetShaderParameter("holl", hl); mat.SetShaderParameter("holl_n", hn);
        mat.SetShaderParameter("pool_strength", SurvivorUnchained.Args.Num("den-shaft-pool-k", 0.16f));
        mat.SetShaderParameter("pool_ext", SurvivorUnchained.Args.Num("den-shaft-pool-ext", 0.15f));
        if (HoleTex != null) { mat.SetShaderParameter("hole_tex", HoleTex); mat.SetShaderParameter("hole_map", HoleMap); }
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
            AddFan(root, new Vector3(c.X, z.HeightAt(c.X, c.Z), c.Z), false);
        }
    }

    // (r14) The room's play floor read dim grey (ring by her L.31 C.028): where the room's light falls it pools warm,
    // a broad soft wash of two overlapping uneven spots (not a disc, not on her), light through the roots.
    static void AddWash(Node3D root, float x, float y, float zz, float rad, int i)
    {
        float e = SurvivorUnchained.Args.Num("den-wash", 4.8f);
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
