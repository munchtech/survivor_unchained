using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>Her hip hinges (tools/anim/helpers.py SPEC "hinges", drive_hinges; armor-D 16 Nov): one bone per side
/// for ARMOR only, a child of the pelvis at a belt-line pivot, its global rest turn none, turned `amount` of the
/// thigh's swing (the arc from the thigh's rest line to its posed line, both in her rest axes carried with the pelvis:
/// flexion and spread, never its roll). A belt plate rides it rigidly: on the belt, over the thigh. HerJoints adds the
/// bones (AddHinges) and drives them with this. The tasset hinge (SPEC "tassets") is one centred bone at the belt's
/// front V's top, turned with the leading thigh (TassetTurn), so a long V rides it rigidly off the thigh.</summary>
public static class HipHinge
{
    /// <summary>The pivot on side `left` (the spec gives her left; the right mirrored in x).</summary>
    public static Vector3 Pivot(Vector3 leftPivot, bool left) => left ? leftPivot : new Vector3(-leftPivot.X, leftPivot.Y, leftPivot.Z);

    /// <summary>The hinge's local rest under its parent (global rest turn `parentRot` at `parentPos`): its global turn
    /// none, at `pivot` (helpers.hinge_rest).</summary>
    public static (Quaternion Rot, Vector3 Pos) Rest(Quaternion parentRot, Vector3 parentPos, Vector3 pivot)
    {
        var inv = Quaternion.Inverse(parentRot);
        return (inv, Vector3.Transform(pivot - parentPos, inv));
    }

    /// <summary>`amount` of the arc from v0 to v, about the arc's own axis (helpers.hinge_turn_q).</summary>
    public static Quaternion Turn(Vector3 v0, Vector3 v, double amount)
    {
        var a = Vector3.Normalize(v0);
        var b = Vector3.Normalize(v);
        var c = Vector3.Cross(a, b);
        double sn = c.Length(), cs = Math.Clamp(Vector3.Dot(a, b), -1f, 1f);
        if (sn < 1e-9) return Quaternion.Identity;
        return Quaternion.CreateFromAxisAngle(c / (float)sn, (float)(Math.Atan2(sn, cs) * amount));
    }

    /// <summary>The hinge's local pose: its rest, then the turn (helpers.drive_hinges: rest x turn).</summary>
    public static Quaternion Pose(Quaternion rest, Vector3 v0, Vector3 v, double amount) =>
        Quaternion.Normalize(rest * Turn(v0, v, amount));

    /// <summary>Degrees the tasset hinge turns (helpers.py SPEC "tassets", tasset_turn): its V's bottom forward and up by
    /// `amount` of the leading thigh's forward swing (fl, fr: degrees from rest, Core.PanelSwing.SwingSpread), smoothly:
    /// amount * softrelu(smooth max(fl, fr) - soft/4).</summary>
    public static double TassetTurn(double fl, double fr, double amount, double soft) =>
        amount * Core.PanelSwing.SoftRelu(Core.PanelSwing.SmoothMax(fl, fr, soft) - soft / 4, soft);

    /// <summary>The tasset hinge's local pose: its rest (Rest: global rest turn none, at its pivot), then `deg` about her
    /// lateral axis, the bottom forward (about -X: her -Y toward +Z; helpers.drive_tassets: rest x turn).</summary>
    public static Quaternion TassetPose(Quaternion rest, double deg) =>
        Quaternion.Normalize(rest * Quaternion.CreateFromAxisAngle(new Vector3(-1, 0, 0), (float)(deg * Math.PI / 180)));
}
