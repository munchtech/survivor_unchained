using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-072) A creature's missile strikes like its blows: whatever its thrower may harm (her, her
/// allies, a rival faction), by the one rule target choice uses (Battle.MayHarm); never its own kind, never her if
/// its thrower is on her side.</summary>
public sealed class CreatureMissileTests
{
    static (Battle B, Projectile Pr, Enemy At) Shot(Battle.SpawnOpts? shooter, Battle.SpawnOpts? at)
    {
        var b = BattleTests.Arena(4);
        double x = b.Player.X + 30, z = b.Player.Z;
        var e = b.SpawnEnemy("risen", x - 6, z, shooter ?? new Battle.SpawnOpts())!;
        var o = b.SpawnEnemy("risen", x, z, at ?? new Battle.SpawnOpts())!;
        o.MaxHp = o.Hp = 1e6;
        var pr = b.SpawnProjectile(Side.Enemy, x, z, 10, School.Physical)!;
        pr.FiredBy(e);
        pr.Life = 2; pr.Radius = 0.5; pr.Vx = 1;
        return (b, pr, o);
    }

    [Fact]
    public void A_hostile_missile_strikes_her_ally()
    {
        // old: the enemy branch tested her alone, so a bowman's arrows flew through the reflection it was aiming at
        var (b, pr, ally) = Shot(null, new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally });
        b.Tick(1 / 60.0, 0, 0);
        Assert.False(pr.Alive);
        Assert.True(ally.Hp < ally.MaxHp);
    }

    [Fact]
    public void A_missile_spares_its_own_kind()
    {
        var (b, pr, kin) = Shot(null, null);
        b.Tick(1 / 60.0, 0, 0);
        Assert.True(pr.Alive);
        Assert.Equal(kin.MaxHp, kin.Hp);
    }

    [Fact]
    public void Her_allys_missile_never_hurts_her()
    {
        var b = BattleTests.Arena(4);
        var e = b.SpawnEnemy("risen", b.Player.X + 6, b.Player.Z, new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally })!;
        var pr = b.SpawnProjectile(Side.Enemy, b.Player.X, b.Player.Z, 10, School.Physical)!;
        pr.FiredBy(e);
        pr.Life = 2; pr.Radius = 0.5;
        b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(b.MaxHp, b.Player.Hp);
    }
}
