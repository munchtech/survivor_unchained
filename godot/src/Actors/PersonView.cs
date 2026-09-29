using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// Someone standing or walking in the world, as a zone's runtime moves them
/// (Play.INpcView): a Quaternius person with their clothes and what they
/// hold, a looping pose, a gesture played once and back to the loop (or
/// held on its last frame), and walking blended from standing to a walk to
/// a jog by speed.
/// </summary>
public partial class PersonView : Node3D, INpcView
{
    readonly People.Person person;
    string loop = "", loopClip = "";
    double loopSpeed = 1;
    double actLeft;
    bool walking, holding;
    readonly System.Collections.Generic.Dictionary<string, Node3D> held = new();
    /// <summary>What walking and running look like for this one (a shambling dead thing walks otherwise).</summary>
    public string WalkClip = "Walk_Loop", RunClip = "Jog_Fwd_Loop";

    /// <summary>A person; the game's figures stand at 0.8 of their authored
    /// size, a touch over life size (the web game's CHARACTER_SCALE × HUMAN_SCALE).</summary>
    public PersonView(PersonSpec spec, Held? arms, double scale)
    {
        person = People.Build(spec);
        person.Root.Scale = Vector3.One * (float)(scale / 0.8 * 1.04);
        AddChild(person.Root);
        if (arms?.Right is string r && Arms.All.ContainsKey(r)) held["handslot.r"] = Arms.Hold(person, r, "hand_r");
        if (arms?.Left is string l && Arms.All.ContainsKey(l)) held["handslot.l"] = Arms.Hold(person, l, "hand_l");
        if (arms?.Forearm is string f && Arms.All.ContainsKey(f)) held["forearm.l"] = Arms.Hold(person, f, "lowerarm_l");
    }

    public People.Person Person => person;

    public void Place(double x, double y, double z, double heading, bool visible)
    {
        Visible = visible;
        Position = new Vector3((float)x, (float)y, (float)z);
        Rotation = new Vector3(0, (float)heading, 0);
    }

    public void Loop(string clip, double blend = 0.3, double speed = 1)
    {
        loop = clip;
        loopSpeed = speed;
        // A held pose gives way to the loop.
        if (holding) { holding = false; actLeft = 0; person.Anim.Play(); }
        if (actLeft <= 0) PlayLoop(blend);
    }

    void PlayLoop(double blend)
    {
        var name = People.Resolve(walking ? loopClip : loop);
        person.Anim.Play(name, blend, (float)loopSpeed);
    }

    public void Act(string clip, double speed = 1) => Act(clip, speed, false);

    /// <summary>A gesture once; held on its last frame (a fall, getting up)
    /// until the next loop or gesture, or back to the loop.</summary>
    public void Act(string clip, double speed, bool hold)
    {
        var name = People.Resolve(clip);
        var anim = People.Clips().GetAnimation(name);
        person.Anim.Play(name, 0.15, (float)speed);
        holding = hold;
        actLeft = hold ? double.MaxValue : anim.Length / Mathf.Max(0.05, speed) - 0.2;
    }

    /// <summary>A clip played out and held at its end at once (a body lying where it fell).</summary>
    public void Pose(string clip)
    {
        var name = People.Resolve(clip);
        var len = People.Clips().GetAnimation(name).Length;
        person.Anim.Play(name, 0);
        person.Anim.Seek(len - 0.02, true);
        person.Anim.Pause();
        holding = true;
        actLeft = double.MaxValue;
    }

    public void Locomotion(double speed)
    {
        if (holding) return;
        // Standing, walking, jogging: the stride matched to the ground.
        string want = speed < 0.3 ? "" : speed < 2.6 ? WalkClip : RunClip;
        bool was = walking;
        walking = want != "";
        if (walking)
        {
            loopSpeed = want == WalkClip ? Mathf.Clamp(speed / 1.5, 0.6, 1.5) : Mathf.Clamp(speed / 3.6, 0.7, 1.5);
            if (want != loopClip || !was) { loopClip = want; if (actLeft <= 0) PlayLoop(0.25); }
            else if (actLeft <= 0) person.Anim.SpeedScale = (float)loopSpeed;
        }
        else if (was)
        {
            loopSpeed = 1;
            if (actLeft <= 0) PlayLoop(0.3);
        }
        if (loop == "") loop = "Idle";
    }

    public void Hold(string slot, string? pack, string? piece)
    {
        if (held.Remove(slot, out var old)) old.QueueFree();
        if (piece == null) return;
        var bone = slot switch { "handslot.l" => "hand_l", "forearm.l" => "lowerarm_l", _ => "hand_r" };
        if (Arms.All.ContainsKey(piece)) { held[slot] = Arms.Hold(person, piece, bone); return; }
        // The kits' small things (a torch, a bucket) as simple stand-ins
        // until the KayKit packs come over.
        if (Carried(piece) is Node3D thing)
        {
            var at = new BoneAttachment3D { BoneName = bone };
            person.Skeleton.AddChild(at);
            at.AddChild(thing);
            held[slot] = at;
        }
    }

    static Node3D? Carried(string piece)
    {
        var root = new Node3D();
        var wood = new StandardMaterial3D { AlbedoColor = new Color("#4a3424"), Roughness = 0.9f };
        switch (piece)
        {
            case "torch_lit":
            {
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.03f, BottomRadius = 0.025f, Height = 0.55f, Material = wood }, Position = new Vector3(0, 0.12f, 0) });
                var flame = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(3f, 1.4f, 0.35f) };
                root.AddChild(new MeshInstance3D { Mesh = new SphereMesh { Radius = 0.06f, Height = 0.18f, Material = flame }, Position = new Vector3(0, 0.44f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
                return root;
            }
            case "bucket_water":
            {
                var tin = new StandardMaterial3D { AlbedoColor = new Color("#6a5a48"), Roughness = 0.7f };
                root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.13f, BottomRadius = 0.1f, Height = 0.22f, Material = tin }, Position = new Vector3(0, -0.2f, 0) });
                return root;
            }
        }
        root.Free();
        return null;
    }

    public override void _Process(double delta)
    {
        if (actLeft > 0 && !holding)
        {
            actLeft -= delta;
            if (actLeft <= 0) PlayLoop(0.25);
        }
    }

    public void Dispose() => QueueFree();
}
