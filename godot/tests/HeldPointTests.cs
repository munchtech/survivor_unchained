using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M7a (docs/design/ARPG.md 3.5, 5 row 5a): a skill's points come one at the first level, then one every second
/// level; a point earned while she carries the skill is held until she lights it.</summary>
public class HeldPointTests
{
    static Journey Warden(uint seed = 7)
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, seed);
    }

    static Battle Day(Journey j) => j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1);

    /// <summary>Levels her up to a level the way play does (GainXp, level by level).</summary>
    static void LevelTo(Journey j, int level)
    {
        while (j.Ch.Level < level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 0.01);
    }

    static WeaponInst? Live(Battle b, string skill) => b.Weapons.Find(w => w.Id == skill);

    [Theory]
    [InlineData(1, 1)] [InlineData(2, 1)] [InlineData(3, 2)] [InlineData(9, 5)] [InlineData(14, 7)] [InlineData(15, 8)] [InlineData(30, 8)]
    public void Points_come_every_second_level(int level, int points) => Assert.Equal(points, SkillBook.PointsAt(level));

    [Fact]
    public void A_new_warden_holds_her_first_point_and_lights_no_lamp()
    {
        var j = Warden();
        var wick = SkillBook.Carried(j.Ch).Select(c => c.Id).Where(id => Wicks.Of(id) != null).ToList();
        Assert.Contains("sunder", wick);
        foreach (var id in wick)
        {
            Assert.Equal(1, WickBook.Held(j.Ch, id));
            Assert.Equal(0, WickBook.Burning(j.Ch, id));
            Assert.Equal(1, WickBook.DayRank(j.Ch, id));
        }
        var b = Day(j);
        Assert.Equal(1, Live(b, "sunder")!.Rank);
        Assert.Empty(WickBook.Lit(b, "sunder"));
    }

    [Fact]
    public void Her_first_levels_offer_Third_Blow_then_Harvest()
    {
        var j = Warden();
        var b = Day(j);
        b.Events.Drain();
        LevelTo(j, 2);
        Assert.Equal(1, WickBook.Held(j.Ch, "sunder"));
        Assert.Equal("sunder.stroke.1", WickBook.NextLamp(j.Ch, "sunder"));
        Assert.Equal("Third Blow", Wicks.Name("sunder.stroke.1"));
        var m = WickBook.LampMeasure(j.Ch, "sunder", "sunder.stroke.1");
        // The live wick's first Stroke lamp is "+10% damage" (wicks.json): the blow changes, so the card measures the blow.
        Assert.Equal("a blow", m.Measure);
        Assert.Equal(m.Before * 1.1, m.After, 1);
        Assert.Equal("sunder.stroke.1", j.LightHeld("sunder", b));
        Assert.Equal(1, WickBook.Burning(j.Ch, "sunder"));
        Assert.Equal(0, WickBook.Held(j.Ch, "sunder"));
        Assert.Equal(["sunder.stroke.1"], WickBook.Lit(b, "sunder"));
        Assert.Equal(1, Live(b, "sunder")!.Rank);
        var ev = b.Events.Drain().OfType<Ev.Wick>().ToList();
        Assert.Equal(["sunder.stroke.1"], ev.Select(e => e.Lamp));
        Assert.Null(j.LightHeld("sunder", b));

        LevelTo(j, 3);
        Assert.Equal(1, WickBook.Held(j.Ch, "sunder"));
        foreach (var id in SkillBook.Carried(j.Ch).Select(c => c.Id).Where(id => Wicks.Of(id) != null && id != "sunder"))
            Assert.True(WickBook.Held(j.Ch, id) >= 2, $"{id} held {WickBook.Held(j.Ch, id)} slotted {string.Join(",", j.Ch.Slotted)}");
        Assert.Equal("sunder.stroke.2", j.LightHeld("sunder", b));
        Assert.Equal(2, WickBook.DayRank(j.Ch, "sunder"));
        Assert.Equal(2, Live(b, "sunder")!.Rank);
        Assert.Equal(["sunder.stroke.1", "sunder.stroke.2"], WickBook.Lit(b, "sunder"));
        // A fight begun now takes the same.
        var b2 = Day(j);
        Assert.Equal(2, Live(b2, "sunder")!.Rank);
        Assert.Equal(["sunder.stroke.1", "sunder.stroke.2"], WickBook.Lit(b2, "sunder"));
    }

    [Fact]
    public void Card_numbers_for_lamps_whose_blow_stays()
    {
        var c = Wicks.Card("sunder.stroke.1")!;
        Assert.Equal(("a heavy blow every", 4.0, 3.0), (c.Measure, c.Before, c.After));
        var g = Wicks.Card("groundbreaker.heave.2")!;
        Assert.Equal(("a heavy heave every", 6.0, 1.0), (g.Measure, g.Before, g.After));
        Assert.Null(Wicks.Card("sunder.stroke.2"));
    }

    [Fact]
    public void With_light_my_way_on_nothing_is_held()
    {
        var j = Warden();
        LampBook.State(j.Ch).LightMyWay = true;
        WickBook.LightAll(j.Ch);
        LevelTo(j, 5);
        foreach (var (id, rank) in SkillBook.Carried(j.Ch))
        {
            Assert.Equal(0, WickBook.Held(j.Ch, id));
            Assert.Equal(SkillBook.Rank(j.Ch), rank);
        }
        Assert.Null(WickBook.NextLamp(j.Ch, "sunder"));
    }

    [Fact]
    public void Light_my_way_burns_every_held_point()
    {
        var j = Warden();
        LevelTo(j, 3);
        Assert.Equal(2, WickBook.Held(j.Ch, "sunder"));
        LampBook.LightSuggested(j.Ch, j.World);
        Assert.Equal(0, WickBook.Held(j.Ch, "sunder"));
        Assert.Equal(2, WickBook.DayRank(j.Ch, "sunder"));
    }

    [Fact]
    public void Nothing_held_fights_as_before()
    {
        var j = Warden();
        j.Ch.Level = 8;
        TaughtBuilds.Grant(j.Ch, 8); // lit after the grant, so nothing is held
        WickBook.LightAll(j.Ch);
        Assert.Equal(4, SkillBook.Rank(j.Ch));
        var b = Day(j);
        foreach (var (id, rank) in SkillBook.Carried(j.Ch))
        {
            Assert.Equal(SkillBook.Rank(j.Ch), rank);
            if (Wicks.Of(id) == null || Live(b, id) is not { } w) continue;
            Assert.Equal(SkillBook.Rank(j.Ch), w.Rank);
            Assert.Equal(WickBook.Path(j.Ch, id).Take(SkillBook.Rank(j.Ch)), WickBook.Lit(b, id));
        }
    }

    [Fact]
    public void A_skill_with_every_point_held_fights_at_rank_one_with_no_lamps_lit()
    {
        var j = Warden();
        var b = Day(j);
        foreach (var (id, _) in SkillBook.Carried(j.Ch).Where(c => Wicks.Of(c.Id) != null))
        {
            Assert.True(WickBook.Held(j.Ch, id) > 0);
            Assert.True(WickBook.DayRank(j.Ch, id) >= 1);
            if (Live(b, id) is { } w) { Assert.True(w.Rank >= 1); Assert.Empty(w.Wick!.Lit); }
        }
    }

    [Fact]
    public void Level_nine_all_lit_has_Sunders_Turn()
    {
        var j = Warden();
        LevelTo(j, 9);
        LampBook.LightSuggested(j.Ch, j.World);
        Assert.Equal(5, WickBook.DayRank(j.Ch, "sunder"));
        var path = WickBook.Path(j.Ch, "sunder");
        // What the code does (pinned, not changed): the Turn is one point of the path, its strand's fourth (lit from
        // level 7, rank 4); rules.costs' "a Turn costs 2" is not counted by Path or Relight.
        Assert.Equal("sunder.stroke.4", path[3]);
        Assert.True(Wicks.IsTurn("sunder", path[3]));
        var lit = WickBook.Lit(Day(j), "sunder");
        Assert.Equal(path.Take(5), lit);
        Assert.Contains("sunder.stroke.4", lit);
    }
}
