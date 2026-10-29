using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A sheathed piece hung from her belt (Play/SheathHang.cs): a held pose is followed in full, a stride's roll is
/// cut to a small, lagging sway, and the first pose is taken as it is.</summary>
public class SheathHangTests
{
    static Quaternion Roll(float deg) => Quaternion.CreateFromAxisAngle(Vector3.UnitZ, deg * MathF.PI / 180f);

    static float Deg(Quaternion a, Quaternion b)
    {
        float d = MathF.Min(1f, MathF.Abs(Quaternion.Dot(Quaternion.Normalize(a), Quaternion.Normalize(b))));
        return 2f * MathF.Acos(d) * 180f / MathF.PI;
    }

    [Fact]
    public void FirstPoseIsTakenAsItIs()
    {
        var h = new SheathHang();
        Assert.True(Deg(h.Step(Roll(12), 1 / 60f), Roll(12)) < 0.01f);
    }

    [Fact]
    public void AHeldPoseIsFollowedInFull()
    {
        var h = new SheathHang();
        h.Step(Quaternion.Identity, 1 / 60f);
        Quaternion q = default;
        for (int i = 0; i < 60 * 12; i++) q = h.Step(Roll(15), 1 / 60f);
        Assert.True(Deg(q, Roll(15)) < 0.2f);
    }

    [Fact]
    public void AStridesRollBecomesASmallLaggingSway()
    {
        // her walk: the pelvis rolls 13 degrees each way once a stride (1.33 s)
        var h = new SheathHang();
        const float dt = 1 / 60f, period = 1.33f;
        float lo = 99, hi = -99, peakT = 0, peakIn = 0;
        for (int i = 0; i < 60 * 20; i++)
        {
            float t = i * dt, roll = 13f * MathF.Sin(2 * MathF.PI * t / period);
            var q = h.Step(Roll(roll), dt);
            if (t < 15f) continue;
            float a = 2f * MathF.Asin(Math.Clamp(q.Z, -1f, 1f)) * 180f / MathF.PI;
            if (a > hi) { hi = a; peakT = t; }
            lo = MathF.Min(lo, a);
            if (roll > 12.99f) peakIn = t;
        }
        Assert.InRange(hi - lo, 2f, 8f);           // 26 peak to peak in, a few degrees out
        Assert.InRange(MathF.Abs(hi + lo), 0f, 0.5f); // centred on the mean
        Assert.True(peakT > 0);
        // it trails the hips (a lag, not a lead): the piece's peak comes after the pelvis's within the stride
        float lag = ((peakT - peakIn) % period + period) % period;
        Assert.InRange(lag, 0.02f, period / 2);
    }

    [Fact]
    public void ResetStartsAgainFromThePose()
    {
        var h = new SheathHang();
        h.Step(Quaternion.Identity, 1 / 60f);
        h.Step(Roll(20), 1 / 60f);
        h.Reset();
        Assert.True(Deg(h.Step(Roll(20), 1 / 60f), Roll(20)) < 0.01f);
    }

    [Theory]
    [InlineData("run_warden_town", true)]
    [InlineData("sprint_warden_town", true)]
    [InlineData("her/run_warden_town", true)]
    [InlineData("walk_warden_town", false)]
    [InlineData("idle_warden_town", false)]
    [InlineData("run_warden", false)]
    [InlineData("run_reaver_town", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void TheHiltIsHeldOnlyInTheListedClips(string? clip, bool held) => Assert.Equal(held, SheathHang.HoldsHilt(clip));

    [Fact]
    public void InAHiltClipThePieceRidesRigidlyAndTheHangEasesBackWithoutAPop()
    {
        // walking (hung), then into the run (her hand on the hilt), then back to the walk
        var h = new SheathHang();
        const float dt = 1 / 60f, period = 1.33f;
        Quaternion last = default;
        float worst = 0;
        for (int i = 0; i < 60 * 12; i++)
        {
            float t = i * dt;
            bool run = t >= 4f && t < 8f;
            var d = Roll(13f * MathF.Sin(2 * MathF.PI * t / period));
            var q = h.Step(d, dt, run);
            if (i > 0) worst = MathF.Max(worst, Deg(q, last));
            last = q;
            if (t > 4.5f && t < 8f) Assert.True(Deg(q, d) < 0.01f);   // rigid: the pelvis's own turn, past the blend
            if (t > 2f && t < 4f) Assert.Equal(1f, h.Weight);
            if (t >= 4f && t < 4f + SheathHang.Blend - 2 * dt) Assert.InRange(h.Weight, 0.001f, 0.999f); // eased, not cut
        }
        // the pelvis turns at most 1.0 degree a frame here and a hard cut would jump the piece about 10; eased, a frame
        // moves it at most the pelvis's step plus the blend's share of the gap (1.6)
        Assert.True(worst < 2.5f, $"worst frame step {worst:0.00} deg");
        Assert.Equal(1f, h.Weight);
    }

    [Fact]
    public void AFirstPoseInAHiltClipStartsRigid()
    {
        var h = new SheathHang();
        Assert.True(Deg(h.Step(Roll(12), 1 / 60f, true), Roll(12)) < 0.01f);
        Assert.Equal(0f, h.Weight);
    }
}
