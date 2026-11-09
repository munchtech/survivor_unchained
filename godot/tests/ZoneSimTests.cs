using SurvivorUnchained.Balance;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The zone sim (balance/Harness/ZoneSim.cs, M5-F) plays the real Low Ford from the Wake.</summary>
public class ZoneSimTests
{
    [Fact]
    public void The_human_bot_reaches_the_Ford_Warden_within_the_cap()
    {
        // (one seed, tier II: a run takes a few seconds; the whole zone, the Warden and the day stretch to the gate)
        var r = ZoneSim.Play(new ZoneRunSpec(1, "lowford", "human", 2), quiet: true);
        Assert.True(r.BossReached, r.StuckAt ?? "capped");
        Assert.True(r.Seconds < ZoneSim.Cap);
        Assert.True(r.Packs > 0 && r.Kills > 0);
    }
}
