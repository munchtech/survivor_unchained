using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-065) A blow's slow follows its damage: a dodged, leapt or blocked Hamstring lames no one,
/// and a damage-free slow asks the one control rule (Battle.ControlReaches).</summary>
public sealed class AvoidedSlowTests
{
    static Battle.EnemyBlow Hamstring(Battle b, double dmg) => new()
    {
        Delay = 0.05, Damage = dmg, Shape = TelegraphShape.Circle, Radius = 2, X = b.Player.X, Z = b.Player.Z, Slow = 0.55, SlowFor = 2, Source = "test",
    };

    static double SlowAfter(double dmg, double iframes)
    {
        var b = BattleTests.Arena(4);
        b.Blow(Hamstring(b, dmg));
        b.Player.Iframes = iframes;
        for (int i = 0; i < 6; i++) b.Tick(1 / 60.0, 0, 0);
        return b.Player.SlowT;
    }

    [Fact]
    public void A_dodged_blow_does_not_slow()
    {
        // old: HurtPlayer returned 0 through the dodge's i-frames, but 0.3 <= 0.45 so the slow still landed
        Assert.Equal(0, SlowAfter(10, 0.3));
        Assert.Equal(0, SlowAfter(0, 0.3));
    }

    [Fact]
    public void A_blow_that_lands_still_slows()
    {
        Assert.True(SlowAfter(10, 0) > 0);
        Assert.True(SlowAfter(0, 0) > 0);
    }
    [Fact]
    public void A_ring_does_not_root_her_while_she_is_beyond_control()
    {
        // (Codex audit 11 L2) old: the root asked only DashT and Leap, so i-frames from anything else still rooted her
        var b = BattleTests.Arena(7);
        b.Tell("ring", null, b.Player.X, b.Player.Z);
        b.Player.Iframes = 5;
        for (int i = 0; i < 60; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(0, b.Player.RootT);
        var c = BattleTests.Arena(7);
        c.Tell("ring", null, c.Player.X, c.Player.Z);
        for (int i = 0; i < 60; i++) c.Tick(1 / 60.0, 0, 0);
        Assert.True(c.Player.RootT > 0);
    }
}
