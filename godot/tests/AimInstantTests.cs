using System;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(A1 lead 21) The sim's aim, blow and reversal stay instant; her eased turn is view only (PlayerView.TurnTo, HerCarriage.Aim).</summary>
public sealed class AimInstantTests
{
    readonly Xunit.Abstractions.ITestOutputHelper output;
    public AimInstantTests(Xunit.Abstractions.ITestOutputHelper output) => this.output = output;

    const double Dt = 1 / 60.0;
    /// <summary>Measured today (see Reversal): steps from stick (-1,0) to Vx &lt; 0.</summary>
    const int ReversalSteps = 3;

    static (Battle B, WeaponInst W) Make()
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
        });
        var w = b.Weapons[0];
        w.Timer = 0;
        return (b, w);
    }

    static void Run(Battle b, int steps, double sx, double sz) { for (int i = 0; i < steps; i++) b.Tick(Dt, sx, sz); }

    void AimAt(double dx, double dz)
    {
        var (b, w) = Make();
        Run(b, 60, 1, 0);
        Assert.True(Math.Abs(b.Player.Vx) > 3, $"Vx {b.Player.Vx}");
        b.Events.Drain();
        w.Timer = 0;
        b.Player.AttackAnim = null;
        double ax = b.Player.X + dx, az = b.Player.Z + dz;
        b.HoldSkill(w.Slot, true, ax, az);
        double px = b.Player.X, pz = b.Player.Z;
        for (int s = 1; s <= 2; s++)
        {
            px = b.Player.X; pz = b.Player.Z;
            b.HoldSkill(w.Slot, true, ax, az);
            b.Tick(Dt, 1, 0);
            if (b.Player.AttackAnim is { } a)
            {
                Assert.Equal(Math.Atan2(az - b.Player.Z, ax - b.Player.X), a.Angle, 1e-6);
                return;
            }
        }
        Assert.Fail("no AttackAnim within 2 steps");
    }

    [Fact] public void PressToSideAimsInstantlyWhileRunning() => AimAt(0, 3);

    [Fact] public void PressBehindAimsInstantlyWhileRunning() => AimAt(-3, 0);

    double RunBlow(bool press)
    {
        var (b, w) = Make();
        Run(b, 60, 1, 0);
        var e = b.SpawnEnemy("footpad", b.Player.X, b.Player.Z + 1.2)!;
        e.Hp = e.MaxHp = 1e9; e.AttackT = e.RangedT = 999;
        double hp0 = e.Hp;
        for (int i = 0; i < 60; i++)
        {
            e.X = b.Player.X; e.Z = b.Player.Z + 1.2; e.Vx = e.Vz = 0; e.AttackT = e.RangedT = 999;
            if (press) b.HoldSkill(w.Slot, true, e.X, e.Z);
            b.Tick(Dt, 1, 0);
        }
        return hp0 - e.Hp;
    }

    [Fact]
    public void BlowLandsWhereAimedWhileRunning()
    {
        // (the foe rides at her side, 1.2 m at 90 degrees, so her running does not carry her off it)
        double hit = RunBlow(true), none = RunBlow(false);
        output.WriteLine($"damage pressed {hit}, unpressed {none}");
        Assert.True(hit > 0);
        Assert.Equal(0, none);
    }

    [Fact]
    public void TravelReversalIsInstant()
    {
        var (b, _) = Make();
        Run(b, 60, 1, 0);
        Assert.True(b.Player.Vx > 3);
        int n = 0;
        while (b.Player.Vx >= 0 && n < 6) { b.Tick(Dt, -1, 0); n++; }
        output.WriteLine($"reversal steps: {n} (Vx {b.Player.Vx})");
        Assert.True(b.Player.Vx < 0);
        Assert.True(n <= ReversalSteps + 1, $"{n} steps");
    }
}
