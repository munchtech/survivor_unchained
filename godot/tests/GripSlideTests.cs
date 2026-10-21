using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The grip slide (Play/GripSlide.cs): which clip's value counts, and the ease between them.</summary>
public class GripSlideTests
{
    [Fact]
    public void FullShotWinsOverUpperAndMove() =>
        Assert.Equal(0.3f, GripSlide.Target(true, 0.3f, true, 0.2f, 0.5f, 0.1f, 0.0f));

    [Fact]
    public void UpperShotWinsOverMove() =>
        Assert.Equal(0.2f, GripSlide.Target(false, 0.3f, true, 0.2f, 0.5f, 0.1f, 0.0f));

    [Fact]
    public void MoveBlendMixesIdleAndRunAndClamps()
    {
        Assert.Equal(0.08f, GripSlide.Target(false, 0, false, 0, 0f, 0.08f, 0f), 5);
        Assert.Equal(0.04f, GripSlide.Target(false, 0, false, 0, 0.5f, 0.08f, 0f), 5);
        Assert.Equal(0.08f, GripSlide.Target(false, 0, false, 0, -3f, 0.08f, 0f), 5);
        Assert.Equal(0f, GripSlide.Target(false, 0, false, 0, 7f, 0.08f, 0f), 5);
    }

    [Fact]
    public void EaseKeepsAtZeroDtAndReachesTargetWithLargeDt()
    {
        Assert.Equal(0.02f, GripSlide.Ease(0.02f, 0.09f, 0f));
        Assert.Equal(0.09f, GripSlide.Ease(0.02f, 0.09f, 100f), 4);
    }

    [Fact]
    public void EaseMovesMonotonicallyTowardTarget()
    {
        float a = GripSlide.Ease(0f, 0.09f, 0.016f), b = GripSlide.Ease(a, 0.09f, 0.016f);
        Assert.InRange(a, 0.0001f, 0.0899f);
        Assert.True(b > a && b < 0.09f);
    }
}
