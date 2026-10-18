using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A living hold for a cinematic: when a clip has played to its end and holds its
/// last frame (a reach held out, a kneel by the fire), a body otherwise turns to
/// wax. This breathes it: the chest lifts and the shoulders rise a little on each
/// breath in, the head keeps its line (people steady the eyes), and the head drifts
/// a degree or so on a slow, uneven wander. Laid over the clip and the gestures,
/// before the head turns and her corrective joints. Each bend is about the body's
/// own side-to-side or front-to-back line (measured from the rest pose, so it
/// follows her lying or kneeling), never the world's. PersonView fades it in when
/// the base clip is held and out when a new one is cued.
/// </summary>
public partial class CineBreath : SkeletonModifier3D
{
    /// <summary>How much of the breath is wanted (0 to 1); it comes and goes at Rate per second.</summary>
    public float Want, Rate = 1.2f;
    /// <summary>Seconds per breath (about 14 a minute at rest).</summary>
    public float Period = 4.2f;
    /// <summary>Scale on every bend (1: a calm breath seen in a close shot).</summary>
    public float Depth = 1f;

    float weight;
    double phase, clock;
    bool found;
    int spine2 = -1, spine3 = -1, neck = -1, head = -1, clavL = -1, clavR = -1;
    // Each bone's side axis (the body's left-right) and forward axis, in its own frame.
    Vector3 s2Side, s3Side, neckSide, headSide, headUp, clavLFwd, clavRFwd;

    public CineBreath() { Name = "CineBreath"; }

    static int Bone(Skeleton3D sk, params string[] names)
    {
        foreach (var n in names) { int i = sk.FindBone(n); if (i >= 0) return i; }
        return -1;
    }

    static Vector3 Local(Skeleton3D sk, int bone, Vector3 axis) =>
        bone < 0 ? Vector3.Zero : (sk.GetBoneGlobalRest(bone).Basis.Orthonormalized().Inverse() * axis).Normalized();

    void Find(Skeleton3D sk)
    {
        found = true;
        spine2 = Bone(sk, "spine_02", "Spine1", "spine.002");
        spine3 = Bone(sk, "spine_03", "Chest", "Spine2", "spine.003");
        neck = Bone(sk, "neck_01", "Neck");
        head = Bone(sk, "Head", "head");
        clavL = Bone(sk, "clavicle_l", "Shoulder.L", "LeftShoulder");
        clavR = Bone(sk, "clavicle_r", "Shoulder.R", "RightShoulder");
        // At rest every body here faces +Z with its left toward +X.
        s2Side = Local(sk, spine2, Vector3.Right);
        s3Side = Local(sk, spine3, Vector3.Right);
        neckSide = Local(sk, neck, Vector3.Right);
        headSide = Local(sk, head, Vector3.Right);
        headUp = Local(sk, head, Vector3.Up);
        clavLFwd = Local(sk, clavL, Vector3.Back);
        clavRFwd = Local(sk, clavR, Vector3.Back);
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (!found) Find(sk);
        weight = Mathf.MoveToward(weight, Want, (float)delta * Rate);
        phase += delta / Mathf.Max(1f, Period) * Mathf.Tau;
        clock += delta;
        if (weight <= 0.001f || spine3 < 0) return;
        float k = weight * Depth;
        // In quicker than out: the breath rises over about two fifths of the cycle.
        double p = phase % Mathf.Tau / Mathf.Tau;
        float b = (float)(p < 0.4 ? 0.5 - 0.5 * System.Math.Cos(p / 0.4 * System.Math.PI) : 0.5 + 0.5 * System.Math.Cos((p - 0.4) / 0.6 * System.Math.PI));
        // The chest lifts (the upper back extends) and the shoulders rise.
        float lift = Mathf.DegToRad(1.1f) * b * k;
        if (spine2 >= 0) Bend(sk, spine2, s2Side, -lift * 0.45f);
        Bend(sk, spine3, s3Side, -lift);
        if (clavL >= 0) Bend(sk, clavL, clavLFwd, Mathf.DegToRad(1.3f) * b * k);
        if (clavR >= 0) Bend(sk, clavR, clavRFwd, -Mathf.DegToRad(1.3f) * b * k);
        // The head keeps its line through the breath, and wanders a little, unevenly.
        float nod = (float)(0.55 * System.Math.Sin(clock * Mathf.Tau / 7.3) + 0.45 * System.Math.Sin(clock * Mathf.Tau / 11.9 + 1.3));
        float yaw = (float)(0.6 * System.Math.Sin(clock * Mathf.Tau / 9.1 + 0.4) + 0.4 * System.Math.Sin(clock * Mathf.Tau / 15.7 + 2.1));
        float steady = lift * 1.25f;
        if (neck >= 0) Bend(sk, neck, neckSide, steady * 0.4f);
        if (head >= 0)
        {
            Bend(sk, head, headSide, steady * 0.6f + Mathf.DegToRad(0.8f) * nod * k);
            Bend(sk, head, headUp, Mathf.DegToRad(1.2f) * yaw * k);
        }
    }

    /// <summary>Turn a bone about one of its own rest axes (as it is posed now), by angle radians.</summary>
    static void Bend(Skeleton3D sk, int bone, Vector3 localAxis, float angle)
    {
        if (Mathf.Abs(angle) < 1e-6f || localAxis == Vector3.Zero) return;
        var g = sk.GetBoneGlobalPose(bone).Basis.Orthonormalized();
        var axis = (g * localAxis).Normalized();
        var turned = new Basis(new Quaternion(axis, angle)) * g;
        int parent = sk.GetBoneParent(bone);
        var pb = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(bone, (pb.Inverse() * turned).GetRotationQuaternion());
    }
}
