using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The systems decisions the items plan left open (docs/SKILLS_DESIGN.md,
/// "Decisions"), held where they are code.</summary>
public class DecisionTests
{
    [Fact]
    public void The_survivor_stops_at_level_thirty()
    {
        var j = Play.Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
            WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = "shield_bash",
        }, 7);
        while (j.Ch.Level < Character.MaxLevel) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        int points = j.Ch.Points;
        Assert.Equal(0, Character.GainXp(j.Ch, 1e9));
        Assert.Equal(Character.MaxLevel, j.Ch.Level);
        Assert.Equal(points, j.Ch.Points);
        Assert.Equal(0, j.Ch.Xp);
    }
}
