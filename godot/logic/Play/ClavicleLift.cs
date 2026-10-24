using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her shoulder girdle as an arm rises (armor 17 C2; body5 lift): a real clavicle and scapula carry the raise with the
/// arm (scapulohumeral rhythm, about 2:1 glenohumeral to scapular), and many clips leave her clavicle at rest (the raised
/// arm plugged into a flat shoulder shelf at a V: "a doll's ball joint"). Per side, A = the upper arm's angle from her
/// torso's down axis (pelvis to neck_01; 90 level, 180 overhead): the clavicle's wanted rise above its rest is
/// <see cref="Max"/> x smoothstep((A - <see cref="From"/>) / (<see cref="To"/> - <see cref="From"/>)): nothing at and
/// below 60 (her idles, the Look and the town untouched), eased in, 5 at level, 15 at 115, 25 at 140, easing out to 34
/// overhead. The clip's own rise counts (the larger wins, never a sum). The outer end also rolls forward
/// <see cref="Roll"/> of the added rise. The hand stays where the clip put it: the upper and lower arm are re-aimed
/// (two-bone, the elbow in the clip's bend plane) and the hand keeps its world turn; where the lifted shoulder can't
/// reach the hand, the lift is cut back until it can. Engine-free (System.Numerics, all in skeleton space);
/// View/HerShrug runs it before HerRaise. Python's twin: tools/anim/helpers.py shrug.
/// </summary>
public static class ClavicleLift
{
    public const float Max = 34f, From = 60f, To = 180f, Roll = 0.25f, Reach = 0.999f;

    /// <summary>On a body with her scapula helpers (Body 6 S1; helpers SPEC "scap", View/HerScap): the scapula carries
    /// most of the girdle's rise, so the clavicle's is <see cref="ScapMax"/> overhead (2 at level, 9.6 at 140) and its
    /// outer end turns back (<see cref="ScapRoll"/> of it, about 8 overhead).</summary>
    public const float ScapMax = 13f, ScapRoll = -0.6f;

    /// <summary>The clavicle's wanted rise in degrees above its rest for an upper arm at <paramref name="a"/> degrees
    /// (<paramref name="scap"/>: a body with her scapula helpers).</summary>
    public static float Target(float a, bool scap = false)
    {
        float x = (a - From) / (To - From);
        if (x <= 0) return 0;
        x = Math.Min(x, 1f);
        return (scap ? ScapMax : Max) * x * x * (3 - 2 * x);
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
    public static (float A, float Rise, float Lift) Apply(ref Arm arm, Vector3 down, Vector3 lateral, Vector3 forward, float restElevation, bool scap = false)
    {
        Vector3 pc = arm.Clavicle, s = arm.Shoulder, e = arm.Elbow, h = arm.Hand;
        var su = Vector3.Normalize(e - s);
        float a = MathF.Acos(Math.Clamp(Vector3.Dot(su, down), -1f, 1f)) * 180f / MathF.PI;
        float rise = Elevation(s - pc, down) - restElevation;
        float t = Target(a, scap);
        float roll = scap ? ScapRoll : Roll;
        float d = Math.Min(t, Math.Max(0f, t - rise));
        if (d < 1e-4f) return (a, rise, 0f);
        var upAx = Vector3.Cross(down, lateral);        // its outer end up
        var rollAx = Vector3.Cross(lateral, forward);   // its outer end forward
        float l1 = (e - s).Length(), l2 = (h - e).Length(), reach = Reach * (l1 + l2);
        Quaternion Q(float k) => Axis(rollAx, roll * k) * Axis(upAx, k);
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
