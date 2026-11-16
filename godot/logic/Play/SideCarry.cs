using System;

namespace SurvivorUnchained.Play;

/// <summary>(warden-move, max judge r3 option c) The side carry: a layer over a held piece's grip for when the hand that
/// holds it faces the camera. At the den's steep camera (pitch 62) a long piece carried along her side reads as a cane, a
/// short still bar near vertical: the front carry that passes toward and away from the camera cannot also pass side-on
/// (projection), and her wrist is at its cap. So with the holding side to the camera the piece is turned in her fist
/// about the grip's tilt axis (the palm's normal, through the fitted pocket: PersonView.Slide's tilt): tipped back by
/// <see cref="Rest"/>, and loosened in the fist by a spring the fist's own swing drives (the blade's inertia: the fist
/// pulled forward leaves the tip behind), so the blade's angle swings each stride a few frames after the fist and trails
/// it. Its weight is the holding side's facing to the camera, squared (none with the piece on the far side, nor facing
/// toward or away), eased over <see cref="Ease"/> seconds; with no weight the grip is exactly the clips'. The added tilt
/// changes at most <see cref="MaxRate"/> degrees a second, so a fast turn never flicks the blade across the screen.
/// Pure (no Godot): PlayerView feeds it each drawn pose and adds <see cref="Tilt"/> to the clip's grip tilt.</summary>
public sealed class SideCarry
{
    /// <summary>The tip-back the piece is turned at full weight (deg, + = tip behind her travel).</summary>
    public float Rest = 27f;
    /// <summary>The loosening per m/s² of the grip's acceleration along her travel (deg; forward pull, tip back).</summary>
    public float Gain = 0.65f;
    /// <summary>The loosening spring's natural frequency (Hz) and damping ratio.</summary>
    public float Hz = 2f, Damping = 0.8f;
    /// <summary>How far the piece may loosen in the fist, tip back (deg), and tip forward (deg: less, so a stop's swing
    /// forward never stands the blade straight down).</summary>
    public float Loose = 15f, LooseFwd = 6f;
    /// <summary>The largest acceleration the spring takes (m/s²): the arm's swing is about 20; a stop or a start, more, is cut to it.</summary>
    public float MaxAccel = 24f;
    /// <summary>The weight's ease, a time constant (s).</summary>
    public float Ease = 0.1f;
    /// <summary>The fastest the added tilt may change (deg/s; 150 is 5 a frame at 30 fps).</summary>
    public float MaxRate = 150f;
    /// <summary>The tip turned in toward her body at full weight (deg; trims the blade's splay out from her side).</summary>
    public float Splay = 3f;

    /// <summary>The eased weight (0..1).</summary>
    public float Weight { get; private set; }
    /// <summary>The loosening now (deg, before the weight; + = tip back).</summary>
    public float Spring { get; private set; }
    /// <summary>The tilt the layer adds now (deg, + = tip back): Weight * (Rest + Spring), rate-limited.</summary>
    public float Tilt { get; private set; }
    /// <summary>The turn in toward her body it adds now (deg): Weight * Splay.</summary>
    public float Inward => Weight * Splay;
    float springV;

    /// <summary>The weight wanted for a side facing: `side` is the cosine between the holding hand's side (out from her,
    /// level) and the way back to the camera (level): 1 that side squarely to the camera, 0 or less facing toward, away or
    /// with the piece on the far side (no weight).</summary>
    public static float Target(float side) => side <= 0f ? 0f : MathF.Min(1f, side * side);

    /// <summary>`side` for a figure turned `faceRad` about up (Godot's yaw: she faces +Z at 0) with the camera's back (its
    /// basis Z, level) along `camBackX`, `camBackZ`, the piece in her right hand (`right`) or left. Her right is -X at yaw 0.</summary>
    public static float Side(float faceRad, float camBackX, float camBackZ, bool right = true)
    {
        float len = MathF.Sqrt(camBackX * camBackX + camBackZ * camBackZ);
        if (len < 1e-6f) return 0f;
        float sx = -MathF.Cos(faceRad), sz = MathF.Sin(faceRad);
        if (!right) { sx = -sx; sz = -sz; }
        return (sx * camBackX + sz * camBackZ) / len;
    }

    /// <summary>Back to no weight and no tilt, the spring at rest (a new body, a cut).</summary>
    public void Reset() { Weight = 0f; Spring = 0f; springV = 0f; Tilt = 0f; }

    /// <summary>One step of `dt` seconds: the weight eased toward `target`, the spring driven by the grip's acceleration
    /// `accel` along her travel (m/s², + forward), the tilt moved toward Weight * (Rest + Spring) at most MaxRate.</summary>
    public void Step(float dt, float target, float accel)
    {
        if (!(dt > 0f)) return;
        target = Math.Clamp(target, 0f, 1f);
        Weight = Ease > 0f ? Weight + (target - Weight) * (1f - MathF.Exp(-dt / Ease)) : target;
        if (Weight < 1e-4f && target == 0f) Weight = 0f;
        // The loosening: a damped spring toward 0, pushed tip-back by a forward pull (fixed sub-steps for any frame rate).
        float k = MathF.Pow(2f * MathF.PI * Hz, 2f), c = 2f * Damping * 2f * MathF.PI * Hz;
        int n = Math.Max(1, (int)MathF.Ceiling(dt / (1f / 240f)));
        float h = dt / n, drive = k * Gain * Math.Clamp(float.IsFinite(accel) ? accel : 0f, -MaxAccel, MaxAccel);
        for (int i = 0; i < n; i++)
        {
            float a = drive - k * Spring - c * springV;
            springV += a * h;
            Spring += springV * h;
            if (Spring > Loose) { Spring = Loose; if (springV > 0f) springV = 0f; }
            if (Spring < -LooseFwd) { Spring = -LooseFwd; if (springV < 0f) springV = 0f; }
        }
        float want = Weight * (Rest + Spring);
        if (Weight == 0f) want = 0f;
        float step = MaxRate * dt;
        Tilt = Tilt + Math.Clamp(want - Tilt, -step, step);
        if (Weight == 0f && MathF.Abs(Tilt) < 1e-3f) Tilt = 0f;
    }
}
