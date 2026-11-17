using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>Body B's (P1Laws) armor-only hip hinges and tasset hinge (tools/anim/helpers.py SPEC "hinges"/"tassets",
/// body_p1/rig_helpers.json, lane G 17 Nov). The same laws as hers (HipHinge); what differs is the body: the pivots are
/// the spec's moved with their bone (helpers.hinge_pivot(hg, s, sk), resolved into the body's own rig_helpers.json) and
/// B's pelvis rest frame is not hers, so every line is read in the parent's global rest frame (`parentRest`), the
/// pivot in her rest axes (global translation). Pure System.Numerics.</summary>
public static class P1Hinges
{
    /// <summary>The hinge's local rest under its parent: global rest turn none, at the pivot on side `left`.</summary>
    public static (Quaternion Rot, Vector3 Pos) Rest(Quaternion parentRot, Vector3 parentPos, Vector3 leftPivot, bool left) =>
        HipHinge.Rest(parentRot, parentPos, HipHinge.Pivot(leftPivot, left));

    /// <summary>The thigh's line (its +Y) in her rest axes carried with the parent: `chain` is the thigh's rotations
    /// composed down to (not with) the parent.</summary>
    public static Vector3 Line(Quaternion parentRest, Quaternion chain) => Vector3.Transform(Vector3.Transform(Vector3.UnitY, chain), parentRest);

    /// <summary>A hip hinge's local pose from the thigh's chain rotation at rest and now.</summary>
    public static Quaternion Pose(Quaternion rest, Quaternion parentRest, Quaternion chainRest, Quaternion chainNow, double amount) =>
        HipHinge.Pose(rest, Line(parentRest, chainRest), Line(parentRest, chainNow), amount);

    /// <summary>The tasset hinge's local pose from both thighs' (left, right) chain rotations at rest and now.</summary>
    public static Quaternion TassetPose(Quaternion rest, Quaternion parentRest, Quaternion[] chainRest, Quaternion[] chainNow, double amount, double soft)
    {
        var sw = new double[2];
        for (int i = 0; i < 2; i++)
        {
            var v0 = Line(parentRest, chainRest[i]);
            var v = Line(parentRest, chainNow[i]);
            sw[i] = Core.PanelSwing.SwingSpread(v.X, v.Y, v.Z, v0.X, v0.Y, v0.Z, i == 0 ? 1 : -1).Swing;
        }
        return HipHinge.TassetPose(rest, HipHinge.TassetTurn(sw[0], sw[1], amount, soft));
    }
}
