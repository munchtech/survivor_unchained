using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// Her clavicle lift as an arm rises (armor 17 C2; body5 lift, Play/ClavicleLift): from 60 degrees her shoulder girdle
/// rises with the arm (a smoothstep: 5 at level, 15 at 115, 34 overhead), the clip's own clavicle counting; her hands
/// stay where the clip put them. Runs
/// before HerRaise (whose pose-space shapes read the lifted clavicle) and HerJoints (whose twists follow the re-aimed arm).
/// Arms at or below 60 degrees: nothing changes. Knobs: --shrug-off, --shrug-log. Python's twin: tools/anim/helpers.py shrug
/// (inside helpers.drive, so the bakes and wearcheck pose her the same).
/// </summary>
public partial class HerShrug : SkeletonModifier3D
{
    readonly bool off = Args.Has("shrug-off"), log = Args.Has("shrug-log");
    int pelvis = -1, neck = -1, chest = -1;
    readonly int[] clav = { -1, -1 }, upper = { -1, -1 }, lower = { -1, -1 }, hand = { -1, -1 };
    readonly float[] restEl = new float[2];
    readonly bool[] scap = new bool[2];   // a side with her scapula helper (SPEC "scap"): the lower clavicle curve
    double logT;

    public HerShrug() { Name = "HerShrug"; }

    static N.Vector3 V(Vector3 v) => new(v.X, v.Y, v.Z);
    static N.Quaternion Q(Basis b) { var q = b.Orthonormalized().GetRotationQuaternion(); return new(q.X, q.Y, q.Z, q.W); }
    static Quaternion G(N.Quaternion q) => new Quaternion(q.X, q.Y, q.Z, q.W).Normalized();

    (N.Vector3 Down, N.Vector3 Left, N.Vector3 Fwd) Torso(System.Func<int, Transform3D> pose)
    {
        var down = N.Vector3.Normalize(V(pose(pelvis).Origin - pose(neck).Origin));
        var left = V(pose(chest).Basis.X.Normalized());
        left = N.Vector3.Normalize(left - N.Vector3.Dot(left, down) * down);
        return (down, left, N.Vector3.Cross(down, left));
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (off || GetSkeleton() is not Skeleton3D sk) return;
        if (pelvis < 0)
        {
            pelvis = sk.FindBone("pelvis"); neck = sk.FindBone("neck_01"); chest = sk.FindBone("spine_03");
            string[] s = { "l", "r" };
            for (int i = 0; i < 2; i++)
            {
                clav[i] = sk.FindBone("clavicle_" + s[i]); upper[i] = sk.FindBone("upperarm_" + s[i]);
                lower[i] = sk.FindBone("lowerarm_" + s[i]); hand[i] = sk.FindBone("hand_" + s[i]);
                scap[i] = sk.FindBone("scap_" + s[i]) >= 0;
            }
            if (pelvis < 0 || neck < 0 || chest < 0) return;
            var rd = Torso(sk.GetBoneGlobalRest).Down;
            for (int i = 0; i < 2; i++)
                if (clav[i] >= 0 && upper[i] >= 0)
                    restEl[i] = ClavicleLift.Elevation(V(sk.GetBoneGlobalRest(upper[i]).Origin - sk.GetBoneGlobalRest(clav[i]).Origin), rd);
        }
        if (pelvis < 0 || neck < 0 || chest < 0) return;
        var (down, left, fwd) = Torso(sk.GetBoneGlobalPose);
        bool print = log && (logT += delta) > 0.1;
        if (print) logT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (clav[i] < 0 || upper[i] < 0 || lower[i] < 0 || hand[i] < 0) continue;
            Transform3D tc = sk.GetBoneGlobalPose(clav[i]), tu = sk.GetBoneGlobalPose(upper[i]),
                tl = sk.GetBoneGlobalPose(lower[i]), th = sk.GetBoneGlobalPose(hand[i]);
            var arm = new ClavicleLift.Arm
            {
                Clavicle = V(tc.Origin), Shoulder = V(tu.Origin), Elbow = V(tl.Origin), Hand = V(th.Origin),
                ClavicleTurn = Q(tc.Basis), UpperTurn = Q(tu.Basis), LowerTurn = Q(tl.Basis),
            };
            var (a, rise, lift) = ClavicleLift.Apply(ref arm, down, i == 0 ? left : -left, fwd, restEl[i], scap[i]);
            if (print) GD.Print($"shrug {(i == 0 ? "l" : "r")} A {a:0.0} rise {rise:0.0} lift {lift:0.00}");
            if (lift <= 0) continue;
            int p = sk.GetBoneParent(clav[i]);
            var parent = p >= 0 ? sk.GetBoneGlobalPose(p).Basis.Orthonormalized().GetRotationQuaternion() : Quaternion.Identity;
            Quaternion c = G(arm.ClavicleTurn), u = G(arm.UpperTurn), l = G(arm.LowerTurn),
                hw = th.Basis.Orthonormalized().GetRotationQuaternion();
            sk.SetBonePoseRotation(clav[i], (parent.Inverse() * c).Normalized());
            sk.SetBonePoseRotation(upper[i], (c.Inverse() * u).Normalized());
            sk.SetBonePoseRotation(lower[i], (u.Inverse() * l).Normalized());
            sk.SetBonePoseRotation(hand[i], (l.Inverse() * hw).Normalized());
        }
    }
}
