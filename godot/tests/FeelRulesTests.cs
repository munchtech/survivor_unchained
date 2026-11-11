using SurvivorUnchained.View;
using Xunit;

namespace SurvivorUnchained.Tests;

public class FeelRulesTests
{
    [Fact]
    public void FoldKeepsTwoAndAddsTheRestIntoTheFirst()
    {
        var shown = FeelRules.Fold(new double[] { 50, 40, 30, 20, 10 }, false, out var folded);
        Assert.Equal(2, shown.Count);
        Assert.Equal((0, 50.0 + 30 + 20 + 10), shown[0]);
        Assert.Equal((1, 40.0), shown[1]);
        Assert.Equal(new[] { 0, 1, 0, 0, 0 }, folded);
    }

    [Fact]
    public void FoldMassStepIsOneTotal()
    {
        var shown = FeelRules.Fold(new double[] { 5, 4, 3, 2, 1 }, true, out var folded);
        Assert.Single(shown);
        Assert.Equal(15.0, shown[0].Sum);
        Assert.All(folded, f => Assert.Equal(0, f));
    }

    [Fact]
    public void FoldSmallInputs()
    {
        var one = FeelRules.Fold(new double[] { 7 }, false, out var f1);
        Assert.Single(one);
        Assert.Equal(7.0, one[0].Sum);
        Assert.Equal(new[] { 0 }, f1);
        var none = FeelRules.Fold(new double[0], false, out var f0);
        Assert.Empty(none);
        Assert.Empty(f0);
    }

    [Fact]
    public void NumberSpotIsAwayFromHerAndOverTheBody()
    {
        var (x, y) = FeelRules.NumberSpot(100, 200, 140, 300, 0, 60, 40);
        Assert.Equal(120 + FeelRules.NumberAside, x);
        Assert.Equal(200 - FeelRules.NumberOver, y + 20);
        var (xl, _) = FeelRules.NumberSpot(100, 200, 140, 300, 500, 60, 40);
        Assert.Equal(120 - FeelRules.NumberAside, xl);
        var (x2, y2) = FeelRules.NumberSpot(100, 200, 140, 300, 0, 60, 40, 2);
        Assert.Equal(120 + 2 * FeelRules.NumberAside, x2);
        Assert.Equal(200 - 2 * FeelRules.NumberOver, y2 + 20);
    }

    [Fact]
    public void KillDimWindow()
    {
        Assert.Equal(1f, FeelRules.KillDim(-1));
        Assert.Equal(0.3f, FeelRules.KillDim(0));
        Assert.Equal(0.3f, FeelRules.KillDim(16));
        Assert.Equal(1f, FeelRules.KillDim(22));
        float mid = FeelRules.KillDim(19);
        Assert.InRange(mid, 0.3001f, 0.9999f);
        Assert.Equal(1f, FeelRules.KillDim(23));
    }

    [Fact]
    public void LaunchRimHoldsThenFades()
    {
        Assert.Equal(1f, FeelRules.LaunchRim(0));
        Assert.Equal(1f, FeelRules.LaunchRim(12));
        Assert.Equal(0f, FeelRules.LaunchRim(18));
        float mid = FeelRules.LaunchRim(15);
        Assert.InRange(mid, 0.0001f, 0.9999f);
        Assert.Equal(0f, FeelRules.LaunchRim(-1));
    }

    [Fact]
    public void ReactRisesThenFalls()
    {
        Assert.Equal(0f, FeelRules.React(0));
        Assert.Equal(1f, FeelRules.React(0.04));
        Assert.Equal(0f, FeelRules.React(0.12));
        Assert.True(FeelRules.React(0.015) > 0 && FeelRules.React(0.015) < 1);
        Assert.True(FeelRules.React(0.02) < FeelRules.React(0.03));
        Assert.True(FeelRules.React(0.1) < FeelRules.React(0.07));
    }

    [Fact]
    public void TintedWindow()
    {
        Assert.False(FeelRules.Tinted(5));
        for (int n = 6; n <= 9; n++) Assert.True(FeelRules.Tinted(n));
        Assert.False(FeelRules.Tinted(10));
    }

    [Fact]
    public void TellDimsItsFillOnlyAndKeepsItsEdge()
    {
        float dim = FeelRules.KillDim(5);
        Assert.Equal(0.3f, FeelRules.TellFill(dim, 1.0f, false));
        Assert.True(FeelRules.TellEdge(dim, 1.0f, false) >= 0.6f);
        // outside the window nothing changes
        Assert.Equal(1f, FeelRules.TellFill(FeelRules.KillDim(40), 1.0f, false));
        Assert.Equal(1f, FeelRules.TellEdge(FeelRules.KillDim(40), 1.0f, false));
        // a standing wall (far from landing) dims as any tell
        Assert.Equal(0.3f, FeelRules.TellFill(dim, float.MaxValue, false));
    }

    [Fact]
    public void TellNeverDimsInItsLastThirdOfASecondNorAnyLane()
    {
        float dim = FeelRules.KillDim(5);
        Assert.Equal(1f, FeelRules.TellFill(dim, 0.3f, false));
        Assert.Equal(1f, FeelRules.TellEdge(dim, 0.1f, false));
        Assert.Equal(1f, FeelRules.TellFill(dim, 2f, true));
        Assert.Equal(1f, FeelRules.TellEdge(dim, 2f, true));
    }
}
