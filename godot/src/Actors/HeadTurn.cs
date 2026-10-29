using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A look with the head, not the body (a cinematic's "head" cue): the neck and
/// the head turn toward a point in the world, the neck taking the smaller part,
/// as far as a neck goes, eased in and out. Laid over whatever the body is
/// doing (after the clip and the other modifiers), so she can kneel on her heels
/// and look over her shoulder at the trail, or Rook lift her eyes to a window.
/// The face's forward is measured from the rest pose: at rest every body here
/// faces +Z.
/// </summary>
public partial class HeadTurn : SkeletonModifier3D
{
    /// <summary>The point looked at (world space); null lets the head go. A new point while the head is already
    /// looking is not jumped to: the aim travels from where it was to the new point at Rate, fast in and slow out
    /// (Play/GazeShift.Skewed), as a head turns (C01 s10: a re-aim over 0.14 s at full weight popped the head from
    /// bowed to profile in one frame, judge Cinematics 7 r1).</summary>
    public Vector3? Target
    {
        get => target;
        set
        {
            if (Glide && value is Vector3 v && target is Vector3 was && weight > 0.001f && v.DistanceSquaredTo(was) > 1e-8f)
            { from = Aim(); travel = 0; }
            else if (value is null || weight <= 0.001f) travel = 1;
            target = value;
        }
    }
    /// <summary>A new Target travels (a cinematic's head cue); off, it is taken at once (play's Watch, set each
    /// frame to a moving camera, follows it as before).</summary>
    public bool Glide;
    Vector3? target;
    Vector3 from;
    float travel = 1;

    /// <summary>Where the head is aimed now: on its way from the last point to the target, or the target.</summary>
    Vector3 Aim() => target is not Vector3 t ? from : travel >= 1 ? t : from.Lerp(t, SurvivorUnchained.Play.GazeShift.Skewed(travel));
    /// <summary>How much of the look is wanted (0 to 1), and how fast it comes (per second).</summary>
    public float Want, Rate = 2;
    /// <summary>How far the head turns from where the body has it, at most (degrees).</summary>
    public float Limit = 75;
    float weight;
    int head = -1, neck = -1, spine = -1;
    Vector3 headForward, neckForward, headUp, neckUp, spineUp;

    public HeadTurn() { Name = "HeadTurn"; }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (head < 0)
        {
            head = sk.FindBone("Head");
            // (her skeleton's neck is neck_01: found as "Neck" alone her look turned her head only, 33 deg on one
            // joint in town's close-up, and her neck's skin between pinched; Face lead 32, 21 Oct)
            neck = sk.FindBone("Neck");
            if (neck < 0) neck = sk.FindBone("neck_01");
            if (head < 0) return;
            var hr = sk.GetBoneGlobalRest(head).Basis.Orthonormalized().Inverse();
            headForward = (hr * Vector3.Back).Normalized();
            headUp = (hr * Vector3.Up).Normalized();
            if (neck >= 0)
            {
                var nr = sk.GetBoneGlobalRest(neck).Basis.Orthonormalized().Inverse();
                neckForward = (nr * Vector3.Back).Normalized();
                neckUp = (nr * Vector3.Up).Normalized();
                spine = sk.GetBoneParent(neck);
                if (spine >= 0) spineUp = (sk.GetBoneGlobalRest(spine).Basis.Orthonormalized().Inverse() * Vector3.Up).Normalized();
            }
        }
        weight = Mathf.MoveToward(weight, Want, (float)delta * Rate);
        if (travel < 1) travel = Mathf.Min(1, travel + (float)delta * Rate);
        if (weight <= 0.001f || Target is null) return;
        var local = sk.GlobalTransform.AffineInverse() * Aim();
        // Lying down the head keeps its roll with the body (C01 s3: her face on its side on the ground,
        // tipped toward the coals): it is levelled only as far as the body under it stands upright.
        float level = spine >= 0 ? Mathf.SmoothStep(0.35f, 0.7f, (sk.GetBoneGlobalPose(spine).Basis.Orthonormalized() * spineUp).Dot(Vector3.Up)) : 1;
        // The neck takes two fifths of the turn, the head the rest.
        if (neck >= 0) Turn(sk, neck, neckForward, neckUp, local, weight * 0.4f, Limit * 0.4f, level);
        Turn(sk, head, headForward, headUp, local, weight, Limit, level);
    }

    static void Turn(Skeleton3D sk, int bone, Vector3 forward, Vector3 up, Vector3 target, float k, float limit, float level)
    {
        var g = sk.GetBoneGlobalPose(bone);
        var basis = g.Basis.Orthonormalized();
        Vector3 now = (basis * forward).Normalized(), want = (target - g.Origin).Normalized();
        float angle = now.AngleTo(want);
        if (angle < 1e-4f) return;
        var axis = now.Cross(want);
        if (axis.LengthSquared() < 1e-8f) return;
        float turn = Mathf.Min(angle, Mathf.DegToRad(limit)) * k;
        var q = new Quaternion(axis.Normalized(), turn);
        var newBasis = new Basis(q) * basis;
        // The shortest turn tips the head over; a person keeps the head level as it
        // turns, so the roll about the new forward is taken back toward the body's up.
        Vector3 fwd = (newBasis * forward).Normalized(), headUpNow = (newBasis * up).Normalized();
        Vector3 upright = (Vector3.Up - fwd * fwd.Dot(Vector3.Up)).Normalized();
        Vector3 have = (headUpNow - fwd * fwd.Dot(headUpNow)).Normalized();
        if (upright.LengthSquared() > 0.5f && have.LengthSquared() > 0.5f && level > 0)
        {
            float roll = have.SignedAngleTo(upright, fwd);
            newBasis = new Basis(new Quaternion(fwd, roll * 0.8f * k * level)) * newBasis;
        }
        int parent = sk.GetBoneParent(bone);
        var parentBasis = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(bone, (parentBasis.Inverse() * newBasis).GetRotationQuaternion());
    }
}
