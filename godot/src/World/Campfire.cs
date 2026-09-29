using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A campfire: a ring of the nature kit's stones, logs in the kit's bark,
/// and a fire of GPU particles (flame, embers, smoke) with its own light.
/// The web game's fires are a few meshes and a glow; this is what an engine
/// gives for the same effort.
/// </summary>
public static class Campfire
{
    /// <param name="ring">Lay its own stones and logs (not where the web
    /// game's are already laid).</param>
    /// <param name="parts">Which of flames, embers, smoke (for telling
    /// them apart).</param>
    public static Node3D Build(Vector3 at, float size = 1, bool ring = true, string parts = "flames,embers,smoke")
    {
        var root = new Node3D { Name = "Campfire", Position = at };
        if (ring) Ring(root, size);
        if (parts.Contains("flames")) root.AddChild(Flames(size));
        if (parts.Contains("embers")) root.AddChild(Embers(size));
        if (parts.Contains("smoke")) root.AddChild(Smoke(size));
        return root;
    }

    static void Ring(Node3D root, float size)
    {
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

    static GpuParticles3D Flames(float size)
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.18f * size,
            Direction = Vector3.Up, Spread = 10, InitialVelocityMin = 0.7f * size, InitialVelocityMax = 1.3f * size,
            Gravity = new Vector3(0, 0.8f, 0), DampingMin = 0.5f, DampingMax = 1f,
            ScaleMin = 0.55f * size, ScaleMax = 0.95f * size,
            ScaleCurve = Curve((0, 0.6f), (0.3f, 1f), (1, 0.35f)),
            AngleMin = -10, AngleMax = 10,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 0.6f, TurbulenceNoiseScale = 2.5f, TurbulenceInfluenceMin = 0.05f, TurbulenceInfluenceMax = 0.12f,
        };
        // The colour, the licking edge and how much light it adds are the
        // flame shader's (shaders/flame.gdshader).
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flame.gdshader") };
        var (first, count) = Sprites.Range("muzzle");
        mat.SetShaderParameter("sprites", Sprites.Array);
        mat.SetShaderParameter("first_tongue", (float)first);
        mat.SetShaderParameter("tongues", (float)count);
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        mat.SetShaderParameter("glow", 0.55f);
        return new GpuParticles3D
        {
            Name = "Flames", Amount = 16, Lifetime = 0.8, ProcessMaterial = p, Position = new Vector3(0, 0.1f, 0),
            DrawPass1 = new QuadMesh { Size = new Vector2(0.45f, 0.9f), CenterOffset = new Vector3(0, 0.3f, 0), Material = mat },
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
            // Hot, not blinding: a speck many times white is spread by the
            // glow into a ball.
            ColorRamp = Ramp((0, new Color(1.8f, 0.9f, 0.3f, 1)), (0.7f, new Color(1.2f, 0.4f, 0.08f, 1)), (1, new Color(0.6f, 0.1f, 0.02f, 0))),
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
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Sprites.Puff, false) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Preprocess = 4.0,
        };
    }

    /// <summary>A chimney's smoke: a thin grey thread leaning with the wind
    /// (the web game's ZoneKit.chimney), grey by day, dark after it.</summary>
    public static GpuParticles3D ChimneySmoke()
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Sphere, EmissionSphereRadius = 0.12f,
            Direction = new Vector3(0.4f, 1, 0.1f).Normalized(), Spread = 8, InitialVelocityMin = 0.9f, InitialVelocityMax = 1.2f,
            DampingMin = 0.2f, DampingMax = 0.3f, Gravity = new Vector3(0.12f, 0, 0.03f),
            ScaleMin = 0.5f, ScaleMax = 0.6f, ScaleCurve = Curve((0, 1f), (1, 5.2f)),
            AngleMin = -180, AngleMax = 180, AngularVelocityMin = -15, AngularVelocityMax = 15,
        };
        var smoke = new GpuParticles3D
        {
            Name = "Chimney", Amount = 15, Lifetime = 4.5, ProcessMaterial = p, Preprocess = 4.5,
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Sprites.Puff, false) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        ChimneyLook(smoke, false);
        return smoke;
    }

    public static void ChimneyLook(GpuParticles3D smoke, bool night)
    {
        // The web game's colours (linear here, its alpha along the life).
        Color a = new Color(night ? "#2a2c34" : "#8a8680").SrgbToLinear(), b = new Color(night ? "#14161c" : "#6a6864").SrgbToLinear();
        float alpha = night ? 0.3f : 0.22f;
        ((ParticleProcessMaterial)smoke.ProcessMaterial).ColorRamp =
            Ramp((0, a with { A = 0 }), (0.15f, a with { A = alpha }), (1, b with { A = 0 }));
    }

    /// <summary>Moths about a lamp after dark: pale specks that dart and
    /// circle (the web game's ZoneKit.moths).</summary>
    public static GpuParticles3D Moths()
    {
        var p = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Ring, EmissionRingRadius = 0.5f, EmissionRingInnerRadius = 0.3f,
            EmissionRingHeight = 0.6f, EmissionRingAxis = Vector3.Up,
            Direction = Vector3.Right, Spread = 180, InitialVelocityMin = 0.8f, InitialVelocityMax = 1.4f,
            Gravity = Vector3.Zero, DampingMin = 0.3f, DampingMax = 0.5f, ScaleMin = 0.05f, ScaleMax = 0.06f,
            TurbulenceEnabled = true, TurbulenceNoiseStrength = 3f, TurbulenceNoiseScale = 0.8f, TurbulenceInfluenceMin = 0.3f, TurbulenceInfluenceMax = 0.6f,
            ColorRamp = Ramp((0, new Color(1.6f, 1.45f, 1.1f, 0)), (0.1f, new Color(1.6f, 1.45f, 1.1f, 0.9f)), (1, new Color(1.3f, 1.05f, 0.6f, 0))),
        };
        return new GpuParticles3D
        {
            Name = "Moths", Amount = 7, Lifetime = 2.1, ProcessMaterial = p, Emitting = false,
            DrawPass1 = new QuadMesh { Size = new Vector2(1, 1), Material = Sprite(Blob(Colors.White, new Color(1, 1, 1, 0)), true) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
    }
}
