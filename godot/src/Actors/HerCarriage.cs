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

    static readonly (string Bone, float Share)[] Spine = { ("spine_01", 0.2f), ("spine_02", 0.3f), ("spine_03", 0.35f), ("neck_01", 0.15f) };

    public HerCarriage() { Name = "HerCarriage"; }

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
    }
}
