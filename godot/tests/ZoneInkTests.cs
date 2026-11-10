using System.Collections.Generic;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class ZoneInkTests
{
    static int At(byte[] px, int n, double extent, double x, double z, int ch)
        => px[((int)((z / extent + 0.5) * n) * n + (int)((x / extent + 0.5) * n)) * 4 + ch];

    [Fact]
    public void PlaceWithNoRoadGetsYardInk()
    {
        var s = new List<ZoneInk.Shape> { new(ZoneInk.Yard, 10, 10, 0, 0, 0, 'y') };
        // a stone square 8 m each way round (10, 10), grass beyond, no road anywhere
        var px = ZoneInk.Build(s, 200, 100, null, (x, z) => System.Math.Abs(x - 10) < 8 && System.Math.Abs(z - 10) < 8);
        Assert.Equal(255, At(px, 200, 100, 10, 10, ZoneInk.Yard));
        Assert.Equal(255, At(px, 200, 100, 16, 4, ZoneInk.Yard));   // flooded over its ground
        Assert.Equal(0, At(px, 200, 100, 20, 10, ZoneInk.Yard));    // not onto the grass
    }

    [Fact]
    public void PlaceOnGrassGetsADisc_PlaceOnRoadNone()
    {
        var s = new List<ZoneInk.Shape> { new(ZoneInk.Yard, -20, 0, 0, 0, 0, 'y'), new(ZoneInk.Yard, 20, 0, 0, 0, 0, 'y') };
        var px = ZoneInk.Build(s, 200, 100, (x, z) => x > 10, null);
        Assert.Equal(255, At(px, 200, 100, -20, 0, ZoneInk.Yard));
        Assert.Equal(255, At(px, 200, 100, -18, 0, ZoneInk.Yard));
        Assert.Equal(0, At(px, 200, 100, -24, 0, ZoneInk.Yard));
        Assert.Equal(0, At(px, 200, 100, 20, 0, ZoneInk.Yard));
    }

    [Fact]
    public void PropsAndBuildingsInkTheirChannels()
    {
        var s = new List<ZoneInk.Shape>
        {
            new(ZoneInk.Prop, 0, 0, 3, 1, System.Math.PI / 2, 'b'),     // a tent 6 x 2 m turned a quarter: 2 x 6 on the sheet
            new(ZoneInk.Building, 30, 30, 5, 0, 0, 'h'),
            new(ZoneInk.Soft, -30, 30, 2, 2, 0, 'b'),
        };
        var px = ZoneInk.Build(s, 200, 100, null, null);
        Assert.Equal(255, At(px, 200, 100, 0, 2.5, ZoneInk.Prop));
        Assert.Equal(0, At(px, 200, 100, 2.5, 0, ZoneInk.Prop));
        Assert.Equal(255, At(px, 200, 100, 30, 30, ZoneInk.Building));
        Assert.Equal(0, At(px, 200, 100, 36, 30, ZoneInk.Building));
        Assert.Equal(255, At(px, 200, 100, -30, 30, ZoneInk.Soft));
    }

    [Fact]
    public void WaystationDataNamesInkForItsYards()
    {
        var m = SurvivorUnchained.World.ZoneMeta.Load("waystation");
        var s = ZoneInk.From(m);
        Assert.Contains(s, x => x.Channel == ZoneInk.Building);
        Assert.Contains(s, x => x.Channel == ZoneInk.Prop);
        Assert.True(s.FindAll(x => x.Channel == ZoneInk.Yard).Count >= m.Fires.Count + 10);
    }
}
