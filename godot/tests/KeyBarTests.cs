using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-keys; no auto slots since 22 Nov, SKILL_KINDS.md) Four pressed keys (the ladder in BUILD_UNLOCKS.md): keys
/// open at levels 1/4/5/9; the basic attack is a real skill in the first key (it ranks, and she may put another in its
/// place); gear's auto skills run beside them uncapped; a Union still takes two keys. SkillBook (the slots), Character.Bar (the bar a fight keys).</summary>
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
    [InlineData(1, 1)]
    [InlineData(3, 1)]
    [InlineData(4, 2)]
    [InlineData(5, 3)]
    [InlineData(7, 3)]
    [InlineData(8, 3)]
    [InlineData(9, 4)]
    [InlineData(10, 4)]
    [InlineData(30, 4)]
    public void Keys_open_on_the_ladder(int level, int keys)
    {
        Assert.Equal(keys, SkillBook.KeysAt(level));
        Assert.Equal(keys, SkillBook.Slots(New(level).Ch));
        Assert.True(keys <= Weapons.MaxKeys);
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
        Assert.Equal(SkillBook.KeysAt(level), keys.Length);
        for (int i = 0; i < keys.Length; i++) Assert.Equal(keys[i], b.OnSlot(i)?.Id);
        Assert.Equal(keys.Length, b.SlotsUsed);
        Assert.Equal(keys.Length, b.Weapons.Count);
        Assert.All(b.Weapons, w => Assert.NotEqual(CastMode.Auto, w.Cast));
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
    public void Gear_auto_skills_stack_beside_her_keys_with_no_cap()
    {
        var j = New(10);
        Fight(j);
        // Six auto skills worn (each runs itself, or is offered both ways), none of them hers.
        var worn = new List<(string Id, int Rank)> { ("rebuke", 2), ("volley", 2), ("firepot", 2), ("arcweb", 2), ("thornbloom", 2), ("spirit_herd", 2) };
        foreach (var (id, _) in worn) Assert.False(Weapons.KeyOnly(id), id);
        var autos = new HashSet<string>();
        var bar = Character.Bar(j.Ch, worn, autos);
        Assert.Equal(worn.Count, autos.Count);
        Assert.All(worn, w => Assert.Contains(w.Id, autos));
        // In a fight: her four keys as they were, six running themselves beyond them.
        var b = new Battle(new BattleSetup
        {
            Seed = 3, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = bar, Kindled = autos, Calling = "warden", Ability = AbilityKind.ShieldBash,
        });
        Assert.Equal(bar.Count, b.Weapons.Count);
        Assert.Equal(4, b.SlotsUsed);
        Assert.Equal(6, b.Weapons.Count(w => w.Slot >= Weapons.MaxKeys && w.Cast == CastMode.Auto));
    }

    [Fact]
    public void A_pressed_skill_on_her_gear_takes_a_free_key_and_waits_when_none_is()
    {
        var j = New(5);
        Fight(j); // (level 5: three keys, sunder, leap, Bladestorm; Shield Charge is taught at 9: she wears it, and it takes the key Bladestorm leaves)
        SkillBook.Unslot(j.Ch, "bladestorm");
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
        // (13 Nov 2026: Bladestorm is no union, one key; Butcher's Wheel, axe gyre + cleaver, is the pair that stands in)
        Assert.Equal(1, Weapons.SlotCost("bladestorm"));
        Assert.Equal(2, Weapons.SlotCost("butchers_wheel"));
        var b = new Battle(new BattleSetup
        {
            Seed = 3, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("axe_gyre", 8), ("cleaver", 8), ("heroic_leap", 1), ("shield_charge", 1)],
            Calling = "warden", Ability = AbilityKind.ShieldBash,
        });
        Assert.Equal(4, b.SlotsUsed);
        var u = b.GrantUnion("butchers_wheel")!;
        Assert.NotNull(u);
        Assert.Equal((0, 1), (u.Slot, u.Slot2));
        Assert.Equal(4, b.SlotsUsed);
        Assert.False(b.HasRoomFor("dawnpulse"));
        // In her book: with three keys used, a union has no room; with two, it has.
        var j = New(9);
        Fight(j);
        SkillBook.Unslot(j.Ch, "iron_vow");
        Assert.Equal(3, SkillBook.KeysUsed(j.Ch));
        Assert.False(SkillBook.HasRoom(j.Ch, "butchers_wheel"));
        Assert.True(SkillBook.HasRoom(j.Ch, "dawnpulse")); // (one key: it fits)
        SkillBook.Unslot(j.Ch, "heroic_leap");
        Assert.True(SkillBook.HasRoom(j.Ch, "butchers_wheel"));
    }

    [Fact]
    public void An_old_save_is_re_cut_to_the_four_keys_once()
    {
        var j = New(10);
        var ch = j.Ch;
        // A seven-slot save (keys and autos): the old build granted through the tenth.
        ch.Bar = 0;
        ch.TaughtUpTo = 10;
        var old = new[] { "sunder", "groundbreaker", "heroic_leap", "iron_vow", "bladestorm", "shield_charge", "watch_bell" };
        ch.Skills.AddRange(old.Where(s => !ch.Skills.Contains(s)));
        ch.Slotted.Clear();
        ch.Slotted.AddRange(old);
        var b = Fight(j);
        Assert.Equal(TaughtBuilds.BarShape, ch.Bar);
        Assert.Equal(["sunder", "heroic_leap", "bladestorm", "iron_vow"], Enumerable.Range(0, 4).Select(i => b.OnSlot(i)?.Id).ToArray());
        Assert.Equal(4, b.Weapons.Count);
        // Once: a skill she then takes off stays off.
        SkillBook.Unslot(ch, "heroic_leap");
        Assert.DoesNotContain(Fight(j).Weapons, w => w.Id == "heroic_leap");
    }
}
