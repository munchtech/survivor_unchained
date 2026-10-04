using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her soft tissue on springs: each breast and buttock bone
/// (tools/assets/build_heroine.py) has a mass at its tip that follows where
/// the clip puts it, lagging, overshooting and settling, in the world (so a
/// stride, a landing or a turn sets it moving, not only the clip). The bone
/// is turned toward the mass and stretched a little along its line, so the
/// flesh swings and gives rather than sliding.
/// </summary>
public partial class HerJiggle : SkeletonModifier3D
{
    /// <summary>Overall strength: 0 still, 1 as tuned, more for the bold.</summary>
    public float Amount = 1f;

    /// <summary>How much the flesh squashes and stretches as it swings: none
    /// under formed plate, which holds its shape (it moves, it never gives).</summary>
    public float Squash = 1f;

    sealed class Mass
    {
        public required string Bone;
        public required float Stiffness, Damping, Reach, Stretch;
        public int Index = -1;
        public Vector3 P, V;
        public bool Live;
    }

    // Stiffness (1/s²) and damping (1/s) give a breast about three swings a
    // second dying away in under a second; buttocks are firmer, quicker.
    readonly Mass[] masses =
    {
        new() { Bone = "breast_l", Stiffness = 250, Damping = 7, Reach = 0.04f, Stretch = 0.12f },
        new() { Bone = "breast_r", Stiffness = 250, Damping = 7, Reach = 0.04f, Stretch = 0.12f },
        new() { Bone = "glute_l", Stiffness = 400, Damping = 10, Reach = 0.025f, Stretch = 0.08f },
        new() { Bone = "glute_r", Stiffness = 400, Damping = 10, Reach = 0.025f, Stretch = 0.08f },
    };

    public HerJiggle() { Name = "HerJiggle"; }


    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null || Amount <= 0) return;
        float dt = Mathf.Clamp((float)delta, 0f, 1f / 20);
        var world = sk.GlobalTransform;
        foreach (var m in masses)
        {
            if (m.Index < 0) m.Index = sk.FindBone(m.Bone);
            if (m.Index < 0) continue;
            var pose = sk.GetBoneGlobalPose(m.Index);
            float len = BoneLength(sk, m.Index);
            var head = world * pose.Origin;
            var target = world * (pose.Origin + pose.Basis.Y.Normalized() * len);
            if (!m.Live || dt <= 0) { m.P = target; m.V = Vector3.Zero; m.Live = true; continue; }
            // Small steps, so a stiff spring stays stable at a low frame rate.
            // Past its reach the flesh is held by a far stiffer spring (skin
            // and ligament taking up), so a hard stride ends in a soft stop
            // and a rebound, never a pin.
            float reach = m.Reach * Amount;
            const int steps = 4;
            float h = dt / steps;
            for (int i = 0; i < steps; i++)
            {
                var off = m.P - target;
                var a = -off * m.Stiffness - m.V * m.Damping;
                float over = off.Length() - reach;
                if (over > 0) a -= off.Normalized() * over * m.Stiffness * 8;
                m.V += a * h;
                m.P += m.V * h;
            }
            var o = m.P - target;
            if (o.Length() > reach * 1.6f) m.P = target + o.Normalized() * reach * 1.6f;
            // The bone turned from where the clip put its tip to the mass.
            var inv = world.AffineInverse();
            var from = (inv * target - pose.Origin);
            var to = (inv * (target + (m.P - target) * Amount) - pose.Origin);
            if (from.LengthSquared() < 1e-8 || to.LengthSquared() < 1e-8) continue;
            var turn = new Quaternion(from.Normalized(), to.Normalized());
            var basis = new Basis(turn) * pose.Basis;
            // Stretched along its line as the mass pulls away, squashed as it
            // presses in, the width answering so the volume holds.
            float k = 1 + Mathf.Clamp((to.Length() - from.Length()) / Mathf.Max(reach, 1e-4f), -1, 1) * m.Stretch * Squash;
            var global = new Transform3D(basis, pose.Origin);
            int parent = sk.GetBoneParent(m.Index);
            var local = parent >= 0 ? sk.GetBoneGlobalPose(parent).AffineInverse() * global : global;
            sk.SetBonePoseRotation(m.Index, local.Basis.GetRotationQuaternion());
            float side = 1 / Mathf.Sqrt(Mathf.Max(k, 0.5f));
            sk.SetBonePoseScale(m.Index, new Vector3(side, k, side));
        }
    }

    static float BoneLength(Skeleton3D sk, int bone)
    {
        // A leaf bone's length is not stored; these were made 8 to 10 cm.
        return sk.GetBoneName(bone).StartsWith("glute") ? 0.10f : 0.085f;
    }

    /// <summary>A push the springs feel at once (a landing, a blow), in metres
    /// per second, in the world.</summary>
    public void Kick(Vector3 velocity)
    {
        foreach (var m in masses) m.V += velocity;
    }
}
