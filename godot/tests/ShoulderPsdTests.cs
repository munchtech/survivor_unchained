using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her shoulder pose-space correctives' weights (Play/ShoulderPsd.cs): nothing with the arm below
/// EaseFrom (60: the Look's and the idles' arms reach ~55), each sample whole at its own raise (the level one at 80),
/// a partition between samples, side to front by the azimuth.</summary>
public class ShoulderPsdTests
{
    static float[] W(float a, float az, float rise = 0f) { var w = new float[ShoulderPsd.Shapes.Length]; ShoulderPsd.Weights(a, az, rise, w); return w; }

    [Theory]
    [InlineData(0f, 0f)]
    [InlineData(43f, 10f)]   // her rest A-pose
    [InlineData(54.5f, -82f)]   // the Look's left arm (Body 9 dump)
    [InlineData(53.6f, -52.5f)]   // the town idle's left arm
    [InlineData(60f, 0f)]
    [InlineData(60f, -60f)]
    public void ArmsDownAreExactlyZero(float a, float az) => Assert.All(W(a, az), v => Assert.Equal(0f, v));

    [Fact]
    public void SamplesAreWhole()
    {
        Assert.Equal(1f, W(117f, 0f)[0], 0.00001f); Assert.Equal(1f, W(140f, 0f)[1], 0.00001f);
        Assert.Equal(1f, W(117f, 90f)[2], 0.00001f); Assert.Equal(1f, W(140f, 90f)[3], 0.00001f);
        Assert.Equal(1f, W(175f, 30f)[4], 0.00001f); Assert.Equal(1f, W(180f, 0f)[4], 0.00001f);
    }

    [Fact]
    public void BetweenSamplesSumsToOne()
    {
        foreach (var a in new[] { 118f, 125f, 139f, 150f, 170f })
            foreach (var az in new[] { -40f, 0f, 30f, 60f, 90f, 130f })
            foreach (var rise in new[] { -5f, 0f, 12f, 45f })
            {
                var w = W(a, az, rise);
                float s = 0; foreach (var v in w) s += v;
                Assert.Equal(1f, s, 0.0001f);
            }
    }

    [Fact]
    public void LevelSampleWholeAtLevelAndHandedOn()   // (Body 9: the lowered key, A 75, near whole)
    {
        foreach (var az in new[] { -60f, 0f, 40f, 90f })
        {
            var w = W(80f, az);
            Assert.Equal(1f, w[8], 0.00001f);
            for (int k = 0; k < 8; k++) Assert.Equal(0f, w[k]);
            Assert.Equal(0f, W(117f, az)[8]);
            foreach (var a in new[] { 85f, 95f, 104f, 113.5f })
            {
                float s = 0; foreach (var v in W(a, az)) s += v;
                Assert.Equal(1f, s, 0.0001f);
            }
        }
        float w75 = W(75.1f, 40.3f)[8];   // the lowered reaver_show swing
        Assert.True(w75 > 0.8f && w75 < 0.9f);
        Assert.True(W(65f, 0f)[8] < W(70f, 0f)[8]);
    }

    [Fact]
    public void ShrugHandsOverToTwins()
    {
        // (the twins are read past HerShrug's own lift: ClavicleLift.Target)
        float t140 = ClavicleLift.Target(140f), t175 = ClavicleLift.Target(175f);
        Assert.Equal(1f, W(140f, 0f, t140 + 30f)[5], 0.00001f); Assert.Equal(0f, W(140f, 0f, t140 + 30f)[1], 0.00001f);
        Assert.Equal(1f, W(140f, 0f, t140)[1], 0.00001f);
        Assert.Equal(1f, W(175f, 0f, t175 + 60f)[7], 0.00001f);
        Assert.Equal(0.5f, W(175f, 0f, t175 + 15f)[4], 0.00001f);
        Assert.Equal(1f, W(117f, 0f, 30f)[0], 0.00001f);   // (A 117 has no twin)
        Assert.All(W(60f, 0f, 30f), v => Assert.Equal(0f, v));
    }

    [Fact]
    public void ElevationOfALine()
    {
        Assert.Equal(0f, ShoulderPsd.Elevation((1f, 0f, 0f), (0f, -1f, 0f)), 0.001f);
        Assert.Equal(30f, ShoulderPsd.Elevation((0.8660254f, 0.5f, 0f), (0f, -1f, 0f)), 0.001f);
    }

    [Fact]
    public void EasesInAboveLevel()
    {
        Assert.True(W(85f, 0f)[0] > 0f && W(85f, 0f)[0] < 0.2f);
        Assert.True(W(100f, 0f)[0] < W(105f, 0f)[0]);
    }

    [Fact]
    public void AnglesSideFrontBack()
    {
        var down = (0f, -1f, 0f); var lat = (1f, 0f, 0f); var fwd = (0f, 0f, 1f);
        var (a, az) = ShoulderPsd.Angles((1f, 0f, 0f), down, lat, fwd);
        Assert.Equal(90f, a, 0.001f); Assert.Equal(0f, az, 0.001f);
        (a, az) = ShoulderPsd.Angles((0f, 1f, 1f), down, lat, fwd);
        Assert.Equal(135f, a, 0.001f); Assert.Equal(90f, az, 0.001f);
        (a, az) = ShoulderPsd.Angles((0f, 0f, -1f), down, lat, fwd);
        Assert.Equal(-90f, az, 0.001f);
    }
}
