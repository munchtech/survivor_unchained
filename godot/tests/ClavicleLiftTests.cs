using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her clavicle lift (Play/ClavicleLift.cs): none at and below 60 degrees, a smoothstep to 34 overhead, the
/// clip's own lift counted (never a sum), the hand kept, the lift cut back where the hand would be out of reach.</summary>
public class ClavicleLiftTests
{
    static readonly Vector3 Down = -Vector3.UnitY, Lat = Vector3.UnitX, Fwd = Vector3.UnitZ;

    // her left arm: clavicle from (0.02, 1.4, 0) out to the shoulder at (0.17, 1.42, 0), the upper arm 0.28 m at A, the
    // forearm 0.25 m bent a quarter turn forward
    static ClavicleLift.Arm Arm(float aDeg, float clavRise = 0f, float bend = 90f)
    {
        var pc = new Vector3(0.02f, 1.4f, 0f);
        var lean = Quaternion.CreateFromAxisAngle(Fwd, clavRise * MathF.PI / 180f);
        var s = pc + Vector3.Transform(new Vector3(0.15f, 0.02f, 0f), lean);
        float a = aDeg * MathF.PI / 180f;
        var up = new Vector3(MathF.Sin(a), -MathF.Cos(a), 0f);
        var e = s + 0.28f * up;
        float b = bend * MathF.PI / 180f;
        var h = e + 0.25f * (MathF.Cos(b) * up + MathF.Sin(b) * Fwd);
        return new ClavicleLift.Arm { Clavicle = pc, Shoulder = s, Elbow = e, Hand = h, ClavicleTurn = lean, UpperTurn = Quaternion.Identity, LowerTurn = Quaternion.Identity };
    }

    static float RestEl => ClavicleLift.Elevation(new Vector3(0.15f, 0.02f, 0f), Down);

    [Theory]
    [InlineData(0f)]
    [InlineData(39f)]   // her rest A-pose
    [InlineData(60f)]
    public void NothingAtOrBelowSixty(float a)
    {
        var arm = Arm(a, -3f);
        var before = arm;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.Equal(0f, lift);
        Assert.Equal(before.ClavicleTurn, arm.ClavicleTurn);
        Assert.Equal(before.UpperTurn, arm.UpperTurn);
    }

    [Fact]
    public void ACurveEasedInFromSixty()
    {
        Assert.Equal(0f, ClavicleLift.Target(60f));
        Assert.True(ClavicleLift.Target(62f) < 0.05f);
        Assert.InRange(ClavicleLift.Target(90f), 5f, 5.6f);
        Assert.InRange(ClavicleLift.Target(115f), 14.5f, 15.2f);
        Assert.InRange(ClavicleLift.Target(117f), 15.3f, 16.1f);
        Assert.InRange(ClavicleLift.Target(140f), 24.8f, 25.6f);
        Assert.InRange(ClavicleLift.Target(175f), 33.5f, 34f);
        Assert.Equal(34f, ClavicleLift.Target(200f));
        // rising, and no kink: the slope changes by less than 0.02 deg/deg per degree anywhere (smoothstep: at most 0.0142)
        float prev = 0, prevSlope = 0;
        for (float a = 58f; a <= 182f; a += 1f)
        {
            float t = ClavicleLift.Target(a), slope = t - prev;
            Assert.True(slope >= 0f);
            if (a > 58f) Assert.True(MathF.Abs(slope - prevSlope) < 0.02f, $"kink at {a}");
            prev = t; prevSlope = slope;
        }
    }

    [Fact]
    public void WithHerScapulaeTheClavicleRisesLess()
    {
        Assert.Equal(0f, ClavicleLift.Target(60f, true));
        Assert.InRange(ClavicleLift.Target(90f, true), 1.9f, 2.1f);
        Assert.InRange(ClavicleLift.Target(140f, true), 9.4f, 9.8f);
        Assert.InRange(ClavicleLift.Target(160f, true), 11.9f, 12.4f);
        Assert.Equal(13f, ClavicleLift.Target(200f, true));
        // the outer end turned back, not forward: the shoulder lands behind where the old curve put it
        var a = Arm(160f); var b = Arm(160f);
        ClavicleLift.Apply(ref a, Down, Lat, Fwd, RestEl, true);
        ClavicleLift.Apply(ref b, Down, Lat, Fwd, RestEl);
        var before = Arm(160f).Shoulder;
        Assert.True(a.Shoulder.Z < before.Z - 0.005f, $"back {a.Shoulder.Z - before.Z}");
        Assert.True(a.Shoulder.Y - before.Y < b.Shoulder.Y - before.Y);
    }

    [Fact]
    public void TheClipsOwnLiftCountsNeverASum()
    {
        var arm = Arm(140f, 5f);
        var (_, rise, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.Equal(5f, rise, 0.01f);
        Assert.Equal(ClavicleLift.Target(140f) - 5f, lift, 0.01f);
        arm = Arm(140f, 40f);
        Assert.Equal(0f, ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl).Lift);
    }

    [Theory]
    [InlineData(90f, 90f)]
    [InlineData(117f, 90f)]
    [InlineData(140f, 40f)]
    [InlineData(170f, 20f)]
    public void TheHandStaysAndTheShoulderRises(float a, float bend)
    {
        var arm = Arm(a, 0f, bend);
        var s0 = arm.Shoulder; var h = arm.Hand; var e0 = arm.Elbow;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.True(lift > 1f);
        Assert.True(arm.Shoulder.Y > s0.Y + 0.005f);
        // the re-aimed bones: the upper arm reaches the new elbow, the forearm the old hand
        Assert.Equal(0f, (arm.Shoulder + Vector3.Transform((e0 - s0), arm.UpperTurn) - arm.Elbow).Length(), 0.001f);
        Assert.Equal(0f, (arm.Elbow + Vector3.Transform(h - e0, arm.LowerTurn) - h).Length(), 0.001f);
    }

    [Fact]
    public void AStraightArmOutToTheSideCutsTheLiftBack()
    {
        // (lifting the clavicle's outer end draws the shoulder up and in, away from a straight arm's hand out past level: the
        // shoulder may not move away from the hand, so the lift is cut back, here to nothing)
        var arm = Arm(100f, 0f, 0f);
        var h = arm.Hand; var e0 = Arm(100f, 0f, 0f).Elbow;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.True(lift < ClavicleLift.Target(100f), $"lift {lift} target {ClavicleLift.Target(100f)}");
        Assert.True((h - arm.Shoulder).Length() <= 0.53f + 1e-4f, $"reach {(h - arm.Shoulder).Length()}");
        Assert.Equal(0f, (arm.Elbow + Vector3.Transform(h - e0, arm.LowerTurn) - h).Length(), 0.001f);
    }

    [Fact]
    public void AStraightArmOverheadKeepsTheWholeLift()
    {
        // (overhead the lifted shoulder comes nearer the hand: the elbow bends a little, the hand stays)
        var arm = Arm(175f, 0f, 0f);
        var h = arm.Hand; var e0 = Arm(175f, 0f, 0f).Elbow;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.Equal(ClavicleLift.Target(175f), lift, 0.01f);
        Assert.Equal(0f, (arm.Elbow + Vector3.Transform(h - e0, arm.LowerTurn) - h).Length(), 0.001f);
    }
}
