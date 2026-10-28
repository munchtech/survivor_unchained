using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her elbow's pose-space shapes' drive (Body 19; tools/assets/elbow_psd_post.py authors elbow_psd45/90/135_{l,r};
/// tools/anim/helpers.py flexion and corrective_weight are the twins). A corrective with "on": "flex" is keyed on the
/// joint's FLEXION, not its whole swing: the bone's line seen along its own X (the hinge her clips bend about), from
/// rest toward her front. Her clips' small "bends" are mostly the forearm swung sideways onto the humerus' line, which
/// folds no crease. "keys" [lo, at, hi] make it an in-between: 0 at lo and below, linear to 1 at `at`, linear to 0 at
/// hi (hi &lt;= at: held at 1 past `at`). Engine-free; View/HerJoints runs it.
/// </summary>
public static class ElbowPsd
{
    /// <summary>Degrees the joint above a bone is flexed, from its local rest and pose rotations.</summary>
    public static float Flexion(Quaternion rest, Quaternion pose)
    {
        var d = Vector3.Transform(Vector3.UnitY, Quaternion.Conjugate(rest) * pose);
        return MathF.Atan2(d.Z, d.Y) * 180f / MathF.PI;
    }

    /// <summary>An in-between's weight at <paramref name="deg"/>.</summary>
    public static float Weight(float lo, float at, float hi, float deg)
    {
        if (deg <= lo) return 0f;
        if (deg < at) return (deg - lo) / (at - lo);
        if (hi <= at) return 1f;
        return MathF.Max(0f, 1f - (deg - at) / (hi - at));
    }
}
