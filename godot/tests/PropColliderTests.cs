using System;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

public class PropColliderTests
{
    [Fact]
    public void RotatedColBoxLandsWhereGodotPutsIt()
    {
        using var doc = JsonDocument.Parse("{\"x\":10,\"z\":0,\"rot\":1.5707963267948966,\"col\":[0.5,0,1,0.25]}");
        var c = ZoneMeta.PropCollider(doc.RootElement)!;
        Assert.Equal(10, c.X, 6);
        Assert.Equal(-0.5, c.Z, 6);
        Assert.Equal(1, c.Hw, 6);
        Assert.Equal(0.25, c.Hd, 6);
        Assert.Equal("prop", c.Tag);

        // Local x (the long side) runs along world -z: the box spans z -1.5..0.5 and x 9.75..10.25.
        var w = new CollisionWorld(60);
        w.AddBox(c.X, c.Z, c.Hw, c.Hd, c.Rot);
        Assert.True(w.Blocked(10, -1.3, 0.05));
        Assert.True(w.Blocked(10, 0.4, 0.05));
        Assert.False(w.Blocked(10, -1.7, 0.05));
        Assert.False(w.Blocked(10.6, -0.5, 0.05));
    }

    [Fact]
    public void EntriesWithoutColAddNothing()
    {
        using var doc = JsonDocument.Parse("{\"x\":1,\"z\":2,\"a\":[0,0],\"b\":[1,1]}");
        Assert.Null(ZoneMeta.PropCollider(doc.RootElement));
    }

    [Fact]
    public void WaystationKeepsItsColliders()
    {
        var withProps = ZoneMeta.Load("waystation");
        var plain = Json.Parse<ZoneMeta>(DataFiles.Text("zones/waystation/zone.json"));
        Assert.True(withProps.Colliders.Count >= plain.Colliders.Count);
        foreach (var c in withProps.Colliders.Where(c => c.Tag == "prop"))
            Assert.True(double.IsFinite(c.X) && double.IsFinite(c.Z) && double.IsFinite(c.Hw)
                && double.IsFinite(c.Hd) && double.IsFinite(c.Rot) && double.IsFinite(c.R));
        Assert.Equal(withProps.Colliders.Count, withProps.Colliders.Select(c => c.Id).Distinct().Count());
    }
}
