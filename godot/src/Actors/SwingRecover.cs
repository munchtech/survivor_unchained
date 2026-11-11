namespace SurvivorUnchained.View;

/// <summary>A released one-shot cut's recover (A1): a cut that does not end on her stance (Sunder's cut A ends in a left wind)
/// is crossfaded from its live pose to the armed idle over Ev.SwingRelease's Recover, not run out and faded in 0.2 s.
/// A cut that ends on the stance (cut B) keeps the old fade. Plain C#, so the tests read it.</summary>
public static class SwingRecover
{
    // Where a cut ends is not in the clip data yet: the clips that end OFF the stance, named here.
    static readonly System.Collections.Generic.HashSet<string> OffStance = new() { "sunder_cut_a" };

    public static bool EndsOnStance(string? clip) => clip == null || !OffStance.Contains(clip);

    /// <summary>The fade-out (seconds) a release gives this clip: the sim's Recover, or null for the usual fade.</summary>
    public static double? Fade(string? clip, double recover) => EndsOnStance(clip) || recover <= 0 ? null : recover;

    /// <summary>Weight of the idle `since` seconds after the release, over `fade` (1 = the idle pose).</summary>
    public static double IdleWeight(double since, double fade) => fade <= 0 ? 1 : System.Math.Clamp(since / fade, 0, 1);
}
