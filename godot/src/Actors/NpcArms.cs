using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// A package NPC's arm set over the shared town clips (World.NpcArmSet; manifest "arms": {"in": DEG, "wrist": SHARE}).
/// After the animation each upper arm is turned In degrees toward the body about the chest's forward axis (the frontal
/// plane only: the clip's forward and back swing is kept), never closer than NpcArmSet.Floor to hanging straight, and
/// the hand is taken Wrist of the way from the clip's wrist bend back toward its rest. Runs before HerJoints so the
/// twist and share bones follow. Package NPCs only (NpcPackage); a cinematic may set Influence to 0.
/// </summary>
public partial class NpcArms : SkeletonModifier3D
{
    public float In, Wrist;
    int[] upper = { -1, -1 }, hand = { -1, -1 };
    int spine = -1, neck = -1;
    Skeleton3D? found;

    public NpcArms(float inDeg, float wrist) { Name = "NpcArms"; In = inDeg; Wrist = wrist; }

    void Find(Skeleton3D sk)
    {
        found = sk;
        upper = new[] { sk.FindBone("upperarm_l"), sk.FindBone("upperarm_r") };
        hand = new[] { sk.FindBone("hand_l"), sk.FindBone("hand_r") };
        spine = sk.FindBone("spine_01"); neck = sk.FindBone("neck_01");
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (sk != found) Find(sk);
        if (upper[0] < 0 || upper[1] < 0 || spine < 0 || neck < 0) return;
        // The chest's frame from the pose: up (spine to neck), right (shoulder to shoulder), forward (their cross).
        var up = (sk.GetBoneGlobalPose(neck).Origin - sk.GetBoneGlobalPose(spine).Origin).Normalized();
        var across = sk.GetBoneGlobalPose(upper[1]).Origin - sk.GetBoneGlobalPose(upper[0]).Origin;
        var right = (across - up * up.Dot(across)).Normalized();
        var fwd = up.Cross(right).Normalized();
        for (int s = 0; s < 2; s++)
        {
            int b = upper[s], c = sk.GetBoneParent(b);
            if (In > 0f)
            {
                var g = sk.GetBoneGlobalPose(b);
                int child = sk.FindBone(s == 0 ? "lowerarm_l" : "lowerarm_r");
                if (child >= 0)
                {
                    var d = (sk.GetBoneGlobalPose(child).Origin - g.Origin).Normalized();
                    float lat = d.Dot(right), down = -d.Dot(up);
                    float abd = Mathf.RadToDeg(Mathf.Atan2(Mathf.Abs(lat), down));
                    float turn = NpcArmSet.TurnIn(abd, In);
                    if (turn > 0f)
                    {
                        // the sign that takes the arm toward the body (its lateral part shrinks)
                        var q = new Quaternion(fwd, Mathf.DegToRad(turn));
                        if (Mathf.Abs((q * d).Dot(right)) > Mathf.Abs(lat)) q = new Quaternion(fwd, -Mathf.DegToRad(turn));
                        var pb = c >= 0 ? sk.GetBoneGlobalPose(c).Basis.Orthonormalized() : Basis.Identity;
                        var want = new Basis(q) * g.Basis.Orthonormalized();
                        sk.SetBonePoseRotation(b, (pb.Inverse() * want).GetRotationQuaternion().Normalized());
                    }
                }
            }
            if (Wrist > 0f && hand[s] >= 0)
                sk.SetBonePoseRotation(hand[s], sk.GetBonePoseRotation(hand[s]).Slerp(sk.GetBoneRest(hand[s]).Basis.GetRotationQuaternion(), Wrist).Normalized());
        }
    }
}
