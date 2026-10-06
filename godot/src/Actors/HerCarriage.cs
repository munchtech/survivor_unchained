using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// How she carries herself over whatever clip plays, the parts no clip can
/// know: she leans into a turn (banking, as a runner does, more the faster
/// she goes) and into a start or a stop; and while her legs run where she is
/// going, her back turns toward what she strikes at (the legs keep their
/// line, the spine takes the turn, a share at each vertebra, the head going
/// with it). Set by the player's view every frame. Runs after the clips and
/// before her corrective pose and her springs.
/// </summary>
public partial class HerCarriage : SkeletonModifier3D
{
    /// <summary>Degrees she banks (+ toward her right, as into a right turn).</summary>
    public float Bank;
    /// <summary>Degrees she pitches forward (+) or back from the ankles.</summary>
    public float Tilt;
    /// <summary>Degrees her back turns toward a blow (+ toward her left).</summary>
    public float Aim;
    /// <summary>How much of her head's droop below HeadEase is taken back (0: as the clip carries
    /// it, 1: all of it), a third at her neck. From play's camera, 56 degrees above her, her hair's
    /// crown hid her brow and the top of her eyes, and her face was a sliver: carried with her chin
    /// a little up, as a fighter walking toward trouble carries it, her eyes and mouth show.
    /// (Play only: her clips are as they were in cinematics and close views.)</summary>
    public float HeadLevel;
    /// <summary>Where her head is brought to, in degrees below level (less than nought: above). At
    /// 12 above her mouth showed from play's camera; 8 is enough for eyes and mouth to read without a
    /// haughty tilt. (--head-ease tries others.)</summary>
    static readonly float HeadEase = SurvivorUnchained.Args.Has("head-ease") ? SurvivorUnchained.Args.Num("head-ease", -8f) : -8f;

    static readonly (string Bone, float Share)[] Spine = { ("spine_01", 0.2f), ("spine_02", 0.3f), ("spine_03", 0.35f), ("neck_01", 0.15f) };

    public HerCarriage() { Name = "HerCarriage"; }

    int head = -2, neck = -2;
    Vector3 headForward;

    /// <summary>Her head brought up: the droop of her face's forward below the
    /// horizon, less HeadEase, times HeadLevel, turned up about the level axis across her face.</summary>
    void Level(Skeleton3D sk)
    {
        if (head == -2)
        {
            head = sk.FindBone("Head");
            neck = sk.FindBone("neck_01");
            // (at rest every body here faces +Z: the face's forward in the head's own frame)
            if (head >= 0) headForward = (sk.GetBoneGlobalRest(head).Basis.Orthonormalized().Inverse() * Vector3.Back).Normalized();
        }
        if (head < 0) return;
        var fwd = (sk.GetBoneGlobalPose(head).Basis.Orthonormalized() * headForward).Normalized();
        float droop = Mathf.RadToDeg(-Mathf.Asin(Mathf.Clamp(fwd.Y, -1, 1))) - HeadEase;
        if (droop <= 0) return;
        var axis = fwd.Cross(Vector3.Up);
        if (axis.LengthSquared() < 1e-6f) return;
        axis = axis.Normalized();
        float lift = Mathf.DegToRad(Mathf.Min(droop, 35) * HeadLevel);
        foreach (var (bone, share) in new[] { (neck, 0.35f), (head, 0.65f) })
        {
            if (bone < 0) continue;
            var g = sk.GetBoneGlobalPose(bone);
            var ng = new Transform3D(new Basis(axis, lift * share) * g.Basis, g.Origin);
            int p = sk.GetBoneParent(bone);
            var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
            sk.SetBonePoseRotation(bone, local.Basis.GetRotationQuaternion());
        }
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        // Bank and tilt about her feet: the root bone stands on the ground
        // between them, so turning it leans the whole of her from there.
        if (Mathf.Abs(Bank) > 0.01f || Mathf.Abs(Tilt) > 0.01f)
        {
            int root = sk.FindBone("root");
            if (root >= 0)
            {
                // (She faces +Z, her left +X: about +Z tips her toward her
                // right, about +X tips her forward.)
                var turn = new Basis(new Vector3(0, 0, 1), Mathf.DegToRad(Bank)) * new Basis(new Vector3(1, 0, 0), Mathf.DegToRad(Tilt));
                var g = sk.GetBoneGlobalPose(root);
                sk.SetBonePoseRotation(root, (turn * g.Basis).GetRotationQuaternion());
            }
        }
        if (Mathf.Abs(Aim) > 0.01f)
            foreach (var (bone, share) in Spine)
            {
                int b = sk.FindBone(bone);
                if (b < 0) continue;
                // About the skeleton's up, from the bone's head.
                var g = sk.GetBoneGlobalPose(b);
                var r = new Basis(Vector3.Up, Mathf.DegToRad(Aim * share));
                var ng = new Transform3D(r * g.Basis, g.Origin);
                int p = sk.GetBoneParent(b);
                var local = p >= 0 ? sk.GetBoneGlobalPose(p).AffineInverse() * ng : ng;
                sk.SetBonePoseRotation(b, local.Basis.GetRotationQuaternion());
            }
        if (HeadLevel > 0.01f) Level(sk);
    }
}
