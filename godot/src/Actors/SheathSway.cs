using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// A sheathed piece hung from her belt (Body 16; Play/SheathHang): each skeleton update (after the clip, as a
/// SkeletonModifier3D that moves no bone) it re-turns its mount (the child of the bone's BoneAttachment3D, Arms.
/// HoldSheathed) about the belt pivot, so the piece trails her hips' roll and turn as a hung weight instead of riding
/// the bone rigidly. The pivot stays where the rigid mount put it. It frees itself when its mount goes (Sheathe swaps).
/// `--sheath-rigid`: the old rigid ride (for before/after frames).
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

    public static SheathSway Attach(Skeleton3D skeleton, Node3D mount, string bone, Vector3 pivot)
    {
        var s = new SheathSway { Name = "SheathSway", mount = mount, rigid = mount.Transform, pivot = pivot, bone = bone };
        s.pivotInMount = mount.Transform.AffineInverse() * pivot;
        skeleton.AddChild(s);
        return s;
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
        var h = hang.Step(d, (float)delta);
        var hung = new Quaternion(h.X, h.Y, h.Z, h.W).Normalized();
        // The piece's turn in skeleton space: hung * rest * rigid; back in the bone's space under the pose.
        var basis = new Basis((poseQ.Inverse() * hung * restQ).Normalized()) * rigid.Basis;
        mount.Transform = new Transform3D(basis, pivot - basis * pivotInMount);
    }
}
