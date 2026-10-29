using System;
using System.Linq;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

public class NpcDyePickTests
{
    [Fact]
    public void PicksRepeatAndSpread()
    {
        // the same seed and copy pick the same; across copies every entry of a palette turns up, none dominates
        Assert.Equal(NpcDyePick.Pick(10, 3, 0, 8), NpcDyePick.Pick(10, 3, 0, 8));
        var counts = new int[8];
        for (int copy = 0; copy < 800; copy++) counts[NpcDyePick.Pick(10, copy, 0, 8)]++;
        Assert.All(counts, c => Assert.InRange(c, 60, 140));
        // channels pick independently of each other
        int same = Enumerable.Range(0, 200).Count(c => NpcDyePick.Pick(1, c, 0, 8) == NpcDyePick.Pick(1, c, 1, 8));
        Assert.InRange(same, 5, 50);
        Assert.Equal(-1, NpcDyePick.Pick(1, 1, 0, 0));
    }

    [Fact]
    public void ScaleAndPhaseStayInRange()
    {
        for (int copy = 0; copy < 500; copy++)
        {
            Assert.InRange(NpcDyePick.Scale(7, copy, 0.04), 0.96, 1.04);
            Assert.InRange(NpcDyePick.Phase(7, copy), 0.0, 1.0);
        }
        Assert.Equal(1.0, NpcDyePick.Scale(7, 3, 0));
    }

    [Fact]
    public void ClampKeepsHueAndHoldsLightness()
    {
        var woad = NpcDyePick.Hex("#2f4466")!.Value;
        var o = NpcDyePick.ToOklab(woad);
        // inside the range: untouched
        Assert.Equal(woad, NpcDyePick.ClampL(woad, 0.1, 0.9));
        // a light shawl's range lifts a dark dye, keeping its hue
        var lifted = NpcDyePick.ClampL(woad, 0.645, 0.865);
        var lo = NpcDyePick.ToOklab(lifted);
        Assert.InRange(lo.L, 0.64, 0.65);
        Assert.InRange(Math.Atan2(lo.B, lo.A) - Math.Atan2(o.B, o.A), -0.05, 0.05);
        // round trip
        var back = NpcDyePick.FromOklab(o);
        Assert.InRange(Math.Abs(back.R - woad.R) + Math.Abs(back.G - woad.G) + Math.Abs(back.B - woad.B), 0, 1e-6);
    }

    [Fact]
    public void HexIsLinear()
    {
        var w = NpcDyePick.Hex("#ffffff")!.Value;
        Assert.InRange(w.R, 0.9999, 1.0001);
        Assert.InRange(NpcDyePick.Hex("#808080")!.Value.G, 0.2158, 0.2160);
        Assert.Null(NpcDyePick.Hex("red"));
        Assert.Null(NpcDyePick.Hex(null));
    }
}
