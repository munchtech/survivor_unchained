using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

public class CastMoveTests
{
    static readonly CastMoveDef B = new() { Side = 0.95, Back = 1.3, Cone = 45 };
    static double At(double deg, double baseSpeed = 5, double walk = 0.7, CastMoveDef? b = null)
    {
        double r = deg * System.Math.PI / 180;
        return CastMove.Speed(System.Math.Sin(r), System.Math.Cos(r), 0, 1, baseSpeed, walk, b ?? B);
    }

    [Fact] public void ForwardAndConeAreTheShare() { Assert.Equal(3.5, At(0), 6); Assert.Equal(3.5, At(45), 6); Assert.Equal(3.5, At(30), 6); }
    [Fact] public void SideIsCapped() => Assert.Equal(0.95, At(90), 6);
    [Fact] public void BackIsCapped() => Assert.Equal(1.3, At(180), 6);
    [Fact] public void BackCapAboveSideCapIsNotExceededByShare() => Assert.Equal(1.3, At(180, 5, 0.7), 6);
    [Fact] public void MonotoneBetween()
    {
        double prev = At(45);
        for (int d = 46; d <= 90; d++) { double v = At(d); Assert.True(v <= prev + 1e-9); prev = v; }
        prev = At(90);
        for (int d = 91; d <= 180; d++) { double v = At(d); Assert.True(v >= prev - 1e-9); prev = v; }
    }
    [Fact] public void BlockAbsentIsTodays() { Assert.Equal(3.5, CastMove.Speed(0, -1, 0, 1, 5, 0.7, null), 6); }
    [Fact] public void SlowedBaseNeverGoesUp()
    {
        Assert.Equal(0.35, At(90, 0.5), 6);
        Assert.Equal(0.35, At(180, 0.5), 6);
        for (int d = 0; d <= 180; d += 5) Assert.True(At(d, 0.5) <= 0.35 + 1e-9);
    }
    [Fact] public void StandingOrNoAimIsForward() { Assert.Equal(3.5, CastMove.Speed(0, 0, 0, 1, 5, 0.7, B), 6); Assert.Equal(3.5, CastMove.Speed(1, 0, 0, 0, 5, 0.7, B), 6); }
    [Fact] public void FwdOverridesWalk() => Assert.Equal(5.0, CastMove.Speed(0, 1, 0, 1, 5, 0.7, new CastMoveDef { Fwd = 1 }), 6);
    // (A1 lead 20, 10 Nov) the shipped cap is OFF until a body that walks the cast's directions ships (cast_move.json castMoveOff)
    [Fact] public void ShippedDefaultIsOff() => Assert.Null(CastMove.Default);
}
