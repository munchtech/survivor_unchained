using System;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A garment's hanging chains (Play/ClothChains.cs, run by View/PieceSprings): a 5-link cape column of a
/// 2.08x giant (0.5 m links, world units) as heavy soaked wool: still at its bind, a slow heavy swing that settles in
/// about a second with little bounce, kept out of a leg swung through it, and settled on a reset (a cut).</summary>
public class ClothChainsTests
{
    const float Dt = 1f / 60;
    static readonly Vector3 Down = -Vector3.UnitY;

    static (ClothChains C, Vector3[] T) Column(int links = 5, float len = 0.5f)
    {
        var par = Enumerable.Range(0, links + 1).Select(i => i - 1).ToArray();
        var rad = Enumerable.Repeat(0.1f, links + 1).ToArray();
        var t = Enumerable.Range(0, links + 1).Select(i => new Vector3(0, -len * i, 0)).ToArray();
        return (new ClothChains(par, rad, ClothChains.Tuning.Wool), t);
    }

    static Vector3[] Tilt(Vector3[] t, float deg)
    {
        var q = Quaternion.CreateFromAxisAngle(Vector3.UnitX, deg * MathF.PI / 180);
        return t.Select(p => Vector3.Transform(p, q)).ToArray();
    }

    [Fact]
    public void TheBindDrapeHangsStill()
    {
        var (c, t) = Column();
        var none = Array.Empty<ClothChains.Capsule>();
        c.Reset(t, none, null, Down);
        for (int f = 0; f < 120; f++) c.Step(Dt, t, none, null, Down);
        Assert.True(t.Zip(c.Positions).Max(p => (p.First - p.Second).Length()) < 1e-3f);
    }

    [Fact]
    public void ASwingIsSlowHeavyAndSettlesInASecond()
    {
        var none = Array.Empty<ClothChains.Capsule>();
        var (c, t) = Column();
        var bent = Tilt(t, 40);   // (the body tips 40 deg forward: the drape now leans off the vertical)
        c.Reset(bent, none, null, Down);
        for (int f = 0; f < 240; f++) c.Step(Dt, bent, none, null, Down);
        var final = c.Positions[^1];

        (c, _) = Column();
        c.Reset(t, none, null, Down);
        var start = c.Positions[^1];
        var axis = Vector3.Normalize(final - start);
        float span = (final - start).Length(), over = 0, at1 = 0, lag = 0;
        // (the body bends over a quarter second, as a lunge or a stoop does, then holds)
        for (int f = 1; f <= 135; f++)
        {
            float u = Math.Min(1, f / 15f);
            var pose = Tilt(t, 40 * u * u * (3 - 2 * u));
            c.Step(Dt, pose, none, null, Down);
            var tip = c.Positions[^1];
            over = Math.Max(over, Vector3.Dot(tip - final, axis));
            if (f == 15) lag = Vector3.Dot(final - tip, axis);
            if (f == 75) at1 = (tip - final).Length();
        }
        Assert.True(span > 0.2f, $"span {span}");
        Assert.True(lag > 0.25f * span, $"heavy: {lag / span:P0} behind as the bend ends");   // (it trails the body)
        Assert.True(at1 < 0.15f * span, $"settled: {at1 / span:P0} left 1 s after");
        Assert.True(over < 0.12f * span, $"bounce: {over / span:P0} past");
    }

    [Fact]
    public void ALegSwungThroughItPushesItAside()
    {
        var (c, t) = Column();
        ClothChains.Capsule Leg(float z) => new(new Vector3(-0.5f, -1.6f, z), new Vector3(0.5f, -1.6f, z), 0.12f);
        var rest = new[] { Leg(0.35f) };
        c.SetRest(t, rest);
        c.Reset(t, rest, null, Down);
        float worst = 0;
        for (int f = 0; f <= 60; f++)
        {
            var leg = new[] { Leg(0.35f - 0.75f * f / 60f) };   // (0.75 m back in a second, through where the chain hangs)
            c.Step(Dt, t, leg, null, Down);
            worst = Math.Max(worst, c.Penetration(leg)[0]);
        }
        Assert.True(worst < 0.02f, $"{worst * 100:0.0} cm inside the leg");
        Assert.True(c.Positions[^1].Z < -0.1f, "pushed back");
    }

    [Fact]
    public void AResetSettlesTheHangSoACutNeverFlingsIt()
    {
        var none = Array.Empty<ClothChains.Capsule>();
        var (c, t) = Column();
        var bent = Tilt(t, 75);
        c.Reset(bent, none, null, Down);
        var before = c.Positions[^1];
        c.Step(Dt, bent, none, null, Down);
        Assert.True((c.Positions[^1] - before).Length() < 0.005f);
        Assert.True(c.Positions[^1].Y < bent[^1].Y - 0.3f, "it hangs, not sticks out with the bend");
    }

    [Fact]
    public void TheGroundHoldsTheHem()
    {
        var none = Array.Empty<ClothChains.Capsule>();
        var (c, t) = Column();
        c.Reset(t, none, -2.2f, Down);
        Assert.True(c.Positions.All(p => p.Y >= -2.2f + 0.1f - 1e-4f));
    }

    [Fact]
    public void ChainsAreOrderedFromTheirRoots()
    {
        var (lp, par, root) = ClothChains.Order(new[] { ("a0", "spine_03"), ("a1", "a0"), ("b0", "clavicle_l"), ("a2", "a1") });
        Assert.Equal(new[] { -1, 0, 1, 2, -1, 4 }, par);
        Assert.Equal(new[] { 1, 2, 5, 3 }, lp);
        Assert.Equal(0, root[0]);
        Assert.Equal(2, root[4]);
    }

    [Theory]
    [InlineData(0, 0)]
    [InlineData(60, 60)]
    [InlineData(-20, -20)]
    public void PitchIsTheForwardTipSideOn(float deg, float want)
    {
        var rest = Vector3.Normalize(new Vector3(0.1f, 1, -0.3f));
        var now = Vector3.Transform(rest, Quaternion.CreateFromAxisAngle(Vector3.UnitX, deg * MathF.PI / 180));
        Assert.Equal((double)want, ClothChains.Pitch(rest, now), 2);
        Assert.True(ClothChains.Pitch(Vector3.UnitY, Vector3.UnitZ) > 89);   // (top toward +Z, forward)
    }

    [Theory]
    [InlineData(30, 0)]
    [InlineData(40, 0)]
    [InlineData(60, 0.5)]
    [InlineData(80, 1)]
    [InlineData(95, 1)]
    public void CorrectiveWeightIsASmoothstep(float deg, float w) => Assert.Equal((double)w, ClothChains.Weight(deg, 40, 80), 4);
}
