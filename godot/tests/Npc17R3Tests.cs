using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>NPC 17 round 3: risen jitter, delay and avoidance (Sim.Vary); talking pairs and side-by-side spacing (Play.FolkSpacing).</summary>
public class Npc17R3Tests
{
    [Fact]
    public void JitterStaysInRadiusAndIsNotOnAGrid()
    {
        var offs = Enumerable.Range(1, 50).Select(i => Vary.Jitter(i / 51.0, 1.5)).ToList();
        Assert.All(offs, o => Assert.True(Math.Sqrt(o.X * o.X + o.Z * o.Z) <= 1.5 + 1e-9));
        Assert.Equal(50, offs.Distinct().Count());
        Assert.Equal(50, offs.Select(o => Math.Round(o.X, 4)).Distinct().Count());
    }

    [Fact]
    public void DelayIsWithinZeroAndMax()
    {
        for (int i = 0; i < 100; i++)
        {
            double d = Vary.Delay(i / 100.0, 2.5);
            Assert.InRange(d, 0, 2.5);
        }
    }

    [Fact]
    public void AvoidIgnoresBehindAndFarSideSteersAheadPushesOutInside()
    {
        // heading +x from the origin; obstacle radius 0.5, margin 0.5 (clear 1.0)
        Assert.Equal((0.0, 0.0), Vary.Avoid(0, 0, 1, 0, -3, 0, 0.5, 0.5));   // behind
        Assert.Equal((0.0, 0.0), Vary.Avoid(0, 0, 1, 0, 3, 4, 0.5, 0.5));    // far to the side
        var a = Vary.Avoid(0, 0, 1, 0, 2, 0, 0.5, 0.5);                      // dead ahead
        Assert.True(Math.Abs(a.Z) > 0.1);
        Assert.True(Math.Abs(a.X) < 1e-9);
        var p = Vary.Avoid(0, 0, 1, 0, 0.3, 0, 0.5, 0.5);                    // inside: away from it (-x)
        Assert.True(p.X < 0);
    }

    [Fact]
    public void PairSpotIsTalkFromTheLead()
    {
        foreach (int side in new[] { -1, 1 })
        {
            var (x, z) = FolkSpacing.PairSpot(3, -2, 0.6, 0.8, side);
            Assert.Equal(FolkSpacing.Talk, Math.Sqrt((x - 3) * (x - 3) + (z + 2) * (z + 2)), 9);
        }
        Assert.Equal(1.1, FolkSpacing.Talk);
    }

    [Fact]
    public void BesidePushesInLinePairApartAndIsZeroWhenClear()
    {
        // view looks +z; "side" is across x
        var a = FolkSpacing.Beside(0.1, 0, 0, 1, 0, 1, 0.5);
        Assert.True(a.X != 0);
        var b = FolkSpacing.Beside(-0.1, 0, 0, 1, 0, 1, 0.5);
        Assert.True(Math.Sign(a.X) == -Math.Sign(b.X));
        Assert.Equal((0.0, 0.0), FolkSpacing.Beside(FolkSpacing.Gap, 0, 0, 0, 0, 1, 0.5));
        Assert.Equal((0.0, 0.0), FolkSpacing.Beside(0.1, 0, 0, 4.0, 0, 1, 0.5));
    }
}
