using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her scapulae (Body 6 S1; tools/anim/helpers.py SPEC "scap", its twin <c>helpers.scap</c>): a real shoulder girdle
/// rises with the arm mostly by the scapula's upward rotation (39-50 degrees overhead), the clavicle only a little;
/// her clavicle alone carried 34 degrees and the trapezius came up rigid into a corner. Per side, scap_l/scap_r (a
/// child of spine_03, no global rest turn, at the root of the scapula's spine) turns about the scapular plane's
/// normal (<see cref="Axis"/>) by <see cref="Angle"/> of A, the upper arm's angle from her torso's down axis read
/// after the clavicle lift: none at and below <see cref="From"/>, a quadratic over <see cref="Ease"/> degrees (no
/// kink), then <see cref="PerDeg"/> a degree (22.6 at 115, 37.6 at 150, 41.9 at 160; under 1 below 60, so her idles
/// and the Look keep their shoulders). Continuous in A, no keys. Engine-free
/// (System.Numerics, skeleton space); View/HerScap runs it after HerShrug and HerRaise, only where the bones are.
/// </summary>
public static class ScapRotation
{
    public const float PerDeg = 0.43f, From = 50f, Ease = 25f;

    /// <summary>Her left scapula's turning axis in her rest space (game axes): the scapular plane's normal, 35 degrees
    /// off her front toward her midline; a positive turn lifts its outer end.</summary>
    public static readonly Vector3 AxisLeft = new(-0.5736f, 0f, 0.8192f);

    /// <summary>The axis for a side: the right is the left mirrored across her midline, as a turn (x kept, y and z
    /// negated), so the same positive angle lifts it too.</summary>
    public static Vector3 Axis(bool left) => left ? AxisLeft : new Vector3(AxisLeft.X, -AxisLeft.Y, -AxisLeft.Z);

    /// <summary>The scapula's upward rotation in degrees for an upper arm at <paramref name="a"/> degrees.</summary>
    public static float Angle(float a)
    {
        float x = a - From;
        if (x <= 0) return 0;
        return PerDeg * (x < Ease ? x * x / (2 * Ease) : x - Ease / 2);
    }

    /// <summary>The upper arm's angle in degrees from her torso's down axis (unit): 0 hanging, 90 level, 180 overhead.</summary>
    public static float ArmAngle(Vector3 shoulder, Vector3 elbow, Vector3 down)
    {
        var u = elbow - shoulder;
        float n = u.Length();
        if (n < 1e-9f) return 0;
        return MathF.Acos(Math.Clamp(Vector3.Dot(u / n, down), -1f, 1f)) * 180f / MathF.PI;
    }

    /// <summary>The scapula's local pose rotation: its rest (<paramref name="restLocal"/>) times a turn of
    /// <paramref name="deg"/> about <paramref name="axis"/> (rest space) taken into its own rest frame
    /// (<paramref name="globalRest"/> its global rest turn).</summary>
    public static Quaternion Local(Quaternion restLocal, Quaternion globalRest, Vector3 axis, float deg)
    {
        var a = Vector3.Normalize(Vector3.Transform(axis, Quaternion.Conjugate(globalRest)));
        return Quaternion.Normalize(restLocal * Quaternion.CreateFromAxisAngle(a, deg * MathF.PI / 180f));
    }
}
