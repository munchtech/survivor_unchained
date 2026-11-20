using System.Linq;
using SurvivorUnchained.World;
using Xunit;

public class ZoneWoodTests
{
    [Fact]
    public void Orphan_colliders_with_nothing_drawn_are_gone()
    {
        var z = ZoneMeta.Load("lowford");
        // a known orphan: nothing drawn at the road's side at (9.5, 38)
        Assert.DoesNotContain(z.Colliders, c => c.Tag == null && System.Math.Abs(c.X - 9.5) < 0.01 && System.Math.Abs(c.Z - 38) < 0.01 && c.R < 1);
        // the big cliff-line circles stay
        Assert.True(z.Colliders.Count(c => c.R >= 3.5) > 50);
    }
}
