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

    /// <summary>A tasset hinge's local pose (HerJoints' drive): from the chain rotations (at rest, now) of the thigh(s) it
    /// reads (`sides`: +1 her left, -1 her right, from each thigh's name). Two thighs: the V turned with the leading one and
    /// rolled away from one crossing the midline (HipHinge.TassetRoll); one thigh (a hip tasset): its own swing, no roll.</summary>
    public static Quaternion TassetPose(Quaternion rest, Quaternion parentRest, Quaternion[] chainRest, Quaternion[] chainNow, int[] sides,
        double amount, double soft, double roll = 0, double rollFrom = 2, double rollSoft = 6, double rollMax = 20)
    {
        int n = chainRest.Length;
        var sw = new double[n];
        var sp = new double[n];
        for (int i = 0; i < n; i++)
        {
            var v0 = Line(parentRest, chainRest[i]);
            var v = Line(parentRest, chainNow[i]);
            (sw[i], sp[i]) = Core.PanelSwing.SwingSpread(v.X, v.Y, v.Z, v0.X, v0.Y, v0.Z, sides[i]);
        }
        double turn = n == 2 ? HipHinge.TassetTurn(sw[0], sw[1], amount, soft) : HipHinge.TassetTurnOne(sw[0], amount, soft);
        double r = n == 2 ? HipHinge.TassetRoll(sp[0], sp[1], roll, rollFrom, rollSoft, rollMax) : 0;
        return HipHinge.TassetPose(rest, turn, r);
    }
}
