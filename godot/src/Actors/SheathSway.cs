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
        if (Log && hilt) LogLine(sk);
    }

    // (warden-move, town run) `--sheath-log`: the hip sword's scabbard as drawn, once a frame: the hang's weight and
    // whether the clip holds the hilt; on screen (px) the sheath point, the throat (where the run's hand lies, 0.16 m
    // down), the scabbard's tip, both feet and balls; then in the world the sheath point, the tip and the left hand.
    static readonly bool Log = Args.Has("sheath-log");
    float tipLen = -1;

    void LogLine(Skeleton3D sk)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null || mount == null) return;
        if (tipLen < 0)
        {
            tipLen = 0;
            foreach (var n in mount.FindChildren("scabbard", "", true, false))
                if (n is Node3D sc)
                    foreach (var m in sc.FindChildren("*", "MeshInstance3D", true, false))
                        if (m is MeshInstance3D mi) tipLen = Mathf.Max(tipLen, (mount.GlobalTransform.AffineInverse() * mi.GlobalTransform * mi.GetAabb().End).Y);
        }
        var g = mount.GlobalTransform;
        Vector3 sp = g.Origin, th = g * new Vector3(0, 0.16f, 0), tp = g * new Vector3(0, tipLen, 0);
        Vector3 B(string b) { int i = sk.FindBone(b); return i >= 0 ? sk.GlobalTransform * sk.GetBoneGlobalPose(i).Origin : Vector3.Zero; }
        Vector2 P(Vector3 v) => cam.UnprojectPosition(v);
        var hl = B("hand_l");
        string S(Vector2 v) => System.FormattableString.Invariant($"{v.X:0.0} {v.Y:0.0}");
        string W(Vector3 v) => System.FormattableString.Invariant($"{v.X:0.000} {v.Y:0.000} {v.Z:0.000}");
        GD.Print(System.FormattableString.Invariant($"SHEATH w {hang.Weight:0.00} held {(held ? 1 : 0)} len {tipLen:0.000} scr {S(P(sp))} {S(P(th))} {S(P(tp))} ft {S(P(B("foot_l")))} {S(P(B("foot_r")))} {S(P(B("ball_l")))} {S(P(B("ball_r")))} w {W(sp)} {W(tp)} {W(th)} hl {W(hl)}"));
    }
}
