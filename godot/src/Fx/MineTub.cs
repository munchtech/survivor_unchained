using System;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The Dig's iron tub (BattleFx.Dig), built in code: a riveted hull flared toward its mouth, its
/// plates rust over dark iron, banded at the lip and strapped at the corners, heaped with spoil and a
/// few lumps of ember-stone still warm, on four flanged wheels. Its front is +Z; its feet are at y = 0
/// on the rail. (A grey box on four discs read as a crate, not as the tub that runs you down.)
/// </summary>
public static class MineTub
{
    static Material? rust, iron, spoil, ember, glass;

    /// <summary>Hull's floor and lip, and its half-sizes at each (x across, z along).</summary>
    const float Floor = 0.34f, Lip = 1.0f, BotX = 0.47f, BotZ = 0.66f, TopX = 0.6f, TopZ = 0.82f, Wall = 0.05f;

    public static Node3D Make(int seed)
    {
        Materials();
        var root = new Node3D { Name = "MineTub" };
        root.AddChild(new MeshInstance3D { Mesh = Hull(), MaterialOverride = rust });
        var r = new Random(seed);
        // The lip's band and the corner straps: dark iron standing proud of the plates.
        AddBox(root, new Vector3(TopX * 2 + 0.06f, 0.08f, 0.06f), new Vector3(0, Lip - 0.03f, TopZ + 0.01f), 0, 0);
        AddBox(root, new Vector3(TopX * 2 + 0.06f, 0.08f, 0.06f), new Vector3(0, Lip - 0.03f, -TopZ - 0.01f), 0, 0);
        AddBox(root, new Vector3(0.06f, 0.08f, TopZ * 2 + 0.06f), new Vector3(TopX + 0.01f, Lip - 0.03f, 0), 0, 0);
        AddBox(root, new Vector3(0.06f, 0.08f, TopZ * 2 + 0.06f), new Vector3(-TopX - 0.01f, Lip - 0.03f, 0), 0, 0);
        float h = Lip - Floor, tiltX = Mathf.Atan2(TopX - BotX, h), tiltZ = Mathf.Atan2(TopZ - BotZ, h);
        foreach (float sx in new[] { -1f, 1f })
            foreach (float k in new[] { -0.62f, 0f, 0.62f })
            {
                // Straps down the long sides, leaning out with the plates.
                float zMid = k * (BotZ + TopZ) / 2, xMid = sx * ((BotX + TopX) / 2 + 0.018f);
                AddBox(root, new Vector3(0.035f, h + 0.04f, 0.09f), new Vector3(xMid, Floor + h / 2, zMid), -sx * tiltX, 0);
            }
        foreach (float sz in new[] { -1f, 1f })
            foreach (float k in new[] { -0.55f, 0.55f })
            {
                float xMid = k * (BotX + TopX) / 2, zMid = sz * ((BotZ + TopZ) / 2 + 0.018f);
                AddBox(root, new Vector3(0.09f, h + 0.04f, 0.035f), new Vector3(xMid, Floor + h / 2, zMid), 0, sz * tiltZ);
            }
        // The underframe, the axles and the couplings.
        AddBox(root, new Vector3(0.12f, 0.1f, BotZ * 2 + 0.5f), new Vector3(-0.32f, Floor - 0.05f, 0), 0, 0);
        AddBox(root, new Vector3(0.12f, 0.1f, BotZ * 2 + 0.5f), new Vector3(0.32f, Floor - 0.05f, 0), 0, 0);
        foreach (float sz in new[] { -1f, 1f })
        {
            AddBox(root, new Vector3(0.22f, 0.08f, 0.14f), new Vector3(0, Floor - 0.04f, sz * (BotZ + 0.3f)), 0, 0);
            var axle = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.035f, BottomRadius = 0.035f, Height = 1.1f, RadialSegments = 8 }, MaterialOverride = iron };
            axle.Position = new Vector3(0, 0.22f, sz * 0.46f);
            axle.Rotation = new Vector3(0, 0, Mathf.Pi / 2);
            root.AddChild(axle);
            foreach (float sx in new[] { -1f, 1f }) root.AddChild(Wheel(new Vector3(sx * 0.5f, 0.22f, sz * 0.46f), sx));
        }
        // Heaped with spoil above its lip, a few small lumps of ember-stone in it still warm.
        for (int i = 0; i < 26; i++)
        {
            float x = (float)(r.NextDouble() * 2 - 1) * (TopX - 0.14f), z = (float)(r.NextDouble() * 2 - 1) * (TopZ - 0.16f);
            float rr = Mathf.Min(1, Mathf.Sqrt(x * x / (TopX * TopX) + z * z / (TopZ * TopZ)));
            float s = 0.09f + (float)r.NextDouble() * 0.11f;
            root.AddChild(new MeshInstance3D
            {
                Mesh = new BoxMesh { Size = new Vector3(s * 1.6f, s * (0.8f + (float)r.NextDouble() * 0.6f), s * (1.0f + (float)r.NextDouble() * 0.8f)) },
                MaterialOverride = spoil,
                Position = new Vector3(x, Lip - 0.1f + 0.2f * (1 - rr * rr) + (float)r.NextDouble() * 0.04f, z),
                Rotation = new Vector3((float)r.NextDouble() * 3, (float)r.NextDouble() * 3, (float)r.NextDouble() * 3),
            });
        }
        for (int i = 0; i < 3; i++)
        {
            float x = (float)(r.NextDouble() * 2 - 1) * (TopX - 0.25f), z = (float)(r.NextDouble() * 2 - 1) * (TopZ - 0.3f);
            root.AddChild(new MeshInstance3D
            {
                Mesh = new BoxMesh { Size = new Vector3(0.11f, 0.08f, 0.09f) },
                MaterialOverride = ember, Position = new Vector3(x, Lip + 0.06f, z),
                Rotation = new Vector3((float)r.NextDouble() * 3, (float)r.NextDouble() * 3, 0),
            });
        }
        // The tub's lamp on its post at the front, hooded: the Dig's tubs run lit, so the rails' dark
        // shows one coming (and it is a lamp, in a hole full of lamps).
        var post = new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.04f, 0.5f, 0.04f) }, MaterialOverride = iron, Position = new Vector3(TopX - 0.06f, Lip + 0.22f, TopZ + 0.02f) };
        root.AddChild(post);
        root.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.16f, 0.04f, 0.16f) }, MaterialOverride = iron, Position = new Vector3(TopX - 0.06f, Lip + 0.6f, TopZ + 0.02f) });
        root.AddChild(new MeshInstance3D
        {
            Mesh = new BoxMesh { Size = new Vector3(0.11f, 0.15f, 0.11f) }, MaterialOverride = glass,
            Position = new Vector3(TopX - 0.06f, Lip + 0.5f, TopZ + 0.02f),
        });
        root.AddChild(new OmniLight3D
        {
            Position = new Vector3(TopX - 0.06f, Lip + 0.5f, TopZ + 0.1f), LightColor = new Color(1.0f, 0.62f, 0.3f),
            LightEnergy = 1.4f, OmniRange = 4.5f, OmniAttenuation = 1.6f, ShadowEnabled = false,
        });
        return root;
    }

    static void Materials()
    {
        if (rust != null) return;
        // Rust over dark iron, patchy, by world position so no two plates match.
        var patches = new NoiseTexture2D
        {
            Width = 256, Height = 256, Seamless = true,
            Noise = new FastNoiseLite { Seed = 31, Frequency = 0.009f, FractalOctaves = 4 },
            ColorRamp = new Gradient
            {
                Colors = new[] { new Color(0.08f, 0.075f, 0.07f), new Color(0.13f, 0.1f, 0.08f), new Color(0.26f, 0.13f, 0.065f), new Color(0.34f, 0.17f, 0.08f) },
                Offsets = new[] { 0f, 0.5f, 0.72f, 1f },
            },
        };
        rust = new StandardMaterial3D
        {
            AlbedoTexture = patches, Uv1Triplanar = true, Uv1Scale = new Vector3(1.6f, 1.6f, 1.6f), Uv1WorldTriplanar = false,
            Metallic = 0.35f, Roughness = 0.78f, CullMode = BaseMaterial3D.CullModeEnum.Disabled,
        };
        iron = new StandardMaterial3D { AlbedoColor = new Color(0.07f, 0.065f, 0.06f), Metallic = 0.75f, Roughness = 0.42f };
        spoil = new StandardMaterial3D { AlbedoColor = new Color(0.11f, 0.095f, 0.085f), Roughness = 0.9f, Metallic = 0.15f };
        ember = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.25f, 0.08f, 0.03f), Roughness = 0.8f,
            EmissionEnabled = true, Emission = new Color(1.0f, 0.28f, 0.05f), EmissionEnergyMultiplier = 0.9f,
        };
        glass = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.4f, 0.25f, 0.1f), Roughness = 0.4f,
            EmissionEnabled = true, Emission = new Color(1.0f, 0.6f, 0.25f), EmissionEnergyMultiplier = 1.2f,
        };
    }

    static void AddBox(Node3D root, Vector3 size, Vector3 at, float rollZ, float pitchX) =>
        root.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = size }, MaterialOverride = iron, Position = at, Rotation = new Vector3(pitchX, 0, rollZ) });

    /// <summary>A flanged iron wheel on the rail (the flange inboard), its hub proud.</summary>
    static Node3D Wheel(Vector3 at, float side)
    {
        var w = new Node3D { Position = at };
        var tyre = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.22f, BottomRadius = 0.22f, Height = 0.09f, RadialSegments = 18 }, MaterialOverride = iron, Rotation = new Vector3(0, 0, Mathf.Pi / 2) };
        var flange = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.26f, BottomRadius = 0.26f, Height = 0.025f, RadialSegments = 18 }, MaterialOverride = iron, Rotation = new Vector3(0, 0, Mathf.Pi / 2), Position = new Vector3(-side * 0.055f, 0, 0) };
        var hub = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.07f, BottomRadius = 0.08f, Height = 0.06f, RadialSegments = 10 }, MaterialOverride = rust, Rotation = new Vector3(0, 0, Mathf.Pi / 2), Position = new Vector3(side * 0.06f, 0, 0) };
        w.AddChild(tyre);
        w.AddChild(flange);
        w.AddChild(hub);
        return w;
    }

    /// <summary>The hull: four plates flared from floor to lip, their inner faces, the lip between,
    /// and the floor; flat-shaded, each face with its own normal.</summary>
    static ArrayMesh Hull()
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        Vector3 B(float sx, float sz, float inset) => new(sx * (BotX - inset), Floor + inset, sz * (BotZ - inset));
        Vector3 T(float sx, float sz, float inset) => new(sx * (TopX - inset), Lip, sz * (TopZ - inset));
        var mid = new Vector3(0, (Floor + Lip) / 2, 0);
        // The four sides, outside (normals out) and inside (normals in), corner to corner round it.
        (float, float)[] ring = { (-1, -1), (1, -1), (1, 1), (-1, 1) };
        for (int i = 0; i < 4; i++)
        {
            var (ax, az) = ring[i];
            var (bx, bz) = ring[(i + 1) % 4];
            Quad(st, B(ax, az, 0), B(bx, bz, 0), T(bx, bz, 0), T(ax, az, 0), mid, true);
            Quad(st, B(ax, az, Wall), B(bx, bz, Wall), T(bx, bz, Wall), T(ax, az, Wall), mid, false);
            // The lip between them, facing up.
            Quad(st, T(ax, az, 0), T(bx, bz, 0), T(bx, bz, Wall), T(ax, az, Wall), mid - Vector3.Up * 5, true);
        }
        Quad(st, B(-1, -1, 0), B(1, -1, 0), B(1, 1, 0), B(-1, 1, 0), mid, true);
        Quad(st, B(-1, -1, Wall), B(1, -1, Wall), B(1, 1, Wall), B(-1, 1, Wall), mid - Vector3.Up * 5, true);
        st.GenerateTangents();
        return st.Commit();
    }

    /// <summary>Two triangles with one normal, pointing away from `from` (or toward it).</summary>
    static void Quad(SurfaceTool st, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 from, bool away)
    {
        var n = (b - a).Cross(c - a).Normalized();
        var centre = (a + b + c + d) / 4;
        if ((n.Dot(centre - from) < 0) == away) n = -n;
        foreach (var v in new[] { a, b, c, a, c, d })
        {
            st.SetNormal(n);
            st.SetUV(new Vector2(v.X + v.Z, v.Y));
            st.AddVertex(v);
        }
    }
}
