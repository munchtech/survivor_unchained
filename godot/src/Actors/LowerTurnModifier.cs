using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her lower-body turn (A1 motion lead 19; math in logic/Play/LowerTurn). While she faces her aim and walks off it, her pelvis
/// (and so her legs, its children) is yawed by Delta about her root's up axis, and the spine takes it back out in mesh space
/// (spine_01 -0.4, spine_02 -0.3, spine_03 -0.3 of Delta), so spine_03's global and everything above it end as without the turn.
///
/// ORDER: right AFTER the PelvisCounterModifier (child index 2; People.Her). The counter reads the pelvis as the gait posed it
/// (Ph) and turns spine_01 by it; if the turn ran first the counter would see Ph yawed by Delta and counter-rotate the upper
/// layer's swing by our own turn. After it, the counter has its clean read, and our spine yaws act on its result: a global yaw
/// on each spine bone leaves the chest's global where it was whatever the counter did, because the shares sum to -1.
/// Nothing that reads her pose (HerPose, Gestures, P1Laws) runs before this, so they all see the turned legs and the untouched chest.
/// </summary>
public partial class LowerTurnModifier : SkeletonModifier3D
{
    /// <summary>Her root node (its up axis is the yaw's axis).</summary>
    public Node3D? Frame;
    /// <summary>The eased turn, degrees (PlayerView sets it each frame); 0 leaves everything alone.</summary>
    public float Delta;

    int pelvis = -1, s1 = -1, s2 = -1, s3 = -1;
    bool checkedRig;

    public LowerTurnModifier() { Name = "LowerTurn"; }

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (Mathf.Abs(Delta) < 0.01f || GetSkeleton() is not Skeleton3D sk) return;
        if (!checkedRig)
        {
            checkedRig = true;
            pelvis = sk.FindBone("pelvis"); s1 = sk.FindBone("spine_01"); s2 = sk.FindBone("spine_02"); s3 = sk.FindBone("spine_03");
            if (pelvis < 0 || s1 < 0 || s2 < 0 || s3 < 0 || sk.GetBoneParent(s1) != pelvis || sk.GetBoneParent(s2) != s1 || sk.GetBoneParent(s3) != s2)
            {
                GD.PrintErr("lower turn: no pelvis > spine_01 > spine_02 > spine_03 chain on this skeleton; it stays off");
                pelvis = -1;
            }
        }
        if (pelvis < 0) return;
        // Her root's up axis in the skeleton's space.
        var up = Frame != null && IsInstanceValid(Frame) ? Frame.GlobalBasis.Y : Vector3.Up;
        var axis = (sk.GlobalBasis.Inverse() * up).Normalized();
        var yaws = LowerTurn.SpineYaws(Delta);
        Turn(sk, pelvis, new Quaternion(axis, Mathf.DegToRad(Delta)));
        Turn(sk, s1, new Quaternion(axis, Mathf.DegToRad((float)yaws[0])));
        Turn(sk, s2, new Quaternion(axis, Mathf.DegToRad((float)yaws[1])));
        Turn(sk, s3, new Quaternion(axis, Mathf.DegToRad((float)yaws[2])));
    }

    /// <summary>The bone's global rotation pre-multiplied by yaw y (skeleton space), as a local pose rotation under its parent's current global.</summary>
    static void Turn(Skeleton3D sk, int bone, Quaternion y)
    {
        int par = sk.GetBoneParent(bone);
        var pg = par >= 0 ? sk.GetBoneGlobalPose(par).Basis.Orthonormalized().GetRotationQuaternion() : Quaternion.Identity;
        var g = pg * sk.GetBonePoseRotation(bone);
        sk.SetBonePoseRotation(bone, (pg.Inverse() * y * g).Normalized());
    }
}
