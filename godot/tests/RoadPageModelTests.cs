using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class RoadPageModelTests
{
    static Journey Warden()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 7);
    }

    [Fact]
    public void The_wardens_two_roads_show_with_their_data_and_the_gate_before_level_six()
    {
        var j = Warden();
        var p = RoadPageModel.Of(j.Ch);
        Assert.Equal(new[] { "sunderer", "bulwark" }, p.Roads.Select(r => r.Id));
        Assert.False(p.Open);
        Assert.Equal("Opens at level 6", p.Gate);
        Assert.All(p.Roads, r => Assert.False(r.Walked));
        var sun = p.Roads[0];
        Assert.Equal(new[] { "sunder", "groundbreaker", "dawnpulse" }, sun.Leaning);
        Assert.Equal("the_long_cut", sun.Strike!.Id);
        Assert.Equal("dawn_in_the_steel", sun.Stand!.Id);
        Assert.False(string.IsNullOrEmpty(sun.Strike.Name));
    }

    [Fact]
    public void Walking_a_road_flags_it_and_opens_the_page()
    {
        var j = Warden();
        while (j.Ch.Level < LampBook.RoadLevel) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        Assert.True(LampBook.ChooseRoad(j.Ch, "bulwark"));
        var p = RoadPageModel.Of(j.Ch);
        Assert.True(p.Open);
        Assert.Equal(new[] { false, true }, p.Roads.Select(r => r.Walked));
        Assert.NotNull(p.Roads[1].RoadSkill);
    }
}
