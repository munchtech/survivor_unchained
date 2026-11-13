using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-ui2) Drops.IsGift / GiftSkill: the four great uniques are gifts for the Warden; a plain Legendary and a Rare are not.</summary>
public class GiftDropTests
{
    static Journey Warden() => Balance.MapSim.Survivor("warden", 20, 1, 5);

    [Theory]
    [InlineData("herd_callers_horn")]
    [InlineData("stormwrights_ring")]
    [InlineData("firebrands_bandolier")]
    [InlineData("thornwreath")]
    public void The_great_uniques_are_gifts_for_the_Warden(string def)
    {
        var ch = Warden().Ch;
        var it = Inventory.Make(ch, def, rarity: 4, level: 5);
        Assert.True(Drops.IsGift(it, "warden"));
        Assert.NotNull(Drops.GiftSkill(it, "warden"));
    }

    [Theory]
    [InlineData("iron_helm", 4)]
    [InlineData("iron_helm", 2)]
    public void A_plain_Legendary_or_Rare_is_not(string def, int rarity)
    {
        var it = Inventory.Make(Warden().Ch, def, rarity: rarity, level: 5);
        Assert.False(Drops.IsGift(it, "warden"));
        Assert.Null(Drops.GiftSkill(it, "warden"));
    }
}

/// <summary>(bd-ui2) The swap's big ring reads its radius from stances.json (BattleFx.Swap).</summary>
public class SwapRadiusTests
{
    [Theory]
    [InlineData("shield", 3.0)]
    [InlineData("twin_blades", 3.6)]
    [InlineData("mace", 3.0)]
    public void Stance_strike_radius_is_in_the_data(string id, double r) => Assert.Equal(r, SurvivorUnchained.Content.Stances.Find(id)!.Strike.Radius);

    [Fact]
    public void Warden_set_one_strike_is_3_4() => Assert.Equal(3.4, SurvivorUnchained.Content.Stances.SetA("warden")!.Radius);
}
