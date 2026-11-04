using System;

namespace SurvivorUnchained.Ui;

/// <summary>The timeline of one lamp mark on the Ford-Warden's bar (no Godot types, so it is tested). t is the
/// seconds since the mark last changed state; a mark that never changed has t = infinity.
/// Going out: the flame flares to 1.4x over 0.12 s, then fades to dark over 0.5 s.
/// Relighting: brightness rises to 1 and the halo blooms to 1.7x over 0.2 s, then settles to 1 over 0.6 s.</summary>
public static class LampMarkAnim
{
    public const float FlarePeak = 1.4f, FlareRise = 0.12f, FadeOut = 0.5f;
    public const float BloomPeak = 1.7f, BloomRise = 0.2f, BloomSettle = 0.6f;

    /// <summary>The flags a bar of `count` marks shows with `lit` burning: the first `lit` are lit (they go out from the right).</summary>
    public static bool[] Targets(int count, int lit)
    {
        var f = new bool[Math.Max(0, count)];
        for (int i = 0; i < f.Length; i++) f[i] = i < lit;
        return f;
    }

    /// <summary>How bright the flame is shown (0 dark, 1 steady, up to 1.4 in the flare).</summary>
    public static float Brightness(bool lit, float t)
    {
        if (t < 0) t = 0;
        if (lit) return t >= BloomRise ? 1f : EaseOut(t / BloomRise);
        if (t < FlareRise) return 1f + (FlarePeak - 1f) * (t / FlareRise);
        float u = (t - FlareRise) / FadeOut;
        return u >= 1 ? 0f : FlarePeak * (1f - u);
    }

    /// <summary>The halo's size as a multiple of its normal radius (1 steady, 1.7 at the relight's bloom).</summary>
    public static float HaloScale(bool lit, float t)
    {
        if (!lit) return 1f;
        if (t < 0) t = 0;
        if (t < BloomRise) return 1f + (BloomPeak - 1f) * EaseOut(t / BloomRise);
        float u = (t - BloomRise) / BloomSettle;
        return u >= 1 ? 1f : BloomPeak + (1f - BloomPeak) * EaseOut(u);
    }

    static float EaseOut(float u) { u = Math.Clamp(u, 0f, 1f); return 1f - (1f - u) * (1f - u); }
}
