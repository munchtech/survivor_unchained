using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-060) A protected boss (TakenMul 0, between phases) takes nothing: no chip, no damage events or
/// accounting, no statuses; the blow shows "immune". A mechanic opts in by name to still hear it (the Barrow Lord's laying).</summary>
public sealed class ProtectedBossTests
{
    static (Battle B, Enemy E, WeaponInst W) Protected()
    {
        var b = BattleTests.Arena(4, ("cleaver", 1));
        var e = b.SpawnEnemy("risen", 3, 0)!;
        e.Boss = e.Elite = true;
        e.MaxHp = e.Hp = 1000;
        e.TakenMul = 0;
        b.Events.Drain();
        return (b, e, b.Weapons.Single(x => x.Id == "cleaver"));
    }

    [Fact]
    public void A_protected_boss_takes_no_chip_no_events_no_accounting_and_no_statuses()
    {
        var (b, e, w) = Protected();
        int heard = 0;
        b.Hooks.OnBossHit = (_, _, _) => heard++;
        double got = b.HitEnemy(e, 200, School.Physical, [Tag.Physical], new HitOpts { Weapon = w, Status = new StatusPayload(StatusKind.Bleed, 1, 0.5, 3) });
        b.ApplyStatus(e, new StatusPayload(StatusKind.Poison, 1, 0.5, 3), 200);
        Assert.Equal(0, got);
        Assert.Equal(1000, e.Hp);
        Assert.Equal(0, w.DamageDealt);
        Assert.False(e.Status.Has(StatusKind.Bleed));
        Assert.False(e.Status.Has(StatusKind.Poison));
        Assert.Equal(0, heard);
        var ev = b.Events.Drain();
        Assert.Empty(ev.OfType<Ev.Hit>());
        Assert.Equal(e.Id, Assert.Single(ev.OfType<Ev.Immune>()).Target);
    }

    [Fact]
    public void A_mechanic_named_to_hear_still_hears_the_hit_and_nothing_lands()
    {
        var (b, e, w) = Protected();
        School? heard = null;
        b.Hooks.OnBossHit = (_, s, d) => { heard = s; Assert.Equal(0, d); };
        e.HearsWhileProtected = "barrow_lord.laying";
        b.HitEnemy(e, 200, School.Holy, [Tag.Holy], new HitOpts { Weapon = w });
        Assert.Equal(School.Holy, heard);
        Assert.Equal(1000, e.Hp);
        Assert.Empty(b.Events.Drain().OfType<Ev.Hit>());
    }
}
