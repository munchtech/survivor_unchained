using System;

namespace SurvivorUnchained.World;

/// <summary>
/// The flame kit's light flicker (look bible 10_props_flames: "+-10-15% energy, never a strobe"):
/// two octaves of smooth 1D gradient noise, a slow sway and a quicker lick, rolled off softly
/// (tanh) toward +-13%: peaks of about +-11-12% every few seconds. Pure, so its range is measured in tests (FxTests).
/// </summary>
public static class FlameFlicker
{
    public const float Depth = 0.13f;

    static float Hash(int i, int seed)
    {
        uint h = unchecked((uint)i * 374761393u + (uint)seed * 668265263u);
        h = unchecked((h ^ (h >> 13)) * 1274126177u);
        return ((h ^ (h >> 16)) & 0xffffff) / (float)0xffffff * 2f - 1f;
    }

    /// <summary>Smooth gradient noise, about -0.5..0.5.</summary>
    public static float Noise(float x, int seed)
    {
        int i = (int)MathF.Floor(x);
        float f = x - i, u = f * f * f * (f * (f * 6 - 15) + 10);
        float a = Hash(i, seed) * f, b = Hash(i + 1, seed) * (f - 1);
        return a + (b - a) * u;
    }

    /// <summary>The factor on a light's energy at time t (s) for a phase 0..1: 1 +- Depth at most.</summary>
    public static float At(float t, float phase)
    {
        int seed = (int)(phase * 9973);
        float n = Noise(t * 2.2f, seed) * 0.7f + Noise(t * 6.3f, seed + 17) * 0.3f;
        return 1 + Depth * MathF.Tanh(n * 5f);
    }
}
