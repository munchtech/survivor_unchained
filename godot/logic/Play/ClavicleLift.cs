using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her shoulder girdle as an arm rises above level (armor 17 C2): a real clavicle and scapula carry about a third of the
/// raise past 90 degrees, and many clips leave her clavicle at rest (the raised shoulder sat no higher than the resting
/// one: "the arm looks plugged into the chest"). Per side, A = the upper arm's angle from her torso's down axis (pelvis to
/// neck_01; 90 level, 180 overhead): the clavicle's wanted rise above its rest is <see cref="K"/> x (A - 90), eased in
/// over the first <see cref="Ease"/> degrees, none at and below level. The clip's own rise counts (the larger wins, never
/// a sum). The outer end also rolls forward <see cref="Roll"/> of the added rise. The hand stays where the clip put it:
/// the upper and lower arm are re-aimed (two-bone, the elbow in the clip's bend plane) and the hand keeps its world turn;
/// where the lifted shoulder can't reach the hand, the lift is cut back until it can. Engine-free (System.Numerics, all
/// in skeleton space); View/HerShrug runs it before HerRaise. Python's twin: tools/anim/helpers.py shrug.
/// </summary>
public static class ClavicleLift
{
    public const float K = 0.36f, Ease = 8f, Roll = 0.25f, Reach = 0.999f;

    /// <summary>The clavicle's wanted rise in degrees above its rest for an upper arm at <paramref name="a"/> degrees.</summary>
    public static float Target(float a)
    {
        float x = a - 90f;
        if (x <= 0) return 0;
        return K * (x < Ease ? x * x / (2 * Ease) : x - Ease / 2);
    }

    /// <summary>A line's elevation in degrees above the plane square to <paramref name="down"/> (unit).</summary>
    public static float Elevation(Vector3 v, Vector3 down)
    {
        float n = v.Length();
        return n < 1e-9f ? 0 : MathF.Asin(Math.Clamp(-Vector3.Dot(v, down) / n, -1f, 1f)) * 180f / MathF.PI;
    }

    /// <summary>One arm in skeleton space: the clavicle's, shoulder's (upper arm), elbow's (lower arm) and wrist's
    /// (hand) origins and the first three bones' global turns.</summary>
    public struct Arm
    {
        public Vector3 Clavicle, Shoulder, Elbow, Hand;
        public Quaternion ClavicleTurn, UpperTurn, LowerTurn;
    }

    static Quaternion Between(Vector3 a, Vector3 b)
    {
        a = Vector3.Normalize(a); b = Vector3.Normalize(b);
        float d = Vector3.Dot(a, b);
        if (d < -0.999999f)
        {
            var o = Vector3.Cross(Vector3.UnitX, a);
            if (o.Length() < 1e-6f) o = Vector3.Cross(Vector3.UnitY, a);
            return Quaternion.CreateFromAxisAngle(Vector3.Normalize(o), MathF.PI);
        }
        var c = Vector3.Cross(a, b);
        return Quaternion.Normalize(new Quaternion(c.X, c.Y, c.Z, 1 + d));
    }

    static Quaternion Axis(Vector3 axis, float deg) => Quaternion.CreateFromAxisAngle(Vector3.Normalize(axis), deg * MathF.PI / 180f);

    /// <summary>Lifts <paramref name="arm"/> in place (its turns; the hand's world turn is the caller's to keep):
    /// <paramref name="down"/> her torso's down axis, <paramref name="lateral"/> out to this arm's side (square to down),
    /// <paramref name="forward"/> their cross (down x her left), <paramref name="restElevation"/> the clavicle line's
    /// elevation at her rest. Returns (A, the clip's rise, the lift added) in degrees; the lift is 0 when nothing moved.</summary>
    public static (float A, float Rise, float Lift) Apply(ref Arm arm, Vector3 down, Vector3 lateral, Vector3 forward, float restElevation)
    {
        Vector3 pc = arm.Clavicle, s = arm.Shoulder, e = arm.Elbow, h = arm.Hand;
        var su = Vector3.Normalize(e - s);
        float a = MathF.Acos(Math.Clamp(Vector3.Dot(su, down), -1f, 1f)) * 180f / MathF.PI;
        float rise = Elevation(s - pc, down) - restElevation;
        float t = Target(a);
        float d = Math.Min(t, Math.Max(0f, t - rise));
        if (d < 1e-4f) return (a, rise, 0f);
        var upAx = Vector3.Cross(down, lateral);        // its outer end up
        var rollAx = Vector3.Cross(lateral, forward);   // its outer end forward
        float l1 = (e - s).Length(), l2 = (h - e).Length(), reach = Reach * (l1 + l2);
        Quaternion Q(float k) => Axis(rollAx, Roll * k) * Axis(upAx, k);
        Vector3 Lifted(float k) => pc + Vector3.Transform(s - pc, Q(k));
        if ((h - Lifted(d)).Length() > reach)
        {
            float lo = 0f, hi = d;
            for (int i = 0; i < 20; i++)
            {
                float m = 0.5f * (lo + hi);
                if ((h - Lifted(m)).Length() > reach) hi = m; else lo = m;
            }
            d = lo;
        }
        var q = Q(d);
        var s2 = Lifted(d);
        var dv = h - s2;
        float dl = dv.Length();
        var ax = dv / dl;
        var pole = (e - s) - Vector3.Dot(e - s, ax) * ax;   // the clip's bend plane
        if (pole.Length() < 1e-6f)
        {
            var r = Vector3.Transform(e - s, q);
            pole = r - Vector3.Dot(r, ax) * ax;
        }
        pole = Vector3.Normalize(pole);
        float ca = Math.Clamp((l1 * l1 + dl * dl - l2 * l2) / (2 * l1 * dl), -1f, 1f);
        var e2 = s2 + l1 * (ca * ax + MathF.Sqrt(1 - ca * ca) * pole);
        arm.ClavicleTurn = Quaternion.Normalize(q * arm.ClavicleTurn);
        arm.UpperTurn = Quaternion.Normalize(Between(e - s, e2 - s2) * arm.UpperTurn);
        arm.LowerTurn = Quaternion.Normalize(Between(h - e, h - e2) * arm.LowerTurn);
        arm.Shoulder = s2;
        arm.Elbow = e2;
        return (a, rise, d);
    }
}
