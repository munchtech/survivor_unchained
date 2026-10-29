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
    /// <summary>Card height (m; its width follows the atlas), light range (m) and energy, for each kind at scale 1.</summary>
    internal static (float H, float Range, float Energy) Spec(FlameKind kind) => kind switch
    {
        FlameKind.Candle => (0.08f, 2.5f, 0.35f),
        FlameKind.Lamp => (0.16f, 6f, 0.9f),
        FlameKind.Torch => (0.48f, 7f, 1.4f),
        FlameKind.Brazier => (0.8f, 8f, 1.8f),
        _ => (1.6f, 8f, 2f),
    };

    public static readonly Color WarmLight = new("#ffb070");
    public static readonly Color ColdLight = new("#9db8ff");

    /// <summary>A flame of the given kind at <paramref name="localAt"/> (its base) under
    /// <paramref name="parent"/>. Camp is two or three cards out of step; the rest one.
    /// With <paramref name="light"/>, its own short unshadowed light (shadows off, distance
    /// fade on); a camp fire's one shadowed light stays the caller's.
    /// <para>With <paramref name="carried"/> (a torch in a hand): faced square to the camera, its body covering what is
    /// behind it, a smaller hot card of the same flame inside it, and grown to about two and a half times its size from the play camera
    /// (a lone carried flame read as a pale wisp at chest-up and a few pixels of glint from above, judge r3).</para></summary>
    public static Flame Add(Node3D parent, Vector3 localAt, FlameKind kind, bool cold = false, float scale = 1, bool light = true, bool carried = false)
    {
        var f = new Flame { Name = kind + "Flame", Position = localAt };
        f.Build(kind, cold, scale, light, carried);
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

    /// <summary>The flicker factor at time t for a phase: 1 +- about 0.12, smooth (World.FlameFlicker).</summary>
    internal static float Flicker(float t, float ph) => SurvivorUnchained.World.FlameFlicker.At(t, ph);

    /// <summary>A carried flame's numbers (flame_mv): the outer card's and the hot inner card's, and how much both grow
    /// from the play camera (far_grow, full from 16 m).</summary>
    internal const float CarriedFarGrow = 2.4f, CarriedCoreW = 0.7f, CarriedCoreH = 0.6f;

    internal void Build(FlameKind kind, bool cold, float scale, bool light, bool carried = false)
    {
        var (h, range, e) = FlameKit.Spec(kind);
        // The card is as wide as the atlas's cell is in the world (the flame fills its cell's width).
        float w = h * FlameShader.Aspect;
        // Neighbours never in step: a phase from where it stands and who it is.
        phase = Mathf.PosMod(Position.X * 0.731f + Position.Z * 0.377f + (GetInstanceId() % 997) * 0.6180339f, 1f);
        var shader = GD.Load<Shader>(FlameShader.Path);
        (Vector3 At, float W, float H, float Ph)[] cards = kind == FlameKind.Camp
            ? new (Vector3, float, float, float)[] { (new(0, 0, 0), 1f, 1f, 0f), (new(-0.27f, 0, 0.1f), 0.85f, 0.72f, 0.37f), (new(0.25f, 0, -0.08f), 0.9f, 0.8f, 0.71f) }
            : carried
            ? new (Vector3, float, float, float)[] { (Vector3.Zero, 1f, 1f, 0f), (Vector3.Zero, CarriedCoreW, CarriedCoreH, 0f) }
            : new (Vector3, float, float, float)[] { (Vector3.Zero, 1f, 1f, 0f) };
        int n = 0;
        foreach (var (at, cw, ch, ph) in cards)
        {
            var mat = new ShaderMaterial { Shader = shader };
            FlameShader.Setup(mat, kind, cold, Mathf.PosMod(phase + ph, 1f), ph == 0 ? 1f : 0.75f);
            if (carried) FlameShader.Carried(mat, core: n > 0);
            n++;
            mats.Add(mat);
            AddChild(new MeshInstance3D
            {
                Mesh = new QuadMesh { Size = Vector2.One, CenterOffset = new Vector3(0, 0.5f, 0), Material = mat },
                Position = at * new Vector3(h, 0, h) * 0.5f * scale,
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
            // Someone else set it (the zone's level, or off): take that as the base. The first frame takes it too
            // (the zone sets a lamp's energy after wiring its flame: taken at Drive, that setting was lost).
            if (drivenLast < 0 || !Mathf.IsEqualApprox(driven.LightEnergy, drivenLast)) drivenBase = driven.LightEnergy;
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
    const string Atlas = "res://art/fx/flame/flame_kit.png", Mv = "res://art/fx/flame/flame_kit_mv.png", Meta = "res://art/fx/flame/flame_kit.json";
    static Godot.Collections.Dictionary? meta;
    static bool Sim => ResourceLoader.Exists(Atlas) && ResourceLoader.Exists(Mv) && FileAccess.FileExists(Meta);
    static Godot.Collections.Dictionary Info => meta ??= Json.ParseString(FileAccess.GetFileAsString(Meta)).AsGodotDictionary();

    /// <summary>A card's width over its height: the atlas cell's (sidecar "aspect"), or the procedural flame's.</summary>
    public static float Aspect => Sim && Info.ContainsKey("aspect") ? (float)Info["aspect"].AsDouble() : 0.5f;

    /// <summary>--fire-tilt, --fire-occlude, --fire-body, --fire-pow, --fire-core, --fire-sat: the camp fire's cards (flame_mv), for pictures.</summary>
    static readonly float CampTilt = SurvivorUnchained.Args.Num("fire-tilt", 0.35f), CampOcclude = SurvivorUnchained.Args.Num("fire-occlude", 0.8f),
        CampBody = SurvivorUnchained.Args.Num("fire-body", 0.9f), CampPow = SurvivorUnchained.Args.Num("fire-pow", 1.3f),
        CampCore = SurvivorUnchained.Args.Num("fire-core", 0.9f), CampSat = SurvivorUnchained.Args.Num("fire-sat", 1f);

    /// <summary>Small flames flicker faster than big ones.</summary>
    static float Fps(FlameKind kind) => kind switch
    {
        FlameKind.Candle => 30, FlameKind.Lamp => 28, FlameKind.Torch => 24, FlameKind.Brazier => 22, _ => 20,
    };

    /// <summary>A carried flame's card: square to the camera (tilt 1), grown from far off, its body covering what is behind;
    /// the inner (core) card drawn over the outer, hot yellow-orange and nearly solid: the brightest thing near him.</summary>
    /// <summary>--torch-tear S, --torch-tear-k K: the carried flame's near teardrop core (flame_mv tear, tear_k), for pictures.</summary>
    static readonly float CarriedTear = SurvivorUnchained.Args.Num("torch-tear", 1f), CarriedTearK = SurvivorUnchained.Args.Num("torch-tear-k", 1.6f);

    public static void Carried(ShaderMaterial mat, bool core)
    {
        // (r4: past 1 the tonemapper washed it to a pale peach wisp, and its half-covering body went pink over a light
        // tunic: the outer card about 1 and half covering (fully, its dim edges went brown), the inner card hot and solid; both drawn a
        // little toward a far camera so his arm's depth doesn't soften them away)
        mat.SetShaderParameter("tilt", 1f);
        mat.SetShaderParameter("far_grow", Flame.CarriedFarGrow);
        mat.SetShaderParameter("warm_sat", 1f);
        if (core)
        {
            mat.RenderPriority = 1;
            mat.SetShaderParameter("pull", 0.3f);
            mat.SetShaderParameter("warm_sat", 0.3f);
            mat.SetShaderParameter("occlude", 1f);
            mat.SetShaderParameter("body_k", 1.3f);
            mat.SetShaderParameter("body_pow", 0.6f);
            mat.SetShaderParameter("core_lo", 0.5f);
            mat.SetShaderParameter("core_k", 0.9f);
            // (NPC 18: near the camera a solid hot teardrop inside it, flame_mv tear; the play camera's flame untouched)
            mat.SetShaderParameter("tear", CarriedTear);
            mat.SetShaderParameter("tear_k", CarriedTearK);
        }
        else
        {
            mat.SetShaderParameter("pull", 0.25f);
            mat.SetShaderParameter("warm_sat", 0.6f);
            mat.SetShaderParameter("occlude", 0.5f);
            mat.SetShaderParameter("body_k", 1.0f);
            mat.SetShaderParameter("body_pow", 1.3f);
            mat.SetShaderParameter("core_lo", 0.85f);
            mat.SetShaderParameter("core_k", 0.5f);
        }
    }

    public static void Setup(ShaderMaterial mat, FlameKind kind, bool cold, float phase, float intensity)
    {
        mat.SetShaderParameter("phase", phase);
        mat.SetShaderParameter("cold", cold ? 1f : 0f);
        mat.SetShaderParameter("intensity", intensity);
        mat.SetShaderParameter("noise_tex", NoiseTex.Get());
        bool sim = Sim;
        mat.SetShaderParameter("procedural", !sim);
        float fps = Fps(kind);
        if (sim)
        {
            var meta = Info;
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
        if (kind == FlameKind.Camp)
        {
            // From the play camera (23 m, 55 degrees down) the upright cards were foreshortened into a cream blob over
            // the coals: leaned back toward the camera (none at a level close-up), the body deeper orange with red tips
            // that show, and the middle covering what is behind it (the log's lit edge showed through the flame).
            mat.SetShaderParameter("tilt", CampTilt);
            mat.SetShaderParameter("occlude", CampOcclude);
            mat.SetShaderParameter("body_k", CampBody);
            mat.SetShaderParameter("body_pow", CampPow);
            mat.SetShaderParameter("core_k", CampCore);
            mat.SetShaderParameter("warm_sat", CampSat);
        }
        // --flame-tune "body_k=0.4,core_k=1.4": the shader's numbers, for pictures.
        if (SurvivorUnchained.Args.Get("flame-tune") is string tune)
            foreach (var kv in tune.Split(',', System.StringSplitOptions.RemoveEmptyEntries))
            {
                var p = kv.Split('=');
                if (p.Length == 2) mat.SetShaderParameter(p[0].Trim(), float.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture) * (p[0].Trim() == "intensity" ? intensity : 1));
            }
    }
}
