using System;

namespace SurvivorUnchained.World;

/* The day's own clock (docs/design/STORY_NIGHTS_AND_TIME.md §2, the owner's decision): time moves
 * by itself, dawn, day, dusk and night, so a player who never finds the inn's bed is still moved on.
 * It counts seconds of free play since the day's dawn (WorldState.Clock), and only free play: it
 * waits in conversations, cinematics, pages, the draft and the chest, travel, arenas and the
 * prologue (the host decides what is free; Journey.PassTime moves it).
 *
 *   dawn    1 min   the morning
 *   day     9 min
 *   dusk    2 min   the warning: the lamps lit, the night's fight named
 *   night   6 min   the night's fight called; then the night passes by itself
 *
 * Twelve minutes of free play make the story's day of about twenty with its talk. */
public static class DayClock
{
    public const double DawnLength = 60, DayLength = 540, DuskLength = 120, NightLength = 360;
    public const double DayAt = DawnLength, DuskAt = DayAt + DayLength, NightAt = DuskAt + DuskLength, NightEnds = NightAt + NightLength;
    /// <summary>Half the night gone: one nudge.</summary>
    public const double NudgeAt = NightAt + NightLength / 2;
    /// <summary>The night left after a fight, at least: time to hear the town, or to go straight to another.</summary>
    public const double AfterFight = 180;

    /// <summary>The time of day at a point on the clock (past the night's end it is still night,
    /// until the host lets it pass).</summary>
    public static TimeOfDay At(double s) => s < DayAt ? TimeOfDay.Dawn : s < DuskAt ? TimeOfDay.Day : s < NightAt ? TimeOfDay.Dusk : TimeOfDay.Night;

    public static double StartOf(TimeOfDay t) => t switch
    {
        TimeOfDay.Dawn => 0, TimeOfDay.Day => DayAt, TimeOfDay.Dusk => DuskAt, _ => NightAt,
    };

    /// <summary>The clock where the time of day says it is: a save from before the clock, or the
    /// time set by something else (a skip, the prologue's dawn), starts at that time's beginning.</summary>
    public static void Sync(WorldState w)
    {
        if (At(w.Clock) != w.Time || w.Clock < 0 || double.IsNaN(w.Clock)) w.Clock = StartOf(w.Time);
    }

    /// <summary>Seconds of free play until the night comes (0 at night).</summary>
    public static double ToNight(WorldState w) => Math.Max(0, NightAt - w.Clock);
}

/// <summary>What a stretch of free play brought (Journey.PassTime): a turn of the day, the
/// night's nudge, or the night's end (the host then lets it pass: Journey.SeeNightOut).</summary>
public enum ClockTurn { Day, Dusk, Night, Nudge, NightOver }
