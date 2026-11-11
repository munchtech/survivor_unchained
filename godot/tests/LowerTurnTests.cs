using System;
using System.Linq;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class LowerTurnTests
{
    [Theory]
    [InlineData(0, 0, false)]
    [InlineData(30, 30, false)]
    [InlineData(60, 60, false)]
    [InlineData(89, 60, false)]
    [InlineData(91, 60, false)]    // from forward, 91 stays forward (band to 100)
    [InlineData(120, -60, true)]
    [InlineData(180, 0, true)]
    [InlineData(-150, 30, true)]
    public void Delta(double theta, double delta, bool back)
    {
        var r = LowerTurn.Solve(theta, 1, false);
        Assert.Equal(delta, r.Delta, 6);
        Assert.Equal(back, r.Back);
    }

    [Theory]
    [InlineData(-1.3, 1.3, 1.0)]
    [InlineData(-2.6, 1.3, 2.0)]
    [InlineData(-5, 1.3, 2.0)]
    [InlineData(-0.1, 1.3, 0.3)]
    [InlineData(-1, 0, 1.0)]
    public void BackScale(double fy, double vb, double want) => Assert.Equal(want, LowerTurn.BackScale(fy, vb), 6);

    [Fact]
    public void Feeds()
    {
        Assert.Equal(1.0, LowerTurn.Solve(0, 1, false).FeedY, 6);
        Assert.Equal(Math.Cos(29 * Math.PI / 180), LowerTurn.Solve(89, 1, false).FeedY, 6);
        Assert.Equal(-1.0, LowerTurn.Solve(180, 1, false).FeedY, 6);
        Assert.Equal(-Math.Cos(0), LowerTurn.Solve(120, 1, false).FeedY, 6);
        Assert.Equal(-1.0, LowerTurn.Solve(-150, 1, true).FeedY, 6);
    }

    [Fact]
    public void Hysteresis()
    {
        Assert.False(LowerTurn.Solve(95, 1, false).Back);
        Assert.True(LowerTurn.Solve(101, 1, false).Back);
        Assert.True(LowerTurn.Solve(85, 1, true).Back);
        Assert.False(LowerTurn.Solve(79, 1, true).Back);
        Assert.True(LowerTurn.Solve(-91, 1, true).Back);
        Assert.False(LowerTurn.Solve(-91, 1, false).Back);
    }

    [Fact]
    public void FeedIsContinuousAtZeroSpeedAndWraps()
    {
        Assert.Equal(0, LowerTurn.Solve(45, 0, false).FeedY, 9);
        Assert.Equal(LowerTurn.Solve(-150, 1, false).Delta, LowerTurn.Solve(210, 1, false).Delta, 6);
    }

    [Theory]
    [InlineData(60)] [InlineData(-37.5)] [InlineData(0)]
    public void SpineSharesSumToTheTurn(double delta)
    {
        Assert.Equal(-delta, LowerTurn.SpineYaws(delta).Sum(), 9);
    }

    [Fact]
    public void EaseApproaches()
    {
        double d = 0;
        for (int i = 0; i < 60; i++) d = LowerTurn.Ease(d, 40, 1 / 60.0);
        Assert.InRange(d, 39.9, 40);
        Assert.InRange(LowerTurn.Ease(0, 40, 0.12), 25, 26);
    }
}
