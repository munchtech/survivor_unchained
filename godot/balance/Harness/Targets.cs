using System;

namespace SurvivorUnchained.Balance;

/// <summary>What the design aims at (docs/SKILLS_DESIGN.md, "Targets"): the
/// ember's pace through an arena, and the power a build should have by then.
/// The pace is measured (the median of the harness's arenas), so a probe at
/// an ember level meets the horde of the minute that level is usually reached.</summary>
public static class Targets
{
    /// <summary>Ember level at the end of each minute (index 0 is the end of
    /// the first), the median of the harness's tier-1 arenas.</summary>
    public static readonly int[] EmberByMinute =
        [6, 9, 11, 13, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 29, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46];

    /// <summary>The minute an ember level is usually reached (fractional).</summary>
    public static double MinuteOf(int ember)
    {
        if (ember <= EmberByMinute[0]) return ember / (double)EmberByMinute[0];
        for (int i = 1; i < EmberByMinute.Length; i++)
            if (ember <= EmberByMinute[i])
                return i + (ember - EmberByMinute[i - 1]) / (double)Math.Max(1, EmberByMinute[i] - EmberByMinute[i - 1]);
        int last = EmberByMinute[^1];
        return EmberByMinute.Length + (ember - last) * 1.2;
    }

    /// <summary>The ember level usually held at a minute.</summary>
    public static int LevelAt(double minute) => EmberByMinute[Math.Clamp((int)minute - 1, 0, EmberByMinute.Length - 1)];
}
