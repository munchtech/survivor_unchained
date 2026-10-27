using System;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The close view's room (Play/CameraRoom.cs): a post is seen past, a cart passed over, a wall still holds
/// the lens before it, and the room glides with no frame's jump over its top speed.</summary>
public class CameraRoomTests
{
    static Collider Circle(double r) => new() { Kind = ColliderKind.Circle, R = r, Hw = r, Hd = r };
    static Collider Box(double hw, double hd) => new() { Kind = ColliderKind.Box, Hw = hw, Hd = hd, R = Math.Sqrt(hw * hw + hd * hd) };

    [Fact]
    public void APostIsSeenPastUnlessTheLensWouldStandInIt()
    {
        Assert.False(CameraRoom.Blocks(Circle(0.3), 0.2, 1.1, 3, 4.5));
        Assert.True(CameraRoom.Blocks(Circle(0.3), 1, 1.1, 3, 4.5));
    }

    [Fact]
    public void ALowThingIsPassedOverAndAWallHolds()
    {
        // (the line at t 0.5 is 2.05 m up)
        Assert.False(CameraRoom.Blocks(Box(1.2, 1.5), 0.5, 1.1, 3, 1.2));
        Assert.True(CameraRoom.Blocks(Box(3, 3), 0.5, 1.1, 3, 7));
        Assert.True(CameraRoom.Blocks(Box(0.5, 18), 0.5, 1.1, 3, null));
        // (a long fence is no post: its height decides)
        Assert.False(CameraRoom.Blocks(Box(0.2, 1.4), 0.5, 1.1, 3, 1.0));
    }

    [Fact]
    public void TheRoomGlidesInAndOut()
    {
        float room = 1, worst = 0;
        for (int i = 0; i < 120; i++) { float n = CameraRoom.Step(room, 0.3f, 1 / 60f); worst = Math.Max(worst, Math.Abs(n / room - 1)); room = n; }
        Assert.InRange(room, 0.3f, 0.31f);
        Assert.True(worst < 0.035f, $"a frame moved {worst:P1}");
        for (int i = 0; i < 400; i++) { float n = CameraRoom.Step(room, 1, 1 / 60f); worst = Math.Max(worst, Math.Abs(n / room - 1)); room = n; }
        Assert.InRange(room, 0.98f, 1f);
        Assert.True(worst < 0.035f);
    }
}
