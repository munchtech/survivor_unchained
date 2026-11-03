using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The Lamps screen's motion (docs/design/LAMPS_SCREEN_BRIEF.md §11): one clock for the board's shaders
/// (shaders/ui_lamps_motion.gdshaderinc reads it as `now`), the grade and the chrome, and reduce-motion. The shots'
/// bursts (--lamps-burst) freeze the clock at exact offsets after an event, so a frame sequence is the motion's own
/// times, not the frames' luck.
/// </summary>
public static class LampMotion
{
    /// <summary>No event (the shaders' NO_EV).</summary>
    public const float None = -1e4f;
    /// <summary>The close's "none" (far ahead).</summary>
    public const float Never = 1e6f;

    /// <summary>Reduce-motion: the game's Motion setting (Settings, "Screen shake": reduced or off) or --lamps-still. It
    /// stills the flicker, the breathing and the flame's run, and the staggers are instant.</summary>
    public static bool Still => SurvivorUnchained.Args.Has("lamps-still") || Play.Settings.Current.Motion != "full";

    static double frozen = -1;
    /// <summary>Seconds (the engine's ticks), or the frozen time in a burst.</summary>
    public static double Now => frozen >= 0 ? frozen : Time.GetTicksUsec() / 1e6;
    public static void Freeze(double t) => frozen = t;
    public static void Thaw() => frozen = -1;

    public static float EaseOut(double u)
    {
        u = Mathf.Clamp(u, 0, 1);
        return (float)(1 - (1 - u) * (1 - u) * (1 - u));
    }
}
