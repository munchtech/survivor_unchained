using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 lead 13 (judge r3b M1, M2): the cost seat's three looks are one rule on one Resolve.</summary>
public class SeatCostTests
{
    [Theory]
    [InlineData(20)]
    [InlineData(40)]
    public void Short_iff_Resolve_under_cost_and_the_arc_never_closes(double cost)
    {
        for (int i = 0; i <= 1000; i++)
        {
            double v = i * 0.1;
            float arc = SeatCost.Arc(v, cost);
            bool shortOfCost = SeatCost.Short(v, cost);
            Assert.Equal(v < cost, shortOfCost);
            if (shortOfCost) { Assert.InRange(arc, 0f, SeatCost.MaxArc); Assert.True(arc < 1f); }
            else Assert.Equal(-1f, arc);
        }
    }

    [Fact]
    public void A_hair_breadth_short_still_shows_the_gap() => Assert.Equal(SeatCost.MaxArc, SeatCost.Arc(39.9, 40));

    [Fact]
    public void No_cost_is_never_short() { Assert.False(SeatCost.Short(0, 0)); Assert.Equal(-1f, SeatCost.Arc(0, 0)); }

    [Fact]
    public void Held_while_short_keeps_the_short_interior_and_no_warm_well()
    {
        Assert.True(SeatCost.ShortLook(shortOfCost: true, numbered: false));
        Assert.False(SeatCost.WarmWell(held: true, shortOfCost: true));
        Assert.True(SeatCost.WarmWell(held: true, shortOfCost: false));
        Assert.False(SeatCost.ShortLook(shortOfCost: false, numbered: false));
    }
}
