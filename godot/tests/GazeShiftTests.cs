using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her eyes' and head's look (Play/GazeShift, run by HerFaceLife and GazeCarry): saccades timed by the main
/// sequence and skewed fast-in, slow-out; the eyes held inside their reach; the head carrying a big look while the eyes
/// roll back, the two summing to the look; small glances eyes-only; the lids riding on the eyes; a blink on a big jump.</summary>
public class GazeShiftTests
{
    const float Eps = 1e-4f;

    [Fact]
    public void SaccadesLastByTheirSize()
    {
        // 0.1 radii = 2.5 deg: 21 + 5.5 ms; 0.9 radii = 22.5 deg: 21 + 49.5 ms.
        Assert.Equal(0.0265, GazeShift.SaccadeTime(0.1f), 4);
        Assert.Equal(0.0705, GazeShift.SaccadeTime(0.9f), 4);
        Assert.True(GazeShift.SaccadeTime(0.9f) > GazeShift.SaccadeTime(0.1f));
    }

    [Fact]
    public void SkewedProfileIsMonotoneFastInAndEndsExactly()
    {
        Assert.Equal(0f, GazeShift.Skewed(0));
        Assert.Equal(1f, GazeShift.Skewed(1));
        Assert.Equal(1f, GazeShift.Skewed(1.5f));
        float prev = 0, bestV = 0, bestX = 0;
        for (int i = 1; i <= 200; i++)
        {
            float x = i / 200f, p = GazeShift.Skewed(x);
            Assert.True(p >= prev - 1e-6f);
            if (p - prev > bestV) { bestV = p - prev; bestX = x; }
            prev = p;
        }
        Assert.InRange(bestX, 0.2f, 0.4f);
        // (past half its travel before 40% of its time)
        Assert.True(GazeShift.Skewed(0.4f) > 0.5f);
    }

    [Fact]
    public void SaccadeLandsOnTargetAtItsTime()
    {
        var g = new GazeShift();
        g.Move(0, new Vector2(0.2f, 0), 0, null);
        double end = GazeShift.SaccadeTime(0.2f);
        g.Step(end * 0.5);
        Assert.InRange(g.Eye.X, 0.1f, 0.2f);
        g.Step(end);
        Assert.Equal(0.2f, g.Eye.X, 1e-4f);
    }

    [Fact]
    public void EyesNeverPassTheirReach()
    {
        var g = new GazeShift();
        g.Move(0, new Vector2(0, 0.9f), 0, Vector2.Zero);
        for (double t = 0; t < 1; t += 0.005) { g.Step(t); Assert.True(g.Eye.Length() <= g.Reach + Eps); }
        Assert.Equal(new Vector2(0.3f, 0), GazeShift.Clamp(new Vector2(0.3f, 0), 0.5f));
        Assert.Equal(0.5f, GazeShift.Clamp(new Vector2(0.6f, 0.8f), 0.5f).Length(), 1e-4f);
    }

    [Fact]
    public void HeadCarriesABigLookAndTheEyesRollBack()
    {
        // A look of 0.45 down from ahead (inside the eyes' reach): the head takes 0.6 of it, and from the saccade's
        // end the eyes and the head sum to the look at every moment, the eyes rolling back as the head comes.
        var g = new GazeShift();
        var look = new Vector2(0, 0.45f);
        var h = GazeShift.HeadFor(look, g.Head, (look - g.Net).Length(), null, g.Reach);
        Assert.Equal(0.27f, h.Y, 1e-4f);
        g.Move(0, look, 0, h);
        double sEnd = GazeShift.SaccadeTime(0.45f);
        float lastEye = float.MaxValue;
        for (double t = sEnd; t < 1.2; t += 0.01)
        {
            g.Step(t);
            Assert.True(Vector2.Distance(g.Eye + g.Head, look) < Eps, $"t {t}: {g.Eye} + {g.Head}");
            Assert.True(g.Eye.Y <= lastEye + Eps);
            lastEye = g.Eye.Y;
        }
        Assert.Equal(0.27f, g.Head.Y, 1e-4f);
        Assert.Equal(0.18f, g.Eye.Y, 1e-4f);
        // (the head waits HeadLag after the eyes)
        var g2 = new GazeShift();
        g2.Move(0, look, 0, h);
        g2.Step(GazeShift.HeadLag * 0.9);
        Assert.Equal(Vector2.Zero, g2.Head);
    }

    [Fact]
    public void ALookPastReachEndsOnTarget()
    {
        // C01's [0,0.1] -> [0,0.9]: the eyes jump to their reach, the head takes the excess and its share, the eyes
        // never pass the reach, and once the head is there the look is the target.
        var g = new GazeShift();
        g.Set(new Vector2(0, 0.1f), Vector2.Zero);
        var look = new Vector2(0, 0.9f);
        var h = GazeShift.HeadFor(look, g.Head, (look - g.Net).Length(), null, g.Reach);
        float jump = g.Move(0, look, 0, h);
        Assert.Equal(0.4f, jump, 1e-4f);
        for (double t = 0; t < 2; t += 0.01)
        {
            g.Step(t);
            Assert.True(g.Eye.Length() <= g.Reach + Eps);
            Assert.True((g.Eye + g.Head).Y <= look.Y + Eps);
        }
        Assert.True(Vector2.Distance(g.Eye + g.Head, look) < Eps);
        Assert.Equal(0.54f, g.Head.Y, 1e-4f);
    }

    [Fact]
    public void SmallShiftsLeaveTheHead()
    {
        var g = new GazeShift();
        var look = new Vector2(0.25f, 0);
        var h = GazeShift.HeadFor(look, g.Head, 0.25f, null, g.Reach);
        Assert.Equal(Vector2.Zero, h);
        g.Move(0, look, 0, h);
        for (double t = 0; t < 1; t += 0.02) { g.Step(t); Assert.Equal(Vector2.Zero, g.Head); }
        Assert.Equal(0.25f, g.Eye.X, 1e-4f);
        // (a head already turned stays turned for a small glance, and comes back near centre)
        Assert.Equal(new Vector2(0.3f, 0), GazeShift.HeadFor(new Vector2(0.5f, 0), new Vector2(0.3f, 0), 0.2f, null, 0.5f));
        Assert.Equal(Vector2.Zero, GazeShift.HeadFor(new Vector2(0.05f, 0), new Vector2(0.3f, 0), 0.6f, null, 0.5f));
        // (a scripted head look owns the head)
        Assert.Equal(Vector2.Zero, GazeShift.HeadFor(new Vector2(0, 0.9f), Vector2.Zero, 0.9f, null, 0.5f, owned: true));
    }

    [Fact]
    public void AGlideTakesItsTime()
    {
        var g = new GazeShift();
        g.Move(0, new Vector2(0.3f, 0), over: 1.0, headTo: null);
        g.Step(0.5);
        Assert.Equal(0.15f, g.Eye.X, 1e-4f);
        g.Step(1.0);
        Assert.Equal(0.3f, g.Eye.X, 1e-4f);
    }

    [Fact]
    public void LidsRideOnTheEyes()
    {
        const float rest = 0.2f;
        Assert.Equal(rest, GazeShift.Lid(rest, 0, 0), 1e-4f);
        Assert.Equal(rest + 0.45f * 0.8f * 0.5f, GazeShift.Lid(rest, 0, 0.5f), 1e-4f);
        Assert.Equal(rest + 0.45f * 0.8f * 0.9f, GazeShift.Lid(rest, 0, 0.9f), 1e-4f);
        Assert.Equal(rest - 0.2f * 0.8f * 0.5f, GazeShift.Lid(rest, 0, -0.5f), 1e-4f);
        Assert.True(GazeShift.Lid(rest, 0, -0.5f) < rest);
        Assert.Equal(0f, GazeShift.Lid(0, 0, -0.5f));
        // (a blink still shuts, whatever the eyes do; a held lid is the lid at straight-ahead)
        Assert.Equal(1f, GazeShift.Lid(rest, 1, 0.9f), 1e-4f);
        Assert.Equal(1f, GazeShift.Lid(rest, 1, -0.5f), 1e-4f);
        Assert.True(GazeShift.Lid(rest, 0.5f, 0.5f) > GazeShift.Lid(rest, 0.5f, 0));
    }

    [Fact]
    public void BigJumpsBlink()
    {
        Assert.False(GazeShift.BlinkOn(0.39f, null, false));
        Assert.True(GazeShift.BlinkOn(0.4f, null, false));
        Assert.True(GazeShift.BlinkOn(0.1f, true, false));
        Assert.False(GazeShift.BlinkOn(0.9f, false, false));
        Assert.False(GazeShift.BlinkOn(0.9f, null, true));
        Assert.False(GazeShift.BlinkOn(0.9f, true, true));
    }

    [Fact]
    public void ACutSetsTheLookAtOnce()
    {
        var g = new GazeShift();
        var look = new Vector2(0.9f, 0.05f);
        g.Set(look, GazeShift.HeadFor(look, g.Head, float.MaxValue, null, g.Reach));
        g.Step(0);
        Assert.True(Vector2.Distance(g.Eye + g.Head, look) < Eps);
        Assert.True(g.Eye.Length() <= g.Reach + Eps);
    }
}
