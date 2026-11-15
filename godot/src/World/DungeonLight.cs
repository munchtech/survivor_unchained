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
    static readonly Vector3 Axis = new Vector3(0.22f, -1f, -0.12f).Normalized();
    const float Height = 15f;

    public static Node3D? Build(ZoneData z)
    {
        if (z.DungeonTheme != "den" || z.Rooms.Count == 0) return null;
        var root = new Node3D { Name = "DungeonLight" };
        var shader = GD.Load<Shader>("res://shaders/dungeon_shaft.gdshader");
        int i = 0;
        foreach (var r in z.Rooms)
        {
            i++;
            if (r.Kind == "Bend") continue;
            // One shaft to a room, two in a big one; off its centre so the fight is not always in the spot.
            int count = r.R > 11 ? 2 : 1;
            for (int k = 0; k < count; k++)
            {
                float a = Hash(i, k, 1) * Mathf.Tau, d = r.R * (0.25f + 0.35f * Hash(i, k, 2));
                float x = r.X + Mathf.Cos(a) * d, zz = r.Z + Mathf.Sin(a) * d;
                float w = 1.6f + 1.4f * Hash(i, k, 3);
                AddShaft(root, shader, new Vector3(x, z.HeightAt(x, zz), zz), w);
            }
        }
        GD.Print($"DungeonLight {z.DungeonTheme}: {root.GetChildCount() / 2} shafts over {z.Rooms.Count} rooms");
        return root;
    }

    static void AddShaft(Node3D root, Shader shader, Vector3 foot, float w)
    {
        var top = foot - Axis * Height;
        var basis = Basis.LookingAt(Axis, Mathf.Abs(Axis.Y) > 0.99f ? Vector3.Forward : Vector3.Up);
        // The light: a spot from the roof's hole, its cone just the shaft's width on the floor.
        var spot = new SpotLight3D
        {
            Name = "shaft_light",
            Transform = new Transform3D(basis, top),
            LightColor = new Color("dfe9ff"),
            LightEnergy = 9f,
            SpotRange = Height + 4f,
            SpotAngle = Mathf.RadToDeg(Mathf.Atan((w * 1.25f) / Height)),
            SpotAngleAttenuation = 0.6f,
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

    static float Hash(int a, int b, int c)
    {
        unchecked
        {
            uint h = (uint)(a * 374761393 + b * 668265263 + c * 1274126177);
            h = (h ^ (h >> 13)) * 1274126177u;
            h ^= h >> 16;
            return (h & 0xFFFFFF) / (float)0x1000000;
        }
    }
}
