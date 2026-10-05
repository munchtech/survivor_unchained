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
    readonly Camera3D cam;

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
        cam = new Camera3D { Fov = framing switch { Framing.Bust => 22, Framing.Half => 27, _ => 30 } };
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

    /// <summary>One of the Verge's modelled creatures (Beasts.cs), in its idle and wearing what it
    /// wears, framed on its head: someone who is not one of the town's people (Snib at his bench).</summary>
    public Portrait Of(Beasts.Def def)
    {
        foreach (var c in stage.GetChildren()) if (c is PersonView or BeastPose) c.QueueFree();
        var pose = new BeastPose(def) { Rotation = new Vector3(0, 0.35f, 0) };
        // Framed once it stands (its head is known only then): a little above and in front of the
        // face, the hat and its lamp in the picture, as a bust frames a person.
        pose.Stood += head =>
        {
            // Level with the face under the hat's brim, far enough back for the lamp over it.
            var at = pose.Transform * head + new Vector3(0, def.Height * 0.1f, 0);
            var from = at + new Vector3(0, -def.Height * 0.16f, def.Height * 1.45f);
            cam.Fov = 28;
            cam.Transform = new Transform3D(Basis.LookingAt(at - from, Vector3.Up), from);
        };
        stage.AddChild(pose);
        return this;
    }

    void Place(PersonView v, string idle)
    {
        foreach (var c in stage.GetChildren()) if (c is PersonView or BeastPose) c.QueueFree();
        stage.AddChild(v);
        v.Rotation = new Vector3(0, 0.35f, 0);
        v.Loop(idle, 0);
        // (Already on screen, it was readied before it had a loop to be posed in.)
        v.Settle();
    }
}

/// <summary>
/// A modelled creature stood up live, as the crowd's bake stands it (Vat.BakeBeast): its glTF turned
/// to face +Z, its feet at 0, scaled to its height, wearing what it wears on its bones, and playing
/// its idle over and over. Stood says where its head is once it stands.
/// </summary>
public partial class BeastPose : Node3D
{
    readonly Beasts.Def def;
    AnimationPlayer? anim;
    string? clip;
    public event System.Action<Vector3>? Stood;

    public BeastPose(Beasts.Def def) => this.def = def;

    public override void _Ready()
    {
        var model = GD.Load<PackedScene>(def.Path)?.Instantiate<Node3D>();
        if (model == null) return;
        AddChild(model);
        var skel = Find<Skeleton3D>(model);
        anim = Find<AnimationPlayer>(model);
        if (skel == null || anim == null) return;
        var idle = def.Roles.Find(r => r.Name == "idle");
        clip = idle?.Clip ?? "Idle";
        anim.Play(clip);
        anim.Seek(idle?.From ?? 0, true);
        // Where it stands, from its bones in its idle pose (the bake's own measure).
        var toView = GlobalTransform.AffineInverse() * skel.GlobalTransform;
        Vector3 At(string bone) => toView * skel.GetBoneGlobalPose(skel.FindBone(bone)).Origin;
        Vector3 pelvis = At(def.Pelvis), head = At(def.Head);
        float low = float.MaxValue, high = float.MinValue;
        for (int b = 0; b < skel.GetBoneCount(); b++) { var y = (toView * skel.GetBoneGlobalPose(b).Origin).Y; low = Mathf.Min(low, y); high = Mathf.Max(high, y); }
        var fwd = def.Legs is var (left, right) ? (At(left) - At(right)).Cross(Vector3.Up) : head - pelvis;
        fwd = new Vector3(fwd.X, 0, fwd.Z).Normalized();
        float yaw = Mathf.Atan2(fwd.X, fwd.Z), scale = def.Height / Mathf.Max(1e-3f, high - low);
        var mid = def.Legs != null ? pelvis : (pelvis + head) / 2;
        var norm = new Transform3D(Basis.FromScale(Vector3.One * scale), Vector3.Zero)
            * new Transform3D(new Basis(Vector3.Up, -yaw), Vector3.Zero)
            * new Transform3D(Basis.Identity, new Vector3(-mid.X, -low, -mid.Z));
        model.Transform = norm * model.Transform;
        var toModel = norm * toView;
        // What it wears, on its bones, set as the bake sets it.
        foreach (var prop in def.Props ?? new())
        {
            int bone = skel.FindBone(prop.Bone);
            if (bone < 0) continue;
            var from = toModel * skel.GetBoneGlobalPose(bone);
            var tip = toModel * skel.GetBoneGlobalPose(skel.FindBone(prop.Tip)).Origin;
            var up = (tip - from.Origin).Normalized();
            var front = (new Vector3(0, 0, 1) - up * up.Z).Normalized();
            var frame = new Basis(up.Cross(front), up, front);
            var att = new BoneAttachment3D { BoneName = skel.GetBoneName(bone) };
            skel.AddChild(att);
            var worn = prop.Make();
            worn.Transform = from.AffineInverse() * new Transform3D(frame, tip + frame * prop.Offset);
            att.AddChild(worn);
        }
        // Its idle, over and over (the clip itself may not loop).
        anim.AnimationFinished += _ => { if (IsInstanceValid(anim) && clip != null) anim.Play(clip); };
        Stood?.Invoke(toModel * skel.GetBoneGlobalPose(skel.FindBone(def.Head)).Origin);
    }

    static T? Find<T>(Node n) where T : Node
    {
        foreach (var c in n.GetChildren()) { if (c is T t) return t; if (Find<T>(c) is { } d) return d; }
        return null;
    }
}
