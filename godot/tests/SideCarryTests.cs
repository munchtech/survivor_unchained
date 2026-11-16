using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The side carry (Play/SideCarry.cs, warden-move): its weight from her facing to the camera, the weight's ease,
/// the spring's loosening and its limits, and the rate cap on the tilt it adds.</summary>
public class SideCarryTests
{
    const float Dt = 1f / 30f;
    static float Rad(float deg) => deg * MathF.PI / 180f;

    // The den camera: its back (basis Z) is world +Z, so side = sin(face) for her right hand.
    [Theory]
    [InlineData(-270f, 1f)]     // side_x: the sword side squarely to the camera
    [InlineData(90f, 1f)]
    [InlineData(-90f, 0f)]      // side_mx: the sword on the far side
    [InlineData(0f, 0f)]        // toward the camera
    [InlineData(180f, 0f)]      // away
    [InlineData(-540f, 0f)]
    [InlineData(45f, 0.5f)]     // toward_x: sin^2 45
    [InlineData(135f, 0.5f)]    // away_x
    public void WeightIsTheSwordSideToTheCameraSquared(float face, float want) =>
        Assert.Equal((double)want, (double)SideCarry.Target(SideCarry.Side(Rad(face), 0f, 1f)), 3);

    [Fact]
    public void TheLeftHandMirrorsAndTheCameraYawCounts()
    {
        Assert.Equal(1.0, (double)SideCarry.Target(SideCarry.Side(Rad(-90f), 0f, 1f, right: false)), 3);
        Assert.Equal(0.0, (double)SideCarry.Target(SideCarry.Side(Rad(90f), 0f, 1f, right: false)), 3);
        // a camera turned to look along +X (its back -X... here +X): her right side (-X at yaw 0) faces away from it
        Assert.Equal(0.0, (double)SideCarry.Target(SideCarry.Side(0f, 1f, 0f)), 3);
        Assert.Equal(1.0, (double)SideCarry.Target(SideCarry.Side(0f, -2f, 0f)), 3);   // the camera's back need not be unit
        Assert.Equal(0f, SideCarry.Side(0f, 0f, 0f));                         // a camera looking straight down: no side
    }

    [Fact]
    public void NoWeightLeavesTheGripExactlyTheClips()
    {
        var c = new SideCarry();
        for (int i = 0; i < 90; i++) c.Step(Dt, 0f, 18f * MathF.Sin(i * 0.4f));
        Assert.Equal(0f, c.Weight);
        Assert.Equal(0f, c.Tilt);
        Assert.Equal(0f, c.Inward);
    }

    [Fact]
    public void WeightEasesOverItsTimeConstant()
    {
        var c = new SideCarry { Ease = 0.1f };
        c.Step(0.1f, 1f, 0f);
        Assert.Equal(1.0 - Math.Exp(-1.0), (double)c.Weight, 3);   // one time constant: 63 %
        for (int i = 0; i < 30; i++) c.Step(Dt, 1f, 0f);
        Assert.True(c.Weight > 0.999f);
        for (int i = 0; i < 60; i++) c.Step(Dt, 0f, 0f);  // and back out: settles to exactly none
        Assert.Equal(0f, c.Weight);
        Assert.Equal(0f, c.Tilt);
    }

    [Fact]
    public void AtFullWeightTheTipSitsBackByRestAndSplayTrims()
    {
        var c = new SideCarry { Rest = 27f, Splay = 3f };
        for (int i = 0; i < 120; i++) c.Step(Dt, 1f, 0f);
        Assert.Equal(27.0, (double)c.Tilt, 2);
        Assert.Equal(3.0, (double)c.Inward, 2);
    }

    [Fact]
    public void AForwardPullTipsTheBladeBackWithinItsLimits()
    {
        var c = new SideCarry { Gain = 0.65f, Loose = 15f, LooseFwd = 6f, MaxAccel = 24f };
        for (int i = 0; i < 60; i++) c.Step(Dt, 1f, 10f);      // a steady pull: Gain x accel
        Assert.Equal(6.5, (double)c.Spring, 1);
        for (int i = 0; i < 60; i++) c.Step(Dt, 1f, 500f);     // cut to MaxAccel, then to Loose
        Assert.True(c.Spring <= 15f + 1e-4f && c.Spring > 14f);
        for (int i = 0; i < 60; i++) c.Step(Dt, 1f, -500f);    // a stop: tip forward no further than LooseFwd
        Assert.True(c.Spring >= -6f - 1e-4f && c.Spring < -5f);
        c.Step(Dt, 1f, float.NaN);                             // a bad reading is no pull
        Assert.True(float.IsFinite(c.Spring) && float.IsFinite(c.Tilt));
    }

    [Fact]
    public void TheSwingLagsTheFistsPull()
    {
        // the fist swung fore and aft at a run's stride (1.875 Hz): the loosening peaks after the pull does
        var c = new SideCarry { Hz = 2f, Damping = 0.8f };
        float w = 2f * MathF.PI * 1.875f;
        int pullPeak = -1, springPeak = -1; float best = float.MinValue, bestS = float.MinValue;
        for (int i = 0; i < 240; i++)
        {
            float t = i * Dt, a = 19f * MathF.Cos(w * t);
            c.Step(Dt, 1f, a);
            if (i < 180) continue;                               // steady state: the last 2 of 7.5 cycles
            if (a > best) { best = a; pullPeak = i; }
            if (c.Spring > bestS) { bestS = c.Spring; springPeak = i; }
        }
        int lag = ((springPeak - pullPeak) % 16 + 16) % 16;     // one stride is 16 frames
        Assert.InRange(lag, 2, 6);
    }

    [Fact]
    public void TheTiltNeverMovesFasterThanItsCap()
    {
        var c = new SideCarry { MaxRate = 150f, Ease = 0.02f };
        float last = 0f;
        for (int i = 0; i < 40; i++)
        {
            c.Step(Dt, i % 10 < 5 ? 1f : 0f, i % 3 == 0 ? 60f : -60f);   // a turn flicked through the side, pulled about
            Assert.True(MathF.Abs(c.Tilt - last) <= 150f * Dt + 1e-4f);
            last = c.Tilt;
        }
    }

    [Fact]
    public void ResetAndBadStepsLeaveItAtRest()
    {
        var c = new SideCarry();
        for (int i = 0; i < 30; i++) c.Step(Dt, 1f, 5f);
        c.Reset();
        Assert.Equal(0f, c.Weight); Assert.Equal(0f, c.Tilt); Assert.Equal(0f, c.Spring);
        c.Step(0f, 1f, 5f); c.Step(-1f, 1f, 5f); c.Step(float.NaN, 1f, 5f);
        Assert.Equal(0f, c.Weight); Assert.Equal(0f, c.Tilt);
    }
}
