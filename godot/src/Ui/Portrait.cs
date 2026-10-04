using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Someone drawn live in a frame of the interface (the web game's
/// ui/portrait.ts): the figure in a world of its own, lit like a museum
/// piece (a warm key from the upper left, a cool rim from behind, a soft
/// fill), breathing through its idle. Whole-body for the pack and the
/// self, head and shoulders for a conversation.
/// </summary>
public partial class Portrait : SubViewportContainer
{
    /// <summary>Full: head to foot. Half: head to hip, a person across a table. Bust: head and shoulders.</summary>
    public enum Framing { Full, Half, Bust }

    readonly SubViewport vp;
    readonly Node3D stage;

    public Portrait(Vector2I size, Framing framing = Framing.Full)
    {
        Stretch = true;
        CustomMinimumSize = size;
        MouseFilter = MouseFilterEnum.Ignore;
        vp = new SubViewport { Size = size, TransparentBg = true, OwnWorld3D = true, Msaa3D = Viewport.Msaa.Msaa4X, RenderTargetUpdateMode = SubViewport.UpdateMode.WhenVisible };
        AddChild(vp);
        stage = new Node3D();
        vp.AddChild(stage);
        var env = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.ClearColor, BackgroundColor = new Color(0, 0, 0, 0),
            AmbientLightSource = Godot.Environment.AmbientSource.Color, AmbientLightColor = new Color("#3a3440"), AmbientLightEnergy = 0.6f,
            TonemapMode = Godot.Environment.ToneMapper.Agx,
        };
        vp.AddChild(new WorldEnvironment { Environment = env });
        stage.AddChild(new DirectionalLight3D { LightColor = new Color("#ffd8a8"), LightEnergy = 2.2f, Rotation = new Vector3(-0.6f, -0.7f, 0) });
        stage.AddChild(new DirectionalLight3D { LightColor = new Color("#8ab0ff"), LightEnergy = 1.6f, Rotation = new Vector3(-0.2f, 2.6f, 0) });
        stage.AddChild(new DirectionalLight3D { LightColor = new Color("#c0a890"), LightEnergy = 0.5f, Rotation = new Vector3(-0.1f, 0.4f, 0) });
        var cam = new Camera3D { Fov = framing switch { Framing.Bust => 22, Framing.Half => 27, _ => 30 } };
        stage.AddChild(cam);
        var (from, to) = framing switch
        {
            Framing.Bust => (new Vector3(0, 1.62f, 1.45f), new Vector3(0, 1.55f, 0)),
            Framing.Half => (new Vector3(0, 1.4f, 2.7f), new Vector3(0, 1.28f, 0)),
            _ => (new Vector3(0, 1.05f, 4.1f), new Vector3(0, 0.95f, 0)),
        };
        cam.Transform = new Transform3D(Basis.LookingAt(to - from, Vector3.Up), from);
    }

    /// <summary>The survivor as they stand, with what they carry.</summary>
    public Portrait Of(Loadout lo)
    {
        var v = new PersonView(lo.Person, new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        Place(v, lo.Arms.Idle);
        return this;
    }

    /// <summary>Someone of the world (a person as a spec).</summary>
    public Portrait Of(PersonSpec spec, Held? arms, double scale = 1)
    {
        Place(new PersonView(spec, arms, 0.8 * scale), "Idle_Loop");
        return this;
    }

    void Place(PersonView v, string idle)
    {
        foreach (var c in stage.GetChildren()) if (c is PersonView old) old.QueueFree();
        stage.AddChild(v);
        v.Rotation = new Vector3(0, 0.35f, 0);
        v.Loop(idle, 0);
    }
}
