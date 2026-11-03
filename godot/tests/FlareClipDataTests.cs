using System.Linq;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A Flare's own clip, grip and free time are data (FlareDef.Clip / Grip / ClipFree); no keys means today's behaviour.</summary>
public class FlareClipDataTests
{
    [Fact]
    public void TheLongCutCarriesItsClipGripAndFreeTime()
    {
        // (Animation 61, 2 Nov: the clip is back ON after its fix round's max judge, PASS-WITH-NOTES; Animation 60 had it off.)
        var f = Lamps.Flare("the_long_cut")!;
        Assert.Equal("flare_long_cut", f.Clip);
        Assert.Equal("sunder_blade", f.Grip);
        Assert.Equal(0.9, f.ClipFree, 3);
    }

    [Fact]
    public void BurnsTwiceAndBulwarkCarryNone()
    {
        foreach (var id in new[] { "burns_twice", "bell_of_the_morning" })
        {
            var f = Lamps.Flare(id)!;
            Assert.Null(f.Clip); Assert.Null(f.Grip); Assert.Equal(0, f.ClipFree);
        }
    }

    [Fact]
    public void OnlyTheLongCutCarriesClipDataToday() =>
        Assert.Equal(["the_long_cut"], Lamps.Flares.Values.Where(f => f.Clip != null || f.Grip != null).Select(f => f.Id).ToArray());
}
