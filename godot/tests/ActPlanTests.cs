using System.Linq;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The --act harness's timing (ActPlan): the travel window, hold repeats, spin only while looping, repeat gaps.</summary>
public class ActPlanTests
{
    static HerEvents.Beats B(int[]? loop = null, params (string, int)[] ev) => new(System.Array.Empty<int>(), null, null, loop, ev);

    [Fact]
    public void TravelRunsOverTakeoffToLandThenStays()
    {
        var p = new ActPlan(2.0, B(null, ("takeoff", 30), ("land", 90)), false, at: 1, travel: 6);   // takeoff 0.5 s, land 1.5 s
        Assert.Equal((0.5, 1.5), p.Window);
        Assert.Equal(-1, p.Sample(0.5).Pass);
        Assert.Equal(0, p.Sample(1.4).Ahead, 6);       // (0.4 s in: before takeoff)
        Assert.Equal(3, p.Sample(2.0).Ahead, 6);       // (1.0 s in: halfway)
        Assert.Equal(6, p.Sample(2.6).Ahead, 6);
        Assert.Equal(6, p.Sample(9).Ahead, 6);         // (stays where it landed)
        Assert.True(p.Sample(2.0).Active); Assert.False(p.Sample(3.5).Active);
        Assert.Equal(1.0, p.Sample(2.0).Clip, 6);
    }

    [Fact]
    public void ChargeWindowThenWholeClipWithAWarningFlag()
    {
        var c = new ActPlan(1.2, B(null, ("launch", 12), ("impact", 48)), false, travel: 4);
        Assert.Equal((0.2, 0.8), c.Window); Assert.False(c.WindowWhole);
        var w = new ActPlan(1.2, B(), false, at: 0, travel: 4);
        Assert.Equal((0.0, 1.2), w.Window); Assert.True(w.WindowWhole);
        Assert.Equal(2, w.Sample(0.6).Ahead, 6);
        Assert.True(new ActPlan(1.0, null, false, travel: 3).WindowWhole);
    }

    [Fact]
    public void HoldRepeatsTheLoopInWholePassesThenPlaysOn()
    {
        var p = new ActPlan(2.0, B(new[] { 30, 60 }), false, at: 0, hold: 2);   // loop 0.5-1.0 s: four passes for 2 s
        Assert.Equal(4, p.Passes);
        Assert.Equal(2.0 + 3 * 0.5, p.Duration, 6);
        Assert.Equal(0.25, p.ClipAt(0.25), 6);
        Assert.Equal(0.75, p.ClipAt(0.75), 6);
        Assert.Equal(0.6, p.ClipAt(1.1), 6);            // (second pass: back at 0.5 and on)
        Assert.Equal(0.5, p.ClipAt(1.0), 6);
        Assert.Equal(1.0, p.ClipAt(2.5), 6);            // (the last pass's end: the clip leaves at b)
        Assert.Equal(1.5, p.ClipAt(3.0), 6);
        Assert.Equal(2.0, p.ClipAt(3.5), 6);
        Assert.Equal(1, new ActPlan(2.0, B(new[] { 30, 60 }), false, hold: 0).Passes);    // (no hold: once)
        Assert.Equal(1, new ActPlan(2.0, B(new[] { 30, 60 }), false, hold: 0.4).Passes);
        Assert.Equal(2.0, new ActPlan(2.0, B(new[] { 30, 60 }), false, hold: 0).Duration, 6);
    }

    [Fact]
    public void ALoopingAnimationHoldsOverItsWholeLengthAndAClipWithNoLoopIgnoresTheHold()
    {
        var l = new ActPlan(1.5, null, true, at: 0, hold: 2);
        Assert.Equal((0.0, 1.5), l.Loop!.Value); Assert.Equal(2, l.Passes);
        Assert.Equal(0.5, l.ClipAt(2.0), 6);
        var n = new ActPlan(1.5, null, false, hold: 2, spin: 1);
        Assert.Null(n.Loop); Assert.True(n.HoldIgnored); Assert.True(n.SpinIgnored);
        Assert.Equal(1.5, n.Duration, 6);
        Assert.Equal(0, n.Sample(5).Yaw);
    }

    [Fact]
    public void SpinTurnsLeftOnlyWhileTheLoopPlaysAndStays()
    {
        var p = new ActPlan(2.0, B(new[] { 30, 60 }), false, at: 0, hold: 1, spin: 2);   // two passes: loop run 0.5-1.5 s
        Assert.Equal(0, p.Sample(0.4).Yaw, 6);
        Assert.Equal(2 * System.Math.Tau * 0.5, p.Sample(1.0).Yaw, 6);                    // (positive: counter-clockwise, to her left)
        Assert.Equal(2 * System.Math.Tau * 1.0, p.Sample(1.5).Yaw, 6);
        Assert.Equal(2 * System.Math.Tau, p.Sample(2.4).Yaw, 6);                          // (past the loop: stopped)
        Assert.Equal(2 * System.Math.Tau, p.Sample(20).Yaw, 6);
    }

    [Fact]
    public void RepeatsStartFromTheFirstSpotAfterTheGap()
    {
        var p = new ActPlan(1.0, B(null, ("takeoff", 0), ("land", 60)), false, at: 1, travel: 3, repeat: 2, gap: 1.5);
        Assert.Equal(2.0, p.Duration + 0.5 + 0.5, 6);
        Assert.Equal(3, p.Sample(2.2).Ahead, 6);        // (first pass done)
        Assert.Equal(0, p.Sample(2.2).Pass);
        Assert.Equal(3, p.Sample(3.4).Ahead, 6);        // (the gap 2.0-3.5: where it ended)
        Assert.Equal(1, p.Sample(3.6).Pass);
        Assert.Equal(0.3, p.Sample(3.6).Ahead, 6);      // (second pass starts at 3.5, from the spot)
        Assert.Equal(3, p.Sample(60).Ahead, 6);
        Assert.Equal(1, p.Sample(60).Pass);
        Assert.Equal(3.5, p.Start(1), 6);
    }

    [Fact]
    public void EventsAreHitInRunTimeAndMissingOnesAreSkipped()
    {
        var p = new ActPlan(2.0, B(new[] { 30, 60 }, ("plant", 12), ("burst", 90)), false, at: 1, hold: 1);   // two loop passes: +0.5 s
        Assert.Equal(1.2, p.EventsRun(0).First(e => e.Name == "plant").Run, 6);
        Assert.Equal(1 + 1.5 + 0.5, p.EventsRun(0).First(e => e.Name == "burst").Run, 6);   // (past the loop: after the held passes)
        Assert.Null(p.EventPass("land"));
        Assert.Empty(new ActPlan(1, null, false).EventsRun(0));
    }
}
