using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>Where her right fist grips the piece (animation 47): a clip may slide it along its shaft, and (animation 48)
/// tilt it in her fist about the palm's normal (the combat arcanist idle holds the staff nearer a square grip, so her
/// forearm slopes down to the fist with the staff upright). Which clip's value counts, the ease between them (the same
/// for the slide and the tilt), and where the piece then sits in its mount.</summary>
public static class GripSlide
{
    /// <summary>The slide wanted now: a whole-body one-shot's, else an upper-body one's, else the idle/run pair's by the move blend.</summary>
    public static float Target(bool fullOn, float fullS, bool upperOn, float upperS, float moveBlend, float idleS, float runS)
        => fullOn ? fullS : upperOn ? upperS : idleS + (runS - idleS) * Math.Clamp(moveBlend, 0f, 1f);

    /// <summary>As above, with the walk between idle and run: idle -> walk by `walkBlend`, then that -> run by `runBlend` (the move graph's order).</summary>
    public static float Target(bool fullOn, float fullS, bool upperOn, float upperS, float walkBlend, float runBlend, float idleS, float walkS, float runS)
    {
        if (fullOn) return fullS;
        if (upperOn) return upperS;
        float iw = idleS + (walkS - idleS) * Math.Clamp(walkBlend, 0f, 1f);
        return iw + (runS - iw) * Math.Clamp(runBlend, 0f, 1f);
    }

    /// <summary>Current eased toward target over dt seconds.</summary>
    public static float Ease(float current, float target, float dt, float rate = 12f)
        => current + (target - current) * (1f - MathF.Exp(-rate * dt));

    /// <summary>A seat part way between two (animation 58: the second axe eased from its plain mount onto the left tilt's
    /// pocket by `w`, 0 the first, 1 the second): the origin lerped, the turn slerped.</summary>
    public static (Quaternion Turn, Vector3 At) Blend(Quaternion a, Vector3 aAt, Quaternion b, Vector3 bAt, float w)
    {
        w = Math.Clamp(w, 0f, 1f);
        if (w == 0f) return (a, aAt);
        if (w == 1f) return (b, bAt);
        return (Quaternion.Normalize(Quaternion.Slerp(a, b, w)), Vector3.Lerp(aAt, bAt, w));
    }

    /// <summary>A seated piece moved by a clip's grip, in its mount's space: turned `tiltDeg` about `axis` (the hand's
    /// palm normal, hand +X) through `pivot` (the fist's fitted pocket, where the seat lays the piece's grip point),
    /// then slid `metres` along its own turned +Y (`seatUp`: the seat's +Y, unit). Returns the turn to set before the
    /// seat's basis and the piece's new origin (`seatAt`: the seat's origin). 0 and 0 leave the seat as it is.
    /// (tools/anim/keyed.py grip_pose is the same move for the clips' tools.)</summary>
    public static (Quaternion Turn, Vector3 At) Apply(Vector3 seatAt, Vector3 seatUp, Vector3 pivot, Vector3 axis, float tiltDeg, float metres)
    {
        var turn = tiltDeg == 0f ? Quaternion.Identity
            : Quaternion.CreateFromAxisAngle(Vector3.Normalize(axis), tiltDeg * MathF.PI / 180f);
        var at = pivot + Vector3.Transform(seatAt - pivot, turn) + Vector3.Transform(seatUp, turn) * metres;
        return (turn, at);
    }
}
