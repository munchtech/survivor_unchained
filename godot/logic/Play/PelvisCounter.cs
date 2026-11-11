using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// The pelvis counter's math (A1 motion lead 19; View/PelvisCounter runs it). Her upper layer (a swing's `_run` clip on
/// everything above the hips) is authored over the walk's MEAN pelvis M, but the walk's own pelvis Ph turns up to 8.65
/// degrees away from M through the cycle and the layer's local rotations ride on it: the blade swung 15-19 cm off its
/// path. The counter turns spine_01 by D so the layer rides M instead of Ph, in mesh space (her root node's frame).
/// E = M * Ph^-1 is split into a twist about the root's up (+Y, the yaw: the walk's own sway, which carries her chest
/// and is kept at once) and the remaining swing; E' = twist * slerp(I, swing, K); E'' = slerp(I, E', w) with w the upper
/// shot's blend weight; D = Ph^-1 * E'' * Ph, so spine_01's global = E'' * Ph * L. K = 1 and w = 1 give M * L exactly.
/// Engine-free (System.Numerics, Hamilton products as Godot's Quaternion).
/// </summary>
public static class PelvisCounter
{
    /// <summary>How much of the swing (the non-yaw part of the pelvis's turn from its mean) is countered. A full counter
    /// (1) holds her chest dead square to the mean and reads stiff over a walk that tips the hips; half keeps the gait's
    /// own roll and pitch visible while taking the blade's error out of both halves.</summary>
    /// <remarks>The shoot harness may set it (--pelvis-k, A1 lead 19's K look); play keeps 0.5.</remarks>
    public static float K = 0.5f;

    /// <summary>The correction E'' = slerp(I, twist * slerp(I, swing, k), w), in mesh space.</summary>
    public static Quaternion Correction(Quaternion mean, Quaternion pelvis, float k, float w)
    {
        var e = Quaternion.Normalize(mean * Quaternion.Inverse(Quaternion.Normalize(pelvis)));
        if (e.W < 0) e = Quaternion.Negate(e);
        // E = twist * swing: the twist about +Y is the conjugate of the +Y part of E^-1 (E^-1 = swing^-1 * twist^-1).
        var inv = Quaternion.Conjugate(e);
        var t = new Quaternion(0, inv.Y, 0, inv.W);
        float n = t.Length();
        t = n > 1e-9f ? t * (1f / n) : Quaternion.Identity;
        var twist = Quaternion.Conjugate(t);
        var swing = Quaternion.Normalize(Quaternion.Conjugate(twist) * e);
        var ek = twist * Quaternion.Slerp(Quaternion.Identity, swing, k);
        return Quaternion.Normalize(Quaternion.Slerp(Quaternion.Identity, ek, Math.Clamp(w, 0f, 1f)));
    }

    /// <summary>spine_01's LOCAL rotation after the counter: D * L, D = Ph^-1 * E'' * Ph.</summary>
    public static Quaternion Apply(Quaternion mean, Quaternion pelvis, Quaternion spineLocal, float k, float w)
    {
        var ph = Quaternion.Normalize(pelvis);
        var d = Quaternion.Inverse(ph) * Correction(mean, ph, k, w) * ph;
        return Quaternion.Normalize(d * spineLocal);
    }

    /// <summary>The one-shot's blend weight from the upper clip's position: its fade in (from the start) and its fade out
    /// (to the end), both in seconds of play; a request to fade out early is `released` seconds ago (-1 for none).</summary>
    public static float Weight(double played, double remaining, double fadeIn, double fadeOut, double released, double releaseFade)
    {
        double w = 1;
        if (fadeIn > 1e-6) w = Math.Min(w, played / fadeIn);
        if (fadeOut > 1e-6) w = Math.Min(w, remaining / fadeOut);
        if (released >= 0) w = Math.Min(w, releaseFade > 1e-6 ? 1 - released / releaseFade : 0);
        return (float)Math.Clamp(w, 0, 1);
    }

    /// <summary>A clip's `pelvis_mean` meta [x, y, z, w] as a quaternion, or null when it is not four numbers.</summary>
    public static Quaternion? Mean(double[]? v) =>
        v is { Length: 4 } && (v[0] != 0 || v[1] != 0 || v[2] != 0 || v[3] != 0) ? Quaternion.Normalize(new Quaternion((float)v[0], (float)v[1], (float)v[2], (float)v[3])) : null;
}
