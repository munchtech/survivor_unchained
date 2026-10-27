using System;

namespace SurvivorUnchained.Play;

/// <summary>
/// How far her pectoral pulls a breast toward the armpit as that arm rises
/// (View/HerRaise.cs): 0 with the arm down, easing in from about horizontal to
/// full with the arm well up. Elevation is the upper arm's angle above her
/// chest's horizontal, in degrees (her rest A-pose is about -47).
/// </summary>
public static class RaiseRamp
{
    /// <summary>The upper arm's elevation in degrees, from the up component
    /// (in her chest's frame) of its unit direction.</summary>
    public static float Elevation(float upComponent) =>
        (float)(Math.Asin(Math.Clamp(upComponent, -1f, 1f)) * 180 / Math.PI);

    /// <summary>The pull, 0..1: smoothstep from <paramref name="start"/> to
    /// <paramref name="full"/> degrees, so it eases in and settles.</summary>
    public static float Weight(float elevation, float start, float full)
    {
        if (full <= start) return elevation >= full ? 1 : 0;
        float t = Math.Clamp((elevation - start) / (full - start), 0f, 1f);
        return t * t * (3 - 2 * t);
    }

    /// <summary>The stretch toward the armpit with the volume kept: up and
    /// side axes grow, projection gives the rest back (their product is 1).</summary>
    public static (float Side, float Along, float Up) Stretch(float w, float up, float side)
    {
        float u = 1 + w * up, s = 1 + w * side;
        return (s, 1 / (u * s), u);
    }
}
