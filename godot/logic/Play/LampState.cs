using System;

namespace SurvivorUnchained.Play;

/// <summary>HUD A2 "Lamps Are Lit": her life lamp's flame from her life (LifeLamp.cs draws it, and lights the
/// ground under it). Full: tall and steady. Half: smaller. At 30% and under: it gutters (lower, flickering, a
/// blue root). At 0: out, with a curl of smoke; it relights (growing back over 0.4 s) when she rises.</summary>
public sealed class LampState
{
    /// <summary>Where the guttering starts (her life, 0..1).</summary>
    public const float GutterAt = 0.30f;
    /// <summary>The relit flame's growth back to its height (s).</summary>
    public const float Relight = 0.4f;

    /// <summary>The flame's height (0..1 of full), its guttering (0..1), seconds since it went out (-1 lit),
    /// and its light now (Glow, flicker included; 0 out): the glass's glow and the pool's.</summary>
    public float Flame { get; private set; } = 1;
    public float Gutter { get; private set; }
    public float OutT { get; private set; } = -1;
    public float Flick { get; private set; } = 1;
    public float Light { get; private set; } = 1;

    float gut, grow = 1;

    /// <summary>The flame's height for a life (before guttering and relighting), steep so the flame is a meter of
    /// its own (round 2 judge: 1.0 and 0.18 looked the same): 1 at full, 0.6 at 55%, 0.28 at 18%.</summary>
    public static float Height(float life) => life <= 0 ? 0 : 0.12f + 0.88f * Math.Clamp(life, 0, 1);

    /// <summary>The flame's light for its height (0..1; the glass's glow, the lamp's own light and the pool on
    /// the ground): full lit at full, about half at 55%, nearly dark at 18%.</summary>
    public static float Glow(float flame) => MathF.Pow(Math.Max(0, flame), 1.5f);

    /// <summary>How hard it gutters at a life: 0 above 30%, 0.35 at 30%, 1 at 6% and under.</summary>
    public static float GutterFor(float life) => life > GutterAt || life <= 0 ? 0 : Math.Min(1, 0.35f + 0.65f * (GutterAt - life) / (GutterAt - 0.06f));

    /// <summary>The flame's flicker at time t (s) for a gutter: a slight breath when steady; guttering, an
    /// irregular 3-6 Hz stutter of up to +-35%. 1 is its full light.</summary>
    public static float FlickerAt(double t, float gutter)
    {
        float steady = 1 + 0.035f * (float)(Math.Sin(t * 7.3) * 0.6 + Math.Sin(t * 12.9 + 1.3) * 0.4);
        // (3.3, 4.7 and 5.9 Hz, out of step: never a clean beat)
        double n = (Math.Sin(t * 20.7) + Math.Sin(t * 29.5 + 2.1) * 0.7 + Math.Sin(t * 37.1 + 0.4) * 0.5) / 2.2;
        float amp = 0.35f * Math.Min(1, gutter / 0.6f);
        return steady * (1 + amp * (float)Math.Clamp(n * 1.4, -1, 1));
    }

    /// <summary>A frame: her life as drawn (0..1), dt and the time (s).</summary>
    public void Tick(float life, float dt, double time)
    {
        if (life <= 0)
        {
            OutT = OutT < 0 ? 0 : OutT + dt;
            grow = 0;
        }
        else
        {
            OutT = -1;
            grow = Math.Min(1, grow + dt / Relight);
        }
        gut += (GutterFor(life) - gut) * (1 - MathF.Exp(-6 * dt));
        Gutter = gut < 0.002f ? 0 : gut;
        float g = 1 - (1 - grow) * (1 - grow);
        Flame = Height(life) * (1 - 0.2f * Gutter) * g;
        Flick = OutT >= 0 ? 0 : FlickerAt(time, Gutter);
        Light = OutT >= 0 ? 0 : Math.Clamp(Glow(Flame) * Flick, 0, 1.2f);
    }
}
