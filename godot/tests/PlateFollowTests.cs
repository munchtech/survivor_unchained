using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Plates riding their own weights and held off the body's skin (Play/PlateFollow, run by View/PieceSprings on
/// her rows with "follow"): the rotation fit recovers a known turn, the farthest-point picks are deterministic, and a
/// plate on a link over a swung thigh is kept out of it by the collider, and only by the collider.</summary>
public class PlateFollowTests
{
    const float Dt = 1f / 60;
    const float Radius = 0.08f;

    [Fact]
    public void RotationRecoversAKnownTurnFromAnIdentityGuess()
    {
        var want = Quaternion.CreateFromAxisAngle(Vector3.Normalize(new Vector3(1, 2, 3)), 70 * MathF.PI / 180);
        var rest = new[] { new Vector3(0.3f, 0.1f, -0.2f), new Vector3(-0.2f, 0.4f, 0.1f), new Vector3(0.1f, -0.3f, 0.5f), new Vector3(-0.4f, -0.2f, -0.3f), new Vector3(0.2f, 0.2f, 0.2f) };
        Vector3 c0 = Vector3.Zero, c1 = Vector3.Zero, c2 = Vector3.Zero;
        foreach (var r in rest)
        {
            var q = Vector3.Transform(r, want);
            c0 += q * r.X; c1 += q * r.Y; c2 += q * r.Z;
        }
        var got = PlateFollow.Rotation(c0, c1, c2, Quaternion.Identity, 30);
        Assert.True(MathF.Abs(Quaternion.Dot(got, want)) > 0.9999f, $"dot {Quaternion.Dot(got, want)}");
    }

    [Fact]
    public void SpreadIsDeterministicAndStartsWithTheStartThenTheFarthest()
    {
        var pts = new[] { new Vector3(0, 0, 0), new Vector3(1, 0, 0), new Vector3(0.4f, 0.1f, 0), new Vector3(5, 0, 0), new Vector3(2.5f, 0.2f, 0), new Vector3(-1, 3, 0) };
        var a = PlateFollow.Spread(pts, 4, 2);
        var b = PlateFollow.Spread(pts, 4, 2);
        Assert.Equal(a, b);
        Assert.Equal(2, a[0]);
        int far = Enumerable.Range(0, pts.Length).OrderByDescending(i => Vector3.DistanceSquared(pts[i], pts[2])).First();
        Assert.Equal(far, a[1]);
        Assert.Equal(a.Count, a.Distinct().Count());
    }

    static PlateFollow.Xf Rot(Quaternion q) => new(Vector3.Transform(Vector3.UnitX, q), Vector3.Transform(Vector3.UnitY, q), Vector3.Transform(Vector3.UnitZ, q), Vector3.Zero);

    /// <summary>A thigh (bone 1, hinged at the origin, hanging down -Y) and a plate on one link in front of it, 15 mm off
    /// its skin, half on the pelvis (bone 0) and half on the thigh; the thigh swung forward 40 degrees; the plates'
    /// vertices as the follow poses them after 60 frames, the deepest any stands inside the thigh (negative: outside).</summary>
    static (float Worst, int Pushes) Run(bool collide)
    {
        // (the body: a cylinder of points every ~1 cm, all on the thigh)
        var bp = new List<Vector3>(); var bn = new List<Vector3>();
        for (float y = 0; y >= -0.5f; y -= 0.01f)
            for (int a = 0; a < 48; a++)
            {
                float ang = a * MathF.Tau / 48;
                var n = new Vector3(MathF.Sin(ang), 0, MathF.Cos(ang));
                bp.Add(new Vector3(0, y, 0) + n * Radius); bn.Add(n);
            }
        var body = new PlateFollow.MeshIn
        {
            K = 1, Place = bp.ToArray(), Normal = bn.ToArray(), Bone = Enumerable.Repeat(1, bp.Count).ToArray(), Weight = Enumerable.Repeat(1f, bp.Count).ToArray(),
        };
        // (the plate: 0.12 x 0.06 of vertices every 5 mm, 15 mm off the skin, on link 0)
        var pp = new List<Vector3>(); var pn = new List<Vector3>();
        float rp = Radius + 0.015f;
        for (int i = 0; i <= 24; i++)
            for (int j = 0; j <= 12; j++)
            {
                float ang = (i * 0.005f - 0.06f) / rp;
                var n = new Vector3(MathF.Sin(ang), 0, MathF.Cos(ang));
                pp.Add(new Vector3(0, -0.10f - j * 0.005f, 0) + n * rp); pn.Add(n);
            }
        var plate = new PlateFollow.MeshIn
        {
            K = 2, Place = pp.ToArray(), Normal = pn.ToArray(),
            Bone = pp.SelectMany(_ => new[] { 0, 1 }).ToArray(), Weight = pp.SelectMany(_ => new[] { 0.5f, 0.5f }).ToArray(),
            Link = Enumerable.Repeat(0, pp.Count).ToArray(),
        };
        var head = new Vector3(0, -0.10f, rp); var tail = new Vector3(0, -0.16f, rp);
        var (lp, par, _) = ClothChains.Order(new List<(string, string)> { ("plate", "thigh") });
        var follow = PlateFollow.Build(new[] { new PlateFollow.Link(head, tail, -1) }, lp, par, new[] { plate }, body, PlateFollow.Tuning.Plate)!;
        Assert.NotNull(follow);
        var sim = new ClothChains(par, Enumerable.Repeat(0.01f, par.Length).ToArray(), ClothChains.Tuning.Wool);
        if (collide) sim.Hook = follow.Collide;
        // (the thigh swung forward about the hip's lateral axis: its skin carried into the plate)
        var swing = Quaternion.CreateFromAxisAngle(Vector3.UnitX, -40 * MathF.PI / 180);
        var skin = new[] { PlateFollow.Xf.Identity, Rot(swing) };
        var targets = new Vector3[par.Length];
        var none = Array.Empty<ClothChains.Capsule>();
        var down = -Vector3.UnitY;
        follow.Update(skin, PlateFollow.Xf.Identity, null, targets);
        follow.Cut();
        follow.Update(skin, PlateFollow.Xf.Identity, null, targets);
        sim.Reset(targets, none, null, down);
        int pushes = 0;
        for (int f = 0; f < 60; f++)
        {
            follow.Update(skin, PlateFollow.Xf.Identity, null, targets);
            sim.Step(Dt, targets, none, null, down);
            pushes += follow.Pushes;
        }
        // (each plate vertex as its link's bone poses it, against the thigh's posed axis)
        var (turn, h) = follow.Pose(0, sim.Positions);
        var axis = Vector3.Transform(-Vector3.UnitY, swing);
        float worst = float.MinValue;
        foreach (var v in pp)
        {
            var posed = h + Vector3.Transform(v - head, turn);
            float along = Vector3.Dot(posed, axis);
            if (along < 0 || along > 0.5f) continue;
            float radial = (posed - axis * along).Length();
            worst = Math.Max(worst, Radius - radial);
        }
        return (worst, pushes);
    }

    [Fact]
    public void ThePlateStaysOutsideTheSwungThighOnlyBecauseOfTheCollider()
    {
        var (held, pushes) = Run(true);
        Assert.True(pushes > 0, "the collider never pushed");
        Assert.True(held <= 0.0005f, $"a plate vertex stands {held * 1000:0.0} mm inside the thigh");
        var (free, _) = Run(false);
        Assert.True(free > 0.0005f, $"without the collider the deepest is {free * 1000:0.0} mm");
        // (deterministic: the same dress and the same frames land the same, bit for bit)
        var (again, pushesAgain) = Run(true);
        Assert.Equal(held, again);
        Assert.Equal(pushes, pushesAgain);
    }
}
