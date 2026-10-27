using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her upper arm's twist chain (Body 5 A2; tools/anim/helpers.py SPEC "twist_chain", its twin): one twist bone a
/// quarter down the arm undoing half the roll left the humerus's turn about its length all in two bands (shear
/// 10.8 deg/cm at reaver_show's +105 roll, the arm pinched to 0.78 of its girth); a chain of four counter-twists
/// (upperarm_twist_01-_04, undoing 0.70, 0.525, 0.35, 0.175 of it) over five weight nodes carries it evenly, and the
/// shoulder's share takes 0.30 of it (the deltoid follows the humerus by 30%). Only on a side whose skeleton has
/// upperarm_twist_02 (View/HerJoints checks): the hero and the NPCs drive as before. The roll is unwrapped frame to
/// frame (<see cref="Unwrap"/>) so a roll through +-180 carries on instead of flipping every counter-twist's sign.
/// Engine-free (System.Numerics); View/HerJoints runs it.
/// </summary>
public static class ArmTwist
{
    /// <summary>d split as swing * twist, the twist about the bone's own +Y: (swing, twist, twist angle in degrees,
    /// -180..180), as helpers._twist_y.</summary>
    public static (Quaternion Swing, Quaternion Twist, float Degrees) TwistY(Quaternion d)
    {
        var t = new Quaternion(0, d.Y, 0, d.W);
        float n = t.Length();
        t = n > 1e-9f ? t * (1f / n) : Quaternion.Identity;
        if (t.W < 0) t = Quaternion.Negate(t);
        float deg = 2 * MathF.Atan2(t.Y, t.W) * 180f / MathF.PI;
        return (d * Quaternion.Conjugate(t), t, deg);
    }

    /// <summary>The upper arm's roll in degrees: its pose's twist about its own +Y from its rest (both local).</summary>
    public static float Roll(Quaternion rest, Quaternion pose) => TwistY(Quaternion.Conjugate(rest) * pose).Degrees;

    /// <summary>The roll <paramref name="deg"/> (-180..180) as the turn nearest <paramref name="last"/> (the last
    /// frame's; NaN at the first): deg or deg +-360 within +-<paramref name="max"/>, as helpers.unwrap_roll.</summary>
    public static float Unwrap(float last, float deg, float max)
    {
        if (float.IsNaN(last)) return deg;
        float best = deg;
        foreach (float c in new[] { deg - 360f, deg + 360f })
            if (MathF.Abs(c) <= max && MathF.Abs(c - last) < MathF.Abs(best - last)) best = c;
        return best;
    }

    /// <summary>A turn of <paramref name="deg"/> degrees about +Y.</summary>
    public static Quaternion AboutY(float deg) => Quaternion.CreateFromAxisAngle(Vector3.UnitY, deg * MathF.PI / 180f);

    /// <summary>A chain bone's local rotation: <paramref name="amount"/> of the roll undone, about its +Y.</summary>
    public static Quaternion Counter(float roll, float amount) => AboutY(-roll * amount);

    /// <summary>As helpers' rig.qslerp: the short way round, a normalised lerp when nearly equal.</summary>
    public static Quaternion Slerp(Quaternion a, Quaternion b, float t)
    {
        float d = Quaternion.Dot(a, b);
        if (d < 0) { b = Quaternion.Negate(b); d = -d; }
        if (d > 0.9995f) return Quaternion.Normalize(a + (b - a) * t);
        float th = MathF.Acos(MathF.Min(1f, d)), s = MathF.Sin(th);
        return a * (MathF.Sin((1 - t) * th) / s) + b * (MathF.Sin(t * th) / s);
    }

    /// <summary>A share bone in a chained arm: <paramref name="amount"/> of its joint's swing (the bone below's pose
    /// against its rest, its own twist left out), turned about its own line by <paramref name="k"/> of the roll:
    /// rest x slerp(swing, amount) x twist_y(roll x k) x own (helpers.drive).</summary>
    public static Quaternion Share(Quaternion rest, Quaternion pose, float amount, Quaternion own, float roll, float k)
    {
        var (swing, _, _) = TwistY(Quaternion.Conjugate(rest) * pose);
        return Quaternion.Normalize(rest * Slerp(Quaternion.Identity, swing, amount) * AboutY(roll * k) * own);
    }
}
