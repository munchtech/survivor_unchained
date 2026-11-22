using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

[CollectionDefinition("MoveFlags", DisableParallelization = true)]
public class MoveFlagsCollection { }

/// <summary>The movement fixes behind MoveFlags (GAME_PLAN tasks 3 and 4): each is off by default, each does what it says when on.</summary>
[Collection("MoveFlags")]
public sealed class MoveFlagsTests : IDisposable
{
    const double Dt = 1 / 60.0;

    public MoveFlagsTests() => MoveFlags.All(false);
    public void Dispose() => MoveFlags.All(false);

    static Battle Make() => new(new BattleSetup
    {
        Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
        Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
    });

    static void Run(Battle b, int steps, double mx, double mz) { for (int i = 0; i < steps; i++) { b.Tick(Dt, mx, mz); b.Events.Drain(); } }
    static double Speed(Battle b) => Math.Sqrt(b.Player.Vx * b.Player.Vx + b.Player.Vz * b.Player.Vz);

    /// <summary>Her speed after holding +X for 120 ticks, flags off.</summary>
    static double Top()
    {
        bool keep = MoveFlags.StartFrames == 0;
        var b = Make();
        Run(b, 120, 1, 0);
        Assert.True(keep);
        return Speed(b);
    }

    static Battle AtFullSpeed(out double top)
    {
        top = Top();
        var b = Make();
        Run(b, 120, 1, 0);
        return b;
    }

    [Fact]
    public void Off_IsTheOldRamp()
    {
        double top = Top();
        var b = Make();
        Run(b, 2, 1, 0);
        Assert.True(Speed(b) < 0.6 * top, $"{Speed(b)} vs top {top}");
        Run(b, 7, 1, 0);
        Assert.True(Speed(b) >= 0.85 * top, $"{Speed(b)} vs top {top}");
    }

    [Fact]
    public void Start_TwoSteps()
    {
        double top = Top();
        MoveFlags.StartFrames = 2;
        var b = Make();
        Run(b, 1, 1, 0);
        Assert.Equal(top / 2, Speed(b), 6);
        Run(b, 1, 1, 0);
        Assert.Equal(top, Speed(b), 6);
        Assert.Equal(0, b.Player.Vz, 6);
    }

    [Fact]
    public void Stop_TwoSteps()
    {
        var b = AtFullSpeed(out double top);
        MoveFlags.StartFrames = MoveFlags.StopFrames = 2;
        double x0 = b.Player.X;
        Run(b, 1, 0, 0);
        Assert.Equal(top / 2, Speed(b), 6);
        Run(b, 1, 0, 0);
        Assert.Equal(0, Speed(b));
        Assert.True(b.Player.X - x0 <= 0.05, $"moved {b.Player.X - x0}");
    }

    [Fact]
    public void Reversal_FourSteps()
    {
        var b = AtFullSpeed(out double top);
        MoveFlags.StartFrames = MoveFlags.StopFrames = 2;
        double x0 = b.Player.X, far = 0;
        for (int i = 0; i < 4; i++) { b.Tick(Dt, -1, 0); b.Events.Drain(); far = Math.Max(far, b.Player.X - x0); }
        Assert.Equal(-top, b.Player.Vx, 6);
        Assert.True(far < 0.1, $"overshoot {far}");
    }

    [Fact]
    public void StopHold_NoSlide()
    {
        var b = AtFullSpeed(out double top);
        MoveFlags.StartFrames = 2;
        MoveFlags.StopHold = true;
        b.HoldFeet(0.06);
        double x = b.Player.X, z = b.Player.Z;
        for (int i = 0; i < 4; i++)
        {
            b.Tick(Dt, 1, 0); b.Events.Drain();
            Assert.Equal(x, b.Player.X);
            Assert.Equal(z, b.Player.Z);
            Assert.Equal(top, b.Player.Vx, 6);
        }
        b.Tick(Dt, 1, 0);
        Assert.Equal(top / 60, b.Player.X - x, 6);
    }

    [Fact]
    public void StopHold_OffDoesNothing()
    {
        var b = AtFullSpeed(out double top);
        MoveFlags.StopHold = false;
        b.HoldFeet(0.06);
        Assert.Equal(0, b.FeetHeld);
        double x = b.Player.X;
        Run(b, 1, 1, 0);
        Assert.True(b.Player.X > x);
    }

    static void RunDash(Battle b, double mx, double mz)
    {
        Assert.True(b.Dash(0, 1));
        for (int i = 0; i < 60; i++)
        {
            b.Tick(Dt, mx, mz); b.Events.Drain();
            if (b.Player.DashT <= 0) return;
        }
        Assert.Fail("the dash never ended");
    }

    [Fact]
    public void DashExit_FollowsKeys()
    {
        MoveFlags.DashExit = true;
        MoveFlags.StartFrames = 2;
        var b = Make();
        RunDash(b, 1, 0);
        Assert.True(b.Player.Vx > 0, $"Vx {b.Player.Vx}");
        Assert.True(Math.Abs(b.Player.Vz) < 1e-6, $"Vz {b.Player.Vz}");

        var c = Make();
        RunDash(c, 0, 0);
        Assert.Equal(0, c.Player.Vx);
        Assert.Equal(0, c.Player.Vz);
    }

    [Fact]
    public void DashExit_OffIsAlongTheDash()
    {
        var b = Make();
        RunDash(b, 1, 0);
        Assert.True(b.Player.Vz > 0, $"Vz {b.Player.Vz}");
        Assert.True(Math.Abs(b.Player.Vx) < 1e-6, $"Vx {b.Player.Vx}");
    }
}
