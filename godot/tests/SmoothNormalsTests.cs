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

    /// <summary>(BAKE pin) a part under TinyPart sigma across keeps its raw normals exactly (a stitch never flips);
    /// a big part beside it is still smoothed; and the skip rule reads a CEL_HERO_VERTEX statement, never its define.</summary>
    [Fact]
    public void TinyPartsKeepRawNormalsAndTheSkipRuleReadsTheStatement()
    {
        var (P1, N1, _, T1) = Revolve(Sphere(0.008f, 6), 8, 0.6f, 7);          // a 1.6 cm closed bead (diagonal 2.8 cm): under 0.5 x 6 cm
        var (P2, N2, A2, T2) = Revolve(Sphere(0.3f, 40), 48, 0.35f, 8, 1f);    // a big noisy sphere beside it
        var P = new float[P1.Length + P2.Length]; P1.CopyTo(P, 0); P2.CopyTo(P, P1.Length);
        var N = new float[N1.Length + N2.Length]; N1.CopyTo(N, 0); N2.CopyTo(N, N1.Length);
        var T = new int[T1.Length + T2.Length]; T1.CopyTo(T, 0); for (int i = 0; i < T2.Length; i++) T[T1.Length + i] = T2[i] + P1.Length / 3;
        var o = SmoothNormals.Smooth(P, N, T, 0.06f);
        float worst = 0;
        for (int v = 0; v < P1.Length / 3; v++)
        {
            float l = MathF.Sqrt(N1[3 * v] * N1[3 * v] + N1[3 * v + 1] * N1[3 * v + 1] + N1[3 * v + 2] * N1[3 * v + 2]);
            float c = (o[3 * v] * N1[3 * v] + o[3 * v + 1] * N1[3 * v + 1] + o[3 * v + 2] * N1[3 * v + 2]) / l;
            worst = MathF.Max(worst, MathF.Acos(Math.Clamp(c, -1f, 1f)) * 57.29578f);
        }
        var big = new float[P2.Length]; Array.Copy(o, P1.Length, big, 0, P2.Length);
        var d = SmoothNormals.AnglesDeg(big, A2);
        log.WriteLine($"tiny bead vs its raw normals: max {worst:0.000} deg; big sphere vs its true normal: median {d[d.Length / 2]:0.00} max {d[^1]:0.00} deg");
        Assert.True(worst < 0.01f);
        Assert.True(d[d.Length / 2] < 3f);   // (raw noise 0.35: still smoothed)
        Assert.True(SmoothNormals.RunsBake("void vertex() {\n\tCEL_HERO_VERTEX;   // the smoothed normal\n}"));
        Assert.False(SmoothNormals.RunsBake("#define CEL_HERO_VERTEX { NORMAL = NORMAL; }\nvoid vertex() { }"));
        Assert.False(SmoothNormals.RunsBake("shader_type spatial; render_mode unshaded; void fragment() { ALBEDO = vec3(0.0); }"));
    }

    /// <summary>(NORM2B, offline, runs only with SU_SN_DUMP = a folder of HeroNormals' SU_HERO_SN_DUMP files) per dumped mesh:
    /// its bbox, mean edge, connected surfaces, and the new bake and the old diffusion each against the raw normals and
    /// each other; plus the mean angle between welded neighbours (how calm each field is).</summary>
    [Fact]
    public void DumpedMeshes()
    {
        var dir = Environment.GetEnvironmentVariable("SU_SN_DUMP");
        if (string.IsNullOrEmpty(dir) || !System.IO.Directory.Exists(dir)) return;
        bool old = Environment.GetEnvironmentVariable("SU_SN_OLD") == "1";
        var files = System.IO.Directory.GetFiles(dir, "*.bin"); Array.Sort(files);
        var lines = new string[files.Length];
        // (BAKE) the runtime's shape: every mesh but the depth-only twins (HeroNormals' skip rule) on its own task at once
        var mesh = new (float[] P, float[] N, int[] T)[files.Length];
        System.Threading.Tasks.Parallel.For(0, files.Length, fi => { var (P, N, T, _) = Load(files[fi]); mesh[fi] = (P, N, T); });
        var ph = new double[files.Length][];
        for (int rep = 0; rep < 3; rep++)
        {
            var sw0 = System.Diagnostics.Stopwatch.StartNew();
            var jobs = new List<System.Threading.Tasks.Task>();
            for (int fi = 0; fi < files.Length; fi++)
            {
                if (files[fi].Contains("FxAfterHole")) continue;
                int k = fi; ph[k] = new double[4];
                jobs.Add(System.Threading.Tasks.Task.Run(() => SmoothNormals.Smooth(mesh[k].P, mesh[k].N, mesh[k].T, 0.06f, ph[k])));
            }
            System.Threading.Tasks.Task.WaitAll(jobs.ToArray());
            log.WriteLine($"bake wall, all meshes at once (rep {rep}): {sw0.Elapsed.TotalMilliseconds:0} ms");
        }
        for (int fi = 0; fi < files.Length; fi++)
            if (ph[fi] != null && ph[fi][3] > 40) log.WriteLine($"  {System.IO.Path.GetFileName(files[fi])}: weld {ph[fi][0]:0} parts {ph[fi][1]:0} smooth {ph[fi][2]:0} out {ph[fi][3]:0} ms (cumulative)");
        System.Threading.Tasks.Parallel.For(0, files.Length, fi =>
        {
            var (P, N, T) = mesh[fi];
            int n = P.Length / 3;
            float[] lo = { 1e9f, 1e9f, 1e9f }, hi = { -1e9f, -1e9f, -1e9f };
            for (int v = 0; v < n; v++) for (int c = 0; c < 3; c++) { lo[c] = MathF.Min(lo[c], P[3 * v + c]); hi[c] = MathF.Max(hi[c], P[3 * v + c]); }
            double el = 0; for (int t = 0; t < T.Length; t += 3) el += Dist(P, T[t], T[t + 1]);
            el /= Math.Max(1, T.Length / 3);
            var raw = new float[n * 3]; for (int v = 0; v < n; v++) { float l = MathF.Sqrt(N[3 * v] * N[3 * v] + N[3 * v + 1] * N[3 * v + 1] + N[3 * v + 2] * N[3 * v + 2]) + 1e-12f; for (int c = 0; c < 3; c++) raw[3 * v + c] = N[3 * v + c] / l; }
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var nw = SmoothNormals.Smooth(P, N, T, 0.06f); double ms = sw.Elapsed.TotalMilliseconds;
            var a = SmoothNormals.AnglesDeg(nw, raw);
            string s = $"{System.IO.Path.GetFileNameWithoutExtension(files[fi]),-40} {n,7} v  bbox {hi[0] - lo[0]:0.000} {hi[1] - lo[1]:0.000} {hi[2] - lo[2]:0.000}  edge {el * 1000:0.0} mm  {ms,5:0} ms  new|raw {a[n / 2],5:0.0} p90 {a[(int)(n * 0.9)],5:0.0}  calm raw {Calm(raw, T),4:0.0} new {Calm(nw, T),4:0.0}";
            if (old && n < 60000)
            {
                var od = SmoothNormals.Diffuse(P, N, T, 0.06f);
                var b = SmoothNormals.AnglesDeg(od, raw); var c2 = SmoothNormals.AnglesDeg(od, nw);
                s += $"  old|raw {b[n / 2],5:0.0} p90 {b[(int)(n * 0.9)],5:0.0}  old|new {c2[n / 2],5:0.0}  calm old {Calm(od, T),4:0.0}";
            }
            lines[fi] = s;
        });
        foreach (var l in lines) log.WriteLine(l);
    }

    static float Dist(float[] P, int a, int b) { float dx = P[3 * a] - P[3 * b], dy = P[3 * a + 1] - P[3 * b + 1], dz = P[3 * a + 2] - P[3 * b + 2]; return MathF.Sqrt(dx * dx + dy * dy + dz * dz); }

    /// <summary>Mean angle (deg) between the two ends of every triangle edge.</summary>
    static float Calm(float[] Nn, int[] T)
    {
        double s = 0; long k = 0;
        for (int t = 0; t < T.Length; t += 3)
            for (int e = 0; e < 3; e++)
            {
                int a = T[t + e], b = T[t + (e + 1) % 3];
                float c = Nn[3 * a] * Nn[3 * b] + Nn[3 * a + 1] * Nn[3 * b + 1] + Nn[3 * a + 2] * Nn[3 * b + 2];
                s += MathF.Acos(Math.Clamp(c, -1f, 1f)) * 57.29578f; k++;
            }
        return (float)(s / Math.Max(1, k));
    }

    /// <summary>A HeroNormals dump: nv, nt, surfaces, surface bases, pos, nrm, tri.</summary>
    public static (float[] P, float[] N, int[] T, int[] Base) Load(string f)
    {
        using var br = new System.IO.BinaryReader(System.IO.File.OpenRead(f));
        int nv = br.ReadInt32(), nt = br.ReadInt32(), ns = br.ReadInt32();
        var bs = new int[ns]; for (int i = 0; i < ns; i++) bs[i] = br.ReadInt32();
        var P = new float[nv * 3]; for (int i = 0; i < P.Length; i++) P[i] = br.ReadSingle();
        var N = new float[nv * 3]; for (int i = 0; i < N.Length; i++) N[i] = br.ReadSingle();
        var T = new int[nt]; for (int i = 0; i < nt; i++) T[i] = br.ReadInt32();
        return (P, N, T, bs);
    }
}
