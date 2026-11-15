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
    static readonly Vector3 Axis = new Vector3(0.12f, -1f, 0.42f).Normalized();  // (the roof hole north of the pool: from the play camera the shaft climbs up the screen)
    const float Height = 15f;
    static readonly float PoolWide = SurvivorUnchained.Args.Num("den-pool-wide", 1.5f), PoolSoft = SurvivorUnchained.Args.Num("den-pool-soft", 0.7f), PoolEnergy = SurvivorUnchained.Args.Num("den-pool-energy", 13f), PackFill = SurvivorUnchained.Args.Num("den-pack-fill", 4f), BossPool = SurvivorUnchained.Args.Num("den-boss-pool", 1.5f);

    public static Node3D? Build(ZoneData z)
    {
        if (z.DungeonTheme != "den" || z.Rooms.Count == 0) return null;
        Salt = z.Seed == 0 ? 0 : z.Seed * 40503 + 17;
        var root = new Node3D { Name = "DungeonLight" };
        var shader = GD.Load<Shader>("res://shaders/dungeon_shaft.gdshader");
        int i = 0;
        foreach (var r in z.Rooms)
        {
            i++;
            if (r.Kind == "Bend") continue;
            // One shaft to a room, two in a big one, three in the boss lair; off its centre so the fight is not always in the spot.
            int count = r.Kind == "Boss" ? 3 : r.R > 11 ? 2 : 1;   // (the lair three: round 6, its open floor read as one empty stretch)
            for (int k = 0; k < count; k++)
            {
                // (clear of the pits and the walls: a shaft down a pit lit its roots bone-white)
                float x = r.X, zz = r.Z;
                for (int t = 0; t < 10; t++)
                {
                    float a = Hash(i, k + 7 * t, 1) * Mathf.Tau, d = r.R * (0.25f + 0.35f * Hash(i, k + 7 * t, 2));
                    x = r.X + Mathf.Cos(a) * d; zz = r.Z + Mathf.Sin(a) * d;
                    if (At(z, z.WallField!, x, zz) > 2.5f && (z.HoleField == null || At(z, z.HoleField, x, zz) > 3f)) break;
                }
                float w = 1.1f + 1.0f * Hash(i, k, 3);
                AddShaft(root, shader, new Vector3(x, z.HeightAt(x, zz), zz), w, r.Kind == "Boss" ? BossPool : PoolWide);
            }
        }
        // (round 8, 15 Nov) The pack reads in the den's light: the wolves' dark fur under a dim key read as black
        // silhouettes (round 7's "black fragments" by the big pit were the resting pack). A fill from the camera's side,
        // high, that reaches the crowd's own layer only (PlayerView.CrowdLayer): the floor, the banks and HER take none of
        // it (her merged skin light is untouched). --den-pack-fill sets its energy (0 off).
        if (PackFill > 0f)
            root.AddChild(new DirectionalLight3D
            {
                Name = "pack_fill",
                Transform = new Transform3D(Basis.LookingAt(new Vector3(0.25f, -0.75f, -0.6f).Normalized(), Vector3.Up), Vector3.Zero),
                LightColor = new Color("e8d8c8"),
                LightEnergy = PackFill,
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

    static void AddShaft(Node3D root, Shader shader, Vector3 foot, float w, float pool)
    {
        var top = foot - Axis * Height;
        var basis = Basis.LookingAt(Axis, Mathf.Abs(Axis.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        // The light: a spot from the roof's hole, its cone just the shaft's width on the floor.
        var spot = new SpotLight3D
        {
            Name = "shaft_light",
            Transform = new Transform3D(basis, top),
            LightColor = new Color(SurvivorUnchained.Args.Get("den-pool-colour") ?? "ffd2a0"),   // (round 8: warmer, den_room.png's pools (134,95,73); ffe2b8 read pale beige)
            LightEnergy = PoolEnergy,   // (round 8: --den-pool-energy) (lead 6: 12 lifted the boss frame to 85; 6 left rooms at 35; warm 9 in the pools only, round 6; 16 moved the room median 36 -> 36: the pools are too small a share of the frame)
            SpotRange = Height + 4f,
            SpotAngle = Mathf.RadToDeg(Mathf.Atan((w * 1.25f * pool) / Height)),
            SpotAngleAttenuation = pool > 1f ? PoolSoft : 1.2f,   // (round 7: the rooms' pools 1.5x wider and softer-edged, the room's centre warm mid-brown; the lair keeps its own)
            SpotAttenuation = 0.4f,
            ShadowEnabled = false,
            LightSpecular = 0.2f,
        };
        root.AddChild(spot);
        // The shaft in the air: a soft cone, brightest a little above the floor and gone toward the roof.
        var mesh = new CylinderMesh { TopRadius = w * 0.55f, BottomRadius = w, Height = Height, RadialSegments = 20, Rings = 1, CapTop = false, CapBottom = false };
        var mat = new ShaderMaterial { Shader = shader };
        mat.SetShaderParameter("height", Height);
        var mid = foot - Axis * (Height * 0.5f);
        // CylinderMesh stands along +y: turn +y to the shaft's upward axis (-Axis).
        var up = -Axis;
        var side = up.Cross(Vector3.Back).Normalized();
        var b = new Basis(side, up, side.Cross(up).Normalized());
        root.AddChild(new MeshInstance3D { Name = "shaft", Mesh = mesh, MaterialOverride = mat, Transform = new Transform3D(b, mid), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
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
