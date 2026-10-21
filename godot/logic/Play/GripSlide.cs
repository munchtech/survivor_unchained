using System;

namespace SurvivorUnchained.Play;

/// <summary>Where her right fist grips the piece (animation 47): a clip may slide it along its shaft (the combat
/// arcanist idle holds the staff 8-9 cm lower in her fist). Which clip's value counts, and the ease between them.</summary>
public static class GripSlide
{
    /// <summary>The slide wanted now: a whole-body one-shot's, else an upper-body one's, else the idle/run pair's by the move blend.</summary>
    public static float Target(bool fullOn, float fullS, bool upperOn, float upperS, float moveBlend, float idleS, float runS)
        => fullOn ? fullS : upperOn ? upperS : idleS + (runS - idleS) * Math.Clamp(moveBlend, 0f, 1f);

    /// <summary>Current eased toward target over dt seconds.</summary>
    public static float Ease(float current, float target, float dt, float rate = 12f)
        => current + (target - current) * (1f - MathF.Exp(-rate * dt));
}
