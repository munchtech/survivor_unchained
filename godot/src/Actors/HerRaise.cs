using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her pectoral's pull on each breast as that arm rises (Armor 16): past about
/// horizontal the breast bone turns up and out toward the same side's armpit,
/// lifts a little and stretches along that line, narrowing in projection so
/// the volume holds. Per side, from the upper arm's elevation in her chest's
/// frame (Play/RaiseRamp). Runs before HerJiggle, so the springs follow the
/// raised pose and plate's hold still works; under plate (HerJiggle.Squash 0)
/// the cup moves rigidly and never stretches. Every top carries her skin
/// weights, so all of them follow. Arms down nothing changes.
/// Knobs: --raise-off, --raise-start/-full (deg), --raise-pitch/-yaw (deg),
/// --raise-up/-out/-back (m), --raise-sup/-sside (stretch), --raise-log.
/// </summary>
public partial class HerRaise : SkeletonModifier3D
{
    public float Start = Args.Num("raise-start", -10f);
    public float Full = Args.Num("raise-full", 70f);
    public float Pitch = Args.Num("raise-pitch", 14f);
    public float Yaw = Args.Num("raise-yaw", 8f);
    public float Up = Args.Num("raise-up", 0.016f);
    public float Out = Args.Num("raise-out", 0.006f);
    public float Back = Args.Num("raise-back", 0.004f);
    public float StretchUp = Args.Num("raise-sup", 0.08f);
    public float StretchSide = Args.Num("raise-sside", 0.03f);
    readonly bool off = Args.Has("raise-off"), log = Args.Has("raise-log");

    int chest = -1;
    readonly int[] breast = { -1, -1 }, upper = { -1, -1 }, lower = { -1, -1 };
    double logT;

    public HerRaise() { Name = "HerRaise"; }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null || off) return;
        if (chest < 0)
        {
            chest = sk.FindBone("spine_03");
            string[] s = { "l", "r" };
            for (int i = 0; i < 2; i++)
            {
                breast[i] = sk.FindBone("breast_" + s[i]);
                upper[i] = sk.FindBone("upperarm_" + s[i]);
                lower[i] = sk.FindBone("lowerarm_" + s[i]);
            }
        }
        if (chest < 0) return;
        float squash = sk.GetNodeOrNull<HerJiggle>("../HerJiggle") is HerJiggle j ? j.Squash : 1f;
        var inv = sk.GetBoneGlobalPose(chest).AffineInverse();
        bool print = log && (logT += delta) > 0.1;
        if (print) logT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (breast[i] < 0 || upper[i] < 0 || lower[i] < 0) continue;
            var dir = (inv * sk.GetBoneGlobalPose(lower[i]).Origin - inv * sk.GetBoneGlobalPose(upper[i]).Origin).Normalized();
            float el = RaiseRamp.Elevation(dir.Y);
            float w = RaiseRamp.Weight(el, Start, Full);
            if (print) GD.Print($"raise {(i == 0 ? "l" : "r")} el {el:0.0} w {w:0.00}");
            if (w <= 0) continue;
            // Left is +X in her chest's frame. Breast bones are children of
            // spine_03, so their pose is already in the chest's frame.
            float side = i == 0 ? 1 : -1;
            var turn = new Quaternion(Vector3.Up, Mathf.DegToRad(Yaw * side * w))
                     * new Quaternion(Vector3.Right, Mathf.DegToRad(-Pitch * w));
            int b = breast[i];
            sk.SetBonePosePosition(b, sk.GetBonePosePosition(b) + new Vector3(Out * side, Up, -Back) * w);
            sk.SetBonePoseRotation(b, (turn * sk.GetBonePoseRotation(b)).Normalized());
            // Bone axes (build_heroine.py): X across, Y out along the breast, Z down the chest.
            var (sx, sy, sz) = RaiseRamp.Stretch(w * squash, StretchUp, StretchSide);
            sk.SetBonePoseScale(b, sk.GetBonePoseScale(b) * new Vector3(sx, sy, sz));
        }
    }
}
