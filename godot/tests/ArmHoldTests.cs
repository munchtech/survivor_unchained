using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class ArmHoldTests
{
    [Fact]
    public void HysteresisHoldsBetweenDownAndUp()
    {
        var h = new ArmHold();
        h.Reset(0f);
        foreach (var w in new[] { 0.1f, 0.4f, 0.5f, 0.6f }) { Assert.False(h.Step(w, 1 / 60f)); Assert.False(h.Run); }
        Assert.True(h.Step(0.61f, 1 / 60f));
        Assert.True(h.Run);
        foreach (var w in new[] { 0.59f, 0.5f, 0.41f, 0.4f }) { Assert.False(h.Step(w, 1 / 60f)); Assert.True(h.Run); }
        Assert.True(h.Step(0.39f, 1 / 60f));
        Assert.False(h.Run);
    }

    [Fact]
    public void HeldStickNeverFlickers()
    {
        // A held stick that wobbles about the middle (the run weight +-0.08 about 0.5): no switch at all.
        var h = new ArmHold();
        h.Reset(0.5f);
        bool start = h.Run;
        for (int i = 0; i < 600; i++) Assert.False(h.Step(0.5f + 0.08f * (float)System.Math.Sin(i * 0.3), 1 / 60f));
        Assert.Equal(start, h.Run);
    }

    [Fact]
    public void CrossfadeIsTimedNotBySpeedAndEased()
    {
        var h = new ArmHold();
        h.Reset(0f);
        Assert.Equal(0f, h.Carry);
        Assert.True(h.Step(1f, 1 / 60f));
        Assert.Equal(1f, h.Carry);
        float prev = 1f;
        int n = 0;
        // The run weight stays put: the fade still runs, by time.
        while (h.Carry > 0f) { h.Step(1f, 1 / 60f); Assert.True(h.Carry < prev); prev = h.Carry; n++; }
        Assert.InRange(n * (1 / 60f), ArmHold.Fade - 0.02f, ArmHold.Fade + 0.02f);
        // Eased: slow at both ends, fast in the middle.
        Assert.Equal(1f, 1f - ArmHold.Ease(0.05f), 0.01f);
        Assert.Equal(0.5f, ArmHold.Ease(0.5f), 1e-4f);
        Assert.True(ArmHold.Ease(0.55f) - ArmHold.Ease(0.45f) > 0.1f * 1.4f);
    }

    [Fact]
    public void BothDirectionsAndAReversalMidFade()
    {
        var h = new ArmHold();
        h.Reset(1f);
        Assert.True(h.Run);
        Assert.True(h.Step(0f, 1 / 60f));     // stopping: back to the walk's hold
        Assert.False(h.Run);
        h.Step(0f, 0.05f);
        Assert.True(h.Carry < 1f && h.Carry > 0f);
        Assert.True(h.Step(1f, 1 / 60f));     // off again mid-fade: a fresh fade from where the arms are
        Assert.True(h.Run);
        Assert.Equal(1f, h.Carry);
    }

    [Fact]
    public void ArmsPlaceIsContinuousThroughAReversal()
    {
        var h = new ArmHold();
        h.Reset(0f);
        Assert.Equal(0f, h.E);
        h.Step(1f, 1 / 60f);
        float prev = h.E;
        for (int i = 0; i < 5; i++) { h.Step(1f, 1 / 60f); Assert.True(h.E >= prev); prev = h.E; }
        Assert.True(h.Fading && prev > 0.05f && prev < 0.95f);
        h.Step(0f, 1 / 60f);                  // back mid-fade: no jump, then home to the walk's hold
        Assert.Equal(prev, h.E, 1e-5f);
        for (int i = 0; i < 30; i++) h.Step(0f, 1 / 60f);
        Assert.False(h.Fading);
        Assert.Equal(0f, h.E);
    }

    [Fact]
    public void SprintKeepsTheRunHold()
    {
        // Into the sprint the run weight stays 1 (Stride.Weights against the sprint's speed): no switch.
        var h = new ArmHold();
        h.Reset(0f);
        int switches = 0;
        for (float s = 0; s <= 7.4f; s += 0.05f)
        {
            var (_, w) = Stride.Weights(s, 1.23f, s > 5.1f ? 5.1f + (s - 5.1f) : 5.1f, true);
            if (h.Step(w, 1 / 60f)) switches++;
        }
        Assert.Equal(1, switches);
        Assert.True(h.Run);
    }

    [Fact]
    public void ArmBonesAreTheArmsOnly()
    {
        foreach (var n in new[] { "clavicle_l", "upperarm_r", "lowerarm_twist_01_l", "hand_r", "index_02_r", "thumb_04_leaf_l", "delt_r", "trap_l", "scap_r", "pec_l", "lat_r", "upperarm_share_l", "lowerarm_point_r" })
            Assert.True(ArmHold.IsArmBone(n), n);
        foreach (var n in new[] { "pelvis", "spine_03", "neck_01", "Head", "thigh_l", "calf_r", "breast_l", "glute_r", "root", "panel_front", "hand" })
            Assert.False(ArmHold.IsArmBone(n), n);
    }
}
