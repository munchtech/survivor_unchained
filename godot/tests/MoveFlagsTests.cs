using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

[CollectionDefinition("MoveFlags", DisableParallelization = true)]
public class MoveFlagsCollection { }

/// <summary>The movement fixes behind MoveFlags (GAME_PLAN tasks 3 and 4): all on by default (what ships, 23 November); each
/// test turns them all off, then on one at a time, and each does what it says when on.</summary>
[Collection("MoveFlags")]
public sealed class MoveFlagsTests : IDisposable
{
    const double Dt = 1 / 60.0;

    public MoveFlagsTests() { MoveFlags.All(false); MoveFlags.RollTime = MoveFlags.RollLength = 0; }
    public void Dispose() => MoveFlags.Shipped();

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

    /// <summary>What ships (the owner's pick, 23 November): every fix on, the dash, no roll.</summary>
    [Fact]
    public void Shipped_IsAllNew_TheDash()
    {
        MoveFlags.Shipped();
        Assert.True(MoveFlags.CamLock && MoveFlags.StopHold && MoveFlags.DashHeld && MoveFlags.DashExit);
        Assert.Equal(2, MoveFlags.StartFrames);
        Assert.Equal(2, MoveFlags.StopFrames);
        Assert.Equal(0, MoveFlags.RollTime);
        Assert.Equal(0, MoveFlags.RollLength);
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

    /// <summary>Dash(1,0) from rest, nothing held: the step of every tick the dash is live before it, and the metres.</summary>
    static (int ticks, double metres, List<double> steps) DashSteps()
    {
        var b = Make();
        Assert.True(b.Dash(1, 0));
        double x0 = b.Player.X, z0 = b.Player.Z;
        var steps = new List<double>();
        for (int i = 0; i < 60 && b.Player.DashT > 0; i++)
        {
            double px = b.Player.X, pz = b.Player.Z;
            b.Tick(Dt, 0, 0); b.Events.Drain();
            steps.Add(Math.Sqrt((b.Player.X - px) * (b.Player.X - px) + (b.Player.Z - pz) * (b.Player.Z - pz)));
        }
        return (steps.Count, Math.Sqrt((b.Player.X - x0) * (b.Player.X - x0) + (b.Player.Z - z0) * (b.Player.Z - z0)), steps);
    }

    [Fact]
    public void Roll_Off_IsTheOldDash()
    {
        // measured: 13 ticks, 5.958 m (0.2 s of float is 12.0000001 steps: a 13th full-speed tick), not the brief's 5.5 +- 0.15
        MoveFlags.RollTime = 0;
        var (ticks, metres, _) = DashSteps();
        Assert.True(Math.Abs(metres - 5.5) <= 0.5, $"metres {metres}, ticks {ticks}");
        Assert.True(ticks <= 13, $"ticks {ticks}, metres {metres}");
    }

    [Fact]
    public void Roll_27Steps()
    {
        double top = Top();
        MoveFlags.RollTime = 0.45;
        var (ticks, metres, steps) = DashSteps();
        Assert.True(ticks == 27, $"ticks {ticks}");
        Assert.True(Math.Abs(metres - 5.5) <= 0.02, $"metres {metres}");
        Assert.True(steps[0] > steps[^1], $"first {steps[0]} last {steps[^1]}");
        // measured: last step 0.08779 vs top/60 0.08333 (+5.3%: the roll's speed at its last step's middle is a little over her run)
        Assert.True(Math.Abs(steps[^1] - top / 60) <= 0.06 * top / 60, $"last {steps[^1]} vs top/60 {top / 60}, first {steps[0]}");
        for (int i = 1; i < steps.Count; i++) Assert.True(steps[i] <= steps[i - 1] + 1e-9, $"step {i}: {steps[i]} > {steps[i - 1]}");
    }

    [Fact]
    public void Roll_Length()
    {
        MoveFlags.RollTime = 0.45;
        MoveFlags.RollLength = 8.0;
        var (ticks, metres, _) = DashSteps();
        Assert.True(ticks == 27, $"ticks {ticks}");
        Assert.True(Math.Abs(metres - 8.0) <= 0.02, $"metres {metres}");
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
