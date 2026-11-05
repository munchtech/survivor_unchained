using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>H7's family (data/content/flare_family.json): every staged Strike's stop sits in 0.25-0.4 s, the world is held,
/// and the grade and marks read their numbers from the data.</summary>
public class FlareFamilyTests
{
    static readonly string[] Strikes = ["the_long_cut", "bell_of_the_morning", "burns_twice", "the_roads_toll", "the_branding", "one_arrow", "drag_them_under", "the_butchers_bill"];

    [Fact]
    public void EveryStrikesStopIsATrueHoldInRange()
    {
        Assert.Equal(0, FlareFamily.Stop.WorldRate);
        foreach (var id in Strikes)
        {
            var f = Lamps.Flare(id)!;
            foreach (var clutch in new[] { false, true })
            {
                double s = FlareFamily.StopOf(id, f.Calling, clutch, clutch);
                Assert.InRange(s, 0.25, 0.4);
            }
        }
        Assert.Equal(0.40, FlareFamily.StopOf("the_long_cut", "warden", false, false), 3);
    }

    [Fact]
    public void TheGradeIsIndigoAndDarkerByNight()
    {
        var g = FlareFamily.Grades;
        Assert.InRange(g.Night.Value, 0.5, 0.6);
        Assert.InRange(g.Day.Value, 0.7, 0.8);
        Assert.InRange(g.Night.Lights, 0.2, 0.3);
        Assert.StartsWith("#", g.Night.Tint);
        Assert.True(FlareFamily.Marks.Main >= 1.8);
    }

    [Fact]
    public void ThePeakKeepsFlareLooksCaps()
    {
        // FLARE_LOOK §1.6: the Spend's peak for 4 frames at most; the judge's r1 fix 1: a 2-frame hitstop, a kick of 8-10 px.
        var pk = FlareFamily.Peak;
        Assert.Equal(2, pk.Hitstop);
        Assert.True(System.Linq.Enumerable.Count(pk.Frames, f => f >= 0.75) <= 4);
        Assert.InRange(FlareFamily.Beat.KickPx, 8, 10);
        Assert.Equal("line", FlareFamily.Of("the_long_cut").Peak.Shape);
        Assert.Equal("disk", FlareFamily.Of("bell_of_the_morning").Peak.Shape);
        Assert.Equal(8, FlareFamily.Of("bell_of_the_morning").Peak.Radius);
        Assert.Equal("toll", FlareFamily.Of("bell_of_the_morning").Ripple);
        // The band crosses the frame in 0.25-0.3 s (§1.6: 0.25 to 0.4).
        Assert.InRange(FlareFamily.Band.Time, 0.25, 0.3);
    }
}
