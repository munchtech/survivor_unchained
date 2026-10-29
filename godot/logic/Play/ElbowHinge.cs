using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her elbow share's half-bend about its own hinge (Body 14; tools/anim/helpers.py hinge_part, its twin). The forearm's
/// swing against its rest runs about the shortest arc, which is off the hinge wherever the joint carries an angle
/// (her elbow's ~16 deg: 23 deg off at 90, 64 at 145), and half of it swung the flesh above the elbow sideways. The
/// share (and its point) in the spec with "hinge": true take instead <c>amount</c> of the angle about the hinge (the
/// share's X, carried into the bone below's rest frame by <c>own</c>) that takes the bone's line to its posed line,
/// both seen along the hinge. Engine-free (System.Numerics); View/HerJoints runs it.
/// </summary>
public static class ElbowHinge
{
    /// <summary><paramref name="amount"/> of the joint's bend about the hinge, as a rotation in the bone-below's rest
    /// frame (helpers.hinge_part).</summary>
    public static Quaternion HingePart(Quaternion swing, Quaternion own, float amount)
    {
        var a = Vector3.Transform(Vector3.UnitX, own);
        var y1 = Vector3.Transform(Vector3.UnitY, swing);
        var p0 = Vector3.UnitY - a * a.Y;
        var p1 = y1 - a * Vector3.Dot(a, y1);
        double ang = Math.Atan2(Vector3.Dot(Vector3.Cross(p0, p1), a), Vector3.Dot(p0, p1));
        return Quaternion.CreateFromAxisAngle(a, (float)ang * amount);
    }

    /// <summary>A hinged share bone's local rotation: rest x hinge_part(swing) x own, the swing being the bone below's
    /// pose against its rest with its own twist left out (helpers.drive).</summary>
    public static Quaternion Share(Quaternion rest, Quaternion pose, float amount, Quaternion own)
    {
        var (swing, _, _) = ArmTwist.TwistY(Quaternion.Conjugate(rest) * pose);
        return Quaternion.Normalize(rest * HingePart(swing, own, amount) * own);
    }
}
