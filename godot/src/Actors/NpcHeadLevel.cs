using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Keeps a package NPC's head level under the heroine's retargeted clips (a guard's head rolling toward
/// one shoulder in the idle, a villager's face dropping in the walk). After the animation it takes the
/// head's roll to zero and its pitch back inside +-PitchBand of level, keeping the clip's yaw and any
/// motion inside the band. The neck takes 40% of the correction, the head the rest. Eased with a
/// per-frame blend so it never snaps. The head's forward and up are read from this rig's own Head rest.
/// Package NPCs only; a cinematic sets the modifier's own Influence (SkeletonModifier3D) to 0 to let the clip's head through.
/// </summary>
public partial class NpcHeadLevel : SkeletonModifier3D
{
    /// <summary>Pitch kept free either side of level (degrees).</summary>
    public float PitchBand = 5;
    /// <summary>Follow speed (per second); the correction eases toward its target at 1 - e^(-Rate dt).</summary>
    public float Rate = 8;
    int head = -1, neck = -1;
    Vector3 headForward, headUp;
    Quaternion smooth = Quaternion.Identity;

    public NpcHeadLevel() { Name = "NpcHeadLevel"; }

    /// <summary>The world-space (skeleton-space) rotation that puts a head with this forward and up level:
    /// pitch clamped into the band, roll removed, yaw untouched.</summary>
    public static Quaternion Correction(Vector3 forward, Vector3 up, float bandDeg)
    {
        forward = forward.Normalized(); up = up.Normalized();
        float pitch = Mathf.Asin(Mathf.Clamp(forward.Y, -1, 1));
        float band = Mathf.DegToRad(bandDeg);
        float want = Mathf.Clamp(pitch, -band, band);
        var q = Quaternion.Identity;
        var f = forward;
        Vector3 axis = forward.Cross(Vector3.Up);
        if (axis.LengthSquared() > 1e-8f && Mathf.Abs(want - pitch) > 1e-5f)
        {
            q = new Quaternion(axis.Normalized(), want - pitch);
            f = q * forward;
        }
        var u = q * up;
        Vector3 upright = (Vector3.Up - f * f.Dot(Vector3.Up)).Normalized();
        Vector3 have = (u - f * f.Dot(u)).Normalized();
        if (upright.LengthSquared() > 0.5f && have.LengthSquared() > 0.5f)
            q = new Quaternion(f, have.SignedAngleTo(upright, f)) * q;
        return q.Normalized();
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (head < 0)
        {
            head = sk.FindBone("Head");
            if (head < 0) { head = -2; return; }
            neck = sk.FindBone("Neck");
            var hr = sk.GetBoneGlobalRest(head).Basis.Orthonormalized().Inverse();
            // Bone-space axes that point forward and up when the rig stands at rest facing +Z.
            headForward = (hr * Vector3.Back).Normalized();
            headUp = (hr * Vector3.Up).Normalized();
        }
        if (head < 0) return;
        var hb = sk.GetBoneGlobalPose(head).Basis.Orthonormalized();
        var target = Correction(hb * headForward, hb * headUp, PitchBand);   // (the engine blends by the modifier's own Influence)
        smooth = smooth.Slerp(target, 1 - Mathf.Exp(-Rate * (float)delta)).Normalized();
        if (smooth.AngleTo(Quaternion.Identity) < 1e-4f) return;
        if (neck >= 0)
        {
            var qn = Quaternion.Identity.Slerp(smooth, 0.4f);
            Apply(sk, neck, qn);
        }
        // The head takes the rest: what lands it at the full correction from where the clip had it.
        var want = new Basis(smooth) * hb;
        int parent = sk.GetBoneParent(head);
        var pb = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(head, (pb.Inverse() * want).GetRotationQuaternion());
    }

    static void Apply(Skeleton3D sk, int bone, Quaternion q)
    {
        var b = new Basis(q) * sk.GetBoneGlobalPose(bone).Basis.Orthonormalized();
        int parent = sk.GetBoneParent(bone);
        var pb = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(bone, (pb.Inverse() * b).GetRotationQuaternion());
    }
}
