using System;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her clavicle lift (Play/ClavicleLift.cs): none at and below level, a third of the raise past level, the
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
    [InlineData(90f)]
    public void NothingAtOrBelowLevel(float a)
    {
        var arm = Arm(a, -3f);
        var before = arm;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.Equal(0f, lift);
        Assert.Equal(before.ClavicleTurn, arm.ClavicleTurn);
        Assert.Equal(before.UpperTurn, arm.UpperTurn);
    }

    [Fact]
    public void ATargetOfAThirdPastLevel()
    {
        Assert.Equal(0f, ClavicleLift.Target(90f));
        Assert.InRange(ClavicleLift.Target(117f), 7f, 9f);
        Assert.InRange(ClavicleLift.Target(175f), 27f, 31f);
        Assert.True(ClavicleLift.Target(92f) < 0.2f);
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
    [InlineData(117f, 90f)]
    [InlineData(140f, 40f)]
    [InlineData(170f, 20f)]
    public void TheHandStaysAndTheShoulderRises(float a, float bend)
    {
        var arm = Arm(a, 0f, bend);
        var s0 = arm.Shoulder; var h = arm.Hand; var e0 = arm.Elbow;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.True(lift > 1f);
        Assert.True(arm.Shoulder.Y > s0.Y + 0.01f);
        // the re-aimed bones: the upper arm reaches the new elbow, the forearm the old hand
        Assert.Equal(0f, (arm.Shoulder + Vector3.Transform((e0 - s0), arm.UpperTurn) - arm.Elbow).Length(), 0.001f);
        Assert.Equal(0f, (arm.Elbow + Vector3.Transform(h - e0, arm.LowerTurn) - h).Length(), 0.001f);
    }

    [Fact]
    public void AStraightArmOverheadCutsTheLiftBack()
    {
        var arm = Arm(175f, 0f, 0f);
        var h = arm.Hand;
        var (_, _, lift) = ClavicleLift.Apply(ref arm, Down, Lat, Fwd, RestEl);
        Assert.True(lift < ClavicleLift.Target(175f));
        Assert.Equal(0f, (arm.Elbow + Vector3.Transform(h - Arm(175f, 0f, 0f).Elbow, arm.LowerTurn) - h).Length(), 0.001f);
    }
}
