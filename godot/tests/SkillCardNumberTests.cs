using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-071) A skill card's {base.X} numbers are what her build gets (the runtime's own helpers), not the
/// written base: Far Spring's leap reaches 13 m and the card says so; Crater lands 4.5 m, stuns 1.2 s, and the card says so.
/// With a live fight or with none (the card built from her alone).</summary>
[Collection("Balance")]
public class SkillCardNumberTests
{
    static Journey Warden()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        j.Ch.Level = 7;
        return j;
    }

    static Battle Lit(Journey j, string lamp)
    {
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 3);
        j.Teach(b);
        Assert.Equal(WickNo.None, WickBook.Plan(j.Ch, "heroic_leap", lamp));
        Assert.Equal(lamp, j.LightHeld("heroic_leap", b));
        return b;
    }

    static string Row(SkillTipView v, string label) => v.Rows.Single(r => r.Item1 == label).Item2;

    [Fact]
    public void Far_spring_card_shows_the_leap_the_fight_gives_live_and_without_a_battle()
    {
        var j = Warden();
        var b = Lit(j, "heroic_leap.flight.1");
        double reach = b.RuleLeapRange(b.Weapons.Single(w => w.Id == "heroic_leap"), 9);
        Assert.Equal(13, reach, 1);
        Assert.EndsWith(" to 13 m", Row(SkillTipModel.Build(j.Ch, b, "heroic_leap", "press"), "Leap"));
        Assert.EndsWith(" to 13 m", Row(SkillTipModel.Build(j.Ch, null, "heroic_leap", "press"), "Leap"));
    }

    [Fact]
    public void Crater_card_shows_the_stun_and_radius_the_fight_gives_live_and_without_a_battle()
    {
        var j = Warden();
        var b = Lit(j, "heroic_leap.quake.1");
        var w = b.Weapons.Single(x => x.Id == "heroic_leap");
        Assert.Equal(1.2, b.LeapStunOf(w), 2);
        string live = Row(SkillTipModel.Build(j.Ch, b, "heroic_leap", "press"), "Knockdown");
        string alone = Row(SkillTipModel.Build(j.Ch, null, "heroic_leap", "press"), "Knockdown");
        string want = $"{SkillTipModel.Plain(b.LeapStunOf(w))} s within {SkillTipModel.Plain(b.LeapRadiusOf(w))} m";
        Assert.True(b.LeapRadiusOf(w) >= 4.5, "Crater reaches 4.5 m or more (area grows it), not the written 3.5");
        Assert.Equal(want, live);
        Assert.Equal(want, alone);
    }
}
