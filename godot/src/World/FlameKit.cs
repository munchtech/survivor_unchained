using Godot;

namespace SurvivorUnchained.View;

/// <summary>The sizes of flame the kit makes; each has its own card size and light.</summary>
public enum FlameKind { Candle, Lamp, Torch, Brazier, Camp }

/// <summary>
/// The shared flame kit (look bible 10_props_flames, "The trick"): every flame is a
/// flipbook card played with motion vectors (shaders/flame_mv.gdshader on
/// art/fx/fb/flame_kit), a light flickering by noise (about +-12% energy, never
/// position), and whatever surfaces that light reaches. Warm or the Warden's cold
/// blue share one atlas; the colour is a ramp in the shader.
/// </summary>
public static class FlameKit
{
    /// <summary>Card width and height (m), light range (m) and energy, for each kind at scale 1.</summary>
    internal static (float W, float H, float Range, float Energy) Spec(FlameKind kind) => kind switch
    {
        FlameKind.Candle => (0.04f, 0.08f, 2.5f, 0.35f),
        FlameKind.Lamp => (0.08f, 0.16f, 6f, 0.9f),
        FlameKind.Torch => (0.24f, 0.48f, 7f, 1.4f),
        FlameKind.Brazier => (0.4f, 0.8f, 8f, 1.8f),
        _ => (0.8f, 1.6f, 8f, 2f),
    };

    public static readonly Color WarmLight = new("#ffb070");
    public static readonly Color ColdLight = new("#9db8ff");

    /// <summary>A flame of the given kind at <paramref name="localAt"/> (its base) under
    /// <paramref name="parent"/>. Camp is two or three cards out of step; the rest one.
    /// With <paramref name="light"/>, its own short unshadowed light (shadows off, distance
    /// fade on); a camp fire's one shadowed light stays the caller's.</summary>
    public static Flame Add(Node3D parent, Vector3 localAt, FlameKind kind, bool cold = false, float scale = 1, bool light = true)
    {
        var f = new Flame { Name = kind + "Flame", Position = localAt };
        f.Build(kind, cold, scale, light);
        parent.AddChild(f);
        return f;
    }
}

/// <summary>One flame of the kit: its cards and (optionally) its light.</summary>
public partial class Flame : Node3D
{
    /// <summary>Its own light (null if built without one); a driven zone light is not here.</summary>
    public OmniLight3D? Light;
    OmniLight3D? driven;
    float drivenBase, drivenLast = -1;
    float energy = 1, time, phase;
    bool lit = true;
    readonly System.Collections.Generic.List<ShaderMaterial> mats = new();
    static readonly FastNoiseLite noise = new() { NoiseType = FastNoiseLite.NoiseTypeEnum.Simplex, Frequency = 1f, Seed = 7 };

    /// <summary>Its light's energy before the flicker.</summary>
    public float Energy { get => energy; set => energy = value; }

    /// <summary>Off: the cards hidden and its light (and a driven light) at zero.</summary>
    public bool Lit
    {
        get => lit;
        set
        {
            lit = value;
            Visible = value;
            if (Light != null) Light.LightEnergy = value ? Light.LightEnergy : 0;
            if (driven != null && !value) { driven.LightEnergy = 0; drivenLast = 0; }
        }
    }

    /// <summary>Flicker an existing (zone) light's energy around its current base. The zone
    /// keeps the light and its on/off: whenever something else sets its energy, that becomes
    /// the new base.</summary>
    public void Drive(OmniLight3D existing)
    {
        driven = existing;
        drivenBase = existing.LightEnergy;
        drivenLast = -1;
    }

    /// <summary>The flicker factor at time t for a phase: 1 +- about 0.12, smooth (two octaves of noise).</summary>
    internal static float Flicker(float t, float ph)
    {
        float n = noise.GetNoise2D(t * 2.3f, ph * 37f) * 0.75f + noise.GetNoise2D(t * 6.1f, ph * 37f + 91f) * 0.25f;
        return 1 + Mathf.Clamp(n * 0.2f, -0.13f, 0.13f);
    }

    internal void Build(FlameKind kind, bool cold, float scale, bool light)
    {
        var (w, h, range, e) = FlameKit.Spec(kind);
        // Neighbours never in step: a phase from where it stands and who it is.
        phase = Mathf.PosMod(Position.X * 0.731f + Position.Z * 0.377f + (GetInstanceId() % 997) * 0.6180339f, 1f);
        var shader = GD.Load<Shader>(FlameShader.Path);
        (Vector3 At, float W, float H, float Ph)[] cards = kind == FlameKind.Camp
            ? new (Vector3, float, float, float)[] { (new(0, 0, 0), 1f, 1f, 0f), (new(-0.28f, 0, 0.1f), 0.8f, 0.72f, 0.37f), (new(0.26f, 0, -0.08f), 0.85f, 0.78f, 0.71f) }
            : new (Vector3, float, float, float)[] { (Vector3.Zero, 1f, 1f, 0f) };
        foreach (var (at, cw, ch, ph) in cards)
        {
            var mat = new ShaderMaterial { Shader = shader };
            FlameShader.Setup(mat, kind, cold, Mathf.PosMod(phase + ph, 1f), ph == 0 ? 1f : 0.75f);
            mats.Add(mat);
            AddChild(new MeshInstance3D
            {
                Mesh = new QuadMesh { Size = Vector2.One, CenterOffset = new Vector3(0, 0.5f, 0), Material = mat },
                Position = at * new Vector3(w, 0, w) * scale,
                Scale = new Vector3(w * cw, h * ch, 1) * scale,
                CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            });
        }
        if (!light) return;
        energy = e;
        Light = new OmniLight3D
        {
            Name = "Light", Position = new Vector3(0, h * 0.35f * scale, 0),
            LightColor = cold ? FlameKit.ColdLight : FlameKit.WarmLight, LightEnergy = e,
            OmniRange = range * Mathf.Max(scale, 0.5f), OmniAttenuation = 1.4f, ShadowEnabled = false, LightSpecular = 0.25f,
            DistanceFadeEnabled = true, DistanceFadeBegin = 40, DistanceFadeLength = 12,
        };
        AddChild(Light);
    }

    public override void _Process(double delta)
    {
        time += (float)delta;
        if (!lit) return;
        float f = Flicker(time, phase);
        if (Light != null) Light.LightEnergy = energy * f;
        if (driven != null && GodotObject.IsInstanceValid(driven))
        {
            // Someone else set it (the zone's level, or off): take that as the base.
            if (drivenLast >= 0 && !Mathf.IsEqualApprox(driven.LightEnergy, drivenLast)) drivenBase = driven.LightEnergy;
            drivenLast = drivenBase * f;
            driven.LightEnergy = drivenLast;
        }
    }
}

/// <summary>The kit's shader, atlas and motion vectors, and their parameters. Without the atlas the
/// shader draws its procedural flame.</summary>
static class FlameShader
{
    public const string Path = "res://shaders/flame_mv.gdshader";
    const string Atlas = "res://art/fx/fb/flame_kit.png", Mv = "res://art/fx/fb/flame_kit_mv.png", Meta = "res://art/fx/fb/flame_kit.json";
    static Godot.Collections.Dictionary? meta;

    /// <summary>Small flames flicker faster than big ones.</summary>
    static float Fps(FlameKind kind) => kind switch
    {
        FlameKind.Candle => 30, FlameKind.Lamp => 28, FlameKind.Torch => 24, FlameKind.Brazier => 22, _ => 20,
    };

    public static void Setup(ShaderMaterial mat, FlameKind kind, bool cold, float phase, float intensity)
    {
        mat.SetShaderParameter("phase", phase);
        mat.SetShaderParameter("cold", cold ? 1f : 0f);
        mat.SetShaderParameter("intensity", intensity);
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        bool sim = ResourceLoader.Exists(Atlas) && ResourceLoader.Exists(Mv) && FileAccess.FileExists(Meta);
        mat.SetShaderParameter("procedural", !sim);
        float fps = Fps(kind);
        if (sim)
        {
            meta ??= Json.ParseString(FileAccess.GetFileAsString(Meta)).AsGodotDictionary();
            mat.SetShaderParameter("atlas", GD.Load<Texture2D>(Atlas));
            mat.SetShaderParameter("mv_atlas", GD.Load<Texture2D>(Mv));
            mat.SetShaderParameter("grid", (int)meta["grid"].AsDouble());
            mat.SetShaderParameter("frames", (int)meta["frames"].AsDouble());
            mat.SetShaderParameter("mv_scale", (float)meta["mv_scale"].AsDouble());
            var cell = meta["cell"].AsGodotArray();
            mat.SetShaderParameter("cell_px", new Vector2((float)cell[0].AsDouble(), (float)cell[1].AsDouble()));
            fps *= (float)meta["fps"].AsDouble() / 24f;
        }
        mat.SetShaderParameter("fps", fps);
    }
}
