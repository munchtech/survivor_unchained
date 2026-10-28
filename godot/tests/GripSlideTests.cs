using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The grip slide and tilt (Play/GripSlide.cs): which clip's value counts, the ease between them, and where the piece sits.</summary>
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
        Assert.Equal(0.08f, GripSlide.Target(false, 0, false, 0, 0f, 0.08f, 0f), 1e-5f);
        Assert.Equal(0.04f, GripSlide.Target(false, 0, false, 0, 0.5f, 0.08f, 0f), 1e-5f);
        Assert.Equal(0.08f, GripSlide.Target(false, 0, false, 0, -3f, 0.08f, 0f), 1e-5f);
        Assert.Equal(0f, GripSlide.Target(false, 0, false, 0, 7f, 0.08f, 0f), 1e-5f);
    }

    [Fact]
    public void WalkBlendUsesWalkValueBetweenIdleAndRun()
    {
        Assert.Equal(-0.13f, GripSlide.Target(false, 0, false, 0, 0f, 0f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(0f, GripSlide.Target(false, 0, false, 0, 1f, 0f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(0.05f, GripSlide.Target(false, 0, false, 0, 1f, 1f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(0.05f, GripSlide.Target(false, 0, false, 0, 0f, 1f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(-0.065f, GripSlide.Target(false, 0, false, 0, 0.5f, 0f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(0.025f, GripSlide.Target(false, 0, false, 0, 1f, 0.5f, -0.13f, 0f, 0.05f), 1e-5f);
        Assert.Equal(0.3f, GripSlide.Target(true, 0.3f, true, 0.2f, 1f, 0f, -0.13f, 0f, 0.05f));
        Assert.Equal(0.2f, GripSlide.Target(false, 0.3f, true, 0.2f, 1f, 0f, -0.13f, 0f, 0.05f));
    }

    [Fact]
    public void EaseKeepsAtZeroDtAndReachesTargetWithLargeDt()
    {
        Assert.Equal(0.02f, GripSlide.Ease(0.02f, 0.09f, 0f));
        Assert.Equal(0.09f, GripSlide.Ease(0.02f, 0.09f, 100f), 1e-4f);
    }

    // Apply (animation 48): the seated piece turned about the palm's normal through the pocket, then slid along its turned +Y.
    static void Near(Vector3 want, Vector3 got) => Assert.True(Vector3.Distance(want, got) < 1e-5f, $"{want} != {got}");

    [Fact]
    public void ApplyWithNoTiltOrSlideLeavesTheSeat()
    {
        var (turn, at) = GripSlide.Apply(new Vector3(0.1f, 0.2f, 0.3f), Vector3.UnitY, new Vector3(-0.03f, 0.08f, -0.01f), Vector3.UnitX, 0f, 0f);
        Assert.Equal(Quaternion.Identity, turn);
        Near(new Vector3(0.1f, 0.2f, 0.3f), at);
    }

    [Fact]
    public void ApplySlideAloneRunsAlongTheSeatsUp()
    {
        var up = Vector3.Normalize(new Vector3(-0.21f, 0.41f, 0.89f));
        var (_, at) = GripSlide.Apply(new Vector3(0.1f, 0.2f, 0.3f), up, Vector3.Zero, Vector3.UnitX, 0f, 0.05f);
        Near(new Vector3(0.1f, 0.2f, 0.3f) + up * 0.05f, at);
    }

    [Fact]
    public void ApplyTiltKeepsThePivotAndTurnsAboutTheAxis()
    {
        var pivot = new Vector3(-0.0326f, 0.0841f, -0.0104f);
        // A point on the pivot stays; one a metre up the seat's +Y turns 90 deg about +X onto +Z.
        Near(pivot, GripSlide.Apply(pivot, Vector3.UnitY, pivot, Vector3.UnitX, 90f, 0f).At);
        var (turn, at) = GripSlide.Apply(pivot + Vector3.UnitY, Vector3.UnitY, pivot, Vector3.UnitX, 90f, 0f);
        Near(pivot + Vector3.UnitZ, at);
        Near(Vector3.UnitZ, Vector3.Transform(Vector3.UnitY, turn));
    }

    [Fact]
    public void ApplySlidesAlongTheTurnedShaft()
    {
        var pivot = new Vector3(0.01f, 0.02f, 0.03f);
        var (_, at) = GripSlide.Apply(pivot, Vector3.UnitY, pivot, Vector3.UnitX, 90f, 0.1f);
        Near(pivot + Vector3.UnitZ * 0.1f, at);
        // An unnormalised axis is the same axis.
        Near(at, GripSlide.Apply(pivot, Vector3.UnitY, pivot, Vector3.UnitX * 3f, 90f, 0.1f).At);
    }

    [Fact]
    public void ApplyTiltTwentyTurnsTheStaffAwayFromTheFingers()
    {
        // The staff's fitted line (WeaponSockets.FistDirR) leaves the fist 65.5 deg off the hand's +Y (the fingers', the
        // forearm's line); +20 about +X (keyed.py grip_tilt) takes it to 85 deg, toward a square grip.
        var dir = WeaponSockets.FistDirR;
        var (turn, _) = GripSlide.Apply(WeaponSockets.FistAtR, dir, WeaponSockets.FistAtR, Vector3.UnitX, 20f, 0f);
        var d = Vector3.Transform(dir, turn);
        float deg(Vector3 v) => MathF.Acos(Math.Clamp(Vector3.Dot(Vector3.Normalize(v), Vector3.UnitY), -1f, 1f)) * 180f / MathF.PI;
        Assert.InRange(deg(dir), 65.4f, 65.7f);
        Assert.InRange(deg(d), 84.9f, 85.2f);
    }

    [Fact]
    public void EaseMovesMonotonicallyTowardTarget()
    {
        float a = GripSlide.Ease(0f, 0.09f, 0.016f), b = GripSlide.Ease(a, 0.09f, 0.016f);
        Assert.InRange(a, 0.0001f, 0.0899f);
        Assert.True(b > a && b < 0.09f);
    }

    // The left tilt (animation 58): the right's pocket mirrored, the palm's normal mirrored and reversed, the seat eased over.
    static Vector3 Mirror(Vector3 v) => new(-v.X, v.Y, v.Z);   // her rest hands are within 0.4 deg of a plain X flip

    [Fact]
    public void LeftTiltPocketIsTheRightsMirrorForAnUnfittedKind()
    {
        var p = WeaponSockets.TiltPocketL(WeaponKind.Axe)!.Value;
        Assert.True(Vector3.Distance(WeaponSockets.ToLeft(WeaponSockets.BladeAtR), p.At) < 1e-6f);
        Assert.True(Vector3.Distance(Mirror(WeaponSockets.BladeAtR), p.At) < 1e-3f);
        Assert.True(Vector3.Distance(Mirror(WeaponSockets.BladeDirR), p.Dir) < 1e-2f);
        Assert.Equal(1f, p.Dir.Length(), 1e-4f);
    }

    [Fact]
    public void LeftTiltPocketKeepsAFittedLeftPocketAndSkipsThePistol()
    {
        Assert.Equal(WeaponSockets.PocketL(WeaponKind.Dagger), WeaponSockets.TiltPocketL(WeaponKind.Dagger));
        Assert.Null(WeaponSockets.TiltPocketL(WeaponKind.Crossbow));
        Assert.Null(WeaponSockets.TiltPocketL(WeaponKind.Shield));
    }

    [Fact]
    public void LeftTiltAxisTurnsTheMirrorImage()
    {
        // A + tilt about hand_r +X, carried through the mirror, is the same + tilt about TiltAxisL in hand_l.
        var axis = WeaponSockets.TiltAxisL;
        Assert.True(axis.X > 0.999f);
        var v = Vector3.Normalize(new Vector3(0.1f, 0.57f, 0.82f));
        var right = Vector3.Transform(v, Quaternion.CreateFromAxisAngle(Vector3.UnitX, 30f * MathF.PI / 180f));
        var left = Vector3.Transform(WeaponSockets.ToLeft(v), Quaternion.CreateFromAxisAngle(axis, 30f * MathF.PI / 180f));
        Assert.True(Vector3.Distance(WeaponSockets.ToLeft(right), left) < 1e-5f, $"{WeaponSockets.ToLeft(right)} != {left}");
    }

    [Fact]
    public void BlendEasesTheSeatOver()
    {
        var a = Quaternion.Identity; var b = Quaternion.CreateFromAxisAngle(Vector3.UnitX, 0.4f);
        var pa = new Vector3(-0.025f, 0.075f, 0f); var pb = new Vector3(0.043f, 0.089f, -0.013f);
        Assert.Equal((a, pa), GripSlide.Blend(a, pa, b, pb, 0f));
        Assert.Equal((b, pb), GripSlide.Blend(a, pa, b, pb, 1f));
        Assert.Equal((b, pb), GripSlide.Blend(a, pa, b, pb, 3f));
        var (q, at) = GripSlide.Blend(a, pa, b, pb, 0.5f);
        Near((pa + pb) / 2, at);
        Assert.True(MathF.Abs(Quaternion.Dot(q, Quaternion.CreateFromAxisAngle(Vector3.UnitX, 0.2f))) > 0.99999f);
    }
}
