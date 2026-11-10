using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 lead 7: the one rule for a bar's trail (BarTrail): by time, never by how often the bar is fed.</summary>
public class BarTrailTests
{
    static float Run(ref BarTrail t, float fill, float secs, float dt)
    {
        int n = (int)System.Math.Round(secs / dt);
        for (int i = 0; i < n; i++) t.Step(fill, dt);
        return t.At;
    }

    [Fact]
    public void A_bar_that_appears_below_full_has_no_trail()
    {
        var t = new BarTrail();
        Assert.Equal(0.6f, t.Step(0.6f, 1 / 60f));           // the first feed: nothing was lost on screen
        var u = new BarTrail();
        u.Snap(0.6f);
        Assert.Equal(0.6f, u.At);
        Assert.Equal(0.6f, u.Step(0.6f, 1 / 60f));
    }

    [Fact]
    public void A_blow_holds_then_closes_and_is_gone_inside_the_bound()
    {
        var t = new BarTrail();
        t.Snap(1);
        Assert.Equal(1, t.Step(0.6f, 1 / 60f));              // parted: the loss shows whole
        Assert.Equal(1, Run(ref t, 0.6f, 0.3f, 1 / 60f));    // still held inside Hold
        float mid = Run(ref t, 0.6f, 0.15f, 1 / 60f);        // past Hold: closing
        Assert.InRange(mid, 0.6f, 0.95f);
        // the longest a trail can stand: Hold + 1 / Rate (a whole bar lost at once)
        Assert.Equal(0.6f, Run(ref t, 0.6f, BarTrail.Hold + 1 / BarTrail.Rate, 1 / 60f));
    }

    [Fact]
    public void The_pace_does_not_depend_on_the_frame_rate()
    {
        foreach (float secs in new[] { 6 / 30f, 13 / 30f, 16 / 30f, 24 / 30f })
        {
            var a = new BarTrail(); a.Snap(1);
            var b = new BarTrail(); b.Snap(1);
            float at30 = Run(ref a, 0.4f, secs, 1 / 30f), at120 = Run(ref b, 0.4f, secs, 1 / 120f);
            Assert.InRange(at30 - at120, -0.06f, 0.06f);       // within one 30 fps frame of travel (Rate / 30)
        }
    }

    [Fact]
    public void A_bar_fed_once_still_settles()
    {
        // the fill is given once and never again: the HUD's frame alone carries the trail home
        var t = new BarTrail();
        t.Snap(1);
        const float fill = 0.6f;
        Assert.Equal(fill, Run(ref t, fill, 2, 1 / 30f));
    }

    [Fact]
    public void A_heal_takes_the_trail_with_it_and_the_trail_is_never_under_the_fill()
    {
        var t = new BarTrail();
        t.Snap(0.5f);
        Assert.Equal(0.8f, t.Step(0.8f, 1 / 60f));
        t.Step(0.3f, 1 / 60f);
        for (int i = 0; i < 200; i++) Assert.True(t.Step(0.3f + i * 0.001f, 1 / 60f) >= 0.3f + i * 0.001f - 1e-6f);
    }

    [Fact]
    public void A_steady_beating_does_not_hang_the_trail()
    {
        // a blow every frame for 3 s (a storm on a boss): later blows do not restart the wait, so the trail keeps
        // within Hold's worth of loss (plus a frame) of the fill
        var t = new BarTrail();
        t.Snap(1);
        float fill = 1, perSec = 0.2f, dt = 1 / 60f, worst = 0;
        for (int i = 0; i < 180; i++)
        {
            fill -= perSec * dt;
            worst = System.Math.Max(worst, t.Step(fill, dt) - fill);
        }
        Assert.InRange(worst, 0.01f, perSec * (BarTrail.Hold + 3 * dt));
    }

    [Fact]
    public void Bad_numbers_do_not_break_it()
    {
        var t = new BarTrail();
        Assert.Equal(0, t.Step(float.NaN, 1 / 60f));
        Assert.Equal(1, t.Step(7, 1 / 60f));
        Assert.Equal(1, t.Step(0.5f, -1));                    // time never runs backward
        Assert.Equal(1, t.Step(-3, 0));                       // under the bar's foot reads as empty; no time, no travel
        Assert.Equal(0, Run(ref t, -3, 2, 1 / 60f));
    }
}
