using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class LampStateTests
{
    [Fact]
    public void FlameFallsWithLifeAndGuttersOnlyLow()
    {
        Assert.Equal(1f, LampState.Height(1), 0.001f);
        Assert.True(LampState.Height(0.55f) < 0.65f && LampState.Height(0.55f) > 0.55f);
        Assert.True(LampState.Height(0.25f) <= 0.4f);
        Assert.True(LampState.Glow(LampState.Height(0.55f)) < 0.55f && LampState.Glow(LampState.Height(0.18f)) < 0.2f);
        Assert.True(LampState.Height(0.18f) < LampState.Height(0.55f));
        Assert.Equal(0f, LampState.GutterFor(0.31f));
        Assert.True(LampState.GutterFor(0.30f) > 0.3f);
        Assert.Equal(1f, LampState.GutterFor(0.05f), 0.001f);
        Assert.Equal(0f, LampState.GutterFor(0f));
    }

    [Fact]
    public void GoesOutAtZeroAndRelights()
    {
        var s = new LampState();
        for (int i = 0; i < 30; i++) s.Tick(1, 1 / 60f, i / 60.0);
        Assert.True(s.OutT < 0 && s.Light > 0.9f);
        s.Tick(0, 1 / 60f, 0.5);
        Assert.Equal(0f, s.OutT);
        Assert.Equal(0f, s.Light);
        s.Tick(0, 0.5f, 1.0);
        Assert.Equal(0.5f, s.OutT, 0.001f);
        s.Tick(0.5f, 1 / 60f, 1.1);
        Assert.True(s.OutT < 0 && s.Flame > 0 && s.Flame < 0.2f);
        for (int i = 0; i < 60; i++) s.Tick(0.5f, 1 / 60f, 1.1 + i / 60.0);
        Assert.Equal(LampState.Height(0.5f), s.Flame, 0.01f);
    }

    [Fact]
    public void GutteringFlickersHarderThanSteady()
    {
        float lo1 = 9, lo2 = 9, hi2 = 0;
        for (int i = 0; i < 600; i++)
        {
            lo1 = System.Math.Min(lo1, LampState.FlickerAt(i / 60.0, 0));
            lo2 = System.Math.Min(lo2, LampState.FlickerAt(i / 60.0, 1));
            hi2 = System.Math.Max(hi2, LampState.FlickerAt(i / 60.0, 1));
        }
        Assert.True(lo1 > 0.95f);
        Assert.True(lo2 < 0.75f && hi2 > 1.25f && hi2 < 1.45f);
    }
}
