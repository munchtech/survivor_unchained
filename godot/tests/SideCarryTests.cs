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

    // (judge r4 fix 2, lead r5) Out of a sword-side stand into a fast turn (the start flick): the drawn blade turns on
    // screen no faster than the clip's own turn plus ScreenRate, the tip turning in or out where the tilt can't reach.
    // (judge r5) the blade's turn beyond her turn + ScreenRate, over the frames of her turn (all 30 with turnOnly false)
    static float MaxExcess(SideCarry c, float to, bool turnOnly = false)
    {
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 0f, At(90f, 0f));
        float worst = float.MinValue, pa = float.NaN, pc = float.NaN;
        for (int i = 0; i < 30; i++)
        {
            float face = 90f + (to - 90f) * MathF.Min(1f, i / 6f);
            var f = At(face, MathF.Min(1f, i / 3f));
            c.Step(Dt, true, 0f, f);
            float a0 = SideCarry.ScreenAngle(f.Blade, Jx, Jy, 1f);
            float a = SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), Jx, Jy, 1f);
            if (!float.IsNaN(pa) && (!turnOnly || i <= 6))
            {
                float W(float d) { d %= 360f; return d > 180f ? d - 360f : d < -180f ? d + 360f : d; }
                float cap = MathF.Abs(W(a0 - pc)) + c.ScreenRate * Dt;
                // (lead r9) a crossing of the down band is made whole in one frame: up to twice its edge plus the slack
                if (c.Cross && (a > 0f) != (pa > 0f) && MathF.Abs(pa) >= c.DownBand - 0.5f && MathF.Abs(a) >= c.DownBand - 0.5f)
                    cap = MathF.Max(cap, 2f * (c.DownBand + c.CrossMargin) + c.CrossSlack + 1f);
                worst = MathF.Max(worst, MathF.Abs(W(a - pa)) - cap);
            }
            pa = a; pc = a0;
        }
        return worst;
    }

    [Theory]
    [InlineData(-90f)]     // side_x stand to side_mx: the half turn through facing the camera
    [InlineData(270f)]     // the half turn the other way, through facing away
    [InlineData(0f)]       // a quarter turn to face the camera
    public void OutOfASideStandTheBladeTurnsNoFasterThanHerPlusTheRate(float to)
    {
        float e = MaxExcess(new SideCarry(), to, turnOnly: true);
        Assert.True(e <= 1f, $"blade outran her turn by {e:F1} deg in a frame");
        float off = MaxExcess(new SideCarry { CarryRate = 0f }, to);
        Assert.True(off <= 1f, $"with CarryRate 0 the blade outran her turn by {off:F1} deg in a frame");
    }

    // (judge r5) Once her turn has ended the blade may ease on at the carry rate, never faster; while she turns it may not.
    [Theory]
    [InlineData(-90f)]
    [InlineData(270f)]
    [InlineData(180f)]
    public void OnceHerTurnEndsTheBladeEasesOnNoFasterThanTheCarryRate(float to)
    {
        var c = new SideCarry();
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 0f, At(90f, 0f));
        float pa = float.NaN, pc = float.NaN;
        float W(float d) { d %= 360f; return d > 180f ? d - 360f : d < -180f ? d + 360f : d; }
        for (int i = 0; i < 30; i++)
        {
            float face = 90f + (to - 90f) * MathF.Min(1f, i / 6f);
            var f = At(face, MathF.Min(1f, i / 3f));
            c.Step(Dt, true, 0f, f);
            float a0 = SideCarry.ScreenAngle(f.Blade, Jx, Jy, 1f);
            float a = SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), Jx, Jy, 1f);
            if (!float.IsNaN(pa) && i >= 8)
            {
                float allow = MathF.Max(MathF.Abs(W(a0 - pc)) + c.ScreenRate * Dt, c.CarryRate * Dt);
                Assert.True(MathF.Abs(W(a - pa)) <= allow + 1f, $"frame {i}: {MathF.Abs(W(a - pa)):F1} deg against {allow:F1}");
            }
            pa = a; pc = a0;
        }
    }

    // (judge r5) While the weight falls, the layer never leaves the blade nearer straight down than the clip's own (to Hold).
    [Theory]
    [InlineData(-90f)]
    [InlineData(270f)]
    [InlineData(180f)]
    public void FadingNeverHangsTheBladeNearerDownThanTheClip(float to)
    {
        var c = new SideCarry();
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 0f, At(90f, 0f));
        float pa = float.NaN;
        for (int i = 0; i < 30; i++)
        {
            float w = c.Weight, face = 90f + (to - 90f) * MathF.Min(1f, i / 6f);
            var f = At(face, MathF.Min(1f, i / 3f));
            c.Step(Dt, true, 0f, f);
            float a0 = SideCarry.ScreenAngle(f.Blade, Jx, Jy, 1f);
            float a = SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), Jx, Jy, 1f);
            // where the blade was already on the clip's side, out of the band (a crossing from the other side is rate-limited)
            if (c.Weight < w && MathF.Abs(a0) >= 15f && (pa > 0f) == (a0 > 0f) && MathF.Abs(pa) >= MathF.Min(MathF.Abs(a0), c.Hold) - 1f)
                Assert.True(MathF.Abs(a) >= MathF.Min(MathF.Abs(a0), c.Hold) - 6f, $"frame {i}: {a:F1} against the clip's {a0:F1}");
            pa = a;
        }
    }

    // (judge r6, lead r9) A stand pivot (her sword side swung away through her back or front): the drawn blade, once out of the
    // down band, never lands back inside it while the layer holds weight; it waits at the edge and crosses in one frame.
    static int BandLandings(bool cross, float to, int turnFrames)
    {
        var c = new SideCarry { Cross = cross };
        for (int i = 0; i < 30; i++) c.Step(Dt, true, 0f, At(90f, 0f));
        float pa = float.NaN; int n = 0;
        for (int i = 0; i < 40; i++)
        {
            float face = 90f + (to - 90f) * MathF.Min(1f, i / (float)turnFrames);
            var f = At(face, 0f);
            c.Step(Dt, true, 0f, f);
            float a0 = SideCarry.ScreenAngle(f.Blade, Jx, Jy, 1f);
            float a = SideCarry.ScreenAngle(SideCarry.Turned(f.Blade, f.Left, c.Tilt, f.Ahead, c.Inward), Jx, Jy, 1f);
            if (MathF.Abs(pa) >= c.DownBand && MathF.Abs(a) < c.DownBand - 0.5f && (c.Weight >= c.CrossWeight || MathF.Abs(a0) >= c.DownBand)) n++;
            pa = a;
        }
        return n;
    }

    [Theory]
    [InlineData(-90f, 6)]
    [InlineData(270f, 6)]
    [InlineData(-90f, 12)]
    [InlineData(270f, 12)]
    [InlineData(180f, 8)]
    [InlineData(0f, 8)]
    public void AStandPivotNeverDropsTheBladeIntoTheDownBand(float to, int turnFrames) =>
        Assert.Equal(0, BandLandings(true, to, turnFrames));

    [Fact]
    public void WithoutTheCrossRuleAPivotDoesLandInTheBand()
    {
        int n = 0;
        foreach (var (to, tf) in new[] { (-90f, 6), (270f, 6), (-90f, 12), (270f, 12), (180f, 8), (0f, 8) }) n += BandLandings(false, to, tf);
        Assert.True(n > 0, "the pivot cases never touch the band, so the theory above tests nothing");
    }

    // (judge r4, solver 18) A calf across the drawn blade's line (strafe_fx_a: the crossing foot behind the blade's middle):
    // the tip turns out by the least that keeps the blade Clear off it, no more than OutMax; with the calf away, none.
    [Fact]
    public void CalfAcrossTheBladeTurnsTheTipOutJustEnough()
    {
        var c = new SideCarry();
        var (a, l, b) = Her(90f);
        Vector3 Far = new(0f, -0.6f, 3f);
        SideCarry.Frame F(Vector3 k, Vector3 an) => new(b, l, a, Jx, Jy, CamBack, 1f, 0f, Vector3.Zero, 1.0f, Far, Far + new Vector3(0f, -0.4f, 0f), k, an);
        for (int i = 0; i < 40; i++) c.Step(Dt, true, 0f, F(Far, Far + new Vector3(0f, -0.4f, 0f)));
        Assert.Equal(0f, c.OutTurn);
        // the calf upright, 0.10 m in from the drawn blade's point 0.5 m out (its skin 3-4 cm off it)
        var d = SideCarry.Turned(b, l, c.Tilt, a, c.Inward);
        var p = d * 0.5f + l * 0.10f;
        Vector3 knee = p + new Vector3(0f, 0.2f, 0f), ankle = p - new Vector3(0f, 0.2f, 0f);
        Span<Vector3> cv = stackalloc Vector3[4] { Far, Far + new Vector3(0f, -0.4f, 0f), knee, ankle };
        Assert.InRange(c.ClearOf(d, 1.0f, cv), -1f, c.Clear - 1e-4f);
        for (int i = 0; i < 12; i++) c.Step(Dt, true, 0f, F(knee, ankle));   // (its arrival, a jump, reads as motion for two frames)
        Assert.InRange(c.OutTurn, 0.5f, c.OutMax - 0.5f);
        var drawn = SideCarry.Turned(b, l, c.Tilt, a, c.Inward);
        Assert.InRange(c.ClearOf(drawn, 1.0f, cv), MathF.Min(c.Clear, c.ClearOf(b, 1.0f, cv)) - 1e-4f, 9f);
        // the least: half a degree less would not clear
        var less = SideCarry.Turned(b, l, c.Tilt, a, c.Inward + 0.5f);
        Assert.InRange(c.ClearOf(less, 1.0f, cv), -1f, c.Clear);
        // the calf gone: it eases back (ClearDown a second), not at once
        float was = c.OutTurn;
        c.Step(Dt, true, 0f, F(Far, Far + new Vector3(0f, -0.4f, 0f)));
        Near(MathF.Max(0f, was - c.ClearDown * Dt), c.OutTurn, 0.6f);
    }
}
