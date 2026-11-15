using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public sealed class DirLegsTests
{
    const double S = 5;

    [Fact] public void ForwardIsPureF()
    {
        var r = DirLegs.Solve(0, S, false);
        Assert.Equal(1, r.W[DirLegs.F], 6); Assert.Equal(0, r.Delta, 6); Assert.False(r.Back);
    }

    [Fact] public void NinetyForwardTurnsPelvis45AndUsesFl()
    {
        var r = DirLegs.Solve(90, S, false);
        Assert.Equal(45, r.Delta, 6); Assert.Equal(1, r.W[DirLegs.FL], 6);
        var l = DirLegs.Solve(-90, S, false);
        Assert.Equal(-45, l.Delta, 6); Assert.Equal(1, l.W[DirLegs.FR], 6);
    }

    [Fact] public void OneEightyIsPureBackNoDelta()
    {
        var r = DirLegs.Solve(180, S, false);
        Assert.True(r.Back); Assert.Equal(1, r.W[DirLegs.B], 6); Assert.Equal(0, r.Delta, 6);
    }

    [Fact] public void BackDiagonalFromBackMode()
    {
        var r = DirLegs.Solve(-135, S, true);
        Assert.True(r.Back);
        Assert.Equal(-157.5, r.H, 6); Assert.Equal(0.5, r.W[DirLegs.B], 6); Assert.Equal(0.5, r.W[DirLegs.BR], 6);
        Assert.Equal(22.5, r.Delta, 6);
    }

    [Fact] public void Hysteresis()
    {
        Assert.False(DirLegs.Solve(100, S, false).Back);
        Assert.True(DirLegs.Solve(100, S, true).Back);
        Assert.False(DirLegs.Solve(60, S, true).Back);
        Assert.True(DirLegs.Solve(111, S, false).Back);
    }

    [Fact] public void IdleIsForwardOnly()
    {
        var r = DirLegs.Solve(170, 0.05, true);
        Assert.Equal(0, r.Delta); Assert.False(r.Back); Assert.Equal(1, r.W[DirLegs.F], 6);
    }

    [Fact] public void WeightsSumToOneAndOnlyActiveSet()
    {
        foreach (bool was in new[] { false, true })
            for (int a = -180; a <= 180; a++)
            {
                var r = DirLegs.Solve(a, S, was);
                Assert.Equal(1, r.W[0] + r.W[1] + r.W[2] + r.W[3] + r.W[4] + r.W[5], 9);
                double fwd = r.W[0] + r.W[1] + r.W[2], back = r.W[3] + r.W[4] + r.W[5];
                Assert.True(r.Back ? fwd == 0 : back == 0);
            }
    }

    [Fact] public void DeltaContinuousInsideEachMode()
    {
        foreach (bool was in new[] { false, true })
        {
            double? prevD = null; bool? prevB = null;
            for (int i = -1800; i <= 1800; i++)
            {
                var r = DirLegs.Solve(i / 10.0, S, was);
                if (prevD is double pd && prevB == r.Back)
                {
                    double jump = Math.Abs(LowerTurn.Wrap(r.Delta - pd));
                    Assert.True(jump < 0.3, $"delta jump {jump} at {i / 10.0} was={was}");
                }
                prevD = r.Delta; prevB = r.Back;
            }
        }
    }

    [Fact] public void EaseConverges()
    {
        double c = 0;
        for (int i = 0; i < 100; i++) c = DirLegs.Ease(c, 10, 1 / 30.0, 0.08);
        Assert.Equal(10, c, 3);
    }
}
