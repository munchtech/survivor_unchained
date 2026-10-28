using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class HeartPulseTests
{
    [Fact]
    public void EdgeIsOffOverThirtyAndGrowsTowardNone()
    {
        Assert.Equal(0f, HeartPulse.EdgeStrength(0.31));
        Assert.Equal(0.3f, HeartPulse.EdgeStrength(0.30), 0.001f);
        Assert.True(HeartPulse.EdgeStrength(0.15) > 0.3f && HeartPulse.EdgeStrength(0.15) < HeartPulse.EdgeStrength(0.05));
        Assert.Equal(1f, HeartPulse.EdgeStrength(0), 0.001f);
    }

    [Fact]
    public void BeatPacesLikeTheSound()
    {
        Assert.Equal(1.05, HeartPulse.Period(0.3), 3);
        Assert.Equal(0.65, HeartPulse.Period(0), 3);
        Assert.True(HeartPulse.Shape(0) > 0.99f && HeartPulse.Shape(0.24) > 0.55f && HeartPulse.Shape(0.6) < 0.1f);
    }

    [Fact]
    public void HerLightFallsWithHerLife()
    {
        Assert.Equal(HeartPulse.PoolFull, HeartPulse.PoolGain(1), 0.001f);
        Assert.Equal(HeartPulse.PoolFull * 0.5f, HeartPulse.PoolGain(0.55), 0.001f);
        Assert.True(HeartPulse.PoolGain(0.18) < HeartPulse.PoolFull * 0.3f && HeartPulse.PoolGain(0.18) > 0);
        Assert.Equal(0f, HeartPulse.PoolGain(0));
        // continuous at the joins
        Assert.Equal(HeartPulse.PoolGain(0.2499), HeartPulse.PoolGain(0.25), 0.002f);
        Assert.Equal(HeartPulse.PoolGain(0.5499), HeartPulse.PoolGain(0.55), 0.002f);
        Assert.Equal(1f, HeartPulse.Flicker(0.5, 3.3));
        for (double t = 0; t < 5; t += 0.07) Assert.InRange(HeartPulse.Flicker(0.1, t), 0.3f, 1f);
    }
}
