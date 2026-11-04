using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her priority target (H1 item 4): the hovered foe is taken first within reach, the pick prefers the big one
/// under the pointer, and the pad's pick follows the right stick.</summary>
public class TargetingTests
{
    /// <summary>A foe stood where asked, up and in the battle's spatial index (it is rebuilt each tick).</summary>
    static Enemy Walk(Battle b, string def, double x, double z, bool elite = false)
    {
        var e = b.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Elite = elite, Style = SpawnStyle.Walk })!;
        e.Speed = 0;
        b.Tick(1 / 60.0, 0, 0);
        return e;
    }

    [Fact]
    public void PriorityWinsWithinReachOnly()
    {
        var b = BattleTests.Arena(2);
        var near = Walk(b, "risen", b.Player.X + 3, b.Player.Z);
        var far = Walk(b, "risen", b.Player.X - 6, b.Player.Z);
        Assert.Equal(near.Id, b.NearestHostile(b.Player.X, b.Player.Z, 10)!.Id);
        b.Priority = far.Id;
        Assert.Equal(far.Id, b.NearestHostile(b.Player.X, b.Player.Z, 10)!.Id);
        // Out of the reach asked: the nearest, as before.
        Assert.Equal(near.Id, b.NearestHostile(b.Player.X, b.Player.Z, 4)!.Id);
        // A filter that refuses it: the nearest that passes.
        Assert.Equal(near.Id, b.NearestHostile(b.Player.X, b.Player.Z, 10, e => e.Id != far.Id)!.Id);
        far.Alive = false;
        Assert.Equal(near.Id, b.NearestHostile(b.Player.X, b.Player.Z, 10)!.Id);
    }

    [Fact]
    public void PointerPrefersTheChampionUnderIt()
    {
        var b = BattleTests.Arena(3);
        double x = b.Player.X + 8, z = b.Player.Z;
        var fodder = Walk(b, "risen", x + 0.2, z);
        var champ = Walk(b, "risen_warrior", x - 0.7, z, elite: true);
        Assert.Equal(champ.Id, Targeting.AtPointer(b, x, z)!.Id);
        Assert.Null(Targeting.AtPointer(b, x + 6, z + 6));
        Assert.Equal(fodder.Id, Targeting.AtPointer(b, x + 1.0, z)!.Id);
    }

    [Fact]
    public void PadPickFollowsTheStick()
    {
        var b = BattleTests.Arena(4);
        var east = Walk(b, "risen", b.Player.X + 7, b.Player.Z);
        var north = Walk(b, "risen", b.Player.X, b.Player.Z + 5);
        Assert.Equal(east.Id, Targeting.AlongStick(b, 1, 0)!.Id);
        Assert.Equal(north.Id, Targeting.AlongStick(b, 0, 1)!.Id);
        Assert.Null(Targeting.AlongStick(b, -1, 0));
        Assert.Null(Targeting.AlongStick(b, 0.1, 0.1));
    }
}
