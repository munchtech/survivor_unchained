using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The "leave" rule of data/content/zone_resets.json (World/ZoneReset.cs): a zone clears when she enters it from another zone.</summary>
public class ZoneResetTests
{
    static WorldState Dirty(string zone)
    {
        var w = new WorldState { Day = 1 };
        w.Zone(zone)["boars.done"] = true;
        w.Facts["lampposts.x"] = true;
        return w;
    }

    [Fact]
    public void Leave_from_another_zone_clears()
    {
        var w = Dirty("verge");
        Assert.Equal("leave", ZoneReset.For("verge")!.Reset);
        Assert.True(ZoneReset.Apply(w, "verge", "lowford"));
        Assert.False(w.Zone("verge").ContainsKey("boars.done"));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("load")]
    [InlineData("death")]
    [InlineData("verge")]
    public void Leave_keeps_on_a_load_a_rise_or_a_re_entry(string? from)
    {
        var w = Dirty("verge");
        Assert.False(ZoneReset.Apply(w, "verge", from));
        Assert.True(w.Zone("verge").ContainsKey("boars.done"));
    }

    [Fact]
    public void Never_keeps()
    {
        var w = Dirty("waystation");
        Assert.False(ZoneReset.Apply(w, "waystation", "verge"));
        Assert.True(w.Zone("waystation").ContainsKey("boars.done"));
    }

    [Fact]
    public void A_world_fact_is_never_touched()
    {
        var w = Dirty("lowford");
        ZoneReset.Apply(w, "lowford", "verge");
        Assert.True(w.Fact("lampposts.x").Truthy);
    }
}
