using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her pelvis counter (A1 motion lead 19; math in logic/Play/PelvisCounter). While her upper shot plays a swing's
/// `_run` clip (one with `pelvis_mean` meta), spine_01 is turned so the upper layer rides the walk's MEAN pelvis and
/// not the pelvis as the gait has turned it this frame.
///
/// ORDER (found, People.Her): a skeleton's SkeletonModifier3Ds run in child order, after the AnimationTree has posed
/// the bones. P1BlendBase is first (it turns the clips' keys by M R_B^-1 on the mixer's pose, pelvis and spine
/// included: the counter must read the pelvis AFTER it), then this counter, then HerPose, Gestures, HerShrug...,
/// then P1Laws last (it reads the globals and writes the helper bones), then P1Jiggle and HerFaceLife. P1Laws.Reorder
/// moves only itself, the blend base (to 0) and the springs, so this stays at index 1 (the base at 0 on B). Nothing
/// that reads her pose runs before it but the blend base, which only re-expresses the mixer's keys.
/// Spine_01 is assumed a child of the pelvis (checked once; a rig where it is not is left alone).
/// </summary>
public partial class PelvisCounterModifier : SkeletonModifier3D
{
    /// <summary>Her root node (the frame the clip's mean is in); the skeleton's own frame is turned into it.</summary>
    public Node3D? Frame;
    /// <summary>The upper clip's mean pelvis (its `pelvis_mean` meta), or null: nothing changes.</summary>
    public System.Numerics.Quaternion? Mean;
    /// <summary>The upper shot's blend weight now (PlayerView sets it each frame; 0 when no upper shot is live).</summary>
    public float Weight;

    int pelvis = -1, spine = -1;
    bool checkedRig;

    public PelvisCounterModifier() { Name = "PelvisCounter"; }

    static System.Numerics.Quaternion N(Quaternion q) => new(q.X, q.Y, q.Z, q.W);

    public override void _ProcessModificationWithDelta(double delta)
    {
        if (Mean is not { } mean || Weight <= 1e-4f || GetSkeleton() is not Skeleton3D sk) return;
        if (!checkedRig)
        {
            checkedRig = true;
            pelvis = sk.FindBone("pelvis"); spine = sk.FindBone("spine_01");
            if (pelvis < 0 || spine < 0 || sk.GetBoneParent(spine) != pelvis)
            {
                GD.PrintErr("pelvis counter: no pelvis > spine_01 chain on this skeleton; it stays off");
                pelvis = spine = -1;
            }
        }
        if (pelvis < 0) return;
        // Ph in her root's frame: the skeleton's pose turned by the skeleton's place under the root.
        var frame = Frame != null && IsInstanceValid(Frame) ? (Frame.GlobalTransform.AffineInverse() * sk.GlobalTransform).Basis.GetRotationQuaternion() : Quaternion.Identity;
        var ph = frame * sk.GetBoneGlobalPose(pelvis).Basis.Orthonormalized().GetRotationQuaternion();
        var l = sk.GetBonePoseRotation(spine);
        var r = Play.PelvisCounter.Apply(mean, N(ph), N(l), Play.PelvisCounter.K, Weight);
        sk.SetBonePoseRotation(spine, new Quaternion(r.X, r.Y, r.Z, r.W).Normalized());
    }
}
