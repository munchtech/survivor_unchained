using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>P1 R1 jiggle: B's springs (Play/P1Springs.cs, godot/data/body/springs.json). ModeMatchesData: a breast spring
/// alone on a toy chest, stopped from 1 m/s, rings at its data's damped frequency and decays at its damping ratio.
/// Harness (only where the bake's keys dump is, tools/body/out/clips, git-ignored): B's baked clips with root motion
/// (run and stop, the town idle, sword_heavy, a dash's landing), bare and support 1, per spring: peak offset, main
/// frequency, settle to 10%, and the skinned breast surface's added depth in the upper arms and past her midline;
/// written to tools/body/out/springs_harness.{json,md}.</summary>
public class P1SpringsTests
{
    readonly ITestOutputHelper log;
    public P1SpringsTests(ITestOutputHelper o) { log = o; }

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static JsonElement Doc(string rel) => JsonDocument.Parse(File.ReadAllText(Path.Combine(Root(), rel))).RootElement;

    static P1M4 Tr(double x, double y, double z) { var m = P1M4.Id; m[0, 3] = x; m[1, 3] = y; m[2, 3] = z; return m; }

    [Fact]
    public void ModeMatchesData()
    {
        // toy: root, spine_04 at 1.3 m, breast_l 10 cm left and forward, its tip 6.11 cm along +Z (the data's size_ref)
        var names = new[] { "root", "spine_04", "breast_l", "breast_tip_l" };
        var parent = new[] { -1, 0, 1, 2 };
        var rest = new[] { P1M4.Id, Tr(0, 1.3, 0), Tr(0.1, 1.3, 0.04), Tr(0.1, 1.3, 0.1011) };
        var doc = Doc("data/body/springs.json");
        var sp = new P1Springs(doc, "p1", null, names, parent, rest);
        var top = doc.GetProperty("bodies").GetProperty("p1").GetProperty("support").GetProperty("top");
        double stiffF = top.GetProperty("stiff").GetDouble(), zetaF = top.GetProperty("zeta").GetDouble();
        var b = sp.Springs.First(s => s.Name == "breast_l");
        Assert.Equal(-1, b.Of);
        Assert.Equal(sp.Springs.IndexOf(b), sp.Springs.First(s => s.Name == "breast_tip_l").Of);
        foreach (double sup in new[] { 0.0, 1.0 })
        {
            sp.Support["top"] = sup; sp.Reset();
            double dt = 1 / 120.0, z = 0;
            var xs = new List<double>();
            for (int i = 0; i < 1200; i++)
            {
                if (i >= 120 && i < 132) z += 0.1 * dt;           // a 1 mm nudge forward, then held (small: inside the limits)
                sp.Step(Tr(0, 0, z), rest, dt, collide: false);
                if (i >= 132) xs.Add(b.X.Z - b.Eq.Z);
            }
            var peaks = new List<(int I, double V)>();
            for (int i = 1; i < xs.Count - 1; i++) if (Math.Abs(xs[i]) > Math.Abs(xs[i - 1]) && Math.Abs(xs[i]) >= Math.Abs(xs[i + 1]) && Math.Abs(xs[i]) > 1e-6) peaks.Add((i, Math.Abs(xs[i])));
            Assert.True(peaks.Count >= 4, $"support {sup}: {peaks.Count} swings");
            double halfT = (peaks[3].I - peaks[1].I) / 2.0 * dt;
            double fd = 1 / (2 * halfT);
            double delta = Math.Log(peaks[1].V / peaks[3].V);             // two half swings: one full period
            double zeta = delta / Math.Sqrt(4 * Math.PI * Math.PI + delta * delta);
            double omega = 2 * Math.PI * b.Freq * Math.Sqrt(1 + sup * (stiffF - 1));
            double zWant = b.Zeta * (1 + sup * (zetaF - 1));
            double fWant = omega * Math.Sqrt(1 - zWant * zWant) / (2 * Math.PI);
            log.WriteLine($"support {sup}: damped {fd:F2} Hz (want {fWant:F2}), zeta {zeta:F3} (want {zWant:F3})");
            Assert.InRange(fd, fWant * 0.93, fWant * 1.07);
            Assert.InRange(zeta, zWant * 0.85, zWant * 1.15);
        }
    }

    /// <summary>R2: on the toy chest, a drop (the chest jerked down 6 cm, the mass lags up) and a rise (jerked up): the
    /// up travel from rest stays under the data's up limit and eases in (peaks below the hard stop), the down travel
    /// goes further than the up; the breast's across-axis squashes on the lift and stretches on the drop by up to the
    /// data's squash, volume kept; support 1 squashes less; Frozen holds the mass at rest.</summary>
    [Fact]
    public void TravelSquashFreeze()
    {
        var names = new[] { "root", "spine_04", "breast_l", "breast_tip_l" };
        var parent = new[] { -1, 0, 1, 2 };
        var rest = new[] { P1M4.Id, Tr(0, 1.3, 0), Tr(0.1, 1.3, 0.04), Tr(0.1, 1.3, 0.1011) };
        var doc = Doc("data/body/springs.json");
        var row = doc.GetProperty("bodies").GetProperty("p1").GetProperty("springs")[0];
        double squash = row.GetProperty("squash").GetDouble();
        var sp = new P1Springs(doc, "p1", null, names, parent, rest);
        var b = sp.Springs.First(s => s.Name == "breast_l");
        double dt = 1 / 60.0;
        (double Up, double Down, double SqMin, double SqMax, double Det) Run(double dir, double sup, bool frozen)
        {
            sp.Support["top"] = sup; sp.Frozen = frozen; sp.Reset();
            double y = 0, up = 0, down = 0, qmin = double.MaxValue, qmax = 0, det = 0;
            for (int i = 0; i < 240; i++)
            {
                if (i >= 30 && i < 36) y += dir * 0.01;           // 6 cm in 0.1 s, then held
                sp.Step(Tr(0, y, 0), rest, dt, collide: false);
                if (frozen) Assert.True((b.X - b.Eq).Len() < 1e-9, "frozen: off rest");
                up = Math.Max(up, b.Rel.Y); down = Math.Min(down, b.Rel.Y);
                var lin = b.G.Lin(); double q = lin.Col(2).Len();
                qmin = Math.Min(qmin, q); qmax = Math.Max(qmax, q);
                det = Math.Max(det, Math.Abs(lin.Col(0).Len() * lin.Col(1).Len() * q - 1));
            }
            return (up, down, qmin, qmax, det);
        }
        var drop = Run(-1, 0, false); var rise = Run(1, 0, false);
        double upLim = b.LimE[2];
        log.WriteLine($"bare: up {drop.Up * 1000:F1} mm (limit {upLim * 1000:F1}), down {rise.Down * 1000:F1} mm; across scale {drop.SqMin:F3} .. {rise.SqMax:F3}; volume off {Math.Max(drop.Det, rise.Det):E1}");
        Assert.True(drop.Up > 0.004, "the drop lifts it");
        Assert.True(drop.Up < upLim * 0.97, "up eases in under its limit");
        Assert.True(-rise.Down > drop.Up, "down travels further than up");
        Assert.InRange(drop.SqMin, 1 - squash - 1e-6, 1 - squash * 0.3);   // the lift flattens
        Assert.InRange(rise.SqMax, 1 + squash * 0.3, 1 + squash + 1e-6);   // the drop stretches
        Assert.True(Math.Max(drop.Det, rise.Det) < 1e-6, "volume kept");
        var firm = Run(-1, 1, false);
        log.WriteLine($"support 1: up {firm.Up * 1000:F1} mm, across scale min {firm.SqMin:F3}");
        Assert.True(1 - firm.SqMin < 1 - drop.SqMin, "support 1 squashes less");
        var held = Run(-1, 0, true);
        Assert.True(held.SqMax - held.SqMin < 1e-9, "frozen: the shape as at rest");
    }

    // ------------------------------------------------------------------ the harness on B's baked clips --
    sealed class Clip
    {
        public double Fps, Period; public bool Loop; public double[][][] B = Array.Empty<double[][]>();
        public double[] At(int bone, double t)
        {
            int n = B.Length; double f = t * Fps;
            int keys = Loop ? n - 1 : n;
            if (!Loop) f = Math.Clamp(f, 0, n - 1);
            int i = (int)Math.Floor(f); double u = f - i;
            double[] K(int k) => B[Loop ? ((k % keys) + keys) % keys : Math.Clamp(k, 0, n - 1)][bone];
            var p0 = K(i - 1); var p1 = K(i); var p2 = K(i + 1); var p3 = K(i + 2);
            var o = new double[12];
            for (int c = 0; c < 12; c++)
                o[c] = 0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * u + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * u * u + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * u * u * u);
            return o;
        }
    }

    static Clip LoadClip(string dir, string name)
    {
        var d = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, name + ".json"))).RootElement;
        var c = new Clip { Fps = d.GetProperty("fps").GetDouble(), Loop = d.GetProperty("loop").GetBoolean() };
        c.B = d.GetProperty("B").EnumerateArray().Select(f => f.EnumerateArray().Select(b => b.EnumerateArray().Select(x => x.GetDouble()).ToArray()).ToArray()).ToArray();
        c.Period = (c.B.Length - (c.Loop ? 1 : 0)) / c.Fps;
        return c;
    }

    static P1M4 M12(double[] a)
    {
        var m = P1M4.FromRows(a.Concat(new double[] { 0, 0, 0, 1 }).ToArray());
        return P1M4.From(P1Springs.Ortho(m.Lin()), m.T());
    }

    /// <summary>A timeline: clips in turn (each from its own time 0, the last held), crossfaded; the root's forward speed.</summary>
    sealed record Seg(string Clip, double Start, double Fade);
    sealed record Scenario(string Name, Seg[] Segs, Func<double, double> Speed, double Length, double PeakFrom, double PeakTo, double SettleFrom, string RefClip, double RefStart);

    [Fact]
    public void Harness()
    {
        string dir = Path.Combine(Root(), "..", "tools", "body", "out", "clips");
        if (!File.Exists(Path.Combine(dir, "run_warden.json"))) { log.WriteLine("no keys dump (tools/body/out/clips): harness skipped"); return; }
        var clips = new Dictionary<string, Clip>();
        Clip C(string n) => clips.TryGetValue(n, out var c) ? c : clips[n] = LoadClip(dir, n);
        var d0 = JsonDocument.Parse(File.ReadAllText(Path.Combine(dir, "run_warden.json"))).RootElement;
        var names = d0.GetProperty("b_names").EnumerateArray().Select(x => x.GetString()!).ToArray();
        var parent = d0.GetProperty("b_parent").EnumerateArray().Select(x => x.GetInt32()).ToArray();
        var rest = d0.GetProperty("b_rest").EnumerateArray().Select(r => M12(r.EnumerateArray().Select(x => x.GetDouble()).ToArray())).ToArray();
        var springsDoc = Environment.GetEnvironmentVariable("P1_SPRINGS_JSON") is string alt && alt != "" ? JsonDocument.Parse(File.ReadAllText(alt)).RootElement : Doc("data/body/springs.json");   // (P1_SPRINGS_JSON: a table to try)
        var samplesDoc = Doc("data/body/p1_spring_samples.json");
        double heavy = C("sword_heavy").Period;
        const double run = 5, dashV = 5.5 / 0.2;   // archetypes moveSpeed 5; Abilities.Dash 5.5 m in 0.2 s
        var scen = new[]
        {
            new Scenario("run+stop", new[] { new Seg("idle_warden_town", 0, 0), new Seg("run_warden", 1.5, 0.2), new Seg("idle_warden", 4.6, 0.2) },
                t => t < 1.5 ? 0 : t < 1.75 ? run * (t - 1.5) / 0.25 : t < 4.5 ? run : t < 4.7 ? run * (4.7 - t) / 0.2 : 0, 8, 2.75, 4.5, 4.7, "idle_warden", 4.6),   // (peak: the steady run, after the start has settled)
            new Scenario("town idle", new[] { new Seg("idle_warden_town", 0, 0) }, _ => 0, 8, 1.0, 8, -1, "", 0),
            new Scenario("sword_heavy", new[] { new Seg("idle_warden", 0, 0), new Seg("sword_heavy", 1.5, 0.12), new Seg("idle_warden", 1.5 + heavy, 0.2) },
                _ => 0, 1.5 + heavy + 3.5, 1.5, 1.5 + heavy, 1.5 + heavy, "idle_warden", 1.5 + heavy),
            new Scenario("dash landing", new[] { new Seg("idle_warden", 0, 0), new Seg("run_warden", 1.0, 0.2), new Seg("idle_warden", 2.75, 0.15) },
                t => t < 1.0 ? 0 : t < 1.25 ? run * (t - 1.0) / 0.25 : t < 2.5 ? run : t < 2.53 ? run + (dashV - run) * (t - 2.5) / 0.03 : t < 2.7 ? dashV : t < 2.75 ? dashV * (2.75 - t) / 0.05 : 0,
                6.5, 2.5, 3.0, 2.75, "idle_warden", 2.75),
        };
        const double dt = 1 / 60.0;
        var rows = new List<Dictionary<string, object>>();
        var md = new StringBuilder();
        md.AppendLine("| scenario | support | spring | peak mm | at reach % | main Hz | settle s | arm pen mm | mid pen mm |");
        md.AppendLine("|---|---|---|---|---|---|---|---|---|");
        foreach (var sc in scen)
            foreach (double sup in new[] { 0.0, 1.0 })
            {
                var main = new P1Springs(springsDoc, "p1", samplesDoc, names, parent, rest);
                var refS = new P1Springs(springsDoc, "p1", samplesDoc, names, parent, rest);
                main.Support["top"] = refS.Support["top"] = sup;
                int nS = main.Springs.Count;
                var off = main.Springs.Select(_ => new List<P1V>()).ToArray();
                var atLim = new int[nS];
                var dif = main.Springs.Select(_ => new List<(double T, P1V D)>()).ToArray();
                var armPen = new double[2]; var midPen = new double[2]; double armBase = 0;
                double z = 0;
                int steps = (int)Math.Round(sc.Length / dt);
                for (int k = 0; k <= steps; k++)
                {
                    double t = k * dt;
                    z += sc.Speed(t) * dt;
                    var G = Pose(sc, t, C, names.Length);
                    main.Step(Tr(0, 0, z), G, k == 0 ? 0 : dt);
                    bool hasRef = sc.RefClip != "";
                    if (hasRef)
                    {
                        var c = C(sc.RefClip); var Gr = new P1M4[names.Length];
                        for (int j = 0; j < names.Length; j++) Gr[j] = M12(c.At(j, t - sc.RefStart));
                        refS.Step(P1M4.Id, Gr, k == 0 ? 0 : dt);
                    }
                    for (int i = 0; i < nS; i++)
                    {
                        var s = main.Springs[i];
                        if (t >= sc.PeakFrom && t <= sc.PeakTo) { off[i].Add(s.X - s.Eq); if (s.X.Len() >= 0.97 * s.ReachE) atLim[i]++; }
                        if (hasRef && t >= sc.SettleFrom) dif[i].Add((t - sc.SettleFrom, s.X - refS.Springs[i].X));
                    }
                    if (k % 2 == 0)
                        foreach (var (side, si) in new[] { (1.0, 0), (-1.0, 1) })
                        {
                            var pts = main.Skin(side, G, true); var bas = main.Skin(side, G, false);
                            var br = main.Springs.First(s => s.Collide && s.Side == side);
                            for (int i = 0; i < pts.Length; i++)
                            {
                                foreach (double a in main.Arms)
                                {
                                    double db = main.ArmDepth(bas[i], a, G, out _);
                                    armBase = Math.Max(armBase, db);
                                    armPen[si] = Math.Max(armPen[si], main.ArmDepth(pts[i], a, G, out _) - Math.Max(db, 0));
                                }
                                double mb = main.MidDepth(bas[i], side, G[br.Parent], br.Parent);
                                midPen[si] = Math.Max(midPen[si], main.MidDepth(pts[i], side, G[br.Parent], br.Parent) - Math.Max(mb, 0));
                            }
                        }
                }
                for (int i = 0; i < nS; i++)
                {
                    var s = main.Springs[i];
                    double peak = off[i].Count > 0 ? off[i].Max(v => v.Len()) : 0;
                    if (sc.SettleFrom < 0)
                    {
                        // the idle: its swing about its mean
                        var mean = off[i].Aggregate(new P1V(0, 0, 0), (a, v) => a + v) / Math.Max(off[i].Count, 1);
                        peak = off[i].Max(v => (v - mean).Len());
                    }
                    var (hz, settle) = Decay(dif[i], dt);
                    int side = s.Side > 0 ? 0 : 1;
                    bool br = s.Collide;
                    rows.Add(new() { ["scenario"] = sc.Name, ["support"] = sup, ["spring"] = s.Name, ["peak_mm"] = Math.Round(peak * 1000, 1),
                        ["hz"] = Math.Round(hz, 2), ["at_reach_pct"] = Math.Round(100.0 * atLim[i] / Math.Max(off[i].Count, 1), 1), ["settle_s"] = Math.Round(settle, 2),
                        ["arm_pen_mm"] = br ? Math.Round(armPen[side] * 1000, 2) : 0, ["mid_pen_mm"] = br ? Math.Round(midPen[side] * 1000, 2) : 0 });
                    md.AppendLine($"| {sc.Name} | {sup} | {s.Name} | {peak * 1000:F1} | {100.0 * atLim[i] / Math.Max(off[i].Count, 1):F0} | {(hz > 0 ? hz.ToString("F2") : "-")} | {(settle >= 0 ? settle.ToString("F2") : "-")} | {(br ? (armPen[side] * 1000).ToString("F2") : "")} | {(br ? (midPen[side] * 1000).ToString("F2") : "")} |");
                }
                md.AppendLine($"|  |  | (clip's own arm depth into the breast samples, max) | {armBase * 1000:F1} mm | | | | | |");
            }
        string outDir = Path.Combine(Root(), "..", "tools", "body", "out");
        File.WriteAllText(Path.Combine(outDir, "springs_harness.json"), JsonSerializer.Serialize(rows, new JsonSerializerOptions { WriteIndented = true }));
        File.WriteAllText(Path.Combine(outDir, "springs_harness.md"), md.ToString());
        log.WriteLine(md.ToString());
    }

    static P1M4[] Pose(Scenario sc, double t, Func<string, Clip> C, int n)
    {
        int cur = 0;
        for (int i = 0; i < sc.Segs.Length; i++) if (t >= sc.Segs[i].Start) cur = i;
        var s = sc.Segs[cur]; var c = C(s.Clip);
        var G = new P1M4[n];
        double w = s.Fade > 0 && cur > 0 ? Math.Clamp((t - s.Start) / s.Fade, 0, 1) : 1;
        w = w * w * (3 - 2 * w);
        Clip? pc = w < 1 ? C(sc.Segs[cur - 1].Clip) : null;
        double pt = cur > 0 ? t - sc.Segs[cur - 1].Start : 0;
        for (int j = 0; j < n; j++)
        {
            var a = c.At(j, t - s.Start);
            if (pc != null) { var b = pc.At(j, pt); for (int k = 0; k < 12; k++) a[k] = b[k] + (a[k] - b[k]) * w; }
            G[j] = M12(a);
        }
        return G;
    }

    /// <summary>The free decay after the stop: its main frequency (zero crossings of its main axis while above 10% of its
    /// peak) and the time it last exceeds 10% of its peak.</summary>
    static (double Hz, double Settle) Decay(List<(double T, P1V D)> d, double dt)
    {
        if (d.Count < 10) return (0, -1);
        double peak = d.Max(x => x.D.Len());
        if (peak < 1e-5) return (0, 0);
        double settle = d.Where(x => x.D.Len() > 0.1 * peak).Select(x => x.T).DefaultIfEmpty(0).Max();
        // main axis: the direction of the largest excursion
        var ax = d.OrderByDescending(x => x.D.Len()).First().D; ax /= ax.Len();
        var cross = new List<double>();
        for (int i = 1; i < d.Count; i++)
        {
            double a = P1V.Dot(d[i - 1].D, ax), b = P1V.Dot(d[i].D, ax);
            if (a * b < 0 && d[i].T <= settle + 0.2) cross.Add(d[i - 1].T + dt * a / (a - b));
        }
        double hz = cross.Count >= 3 ? (cross.Count - 1) / (2 * (cross[^1] - cross[0])) : 0;
        return (hz, settle);
    }
}
