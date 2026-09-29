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
    readonly Node3D lamp;
    readonly List<StandardMaterial3D> eyes = new(), skin = new();
    string pose = "";
    double heading, time, flash;
    public double Glow { get; set; } = 1;
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
        var iron = new StandardMaterial3D { AlbedoColor = new Color("#2a2622"), Metallic = 0.6f, Roughness = 0.5f };
        lamp.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.12f, 0.16f, 0.12f), Material = iron }, Position = new Vector3(0, -0.14f, 0) });
        lamp.AddChild(new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = 0.045f, Height = 0.1f, Material = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(1.4f, 2.4f, 3.2f) } },
            Position = new Vector3(0, -0.14f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
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
        foreach (var m in eyes) m.EmissionEnergyMultiplier = (float)(1.2 + g * 2.4 + Math.Sin(time * 5) * g * 0.5);
        // The light is the lamp in his fist, hung a little out from the body.
        double i = g * (5 + Math.Sin(time * 3.1) * 0.8 + (pose == "channel" ? 4 + Math.Sin(time * 14) * 2 : 0));
        light.LightEnergy = (float)(i / Math.PI);
        var at = lamp.GlobalPosition;
        light.GlobalPosition = new Vector3(at.X, Mathf.Max(at.Y, (float)y + 1.2f) + 0.8f, at.Z);
        lamp.Visible = pose != "dead" || g > 0.01;
    }

    public void Hide() => Visible = false;
    public void Dispose() => QueueFree();
}

/// <summary>A bright thing with a light of its own (the Warden's heart).</summary>
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
    public void Dispose() => QueueFree();
}
