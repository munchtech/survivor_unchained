using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The hands rule (BUILD_DIRECTION.md round 8, the owner's 13 November interview; it replaces the six slots of
/// 9 November): four keys, the basic attack held in the first and at most three pressed beside it (the dash, the Flare and
/// the swap are not keys), three auto slots that run kindled, and each calling's kit offers at least half its skills
/// kindled. data/content/taught_builds.json and skills.json's press records.</summary>
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
    public void At_least_half_the_warden_kit_is_offered_kindled()
    {
        int kindled = WardenKit.Count(id => WeaponInst.OfferedKindled(Weapons.Get(id)));
        Assert.True(kindled * 2 >= WardenKit.Length, $"{kindled} of {WardenKit.Length}");
        Assert.True(kindled >= 7);
    }

    [Fact]
    public void The_taught_warden_build_keeps_the_hands_rule()
    {
        var t = TaughtBuilds.Of("warden")!;
        Assert.Equal("sunder", t.Grip);
        Assert.Equal(Weapons.MaxKeys, t.Keys.Count);
        Assert.Equal(Weapons.AutoSlots, t.Autos.Count);
        Assert.Equal(t.Grip, t.Keys[0].Skill);
        Assert.Equal("hold", t.Keys[0].Cast);
        Assert.True(TaughtBuilds.PressedSlots(t) <= 3, $"{TaughtBuilds.PressedSlots(t)} pressed beside the grip");
        Assert.All(t.Keys.Skip(1), s => Assert.NotEqual("kindle", s.Cast));
        Assert.All(t.Autos, s => Assert.Equal("kindle", s.Cast));
        foreach (var s in t.Slots)
        {
            Assert.True(Weapons.CanCarry("warden", s.Skill), s.Skill);
            Assert.True(WeaponInst.Allows(Weapons.Get(s.Skill), s.Cast), $"{s.Skill} as {s.Cast}");
        }
        Assert.Equal(t.Slots.Count, t.Slots.Select(s => s.Skill).Distinct().Count());
        // Every slot at the ladder's level (BUILD_UNLOCKS.md): the n-th key when the n-th key opens, the same for autos.
        for (int i = 0; i < t.Keys.Count; i++) Assert.Equal(i + 1, SkillBook.KeysAt(t.Keys[i].Level));
        for (int i = 0; i < t.Keys.Count; i++) Assert.True(t.Keys[i].Level == 1 || SkillBook.KeysAt(t.Keys[i].Level - 1) == i, t.Keys[i].Skill);
        for (int i = 0; i < t.Autos.Count; i++) Assert.Equal(i + 1, SkillBook.AutosAt(t.Autos[i].Level));
        for (int i = 0; i < t.Autos.Count; i++) Assert.True(t.Autos[i].Level == 1 || SkillBook.AutosAt(t.Autos[i].Level - 1) == i, t.Autos[i].Skill);
        Assert.Equal("bladestorm", t.Union!.Id);
    }

    [Fact]
    public void The_taught_forms_go_on_a_campaign_fight()
    {
        var t = TaughtBuilds.Of("warden")!;
        var b = new Battle(new BattleSetup
        {
            Seed = 2, Collision = new CollisionWorld(120), Combat = true, Campaign = true,
            Stats = BattleTests.BaseStats(), Weapons = t.Slots.Select(s => (s.Skill, 1)).ToList(), Ability = AbilityKind.ShieldBash,
            Kindled = t.Autos.Select(s => s.Skill).ToHashSet(), Calling = "warden",
        });
        Assert.Equal(t.Slots.Count, TaughtBuilds.Apply(b, "warden").Count);
        Assert.True(b.Weapons.First(x => x.Id == "sunder").Hold);
        Assert.Equal(0, b.Weapons.First(x => x.Id == "sunder").Slot);
        foreach (var s in t.Autos)
        {
            var w = b.Weapons.First(x => x.Id == s.Skill);
            Assert.Equal(CastMode.Auto, w.Cast);
            Assert.True(w.Slot >= Weapons.MaxKeys, s.Skill);
        }
        Assert.Equal(CastMode.Press, b.Weapons.First(x => x.Id == "heroic_leap").Cast);
        // The keys she actually presses beside the grip: three.
        Assert.Equal(3, b.Weapons.Count(w => w.Pressed && !w.Hold));
        Assert.Equal(Weapons.MaxKeys, b.SlotsUsed);
        // Every key does something.
        Assert.All(b.Weapons, w => Assert.True(w.Keyed, w.Id));
    }
}
