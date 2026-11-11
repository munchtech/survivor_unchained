using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class PelvisCounterTests
{
    static Quaternion Q(float x, float y, float z, float deg) => Quaternion.CreateFromAxisAngle(Vector3.Normalize(new Vector3(x, y, z)), deg * MathF.PI / 180f);
    static bool Same(Quaternion a, Quaternion b) => MathF.Abs(Quaternion.Dot(a, b)) > 1 - 1e-5f;

    static readonly Quaternion M = Q(0.3f, 1, 0.2f, 12), Ph = Q(1, 0.4f, -0.5f, 8.6f), L = Q(0.1f, 0.2f, 1, 33);

    [Fact]
    public void FullCounterRidesTheMean()
    {
        var local = PelvisCounter.Apply(M, Ph, L, 1, 1);
        Assert.True(Same(Ph * local, M * L));
    }

    [Fact]
    public void ZeroWeightIsIdentity()
    {
        Assert.True(Same(PelvisCounter.Apply(M, Ph, L, 1, 0), L));
        Assert.True(Same(PelvisCounter.Correction(M, Ph, 0.5f, 0), Quaternion.Identity));
    }

    [Fact]
    public void ZeroKeepsOnlyTheYaw()
    {
        var e = PelvisCounter.Correction(M, Ph, 0, 1);
        // a pure turn about +Y, and it is the yaw part of M * Ph^-1
        Assert.True(MathF.Abs(e.X) < 1e-5f && MathF.Abs(e.Z) < 1e-5f);
        var full = M * Quaternion.Inverse(Ph);
        Assert.True(e.Y != 0);
        var withSwing = PelvisCounter.Correction(M, Ph, 1, 1);
        Assert.True(Same(withSwing, full));
        Assert.False(Same(e, full));
    }

    [Fact]
    public void PureYawPassesAtAnyK()
    {
        var ph = Q(0.2f, 1, 0.1f, 20);
        var m = Q(0, 1, 0, 7) * ph;   // E = a pure yaw of 7 degrees
        foreach (var k in new[] { 0f, 0.5f, 1f })
            Assert.True(Same(PelvisCounter.Correction(m, ph, k, 1), Q(0, 1, 0, 7)));
    }

    [Fact]
    public void HalfWeightIsHalfTheTurn()
    {
        var full = PelvisCounter.Correction(M, Ph, 1, 1);
        var half = PelvisCounter.Correction(M, Ph, 1, 0.5f);
        Assert.True(Same(half * half, full));
    }

    [Fact]
    public void WeightFollowsTheFades()
    {
        Assert.Equal((double)1f, (double)PelvisCounter.Weight(1, 1, 0.05, 0.18, -1, 0.18), 3);
        Assert.Equal((double)0.5f, (double)PelvisCounter.Weight(0.025, 1, 0.05, 0.18, -1, 0.18), 3);
        Assert.Equal((double)0.5f, (double)PelvisCounter.Weight(1, 0.09, 0.05, 0.18, -1, 0.18), 3);
        Assert.Equal((double)0.5f, (double)PelvisCounter.Weight(1, 1, 0.05, 0.18, 0.09, 0.18), 3);
        Assert.Equal((double)0f, (double)PelvisCounter.Weight(1, 1, 0.05, 0.18, 0.5, 0.18), 3);
    }

    [Fact]
    public void MeanMetaReadsFourNumbers()
    {
        Assert.Null(PelvisCounter.Mean(null));
        Assert.Null(PelvisCounter.Mean(new double[] { 0, 0, 0 }));
        Assert.True(Same(PelvisCounter.Mean(new double[] { 0, 0, 0, 2 })!.Value, Quaternion.Identity));
    }
}
