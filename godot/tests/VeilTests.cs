using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The black over the play (logic/Play/Veil.cs): the arena entry must always lift (demo gate item 6).</summary>
public sealed class VeilTests
{
    /// <summary>Game.Travel's order with a pull: pull 1.1 s, the zone built after 1.15 s real, the lift
    /// (Fade 0 over 1.4 s) once frames come smooth. Frames: one long build hitch whose delta the engine
    /// clamps to 0.133 s, as on 3 November (c6_pull_auto: the pull had counted 0.32 s after 3 s).</summary>
    static void Frames(Veil v, ref double now, double until, double step, double clamp = 0.133)
    {
        while (now < until) { now += step; v.Tick(System.Math.Min(step, clamp), now); }
    }

    [Fact]
    public void PullEndsInRealTimeThroughClampedHitches()
    {
        var v = new Veil();
        v.Fade(0, 0);
        double now = 0;
        Frames(v, ref now, 0.1, 0.016);
        Assert.Equal(0, v.Alpha, 3);
        v.Pull(1.1, now);
        // the arena built behind the pull: two-second frames, clamped
        Frames(v, ref now, 1.3, 0.6);
        Assert.False(v.Pulling);
        Assert.Equal(1, v.Alpha, 3);
    }

    [Fact]
    public void LiftAfterTheEntryIsNeverReblackened()
    {
        var v = new Veil();
        v.Fade(0, 0);
        double now = 0;
        Frames(v, ref now, 0.1, 0.016);
        v.Pull(1.1, now);
        Frames(v, ref now, 1.25, 0.016);
        // the zone is entered; the blessing opens and is picked; the lift begins
        v.Fade(0, 1.4);
        Frames(v, ref now, 30, 0.016);
        Assert.False(v.Pulling);
        Assert.Equal(0, v.Alpha, 3);
    }

    [Fact]
    public void LiftDuringAPendingPullCancelsIt()
    {
        // The 3 November order: the lift came while the pull still ran (its end then held the black all night).
        var v = new Veil();
        v.Fade(0, 0);
        double now = 0;
        Frames(v, ref now, 0.1, 0.016);
        v.Pull(1.1, now);
        Frames(v, ref now, 0.45, 0.016);
        Assert.True(v.Pulling);
        v.Fade(0, 1.4);
        Assert.False(v.Pulling);
        Frames(v, ref now, 10, 0.016);
        Assert.Equal(0, v.Alpha, 3);
    }

    [Fact]
    public void FadeToBlackLeavesAPullRunning()
    {
        var v = new Veil();
        v.Fade(0, 0);
        double now = 0;
        Frames(v, ref now, 0.1, 0.016);
        v.Pull(1.1, now);
        v.Fade(1, 0.8);
        Assert.True(v.Pulling);
        Frames(v, ref now, 2, 0.016);
        Assert.Equal(1, v.Alpha, 3);
    }
}
