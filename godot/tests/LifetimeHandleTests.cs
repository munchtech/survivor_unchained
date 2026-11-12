using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-053) A creature is known by its lifetime, never its pool slot: the pool reuses the slot and the
/// object, so what a Flare or wick keeps past a tick (a poison, a ring's captive, a brand) must end when the slot is
/// spawned into again. Each test releases the creature and spawns a newcomer into the same slot.</summary>
public sealed class LifetimeHandleTests
{
    const double Dt = 1 / 60.0;

    static Enemy Replace(Battle b, Enemy gone, double x, double z)
    {
        var was = Lifetime.Of(gone);
        b.Enemies.Release(gone);
        var n = Foe(b, x, z, hp: 1e9);
        Assert.Equal(gone.Id, n.Id);
        Assert.NotEqual(was, Lifetime.Of(n));
        return n;
    }

    [Fact]
    public void A_Road_Toll_poison_ends_when_its_creatures_slot_is_reused()
    {
        var b = Carrying("the_roads_toll");
        var a = Foe(b, 2, 0, hp: 1e9);
        Cast(b);
        double before = a.Hp;
        Run(b, 0.6);
        Assert.True(a.Hp < before, "the poison is ticking on the poisoned");
        var n = Replace(b, a, 3, 0);
        Run(b, 3);
        // old code: the poison held the slot id (and the same pooled object), so it kept ticking on the newcomer
        Assert.Equal(n.MaxHp, n.Hp);
    }

    [Fact]
    public void A_Branding_burst_does_not_land_on_a_newcomer_in_its_branded_ones_slot()
    {
        var b = Carrying("the_branding");
        var a = Foe(b, 2, 0, hp: 1e9);
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Run(b, 0.6);
        Assert.True(a.Status.Has(StatusKind.Mark), "branded before the burst");
        var n = Replace(b, a, 14, 0);
        Run(b, 1.2);
        // old code: br.On == e && br.Id == e.Id held for the reused object, so the burst struck the newcomer
        Assert.Equal(n.MaxHp, n.Hp);
    }

    [Fact]
    public void The_Henge_does_not_hold_a_newcomer_in_a_released_captives_slot()
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("heroic_leap", 1)], Ability = AbilityKind.ShieldBash,
        });
        b.Calling = "warden";
        b.Lamps = new LampLoadout();
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "heroic_leap.henge", Args = new() { ["radius"] = 6, ["seconds"] = 4 } });
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Resolve.Set(100);
        var p = b.Player;
        double x0 = p.X, z0 = p.Z;
        var a = b.SpawnEnemy("footpad", x0 + 8, z0 + 1)!;
        a.Hp = a.MaxHp = 1e9;
        a.AttackT = a.RangedT = 999;
        int slot = b.Weapons.Single(w => w.Id == "heroic_leap").Slot;
        Assert.True(b.PressSkill(slot, x0 + 8, z0));
        for (double t = 0; t < 1.0; t += Dt) b.Tick(Dt, 0, 0);
        double cx = p.X, cz = p.Z;
        Assert.True(MathX.Dist(cx, cz, a.X, a.Z) < 6, "the captive is inside the ring");
        b.Enemies.Release(a);
        var n = b.SpawnEnemy("footpad", cx + 14, cz)!;
        n.Hp = n.MaxHp = 1e9;
        n.AttackT = n.RangedT = 999;
        Assert.Equal(a.Id, n.Id);
        for (double t = 0; t < 1.0; t += Dt) b.Tick(Dt, 0, 0);
        // old code: the ring's captives were slot ids, so the newcomer was dragged inside the ring (within R - radius of it)
        Assert.True(MathX.Dist(cx, cz, n.X, n.Z) > 6, "the newcomer is outside the ring, not held in it");
    }
}
