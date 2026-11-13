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
}
