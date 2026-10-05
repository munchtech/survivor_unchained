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
    /// <summary>The point looked at (world space); null lets the head go.</summary>
    public Vector3? Target;
    /// <summary>How much of the look is wanted (0 to 1), and how fast it comes (per second).</summary>
    public float Want, Rate = 2;
    /// <summary>How far the head turns from where the body has it, at most (degrees).</summary>
    public float Limit = 75;
    float weight;
    int head = -1, neck = -1;
    Vector3 headForward, neckForward, headUp, neckUp;

    public HeadTurn() { Name = "HeadTurn"; }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (head < 0)
        {
            head = sk.FindBone("Head");
            neck = sk.FindBone("Neck");
            if (head < 0) return;
            var hr = sk.GetBoneGlobalRest(head).Basis.Orthonormalized().Inverse();
            headForward = (hr * Vector3.Back).Normalized();
            headUp = (hr * Vector3.Up).Normalized();
            if (neck >= 0)
            {
                var nr = sk.GetBoneGlobalRest(neck).Basis.Orthonormalized().Inverse();
                neckForward = (nr * Vector3.Back).Normalized();
                neckUp = (nr * Vector3.Up).Normalized();
            }
        }
        weight = Mathf.MoveToward(weight, Want, (float)delta * Rate);
        if (weight <= 0.001f || Target is not Vector3 target) return;
        var local = sk.GlobalTransform.AffineInverse() * target;
        // The neck takes two fifths of the turn, the head the rest.
        if (neck >= 0) Turn(sk, neck, neckForward, neckUp, local, weight * 0.4f, Limit * 0.4f);
        Turn(sk, head, headForward, headUp, local, weight, Limit);
    }

    static void Turn(Skeleton3D sk, int bone, Vector3 forward, Vector3 up, Vector3 target, float k, float limit)
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
        Vector3 level = (Vector3.Up - fwd * fwd.Dot(Vector3.Up)).Normalized();
        Vector3 have = (headUpNow - fwd * fwd.Dot(headUpNow)).Normalized();
        if (level.LengthSquared() > 0.5f && have.LengthSquared() > 0.5f)
        {
            float roll = have.SignedAngleTo(level, fwd);
            newBasis = new Basis(new Quaternion(fwd, roll * 0.8f * k)) * newBasis;
        }
        int parent = sk.GetBoneParent(bone);
        var parentBasis = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(bone, (parentBasis.Inverse() * newBasis).GetRotationQuaternion());
    }
}
