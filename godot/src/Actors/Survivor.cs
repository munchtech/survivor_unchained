using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The survivor: a Quaternius person in the Warden's ranger leathers, a
/// sword and a buckler, driven by an AnimationTree: running blends with
/// standing, and a swing plays on the upper body alone, so the legs keep
/// running under it (the web game layers the same way by hand).
/// </summary>
public partial class Survivor : Node3D
{
    public People.Person Person = null!;
    AnimationTree tree = null!;
    AnimationNodeAnimation swing = null!;
    public float Speed;
    int combo;

    public override void _Ready()
    {
        Person = People.Build(new People.Look("male", People.MaleRanger, Hair: "Hair_SimpleParted", Beard: true,
            HairColor: new Color("#3a2a1e"), Cloth: new Color("#8a9a70")));
        Person.Root.Scale = Vector3.One * 1.04f;
        AddChild(Person.Root);
        Arms.Hold(Person, "viking_sword", "hand_r");
        Arms.Hold(Person, "shield_round", "lowerarm_l");

        var bt = new AnimationNodeBlendTree();
        var idle = new AnimationNodeAnimation { Animation = "Sword_Idle" };
        var run = new AnimationNodeAnimation { Animation = "Jog_Fwd" };
        swing = new AnimationNodeAnimation { Animation = "Sword_Regular_A" };
        var move = new AnimationNodeBlend2();
        var attack = new AnimationNodeOneShot { FadeInTime = 0.06, FadeOutTime = 0.18, FilterEnabled = true };
        // The swing moves the spine, arms and head; the hips and legs stay
        // with the run.
        var skel = Person.Skeleton;
        for (int b = 0; b < skel.GetBoneCount(); b++)
        {
            var name = skel.GetBoneName(b);
            if (name is "root" or "pelvis" || name.StartsWith("thigh") || name.StartsWith("calf") || name.StartsWith("foot") || name.StartsWith("ball")) continue;
            attack.SetFilterPath($"Armature/Skeleton3D:{name}", true);
        }
        bt.AddNode("idle", idle, new Vector2(0, 0));
        bt.AddNode("run", run, new Vector2(0, 200));
        bt.AddNode("move", move, new Vector2(300, 100));
        bt.AddNode("swing", swing, new Vector2(300, 300));
        bt.AddNode("attack", attack, new Vector2(600, 150));
        bt.ConnectNode("move", 0, "idle");
        bt.ConnectNode("move", 1, "run");
        bt.ConnectNode("attack", 0, "move");
        bt.ConnectNode("attack", 1, "swing");
        bt.ConnectNode("output", 0, "attack");
        tree = new AnimationTree { TreeRoot = bt, RootNode = "..", Active = true };
        tree.AddAnimationLibrary("", People.Clips());
        Person.Root.AddChild(tree);
    }

    /// <summary>Blend toward running as the survivor moves.</summary>
    public void Move(float speed, float dt)
    {
        Speed = Mathf.Lerp(Speed, speed, 1 - Mathf.Exp(-10 * dt));
        tree.Set("parameters/move/blend_amount", Mathf.Clamp(Speed / 5f, 0, 1));
        tree.Set("parameters/run/timescale", Mathf.Clamp(Speed / 5f, 0.6f, 1.4f));
    }

    /// <summary>A swing, alternating the two cuts.</summary>
    public void Swing()
    {
        swing.Animation = (combo++ % 2 == 0) ? "Sword_Regular_A" : "Sword_Regular_B";
        tree.Set("parameters/attack/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }
}
