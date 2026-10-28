using System;

namespace SurvivorUnchained.Play;

/// <summary>Her life's pulse: her own bar under her and the screen's edges at low life (HerLight) read her life (the
/// pool of light round her, PoolGain, is the retired "her life" variant's, kept for its tests). One heart for all of it: the heartbeat sound
/// (SoundBridge) and the pictures' pulse share Period, so what beats on screen beats with what is heard.</summary>
public static class HeartPulse
{
    /// <summary>Where the heart starts (her life, 0..1): the sound's threshold, and the bar's low state.</summary>
    public const double LowAt = 0.30;

    /// <summary>How close to the end, 0 at LowAt (and over), 1 at none.</summary>
    public static double Urgency(double life) => Math.Clamp(1 - life / LowAt, 0, 1);

    /// <summary>The beat's period (s): 1.05 at 30%, 0.65 at none (the sound's own pacing).</summary>
    public static double Period(double life) => 1.05 - Urgency(life) * 0.4;

    /// <summary>When the sound last beat (the game's clock, s; SoundBridge sets it): the pictures' beat
    /// follows it while it sounds.</summary>
    public static double LastSound = double.NegativeInfinity;

    /// <summary>The beat's shape s seconds after a beat: lub (a sharp rise, a softer fall), dub 0.24 s later
    /// (the sound's second tone), 0..1.</summary>
    public static float Shape(double s)
    {
        static double P(double u) => u < 0 ? Math.Exp(-(u / 0.035) * (u / 0.035)) : Math.Exp(-u / 0.14);
        return (float)Math.Min(1, P(s) + 0.6 * P(s - 0.24));
    }

    /// <summary>The screen-edge vignette's strength at this life: none over 30%, subtle (0.3) at 30%, full
    /// toward 0 (eased, so it climbs fastest in the last stretch).</summary>
    public static float EdgeStrength(double life)
    {
        if (life > LowAt) return 0;
        double u = Urgency(life);
        return (float)(0.3 + 0.7 * Math.Pow(u, 1.3));
    }

    /// <summary>Her light on the ground: its gain (the pool shader's) at this life. Full 0.45 (about +40% at its
    /// heart), half at 55%, small at 25% and under, none at 0.</summary>
    public const float PoolFull = 0.45f;
    public static float PoolGain(double life)
    {
        life = Math.Clamp(life, 0, 1);
        if (life <= 0) return 0;
        // half at .55 rising to full at 1; .30 of it at .25; under that a small ember of it (.08 at the end)
        double g = life >= 0.55 ? 0.5 + 0.5 * (life - 0.55) / 0.45
            : life >= 0.25 ? 0.30 + 0.20 * (life - 0.25) / 0.30
            : 0.08 + 0.22 * life / 0.25;
        return (float)(PoolFull * Math.Clamp(g, 0, 1));
    }

    /// <summary>The flicker on her light at 25% and under (a multiplier, 0.35..1 at the end; 1 over 25%):
    /// a few incommensurate sines, so it never loops visibly.</summary>
    public static float Flicker(double life, double t)
    {
        if (life > 0.25) return 1;
        double depth = 0.25 + 0.4 * Math.Clamp(1 - life / 0.25, 0, 1);
        double n = 0.5 + 0.22 * Math.Sin(t * 13.1) + 0.17 * Math.Sin(t * 23.7 + 1.3) + 0.11 * Math.Sin(t * 41.3 + 4.1);
        return (float)(1 - depth * Math.Clamp(n, 0, 1));
    }
}
