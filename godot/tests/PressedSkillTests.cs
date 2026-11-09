using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Pressed and channelled skills by data (skills.json "cast"), and the slots counted, not the weapons: a
/// union holds both its parts' slots and answers either key (the owner, 8 Nov). Sim/PressedSkills.cs, Sim/Weapons.cs.</summary>
public class PressedSkillTests
{
    const double Dt = 1 / 60.0;

    static void Tick(Battle b, double seconds, Action? each = null)
    {
        for (double t = 0; t < seconds - 1e-9; t += Dt) { each?.Invoke(); b.Tick(Dt, 0, 0); b.Events.Drain(); }
    }

    static Enemy Dummy(Battle b, double dx, double dz)
    {
        var e = b.SpawnEnemy("footpad", b.Player.X + dx, b.Player.Z + dz)!;
        e.Hp = e.MaxHp = 1e7;
        e.AttackT = 999;
        return e;
    }

    [Fact]
    public void Every_skill_but_the_wardens_four_pressed_ones_still_fires_itself()
    {
        string[] pressed = ["heroic_leap", "shield_charge", "bladestorm", "iron_vow"];
        foreach (var w in Weapons.All.Values.Where(w => !pressed.Contains(w.Id)))
        {
            Assert.Equal(CastMode.Auto, w.Cast);
            foreach (var e in w.Evolutions) Assert.Null(e.Cast);
        }
        Assert.Equal(CastMode.Press, Weapons.Get("heroic_leap").Cast);
        Assert.Equal(CastMode.Press, Weapons.Get("shield_charge").Cast);
        Assert.Equal(CastMode.Press, Weapons.Get("iron_vow").Cast);
        Assert.Equal(CastMode.Channel, Weapons.Get("bladestorm").Cast);
    }

    [Fact]
    public void The_cast_key_round_trips_and_an_auto_skill_writes_none()
    {
        var once = SkillsJson.File;
        string written = SkillsJson.Write(once);
        Assert.Contains("\"cast\": \"channel\"", written);
        Assert.Equal(4, written.Split("\"cast\"").Length - 1);
        Assert.Equal(CastMode.Channel, SkillsJson.Parse(written).Skills.Single(s => s.Id == "bladestorm").Cast);
    }

    [Fact]
    public void An_auto_skill_ignores_its_key_and_fires_on_its_own()
    {
        var b = BattleTests.Arena(3, ("cleaver", 1));
        Dummy(b, 1.5, 0);
        Assert.False(b.PressSkill(0, b.Player.X + 3, b.Player.Z));
        Tick(b, 2);
        Assert.True(b.Weapons[0].Casts > 0);
    }

    [Fact]
    public void A_union_takes_two_slots_and_never_makes_a_seventh()
    {
        var b = BattleTests.Arena(4, ("cleaver", 8), ("sunder", 8), ("oathblade", 1), ("dawnpulse", 1), ("volley", 1), ("arcweb", 1));
        Assert.Equal(6, b.SlotsUsed);
        var u = b.GrantUnion("bladestorm")!;
        Assert.NotNull(u);
        Assert.Equal(5, b.Weapons.Count);
        Assert.Equal(6, b.SlotsUsed);
        // It sits on its parts' keys: cleaver's slot 0 and sunder's slot 1.
        Assert.Equal((0, 1), (u.Slot, u.Slot2));
        Assert.Same(u, b.OnSlot(0));
        Assert.Same(u, b.OnSlot(1));
        Assert.Null(b.AddWeapon("knifestorm"));
        // A slot freed is one slot, and the others keep their keys.
        b.RemoveWeapon("arcweb");
        Assert.Equal(5, b.SlotsUsed);
        Assert.Equal("volley", b.OnSlot(4)!.Id);
        Assert.NotNull(b.AddWeapon("knifestorm"));
        Assert.Equal(5, b.Weapons.Single(w => w.Id == "knifestorm").Slot);
    }

    [Fact]
    public void Unite_puts_the_union_on_both_parts_slots()
    {
        var b = BattleTests.Arena(1, ("oathblade", 1), ("judgement_disc", 8), ("volley", 1), ("dawnpulse", 8));
        b.Evolve("judgement_disc", "reckoning", chest: true);
        b.Evolve("dawnpulse", Weapons.Get("dawnpulse").Evolutions[0].Id, chest: true);
        var u = b.Unite("dawns_judgement")!;
        // Slot is part A's key (Dawnpulse's), Slot2 part B's (the disc's).
        Assert.Equal((3, 1), (u.Slot, u.Slot2));
        Assert.Equal(4, b.SlotsUsed);
        Assert.Equal(0, b.OnSlot(0)!.Slot);
        Assert.Equal("volley", b.OnSlot(2)!.Id);
    }

    [Fact]
    public void A_full_build_with_a_union_is_offered_no_new_skill()
    {
        var b = BattleTests.Arena(7, ("cleaver", 8), ("sunder", 8), ("oathblade", 2), ("dawnpulse", 2), ("volley", 2), ("arcweb", 2));
        b.GrantUnion("bladestorm");
        for (int i = 0; i < 20; i++)
            Assert.DoesNotContain(LevelUp.Draft(b), o => o.Kind == OfferKind.Weapon);
    }

    [Fact]
    public void A_union_whose_skill_shares_its_id_keeps_its_access_and_unites()
    {
        Assert.Equal(["warden"], Weapons.AccessOf("bladestorm")!.ToArray());
        Assert.True(Weapons.CanCarry("warden", "bladestorm"));
        Assert.False(Weapons.CanCarry("reaver", "bladestorm"));
        Assert.Equal(2, Weapons.SlotCost("bladestorm"));
        Assert.Equal(1, Weapons.SlotCost("cleaver"));
        // Sunder has no evolution yet (a placeholder union): Unite asks both evolved, so only a grant makes it.
        var b = BattleTests.Arena(2, ("cleaver", 8), ("sunder", 8));
        b.Evolve("cleaver", "whirlwind", chest: true);
        Assert.Null(b.Unite("bladestorm"));
        Assert.NotNull(b.GrantUnion("bladestorm"));
    }

    [Fact]
    public void A_channel_waits_for_its_key_runs_while_held_and_its_cooldown_starts_when_it_ends()
    {
        var b = BattleTests.Arena(5, ("oathblade", 1));
        b.RemoveWeapon("oathblade");
        var w = b.GrantUnion("bladestorm")!;
        var foe = Dummy(b, 1.2, 0);
        // Never on its own: ready, a foe in reach, no key.
        Tick(b, 2);
        Assert.Equal(0, w.Casts);
        Assert.Equal(0, w.Timer);
        // Held on its first key (Bladestorm's spin key; its second is the break).
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, foe.X, foe.Z));
        Assert.True(w.Channeling);
        Assert.Equal(foe.X, b.SkillAim!.Value.X);
        Assert.False(b.PressSkill(w.Slot, foe.X, foe.Z));
        // (The foe is pinned where it stood: the storm's knockback would carry it out of reach.)
        Tick(b, 1.0, () => { b.HoldSkill(w.Slot, true); foe.X = b.Player.X + 1.2; foe.Z = b.Player.Z; });
        int during = w.Casts;
        Assert.True(during >= 3, $"{during} firings in a held second");
        Assert.True(foe.Hp < foe.MaxHp);
        // Let go: it ends, and only now its cooldown runs.
        b.HoldSkill(w.Slot, false);
        Tick(b, Dt);
        Assert.False(w.Channeling);
        Assert.True(w.Timer > 5, $"timer {w.Timer}");
        Assert.False(b.PressSkill(w.Slot, foe.X, foe.Z));
        Tick(b, 1);
        Assert.Equal(during, w.Casts);
    }

    [Fact]
    public void A_channel_held_on_ends_at_its_longest()
    {
        var b = BattleTests.Arena(6, ("oathblade", 1));
        b.RemoveWeapon("oathblade");
        var w = b.GrantUnion("bladestorm")!;
        Dummy(b, 1.2, 0);
        Tick(b, 2); // (a union comes in with its clock running: let it settle ready)
        b.HoldSkill(w.Slot, true);
        Assert.True(b.PressSkill(w.Slot, b.Player.X + 2, b.Player.Z));
        Tick(b, w.ChannelMax - 0.1, () => b.HoldSkill(w.Slot, true));
        Assert.True(w.Channeling);
        Tick(b, 0.2, () => b.HoldSkill(w.Slot, true));
        Assert.False(w.Channeling);
        Assert.True(w.Timer > 0);
    }

    [Fact]
    public void A_granted_union_comes_back_with_a_checkpoint()
    {
        var b = BattleTests.Arena(8, ("cleaver", 8), ("sunder", 8));
        b.GrantUnion("bladestorm");
        var snap = b.Snapshot();
        b.Restore(snap);
        Assert.Equal(["bladestorm"], b.Weapons.Select(w => w.Id).ToArray());
        Assert.Equal(2, b.SlotsUsed);
    }

    [Fact]
    public void The_debug_grants_put_skills_unions_and_steps_in()
    {
        var b = BattleTests.Arena(9, ("oathblade", 1));
        var said = DevGrants.Apply(b, "cleaver:4,sunder", "bladestorm", "long_stride,second_wind_pip,nope");
        Assert.Equal(["oathblade", "bladestorm"], b.Weapons.Select(w => w.Id).ToArray());
        Assert.Equal(3, b.SlotsUsed);
        Assert.Equal(["long_stride", "second_wind_pip"], b.DashSteps.ToArray());
        Assert.Contains(said, l => l.Contains("nope") && l.Contains("not taken"));
    }

    [Fact]
    public void Day_skills_count_a_union_as_two()
    {
        Assert.Equal(6, Weapons.SlotsOf(["bladestorm", "oathblade", "volley", "arcweb", "dawnpulse"]));
    }
}

/// <summary>A press skill (Shield Charge): never on its own, once on a press when ready, its cooldown then.</summary>
public class PressSkillTests
{
    [Fact]
    public void A_press_skill_fires_once_on_a_press_when_ready()
    {
        var b = BattleTests.Arena(10, ("shield_charge", 1));
        var w = b.Weapons.Single();
        w.Timer = 0;
        var foe = b.SpawnEnemy("footpad", b.Player.X + 3, b.Player.Z)!;
        foe.Hp = foe.MaxHp = 1e7; foe.AttackT = 999;
        for (int i = 0; i < 60; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
        Assert.Equal(0, w.Casts);
        Assert.Equal(0, w.Timer);
        Assert.True(b.PressSkill(w.Slot, foe.X, foe.Z));
        Assert.Equal(1, w.Casts);
        Assert.True(w.Timer > 6);
        for (int i = 0; i < 30; i++) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
        Assert.False(b.PressSkill(w.Slot, foe.X, foe.Z));
        Assert.Equal(1, w.Casts);
    }
}
