using System.Collections.Generic;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>P4 clips over B's bridge clips (P4Overlay): a P4 name wins, new names add, --p4-as aliases.</summary>
public class P4OverlayTests
{
    static readonly string[] Bridge = { "idle_warden_town", "walk_warden_town", "run_warden" };

    [Fact]
    public void SameNameWinsNewNameAdds()
    {
        var plan = P4Overlay.Plan(Bridge, new[] { "run_warden", "p4_proof_idle" }, null);
        Assert.Equal("run_warden", plan["run_warden"]);
        Assert.Equal("p4_proof_idle", plan["p4_proof_idle"]);
        Assert.False(plan.ContainsKey("idle_warden_town"));   // (bridge clips not named by P4 stay the bridge's)
        Assert.Equal(2, plan.Count);
    }

    [Fact]
    public void AliasPlaysAP4ClipUnderATargetName()
    {
        var bad = new List<string>();
        var plan = P4Overlay.Plan(Bridge, new[] { "p4_proof_idle", "p4_proof_walk" },
            "idle_warden_town=p4_proof_idle, walk_warden_town=p4_proof_walk,run_warden=missing,junk", bad);
        Assert.Equal("p4_proof_idle", plan["idle_warden_town"]);
        Assert.Equal("p4_proof_walk", plan["walk_warden_town"]);
        Assert.False(plan.ContainsKey("run_warden"));
        Assert.Equal(new[] { "run_warden=missing" }, bad);
    }

    [Fact]
    public void AliasOverridesASameNamedP4Clip()
    {
        var plan = P4Overlay.Plan(Bridge, new[] { "run_warden", "p4_run" }, "run_warden=p4_run");
        Assert.Equal("p4_run", plan["run_warden"]);
    }
}
