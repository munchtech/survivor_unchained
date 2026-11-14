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
    /// <summary>The right arm carries (Corvane's lamp, in the hand his cast clip raises: P6 judge r1 fix 4); else the left.</summary>
    public bool Right;
    /// <summary>How far the carry holds its fist out ahead (0: the torch's and Corvane's lay, the forearm well down; 1: a hand
    /// lamp held out to light the way, the upper arm a little forward and the forearm near level, so a short lamp hangs
    /// clear of the thighs and a skirt's front: a package's own lamp, World.NpcHeld). The fist's own frame does not change.</summary>
    public float Reach;
    int up = -1, lo = -1, hand = -1, spine = -1, neck = -1, other = -1;
    Skeleton3D? found;

    public NpcTorchArm() { Name = "NpcTorchArm"; }

    void Find(Skeleton3D sk) { found = sk; (up, lo, hand, other, spine, neck) = Bones(sk, Right); }

    static (int Up, int Lo, int Hand, int Other, int Spine, int Neck) Bones(Skeleton3D sk, bool right)
    {
        string s = right ? "r" : "l", o = right ? "l" : "r";
        return (sk.FindBone($"upperarm_{s}"), sk.FindBone($"lowerarm_{s}"), sk.FindBone($"hand_{s}"), sk.FindBone($"upperarm_{o}"),
            sk.FindBone("spine_01"), sk.FindBone("neck_01"));
    }

    /// <summary>The directions the arm is laid along, in the chest's frame (up, `r` toward the body's middle from the carrying
    /// shoulder: the chest's right for the left arm, its left for the right; forward): the upper arm, the forearm, and the
    /// fist's fingers.</summary>
    public static (Vector3 Upper, Vector3 Fore, Vector3 Fist) Lay(Vector3 u, Vector3 r, Vector3 f, float reach = 0) =>
        ((-u * 1.0f - r * 0.21f).Lerp(-u * 0.9f + f * 0.55f - r * 0.3f, reach).Normalized(),
         (f * 0.57f - u * 0.82f - r * 0.12f).Lerp(f * 1.0f - u * 0.22f - r * 0.48f, reach).Normalized(),
         (f * 0.9f - u * 0.2f - r * 0.3f).Normalized());

    /// <summary>The arm raised overhead (the clip's own raise of that hand: Corvane's cast lifting the lamp): the upper arm
    /// up, a little forward and out, the forearm on up; the fist's frame is Lay's, so what it holds hangs as it does in the carry.</summary>
    public static (Vector3 Upper, Vector3 Fore) Raised(Vector3 u, Vector3 r, Vector3 f) =>
        ((u * 0.86f + f * 0.3f - r * 0.4f).Normalized(), (u * 0.95f + f * 0.28f - r * 0.1f).Normalized());

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        if (up < 0 || lo < 0 || hand < 0 || spine < 0 || neck < 0 || other < 0) return;
        Lift(sk, up, lo, hand, spine, neck, other, Right, Reach);
    }

    /// <summary>The same arm laid on a skeleton as posed now, outside the modifier pass (Vat's bake of a crowd body that
    /// carries a lamp: the bake seeks the clip and reads the bones, so no modifier runs there).</summary>
    public static bool Lift(Skeleton3D sk, bool right = false, float reach = 0)
    {
        var (up, lo, hand, other, spine, neck) = Bones(sk, right);
        if (up < 0 || lo < 0 || hand < 0 || spine < 0 || neck < 0 || other < 0) return false;
        Lift(sk, up, lo, hand, spine, neck, other, right, reach);
        return true;
    }

    /// <summary>The fist's frame in the chest's (up, `r` toward the middle, forward): fingers along Lay's fist line, the palm
    /// toward the body. A thing held in it is turned by this frame's inverse to stand upright in the chest's frame.</summary>
    public static Basis FistIn(Vector3 u, Vector3 r, Vector3 f)
    {
        var dH = Lay(u, r, f).Fist;
        var palm = (r - dH * r.Dot(dH)).Normalized();
        return new Basis(dH.Cross(palm).Normalized(), dH, palm);
    }

    /// <summary>How far the clip has raised the carrying hand (0: at or below the shoulder; 1: most of an arm above it).</summary>
    static float Raise(Skeleton3D sk, int up, int lo, int hand, Vector3 u)
    {
        var s = sk.GetBoneGlobalPose(up).Origin;
        float len = sk.GetBonePose(lo).Origin.Length() + sk.GetBonePose(hand).Origin.Length();
        float h = (sk.GetBoneGlobalPose(hand).Origin - s).Dot(u);
        float w = Mathf.Clamp(h / Mathf.Max(1e-4f, 0.7f * len), 0, 1);
        return w * w * (3 - 2 * w);
    }

    static void Lift(Skeleton3D sk, int up, int lo, int hand, int spine, int neck, int other, bool right, float reach)
    {
        var gU = sk.GetBoneGlobalPose(up);
        var u = (sk.GetBoneGlobalPose(neck).Origin - sk.GetBoneGlobalPose(spine).Origin).Normalized();
        // (toward the body's middle from the carrying shoulder; the chest's right, from the left arm)
        var across = sk.GetBoneGlobalPose(other).Origin - gU.Origin;
        var r = (across - u * u.Dot(across)).Normalized();
        // (the chest's forward: its right crossed with up; from the right arm `r` is the chest's left, so flip it)
        var f = (right ? r.Cross(u) : u.Cross(r)).Normalized();
        var (dU, dF, dH) = Lay(u, r, f, reach);
        float w = Raise(sk, up, lo, hand, u);
        if (w > 0)
        {
            var (rU, rF) = Raised(u, r, f);
            dU = dU.Slerp(rU, w).Normalized();
            dF = dF.Slerp(rF, w).Normalized();
        }

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
