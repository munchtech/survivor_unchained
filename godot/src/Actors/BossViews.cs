using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// The Ford-Warden (the web game's render/bossViews.ts): a watchman of the
/// old Watch, dead and got up, grown huge, with the greatsword and the lamp
/// he carried in life. Bosses get a full skeleton, a light of their own and
/// hand-picked motion; the zone says what he is doing (his pose) and this
/// turns it into a clip and keeps the body where the fight has it.
/// </summary>
public partial class WardenView : Node3D, IBossView
{
    readonly PersonView view;
    readonly OmniLight3D light;
    readonly Node3D lamp, grip;
    readonly List<StandardMaterial3D> eyes = new(), skin = new();
    string pose = "";
    double heading, time, flash;
    public double Glow { get; set; } = 1;
    /// <summary>Whether his lamp burns (it goes out in the river in C03).</summary>
    public bool LampLit { get; set; } = true;
    /// <summary>A cinematic's say over the flame's own look: its core's brightness (1 = as built) and hue,
    /// and its halo's strength (C02's night: the core was a flat white disc, the brightest thing on screen).</summary>
    public float FlameLevel { get => flameLevel; set { flameLevel = value; Tint(); } }
    public Color? FlameColor { get => flameColor; set { flameColor = value; Tint(); } }
    public float HaloLevel { get => haloLevel; set { haloLevel = value; Tint(); } }
    float flameLevel = 1, haloLevel = 1;
    Color? flameColor;
    LampFire? fire;
    void Tint() => fire?.Look(flameColor, flameLevel, haloLevel);
    /// <summary>Where his lamp hangs (for framing a cinematic on it).</summary>
    public Vector3 LampAt => lamp.GlobalPosition;
    /// <summary>The body, for a cinematic that moves and poses him itself.</summary>
    public PersonView Body => view;
    const float Size = 2.6f;
    /// <summary>His kit's colour: wool and leather dark with the river.</summary>
    static readonly Color Soaked = new("#3a3e44");
    /// <summary>The ranger's cloth band (People's MI_Ranger), measured against brighter paint.</summary>
    static readonly People.DyeMask SoakedMask = new(new Vector2(0.17f, 0.45f), new Vector2(0.25f, 1), new Vector2(0.03f, 1), 0.3f);

    public WardenView()
    {
        Name = "FordWarden";
        // His own baked package (art/npc/ford_warden); the Quaternius townsman only if the package is missing.
        bool package = NpcPackage.Read("ford_warden") != null;
        if (!package) GD.Print("WardenView: no ford_warden package, using the old townsman");
        var spec = package ? new PersonSpec { Sex = Sex.Male, Body = "npc:ford_warden" } : new PersonSpec
        {
            Sex = Sex.Male, Outfit = Lore.OutfitFor(Sex.Male, "ranger", true, true), Beard = true, HairColor = "#6a6660", Skin = "#8e9680",
            Dye = new Dye { Cloth = "#3a3e44" },
        };
        view = new PersonView(spec, new Held { Right = "watch_blade" }, 0.8 * Size)
        { WalkClip = "Zombie_Walk_Fwd_Loop", RunClip = "Zombie_Walk_Fwd_Loop" };
        AddChild(view);
        foreach (var mi in view.Person.Meshes)
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is StandardMaterial3D m)
                {
                    m.EmissionEnabled = true;
                    if (m.ResourceName.Contains("Eye")) { m.Emission = new Color("#7ac8ff"); eyes.Add(m); }
                    else { m.Emission = Colors.Black; skin.Add(m); }
                }
        // His kit's cloth is the ranger's green paint dyed, and the dye is as bright as
        // the paint under it over the mask's brightness. The ranger's mask is set for a
        // townsman's dark green, so the hood's and mantle's light greens came out near
        // white, and read as a white cowl round the face C02 holds in close-up. Until he
        // has his own model (docs/art/MODELS_TO_MAKE.md), his dye is measured against
        // brighter paint, so all of it comes out dark with the river.
        if (package) { WardenLook.Wet(view.Person, NpcPackage.Dir("ford_warden")); EyeLights(); Pendant.Attach(view.Person.Skeleton, "spine_03", "Spine_03"); if (System.Environment.GetEnvironmentVariable("WARDEN_HOODCHECK") == "1") view.Person.Skeleton.AddChild(new HoodCheck()); }
        else
        foreach (var mi in view.Person.Meshes)
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial dyed && dyed.ResourceName == "MI_Ranger")
                    People.SetDye(dyed, SoakedMask, Soaked);
        // The lantern hangs from the left fist by its bail, plumb, whatever the arm
        // does (Hang): the grip is in the closed fist, where Arms.Hold puts a held thing.
        var at = new BoneAttachment3D { BoneName = "hand_l" };
        view.Person.Skeleton.AddChild(at);
        grip = new Node3D { Position = new Vector3(0, 0.075f, 0) };
        at.AddChild(grip);
        lamp = LampIron.Make(Bail);
        AddChild(lamp);
        // The flame (LampIron.Fire: the kit's cold flame and a soft glow; the glass lit by it).
        fire = LampIron.Fire(lamp);
        Tint();
        // LightSize: soft shadows (the cage's bars throw broad soft stripes, not hard lines, from the flame).
        light = new OmniLight3D { LightColor = new Color("#8ac8ff"), OmniRange = 16, OmniAttenuation = 1.3f, LightEnergy = 0, ShadowEnabled = false, LightSize = 0.012f };
        AddChild(light);
    }

    static readonly Color EyeBlue = new("#7ac8ff");

    /// <summary>Two small glowing points in his hood, on the head bone at the manifest's head.eyes sockets
    /// (Head-bone local, metres). Unshaded, so Light() drives their albedo too: eyes off is really off.</summary>
    void EyeLights()
    {
        // (WARDEN_EYES=0: no eye-lights, for judging his face by itself; Warden 6 face gate)
        if (System.Environment.GetEnvironmentVariable("WARDEN_EYES") == "0") return;
        Vector3 l = new(0.0352f, 0.0833f, 0.1582f), r = new(-0.0352f, 0.0832f, 0.1593f);
        var d = Json.ParseString(FileAccess.GetFileAsString($"{NpcPackage.Dir("ford_warden")}/manifest.json")).AsGodotDictionary();
        if (d.TryGetValue("head", out var hv) && hv.VariantType == Godot.Variant.Type.Dictionary
            && hv.AsGodotDictionary().TryGetValue("eyes", out var ev) && ev.VariantType == Godot.Variant.Type.Dictionary)
        {
            var e = ev.AsGodotDictionary();
            static Vector3 P(Godot.Variant a) { var x = a.AsGodotArray(); return new Vector3((float)x[0], (float)x[1], (float)x[2]); }
            if (e.TryGetValue("l", out var lv) && e.TryGetValue("r", out var rv)) { l = P(lv); r = P(rv); }
        }
        // (WardenLook: a white-hot core going to cyan, a soft glow, one tiny cold light on brow, cheekbones and beard)
        eyeLook = WardenLook.Eyes(view.Person.Skeleton, l, r);
    }

    (StandardMaterial3D Core, StandardMaterial3D Glow, OmniLight3D Glint)? eyeLook;

    public void SetPose(string p)
    {
        if (p == pose) return;
        pose = p;
        var v = view;
        switch (p)
        {
            // Lying where he fell (the first frame of getting up), then up.
            case "sleep": v.Act("LayToIdle", 0.0001, true); break;
            case "wake": v.Loop("Sword_Idle", 0); v.Act("LayToIdle", 0.6, true); break;
            case "walk": case "idle": v.Loop("Sword_Idle", 0.2); break;
            case "windup": v.Loop("Sword_Idle", 0.1, 0.5); break;
            case "cleave": v.Act("Sword_Attack", 1.1); break;
            case "charge-windup": v.Loop("Idle_Shield_Loop", 0.15); break;
            case "charge": v.Loop("Jog_Fwd_Loop", 0.1, 1.6); break;
            case "stunned": v.Act("Hit_Head", 0.7, true); break;
            case "channel": v.Loop("Spell_Simple_Idle_Loop", 0.3); break;
            case "dead": v.Act("Death01", 0.7, true); break;
        }
    }

    /// <summary>Back to walking after a held pose.</summary>
    public void Release()
    {
        pose = "walk";
        view.Loop("Sword_Idle", 0.2);
    }

    public void Update(Enemy? e, double x, double y, double z, double facing, double dt)
    {
        time += dt;
        Visible = true;
        Position = new Vector3((float)x, (float)y, (float)z);
        heading = Core.MathX.DampAngle(heading, facing, 14, dt);
        Rotation = new Vector3(0, (float)heading, 0);
        if (e != null && pose is "walk" or "idle") view.Locomotion(Math.Sqrt(e.Vx * e.Vx + e.Vz * e.Vz) * 1.2);
        flash = Math.Max(flash - dt * 6, e?.Flash ?? 0);
        foreach (var m in skin) m.Emission = new Color(1f, 0.8f, 0.6f) * (float)(flash * 0.25);
        double g = Glow * (pose == "sleep" ? 0.35 : 1) * (pose == "dead" ? 0 : 1);
        Hang();
        Light(g, (float)y, false);
        lamp.Visible = pose != "dead" || g > 0.01;
        fire!.Lit(LampLit && g > 0.01);
    }

    /// <summary>A cinematic's frame: the eyes and the lamp at the glow it sets,
    /// wherever the cinematic has put the body.</summary>
    public void Shine(double dt)
    {
        time += dt;
        Visible = true;
        Hang();
        Light(Glow, view.GlobalPosition.Y, true);
        lamp.Visible = true;
        fire!.Lit(LampLit && Glow > 0.01);
    }

    /// <summary>The bail's length, ring to fist, in the lamp's own measure.</summary>
    const float Bail = 0.07f;

    /// <summary>The lamp hangs straight down from his fist on its bail, turned with him.</summary>
    void Hang()
    {
        // As big as it was in his hand (the body is scaled up to a giant's).
        float s = grip.GlobalTransform.Basis.Scale.X;
        lamp.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, GlobalRotation.Y).Scaled(Vector3.One * s),
            grip.GlobalPosition - new Vector3(0, Bail * s, 0));
    }

    /// <summary>The eyes and the lamp's light; atFlame (a cinematic): the light burns at the flame itself, inside the
    /// cage, so the bars throw their shadows over him and whatever he holds it to.</summary>
    void Light(double g, float ground, bool atFlame)
    {
        if (eyeLook is { } el) WardenLook.Glow(el, g, time);
        foreach (var m in eyes)
        {
            float k = (float)(g <= 0.001 ? 0 : 1.2 + g * 2.4 + Math.Sin(time * 5) * g * 0.5);
            m.EmissionEnergyMultiplier = k;
            // (the unshaded eye lights show their albedo, so it follows the glow: dark at 0)
            if (m.ShadingMode == BaseMaterial3D.ShadingModeEnum.Unshaded) { float b = Mathf.Clamp(k / 3.6f, 0, 1.5f); m.AlbedoColor = new Color(EyeBlue.R * b, EyeBlue.G * b, EyeBlue.B * b); }
        }
        // The light is the lamp in his fist, hung a little out from the body.
        double i = LampLit ? g * (5 + Math.Sin(time * 3.1) * 0.8 + (pose == "channel" ? 4 + Math.Sin(time * 14) * 2 : 0)) : 0;
        light.LightEnergy = (float)(i / Math.PI);
        // The one shadowed positional light of the scene, ahead of any lamp (ShadowLamp).
        if (light.LightEnergy > 0) ShadowLamp.Offer(light, 1); else ShadowLamp.Withdraw(light);
        if (atFlame && fire != null) { light.GlobalPosition = fire.At; return; }
        var at = lamp.GlobalPosition;
        light.GlobalPosition = new Vector3(at.X, Mathf.Max(at.Y, ground + 1.2f) + 0.8f, at.Z);
        // (its streak on the water in the flame's hue, not the light's blue: C03 s2)
        if (light.IsInsideTree()) Water.StreakTint(light, flameColor);
    }

    // Explicit, so they do not shadow Godot's own Hide() and Dispose().
    void IBossView.Hide() => Visible = false;
    void IBossView.Dispose() => QueueFree();

    public override void _ExitTree() => ShadowLamp.Withdraw(light);
}

/// <summary>A bright thing with a light of its own (the Warden's heart).</summary>
/// <summary>The Kindling's ember-core (shaders/ember_core.gdshader): a dark crust knobbled out of a
/// sphere, its fissures glowing from inside and widening as it is broken, its own warm light.</summary>
public partial class EmberCoreView : Node3D, IOrb
{
    readonly MeshInstance3D lump;
    readonly ShaderMaterial mat;
    readonly OmniLight3D light;

    public EmberCoreView(double size)
    {
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ember_core.gdshader") };
        lump = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = (float)size, Height = (float)size * 2, RadialSegments = 40, Rings = 20 },
            MaterialOverride = mat,
        };
        AddChild(lump);
        light = new OmniLight3D { LightColor = new Color("#ff7a2a"), OmniRange = 9, OmniAttenuation = 1.6f, LightEnergy = 1.4f, ShadowEnabled = false };
        light.Position = new Vector3(0, (float)size * 1.2f, 0);
        AddChild(light);
        Visible = false;
    }

    bool IOrb.Visible { get => Visible; set => Visible = value; }

    public void Place(double x, double y, double z, double spin, double scale)
    {
        Position = new Vector3((float)x, (float)y, (float)z);
        lump.Rotation = new Vector3(0, (float)spin, 0);
        lump.Scale = Vector3.One * (float)scale;
    }

    public double Light
    {
        set
        {
            float heat = Mathf.Clamp((float)value, 0, 1);
            mat.SetShaderParameter("heat", heat);
            light.LightEnergy = 1.2f + 3.5f * heat;
        }
    }

    void IOrb.Dispose() => QueueFree();
}

/// <summary>The Warden's heart (E7c, look bible 10): a wet stone the size of a fist, cut in a few broad chipped faces
/// (tools/assets/env_heart.py), cold light in its cracks pulsing like a slow heartbeat (shaders/heart.gdshader), water
/// running down it and dripping off its underside while it is wet, and a short cold light that pulses with the veins and
/// lights the hands holding it and the water about it. No halo: the cracks' cores alone cross the glow threshold.
/// size is its longest half-length (m). --heart-old draws the old faceted glass ball and its ring halo (the before
/// shots); --heart-try k=v,... sets the shader's uniforms and the light's (light_k, light_att, light_amp, light_range).</summary>
public partial class OrbView : Node3D, IOrb
{
    readonly Node3D ball;
    readonly OmniLight3D light;
    readonly StandardMaterial3D? stone;
    readonly ShaderMaterial? heart;
    readonly GpuParticles3D? drips;
    readonly MeshInstance3D? bead;
    Vector3 bottom;
    readonly float size;
    double lightIn, t, shownT;
    bool wasShown;

    // The heartbeat's period (s); the light's swing about its mean (+-; the veins' is the shader's beat_amp).
    const double Period = 1.55;
    float lightAmp = 0.12f, lightK = 0.12f, lightAtt = 0.8f;
    const float FistK = 0.002f;

    static Mesh? heartMesh;
    static Aabb heartBox;
    static Vector3 heartLow;
    static Shader? heartShader;

    public OrbView(string color, double size)
    {
        this.size = (float)size;
        var c = new Color(color);
        if (Array.IndexOf(OS.GetCmdlineUserArgs(), "--heart-old") >= 0 || !LoadHeart())
        {
            // (--heart-old-k K: its size times K, as the before was drawn: c03's heart was 0.11 before E7c, 0.05 now: K 2.2)
            if (Array.IndexOf(OS.GetCmdlineUserArgs(), "--heart-old") >= 0) size *= SurvivorUnchained.Args.Num("heart-old-k", 1);
            stone = new StandardMaterial3D
            {
                AlbedoColor = c.Darkened(0.7f), Metallic = 0.35f, Roughness = 0.12f,
                EmissionEnabled = true, Emission = new Color(c.R * 0.3f, c.G * 0.6f, c.B * 0.95f), EmissionEnergyMultiplier = 0.5f,
                RimEnabled = true, Rim = 0.6f, RimTint = 0.8f,
            };
            ball = new MeshInstance3D { Mesh = Facets((float)size), MaterialOverride = stone, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(ball);
            AddChild(new MeshInstance3D
            {
                Mesh = new QuadMesh { Size = Vector2.One * (float)size * 4.5f },
                CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                MaterialOverride = new StandardMaterial3D
                {
                    ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                    BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                    AlbedoTexture = new GradientTexture2D
                    {
                        Gradient = new Gradient { Colors = [new Color(1, 1, 1, 0), new Color(1, 1, 1, 0), new Color(1, 1, 1, 0.55f), new Color(1, 1, 1, 0)], Offsets = [0, 0.16f, 0.24f, 1] },
                        Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
                    },
                    AlbedoColor = new Color(c, 0.35f),
                },
            });
            light = new OmniLight3D { LightColor = c, OmniRange = 14, OmniAttenuation = 1.3f };
            AddChild(light);
            Visible = false;
            return;
        }
        // The stone: the mesh scaled so its longest half-length is size, turned and pulsed by Place/Turn about its middle.
        ball = new Node3D();
        AddChild(ball);
        float half = Mathf.Max(heartBox.Size.X, Mathf.Max(heartBox.Size.Y, heartBox.Size.Z)) * 0.5f;
        float k = this.size / Mathf.Max(half, 1e-4f);
        heart = new ShaderMaterial { Shader = heartShader };
        heart.SetShaderParameter("stone_tex", GD.Load<Texture2D>("res://art/world/flora/stone_albedo.png"));
        // (the cores a little off white, the light about them a deeper blue: c03's #bfe6ff gives sRGB 175,220,255 and 60,130,255)
        heart.SetShaderParameter("core_color", new Color(c.R * 0.916f, c.G * 0.957f, c.B));
        heart.SetShaderParameter("glow_color", new Color(c.R * 0.31f, c.G * 0.565f, c.B));
        heart.SetShaderParameter("unit", k);
        var mi = new MeshInstance3D
        {
            Mesh = heartMesh, MaterialOverride = heart, Scale = Vector3.One * k, Position = -heartBox.GetCenter() * k,
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        ball.AddChild(mi);
        // The light: short, cold, unshadowed (the frame's one shadowed light is the sky's); its range from the stone's size
        // (a fist at a close-up: 1 m and a steep falloff, so it lights the fingers near it and little else (E7c r2); the play
        // camera's larger stand-in: as far as the old one reached).
        bool fist = this.size <= 0.1f;
        float range = fist ? 1f : this.size * 32;
        if (fist) { lightK = FistK; lightAtt = 2f; }
        foreach (var (key, v) in Tries())
            switch (key)
            {
                case "light_k": lightK = v; break;
                case "light_att": lightAtt = v; break;
                case "light_amp": lightAmp = v; break;
                case "light_range": range = v; break;
                default: heart.SetShaderParameter(key, v); break;
            }
        // (a fist's light sits in its upper part: with the steep falloff, whatever it lies on would burn white at 5 cm)
        light = new OmniLight3D { LightColor = c, OmniRange = range, OmniAttenuation = lightAtt, ShadowEnabled = false, LightSpecular = 0.6f, LightVolumetricFogEnergy = 0.3f,
            Position = fist ? new Vector3(0, this.size * 0.6f, 0) : Vector3.Zero };
        AddChild(light);
        drips = Drips(this.size, c);
        AddChild(drips);
        // One clear drop at a time gathering on its lowest point and falling (E7c r3): big enough to read at 1:1 in an
        // 85 mm close-up (~2 mm across: 7 px at c03 s8), glossy, the heart's blue in it.
        bottom = (heartLow - heartBox.GetCenter()) * k;
        bead = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = this.size * 0.02f, Height = this.size * 0.04f, RadialSegments = 12, Rings = 8 },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D
            {
                AlbedoColor = new Color(0.5f, 0.6f, 0.72f, 0.9f), Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                Roughness = 0.03f, Metallic = 0, MetallicSpecular = 1f,
                EmissionEnabled = true, Emission = new Color(c.R * 0.55f, c.G * 0.75f, c.B), EmissionEnergyMultiplier = 2.6f,
                RimEnabled = true, Rim = 1f, RimTint = 0.15f,
            },
            Visible = false,
        };
        // (its highlight: a hot point near its top, where it catches the light)
        bead.AddChild(new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = this.size * 0.0065f, Height = this.size * 0.013f, RadialSegments = 8, Rings = 4 },
            Position = new Vector3(0, this.size * 0.011f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(0.9f, 0.96f, 1f) },
        });
        AddChild(bead);
        Visible = false;
    }

    static IEnumerable<(string, float)> Tries()
    {
        var a = OS.GetCmdlineUserArgs();
        int i = Array.IndexOf(a, "--heart-try");
        if (i < 0 || i + 1 >= a.Length) yield break;
        foreach (var kv in a[i + 1].Split(','))
            if (kv.Split('=') is [var key, var val] && float.TryParse(val, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                yield return (key.Trim(), f);
    }

    static bool LoadHeart()
    {
        if (heartMesh != null) return true;
        var scene = ResourceLoader.Exists("res://art/world/props/heart.gltf") ? GD.Load<PackedScene>("res://art/world/props/heart.gltf") : null;
        if (scene?.Instantiate() is not Node3D root) return false;
        if (root.FindChild("lod0", true, false) is MeshInstance3D m && m.Mesh != null)
        {
            heartMesh = m.Mesh;
            heartBox = m.Mesh.GetAabb();
            heartLow = heartBox.GetCenter();
            foreach (var v in m.Mesh.SurfaceGetArrays(0)[(int)Mesh.ArrayType.Vertex].AsVector3Array())
                if (v.Y < heartLow.Y) heartLow = v;
            heartShader = GD.Load<Shader>("res://shaders/heart.gdshader");
        }
        root.QueueFree();
        return heartMesh != null;
    }

    /// <summary>Water dripping off its underside: a few small drops gathering under it and falling (world space, so they
    /// fall straight as it moves), each carrying a little of its light.</summary>
    static GpuParticles3D Drips(float size, Color c)
    {
        float r = size * 0.05f;
        var pm = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Ring,
            EmissionRingAxis = Vector3.Up, EmissionRingRadius = size * 0.35f, EmissionRingInnerRadius = 0, EmissionRingHeight = size * 0.1f,
            Direction = Vector3.Down, Spread = 8, InitialVelocityMin = 0.0f, InitialVelocityMax = 0.12f,
            Gravity = new Vector3(0, -9.8f, 0), ScaleMin = 0.6f, ScaleMax = 1.2f,
        };
        var drop = new SphereMesh { Radius = r, Height = r * 2.8f, RadialSegments = 8, Rings = 5 };
        drop.Material = new StandardMaterial3D
        {
            AlbedoColor = new Color(0.7f, 0.8f, 0.88f, 0.35f), Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            Roughness = 0.04f, Metallic = 0, MetallicSpecular = 1f,
            EmissionEnabled = true, Emission = c, EmissionEnergyMultiplier = 0.15f,
            RimEnabled = true, Rim = 0.7f, RimTint = 0.3f,
        };
        return new GpuParticles3D
        {
            Amount = 8, Lifetime = 0.45, LocalCoords = false, ProcessMaterial = pm, DrawPass1 = drop,
            Position = new Vector3(0, -size * 0.72f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            VisibilityAabb = new Aabb(new Vector3(-1, -4, -1), new Vector3(2, 5, 2)),
        };
    }

    bool IOrb.Visible { get => Visible; set => Visible = value; }

    public void Place(double x, double y, double z, double spin, double scale)
    {
        Position = new Vector3((float)x, (float)y, (float)z);
        ball.Rotation = new Vector3(0, (float)spin, 0);
        ball.Scale = Vector3.One * (float)scale;
        Bead();
    }

    // The drop's cycle (s): it gathers (swelling on the stone's lowest point), then falls.
    const double BeadGather = 1.35, BeadFall = 0.35;
    static readonly bool beadLog = Array.IndexOf(OS.GetCmdlineUserArgs(), "--bead-log") >= 0;
    int beadTick = -1;

    void Bead()
    {
        if (bead == null) return;
        // (while it is wet: soaked to 40 s shown)
        bead.Visible = Visible && shownT < 40;
        if (!bead.Visible) return;
        double ph = t % (BeadGather + BeadFall);
        float r = size * 0.02f;
        var low = ball.Transform.Basis * bottom;
        if (ph < BeadGather)
        {
            float g = (float)Mathf.SmoothStep(0, 1, ph / BeadGather);
            float sc = Mathf.Lerp(0.35f, 1f, g);
            // (hanging: a little long, just under the point)
            bead.Scale = new Vector3(sc, sc * Mathf.Lerp(1f, 1.2f, g), sc);
            bead.Position = low + new Vector3(0, -r * sc * 0.9f, 0);
        }
        else
        {
            float f = (float)(ph - BeadGather);
            bead.Scale = new Vector3(0.92f, 1.2f, 0.92f);
            bead.Position = low + new Vector3(0, -r * 0.9f - 4.9f * f * f, 0);
        }
        if (beadLog && (int)(t * 4) != beadTick && GetViewport().GetCamera3D() is { } cam)
        {
            beadTick = (int)(t * 4);
            GD.Print($"bead t={t:0.00} ph={ph:0.00} px={cam.UnprojectPosition(bead.GlobalPosition)} behind={cam.IsPositionBehind(bead.GlobalPosition)} low={low}");
        }
    }

    public double Light
    {
        set
        {
            lightIn = value;
            if (heart == null)
            {
                light.LightEnergy = (float)(value / Math.PI);
                stone!.EmissionEnergyMultiplier = 0.35f + Mathf.Clamp((float)value, 0, 6) * 0.15f;
            }
            else Pulse();
        }
    }

    /// <summary>The heartbeat's shape (0..1): a soft double beat (lub, dub) on a slow swell, never a strobe.</summary>
    static double Beat(double t)
    {
        double ph = t / Period % 1.0;
        double lub = Math.Exp(-Math.Pow((ph - 0.12) / 0.11, 2)), dub = 0.65 * Math.Exp(-Math.Pow((ph - 0.38) / 0.13, 2));
        double swell = 0.5 + 0.5 * Math.Sin(2 * Math.PI * ph - 0.6);
        return Math.Clamp(0.75 * Math.Max(lub, dub) + 0.25 * swell, 0, 1);
    }

    void Pulse()
    {
        double b = Beat(t);
        // (the orb's Light: c03's glow x 6 (0.8 -> 4.8), the play's 16-18: the veins at 1 for 4.8, up to 1.6 for the play's)
        float level = (float)Math.Clamp(lightIn / 4.8, 0, 1.6);
        heart!.SetShaderParameter("beat", (float)b);
        heart.SetShaderParameter("level", level);
        heart.SetShaderParameter("flow_t", (float)t);
        float sizeK = size / 0.05f;
        light.LightEnergy = (float)(lightIn * lightK * sizeK * (1 + lightAmp * (2 * b - 1)));
        light.Visible = lightIn > 0.01;
        // Wet from the water: soaked for its first 20 s shown, drying to a damp sheen by 60 s; the drips thin out by 25 s.
        float wet = (float)Math.Clamp(1 - (shownT - 20) / 40, 0.35, 1);
        heart.SetShaderParameter("wet", wet);
        if (drips != null)
        {
            double ratio = Math.Clamp(1 - (shownT - 12) / 13, 0, 1);
            drips.Emitting = ratio > 0.02;
            drips.AmountRatio = (float)ratio;
        }
    }

    public override void _Process(double delta)
    {
        if (heart == null) return;
        if (!Visible) { wasShown = false; return; }
        if (!wasShown) { wasShown = true; shownT = 0; }
        t += delta;
        shownT += delta;
        Pulse();
        Bead();
    }

    /// <summary>The old look (--heart-old): a squashed, uneven sphere of a few flat faces.</summary>
    static Mesh Facets(float size)
    {
        var src = new SphereMesh { Radius = size, Height = size * 1.7f, RadialSegments = 7, Rings = 4 };
        var st = new SurfaceTool();
        st.CreateFrom(src, 0);
        st.Deindex();
        var arrays = st.Commit().SurfaceGetArrays(0);
        var verts = (Vector3[])arrays[(int)Mesh.ArrayType.Vertex];
        for (int i = 0; i < verts.Length; i++)
        {
            var v = verts[i];
            float n = Mathf.Sin(v.X * 53.1f + v.Y * 17.3f) * Mathf.Cos(v.Z * 41.7f - v.Y * 9.1f);
            verts[i] = v * (1 + n * 0.14f);
        }
        var flat = new SurfaceTool();
        flat.Begin(Mesh.PrimitiveType.Triangles);
        foreach (var v in verts) flat.AddVertex(v);
        flat.GenerateNormals();
        return flat.Commit();
    }

    /// <summary>Turning slowly where it hangs (a cinematic's frame).</summary>
    public void Turn(double dt) => ball.RotateY((float)(dt * 1.4));
    void IOrb.Dispose() => QueueFree();
}

/// <summary>A kit piece that moves (Snib's barrel): placed and turned where the fight puts it, rolled
/// about its own long axis as it goes (spin), with no light of its own.</summary>
public partial class PieceView : Node3D, IOrb
{
    readonly Node3D piece;

    public PieceView(Node3D piece)
    {
        this.piece = piece;
        AddChild(piece);
        Visible = false;
    }

    bool IOrb.Visible { get => Visible; set => Visible = value; }

    /// <summary>`spin`: how far round it has rolled; it lies on its side, rolling the way it faces.</summary>
    public void Place(double x, double y, double z, double spin, double scale)
    {
        Position = new Vector3((float)x, (float)y, (float)z);
        piece.Rotation = new Vector3((float)spin, 0, 0);
        Scale = Vector3.One * (float)scale;
    }

    public double Light { set { } }
    public void Face(double yaw) => Rotation = new Vector3(0, (float)yaw, 0);
    void IOrb.Dispose() => QueueFree();
}

/// <summary>WARDEN_HOODCHECK=1 (Warden 6 hood): his hood and capelet (armor/hood.glb, the "warden_hood_wool" surface)
/// measured in whatever he plays, every 0.2 s on the CPU from the skeleton's pose: each edge's stretch against its rest,
/// and his body and head points that sit inside the cloth at rest but come out through it (more than 2 mm past the
/// outer surface at the nearest cloth point). Printed as "hoodcheck" lines, and a summary when he leaves.</summary>
public partial class HoodCheck : Node
{
    sealed class Skinned
    {
        public Vector3[] P = Array.Empty<Vector3>(), N = Array.Empty<Vector3>();
        public int[] B = Array.Empty<int>(), Idx = Array.Empty<int>();
        public float[] W = Array.Empty<float>();
        public int K;
        public int[] BindBone = Array.Empty<int>();
        public Transform3D[] Bind = Array.Empty<Transform3D>();
        public string[] BoneName = Array.Empty<string>();
    }

    Skeleton3D skel = null!;
    Skinned? hood;
    readonly List<Skinned> body = new();
    readonly List<(int Mesh, int V)> inside = new();
    int[] edges = Array.Empty<int>();
    float[] restLen = Array.Empty<float>();
    double t, tick;
    int samples, worstCount;
    float worstStretch, worstDepth;
    string worstWhere = "";
    readonly List<float> stretchAll = new();

    static Skinned? Read(MeshInstance3D mi, int s, Skeleton3D skel)
    {
        var a = mi.Mesh.SurfaceGetArrays(s);
        if (a[(int)Mesh.ArrayType.Bones].VariantType == Godot.Variant.Type.Nil || mi.Skin == null) return null;
        var o = new Skinned { P = a[(int)Mesh.ArrayType.Vertex].AsVector3Array(), N = a[(int)Mesh.ArrayType.Normal].AsVector3Array() };
        var bones = a[(int)Mesh.ArrayType.Bones];
        o.B = bones.VariantType == Godot.Variant.Type.PackedInt32Array ? bones.AsInt32Array() : Array.ConvertAll(bones.AsFloat32Array(), f => (int)f);
        o.W = a[(int)Mesh.ArrayType.Weights].AsFloat32Array();
        o.Idx = a[(int)Mesh.ArrayType.Index].AsInt32Array();
        o.K = o.B.Length / Math.Max(o.P.Length, 1);
        int n = mi.Skin.GetBindCount();
        o.BindBone = new int[n];
        o.Bind = new Transform3D[n];
        o.BoneName = new string[n];
        for (int i = 0; i < n; i++)
        {
            string bn = mi.Skin.GetBindName(i);
            o.BindBone[i] = bn != "" ? skel.FindBone(bn) : mi.Skin.GetBindBone(i);
            o.Bind[i] = mi.Skin.GetBindPose(i);
            o.BoneName[i] = o.BindBone[i] >= 0 ? skel.GetBoneName(o.BindBone[i]) : "?";
        }
        return o;
    }

    Transform3D[] Mats(Skinned m, bool rest)
    {
        var r = new Transform3D[m.Bind.Length];
        for (int i = 0; i < r.Length; i++)
            r[i] = (m.BindBone[i] < 0 ? Transform3D.Identity : rest ? skel.GetBoneGlobalRest(m.BindBone[i]) : skel.GetBoneGlobalPose(m.BindBone[i])) * m.Bind[i];
        return r;
    }

    static (Vector3 P, Vector3 N) At(Skinned m, Transform3D[] M, int v)
    {
        Vector3 p = Vector3.Zero, n = Vector3.Zero;
        for (int k = 0; k < m.K; k++)
        {
            float w = m.W[v * m.K + k];
            if (w <= 0) continue;
            var x = M[m.B[v * m.K + k]];
            p += w * (x * m.P[v]);
            n += w * (x.Basis * m.N[v]);
        }
        return (p, n.Normalized());
    }

    public override void _Ready()
    {
        skel = GetParent<Skeleton3D>();
        foreach (var c in skel.GetChildren())
        {
            if (c is not MeshInstance3D mi || mi.Mesh == null || mi.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                string mat = mi.Mesh.SurfaceGetMaterial(s)?.ResourceName ?? "";
                if (mat == "warden_hood_wool" && mi.VisibilityRangeBegin <= 0) hood ??= Read(mi, s, skel);
                else if (mat is "generated" or "warden_face" or "warden_patch" && mi.Name.ToString() != "lod" && Read(mi, s, skel) is { } b) body.Add(b);
            }
        }
        if (hood == null) { GD.Print("hoodcheck: no hood surface"); QueueFree(); return; }
        var seen = new HashSet<long>();
        var el = new List<int>();
        for (int i = 0; i + 2 < hood.Idx.Length; i += 3)
            for (int e = 0; e < 3; e++)
            {
                int a = hood.Idx[i + e], b = hood.Idx[i + (e + 1) % 3];
                long key = (long)Math.Min(a, b) << 32 | (uint)Math.Max(a, b);
                if (seen.Add(key)) { el.Add(a); el.Add(b); }
            }
        edges = el.ToArray();
        var hm = Mats(hood, true);
        var hp = new Vector3[hood.P.Length];
        var hn = new Vector3[hood.P.Length];
        for (int v = 0; v < hp.Length; v++) (hp[v], hn[v]) = At(hood, hm, v);
        restLen = new float[edges.Length / 2];
        for (int i = 0; i < restLen.Length; i++) restLen[i] = hp[edges[2 * i]].DistanceTo(hp[edges[2 * i + 1]]);
        var grid = Grid(hp);
        for (int m = 0; m < body.Count; m++)
        {
            var bm = Mats(body[m], true);
            for (int v = 0; v < body[m].P.Length; v += 2)
            {
                var p = At(body[m], bm, v).P;
                int h = Nearest(grid, hp, p, 0.06f);
                if (h >= 0 && (p - hp[h]).Dot(hn[h]) < -0.002f) inside.Add((m, v));
            }
        }
        GD.Print($"hoodcheck: hood {hp.Length} verts, {restLen.Length} edges; {inside.Count} body points under the cloth at rest");
    }

    static Dictionary<(int, int, int), List<int>> Grid(Vector3[] p)
    {
        var g = new Dictionary<(int, int, int), List<int>>();
        for (int i = 0; i < p.Length; i++)
        {
            var k = ((int)Mathf.Floor(p[i].X / 0.03f), (int)Mathf.Floor(p[i].Y / 0.03f), (int)Mathf.Floor(p[i].Z / 0.03f));
            if (!g.TryGetValue(k, out var l)) g[k] = l = new List<int>();
            l.Add(i);
        }
        return g;
    }

    static int Nearest(Dictionary<(int, int, int), List<int>> g, Vector3[] hp, Vector3 p, float reach)
    {
        int best = -1;
        float bd = reach * reach;
        int cx = (int)Mathf.Floor(p.X / 0.03f), cy = (int)Mathf.Floor(p.Y / 0.03f), cz = (int)Mathf.Floor(p.Z / 0.03f);
        for (int x = -2; x <= 2; x++)
            for (int y = -2; y <= 2; y++)
                for (int z = -2; z <= 2; z++)
                    if (g.TryGetValue((cx + x, cy + y, cz + z), out var l))
                        foreach (int i in l)
                        {
                            float d = hp[i].DistanceSquaredTo(p);
                            if (d < bd) { bd = d; best = i; }
                        }
        return best;
    }

    public override void _Process(double delta)
    {
        t += delta;
        if ((tick -= delta) > 0 || hood == null) return;
        tick = 0.2;
        samples++;
        var hm = Mats(hood, false);
        var hp = new Vector3[hood.P.Length];
        var hn = new Vector3[hood.P.Length];
        for (int v = 0; v < hp.Length; v++) (hp[v], hn[v]) = At(hood, hm, v);
        float smax = 0;
        for (int i = 0; i < restLen.Length; i++)
        {
            float r = hp[edges[2 * i]].DistanceTo(hp[edges[2 * i + 1]]) / Math.Max(restLen[i], 1e-5f);
            smax = Math.Max(smax, r);
            if ((i & 7) == 0) stretchAll.Add(r);
        }
        var grid = Grid(hp);
        var bms = new Transform3D[body.Count][];
        for (int m = 0; m < body.Count; m++) bms[m] = Mats(body[m], false);
        int count = 0;
        float depth = 0;
        var where = new Dictionary<string, int>();
        foreach (var (m, v) in inside)
        {
            var b = body[m];
            var p = At(b, bms[m], v).P;
            int h = Nearest(grid, hp, p, 0.06f);
            if (h < 0) continue;
            float d = (p - hp[h]).Dot(hn[h]);
            if (d <= 0.002f) continue;
            count++;
            depth = Math.Max(depth, d);
            int kb = 0;
            for (int k = 1; k < b.K; k++) if (b.W[v * b.K + k] > b.W[v * b.K + kb]) kb = k;
            string bn = b.BoneName[b.B[v * b.K + kb]];
            where[bn] = where.GetValueOrDefault(bn) + 1;
        }
        worstStretch = Math.Max(worstStretch, smax);
        var top = new List<KeyValuePair<string, int>>(where);
        top.Sort((x, y) => y.Value.CompareTo(x.Value));
        string w = string.Join(",", top.GetRange(0, Math.Min(3, top.Count)));
        if (count > worstCount) { worstCount = count; worstWhere = w; }
        worstDepth = Math.Max(worstDepth, depth);
        GD.Print($"hoodcheck t={t:F1} stretch_max={smax:F3} poke={count} depth_mm={depth * 1000:F1} {w}");
    }

    public override void _ExitTree()
    {
        if (hood == null) return;
        stretchAll.Sort();
        float p99 = stretchAll.Count > 0 ? stretchAll[(int)(stretchAll.Count * 0.99)] : 0;
        float p01 = stretchAll.Count > 0 ? stretchAll[(int)(stretchAll.Count * 0.01)] : 0;
        GD.Print($"hoodcheck SUMMARY samples={samples} stretch_max={worstStretch:F3} stretch_p99={p99:F3} squash_p01={p01:F3} poke_max={worstCount} ({worstWhere}) depth_max_mm={worstDepth * 1000:F1} under_at_rest={inside.Count}");
    }
}
