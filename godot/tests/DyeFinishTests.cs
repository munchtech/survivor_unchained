using System.Collections.Generic;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Wear.DyeFinish: a colour dye paints the enamel, a light neutral or ":metal" dye stays metal.</summary>
public class DyeFinishTests
{
    [Theory]
    [InlineData("#8a2a22", false)]
    [InlineData("#c8ccd4", true)]
    [InlineData("#46403c", false)]
    [InlineData("#d2b25a", false)]
    [InlineData("#d2b25a:metal", true)]
    [InlineData("#c8ccd4:PAINT", false)]
    [InlineData(" #c8ccd4 : metal ", true)]
    public void Finish(string dye, bool metal) => Assert.Equal(metal, Wear.DyeFinish(dye).Metal);

    [Fact]
    public void GoldPlateDarkensTrim()
    {
        var r = Wear.TrimUnderGold(new Dictionary<string, string> { ["metal"] = "#d2b25a:metal" });
        Assert.Equal(Wear.GoldTrimBronze, r["trim"]);
    }

    [Theory]
    [InlineData("#d2b25a")]
    [InlineData("#c8ccd4")]
    [InlineData("#8a2a22")]
    public void OtherMetalDyesKeepTrim(string dye)
    {
        var d = new Dictionary<string, string> { ["metal"] = dye };
        Assert.Same(d, Wear.TrimUnderGold(d));
    }

    [Fact]
    public void ExplicitTrimWins()
    {
        var d = new Dictionary<string, string> { ["metal"] = "#d2b25a:metal", ["trim"] = "#101010" };
        var r = Wear.TrimUnderGold(d);
        Assert.Same(d, r);
        Assert.Equal("#101010", r["trim"]);
    }

    [Fact]
    public void HexLosesSuffix()
    {
        Assert.Equal("#d2b25a", Wear.DyeFinish("#d2b25a:metal").Hex);
        Assert.Equal("#c8ccd4", Wear.DyeFinish(" #c8ccd4 : metal ").Hex);
    }
}
