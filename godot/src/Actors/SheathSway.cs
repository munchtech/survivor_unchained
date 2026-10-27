using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// A sheathed piece hung from her belt (Body 16; Play/SheathHang): each skeleton update (after the clip, as a
/// SkeletonModifier3D that moves no bone) it re-turns its mount (the child of the bone's BoneAttachment3D, Arms.
/// HoldSheathed) about the belt pivot, so the piece trails her hips' roll and turn as a hung weight instead of riding
/// the bone rigidly. The pivot stays where the rigid mount put it. It frees itself when its mount goes (Sheathe swaps).
/// A piece whose hilt a clip's hand holds (hilt: the warden's hip sword; Body 17) rides rigidly in those clips
/// (SheathHang.HiltHeld, read from the playing clip of the AnimationPlayer nearest above the skeleton), the hang eased
/// out and back in over SheathHang.Blend s. `--sheath-rigid`: the old rigid ride (for before/after frames).
/// </summary>
public partial class SheathSway : SkeletonModifier3D
{
    static readonly bool Rigid = Args.Has("sheath-rigid");

    Node3D? mount;
    Transform3D rigid;   // the mount's rigid transform in the bone's space (Arms.Sheathed)
    Vector3 pivot;       // the belt pivot in the bone's space
    Vector3 pivotInMount;
    string bone = "";
    int idx = -2;
    Quaternion restQ;
    readonly SheathHang hang = new();
    bool hilt;           // rigid in the clips whose hand holds its hilt
    AnimationPlayer? anim;
    int seek;
    StringName? clip;
    bool held;

    public static SheathSway Attach(Skeleton3D skeleton, Node3D mount, string bone, Vector3 pivot, bool hilt = false)
    {
        var s = new SheathSway { Name = "SheathSway", mount = mount, rigid = mount.Transform, pivot = pivot, bone = bone, hilt = hilt };
        s.pivotInMount = mount.Transform.AffineInverse() * pivot;
        skeleton.AddChild(s);
        return s;
    }

    /// <summary>Whether the playing clip holds the hilt (the AnimationPlayer found once, nearest above the skeleton).</summary>
    bool HiltHeldNow()
    {
        if (!hilt) return false;
        if (anim == null || !IsInstanceValid(anim))
        {
            anim = null;
            if (seek-- > 0) return held;
            seek = 30;
            for (Node? n = GetSkeleton(); n != null && anim == null; n = n.GetParent())
                foreach (var c in n.GetChildren())
                    if (c is AnimationPlayer ap) { anim = ap; break; }
            if (anim == null) return held = false;
        }
        var now = anim.CurrentAnimation;
        if (now != clip) { clip = now; held = SheathHang.HoldsHilt(now.ToString()); }
        return held;
    }

    static N.Quaternion Q(Quaternion q) => new(q.X, q.Y, q.Z, q.W);

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (mount == null || !IsInstanceValid(mount) || mount.IsQueuedForDeletion()) { QueueFree(); return; }
        if (Rigid || GetSkeleton() is not Skeleton3D sk) return;
        if (idx == -2)
        {
            idx = sk.FindBone(bone);
            if (idx >= 0) restQ = sk.GetBoneGlobalRest(idx).Basis.Orthonormalized().GetRotationQuaternion();
        }
        if (idx < 0) return;
        // The bone's turn in skeleton space and from its rest there (D = pose * rest^-1).
        var poseQ = sk.GetBoneGlobalPose(idx).Basis.Orthonormalized().GetRotationQuaternion();
        var d = Q((poseQ * restQ.Inverse()).Normalized());
        var h = hang.Step(d, (float)delta, HiltHeldNow());
        var hung = new Quaternion(h.X, h.Y, h.Z, h.W).Normalized();
        // The piece's turn in skeleton space: hung * rest * rigid; back in the bone's space under the pose.
        var basis = new Basis((poseQ.Inverse() * hung * restQ).Normalized()) * rigid.Basis;
        mount.Transform = new Transform3D(basis, pivot - basis * pivotInMount);
    }
}
