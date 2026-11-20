using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 19 Nov: Heroic Leap "leaps over" charges; and she cannot shove a boss by running into him.</summary>
public sealed class BodyPushTests
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

    [Fact]
    public void Walking_into_a_boss_does_not_move_him()
    {
        var b = Make();
        var boss = b.SpawnEnemy("ford_warden", 4, 0, new Battle.SpawnOpts { Level = 1 })!;
        boss.Speed = 0; double x0 = boss.X, z0 = boss.Z;
        for (int i = 0; i < 300; i++) { b.Tick(Dt, 1, 0); b.Events.Drain(); }
        Assert.True(System.Math.Sqrt((boss.X - x0) * (boss.X - x0) + (boss.Z - z0) * (boss.Z - z0)) < 0.1);
        Assert.True(b.Player.X < boss.X);
    }

    [Fact]
    public void Walking_into_a_wolf_moves_it_less_than_her()
    {
        var b = Make();
        var wolf = b.SpawnEnemy("wolf", 1.0, 0, new Battle.SpawnOpts { Level = 1 })!;
        double x0 = wolf.X, px0 = b.Player.X;
        b.Tick(Dt, 1, 0);   // one step into it
        Assert.True(wolf.X - x0 < b.Player.X - px0 + 1e-9 || b.Player.X - px0 <= 0);
        Assert.True(Battle.BodyYield(wolf) <= 0.3);
        Assert.True(b.Player.Radius + wolf.Radius <= wolf.X - b.Player.X + 1e-6);
    }
}
