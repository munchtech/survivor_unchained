using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her 2D move node's input: velocity in her facing frame (x right, y forward), and the --act-walk parse.</summary>
public class Move2DTests
{
    static void Near((float X, float Y) a, float x, float y) { Assert.Equal((double)x, (double)a.X, 3); Assert.Equal((double)y, (double)a.Y, 3); }

    [Fact]
    public void FacingPlusZ_ForwardBackLeftRight()
    {
        Near(Move2D.Local(0, 2, 0), 0, 2);       // forward
        Near(Move2D.Local(0, -2, 0), 0, -2);     // back
        Near(Move2D.Local(2, 0, 0), -2, 0);      // +X is her left at yaw 0
        Near(Move2D.Local(-2, 0, 0), 2, 0);      // her right
    }

    [Fact]
    public void Diagonal()
    {
        Near(Move2D.Local(1, 1, 0), -1, 1);      // forward-left
        Near(Move2D.Local(-1, -1, 0), 1, -1);    // back-right
    }

    [Fact]
    public void FacingTurned90()
    {
        float yaw = MathF.PI / 2;                // faces +X
        Near(Move2D.Local(3, 0, yaw), 0, 3);     // +X is now forward
        Near(Move2D.Local(0, 3, yaw), 3, 0);     // +Z is her right (facing +X, left is -Z)
        Near(Move2D.Local(0, -3, yaw), -3, 0);   // her left
        Near(Move2D.Local(-3, 0, yaw), 0, -3);   // back
    }

    [Fact]
    public void WorldIsTheInverse()
    {
        foreach (float yaw in new[] { 0f, 0.7f, 2.1f, -1.3f })
        {
            var l = Move2D.Local(1.5f, -0.8f, yaw);
            var w = Move2D.World(l.X, l.Y, yaw);
            Assert.Equal(1.5, (double)w.X, 3); Assert.Equal(-0.8, (double)w.Z, 3);
        }
    }

    [Theory]
    [InlineData(0, 0, 0.84)]
    [InlineData(180, 0, -0.84)]
    [InlineData(90, -0.84, 0)]
    [InlineData(-90, 0.84, 0)]
    public void ActWalkMakesTheLocalVelocityItAsks(double deg, double right, double fwd)
    {
        foreach (float yaw in new[] { 0f, 1.1f, -2.5f })
        {
            var w = Move2D.ActWalkWorld((deg, 0.84), yaw);
            var l = Move2D.Local(w.X, w.Z, yaw);
            Assert.Equal(right, (double)l.X, 2); Assert.Equal(fwd, (double)l.Y, 2);
        }
    }

    [Fact]
    public void ParseActWalk()
    {
        Assert.Equal((0.0, 0.84), Move2D.ParseActWalk("0,0.84"));
        Assert.Equal((-90.0, 1.5), Move2D.ParseActWalk(" -90 , 1.5".Replace(" ", "")));
        Assert.Equal((180.0, 0.0), Move2D.ParseActWalk("180,0"));
        Assert.Null(Move2D.ParseActWalk(null));
        Assert.Null(Move2D.ParseActWalk(""));
        Assert.Null(Move2D.ParseActWalk("90"));
        Assert.Null(Move2D.ParseActWalk("a,b"));
        Assert.Null(Move2D.ParseActWalk("0,-1"));
        Assert.Null(Move2D.ParseActWalk("1,2,3"));
    }
}
