using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The heroine's own carriage, laid over whatever clip is playing (the
/// clips were made for the Quaternius bodies, which are built differently):
/// her fingers eased halfway back to rest, so a relaxed hand is relaxed and
/// not a claw; her upper arms brought in toward her body, which the clips
/// hold out for narrower hips; and a little contrapposto, her weight on one
/// hip and her shoulders answering it.
/// </summary>
public partial class HerPose : SkeletonModifier3D
{
    /// <summary>How far the fingers go back toward rest (0 none, 1 all).</summary>
    public float FingerEase = 0.5f;
    /// <summary>Degrees the upper arms come in toward the body.</summary>
    public float ArmsIn = 9f;
    /// <summary>Degrees of hip tilt (the shoulders answer at half).</summary>
    public float HipTilt = 3.5f;

    public HerPose() { Name = "HerPose"; }

    /// <summary>The library's own pelvis at rest (UAL), against which a
    /// clip's pelvis track is written.</summary>
    static readonly Vector3 LibraryPelvis = new(0, 0.0501f, 0.9167f);

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        // Clips set the pelvis where the library's stands; hers stands
        // higher (longer legs): the clip's motion kept, measured from hers.
        int pel = sk.FindBone("pelvis");
        if (pel >= 0) sk.SetBonePosePosition(pel, sk.GetBonePosePosition(pel) - LibraryPelvis + sk.GetBoneRest(pel).Origin);
        int n = sk.GetBoneCount();
        for (int b = 0; b < n; b++)
        {
            var name = sk.GetBoneName(b);
            if (name.StartsWith("index") || name.StartsWith("middle") || name.StartsWith("ring") || name.StartsWith("pinky") || name.StartsWith("thumb_02") || name.StartsWith("thumb_03"))
            {
                var rest = sk.GetBoneRest(b).Basis.GetRotationQuaternion();
                var pose = sk.GetBonePoseRotation(b);
                sk.SetBonePoseRotation(b, pose.Slerp(rest, FingerEase));
            }
        }
        Turn(sk, "upperarm_l", Vector3.Forward, -ArmsIn);
        Turn(sk, "upperarm_r", Vector3.Forward, ArmsIn);
        Turn(sk, "pelvis", Vector3.Forward, HipTilt);
        Turn(sk, "spine_03", Vector3.Forward, -HipTilt * 0.5f);
    }

    /// <summary>A bone turned about an axis of the skeleton's own space, by
    /// `degrees`, about its head.</summary>
    static void Turn(Skeleton3D sk, string bone, Vector3 axis, float degrees)
    {
        int b = sk.FindBone(bone);
        if (b < 0) return;
        var g = sk.GetBoneGlobalPose(b);
        var r = new Basis(axis, Mathf.DegToRad(degrees));
        var ng = new Transform3D(r * g.Basis, g.Origin);
        int p = sk.GetBoneParent(b);
        var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
        sk.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
    }
}
