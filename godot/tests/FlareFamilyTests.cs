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
}
