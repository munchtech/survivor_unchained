using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Actors;

/// <summary>
/// A body that falls as a body: physical bones (capsules from each bone to
/// its child, jointed) under a PhysicalBoneSimulator3D, made the way Godot's
/// editor makes a physical skeleton, simulated from the moment of death and
/// thrown the way the blow went. The web game can only play a death clip.
/// </summary>
public sealed class Ragdoll
{
    // The bones that carry the body, and the child each capsule runs to.
    static readonly (string Bone, string To, float Radius)[] Chain =
    {
        ("pelvis", "spine_02", 0.13f), ("spine_02", "neck_01", 0.14f), ("Head", "Head", 0.11f),
        ("upperarm_l", "lowerarm_l", 0.05f), ("lowerarm_l", "hand_l", 0.045f),
        ("upperarm_r", "lowerarm_r", 0.05f), ("lowerarm_r", "hand_r", 0.045f),
        ("thigh_l", "calf_l", 0.07f), ("calf_l", "foot_l", 0.055f),
        ("thigh_r", "calf_r", 0.07f), ("calf_r", "foot_r", 0.055f),
    };

    readonly PhysicalBoneSimulator3D sim;
    readonly List<PhysicalBone3D> bones = new();
    public bool Active { get; private set; }

    public Ragdoll(Skeleton3D skel)
    {
        sim = new PhysicalBoneSimulator3D { Name = "Ragdoll" };
        skel.AddChild(sim);
        foreach (var (name, to, radius) in Chain)
        {
            int b = skel.FindBone(name), c = skel.FindBone(to);
            if (b < 0 || c < 0) continue;
            // The capsule from this bone to the next, in the bone's own space
            // (rests are relative to the parent, so the child's rest origin is
            // where the child sits from here).
            var toChild = name == to ? new Vector3(0, 0.22f, 0) : RestFrom(skel, b, c);
            float length = Mathf.Max(toChild.Length(), 0.08f);
            var pb = new PhysicalBone3D
            {
                Name = $"pb:{name}", Mass = name.StartsWith("spine") || name == "pelvis" ? 6 : 2.5f,
                JointType = name == "pelvis" ? PhysicalBone3D.JointTypeEnum.None : PhysicalBone3D.JointTypeEnum.Cone,
                LinearDamp = 0.4f, AngularDamp = 2.5f, Friction = 0.9f,
                // The ground only: a body's own limbs do not fight each other.
                CollisionLayer = 2, CollisionMask = 1,
            };
            pb.Set("bone_name", name);
            var dir = toChild.Normalized();
            var basis = Basis.LookingAt(dir, Mathf.Abs(dir.Y) > 0.9f ? Vector3.Forward : Vector3.Up);
            pb.BodyOffset = new Transform3D(basis, toChild / 2);
            pb.JointOffset = new Transform3D(Basis.Identity, new Vector3(0, 0, length / 2));
            var shape = new CollisionShape3D { Shape = new CapsuleShape3D { Radius = radius, Height = Mathf.Max(length, radius * 2 + 0.01f) } };
            shape.RotateX(Mathf.Pi / 2);
            pb.AddChild(shape);
            sim.AddChild(pb);
            bones.Add(pb);
        }
    }

    /// <summary>Where bone `c` sits in bone `b`'s space, at rest.</summary>
    static Vector3 RestFrom(Skeleton3D skel, int b, int c)
    {
        var gb = skel.GetBoneGlobalRest(b);
        var gc = skel.GetBoneGlobalRest(c);
        return gb.AffineInverse() * gc.Origin;
    }

    /// <summary>Fall, thrown along `push`.</summary>
    public void Fall(Vector3 push)
    {
        Active = true;
        sim.PhysicalBonesStartSimulation();
        foreach (var pb in bones)
            pb.ApplyCentralImpulse(push * pb.Mass * (pb.Name.ToString().Contains("spine") ? 1.3f : 0.8f));
    }

    public void Stop()
    {
        if (!Active) return;
        Active = false;
        sim.PhysicalBonesStopSimulation();
    }
}
