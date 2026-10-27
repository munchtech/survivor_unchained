using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// A sheathed piece HUNG from her belt (Body 16): a scabbard or an axe in its loop moves like a hung weight, not bolted
/// to her pelvis. Her town walk rolls the pelvis about 13 degrees each way and turns it 10-14; a piece riding the bone
/// rigidly flapped out about 20 degrees (the warden's sword 37 peak to peak out from her leg, the reaver's axe 22).
/// Hung, the piece keeps its pivot on the belt exactly (the mount follows the bone) and only its turn is eased: the
/// pelvis's turn from its rest in skeleton space (her facing frame; turning her whole body is never lagged), D, is
/// split into its slow mean (low-passed over <see cref="Settle"/> s, so a stance held or a lean kept is followed in
/// full and the idles and holds look as they did) and the swing about it, of which <see cref="Keep"/> is kept; the
/// result is low-passed again over <see cref="Lag"/> s, the small trailing sway of a weight. Walk: the sword 37 -> 6
/// degrees peak to peak, the axe 22 -> 3, and both clear of her skin. Engine-free (System.Numerics);
/// View/SheathSway runs it per mount. Python's twin: tools/scratch/body16/hang.py.
/// </summary>
public sealed class SheathHang
{
    /// <summary>The share of the pelvis's swing about its slow mean the piece keeps.</summary>
    public const float Keep = 0.2f;

    /// <summary>The piece's trailing lag (s): the time constant it eases toward its target with.</summary>
    public const float Lag = 0.2f;

    /// <summary>The mean's time constant (s): longer than a stride, so the stride's roll is swing, not mean.</summary>
    public const float Settle = 1.5f;

    /// <summary>The time (s) the hang eases in or out over when the clip turns to or from one whose hand holds the
    /// hilt, so the piece never pops.</summary>
    public const float Blend = 0.2f;

    /// <summary>Clips where her hand HOLDS the hilt of a hung piece (Body 17, 27 Oct): hung there, the scabbard swings
    /// into the hand that holds it (the warden's sword, run 10.0 mm and sprint 11.6 into her left hand), so in these the
    /// piece rides the pelvis rigidly (weight 0). Names without a library prefix ("her/", "folk/", "npc:x/").</summary>
    public static readonly string[] HiltHeld = ["run_warden_town", "sprint_warden_town"];

    /// <summary>Whether <paramref name="clip"/> (as an AnimationPlayer names it, any library prefix kept or not) is one
    /// whose hand holds the hilt.</summary>
    public static bool HoldsHilt(string? clip)
    {
        if (string.IsNullOrEmpty(clip)) return false;
        int cut = clip.LastIndexOfAny(['/', ':']);
        var bare = cut >= 0 ? clip[(cut + 1)..] : clip;
        return Array.IndexOf(HiltHeld, bare) >= 0;
    }

    Quaternion mean, now;
    bool started;
    float w = 1;

    /// <summary>The share of the hang applied now (0: riding the pelvis rigidly, 1: hung), eased over
    /// <see cref="Blend"/> s toward 0 while the clip holds the hilt and 1 otherwise.</summary>
    public float Weight => w * w * (3f - 2f * w);

    /// <summary>As <see cref="Step(Quaternion, float)"/>, scaled by the per-clip weight: <paramref name="rigid"/> (the
    /// clip holds the hilt) eases the hang out, else in. The hang itself keeps running beneath, so easing back in is
    /// smooth. The first call takes the weight as it is.</summary>
    public Quaternion Step(Quaternion d, float dt, bool rigid)
    {
        float wTarget = rigid ? 0f : 1f;
        float stepW = Math.Clamp(dt, 0f, 0.25f) / Blend;
        w = !started ? wTarget : Math.Clamp(w + Math.Clamp(wTarget - w, -stepW, stepW), 0f, 1f);
        var hung = Step(d, dt);
        var k = Weight;
        return k >= 1f ? hung : Quaternion.Normalize(Quaternion.Slerp(Quaternion.Normalize(d), hung, k));
    }

    /// <summary>The turn the piece takes this frame (as the pelvis's own, from its rest in skeleton space) for the
    /// pelvis's turn <paramref name="d"/>, <paramref name="dt"/> seconds after the last. The first call (or after
    /// <see cref="Reset"/>) takes d as it is.</summary>
    public Quaternion Step(Quaternion d, float dt)
    {
        d = Quaternion.Normalize(d);
        if (!started || float.IsNaN(now.W))
        {
            mean = now = d;
            started = true;
            return d;
        }
        dt = Math.Clamp(dt, 0f, 0.25f);
        mean = Ease(mean, d, dt, Settle);
        var target = Quaternion.Slerp(mean, d, Keep);
        now = Ease(now, target, dt, Lag);
        return now;
    }

    /// <summary>Start again from the next pose (a new mount, a cut).</summary>
    public void Reset() => started = false;

    static Quaternion Ease(Quaternion from, Quaternion to, float dt, float tau) =>
        Quaternion.Normalize(Quaternion.Slerp(from, to, 1f - MathF.Exp(-dt / tau)));
}
