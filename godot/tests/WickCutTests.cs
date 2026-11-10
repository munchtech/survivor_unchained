using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>WickSumView.Cut / Every: a chained skill's cut by day; Total and Parts stay the fight's own number.</summary>
public sealed class WickCutTests
{
    static bool HasData => System.IO.File.Exists(System.IO.Path.Combine(Core.DataFiles.Dir, "content", "lamps_v2.json"));

    static (CharacterData Ch, string Calling) Hero(string skill)
    {
        Lamps.UseV2(true);
        var calling = new[] { "warden", "reaver", "arcanist", "stalker" }.First(c => Weapons.CanCarry(c, skill));
        var a = Callings.Archetype(calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = 1;
        LampBook.Begin(ch, null);
        return (ch, calling);
    }

    [Fact]
    public void Oathblade_by_day_has_a_cut_and_total_and_parts_are_the_fights()
    {
        if (!HasData) return;
        var (ch, _) = Hero("oathblade");
        var sum = WickBook.Sum(ch, "oathblade", false)!;
        // Level 1 lights one lead-in (+10%): the cut is the total x 0.70 / the 1.05 wait.
        Assert.Equal(sum.Total * 0.70 / 1.05, sum.Cut!.Value, 9);
        Assert.Equal(16.7273, sum.Cut!.Value, 4);
        Assert.Equal(0.70, sum.Every!.Value, 9);
        Assert.Equal("wicks", sum.Parts[1].What);
        int rank = WickBook.RankIn(ch, "oathblade", false);
        var b = BattleTests.Arena(3, ("oathblade", rank));
        b.SetWickPath("oathblade", WickBook.Path(ch, "oathblade"));
        Assert.Equal(b.Weapons.Single(x => x.Id == "oathblade").Damage, sum.Total, 9);
        Assert.Equal("Damage", sum.Stat);
        Assert.Equal("base", sum.Parts[0].What);
    }

    [Fact]
    public void Without_wicks_lit_the_cuts_are_the_written_blow_scaled()
    {
        if (!HasData) return;
        var prev = WickBook.Lights;
        try
        {
            WickBook.Lights = WickBook.Mode.None;
            var (ch, _) = Hero("oathblade");
            Assert.Equal(15.2067, WickBook.Sum(ch, "oathblade", false)!.Cut!.Value, 4);
            var (c2, _) = Hero("sunder");
            Assert.Equal(12.25, WickBook.Sum(c2, "sunder", false)!.Cut!.Value, 4);
        }
        finally { WickBook.Lights = prev; }
    }

    [Fact]
    public void Sunder_by_day_has_a_cut()
    {
        if (!HasData) return;
        var (ch, _) = Hero("sunder");
        var sum = WickBook.Sum(ch, "sunder", false)!;
        Assert.Equal(13.475, sum.Cut!.Value, 4);
        Assert.Equal(0.70, sum.Every!.Value, 9);
    }

    [Fact]
    public void Night_and_unchained_skills_have_no_cut()
    {
        if (!HasData) return;
        var (ch, _) = Hero("oathblade");
        var night = WickBook.Sum(ch, "oathblade", true)!;
        Assert.Null(night.Cut);
        Assert.Null(night.Every);
        var plain = Wicks.Skills.First(s => Weapons.All[s].Press?.Chain?.Period is not > 0 && (Weapons.All[s].Base.Damage ?? 0) > 0);
        var (c2, _) = Hero(plain);
        var s2 = WickBook.Sum(c2, plain, false)!;
        Assert.Null(s2.Cut);
        Assert.Null(s2.Every);
    }
}
