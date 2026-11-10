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
}
