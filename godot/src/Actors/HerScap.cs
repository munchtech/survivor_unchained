using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// Her scapulae (Body 6 S1, Play/ScapRotation): scap_l/scap_r turned up about the scapular plane's normal as each arm
/// rises (22.6 degrees at 115, 37.6 at 150), read from the arm as HerShrug and HerRaise left it. Only on a skeleton with
/// the bones (tools/assets/scap_rig_post.py builds them into her body): every other body is untouched. Knobs:
/// --scap-off, --scap-log. Python's twin: tools/anim/helpers.py scap (inside helpers.drive).
/// </summary>
public partial class HerScap : SkeletonModifier3D
{
    readonly bool off = Args.Has("scap-off"), log = Args.Has("scap-log");
    int pelvis = -2, neck = -1;
    readonly int[] scap = { -1, -1 }, upper = { -1, -1 }, lower = { -1, -1 };
    readonly N.Quaternion[] rest = new N.Quaternion[2], globalRest = new N.Quaternion[2];
    double logT;

    public HerScap() { Name = "HerScap"; }

    static N.Vector3 V(Vector3 v) => new(v.X, v.Y, v.Z);
    static N.Quaternion Q(Basis b) { var q = b.Orthonormalized().GetRotationQuaternion(); return new(q.X, q.Y, q.Z, q.W); }

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (off || GetSkeleton() is not Skeleton3D sk) return;
        if (pelvis == -2)
        {
            pelvis = sk.FindBone("pelvis"); neck = sk.FindBone("neck_01");
            string[] s = { "l", "r" };
            for (int i = 0; i < 2; i++)
            {
                scap[i] = sk.FindBone("scap_" + s[i]); upper[i] = sk.FindBone("upperarm_" + s[i]); lower[i] = sk.FindBone("lowerarm_" + s[i]);
                if (scap[i] < 0) continue;
                rest[i] = Q(sk.GetBoneRest(scap[i]).Basis);
                globalRest[i] = Q(sk.GetBoneGlobalRest(scap[i]).Basis);
            }
        }
        if (pelvis < 0 || neck < 0 || (scap[0] < 0 && scap[1] < 0)) return;
        var down = N.Vector3.Normalize(V(sk.GetBoneGlobalPose(pelvis).Origin - sk.GetBoneGlobalPose(neck).Origin));
        bool print = log && (logT += delta) > 0.1;
        if (print) logT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (scap[i] < 0 || upper[i] < 0 || lower[i] < 0) continue;
            float a = ScapRotation.ArmAngle(V(sk.GetBoneGlobalPose(upper[i]).Origin), V(sk.GetBoneGlobalPose(lower[i]).Origin), down);
            float deg = ScapRotation.Angle(a);
            var q = ScapRotation.Local(rest[i], globalRest[i], ScapRotation.Axis(i == 0), deg);
            sk.SetBonePoseRotation(scap[i], new Quaternion(q.X, q.Y, q.Z, q.W).Normalized());
            if (print) GD.Print($"scap {(i == 0 ? "l" : "r")} A {a:0.0} deg {deg:0.0}");
        }
    }
}
