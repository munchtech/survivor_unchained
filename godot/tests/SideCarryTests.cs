using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The side carry (Play/SideCarry.cs, warden-move): its weight from her facing to the camera, the screen-aware
/// tilt (solved for an on-screen angle at the den camera, clamped in 3D), the swing's spring and its limits, the rate cap.</summary>
public class SideCarryTests
{
    const float Dt = 1f / 30f;
    static float Rad(float deg) => deg * MathF.PI / 180f;
    static void Near(float want, float got, float tol) => Assert.InRange(got, want - tol, want + tol);

    // The den camera, orthographic: pitch 62, yaw 0 (its back is world +Z and up); screen x = world X, screen y (down) below.
    static readonly Vector3 CamBack = new(0f, MathF.Sin(Rad(62f)), MathF.Cos(Rad(62f)));
    static readonly Vector3 Jx = new(100f, 0f, 0f);
    static readonly Vector3 Jy = new(0f, -100f * MathF.Cos(Rad(62f)), 100f * MathF.Sin(Rad(62f)));

    // Her axes at a yaw (deg): facing (sin, 0, cos), left (cos, 0, -sin); the clip's blade hanging tipped back 7, out 15.
    static (Vector3 ahead, Vector3 left, Vector3 blade) Her(float face)
    {
        float f = Rad(face);
        var ahead = new Vector3(MathF.Sin(f), 0f, MathF.Cos(f));
        var left = new Vector3(MathF.Cos(f), 0f, -MathF.Sin(f));
        var b = SideCarry.Rot(left, 7f, -Vector3.UnitY);
        b = SideCarry.Rot(ahead, -15f, b);
        return (ahead, left, b);
    }

    static SideCarry.Frame At(float face, float moving = 1f, float strafe = 0f)
    {
        var (a, l, b) = Her(face);
        return new SideCarry.Frame(b, l, a, Jx, Jy, CamBack, moving, strafe);
    }

    static float Shown(SideCarry c, float face)
    {
        var (a, l, b) = Her(face);
        var t = SideCarry.Turned(b, l, c.Tilt, a, c.Inward);
        return SideCarry.ScreenAngle(t, Jx, Jy, c.Sigma);
    }

    [Theory]
    [InlineData(90f, 1f)]      // side_x: the sword side squarely to the camera
    [InlineData(45f, 1f)]      // toward_x: the diagonals take it whole
    [InlineData(135f, 1f)]     // away_x
    [InlineData(-90f, 0f)]     // side_mx: the sword on the far side
    [InlineData(0f, 0f)]       // toward the camera
    [InlineData(180f, 0f)]     // away
    [InlineData(-540f, 0f)]
    [InlineData(8f, 0f)]       // nearly toward: still none
    public void WeightIsFullFromTheDiagonalsAndNoneTowardAwayOrFar(float face, float want) =>
        Assert.Equal((double)want, (double)new SideCarry().Target(SideCarry.Side(Rad(face), 0f, 1f)), 3);

    [Fact]
    public void TheLeftHandMirrorsAndTheCameraYawCounts()
    {
        Assert.Equal(1.0, (double)SideCarry.Side(Rad(-90f), 0f, 1f, right: false), 3);
        Assert.Equal(1.0, (double)SideCarry.Side(0f, -1f, 0f), 3);   // camera turned 90: her right (-X) faces it at yaw 0
    }

    [Fact]
    public void NoWeightLeavesTheGripExactlyTheClips()
    {
        foreach (float face in new[] { 0f, 180f, -90f, -135f })
        {
            var c = new SideCarry();
            for (int i = 0; i < 60; i++) c.Step(Dt, true, 15f * MathF.Sin(i * 0.4f), At(face));
            Assert.Equal(0f, c.Weight);
            Assert.Equal(0f, c.Tilt);
            Assert.Equal(0f, c.Inward);
        }
        var off = new SideCarry();
        for (int i = 0; i < 30; i++) off.Step(Dt, false, 0f, At(90f));
        Assert.Equal(0f, off.Tilt);
    }

    [Theory]
    [InlineData(90f)]
    [InlineData(45f)]
    [InlineData(120f)]
    public void TheSolvedTiltShowsTheBladeAtTheWantedAngle(float face)
    {
        var (a, l, b) = Her(face);
        foreach (float want in new[] { 25f, 35f, 45f })
        {
            float t = SideCarry.Solve(b, l, a, 3f, Jx, Jy, -1f, want, -60f, 80f, 20f);
            Near(want, SideCarry.ScreenAngle(SideCarry.Turned(b, l, t, a, 3f), Jx, Jy, -1f), 0.1f);
        }
    }

    [Fact]
    public void AwayDiagonalsTipBackMoreAndTowardLessForOneScreenAngle()
    {
        float T(float face) { var (a, l, b) = Her(face); return SideCarry.Solve(b, l, a, 3f, Jx, Jy, -1f, 30f, -60f, 80f, 20f); }
        Assert.True(T(135f) > T(90f) + 10f, $"away {T(135f)} side {T(90f)}");
        Assert.True(T(45f) < T(90f) - 5f, $"toward {T(45f)} side {T(90f)}");
    }

    [Fact]
    public void BeyondTheClampItStopsAtTheEndNearerOnScreen()
    {
        var (a, l, b) = Her(135f);   // away_x: 80 on screen is out of reach within 0..50 of tip-back
        float t = SideCarry.Solve(b, l, a, 3f, Jx, Jy, -1f, 80f, 0f, 43f, 20f);
        Near(43f, t, 0.001f);
    }

    [Fact]
    public void AtARunTheBladeSitsAtItsAngleAndStandingLess()
    {
        var c = new SideCarry();
        for (int i = 0; i < 90; i++) c.Step(Dt, true, 0f, At(90f));
        Near(1f, c.Weight, 0.001f);
        Near(c.RunAngle, Shown(c, 90f), 0.5f);
        for (int i = 0; i < 90; i++) c.Step(Dt, true, 0f, At(90f, moving: 0f));
        Near(c.StandAngle, Shown(c, 90f), 0.5f);
        float run = c.Tilt;
        for (int i = 0; i < 90; i++) c.Step(Dt, true, 0f, At(90f, moving: 1f, strafe: 1f));
        Near(c.RunAngle - c.StrafeCut, Shown(c, 90f), 0.5f);
        Assert.True(run < c.Tilt);
    }

    [Fact]
    public void TheClampKeepsTheBladesOwnTipBackAndRoomUnderIt()
    {
        var c = new SideCarry();
        for (int i = 0; i < 120; i++) c.Step(Dt, true, 0f, At(135f));
        var (a, l, b) = Her(135f);
        float back = SideCarry.BackOf(SideCarry.Rot(l, c.Tilt, b), a);
        Assert.InRange(back, c.BackMin - 0.01f, c.BackMax + 0.01f);
        Assert.True(Shown(c, 135f) <= c.RunAngle - 0.5f, "away_x is held under the clamp's angle");
        Assert.True(Shown(c, 135f) > 15f, $"away_x {Shown(c, 135f)}: off the stick");
    }

    [Fact]
    public void AForwardPullSwingsTheTipBackWithinItsLimits()
    {
        var c = new SideCarry();
        for (int i = 0; i < 60; i++) c.Step(Dt, true, 100f, At(90f));
        Near(MathF.Min(c.Loose, c.Gain * c.MaxAccel), c.Spring, 0.001f);
        for (int i = 0; i < 60; i++) c.Step(Dt, true, -100f, At(90f));
        Near(-c.LooseFwd, c.Spring, 0.001f);
    }

    [Fact]
    public void TheSwingLagsTheFistsPull()
    {
        // The fist swung at the run's stride (1.875 Hz): the tip's swing peaks after the forward pull's, by a few frames.
        var c = new SideCarry();
        float w = 2f * MathF.PI * 1.875f, bestT = 0f, bestS = float.MinValue;
        for (int i = 0; i < 120; i++)
        {
            float t = i * Dt;
            c.Step(Dt, true, 20f * MathF.Cos(w * t), At(90f));
            if (t > 2f && c.Spring > bestS) { bestS = c.Spring; bestT = t; }
        }
        float lag = ((bestT * 1.875f) % 1f) * 16f;   // frames after the pull's peak (a period is 16 frames)
        Assert.InRange(lag, 1.5f, 4.5f);
        Assert.InRange(bestS, 6f, c.Loose);
    }

    [Fact]
    public void TheTiltNeverMovesFasterThanItsCap()
    {
        var c = new SideCarry();
        float prev = 0f;
        for (int i = 0; i < 90; i++)
        {
            c.Step(Dt, true, 0f, At(i < 30 ? 0f : i < 60 ? 90f : 0f));
            Assert.True(MathF.Abs(c.Tilt - prev) <= c.MaxRate * Dt + 1e-3f);
            prev = c.Tilt;
        }
    }

    [Fact]
    public void ResetAndBadStepsLeaveItAtRest()
    {
        var c = new SideCarry();
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 10f, At(90f));
        c.Reset();
        Assert.Equal(0f, c.Tilt);
        Assert.Equal(0f, c.Weight);
        c.Step(0f, true, 10f, At(90f));
        c.Step(float.NaN, true, 10f, At(90f));
        Assert.Equal(0f, c.Tilt);
        c.Step(Dt, true, float.NaN, At(90f));
        Assert.True(float.IsFinite(c.Tilt) && float.IsFinite(c.Spring));
    }
    // (judge r4, solver 17) A frame at `face` with the clip's blade swayed by `back` (tip back) and `outward` (tip out).
    static SideCarry.Frame Swayed(float face, float back, float outward, float moving = 0f)
    {
        var (a, l, b) = Her(face);
        b = SideCarry.Rot(a, -outward, SideCarry.Rot(l, back, b));
        return new SideCarry.Frame(b, l, a, Jx, Jy, CamBack, moving, 0f);
    }
    static float ShownOf(SideCarry c, in SideCarry.Frame f)
        => SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), f.Jx, f.Jy, c.Sigma);

    [Theory]
    [InlineData(90f)]      // side_x
    [InlineData(135f)]     // away_x: the stand's angle needs the extra turn in
    public void StandHoldsStillWhileTheIdleSways(float face)
    {
        var c = new SideCarry();
        float lo = float.MaxValue, hi = float.MinValue;
        for (int i = 0; i < 60; i++)
        {
            var f = Swayed(face, 10f * MathF.Sin(i * 0.4f), 8f + 8f * MathF.Sin(i * 0.25f));
            c.Step(Dt, true, 0f, f);
            if (i < 20) continue;
            float a = ShownOf(c, f);
            lo = MathF.Min(lo, a); hi = MathF.Max(hi, a);
        }
        Assert.True(hi - lo <= 2f, $"stand wandered {lo:F1}..{hi:F1}");
        Assert.InRange(lo, c.Floor - 0.5f, c.StandAngle + 1f);
    }

    [Fact]
    public void WeightFadesNoFasterThanFadeOut()
    {
        var c = new SideCarry();
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 0f, At(90f, 0f));
        Near(1f, c.Weight, 1e-3f);
        c.Step(Dt, true, 0f, At(-90f, 0f));
        Assert.True(c.Weight >= 1f - Dt / c.FadeOut - 1e-4f, $"weight fell to {c.Weight:F3}");
    }

    [Fact]
    public void NeverPastTheEdgeWhereTheClipIsInside()
    {
        var c = new SideCarry();
        for (int i = 0; i < 240; i++)
        {
            float face = 90f + 60f * MathF.Sin(i * 0.07f);
            var f = Swayed(face, 15f * MathF.Sin(i * 0.3f), 10f * MathF.Sin(i * 0.17f), 0.5f + 0.5f * MathF.Sin(i * 0.05f));
            c.Step(Dt, true, 20f * MathF.Sin(i * 0.7f), f);
            float a0 = SideCarry.ScreenAngle(f.Blade, Jx, Jy, 1f);
            float a = SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), Jx, Jy, 1f);
            if (MathF.Abs(a0) <= c.Edge) Assert.True(MathF.Abs(a) <= c.Edge + 0.5f, $"frame {i}: {a:F1} past the edge");
        }
    }
}
