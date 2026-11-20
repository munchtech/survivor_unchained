using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

public sealed class ResolveStartFloorTests
{
    [Fact]
    public void A_new_battle_starts_her_resolve_at_the_fade_floor()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double> { [Stat.MaxHealth] = 100, [Stat.MoveSpeed] = 5, [Stat.Luck] = 1 });
        var b = new Battle(new BattleSetup { Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Calling = "warden", Stats = s, Weapons = [] });
        Assert.True(b.Resolve.On);
        b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(ResolveMeter.FadeFloor, b.Resolve.Value);
        Assert.Equal(4, ResolveMeter.FadeFloor);
    }
}
