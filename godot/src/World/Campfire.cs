using Godot;

namespace SurvivorUnchained.World;

/// <summary>
/// A campfire: a ring of the nature kit's stones, logs in the kit's bark,
/// and a fire of GPU particles (flame, embers, smoke) with its own light.
/// The web game's fires are a few meshes and a glow; this is what an engine
/// gives for the same effort.
/// </summary>
public static class Campfire
{
    public static Node3D Build(Vector3 at, float size = 1)
    {
        var root = new Node3D { Name = "Campfire", Position = at };
        // The ring: kit pebbles, turned and sized a little differently each.
        var rng = new RandomNumberGenerator { Seed = 11 };
        for (int i = 0; i < 9; i++)
        {
            float a = i / 9f * Mathf.Tau + rng.Randf() * 0.2f;
            var stone = GD.Load<PackedScene>($"res://assets/env/nature/Pebble_Round_{1 + i % 5}.gltf").Instantiate<Node3D>();
            stone.Position = new Vector3(Mathf.Cos(a) * 0.62f, -0.05f, Mathf.Sin(a) * 0.62f) * size;
            stone.Rotation = new Vector3(0, rng.Randf() * Mathf.Tau, 0);
            stone.Scale = Vector3.One * (1.6f + rng.Randf() * 0.5f) * size;
            root.AddChild(stone);
        }
        // Logs laid in a star, charred toward the middle.
        var bark = new StandardMaterial3D
        {
            AlbedoTexture = GD.Load<Texture2D>("res://assets/env/nature/Bark_DeadTree.ktx2"),
            NormalEnabled = true, NormalTexture = GD.Load<Texture2D>("res://assets/env/nature/Bark_DeadTree_Normal.ktx2"),
            Uv1Scale = new Vector3(1, 2, 1), Roughness = 0.9f, AlbedoColor = new Color(0.55f, 0.5f, 0.46f),
        };
        for (int i = 0; i < 4; i++)
        {
            float a = i / 4f * Mathf.Tau + 0.4f;
            var log = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.07f * size, BottomRadius = 0.08f * size, Height = 0.8f * size, RadialSegments = 10 }, MaterialOverride = bark };
            log.Position = new Vector3(Mathf.Cos(a) * 0.22f, 0.09f, Mathf.Sin(a) * 0.22f) * size;
            log.Basis = new Basis(new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a)), Mathf.DegToRad(72)) ;
            root.AddChild(log);
        }
        root.AddChild(Flames(size));
        root.AddChild(Embers(size));
        root.AddChild(Smoke(size));
        return root;
    }

    /// <summary>A soft round sprite: bright middle, nothing at the edge.</summary>
    static Texture2D Blob(Color inner, Color outer)
    {
        var g = new Gradient();
        g.SetColor(0, inner);
        g.SetColor(1, outer);
        return new GradientTexture2D
        {
            Gradient = g, Fill = GradientTexture2D.FillEnum.Radial, Width = 64, Height = 64,
            FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
        };
    }

    static StandardMaterial3D Sprite(Texture2D tex, bool additive)
    {
        return new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded,
            Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            BlendMode = additive ? BaseMaterial3D.BlendModeEnum.Add : BaseMaterial3D.BlendModeEnum.Mix,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Particles,
            VertexColorUseAsAlbedo = true,
            AlbedoTexture = tex,
            DepthDrawMode = BaseMaterial3D.DepthDrawModeEnum.Disabled,
            NoDepthTest = false,
        };
    }

    /// <summary>A colour over a particle's life; HDR, so a flame can be
    /// brighter than white and bloom.</summary>
    static GradientTexture1D Ramp(params (float At, Color C)[] stops)
    {
        var g = new Gradient();
        g.Offsets = System.Array.ConvertAll(stops, s => s.At);
        g.Colors = System.Array.ConvertAll(stops, s => s.C);
        return new GradientTexture1D { Gradient = g, UseHdr = true };
    }

    static CurveTexture Curve(params (float At, float V)[] pts)
    {
        var c = new Curve();
        foreach (var (at, v) in pts) c.AddPoint(new Vector2(at, v));
        return new CurveTexture { Curve = c };
    }

    /// <summary>A tongue of flame: a teardrop, broad and bright at the root,
    /// narrowing to a ragged tip, its edge broken by noise.</summary>
    static Texture2D FlameTongue()
    {
        const int W = 64, H = 128;
        var img = Image.CreateEmpty(W, H, false, Image.Format.Rgba8);
        var noise = new FastNoiseLite { Seed = 4, Frequency = 0.08f };
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                float v = 1 - (float)y / H;          // 0 at the root, 1 at the tip
                float half = 0.46f * Mathf.Pow(1 - v, 0.55f) * (1 + 0.25f * Mathf.Sin(v * 3)) + 0.02f;
                float u = Mathf.Abs((x + 0.5f) / W - 0.5f) / Mathf.Max(half, 0.001f);
                float n = noise.GetNoise2D(x * 1.5f, y) * 0.35f;
                float a = (1 - Mathf.SmoothStep(0.55f, 1f, u + n)) * Mathf.SmoothStep(0f, 0.12f, v) * (1 - Mathf.SmoothStep(0.75f, 1f, v + n * 0.5f));
                float hot = 1 - Mathf.SmoothStep(0f, 0.7f, u);
                img.SetPixel(x, y, new Color(1, 0.85f + 0.15f * hot, 0.7f + 0.3f * hot, Mathf.Clamp(a, 0, 1)));
            }
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    static GpuParticles3D Flames(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.2f * size,
            Direction = Vector3.Up, Spread = 12, InitialVelocityMin = 0.9f * size, InitialVelocityMax = 1.6f * size,
            Gravity = new Vector3(0, 0.6f, 0), DampingMin = 0.5f, DampingMax = 1f,
            ScaleMin = 0.45f * size, ScaleMax = 0.8f * size,
            ScaleCurve = Curve((0, 0.5f), (0.25f, 1f), (1, 0.2f)),
            AngleMin = -12, AngleMax = 12,
            ColorRamp = Ramp((0, new Color(1.3f, 0.75f, 0.3f, 0)), (0.15f, new Color(1.25f, 0.5f, 0.12f, 0.5f)), (0.6f, new Color(0.8f, 0.2f, 0.04f, 0.3f)), (1, new Color(0.25f, 0.04f, 0.01f, 0))),
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.6f, TurbulenceNoiseScale = 2.5f, TurbulenceInfluenceMin = 0.05f, TurbulenceInfluenceMax = 0.15f,
        };
        return new GpuParticles3D
        {
            Name = "Flames", Amount = 64, Lifetime = 0.75, ProcessMaterial = p, Position = new Vector3(0, 0.15f, 0),
            DrawPass1 = new QuadMesh { Size = new Vector2(0.4f, 0.8f), Material = Sprite(FlameTongue(), true) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 1.0,
        };
    }

    static GpuParticles3D Embers(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.25f * size,
            Direction = Vector3.Up, Spread = 25, InitialVelocityMin = 1.5f, InitialVelocityMax = 3.2f,
            Gravity = new Vector3(0, 0.4f, 0), ScaleMin = 0.03f, ScaleMax = 0.06f,
            ColorRamp = Ramp((0, new Color(5f, 2.5f, 0.8f, 1)), (0.7f, new Color(3f, 0.9f, 0.2f, 1)), (1, new Color(1f, 0.2f, 0.05f, 0))),
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 2f, TurbulenceNoiseScale = 1.5f, TurbulenceInfluenceMin = 0.2f, TurbulenceInfluenceMax = 0.4f,
        };
        return new GpuParticles3D
        {
            Name = "Embers", Amount = 24, Lifetime = 2.2, ProcessMaterial = p, Position = new Vector3(0, 0.4f, 0),
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Blob(Colors.White, new Color(1, 1, 1, 0)), true) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 2.0,
        };
    }

    static GpuParticles3D Smoke(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.2f * size,
            Direction = Vector3.Up, Spread = 8, InitialVelocityMin = 0.6f, InitialVelocityMax = 1f,
            Gravity = new Vector3(0.25f, 0.15f, 0), ScaleMin = 0.8f, ScaleMax = 1.4f,
            ScaleCurve = Curve((0, 0.5f), (1, 2.6f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -20, AngularVelocityMax = 20,
            // Dark: night smoke is barely lit (these are linear values; 0.14
            // would show as a pale grey).
            ColorRamp = Ramp((0, new Color(0.03f, 0.028f, 0.025f, 0)), (0.2f, new Color(0.035f, 0.032f, 0.03f, 0.45f)), (1, new Color(0.045f, 0.045f, 0.05f, 0))),
        };
        return new GpuParticles3D
        {
            Name = "Smoke", Amount = 20, Lifetime = 4.5, ProcessMaterial = p, Position = new Vector3(0, 1.1f, 0),
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Blob(Colors.White, new Color(1, 1, 1, 0)), false) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 4.0,
        };
    }
}
