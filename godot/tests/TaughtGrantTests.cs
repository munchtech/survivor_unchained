using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3) The taught build is what a campaign warden carries (taught_builds.json; Content/TaughtBuilds.Grant):
/// the level-1 slots from the first campaign fight, each later slot at its level, in its taught form, the grip on key 0.</summary>
public sealed class TaughtGrantTests
{
    static Journey New(uint seed = 7)
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
    }

    static Battle Fight(Journey j) => j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 3);

    static string? Key(Battle b, int slot) => b.OnSlot(slot)?.Id;

    [Theory]
    [InlineData(1, new[] { "sunder", "groundbreaker" })]
    [InlineData(4, new[] { "sunder", "groundbreaker", "heroic_leap" })]
    [InlineData(5, new[] { "sunder", "groundbreaker", "heroic_leap", "shield_charge" })]
    [InlineData(9, new[] { "sunder", "groundbreaker", "heroic_leap", "shield_charge", "iron_vow", "watch_bell" })]
    public void A_new_warden_carries_the_taught_build_of_her_level(int level, string[] keys)
    {
        var j = New();
        j.Ch.Level = level;
        var b = Fight(j);
        Assert.True(b.Campaign);
        Assert.Equal(keys, j.Ch.Slotted.Take(keys.Length).ToArray());
        for (int i = 0; i < keys.Length; i++) Assert.Equal(keys[i], Key(b, i));
        var t = TaughtBuilds.Of("warden")!;
        foreach (var s in t.Slots.Where(s => s.Level <= level))
        {
            var w = b.Weapons.First(x => x.Id == s.Skill);
            if (s.Cast == "hold") Assert.True(w.Hold, s.Skill);
            else if (s.Cast == "kindle") Assert.Equal(CastMode.Auto, w.Cast);
            else Assert.Equal(CastMode.Press, w.Cast);
        }
        Assert.DoesNotContain(t.Slots, s => s.Level > level && b.Weapons.Any(w => w.Id == s.Skill));
    }

    [Fact]
    public void A_level_reached_in_a_campaign_fight_teaches_its_slot_into_it()
    {
        var j = New();
        j.Ch.Level = 3;
        var b = Fight(j);
        b.Events.Drain().ToList();
        Assert.DoesNotContain(b.Weapons, w => w.Id == "heroic_leap");
        j.Ch.Level = 4;
        var got = j.Teach(b);
        Assert.Equal("heroic_leap", Assert.Single(got).Skill);
        var leap = b.Weapons.First(w => w.Id == "heroic_leap");
        Assert.Equal(CastMode.Press, leap.Cast);
        var ev = Assert.Single(b.Events.Drain().OfType<Ev.Taught>());
        Assert.Equal(("heroic_leap", leap.Slot, 4), (ev.Skill, ev.Slot, ev.Level));
        // Taught once: again at the same level, nothing.
        Assert.Empty(j.Teach(b));
    }

    [Fact]
    public void A_taught_skill_taken_off_is_not_put_back()
    {
        var j = New();
        j.Ch.Level = 4;
        Fight(j);
        SkillBook.Unslot(j.Ch, "heroic_leap");
        var b = Fight(j);
        Assert.DoesNotContain(b.Weapons, w => w.Id == "heroic_leap");
        Assert.Contains("heroic_leap", j.Ch.Skills);
    }

    [Fact]
    public void An_arena_fight_is_left_as_it_was()
    {
        var j = New();
        j.Ch.Level = 9;
        j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.Equal(0, j.Ch.TaughtUpTo);
        Assert.DoesNotContain("groundbreaker", j.Ch.Slotted);
    }
}
