using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her arm-hold crossfade (animation 55, Play/ArmHold). The move tree hands her arms one hold or the other, switched at
/// once (a filtered copy of the move graph); through the fade this lays her arms between the two holds as they are
/// this frame (each sampled from its clips at the stride's time), in the chest's space rather than per bone. Each bone
/// turns along its chest-space arc; a hand holding a piece is split into the swing of the piece's own axis (along the
/// great circle from the walk's direction to the run's) and the twist about it, so the piece points straight between
/// the two holds and never through a per-bone mix (a geodesic turn alone swung the sword's tip 24 degrees off on a
/// cone). Runs first, on the tree's pose, before her carriage, her pose layer and the helpers that read the arm.
/// PlayerView feeds it the frame the tree shows (after Advance). --arm-log prints each fade's frames.
/// </summary>
public partial class HerArmHold : SkeletonModifier3D
{
    /// <summary>Lay the fade this frame: E from the walk's hold (0) to the run's (1).</summary>
    public bool Fading;
    public float E;
    /// <summary>The holds' clips and their times: the walk; the run and the sprint mixed by Fast.</summary>
    public Animation? Walk, Run, Sprint;
    public double WalkT, RunT;
    public float Fast;
    /// <summary>Each hand's piece axis in the hand bone's frame (zero: no piece; the hand turns on its arc).</summary>
    public Vector3 AxisR, AxisL;
    /// <summary>Degrees the arm swings out from her side at mid-fade (--arm-bump).</summary>
    public float Bump = float.TryParse(Args.Get("arm-bump"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var b) ? b : 12f;
    int pelvis = -1, spine3 = -1;
    int[] swings = System.Array.Empty<int>();

    /// <summary>From a's turn to b's by e, the piece's axis (in the bone's frame) swung along the great circle between
    /// its two directions and the twist about it eased alongside: the axis never leaves the arc.</summary>
    public static Quaternion SwingTwist(Quaternion a, Quaternion b, Vector3 axis, float e)
    {
        var x = axis.Normalized();
        Vector3 ua = a * x, ub = b * x;
        var c = ua.Cross(ub);
        float d = Mathf.Clamp(ua.Dot(ub), -1f, 1f);
        var swing = c.LengthSquared() > 1e-12f ? new Quaternion(c.Normalized(), Mathf.Acos(d)) : Quaternion.Identity;
        var twist = (swing.Inverse() * b * a.Inverse()).Normalized();
        swing = swing.Normalized();
        if (twist.W < 0) twist = -twist;
        return (Quaternion.Identity.Slerp(swing, e) * Quaternion.Identity.Slerp(twist, e) * a).Normalized();
    }

    readonly bool log = Args.Has("arm-log");
    int[] bones = System.Array.Empty<int>();
    int[] parentSlot = System.Array.Empty<int>();
    string[] paths = System.Array.Empty<string>();
    Quaternion[] rest = System.Array.Empty<Quaternion>(), cw = System.Array.Empty<Quaternion>(), cr = System.Array.Empty<Quaternion>(), co = System.Array.Empty<Quaternion>();
    int handR = -1, handL = -1;
    bool ready;
    readonly Dictionary<Animation, int[]> tracks = new();

    public HerArmHold() { Name = "HerArmHold"; }

    void Setup(Skeleton3D sk)
    {
        ready = true;
        var list = new List<int>();
        for (int b = 0; b < sk.GetBoneCount(); b++) if (ArmHold.IsArmBone(sk.GetBoneName(b))) list.Add(b);
        // Parents before children, so a bone's chest-space turn can use its parent's.
        int Depth(int b) { int d = 0; for (int p = sk.GetBoneParent(b); p >= 0; p = sk.GetBoneParent(p)) d++; return d; }
        list.Sort((a, c) => Depth(a).CompareTo(Depth(c)));
        bones = list.ToArray();
        int n = bones.Length;
        parentSlot = new int[n]; paths = new string[n]; rest = new Quaternion[n];
        cw = new Quaternion[n]; cr = new Quaternion[n]; co = new Quaternion[n];
        swings = new int[n];
        pelvis = sk.FindBone("pelvis"); spine3 = sk.FindBone("spine_03");
        for (int i = 0; i < n; i++)
        {
            parentSlot[i] = list.IndexOf(sk.GetBoneParent(bones[i]));
            var name = sk.GetBoneName(bones[i]);
            // The upper arm and all below it swing out (the clavicle and the shoulder's helpers stay).
            bool shoulder = name.StartsWith("clavicle") || name.StartsWith("trap") || name.StartsWith("scap") || name.StartsWith("pec") || name.StartsWith("lat") || name.StartsWith("upperarm_share");
            swings[i] = shoulder ? 0 : name.EndsWith("_l") ? 1 : -1;
            paths[i] = $"Armature/Skeleton3D:{name}";
            rest[i] = sk.GetBoneRest(bones[i]).Basis.Orthonormalized().GetRotationQuaternion().Normalized();
            if (name == "hand_r") handR = i;
            if (name == "hand_l") handL = i;
        }
    }

    int[] Tracks(Animation a)
    {
        if (tracks.TryGetValue(a, out var t)) return t;
        t = new int[paths.Length];
        for (int i = 0; i < paths.Length; i++) t[i] = a.FindTrack(paths[i], Animation.TrackType.Rotation3D);
        tracks[a] = t;
        return t;
    }

    Quaternion Sample(Animation a, int[] t, int i, double time) => (t[i] >= 0 ? a.RotationTrackInterpolate(t[i], time) : rest[i]).Normalized();

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (!Fading || Walk == null || Run == null || GetSkeleton() is not Skeleton3D sk) return;
        if (!ready) Setup(sk);
        int n = bones.Length;
        if (n == 0) return;
        float e = Mathf.Clamp(E, 0f, 1f);
        var tw = Tracks(Walk);
        var tr = Tracks(Run);
        var ts = Sprint != null && Fast > 1e-4f ? Tracks(Sprint) : null;
        for (int i = 0; i < n; i++)
        {
            var qw = Sample(Walk, tw, i, WalkT);
            var qr = Sample(Run, tr, i, RunT);
            if (ts != null) qr = qr.Slerp(Sample(Sprint!, ts, i, RunT), Fast).Normalized();
            int p = parentSlot[i];
            cw[i] = (p >= 0 ? cw[p] * qw : qw).Normalized();
            cr[i] = (p >= 0 ? cr[p] * qr : qr).Normalized();
            var axis = i == handR ? AxisR : i == handL ? AxisL : Vector3.Zero;
            co[i] = axis.LengthSquared() > 1e-8f ? SwingTwist(cw[i], cr[i], axis, e) : cw[i].Slerp(cr[i], e);
        }
        // Mid-fade the arm swung a little out from her side (sin-shaped, 0 at both holds), so a piece crossing from
        // trailing to forward passes beside her thigh, not through it (the stop's sword went 41 mm in without it).
        if (pelvis >= 0 && spine3 >= 0 && Bump > 0)
        {
            var f = (sk.GetBoneGlobalPose(spine3).Basis.Inverse() * (sk.GetBoneGlobalPose(pelvis).Basis * Vector3.Back)).Normalized();
            float th = Mathf.DegToRad(Bump) * Mathf.Sin(Mathf.Pi * e);
            var outL = new Quaternion(f, th).Normalized();
            var outR = new Quaternion(f, -th).Normalized();
            for (int i = 0; i < n; i++) if (swings[i] != 0) co[i] = ((swings[i] > 0 ? outL : outR) * co[i]).Normalized();
        }
        for (int i = 0; i < n; i++)
        {
            int p = parentSlot[i];
            var local = p >= 0 ? co[p].Inverse() * co[i] : co[i];
            sk.SetBonePoseRotation(bones[i], local.Normalized());
        }
        if (log && handR >= 0)
        {
            var a = AxisR.LengthSquared() > 1e-8f ? AxisR.Normalized() : Vector3.Down;
            Vector3 uw = cw[handR] * a, ur = cr[handR] * a, uo = co[handR] * a;
            float off = Mathf.RadToDeg(uo.AngleTo(uw) + uo.AngleTo(ur) - uw.AngleTo(ur));
            GD.Print($"armhold e {e:0.00} hand_r piece off the arc {off:0.0} deg (holds {Mathf.RadToDeg(uw.AngleTo(ur)):0} apart)");
        }
    }
}
