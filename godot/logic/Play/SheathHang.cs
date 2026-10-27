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

    Quaternion mean, now;
    bool started;

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
