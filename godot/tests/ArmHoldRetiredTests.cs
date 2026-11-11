using SurvivorUnchained.Play;
using Xunit;

/// <summary>B (P1) has no arm-hold layer: its walk and run carry compatible holds as clip data (P4), so the move graph
/// blends them as authored. A keeps the layer until it leaves the game.</summary>
public class ArmHoldRetiredTests
{
    [Fact]
    public void BGetsNoLayer_AKeepsIt()
    {
        Assert.False(ArmHold.Layered(isB: true));
        Assert.True(ArmHold.Layered(isB: false));
    }

    // PlayerView builds the filtered "arms" copy, adds HerArmHold and eases the grip only behind the layered flag,
    // which is ArmHold.Layered(isB), isB = P1Body.IsB(...).
    [Fact]
    public void PlayerViewGatesEveryPieceOfTheLayer()
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        var src = System.IO.File.ReadAllText(System.IO.Path.Combine(d!.FullName, "src", "Actors", "PlayerView.cs"));
        Assert.Contains("isB = P1Body.IsB(person.Skeleton);", src);
        Assert.Contains("layered = ArmHold.Layered(isB);", src);
        int gate = src.IndexOf("if (layered)\n            {\n                aIdle = new", System.StringComparison.Ordinal);
        if (gate < 0) gate = src.IndexOf("if (layered)\r\n            {\r\n                aIdle = new", System.StringComparison.Ordinal);
        Assert.True(gate > 0, "the arms copy (and its filter) is built only when layered");
        Assert.True(src.IndexOf("FilterEnabled = true", gate, System.StringComparison.Ordinal) > gate);
        int mod = src.IndexOf("armMod = new HerArmHold();", System.StringComparison.Ordinal);
        Assert.True(mod > 0 && src.LastIndexOf("if (layered)", mod, System.StringComparison.Ordinal) > mod - 80, "HerArmHold only when layered");
        Assert.Contains("if (layered && idleNode != null && runNode != null)", src);   // the grip ease
    }
}

public class P4SpeedTests
{
    [Fact]
    public void P4GaitSpeedWinsOnB_ElseBridge()
    {
        var p4 = new System.Collections.Generic.Dictionary<string, float> { ["walk_warden_town"] = 1.18f, ["idle_warden"] = 0f };
        Assert.Equal(1.18f, SurvivorUnchained.Play.P4Overlay.Speed("walk_warden_town", p4, 1.2f));
        Assert.Equal(5.1f, SurvivorUnchained.Play.P4Overlay.Speed("run_warden", p4, 5.1f));
        Assert.Equal(0.5f, SurvivorUnchained.Play.P4Overlay.Speed("idle_warden", p4, 0.5f));
    }
}
