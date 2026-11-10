using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3 MR 3 clock) Every wait is its written length, on average to the instant, hasted ones too (no whole-step
/// breakpoints): held at dt = 1/60 for 220 blows or more, the instants a skill's blows start are the wait apart (within
/// 1e-9 over the run), and each lands on the step its instant falls in (never a step late). Three clocks: the chained
/// cut (SwingChain's PeriodEnd and overshoot), the unchained deferred press (Battle.DeferBlow backdated by Firing.Late,
/// re-armed at the contact from the press's instant: Firing.LandBlow), and the bare countdown (an arena skill's timer
/// fire: Firing.CountDown, the next wait carried from the instant it ran out). Written waits 1.05 and 1.60 (whole steps:
/// 63, 96), and hasted 1.05 / 1.25 = 0.84 (50.4 steps) and 1.60 / 1.15 = 1.3913 (83.48 steps).</summary>
public sealed class ClockTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public ClockTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    const int Blows = 220;

    public enum Clock { Chained, Deferred, Bare }

    /// <summary>Holds the skill on a foe that does not die until `Blows` blows have started; their instants and steps.</summary>
    static (List<double> At, List<int> Step, List<double> Gap) Run(Clock clock, double wait)
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = clock != Clock.Bare, Stats = BattleTests.BaseStats(),
            Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
        });
        b.Calling = "warden";
        var w = b.Weapons[0];
        if (clock == Clock.Chained) w.Press = w.Press!.WithChain(new ChainDef { Grace = 0.40, Recover = 18, Period = 0.70 });
        else if (w.Press != null) w.Press = w.Press.WithChain(null);
        if (clock == Clock.Bare) Assert.False(w.Pressed);
        // (the wait set through the skill's own cooldown factor, as a haste would)
        w.Mods.Cooldown *= wait / Firing.CooldownOf(b, w);
        Assert.Equal(wait, Firing.CooldownOf(b, w), 12);
        w.Timer = 0;
        var e = b.SpawnEnemy("footpad", 2, 0)!;
        e.Hp = e.MaxHp = 1e12;
        e.AttackT = e.RangedT = 999;
        var at = new List<double>();
        var step = new List<int>();
        // each gap's own written length: the wait, or a chained cut's period (its share of the wait; a heavy's longer)
        var gap = new List<double>();
        double period = wait;
        AttackAnim? last = null;
        for (int i = 1; at.Count < Blows && i < (int)(Blows * (wait + 1) * 60); i++)
        {
            if (clock != Clock.Bare) b.HoldSkill(w.Slot, true, e.X, e.Z);
            e.X = 2; e.Z = 0; e.Vx = e.Vz = 0; e.Hp = e.MaxHp;
            b.Player.X = b.Player.Z = 0; b.Player.Vx = b.Player.Vz = 0;
            b.Tick(Dt, 0, 0);
            bool fired = false;
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Slash) fired = true;
            if (clock == Clock.Bare)
            {
                // the timer fire: its instant is where its next wait runs from (now + what is left - the wait)
                if (fired) { at.Add(b.Time + w.Timer - wait); step.Add(i); gap.Add(wait); }
            }
            else if (b.Player.AttackAnim is { } a && !ReferenceEquals(a, last) && a.Weapon == w.Id)
            {
                last = a;
                at.Add(a.T); step.Add(i); gap.Add(period);
            }
            if (w.Chain is { } c) period = c.PeriodEnd - c.StartAt;
        }
        Assert.Equal(Blows, at.Count);
        return (at, step, gap);
    }

    [Theory]
    [InlineData(Clock.Chained, 1.05)]
    [InlineData(Clock.Chained, 1.60)]
    [InlineData(Clock.Chained, 1.05 / 1.25)]
    [InlineData(Clock.Chained, 1.60 / 1.15)]
    [InlineData(Clock.Deferred, 1.05)]
    [InlineData(Clock.Deferred, 1.60)]
    [InlineData(Clock.Deferred, 1.05 / 1.25)]
    [InlineData(Clock.Deferred, 1.60 / 1.15)]
    [InlineData(Clock.Bare, 1.05)]
    [InlineData(Clock.Bare, 1.60)]
    [InlineData(Clock.Bare, 1.05 / 1.25)]
    [InlineData(Clock.Bare, 1.60 / 1.15)]
    public void Steps_per_blow_are_the_written_wait(Clock clock, double wait)
    {
        var (at, step, gap) = Run(clock, wait);
        double w = wait;
        // (from the second blow: the first starts on the hold's first step, a whole step); gap[k] is blow k-1's own length
        int n = at.Count - 2;
        double written = gap.Skip(2).Sum();
        double mean = (at[^1] - at[1]) / written;
        double steps = (step[^1] - step[1]) / (written * 60);
        double worst = 0;
        for (int k = 1; k < at.Count; k++)
        {
            // each blow starts on the step its instant falls in: step k ends at k * Dt, the instant inside (k-1, k] * Dt
            double into = step[k] * Dt - at[k];
            worst = Math.Max(worst, into);
            Assert.True(into >= -1e-9 && into < Dt + 1e-9, $"{clock} {w:F4}: blow {k} at {at[k]:F6} on step {step[k]} ({into / Dt:F4} of a step)");
        }
        output.WriteLine($"{clock} wait {w:F4} ({w * 60:F3} steps): {n} gaps, instants {mean:F12} of the wait, steps per blow {steps * w * 60:F4} ({steps:F6} of the written), latest start {worst / Dt:F4} of a step");
        Assert.True(Math.Abs(mean - 1) <= 1e-9, $"{clock} {w:F4}: {mean:F12}");
        Assert.True(Math.Abs(steps - 1) <= 1 / (written * 60) + 1e-9, $"{clock} {w:F4}: steps {steps:F6} of the written");
    }
}
