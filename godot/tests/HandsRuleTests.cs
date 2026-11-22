using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The hands rule (BUILD_DIRECTION.md round 8, the owner's 13 November interview; it replaces the six slots of
/// 9 November): five keys (22 Nov, Round 10), the basic attack held in the first and at most four pressed beside it (the dash, the Flare and
/// the swap are not keys), every key at its ladder level, and no auto slots (SKILL_KINDS.md). data/content/taught_builds.json and skills.json's press records.</summary>
public sealed class HandsRuleTests
{
    /// <summary>The warden's kit in the ARPG (ARPG.md 3.2), its unions apart.</summary>
    static readonly string[] WardenKit =
    [
        "cleaver", "sunder", "oathblade", "groundbreaker", "judgement_disc", "dawnpulse", "hallowed_ring", "watch_bell",
        "rebuke", "iron_palms", "gale_chakram", "heroic_leap", "shield_charge", "iron_vow",
    ];

    [Fact]
    public void Every_warden_skill_and_its_unions_carry_a_press_record()
    {
        foreach (var id in WardenKit.Append("bladestorm").Append("dawns_judgement"))
        {
            Assert.NotNull(Weapons.Get(id).Press);
            Assert.True(Weapons.CanCarry("warden", id), id);
        }
        Assert.Equal(PressKind.Hold, Weapons.Get("sunder").Press!.Kind);
        Assert.Equal(PressKind.Hold, Weapons.Get("oathblade").Press!.Kind);
        Assert.Equal(PressKind.Channel, Weapons.Get("bladestorm").Press!.Kind);
        Assert.Equal(PressKind.Kindle, Weapons.Get("rebuke").Press!.Kind);
        foreach (var id in new[] { "groundbreaker", "judgement_disc", "dawnpulse", "cleaver" })
            Assert.True(Weapons.Get(id).Press!.Resolve > 0, id);
    }

    [Fact]
    public void The_taught_warden_build_keeps_the_hands_rule()
    {
        var t = TaughtBuilds.Of("warden")!;
        Assert.Equal("sunder", t.Grip);
        Assert.Equal(Weapons.MaxKeys, t.Keys.Count);
        Assert.Equal(t.Grip, t.Keys[0].Skill);
        Assert.Equal("hold", t.Keys[0].Cast);
        Assert.True(TaughtBuilds.PressedSlots(t) <= 4, $"{TaughtBuilds.PressedSlots(t)} pressed beside the grip");
        Assert.All(t.Keys.Skip(1), s => Assert.NotEqual("kindle", s.Cast));
        foreach (var s in t.Slots)
        {
            Assert.True(Weapons.CanCarry("warden", s.Skill), s.Skill);
            Assert.NotEqual("kindle", s.Cast);
            Assert.Equal(s.Cast, Weapons.Get(s.Skill).Press!.Kind.ToString().ToLowerInvariant());
        }
        Assert.Equal(t.Slots.Count, t.Slots.Select(s => s.Skill).Distinct().Count());
        // Every slot at the ladder's level (BUILD_UNLOCKS.md): the n-th key when the n-th key opens, 
        for (int i = 0; i < t.Keys.Count; i++) Assert.Equal(i + 1, SkillBook.KeysAt(t.Keys[i].Level));
        for (int i = 0; i < t.Keys.Count; i++) Assert.True(t.Keys[i].Level == 1 || SkillBook.KeysAt(t.Keys[i].Level - 1) == i, t.Keys[i].Skill);
        // (13 Nov 2026) Bladestorm is key 3's own skill (a channel, level 5), Iron Vow key 4 (level 7) and Shield Charge key 5 (level 9, 22 Nov Round 10); Dawnpulse is offered later; Falling Wall is the first union (both halves are keys).
        Assert.Equal(["sunder", "heroic_leap", "bladestorm", "iron_vow", "shield_charge"], t.Keys.Select(k => k.Skill).ToArray());
        Assert.Equal([1, 4, 5, 7, 9], t.Keys.Select(k => k.Level).ToArray());
        Assert.Equal("channel", t.Keys[2].Cast);
        Assert.Equal(["dawnpulse"], t.Later);
        Assert.Equal("falling_wall", t.Union?.Id);
    }

    [Fact]
    public void The_taught_keys_go_on_a_campaign_fight()
    {
        var t = TaughtBuilds.Of("warden")!;
        var b = new Battle(new BattleSetup
        {
            Seed = 2, Collision = new CollisionWorld(120), Combat = true, Campaign = true,
            Stats = BattleTests.BaseStats(), Weapons = t.Slots.Select(s => (s.Skill, 1)).ToList(), Ability = AbilityKind.ShieldBash,
            Calling = "warden",
        });
        Assert.Equal(0, b.Weapons.First(x => x.Id == "sunder").Slot);
        Assert.Equal(CastMode.Press, b.Weapons.First(x => x.Id == "heroic_leap").Cast);
        Assert.All(b.Weapons, w => Assert.NotEqual(CastMode.Auto, w.Cast));
        // The keys she actually presses beside the grip: four.
        Assert.Equal(4, b.Weapons.Count(w => w.Pressed && !w.Hold));
        Assert.Equal(Weapons.MaxKeys, b.SlotsUsed);
        // Every key does something.
        Assert.All(b.Weapons, w => Assert.True(w.Keyed, w.Id));
    }
}
