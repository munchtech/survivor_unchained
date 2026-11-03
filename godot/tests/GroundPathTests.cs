using System;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>GroundPath: the autopilot's way round what is solid (it follows the tracker's pins with it).</summary>
public class GroundPathTests
{
    [Fact]
    public void GoesRoundAWallNotThroughIt()
    {
        var col = new CollisionWorld(120);
        // A wall 20 m long across the straight line from (0,-8) to (0,8), open at both ends.
        col.AddBox(0, 0, 10, 0.5);
        var route = GroundPath.Find(col, 0, -8, 0, 8);
        Assert.NotNull(route);
        var at = (X: 0.0, Z: -8.0);
        foreach (var w in route!)
        {
            Assert.True(GroundPath.Clear(col, at, w, 0.45), $"leg to ({w.X:0.0},{w.Z:0.0}) touches the wall");
            at = w;
        }
        Assert.True(Math.Abs(at.X) < 0.6 && Math.Abs(at.Z - 8) < 0.6);
        Assert.True(route.Count >= 2, "a straight line through the wall is not a route");
    }

    [Fact]
    public void AGoalInsideSomethingSolidIsReachedBesideIt()
    {
        var col = new CollisionWorld(120);
        col.AddCircle(5, 0, 1.2); // a counter, with the pin at its middle
        var route = GroundPath.Find(col, -5, 0, 5, 0);
        Assert.NotNull(route);
        var end = route![^1];
        Assert.True(Math.Sqrt((end.X - 5) * (end.X - 5) + end.Z * end.Z) < 2.5);
    }

    [Fact]
    public void ShutInIsNoRoute()
    {
        var col = new CollisionWorld(120);
        foreach (var (x, z, hw, hd) in new[] { (0.0, 6.0, 7.0, 0.5), (0.0, -6.0, 7.0, 0.5), (6.0, 0.0, 0.5, 7.0), (-6.0, 0.0, 0.5, 7.0) }) col.AddBox(x, z, hw, hd);
        Assert.Null(GroundPath.Find(col, 0, 0, 20, 0, margin: 6));
    }
}
