using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>CODEX_audit.md installment 9, SU-051: Heroic Leap, Shield Charge and Iron Vow, taught at 4, 5 and 7, carry
/// their skill_lamps.json trees as wicks (Wicks.RuleTrees): reached through play (the level, the teaching, a planned lamp,
/// a held point lit), the lamp's rule is at work in the fight, never injected. A carried skill with no strands says so.</summary>
[Collection("Balance")]
public class RuleWickProgressionTests
{
    static Journey Warden(int level)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        j.Ch.Level = level;
        return j;
    }

    static Battle Campaign(Journey j) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 3);

    /// <summary>Where the leap takes off for: pressed at a spot 20 m off, the distance it lands (Ev.Leap Takeoff).</summary>
    static double LeapReach(Battle b)
    {
        b.Events.Drain().ToList();
        var w = b.Weapons.Single(x => x.Id == "heroic_leap");
        w.Timer = 0;
        b.Resolve.Set(100);
        Assert.True(b.PressSkill(w.Slot, b.Player.X + 20, b.Player.Z), "the leap went off");
        var t = b.Events.Drain().OfType<Ev.Leap>().First(e => e.Phase == LeapPhase.Takeoff);
        return Math.Sqrt((t.X1 - t.X0) * (t.X1 - t.X0) + (t.Z1 - t.Z0) * (t.Z1 - t.Z0));
    }

    /// <summary>Level 7 reached mid-fight: the three are taught into it with wicks; Far Spring planned and its held point
    /// lit, the very next leap reaches 13 m, not 9. Shield Charge's Headlong and Iron Vow's Steadfast, planned and lit
    /// the same way, are lit in the fight's lamps.</summary>
    [Fact]
    public void Taught_leap_charge_and_vow_light_their_planned_lamps_into_the_fight()
    {
        var j = Warden(3);
        var b = Campaign(j);
        Assert.DoesNotContain(b.Weapons, w => w.Id == "heroic_leap");

        j.Ch.Level = 7;
        var taught = j.Teach(b).Select(s => s.Skill).ToHashSet();
        foreach (var s in new[] { "heroic_leap", "shield_charge", "iron_vow" })
        {
            Assert.Contains(s, taught);
            Assert.Contains(b.Weapons, w => w.Id == s);
            Assert.NotNull(Wicks.Of(s));
            Assert.Equal(3, Wicks.StrandsOf(s).Count());
            Assert.True(WickBook.Held(j.Ch, s) > 0, $"{s} holds its points");
            Assert.False(WickBook.Panel(j.Ch, s, false).NoWick);
        }

        double before = LeapReach(b);
        Assert.Equal(9, before, 1);

        foreach (var (skill, lamp, rule) in new[]
        {
            ("heroic_leap", "heroic_leap.flight.1", "heroic_leap.far_spring"),
            ("shield_charge", "shield_charge.drive.1", "shield_charge.headlong"),
            ("iron_vow", "iron_vow.brace.1", "iron_vow.steadfast"),
        })
        {
            Assert.False(b.Lamps.Has(rule), $"{rule} dark before");
            Assert.Equal(WickNo.None, WickBook.Plan(j.Ch, skill, lamp));
            Assert.Equal(lamp, j.LightHeld(skill, b));
            Assert.Contains(lamp, b.Weapons.Single(w => w.Id == skill).Wick!.Lit);
            Assert.True(b.Lamps.Has(rule), $"{rule} lit in the fight");
            Assert.Equal(lamp, WickBook.Panel(j.Ch, skill, false).Lit.Single());
        }

        for (int i = 0; i < 90; i++) b.Tick(1 / 60.0, 0, 0);
        b.Player.X = 0; b.Player.Z = 0;
        double after = LeapReach(b);
        Assert.Equal(13, after, 1);

        // a refreshed kit (a new loadout mid-fight) keeps the wick's rules lit, once
        j.RefreshKit(b);
        Assert.True(b.Lamps.Has("heroic_leap.far_spring"));
        Assert.Single(b.Lamps.Each["heroic_leap.far_spring"]);

        // a fresh campaign fight lights the same lamps from the day path
        var b2 = Campaign(j);
        foreach (var rule in new[] { "heroic_leap.far_spring", "shield_charge.headlong", "iron_vow.steadfast" })
            Assert.True(b2.Lamps.Has(rule), $"{rule} lit in the next fight");
    }

    /// <summary>A "built" Turn (Shield Charge's Ram: Pile Driver) lit makes the weapon its evolution, once.</summary>
    [Fact]
    public void A_lit_built_turn_evolves_the_skill()
    {
        var b = BattleTests.Arena(4, ("shield_charge", 4));
        var w = b.Weapons.Single(x => x.Id == "shield_charge");
        Assert.Null(w.Evolution);
        b.SetWickPath("shield_charge", ["shield_charge.ram.1", "shield_charge.ram.2", "shield_charge.ram.3", "shield_charge.ram.4"]);
        Assert.Equal("pile_driver", w.Evolution?.Id);
        Assert.True(b.Lamps.Has("shield_charge.iron_hide"));
        Assert.Single(b.Events.Drain().OfType<Ev.Evolve>());
        b.SetWickPath("shield_charge", ["shield_charge.ram.1", "shield_charge.ram.2", "shield_charge.ram.3", "shield_charge.ram.4"]);
        Assert.Empty(b.Events.Drain().OfType<Ev.Evolve>());
    }

    /// <summary>The guard: a carried skill with no strands opens to an explicit "no wick yet", never an empty tree.</summary>
    [Fact]
    public void A_skill_with_no_strands_shows_no_wick_yet()
    {
        var j = Warden(7);
        string bare = Weapons.All.Keys.First(id => Wicks.Of(id) == null);
        Assert.True(WickBook.NoWickYet(bare));
        var p = WickBook.Panel(j.Ch, bare, false);
        Assert.True(p.NoWick);
        Assert.Empty(p.Path);
        Assert.False(string.IsNullOrWhiteSpace(WickBook.NoWickText));
        foreach (var s in new[] { "heroic_leap", "shield_charge", "iron_vow", "sunder" }) Assert.False(WickBook.NoWickYet(s));
    }
}
