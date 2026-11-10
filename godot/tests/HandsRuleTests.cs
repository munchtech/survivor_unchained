using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The hands rule (ARPG.md, the owner's amendment of 9 November): six slots stand, but a taught build has at most
/// two pressed skills beside the held swing (the dash is not a slot), and each calling's kit offers at least half its
/// skills kindled. data/content/taught_builds.json and skills.json's press records.</summary>
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
        Assert.True(t.Slots.Count <= Weapons.MaxWeapons);
        Assert.True(TaughtBuilds.PressedSlots(t) <= 2, $"{TaughtBuilds.PressedSlots(t)} pressed beside the grip");
        Assert.Equal("hold", t.Slots.Single(s => s.Skill == t.Grip).Cast);
        foreach (var s in t.Slots)
        {
            Assert.True(Weapons.CanCarry("warden", s.Skill), s.Skill);
            Assert.True(WeaponInst.Allows(Weapons.Get(s.Skill), s.Cast), $"{s.Skill} as {s.Cast}");
        }
        Assert.Equal(t.Slots.Count, t.Slots.Select(s => s.Skill).Distinct().Count());
        Assert.Contains("dawnpulse", t.Later);
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
        });
        b.Calling = "warden";
        Assert.Equal(t.Slots.Count, TaughtBuilds.Apply(b, "warden").Count);
        Assert.True(b.Weapons.First(x => x.Id == "sunder").Hold);
        Assert.Equal(CastMode.Auto, b.Weapons.First(x => x.Id == "groundbreaker").Cast);
        Assert.Equal(CastMode.Auto, b.Weapons.First(x => x.Id == "iron_vow").Cast);
        Assert.Equal(CastMode.Auto, b.Weapons.First(x => x.Id == "watch_bell").Cast);
        Assert.Equal(CastMode.Press, b.Weapons.First(x => x.Id == "heroic_leap").Cast);
        // The keys she actually presses beside the grip: two.
        Assert.Equal(2, b.Weapons.Count(w => w.Pressed && !w.Hold));
        // Every key does something.
        Assert.All(b.Weapons, w => Assert.True(w.Keyed, w.Id));
    }
}
