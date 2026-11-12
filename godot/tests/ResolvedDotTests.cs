using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-057) A share of a resolved blow (Whetstone's bleed) carries the global multipliers once, from
/// the blow: at global x2 a 30% bleed is 30% of the blow, not 60%.</summary>
public sealed class ResolvedDotTests
{
    static (double Blow, double Bled) Bleed(double global)
    {
        var b = BattleTests.Arena(3);
        b.Stats.SetBase(new Dictionary<string, double> { [Stat.MaxHealth] = 140, [Stat.PickupRadius] = 2.4, [Stat.Damage] = global });
        Assert.Equal(global, b.Stats.Get(Stat.Damage), 6);
        var e = b.SpawnEnemy("risen", 30, 30)!;
        e.MaxHp = e.Hp = 1e7;
        double hp = e.Hp;
        b.HitEnemy(e, 100, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true, Status = new StatusPayload(StatusKind.Bleed, 1, 0.3, 3) });
        double blow = hp - e.Hp;
        hp = e.Hp;
        for (int i = 0; i < 4 * 60; i++) { e.Vx = e.Vz = 0; b.TickStatus(e, 1 / 60.0); }
        return (blow, hp - e.Hp);
    }

    [Fact]
    public void Whetstones_bleed_is_its_share_of_the_blow_whatever_the_global_multiplier()
    {
        var (blow1, bled1) = Bleed(1);
        var (blow2, bled2) = Bleed(2);
        Assert.Equal(2 * blow1, blow2, 6);
        Assert.Equal(0.3 * blow1, bled1, 6);
        Assert.Equal(0.3 * blow2, bled2, 6);
    }

    /// <summary>(L1, found fixing SU-057) her side is taken once, at the blow: the global multiplier raised after the blow
    /// leaves its bleed as it was; the target's state applies at each tick: a mark on at the blow is not counted twice,
    /// one laid after it raises the ticks.</summary>
    static (double Blow, double Bled) Later(bool markAtBlow, bool markLater, double globalLater)
    {
        var b = BattleTests.Arena(3);
        b.Stats.SetBase(new Dictionary<string, double> { [Stat.MaxHealth] = 140, [Stat.PickupRadius] = 2.4, [Stat.Damage] = 1 });
        var e = b.SpawnEnemy("risen", 30, 30)!;
        e.MaxHp = e.Hp = 1e7;
        var mark = new StatusPayload(StatusKind.Mark, 1, 1, 10);
        if (markAtBlow) b.ApplyStatus(e, mark, 0);
        double hp = e.Hp;
        b.HitEnemy(e, 100, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true, Status = new StatusPayload(StatusKind.Bleed, 1, 0.3, 3) });
        double blow = hp - e.Hp;
        hp = e.Hp;
        if (markLater) b.ApplyStatus(e, mark, 0);
        if (globalLater != 1) b.Stats.SetBase(new Dictionary<string, double> { [Stat.MaxHealth] = 140, [Stat.PickupRadius] = 2.4, [Stat.Damage] = globalLater });
        for (int i = 0; i < 4 * 60; i++) { e.Vx = e.Vz = 0; b.TickStatus(e, 1 / 60.0); }
        return (blow, hp - e.Hp);
    }

    [Fact]
    public void Her_side_counts_once_at_the_blow_and_the_target_state_at_each_tick()
    {
        var (blow, bled) = Later(false, false, 1);
        Assert.Equal(0.3 * blow, bled, 6);
        // global damage doubled after the blow: the bleed is the blow's
        var (_, bledG) = Later(false, false, 2);
        Assert.Equal(bled, bledG, 6);
        // a mark on at the blow (and still on): the bleed is 30% of the marked blow, the mark not counted twice
        var (blowM, bledM) = Later(true, false, 1);
        Assert.Equal(1.3 * blow, blowM, 6);
        Assert.Equal(0.3 * blowM, bledM, 6);
        // a mark laid after the blow: the ticks take it
        var (_, bledL) = Later(false, true, 1);
        Assert.Equal(1.3 * bled, bledL, 6);
    }
}
