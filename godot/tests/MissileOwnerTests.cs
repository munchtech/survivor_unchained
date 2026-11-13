using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-056, SU-053) An enemy missile knows its thrower by lifetime and carries what it needs at
/// impact from the moment it was fired: a slot reused in flight lends the newcomer's bite, credit or aim to nothing.</summary>
public sealed class MissileOwnerTests
{
    static (Battle B, Projectile Pr) Fired(string thrower)
    {
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy(thrower, 20, 20)!;
        var pr = b.SpawnProjectile(Side.Enemy, b.Player.X, b.Player.Z, 10, School.Physical)!;
        pr.FiredBy(e);
        pr.Life = 2; pr.Radius = 0.5;
        b.Enemies.Release(e);
        return (b, pr);
    }

    [Fact]
    public void A_slot_reused_in_flight_lends_the_newcomer_neither_bite_nor_credit()
    {
        // old: Enemies.Items[OwnerId] at impact is the poison-biting newcomer: she is poisoned and it is her LastKiller
        var (b, pr) = Fired("risen");
        var newcomer = b.SpawnEnemy("mb_blight_mother", 25, 25)!;
        Assert.Equal(pr.OwnerId, newcomer.Id);
        b.Tick(1 / 60.0, 0, 0);
        Assert.False(pr.Alive);
        Assert.True(b.Player.Hp < b.MaxHp);
        Assert.Equal(0, b.Player.PoisonT);
        Assert.Null(b.Player.LastKiller);
    }

    [Fact]
    public void A_dead_throwers_missile_still_carries_its_bite()
    {
        // old: a thrower no longer alive passed no source, so its missile's poison was lost
        var (b, pr) = Fired("mb_blight_mother");
        b.Tick(1 / 60.0, 0, 0);
        Assert.False(pr.Alive);
        Assert.True(b.Player.PoisonT > 0);
    }

    [Fact]
    public void Her_last_killer_is_not_whatever_took_its_slot()
    {
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy("risen", 20, 20)!;
        b.Player.LastKiller = e;
        Assert.Same(e, b.Player.LastKiller);
        b.Enemies.Release(e);
        var newcomer = b.SpawnEnemy("risen", 25, 25)!;
        Assert.Same(e, newcomer);
        Assert.Null(b.Player.LastKiller);
    }
}
