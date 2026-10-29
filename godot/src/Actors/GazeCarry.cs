using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The head's part in a look of her eyes (Play/GazeShift, run by HerFaceLife): a big look is not the eyes alone, the
/// head turns after them and the eyes roll back as it comes. A small yaw (about the head's own up, + toward her left)
/// and pitch (about its own left axis, + down), laid on top of whatever posed the head, the clip and any scripted
/// head look (kept after HeadTurn among the skeleton's modifiers), the neck taking two fifths, the head the rest, as
/// HeadTurn shares a turn. Nothing is done at zero, so play is untouched unless a look is set.
/// </summary>
public partial class GazeCarry : SkeletonModifier3D
{
    /// <summary>The head's turn (degrees): yaw + toward her left, pitch + down.</summary>
    public float Yaw, Pitch;
    int head = -1, neck = -1;
    Vector3 headUp, headLeft, neckUp, neckLeft;

    public GazeCarry() { Name = "GazeCarry"; }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null || (Mathf.Abs(Yaw) < 0.01f && Mathf.Abs(Pitch) < 0.01f)) return;
        if (head < 0)
        {
            head = sk.FindBone("Head");
            neck = sk.FindBone("Neck");
            if (neck < 0) neck = sk.FindBone("neck_01");
            if (head < 0) return;
            // (her body's up and left at rest, in each bone's own frame: at rest every body here faces +Z, up +Y, her left +X)
            var hr = sk.GetBoneGlobalRest(head).Basis.Orthonormalized().Inverse();
            headUp = (hr * Vector3.Up).Normalized();
            headLeft = (hr * Vector3.Right).Normalized();
            if (neck >= 0)
            {
                var nr = sk.GetBoneGlobalRest(neck).Basis.Orthonormalized().Inverse();
                neckUp = (nr * Vector3.Up).Normalized();
                neckLeft = (nr * Vector3.Right).Normalized();
            }
        }
        if (neck >= 0) Turn(sk, neck, neckUp, neckLeft, 0.4f);
        Turn(sk, head, headUp, headLeft, neck >= 0 ? 0.6f : 1f);
    }

    void Turn(Skeleton3D sk, int bone, Vector3 up, Vector3 left, float k)
    {
        var basis = sk.GetBoneGlobalPose(bone).Basis.Orthonormalized();
        Vector3 u = (basis * up).Normalized(), l = (basis * left).Normalized();
        // (pitch about the head's left tips its forward down; yaw about its up turns it toward her left)
        var turned = new Basis(u, Mathf.DegToRad(Yaw * k)) * new Basis(l, Mathf.DegToRad(Pitch * k)) * basis;
        int parent = sk.GetBoneParent(bone);
        var parentBasis = parent >= 0 ? sk.GetBoneGlobalPose(parent).Basis.Orthonormalized() : Basis.Identity;
        sk.SetBonePoseRotation(bone, (parentBasis.Inverse() * turned).GetRotationQuaternion());
    }
}
