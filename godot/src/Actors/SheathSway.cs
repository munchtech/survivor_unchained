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
/// (her left wrist on its throat: SheathHang.HandHolds, read from the pose), the hang eased
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
    int handIdx = -2;
    bool held;

    public static SheathSway Attach(Skeleton3D skeleton, Node3D mount, string bone, Vector3 pivot, bool hilt = false)
    {
        var s = new SheathSway { Name = "SheathSway", mount = mount, rigid = mount.Transform, pivot = pivot, bone = bone, hilt = hilt };
        s.pivotInMount = mount.Transform.AffineInverse() * pivot;
        skeleton.AddChild(s);
        return s;
    }

    /// <summary>Whether her left hand holds the hilt now: its wrist within SheathHang.HoldOn of the throat as the rigid
    /// mount puts it (hysteresis to HoldOff). The pose, not the clip's name: under her AnimationTree the AnimationPlayer's
    /// current clip is empty, so the name list never engaged in play.</summary>
    Vector3 prevRel;
    bool havePrev;
    float wristSpeed = float.PositiveInfinity, wristToThroat;

    bool HiltHeldNow(Skeleton3D sk, float dt)
    {
        if (!hilt) return false;
        if (handIdx == -2) handIdx = sk.FindBone("hand_l");
        if (handIdx < 0) return held = false;
        var g = sk.GlobalTransform;
        var boneW = g * sk.GetBoneGlobalPose(idx);
        var throat = boneW * (rigid * new Vector3(0, SheathHang.Throat, 0));
        var wrist = g * sk.GetBoneGlobalPose(handIdx).Origin;
        var rel = boneW.AffineInverse() * wrist;
        wristSpeed = havePrev && dt > 0 ? wrist.DistanceTo(boneW * prevRel) / dt : float.PositiveInfinity;
        prevRel = rel;
        havePrev = true;
        wristToThroat = throat.DistanceTo(wrist);
        return held = SheathHang.HandHolds(held, wristToThroat, wristSpeed);
    }

    // `--hilt-tilt off`: held, the piece rides rigidly as before (before/after frames); `--hilt-held x,y,z`: another axis.
    static readonly bool TiltOff = Args.Get("hilt-tilt") == "off";
    bool tiltSet;
    Quaternion tilt = Quaternion.Identity;   // in the bone's space: the rigid shaft onto the held one

    void TiltOnce(Skeleton3D sk)
    {
        tiltSet = true;
        var held = WeaponSockets.HipBladeHeld;
        if (Args.Get("hilt-held") is string hh && hh.Split(',') is { Length: 3 } v)
            held = new N.Vector3(float.Parse(v[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(v[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(v[2], System.Globalization.CultureInfo.InvariantCulture));
        var rest = sk.GetBoneGlobalRest(idx).Basis.Orthonormalized();
        var shaft = rigid.Basis.Y.Normalized();
        var h = new Vector3(held.X, held.Y, held.Z).Normalized();
        if ((rest * shaft).X < 0) h.X = -h.X;
        tilt = new Quaternion(shaft, (rest.Inverse() * h).Normalized()).Normalized();
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
        var h = hang.Step(d, (float)delta, HiltHeldNow(sk, (float)delta));
        var hung = new Quaternion(h.X, h.Y, h.Z, h.W).Normalized();
        // The piece's turn in skeleton space: hung * rest * rigid; back in the bone's space under the pose.
        var basis = new Basis((poseQ.Inverse() * hung * restQ).Normalized()) * rigid.Basis;
        var at = new Transform3D(basis, pivot - basis * pivotInMount);
        // Held (the hang eased out), the piece turns about its throat onto WeaponSockets.HipBladeHeld, by as much as the
        // hand holds it: the throat stays under her hand.
        float k = hilt && !TiltOff ? 1f - hang.Weight : 0f;
        if (k > 0.001f)
        {
            if (!tiltSet) TiltOnce(sk);
            var throat = at * new Vector3(0, SheathHang.Throat, 0);
            var nb = new Basis(Quaternion.Identity.Slerp(tilt, k)) * at.Basis;
            at = new Transform3D(nb, throat - nb * new Vector3(0, SheathHang.Throat, 0));
        }
        mount.Transform = at;
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
        GD.Print(System.FormattableString.Invariant($"SHEATH w {hang.Weight:0.00} held {(held ? 1 : 0)} len {tipLen:0.000} scr {S(P(sp))} {S(P(th))} {S(P(tp))} ft {S(P(B("foot_l")))} {S(P(B("foot_r")))} {S(P(B("ball_l")))} {S(P(B("ball_r")))} w {W(sp)} {W(tp)} {W(th)} hl {W(hl)} v {wristSpeed:0.000} d {wristToThroat:0.000}"));
    }
}
