using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her raise corrective's ramp (Play/RaiseRamp.cs): nothing at rest, full overhead, smooth between, volume kept.</summary>
public class RaiseRampTests
{
    [Fact]
    public void RestArmIsZero() => Assert.Equal(0f, RaiseRamp.Weight(-47f, -10f, 70f));

    [Fact]
    public void OverheadIsFull() => Assert.Equal(1f, RaiseRamp.Weight(85f, -10f, 70f));

    [Fact]
    public void MidwayIsHalfAndRisesSmoothly()
    {
        Assert.Equal(0.5f, RaiseRamp.Weight(30f, -10f, 70f), 0.0001f);
        Assert.True(RaiseRamp.Weight(-9f, -10f, 70f) < 0.002f);
        Assert.True(RaiseRamp.Weight(20f, -10f, 70f) < RaiseRamp.Weight(21f, -10f, 70f));
    }

    [Fact]
    public void ElevationFromUpComponent()
    {
        Assert.Equal(90f, RaiseRamp.Elevation(1f), 0.001f);
        Assert.Equal(0f, RaiseRamp.Elevation(0f), 0.001f);
        Assert.Equal(-30f, RaiseRamp.Elevation(-0.5f), 0.001f);
    }

    [Fact]
    public void StretchKeepsVolume()
    {
        var (s, a, u) = RaiseRamp.Stretch(0.7f, 0.08f, 0.03f);
        Assert.Equal(1f, s * a * u, 0.00001f);
        Assert.True(u > 1 && s > 1 && a < 1);
        Assert.Equal((1f, 1f, 1f), RaiseRamp.Stretch(0f, 0.08f, 0.03f));
    }
}
