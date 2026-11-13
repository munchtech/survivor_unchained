using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class QuenchBarModelTests
{
    [Fact]
    public void Five_segments_in_the_card_order_and_fractions_sum_to_one()
    {
        var s = QuenchBarModel.Build(Crafting.QuenchOdds());
        Assert.Equal(new[] { "perfect", "up", "nothing", "down", "ruin" }, s.Select(x => x.Id));
        Assert.Equal(1.0, s.Sum(x => x.Fraction), 6);
    }

    [Fact]
    public void Fractions_follow_QuenchOdds_not_a_hardcoded_table()
    {
        var odds = Crafting.QuenchOdds().ToDictionary(o => o.Outcome, o => o.Chance);
        var s = QuenchBarModel.Build(Crafting.QuenchOdds());
        foreach (var seg in s) Assert.Equal(odds[seg.Id], seg.Fraction, 6);
        var other = QuenchBarModel.Build(new[] { ("perfect", 1.0), ("up", 1.0), ("nothing", 2.0), ("down", 0.0), ("ruin", 0.0) });
        Assert.Equal(new[] { 0.25, 0.25, 0.5, 0, 0 }, other.Select(x => x.Fraction));
    }

    [Fact]
    public void Gains_are_warm_the_lost_grade_is_cold_and_percents_are_whole()
    {
        var s = QuenchBarModel.Build(Crafting.QuenchOdds());
        Assert.Equal(new[] { true, true, false, false, false }, s.Select(x => x.Warm));
        Assert.Equal(new[] { false, false, false, true, false }, s.Select(x => x.Cold));
        Assert.Equal("6%", QuenchBarModel.Percent(s[0].Fraction));
    }
}

public class QuenchEffectsTests
{
    static string G(int t) => new[] { "I", "II", "III", "IV", "V" }[t];

    [Fact]
    public void One_shared_grade_reads_from_to()
    {
        var e = QuenchBarModel.Effects(new[] { 2, 2 }, 3, 4, 2, 2, 2, G);
        Assert.Equal("III › V", e["perfect"]);
        Assert.Equal("III › IV", e["up"]);
        Assert.Equal("stays III", e["nothing"]);
        Assert.Equal("III › II", e["down"]);
        Assert.Equal("III › I", e["ruin"]);
    }

    [Fact]
    public void Ruin_that_lands_where_a_grade_lost_does_says_floor()
    {
        var e = QuenchBarModel.Effects(new[] { 1, 1 }, 3, 4, 2, 2, 2, G);
        Assert.Equal("II › I", e["down"]);
        Assert.Equal("II › I · floor", e["ruin"]);
    }

    [Fact]
    public void Capped_floored_mixed_and_empty_pieces_are_stated_honestly()
    {
        Assert.Equal("no room above", QuenchBarModel.Effects(new[] { 3 }, 3, 4, 2, 2, 2, G)["up"]);
        var low = QuenchBarModel.Effects(new[] { 0 }, 3, 4, 2, 2, 2, G);
        Assert.Equal("stays", low["down"]); Assert.Equal("stays", low["ruin"]);
        var mix = QuenchBarModel.Effects(new[] { 1, 2, 3 }, 3, 4, 2, 2, 2, G);
        Assert.Equal("all to V", mix["perfect"]); Assert.Equal("2 powers +1", mix["up"]); Assert.Equal("all -2 grades", mix["ruin"]);
        Assert.All(QuenchBarModel.Effects(new int[0], 3, 4, 2, 2, 2, G).Values, v => Assert.Equal("no powers to move", v));
    }
}
