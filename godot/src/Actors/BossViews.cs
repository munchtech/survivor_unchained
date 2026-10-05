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
    readonly Node3D lamp, flame;
    readonly List<StandardMaterial3D> eyes = new(), skin = new();
    string pose = "";
    double heading, time, flash;
    public double Glow { get; set; } = 1;
    /// <summary>Whether his lamp burns (it goes out in the river in C03).</summary>
    public bool LampLit { get; set; } = true;
    /// <summary>The body, for a cinematic that moves and poses him itself.</summary>
    public PersonView Body => view;
    const float Size = 2.6f;

    public WardenView()
    {
        Name = "FordWarden";
        view = new PersonView(new PersonSpec
        {
            Sex = Sex.Male, Outfit = Lore.OutfitFor(Sex.Male, "ranger", true, true), Beard = true, HairColor = "#6a6660", Skin = "#8e9680",
            Dye = new Dye { Cloth = "#3a3e44" },
        }, new Held { Right = "zweihander" }, 0.8 * Size)
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
        // The lantern hangs from the left fist.
        var at = new BoneAttachment3D { BoneName = "hand_l" };
        view.Person.Skeleton.AddChild(at);
        lamp = new Node3D { Position = new Vector3(0, -0.1f, 0) };
        at.AddChild(lamp);
        // A lamp-iron, new black iron in the old fist: an open cage, so the flame shows.
        var iron = new StandardMaterial3D { AlbedoColor = new Color("#1e1c1a"), Metallic = 0.7f, Roughness = 0.38f };
        void Iron(Mesh m, Vector3 at) { m.SurfaceSetMaterial(0, iron); lamp.AddChild(new MeshInstance3D { Mesh = m, Position = at }); }
        Iron(new BoxMesh { Size = new Vector3(0.13f, 0.018f, 0.13f) }, new Vector3(0, -0.06f, 0));
        Iron(new BoxMesh { Size = new Vector3(0.13f, 0.02f, 0.13f) }, new Vector3(0, -0.22f, 0));
        Iron(new CylinderMesh { TopRadius = 0.02f, BottomRadius = 0.06f, Height = 0.045f, RadialSegments = 4 }, new Vector3(0, -0.03f, 0));
        foreach (var (x, z) in new[] { (-1, -1), (-1, 1), (1, -1), (1, 1) })
            Iron(new BoxMesh { Size = new Vector3(0.012f, 0.16f, 0.012f) }, new Vector3(x * 0.058f, -0.14f, z * 0.058f));
        Iron(new TorusMesh { InnerRadius = 0.022f, OuterRadius = 0.032f, Rings = 12, RingSegments = 6 }, new Vector3(0, 0.0f, 0));
        flame = new Node3D { Position = new Vector3(0, -0.15f, 0) };
        lamp.AddChild(flame);
        flame.AddChild(new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = 0.026f, Height = 0.075f, Material = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(1.4f, 2.4f, 3.2f) } },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });
        flame.AddChild(new MeshInstance3D
        {
            Mesh = new QuadMesh { Size = Vector2.One * 0.3f },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                AlbedoTexture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.15f), new Color(1, 1, 1, 0)], Offsets = [0, 0.25f, 1] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
                },
                AlbedoColor = new Color(0.55f, 0.8f, 1f, 0.6f),
            },
        });
        light = new OmniLight3D { LightColor = new Color("#8ac8ff"), OmniRange = 16, OmniAttenuation = 1.3f, LightEnergy = 0, ShadowEnabled = true };
        AddChild(light);
    }

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
        Light(g, (float)y);
        lamp.Visible = pose != "dead" || g > 0.01;
        flame.Visible = LampLit && g > 0.01;
    }

    /// <summary>A cinematic's frame: the eyes and the lamp at the glow it sets,
    /// wherever the cinematic has put the body.</summary>
    public void Shine(double dt)
    {
        time += dt;
        Visible = true;
        Light(Glow, view.GlobalPosition.Y);
        lamp.Visible = true;
        flame.Visible = LampLit && Glow > 0.01;
    }

    void Light(double g, float ground)
    {
        foreach (var m in eyes) m.EmissionEnergyMultiplier = (float)(g <= 0.001 ? 0 : 1.2 + g * 2.4 + Math.Sin(time * 5) * g * 0.5);
        // The light is the lamp in his fist, hung a little out from the body.
        double i = LampLit ? g * (5 + Math.Sin(time * 3.1) * 0.8 + (pose == "channel" ? 4 + Math.Sin(time * 14) * 2 : 0)) : 0;
        light.LightEnergy = (float)(i / Math.PI);
        var at = lamp.GlobalPosition;
        light.GlobalPosition = new Vector3(at.X, Mathf.Max(at.Y, ground + 1.2f) + 0.8f, at.Z);
    }

    // Explicit, so they do not shadow Godot's own Hide() and Dispose().
    void IBossView.Hide() => Visible = false;
    void IBossView.Dispose() => QueueFree();
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

public partial class OrbView : Node3D, IOrb
{
    readonly MeshInstance3D ball;
    readonly OmniLight3D light;

    public OrbView(string color, double size)
    {
        var c = new Color(color).SrgbToLinear();
        ball = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = (float)size, Height = (float)size * 2, RadialSegments = 16, Rings = 8 },
            MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(c.R * 3, c.G * 3, c.B * 3) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        AddChild(ball);
        // A soft halo about it, as a bright thing has in mist.
        AddChild(new MeshInstance3D
        {
            Mesh = new QuadMesh { Size = Vector2.One * (float)size * 7 },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                AlbedoTexture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.2f), new Color(1, 1, 1, 0)], Offsets = [0, 0.2f, 1] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
                },
                AlbedoColor = new Color(new Color(color), 0.5f),
            },
        });
        light = new OmniLight3D { LightColor = new Color(color), OmniRange = 14, OmniAttenuation = 1.3f };
        AddChild(light);
        Visible = false;
    }

    bool IOrb.Visible { get => Visible; set => Visible = value; }

    public void Place(double x, double y, double z, double spin, double scale)
    {
        Position = new Vector3((float)x, (float)y, (float)z);
        ball.Rotation = new Vector3(0, (float)spin, 0);
        ball.Scale = Vector3.One * (float)scale;
    }

    public double Light { set => light.LightEnergy = (float)(value / Math.PI); }

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
    void IOrb.Dispose() => QueueFree();
}
