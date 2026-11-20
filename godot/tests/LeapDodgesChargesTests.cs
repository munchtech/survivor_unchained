using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 19 Nov: "heroic leap should dodge charges (leaps over them)".</summary>
public sealed class LeapDodgesChargesTests
{
    const double Dt = 1 / 60.0;

    static Battle Make()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 500, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4, [Stat.CritChance] = 0, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return new Battle(new BattleSetup { Seed = 5, Collision = new CollisionWorld(120), Combat = true, Stats = s, Weapons = [] });
    }

    static double ChargeThrough(bool leaping)
    {
        var b = Make();
        var boar = b.SpawnEnemy("boar", 1.5, 0, new Battle.SpawnOpts { Level = 1 })!;
        boar.State = EnemyState.Lunging; boar.StateT = 1; boar.LungeX = -1; boar.LungeZ = 0; boar.AttackT = 0;
        if (leaping) b.Player.Leap = new Leap { T = 0, Dur = 5, X0 = b.Player.X, Z0 = b.Player.Z, X1 = b.Player.X, Z1 = b.Player.Z };
        double hp0 = b.Player.Hp;
        for (int i = 0; i < 30; i++) { b.Tick(Dt, 0, 0); b.Events.Drain(); if (!leaping) { } else b.Player.Leap!.T = 0; }
        return hp0 - b.Player.Hp;
    }

    [Fact]
    public void A_charge_through_her_mid_leap_does_nothing_but_hurts_on_the_ground()
    {
        Assert.True(ChargeThrough(false) > 0);
        Assert.Equal(0, ChargeThrough(true));
    }
}
