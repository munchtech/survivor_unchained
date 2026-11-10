using System;
using System.Collections.Generic;
using SurvivorUnchained.Look;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 lead 23, NORM2) SmoothNormals: a noisy sphere and a noisy capsule smooth back to their analytic normals,
/// opposite surfaces that touch never bleed, and a 60k-vertex mesh bakes fast.</summary>
public class SmoothNormalsTests
{
    readonly ITestOutputHelper log;
    public SmoothNormalsTests(ITestOutputHelper o) => log = o;

    /// <summary>A surface of revolution about y from a profile (r, y, analytic normal nr, ny), seg segments, seam and
    /// pole vertices duplicated (the weld joins them); normals noised by up to `noise` (unit vector added, renormalized).</summary>
    static (float[] P, float[] N, float[] A, int[] T) Revolve(List<(float r, float y, float nr, float ny)> prof, int seg, float noise, int seed, float ox = 0)
    {
        var rnd = new Random(seed);
        var P = new List<float>(); var N = new List<float>(); var A = new List<float>(); var T = new List<int>();
        int rows = prof.Count, cols = seg + 1;
        for (int i = 0; i < rows; i++)
            for (int j = 0; j < cols; j++)
            {
                double a = 2 * Math.PI * (j % seg) / seg; float c = (float)Math.Cos(a), s = (float)Math.Sin(a);
                var (r, y, nr, ny) = prof[i];
                float ax = nr * c, ay = ny, az = nr * s;
                P.Add(ox + r * c); P.Add(y); P.Add(r * s);
                A.Add(ax); A.Add(ay); A.Add(az);
                float qx = ax + noise * (float)(rnd.NextDouble() * 2 - 1), qy = ay + noise * (float)(rnd.NextDouble() * 2 - 1), qz = az + noise * (float)(rnd.NextDouble() * 2 - 1);
                float l = MathF.Sqrt(qx * qx + qy * qy + qz * qz); N.Add(qx / l); N.Add(qy / l); N.Add(qz / l);
            }
        for (int i = 0; i + 1 < rows; i++)
            for (int j = 0; j < seg; j++)
            {
                int a = i * cols + j, b = a + 1, c = a + cols, d = c + 1;
                T.AddRange(new[] { a, c, b, b, c, d });
            }
        return (P.ToArray(), N.ToArray(), A.ToArray(), T.ToArray());
    }

    static List<(float, float, float, float)> Sphere(float R, int rings)
    {
        var p = new List<(float, float, float, float)>();
        for (int i = 0; i <= rings; i++) { double t = Math.PI * i / rings; float s = (float)Math.Sin(t), c = (float)-Math.Cos(t); p.Add((R * s, R * c, s, c)); }
        return p;
    }

    static List<(float, float, float, float)> Capsule(float R, float half, int capRings, int bodyRings)
    {
        var p = new List<(float, float, float, float)>();
        for (int i = 0; i <= capRings; i++) { double t = 0.5 * Math.PI * i / capRings; float s = (float)Math.Sin(t), c = (float)-Math.Cos(t); p.Add((R * s, -half + R * c, s, c)); }
        for (int i = 1; i < bodyRings; i++) p.Add((R, -half + 2 * half * i / bodyRings, 1, 0));
        for (int i = 0; i <= capRings; i++) { double t = 0.5 * Math.PI + 0.5 * Math.PI * i / capRings; float s = (float)Math.Sin(t), c = (float)-Math.Cos(t); p.Add((R * s, half + R * c, s, c)); }
        return p;
    }

    [Fact]
    public void NoisySphereSmoothsToItsNormal()
    {
        var (P, N, A, T) = Revolve(Sphere(0.15f, 90), 96, 0.25f, 1);
        var raw = SmoothNormals.AnglesDeg(N, A);
        var d = SmoothNormals.AnglesDeg(SmoothNormals.Smooth(P, N, T, 0.06f), A);
        log.WriteLine($"sphere: raw median {raw[raw.Length / 2]:0.0} max {raw[^1]:0.0}; smoothed median {d[d.Length / 2]:0.00} p99 {d[(int)(d.Length * 0.99)]:0.00} max {d[^1]:0.00} deg");
        Assert.True(raw[raw.Length / 2] > 8f);
        Assert.True(d[^1] < 3f);
    }

    [Fact]
    public void GridMatchesThePairSum()
    {
        var (P, N, A, T) = Revolve(Sphere(0.15f, 40), 48, 0.2f, 7);
        var g = SmoothNormals.Smooth(P, N, T, 0.06f);
        int keep = SmoothNormals.BruteMax; SmoothNormals.BruteMax = 1 << 30;
        try
        {
            var d = SmoothNormals.AnglesDeg(g, SmoothNormals.Smooth(P, N, T, 0.06f));
            log.WriteLine($"grid vs pair sum: median {d[d.Length / 2]:0.00} max {d[^1]:0.00} deg");
            Assert.True(d[^1] < 1f);
        }
        finally { SmoothNormals.BruteMax = keep; }
    }

    [Fact]
    public void NoisyCapsuleSmoothsToItsNormal()
    {
        var (P, N, A, T) = Revolve(Capsule(0.08f, 0.25f, 24, 60), 72, 0.25f, 2);
        var d = SmoothNormals.AnglesDeg(SmoothNormals.Smooth(P, N, T, 0.025f), A);
        log.WriteLine($"capsule r 8 cm, sigma 2.5 cm: smoothed median {d[d.Length / 2]:0.00} p99 {d[(int)(d.Length * 0.99)]:0.00} max {d[^1]:0.00} deg");
        Assert.True(d[(int)(d.Length * 0.9)] < 3f);   // (the worst 10% sit at the caps' seams, where the curvature jumps)
    }

    [Fact]
    public void TouchingSurfacesDoNotBleed()
    {
        // two capsules (thighs) 1 mm apart, one mesh, two connected surfaces: the faces that touch keep their own normals
        var (P1, N1, A1, T1) = Revolve(Capsule(0.07f, 0.2f, 12, 30), 48, 0.0f, 3, -0.0705f);
        var (P2, N2, A2, T2) = Revolve(Capsule(0.07f, 0.2f, 12, 30), 48, 0.0f, 4, 0.0705f);
        int off = P1.Length / 3;
        var P = new float[P1.Length + P2.Length]; P1.CopyTo(P, 0); P2.CopyTo(P, P1.Length);
        var N = new float[P.Length]; N1.CopyTo(N, 0); N2.CopyTo(N, N1.Length);
        var A = new float[P.Length]; A1.CopyTo(A, 0); A2.CopyTo(A, A1.Length);
        var T = new int[T1.Length + T2.Length]; T1.CopyTo(T, 0); for (int i = 0; i < T2.Length; i++) T[T1.Length + i] = T2[i] + off;
        var alone = new float[P.Length]; SmoothNormals.Smooth(P1, N1, T1, 0.06f).CopyTo(alone, 0); SmoothNormals.Smooth(P2, N2, T2, 0.06f).CopyTo(alone, P1.Length);
        var d = SmoothNormals.AnglesDeg(SmoothNormals.Smooth(P, N, T, 0.06f), alone);
        log.WriteLine($"touching capsules vs each alone: median {d[d.Length / 2]:0.00} max {d[^1]:0.00} deg");
        Assert.True(d[^1] < 0.5f);
    }

    [Fact]
    public void SixtyThousandVertsBakeFast()
    {
        var (P, N, A, T) = Revolve(Sphere(0.3f, 240), 249, 0.35f, 5);
        Assert.True(P.Length / 3 >= 60000);
        SmoothNormals.Smooth(P, N, T, 0.06f);   // (warm the JIT)
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var s = SmoothNormals.Smooth(P, N, T, 0.06f);
        double ms = sw.Elapsed.TotalMilliseconds;
        var d = SmoothNormals.AnglesDeg(s, A);
        log.WriteLine($"60k verts ({P.Length / 3}): {ms:0} ms, median {d[d.Length / 2]:0.00} max {d[^1]:0.00} deg");
        Assert.True(ms < 250, $"{ms:0} ms");
    }
}
