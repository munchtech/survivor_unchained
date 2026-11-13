using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-keys) Four keys and three auto slots (docs/design/BUILD_DIRECTION.md round 8; the ladder in
/// BUILD_UNLOCKS.md): keys open at levels 1/4/5/9, auto slots at 1/7/10; the basic attack is a real skill in the first key
/// (it ranks, and she may put another in its place); the auto slots run kindled through a stance change; gear's auto skills
/// stack beside them uncapped; a Union still takes two keys. SkillBook (the slots), Character.Bar (the bar a fight keys).</summary>
public sealed class KeyBarTests
{
    internal static Journey New(int level = 1, uint seed = 7)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "K", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
        j.Ch.Level = level;
        return j;
    }

    internal static Battle Fight(Journey j) => j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 3);

    [Theory]
    [InlineData(1, 1, 1)]
    [InlineData(3, 1, 1)]
    [InlineData(4, 2, 1)]
    [InlineData(5, 3, 1)]
    [InlineData(7, 3, 2)]
    [InlineData(8, 3, 2)]
    [InlineData(9, 4, 2)]
    [InlineData(10, 4, 3)]
    [InlineData(30, 4, 3)]
    public void Keys_and_auto_slots_open_on_the_ladder(int level, int keys, int autos)
    {
        Assert.Equal(keys, SkillBook.KeysAt(level));
        Assert.Equal(autos, SkillBook.AutosAt(level));
        Assert.Equal(keys + autos, SkillBook.SlotsAt(level));
        Assert.True(keys <= Weapons.MaxKeys && autos <= Weapons.AutoSlots);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(4)]
    [InlineData(5)]
    [InlineData(7)]
    [InlineData(9)]
    [InlineData(10)]
    [InlineData(12)]
    public void A_campaign_fight_keys_what_her_level_opens(int level)
    {
        var j = New(level);
        var b = Fight(j);
        var t = TaughtBuilds.Of("warden")!;
        var keys = t.Keys.Where(s => s.Level <= level).Select(s => s.Skill).ToArray();
        var autos = t.Autos.Where(s => s.Level <= level).Select(s => s.Skill).ToArray();
        Assert.Equal(SkillBook.KeysAt(level), keys.Length);
        Assert.Equal(SkillBook.AutosAt(level), autos.Length);
        for (int i = 0; i < keys.Length; i++) Assert.Equal(keys[i], b.OnSlot(i)?.Id);
        Assert.Equal(keys.Length, b.SlotsUsed);
        foreach (var id in autos)
        {
            var w = b.Weapons.Single(x => x.Id == id);
            Assert.True(w.Slot >= Weapons.MaxKeys, $"{id} on {w.Slot}");
            Assert.Equal(CastMode.Auto, w.Cast);
        }
        Assert.Equal(keys.Length + autos.Length, b.Weapons.Count);
    }

    [Fact]
    public void The_basic_attack_is_slotted_ranked_and_swappable()
    {
        var j = New(5);
        var b = Fight(j);
        var sunder = b.OnSlot(0)!;
        Assert.Equal("sunder", sunder.Id);
        Assert.True(sunder.Hold);
        // It ranks as any skill (its wick's points by day: WickBook.DayRank).
        Assert.Equal(WickBook.DayRank(j.Ch, "sunder"), sunder.Rank);
        Assert.True(sunder.Rank > 1);
        // She puts another in its key: the key keeps its number, Sunder is set down (still known).
        j.Ch.Discovered.Add("cleaver");
        Assert.True(SkillBook.Learn(j.Ch, "cleaver"));
        Assert.True(SkillBook.Swap(j.Ch, "sunder", "cleaver"));
        Assert.Equal("cleaver", j.Ch.Slotted[0]);
        Assert.Contains("sunder", j.Ch.Skills);
        var b2 = Fight(j);
        Assert.Equal("cleaver", b2.OnSlot(0)?.Id);
        Assert.DoesNotContain(b2.Weapons, w => w.Id == "sunder");
        // And back.
        Assert.True(SkillBook.Swap(j.Ch, "cleaver", "sunder"));
        Assert.Equal("sunder", Fight(j).OnSlot(0)?.Id);
    }

    [Fact]
    public void A_skill_offered_both_ways_moves_between_a_key_and_an_auto_slot()
    {
        var j = New(9);
        Fight(j);
        Assert.True(SkillBook.IsAuto(j.Ch, "groundbreaker"));
        // The keys are full (four): it cannot come off its auto slot onto one; nothing changes.
        Assert.False(SkillBook.SetAuto(j.Ch, "groundbreaker", false));
        Assert.True(SkillBook.IsAuto(j.Ch, "groundbreaker"));
        // A key freed, it can.
        SkillBook.Unslot(j.Ch, "dawnpulse");
        Assert.True(SkillBook.SetAuto(j.Ch, "groundbreaker", false));
        var b = Fight(j);
        var gb = b.Weapons.Single(w => w.Id == "groundbreaker");
        Assert.True(gb.Slot < Weapons.MaxKeys);
        Assert.Equal(CastMode.Press, gb.Cast);
        // Keyed only, never auto; auto only, never keyed.
        Assert.False(SkillBook.SetAuto(j.Ch, "heroic_leap", true));
        Assert.False(SkillBook.SetAuto(j.Ch, "rebuke", false));
    }

    [Fact]
    public void The_auto_slots_survive_a_stance_change()
    {
        var j = New(10);
        var b = Fight(j);
        Assert.NotNull(b.StanceB);
        var before = b.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).Select(w => (w.Id, w.Slot, w.Cast)).OrderBy(x => x.Slot).ToList();
        Assert.Equal(3, before.Count);
        Assert.True(b.Swap());
        Assert.True(b.OnB);
        Assert.Equal(before, b.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).Select(w => (w.Id, w.Slot, w.Cast)).OrderBy(x => x.Slot).ToList());
        Assert.True(b.Swap());
        Assert.False(b.OnB);
        Assert.Equal(before, b.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).Select(w => (w.Id, w.Slot, w.Cast)).OrderBy(x => x.Slot).ToList());
        // And when she changes the stance itself between fights.
        Assert.True(SkillBook.SetStance(j.Ch, "mace"));
        var b2 = Fight(j);
        Assert.Equal("mace", b2.StanceB!.Id);
        Assert.Equal(before.Select(x => x.Id), b2.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).OrderBy(w => w.Slot).Select(w => w.Id));
    }

    [Fact]
    public void Gear_auto_skills_stack_beside_her_auto_slots_with_no_cap()
    {
        var j = New(10);
        Fight(j);
        // Six auto skills worn (each runs itself, or is offered both ways), none of them hers.
        var worn = new List<(string Id, int Rank)> { ("rebuke", 2), ("judgement_disc", 2), ("hallowed_ring", 2), ("volley", 2), ("firepot", 2), ("arcweb", 2) };
        foreach (var (id, _) in worn) Assert.False(Weapons.KeyOnly(id), id);
        var autos = new HashSet<string>();
        var bar = Character.Bar(j.Ch, worn, autos);
        Assert.Equal(3 + worn.Count, autos.Count);
        Assert.All(worn, w => Assert.Contains(w.Id, autos));
        // In a fight: her four keys as they were, nine running themselves beyond them.
        var b = new Battle(new BattleSetup
        {
            Seed = 3, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = bar, Kindled = autos, Calling = "warden", Ability = AbilityKind.ShieldBash,
        });
        Assert.Equal(bar.Count, b.Weapons.Count);
        Assert.Equal(4, b.SlotsUsed);
        Assert.Equal(9, b.Weapons.Count(w => w.Slot >= Weapons.MaxKeys && w.Cast == CastMode.Auto));
    }

    [Fact]
    public void A_pressed_skill_on_her_gear_takes_a_free_key_and_waits_when_none_is()
    {
        var j = New(5);
        Fight(j);
        SkillBook.Unslot(j.Ch, "shield_charge");
        var autos = new HashSet<string>();
        var bar = Character.Bar(j.Ch, [("shield_charge", 3)], autos);
        Assert.Contains(bar, x => x.Id == "shield_charge");
        Assert.DoesNotContain("shield_charge", autos);
        // Keys full: a keyed-only skill worn is not carried (it never runs itself).
        var j9 = New(9);
        Fight(j9);
        Assert.True(Weapons.KeyOnly("heroic_leap"));
        SkillBook.Unslot(j9.Ch, "heroic_leap");
        j9.Ch.Discovered.Add("cleaver");
        SkillBook.Learn(j9.Ch, "cleaver");
        Assert.Equal(4, SkillBook.KeysUsed(j9.Ch));
        var bar9 = Character.Bar(j9.Ch, [("heroic_leap", 3)], autos);
        Assert.DoesNotContain(bar9, x => x.Id == "heroic_leap");
    }

    [Fact]
    public void A_union_still_takes_two_keys()
    {
        Assert.Equal(2, Weapons.SlotCost("bladestorm"));
        var b = new Battle(new BattleSetup
        {
            Seed = 3, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("cleaver", 8), ("sunder", 8), ("heroic_leap", 1), ("shield_charge", 1), ("groundbreaker", 1)],
            Kindled = ["groundbreaker"], Calling = "warden", Ability = AbilityKind.ShieldBash,
        });
        Assert.Equal(4, b.SlotsUsed);
        var u = b.GrantUnion("bladestorm")!;
        Assert.NotNull(u);
        Assert.Equal((0, 1), (u.Slot, u.Slot2));
        Assert.Equal(4, b.SlotsUsed);
        Assert.False(b.HasRoomFor("dawnpulse"));
        // In her book: with three keys used, a union has no room; with two, it has.
        var j = New(9);
        Fight(j);
        SkillBook.Unslot(j.Ch, "dawnpulse");
        Assert.Equal(3, SkillBook.KeysUsed(j.Ch));
        Assert.False(SkillBook.HasRoom(j.Ch, "bladestorm"));
        SkillBook.Unslot(j.Ch, "shield_charge");
        Assert.True(SkillBook.HasRoom(j.Ch, "bladestorm"));
    }

    [Fact]
    public void An_old_save_is_re_cut_to_keys_and_auto_slots_once()
    {
        var j = New(10);
        var ch = j.Ch;
        // A six-slot save: the taught build granted through the ninth, kindled ones on keys.
        ch.Bar = 0;
        ch.TaughtUpTo = 9;
        ch.AutoForm.Clear();
        ch.Skills.AddRange(new[] { "sunder", "groundbreaker", "heroic_leap", "shield_charge", "iron_vow", "watch_bell" }.Where(s => !ch.Skills.Contains(s)));
        ch.Slotted.Clear();
        ch.Slotted.AddRange(["sunder", "groundbreaker", "heroic_leap", "shield_charge", "iron_vow", "watch_bell"]);
        var b = Fight(j);
        Assert.Equal(TaughtBuilds.BarShape, ch.Bar);
        Assert.Equal(["sunder", "heroic_leap", "shield_charge", "dawnpulse"], Enumerable.Range(0, 4).Select(i => b.OnSlot(i)?.Id).ToArray());
        Assert.Equal(["groundbreaker", "iron_vow", "watch_bell"], b.Weapons.Where(w => w.Slot >= Weapons.MaxKeys).OrderBy(w => w.Slot).Select(w => w.Id).ToArray());
        // Once: a skill she then takes off stays off.
        SkillBook.Unslot(ch, "heroic_leap");
        Assert.DoesNotContain(Fight(j).Weapons, w => w.Id == "heroic_leap");
    }

    [Fact]
    public void Resolve_pacing_is_per_skill()
    {
        // The basic attack builds; Dawnpulse and Groundbreaker spend; the leap and the charge run on their cooldowns.
        Assert.True(Weapons.Get("sunder").Press!.Builds > 0);
        Assert.True(Weapons.Get("dawnpulse").Press!.Resolve > 0);
        Assert.True(Weapons.Get("groundbreaker").Press!.Resolve > 0);
        foreach (var id in new[] { "heroic_leap", "shield_charge" })
        {
            Assert.True((Weapons.Get(id).Press!.Resolve ?? 0) == 0, id);
            Assert.True((Weapons.Get(id).Press!.Builds ?? 0) == 0, id);
            Assert.True(Weapons.Get(id).Base.Cooldown > 0, id);
        }
    }
}
