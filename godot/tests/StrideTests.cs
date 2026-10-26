using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class StrideTests
{
    [Fact]
    public void WeightsRiseWithSpeedAndEndAtZeroAndOne()
    {
        float pw = -1, pr = -1;
        for (float s = 0; s <= 8; s += 0.05f)
        {
            var (w, r) = Stride.Weights(s, 1.3f, 5f, true);
            Assert.True(w >= pw && r >= pr);
            pw = w; pr = r;
        }
        Assert.Equal((0f, 0f), Stride.Weights(0, 1.3f, 5f, true));
        Assert.Equal((1f, 1f), Stride.Weights(8, 1.3f, 5f, true));
    }

    [Fact]
    public void NoWalkIsTodaysBlend()
    {
        foreach (var s in new[] { 0f, 0.25f, 1f, 2.2f, 4f })
        {
            var (w, r) = Stride.Weights(s, 1.3f, 5f, false);
            Assert.Equal(0f, w);
            float t = System.Math.Clamp((s - 0.25f) / 1.95f, 0f, 1f);
            Assert.Equal(t * t * (3 - 2 * t), r, 1e-3f);
            Assert.Equal(0.8f / 0.55f, Stride.Period(s, 0.9f, 1.3f, 0.8f, 0.55f, r, false), 1e-3f);
        }
    }

    [Fact]
    public void PeriodIsContinuousAcrossTheBand()
    {
        float last = float.NaN;
        for (float s = 0.3f; s <= 6f; s += 0.01f)
        {
            var (_, r) = Stride.Weights(s, 1.3f, 5f, true);
            float p = Stride.Period(s, 1.1f, 1.3f, 0.8f, Stride.RunScale(s, 5f), r, true);
            if (!float.IsNaN(last)) Assert.True(System.Math.Abs(p - last) < 0.05f, $"jump at {s}");
            last = p;
        }
    }

    [Fact]
    public void PhaseWraps()
    {
        Assert.Equal(0.1f, Stride.Advance(0.9f, 0.2f, 1f), 1e-3f);
        Assert.InRange(Stride.Advance(0.99f, 10.37f, 0.7f), 0f, 0.9999f);
        Assert.Equal(0.3f, Stride.Advance(0.3f, 1f, 0f), 1e-3f);
    }

    [Fact]
    public void PureWalkHoldsTheFeet()
    {
        // At walk speed the clip plays at its own rate (period = its length); at 1.2x it plays 1.2x faster.
        Assert.Equal(1.1f, Stride.Period(1.3f, 1.1f, 1.3f, 0.8f, 0.3f, 0f, true), 1e-3f);
        Assert.Equal(1.1f / 1.2f, Stride.Period(1.56f, 1.1f, 1.3f, 0.8f, 0.3f, 0f, true), 1e-3f);
    }
}
