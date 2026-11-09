using SurvivorUnchained.Play.Zones;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M5 r3) The Warden's Legendary lands on its own ground (Prologue.LegendSpot): off her feet, off the corpse, on screen.</summary>
public class LegendSpotTests
{
    static double D((double X, double Z) a, (double X, double Z) b) => System.Math.Sqrt((a.X - b.X) * (a.X - b.X) + (a.Z - b.Z) * (a.Z - b.Z));

    [Theory]
    [InlineData(-2.8, 0)]   // she stands where the old spot was (the judge's frame: the beam on her)
    [InlineData(0, 4)]      // C03's mark, 4 m south of him
    [InlineData(3, -1)]
    [InlineData(-1, 1)]
    public void It_lands_clear_of_her_and_the_corpse_inside_the_safe_box(double hx, double hz)
    {
        var corpse = (X: 10.0, Z: 20.0);
        var her = (X: corpse.X + hx, Z: corpse.Z + hz);
        var at = Prologue.LegendSpot(corpse, her, 0, (_, _) => true);
        Assert.True(D(at, her) >= Prologue.LegendFromHer, $"{D(at, her):0.00} m from her");
        Assert.True(D(at, corpse) >= Prologue.LegendFromCorpse - 1e-9);
        Assert.InRange(at.X - her.X, -Prologue.LegendSafeX, Prologue.LegendSafeX);
        Assert.InRange(at.Z - her.Z, -Prologue.LegendSafeZ, Prologue.LegendSafeZ);
    }

    [Fact]
    public void It_lands_on_free_ground()
    {
        var at = Prologue.LegendSpot((0, 0), (0, 4), 0, (x, _) => x > 0);
        Assert.True(at.X > 0);
    }
}
