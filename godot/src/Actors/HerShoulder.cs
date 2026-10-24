using Godot;
using SurvivorUnchained.Play;
using N = System.Numerics;

namespace SurvivorUnchained.View;

/// <summary>
/// Her shoulder's muscle helpers (Body 6 S2, Play/ShoulderHelpers): delt, trap, pec and lat per side, each moved as its
/// parent bone does and, as the arm rises past 60 degrees (full at 120), turned, stretched and shifted toward the arm.
/// A is read as HerScap reads it. Only on a skeleton with the bones (tools/assets/shoulder_rig_post.py builds them into
/// her body): every other body is untouched, and a side without its delt_{s} is skipped. Knobs: --shoulder-off,
/// --shoulder-log. Python's twin: tools/anim/helpers.py shoulder_pose.
/// </summary>
public partial class HerShoulder : SkeletonModifier3D
{
    readonly bool off = Args.Has("shoulder-off"), log = Args.Has("shoulder-log");
    int pelvis = -2, neck = -1;
    readonly int[] upper = { -1, -1 }, lower = { -1, -1 };
    readonly Rig[] rigs = new Rig[8];
    double logT;

    sealed class Rig
    {
        public ShoulderHelpers.Kind Kind = null!;
        public bool Left;
        public int Bone, Parent, On;
        public N.Quaternion Rp0, Rh0, Ron0;
        public N.Vector3 Op0, Oh0, Oon0, Off, T0Value;
        public bool HasAim;
        public float L0;
    }

    public HerShoulder() { Name = "HerShoulder"; }

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
                upper[i] = sk.FindBone("upperarm_" + s[i]); lower[i] = sk.FindBone("lowerarm_" + s[i]);
                if (sk.FindBone("delt_" + s[i]) < 0 || upper[i] < 0 || lower[i] < 0) continue;
                var u0 = V(sk.GetBoneGlobalRest(upper[i]).Origin);
                var e0 = V(sk.GetBoneGlobalRest(lower[i]).Origin);
                for (int k = 0; k < 4; k++)
                {
                    var kind = ShoulderHelpers.All[k];
                    int b = sk.FindBone(kind.Name + "_" + s[i]);
                    int p = sk.FindBone(kind.Parent.Replace("{s}", s[i]));
                    int on = sk.FindBone(kind.On.Replace("{s}", s[i]));
                    if (b < 0 || p < 0 || on < 0) continue;
                    var r = new Rig { Kind = kind, Left = i == 0, Bone = b, Parent = p, On = on };
                    var gh = sk.GetBoneGlobalRest(b);
                    r.Rh0 = Q(gh.Basis); r.Oh0 = V(gh.Origin);
                    var gp = sk.GetBoneGlobalRest(p);
                    r.Rp0 = Q(gp.Basis); r.Op0 = V(gp.Origin);
                    var go = sk.GetBoneGlobalRest(on);
                    r.Ron0 = Q(go.Basis); r.Oon0 = V(go.Origin);
                    var (t0, l0) = ShoulderHelpers.RestAim(kind, r.Left, u0, e0, r.Oh0);
                    r.HasAim = t0.HasValue; r.T0Value = t0 ?? default; r.L0 = l0;
                    r.Off = ShoulderHelpers.Off(kind, r.Left);
                    rigs[i * 4 + k] = r;
                }
            }
        }
        if (pelvis < 0 || neck < 0) return;
        var down = N.Vector3.Normalize(V(sk.GetBoneGlobalPose(pelvis).Origin - sk.GetBoneGlobalPose(neck).Origin));
        bool print = log && (logT += delta) > 0.1;
        if (print) logT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (upper[i] < 0 || lower[i] < 0 || rigs[i * 4] == null) continue;
            float a = ScapRotation.ArmAngle(V(sk.GetBoneGlobalPose(upper[i]).Origin), V(sk.GetBoneGlobalPose(lower[i]).Origin), down);
            if (print) GD.Print($"shoulder {(i == 0 ? "l" : "r")} A {a:0.0} g {ShoulderHelpers.G(a):0.00}");
            for (int k = 0; k < 4; k++)
            {
                var r = rigs[i * 4 + k];
                if (r == null) continue;
                var gp = sk.GetBoneGlobalPose(r.Parent);
                var go = sk.GetBoneGlobalPose(r.On);
                var (q, sc, pos) = ShoulderHelpers.Pose(r.Kind, Q(gp.Basis), V(gp.Origin), r.Rp0, r.Op0, r.Rh0, r.Oh0,
                    Q(go.Basis), V(go.Origin), r.Ron0, r.Oon0, r.HasAim ? r.T0Value : null, r.L0, r.Off, a);
                sk.SetBonePoseRotation(r.Bone, new Quaternion(q.X, q.Y, q.Z, q.W).Normalized());
                sk.SetBonePoseScale(r.Bone, new Vector3(sc.X, sc.Y, sc.Z));
                sk.SetBonePosePosition(r.Bone, new Vector3(pos.X, pos.Y, pos.Z));
            }
        }
    }
}
