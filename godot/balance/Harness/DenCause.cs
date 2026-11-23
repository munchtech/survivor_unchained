using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>(P3 first-blow item, measuring only) Why less than half a den pack stands inside her first Leap or Bladestorm
/// (DEN_ROSTER.md line 78): each pack's melee members' spread at the wake, at first contact and at that first blow, how long
/// they take to come in, where a leap lands against the pack, and each kind's run-in speed. Fed by DenFeel's tap.</summary>
public static class DenCause
{
    /// <summary>The live melee members at one moment: their spread about their own middle (mean and farthest), their length
    /// along the line from their middle to her and their width across it, her distance to their middle, nearest and farthest,
    /// and the most of them one AreaR circle could hold wherever it were put.</summary>
    public struct Geo { public bool Set; public double T, RMax, RMean, Len, Wid, ToMid, ToFront, ToBack, Best; public int N; }

    public sealed class Row
    {
        public Geo Wake, Contact, Blow;
        /// <summary>At the wake: the farthest melee member from the pack's home, and the melee members then live.</summary>
        public double HomeMax = -1; public int Base;
        public readonly Dictionary<Enemy, (double X, double Z, double Path, double D0, double T0)> Track = new();
        /// <summary>Each member's first step inside AreaR of her: seconds after the wake, its closing speed and its ground speed.</summary>
        public readonly List<(string Def, double At, double Close, double Ground)> Arrived = new();
        public double PeakBest = -1, PeakBestAt = -1;
        /// <summary>Her last takeoff: where she left, where she aimed, and the pack's middle then.</summary>
        public (double X0, double Z0, double X1, double Z1, double MidX, double MidZ)? Takeoff;
        /// <summary>A first area blow that was a leap: the aim's distance from the pack's middle at takeoff, how far that middle
        /// moved while she was in the air, and the landing against the middle and the front along her line (+ = past it).</summary>
        public bool Leap; public double AimOff, MidMoved, PastMid, PastFront;
        /// <summary>Her first landing after the wake, whether or not it caught any of the pack: the share of its live melee members
        /// inside AreaR of it (0: none), the nearest member's edge distance, the aim's distance from the pack's middle at takeoff,
        /// how far the middle moved in the air, and the leap's length.</summary>
        public double Land1 = -1, Land1Near, Land1Aim, Land1Moved, Land1Len, Land1Off;
    }

    static double D(double x, double z, double x1, double z1) => Math.Sqrt((x - x1) * (x - x1) + (z - z1) * (z - z1));

    public static Geo Snap(double t, List<Enemy> m, double px, double pz)
    {
        var g = new Geo { Set = true, T = t, N = m.Count };
        double cx = m.Average(e => e.X), cz = m.Average(e => e.Z);
        g.RMax = m.Max(e => D(e.X, e.Z, cx, cz)); g.RMean = m.Average(e => D(e.X, e.Z, cx, cz));
        g.ToMid = D(px, pz, cx, cz);
        double ux = (px - cx) / Math.Max(1e-6, g.ToMid), uz = (pz - cz) / Math.Max(1e-6, g.ToMid);
        var s = m.Select(e => (e.X - cx) * ux + (e.Z - cz) * uz).ToList();
        var w = m.Select(e => -(e.X - cx) * uz + (e.Z - cz) * ux).ToList();
        g.Len = s.Max() - s.Min(); g.Wid = w.Max() - w.Min();
        g.ToFront = m.Min(e => D(e.X, e.Z, px, pz) - e.Radius); g.ToBack = m.Max(e => D(e.X, e.Z, px, pz) - e.Radius);
        g.Best = BestCircle(m);
        return g;
    }

    /// <summary>The most of them one AreaR circle could hold (centres tried: each member, each pair's middle, the middle of all).</summary>
    public static double BestCircle(List<Enemy> m)
    {
        var cs = new List<(double X, double Z)> { (m.Average(e => e.X), m.Average(e => e.Z)) };
        for (int i = 0; i < m.Count; i++) { cs.Add((m[i].X, m[i].Z)); for (int j = i + 1; j < m.Count; j++) cs.Add(((m[i].X + m[j].X) / 2, (m[i].Z + m[j].Z) / 2)); }
        int best = 0;
        foreach (var c in cs) best = Math.Max(best, m.Count(e => D(e.X, e.Z, c.X, c.Z) < DenFeel.AreaR + e.Radius));
        return (double)best / m.Count;
    }

    /// <summary>One step of a woken pack with a live melee member.</summary>
    public static void Step(Row r, double t, double woke, List<Enemy> melee, PlayerState p, IReadOnlyList<CombatEvent> evs, bool anyDeath, List<Enemy>? fell = null)
    {
        if (!r.Wake.Set)
        {
            r.Wake = Snap(t, melee, p.X, p.Z); r.Base = melee.Count;
            r.HomeMax = melee.Max(e => D(e.X, e.Z, e.HomeX, e.HomeZ));
            foreach (var e in melee) r.Track[e] = (e.X, e.Z, 0, D(e.X, e.Z, p.X, p.Z), t);
        }
        bool touch = false;
        foreach (var e in melee)
        {
            double d = D(e.X, e.Z, p.X, p.Z);
            if (d < DenFeel.AreaR + e.Radius) touch = true;
            if (!r.Track.TryGetValue(e, out var k)) continue;
            double path = k.Path + D(e.X, e.Z, k.X, k.Z);
            if (d < DenFeel.AreaR + e.Radius)
            {
                double dt = Math.Max(1 / 60.0, t - k.T0);
                r.Arrived.Add((e.Def.Id, t - woke, (k.D0 - d) / dt, path / dt));
                r.Track.Remove(e);
            }
            else r.Track[e] = (e.X, e.Z, path, k.D0, k.T0);
        }
        if (touch && !r.Contact.Set) r.Contact = Snap(t, melee, p.X, p.Z);
        if (!anyDeath)
        {
            double best = BestCircle(melee);
            if (best > r.PeakBest) { r.PeakBest = best; r.PeakBestAt = t - woke; }
        }
        foreach (var ev in evs)
            if (ev is Ev.Leap { Phase: LeapPhase.Land } ld && r.Takeoff is { } tk && r.Land1 < 0)
            {
                // The pack as it stood when she landed: the members the landing felled are counted.
                var at = fell == null || fell.Count == 0 ? melee : melee.Concat(fell).ToList();
                r.Land1 = (double)at.Count(e => D(e.X, e.Z, ld.X1, ld.Z1) < DenFeel.AreaR + e.Radius) / at.Count;
                r.Land1Near = at.Min(e => D(e.X, e.Z, ld.X1, ld.Z1) - e.Radius);
                r.Land1Off = D(ld.X1, ld.Z1, at.Average(e => e.X), at.Average(e => e.Z));
                r.Land1Aim = D(ld.X1, ld.Z1, tk.MidX, tk.MidZ);
                r.Land1Moved = D(melee.Average(e => e.X), melee.Average(e => e.Z), tk.MidX, tk.MidZ);
                r.Land1Len = D(ld.X0, ld.Z0, ld.X1, ld.Z1);
            }
        foreach (var ev in evs)
            if (ev is Ev.Leap { Phase: LeapPhase.Takeoff } lp)
                r.Takeoff = (lp.X0, lp.Z0, lp.X1, lp.Z1, melee.Average(e => e.X), melee.Average(e => e.Z));
    }

    /// <summary>The first area blow that reached the pack: centred at (x, z), a leap's landing ('L') or a spin's start ('S').</summary>
    public static void AtBlow(Row r, double t, List<Enemy> melee, double x, double z, char kind)
    {
        r.Blow = Snap(t, melee, x, z);
        if (kind != 'L' || r.Takeoff is not { } tk) return;
        r.Leap = true;
        double cx = melee.Average(e => e.X), cz = melee.Average(e => e.Z);
        r.AimOff = D(tk.X1, tk.Z1, tk.MidX, tk.MidZ);
        r.MidMoved = D(cx, cz, tk.MidX, tk.MidZ);
        double run = Math.Max(1e-6, D(cx, cz, tk.X0, tk.Z0)), ux = (cx - tk.X0) / run, uz = (cz - tk.Z0) / run;
        double land = (x - tk.X0) * ux + (z - tk.Z0) * uz;
        r.PastMid = land - run;
        r.PastFront = land - melee.Min(e => (e.X - tk.X0) * ux + (e.Z - tk.Z0) * uz);
    }

    static double Q(IEnumerable<double> xs, double q)
    {
        var a = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        if (a.Count == 0) return double.NaN;
        return a[Math.Clamp((int)Math.Round(q * (a.Count - 1)), 0, a.Count - 1)];
    }
    static string Q3(IEnumerable<double> xs) { var a = xs.ToList(); return $"{Q(a, .25):0.0}/{Q(a, .5):0.0}/{Q(a, .75):0.0}"; }
    static string Pct(IEnumerable<bool> xs) { var a = xs.ToList(); return a.Count == 0 ? "-" : $"{100.0 * a.Count(x => x) / a.Count:0}%"; }

    public static string Report(IReadOnlyList<DenFeel.Run> runs)
    {
        var sb = new StringBuilder();
        sb.AppendLine();
        sb.AppendLine("## Cause table: the pack's melee members (metres; p25/p50/p75 where three are given)");
        // Each bot's packs; and for the opener variant, only the packs it opened, by the opener's kind.
        var groups = new List<(string Key, List<DenFeel.PackRow> Packs)>();
        foreach (var g0 in runs.GroupBy(r => r.Label).OrderBy(g => g.Key))
        {
            var all = g0.SelectMany(r => r.Packs).Where(p => p.C.Wake.Set).ToList();
            groups.Add((g0.Key, all));
            if (!g0.Key.EndsWith("+open") && !g0.Key.EndsWith("+lead")) continue;
            groups.Add((g0.Key + ", opened with Leap", all.Where(p => p.Opener == 'L' && (p.Inside >= 0 || p.InsideAll >= 0 || p.C.Land1 >= 0)).ToList()));
            groups.Add((g0.Key + ", opened with Bladestorm", all.Where(p => p.Opener == 'S' && (p.Inside >= 0 || p.InsideAll >= 0)).ToList()));
        }
        foreach (var g in groups)
        {
            var ps = g.Packs;
            sb.AppendLine();
            sb.AppendLine($"### {g.Key} ({ps.Count} packs; inside the first area blow p50 {Q(ps.Where(p => p.Inside >= 0).Select(p => p.Inside), .5):0.00}, packs >=50%: {Pct(ps.Where(p => p.Inside >= 0).Select(p => p.Inside >= 0.5))})");
            sb.AppendLine("| moment | packs | s after wake p50 | melee live p50 | mean dist from own middle | farthest from own middle | length along her line | width across it | her to middle | her to nearest | her to farthest | best 3.5 m circle anywhere p50 (packs >=50%) |");
            sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|");
            void line(string name, Func<DenFeel.PackRow, Geo> f)
            {
                var gs = ps.Select(p => (P: p, G: f(p))).Where(x => x.G.Set).ToList();
                sb.AppendLine($"| {name} | {gs.Count} | {Q(gs.Select(x => x.G.T - x.P.Woke), .5):0.0} | {Q(gs.Select(x => (double)x.G.N), .5):0} | {Q(gs.Select(x => x.G.RMean), .5):0.0} | {Q3(gs.Select(x => x.G.RMax))} | {Q3(gs.Select(x => x.G.Len))} | {Q(gs.Select(x => x.G.Wid), .5):0.0} | {Q(gs.Select(x => x.G.ToMid), .5):0.0} | {Q(gs.Select(x => x.G.ToFront), .5):0.0} | {Q(gs.Select(x => x.G.ToBack), .5):0.0} | {Q(gs.Select(x => x.G.Best), .5):0.00} ({Pct(gs.Select(x => x.G.Best >= 0.5))}) |");
            }
            line("wake", p => p.C.Wake);
            line("first contact (one inside 3.5 m of her)", p => p.C.Contact);
            line("first area blow (centre = the blow)", p => p.C.Blow);
            line("- if a leap's landing", p => p.FirstKind == 'L' ? p.C.Blow : default);
            line("- if a spin's start", p => p.FirstKind == 'S' ? p.C.Blow : default);
            sb.AppendLine();
            sb.AppendLine($"At the wake, the farthest melee member from the pack's home: {Q3(ps.Select(p => p.C.HomeMax))} m.");
            // Arrivals: members inside 3.5 m of her, in seconds after the wake.
            var arr = ps.Where(p => p.C.Arrived.Count > 0).Select(p => (P: p, A: p.C.Arrived.Select(a => a.At).OrderBy(a => a).ToList())).ToList();
            var half = arr.Where(x => x.A.Count >= (x.P.C.Base + 1) / 2).Select(x => x.A[(x.P.C.Base + 1) / 2 - 1] - x.A[0]).ToList();
            sb.AppendLine($"Coming in (inside 3.5 m of her): first member {Q3(arr.Select(x => x.A[0]))} s after the wake; first to half the pack {Q3(half)} s ({half.Count} packs where half came in); first to last of those that came in {Q3(arr.Select(x => x.A[^1] - x.A[0]))} s; share of the pack that never came in before it died or the pack ended p50 {Q(arr.Select(x => 1 - (double)x.A.Count / Math.Max(1, x.P.C.Base)), .5):0.00}.");
            var fd = ps.Where(p => p.Deaths.Count > 0).ToList();
            sb.AppendLine($"First death: {Q3(fd.Select(p => p.Deaths.Min() - p.Woke))} s after the wake; {Q3(fd.Where(p => p.C.Contact.Set).Select(p => p.Deaths.Min() - p.C.Contact.T))} s after first contact.");
            sb.AppendLine($"Best 3.5 m circle anywhere, at its peak before the first death: p50 {Q(ps.Select(p => p.C.PeakBest), .5):0.00} (packs >=50%: {Pct(ps.Select(p => p.C.PeakBest >= 0.5))}), {Q3(ps.Select(p => p.C.PeakBestAt))} s after the wake.");
            var lp = ps.Where(p => p.C.Leap).ToList();
            sb.AppendLine($"Leap as the first area blow ({lp.Count}): aim to the pack's middle at takeoff {Q3(lp.Select(p => p.C.AimOff))} m; the middle moved while she was in the air {Q3(lp.Select(p => p.C.MidMoved))} m; landing past the middle along her line {Q3(lp.Select(p => p.C.PastMid))} m (minus = short of it); landing past the front {Q3(lp.Select(p => p.C.PastFront))} m; landed beyond the front by more than 3.5 m in {Pct(lp.Select(p => p.C.PastFront > DenFeel.AreaR))}.");
            var l1 = ps.Where(p => p.C.Land1 >= 0 && (!g.Key.Contains("opened with") || p.Opener == 'L')).ToList();
            sb.AppendLine($"Her first landing after the wake, a miss counted as 0, the felled counted ({l1.Count}): share inside {Q3(l1.Select(p => p.C.Land1))} (as .0: {Q(l1.Select(p => p.C.Land1), .25):0.00}/{Q(l1.Select(p => p.C.Land1), .5):0.00}/{Q(l1.Select(p => p.C.Land1), .75):0.00}), packs >=50%: {Pct(l1.Select(p => p.C.Land1 >= 0.5))}, caught none: {Pct(l1.Select(p => p.C.Land1 == 0))}; nearest member to the landing {Q3(l1.Select(p => p.C.Land1Near))} m; landing off the middle at takeoff {Q3(l1.Select(p => p.C.Land1Aim))} m; middle moved in the air {Q3(l1.Select(p => p.C.Land1Moved))} m; leap length {Q3(l1.Select(p => p.C.Land1Len))} m; landing off the pack's middle as she lands {Q3(l1.Select(p => p.C.Land1Off))} m.");
            sb.AppendLine("Run-in by kind (wake to inside 3.5 m of her): | kind | n | came in, s after wake p25/p50/p75 | closing speed m/s p50 | ground speed m/s p50 |");
            foreach (var k in ps.SelectMany(p => p.C.Arrived).GroupBy(a => a.Def).OrderBy(k => k.Key))
                sb.AppendLine($"| {k.Key} | {k.Count()} | {Q3(k.Select(a => a.At))} | {Q(k.Select(a => a.Close), .5):0.0} | {Q(k.Select(a => a.Ground), .5):0.0} |");
            sb.AppendLine("By recipe (normal packs): | recipe | packs | wake: farthest from middle p50 | wake: length p50 | wake best circle p50 | contact best circle p50 | blow best circle p50 | inside first blow p50 | first to half s p50 |");
            foreach (var rg in ps.Where(p => p.Grade == 0).GroupBy(p => p.Recipe).OrderBy(x => x.Key))
            {
                var hf = rg.Where(p => p.C.Arrived.Count >= (p.C.Base + 1) / 2 && p.C.Arrived.Count > 0).Select(p => { var a = p.C.Arrived.Select(x => x.At).OrderBy(x => x).ToList(); return a[(p.C.Base + 1) / 2 - 1] - a[0]; });
                sb.AppendLine($"| {rg.Key} | {rg.Count()} | {Q(rg.Select(p => p.C.Wake.RMax), .5):0.0} | {Q(rg.Select(p => p.C.Wake.Len), .5):0.0} | {Q(rg.Select(p => p.C.Wake.Best), .5):0.00} | {Q(rg.Where(p => p.C.Contact.Set).Select(p => p.C.Contact.Best), .5):0.00} | {Q(rg.Where(p => p.C.Blow.Set).Select(p => p.C.Blow.Best), .5):0.00} | {Q(rg.Where(p => p.Inside >= 0).Select(p => p.Inside), .5):0.00} | {Q(hf, .5):0.0} |");
            }
        }
        return sb.ToString();
    }
}
