using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A package NPC's left arm carrying a lit torch (the night Watch, NPC 17): the kit's "handslot.l" stood the torch up
/// in a hanging hand, but on the generated packages the left hand only has the heroine rig's hand_l, its fingers along
/// +Y and the palm toward +Z, so a torch mounted on it hung down the leg. After the clip, the upper arm hangs a little
/// forward and out, the forearm comes up forward to just below the horizontal (the elbow near a right angle), and the
/// fist is set straight on the forearm with the palm toward the body and the wrist cocked up a little, so the torch it
/// grips stands up ahead of the left shoulder and its light falls across the face. The chest's frame is read from the
/// pose (spine to neck, shoulder to shoulder), so the body's own sway and stride still carry the arm. Added before
/// HerJoints (PersonView.Hold), so the twist and share bones follow; the fingers close round the shaft (NpcHands.FistL).
/// </summary>
public partial class NpcTorchArm : SkeletonModifier3D
{
    int up = -1, lo = -1, hand = -1, spine = -1, neck = -1, ur = -1;
    Skeleton3D? found;

    public NpcTorchArm() { Name = "NpcTorchArm"; }

    void Find(Skeleton3D sk)
    {
        found = sk;
        up = sk.FindBone("upperarm_l"); lo = sk.FindBone("lowerarm_l"); hand = sk.FindBone("hand_l");
        ur = sk.FindBone("upperarm_r"); spine = sk.FindBone("spine_01"); neck = sk.FindBone("neck_01");
    }

    /// <summary>The directions the arm is laid along, in the chest's frame (up, right, forward): the upper arm, the
    /// forearm, and the fist's fingers.</summary>
    public static (Vector3 Upper, Vector3 Fore, Vector3 Fist) Lay(Vector3 u, Vector3 r, Vector3 f) =>
        ((-u * 1.0f + f * 0.15f - r * 0.5f).Normalized(), (f * 0.75f - u * 0.7f - r * 0.4f).Normalized(), (f * 0.8f + u * 0.38f - r * 0.3f).Normalized());

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        if (up < 0 || lo < 0 || hand < 0 || spine < 0 || neck < 0 || ur < 0) return;
        var gU = sk.GetBoneGlobalPose(up);
        var u = (sk.GetBoneGlobalPose(neck).Origin - sk.GetBoneGlobalPose(spine).Origin).Normalized();
        var across = sk.GetBoneGlobalPose(ur).Origin - gU.Origin;
        var r = (across - u * u.Dot(across)).Normalized();
        var f = u.Cross(r).Normalized();
        var (dU, dF, dH) = Lay(u, r, f);

        // The upper arm: its line (shoulder to elbow) turned onto dU, the least turn.
        int pu = sk.GetBoneParent(up);
        var pb = pu >= 0 ? sk.GetBoneGlobalPose(pu).Basis.Orthonormalized() : Basis.Identity;
        var bU = gU.Basis.Orthonormalized();
        var loLocal = sk.GetBonePose(lo);
        var cur = (bU * loLocal.Origin).Normalized();
        bU = new Basis(new Quaternion(cur, dU)) * bU;
        sk.SetBonePoseRotation(up, (pb.Inverse() * bU).GetRotationQuaternion().Normalized());

        // The forearm under it: its line (elbow to wrist) onto dF.
        var bL = bU * loLocal.Basis.Orthonormalized();
        var handLocal = sk.GetBonePose(hand);
        cur = (bL * handLocal.Origin).Normalized();
        bL = new Basis(new Quaternion(cur, dF)) * bL;
        sk.SetBonePoseRotation(lo, (bU.Inverse() * bL).GetRotationQuaternion().Normalized());

        // The fist: fingers (+Y) along dH, the palm (+Z) toward the body, the knuckle line (+X) their cross.
        var palm = (r - dH * r.Dot(dH)).Normalized();
        var bH = new Basis(dH.Cross(palm).Normalized(), dH, palm);
        sk.SetBonePoseRotation(hand, (bL.Inverse() * bH).GetRotationQuaternion().Normalized());
    }
}

/// <summary>A held piece kept standing up in the world whatever the hand under it does (the torch in a fist: its
/// flame stays above the shaft), tilted Lean radians forward of its holder's facing.</summary>
public partial class UprightNode : Node3D
{
    public float Lean = 0.12f;
    /// <summary>Its size in the world (its holder's root scale): the bone chain above it carries the rig's own scale.</summary>
    public float Size = 1f;

    public override void _Process(double delta)
    {
        var g = GlobalTransform;
        float s = Size;
        // (its holder's facing, from the skeleton above it: the flat forward of the first Node3D ancestor's basis)
        var fwd = (GetParent()?.GetParent() as Node3D)?.GlobalBasis.Z ?? Vector3.Forward;
        fwd.Y = 0;
        var axis = fwd.LengthSquared() > 1e-6 ? Vector3.Up.Cross(fwd.Normalized()) : Vector3.Right;
        GlobalTransform = new Transform3D(new Basis(axis.Normalized(), Lean).Scaled(new Vector3(s, s, s)), g.Origin);
    }
}
