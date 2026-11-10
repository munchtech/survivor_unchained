using System;

namespace SurvivorUnchained.View;

/// <summary>Where a damage number may start, the part with no Godot in it (the tests compile it). M4 lead 6: a number's
/// first 0.3 s is never inside the strap under her (her life and dash pips, HerLight.Under): a crit "188" started half
/// behind it and read "88".</summary>
public static class HitsPlace
{
    /// <summary>A number's life (s) and how fast it lifts at its birth (m/s, easing to nothing over its life): Hits._Process.</summary>
    public const double Life = 0.75, Lift = 1.4;
    /// <summary>The seconds of a number's life kept clear of the strap, and the gap kept between them (px at 1080).</summary>
    public const double Young = 0.3;
    public const float StrapGap = 6;

    /// <summary>(fix E, 3) A damage number's font size, one rule: a normal blow 46, a heavy one (a fifth of its target) +12, so
    /// no normal number passes NormalMost = 58; a crit starts at 80 (1.38 x that), +12 when heavy. At the same depth a crit is
    /// therefore never under 1.35 x the largest normal. (Before: crit 72 against a heavy normal's 58 = 1.24, and a crit's
    /// 1.35 punch scale lasts only the first 0.08 s, so a frame shot later showed the font sizes alone.)</summary>
    public const int NormalSize = 46, HeavyAdd = 12, NormalMost = NormalSize + HeavyAdd, CritSize = 80;
    public const float CritOverNormal = 1.35f;
    public static int NumberSize(bool crit, bool heavy) => (crit ? CritSize : NormalSize) + (heavy ? HeavyAdd : 0);

    /// <summary>How far a number has lifted (m) `secs` into its life: the integral of Lift x (1 - t / Life).</summary>
    public static double RiseIn(double secs)
    {
        double s = Math.Clamp(secs, 0, Life);
        return Lift * (s - s * s / (2 * Life));
    }

    /// <summary>How far sideways (px; 0: it stays) a number's box (x0..x1, y0..y1 on screen, y down) is moved so that
    /// neither it nor the `rise` px above it (where it lifts to in its first Young seconds) touches the strap's rect
    /// (sx0..sx1, sy0..sy1) grown by `gap`: to the side its middle is already on (the right when dead centre: a number
    /// is lifted to the right of its impact), so it stays beside the blow. Never up (her legs are there) or down.</summary>
    public static float StrapNudge(float x0, float y0, float x1, float y1, float rise, float sx0, float sy0, float sx1, float sy1, float gap = StrapGap)
    {
        float top = y0 - Math.Max(0, rise);
        if (x1 <= sx0 - gap || x0 >= sx1 + gap || y1 <= sy0 - gap || top >= sy1 + gap) return 0;
        return (x0 + x1) / 2 < (sx0 + sx1) / 2 ? sx0 - gap - x1 : sx1 + gap - x0;
    }

    /// <summary>A rect on screen (px, y down).</summary>
    public readonly record struct Box(float X0, float Y0, float X1, float Y1);

    /// <summary>The gap kept between a number and her body (px at 1080).</summary>
    public const float BodyGap = 4;
    /// <summary>HerNudge's `hit`: which of her rects the number was on (or would lift into).</summary>
    public const int HitBody = 1, HitStrap = 2;

    /// <summary>How far sideways (px; 0: it stays) a number's box is moved so that neither it nor the `rise` px above it
    /// (its first Young seconds) touches her body's rect grown by bodyGap or the strap's under her grown by strapGap
    /// (either may be null: not on screen). Always to the side its middle is on of HER centre line `herX` (the right
    /// when dead centre), so the numbers born on her stand in two lanes beside her; the result is clear of both rects
    /// at once (the strap is wider than she is: a number moved off her body is moved on past the strap when it would
    /// land there). Never up or down. `hit`: HitBody | HitStrap, the rects it was moved off.</summary>
    public static float HerNudge(Box num, float rise, float herX, Box? body, Box? strap, out int hit, float bodyGap = BodyGap, float strapGap = StrapGap)
    {
        hit = 0;
        bool right = (num.X0 + num.X1) / 2 >= herX;
        float top = num.Y0 - Math.Max(0, rise), dx = 0;
        // (each push goes the same way, so the second pass only confirms the first: two rects, two passes)
        for (int pass = 0; pass < 2; pass++)
        {
            if (body is Box b && On(b, bodyGap)) { hit |= HitBody; dx = right ? b.X1 + bodyGap - num.X0 : b.X0 - bodyGap - num.X1; }
            if (strap is Box s && On(s, strapGap)) { hit |= HitStrap; dx = right ? s.X1 + strapGap - num.X0 : s.X0 - strapGap - num.X1; }
        }
        return dx;

        bool On(Box r, float gap) => !(num.X1 + dx <= r.X0 - gap || num.X0 + dx >= r.X1 + gap || num.Y1 <= r.Y0 - gap || top >= r.Y1 + gap);
    }
}
