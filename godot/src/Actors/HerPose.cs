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
    /// <summary>Degrees the neck is bowed forward: a body whose neck leans
    /// further forward at rest than the library's (the hero's) has his head
    /// thrown back by its clips without it.</summary>
    public float NeckPitch = 0f;
    /// <summary>How much of what is playing is her own (tools/anim, made on
    /// her skeleton): 0 a library clip, wholly corrected; 1 her own, left as
    /// made. Split in two because the body's halves can play different
    /// clips (a swing over the run): Lower is the pelvis and hips, Upper the
    /// arms and hands.</summary>
    public float Lower, Upper;
    /// <summary>Both halves at once.</summary>
    public float Native { set { Lower = Upper = value; } }

    public HerPose() { Name = "HerPose"; }

    /// <summary>The library's own pelvis at rest (UAL), against which a
    /// clip's pelvis track is written.</summary>
    static readonly Vector3 LibraryPelvis = new(0, 0.0501f, 0.9167f);

    // The bones it moves, found once (asking the skeleton for every bone's
    // name each frame made a string of each, and a frame's worth of garbage).
    Skeleton3D? found;
    int pelvis = -1, upperL = -1, upperR = -1, spine3 = -1, neck = -1;
    int[] fingers = System.Array.Empty<int>();

    void Find(Skeleton3D sk)
    {
        found = sk;
        pelvis = sk.FindBone("pelvis");
        upperL = sk.FindBone("upperarm_l");
        upperR = sk.FindBone("upperarm_r");
        spine3 = sk.FindBone("spine_03");
        neck = sk.FindBone("neck_01");
        var list = new System.Collections.Generic.List<int>();
        for (int b = 0; b < sk.GetBoneCount(); b++)
        {
            var name = sk.GetBoneName(b);
            if (name.StartsWith("index") || name.StartsWith("middle") || name.StartsWith("ring") || name.StartsWith("pinky") || name.StartsWith("thumb_02") || name.StartsWith("thumb_03"))
                list.Add(b);
        }
        fingers = list.ToArray();
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        // Clips set the pelvis where the library's stands; hers stands
        // higher (longer legs): the clip's motion kept, measured from hers.
        // (Her own clips are made at her height already: the shift fades
        // with them.)
        float lib = 1 - Mathf.Clamp(Lower, 0, 1), arms = 1 - Mathf.Clamp(Upper, 0, 1);
        int pel = pelvis;
        if (pel >= 0 && lib > 0) sk.SetBonePosePosition(pel, sk.GetBonePosePosition(pel) + (sk.GetBoneRest(pel).Origin - LibraryPelvis) * lib);
        if (arms > 0)
            foreach (int b in fingers)
            {
                var rest = sk.GetBoneRest(b).Basis.GetRotationQuaternion();
                var pose = sk.GetBonePoseRotation(b);
                sk.SetBonePoseRotation(b, pose.Slerp(rest, FingerEase * arms));
            }
        if (arms > 0)
        {
            Turn(sk, upperL, Vector3.Forward, -ArmsIn * arms);
            Turn(sk, upperR, Vector3.Forward, ArmsIn * arms);
            if (NeckPitch != 0) Turn(sk, neck, Vector3.Right, NeckPitch * arms);
        }
        if (lib > 0)
        {
            Turn(sk, pelvis, Vector3.Forward, HipTilt * lib);
            Turn(sk, spine3, Vector3.Forward, -HipTilt * 0.5f * lib);
        }
    }

    /// <summary>A bone turned about an axis of the skeleton's own space, by
    /// `degrees`, about its head.</summary>
    static void Turn(Skeleton3D sk, int b, Vector3 axis, float degrees)
    {
        if (b < 0) return;
        var g = sk.GetBoneGlobalPose(b);
        var r = new Basis(axis, Mathf.DegToRad(degrees));
        var ng = new Transform3D(r * g.Basis, g.Origin);
        int p = sk.GetBoneParent(b);
        var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
        sk.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
    }
}
