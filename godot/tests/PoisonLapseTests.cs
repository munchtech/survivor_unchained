using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-079) Her poison's rate is the worst of the live poison's: one that ran out or was cured keeps
/// no rate, so a weak bite after it poisons at its own.</summary>
public sealed class PoisonLapseTests
{
    [Fact]
    public void A_cured_poison_leaves_no_rate_for_the_next_bite()
    {
        // old: PoisonDps = Max(old, new) outlived the cure, so the weak bite poisoned at the strong one's rate
        var b = BattleTests.Arena(4);
        b.Rules.HitPoison = true;
        var p = b.Player;
        p.Hp = b.MaxHp;
        var strong = b.SpawnEnemy("risen", p.X + 20, p.Z)!; strong.Damage = 50;
        var weak = b.SpawnEnemy("risen", p.X - 20, p.Z)!; weak.Damage = 5;
        b.HurtPlayer(1, School.Physical, "test", strong);
        Assert.Equal(6, p.PoisonDps, 6);
        p.PoisonT = 0;   // the antidote (Journey.UseItem's cure)
        p.Iframes = 0;
        b.HurtPlayer(1, School.Physical, "test", weak);
        Assert.Equal(0.6, p.PoisonDps, 6);
        // while it lasts, the worst is kept
        p.Iframes = 0;
        b.HurtPlayer(1, School.Physical, "test", strong);
        Assert.Equal(6, p.PoisonDps, 6);
    }
}
