using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;

namespace SurvivorUnchained.Balance;

/// <summary>The harness's runs as tables (markdown, for the design doc and
/// the console).</summary>
public static class Report
{
    static string F(double v, string f = "0.0") => double.IsNaN(v) ? "–" : v.ToString(f, CultureInfo.InvariantCulture);
    static string Pct(double v) => double.IsNaN(v) ? "–" : $"{v * 100:0}%";

    public static double Median(IEnumerable<double> xs)
    {
        var s = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s.Count % 2 == 1 ? s[s.Count / 2] : (s[s.Count / 2 - 1] + s[s.Count / 2]) / 2;
    }

    static double Rate(IEnumerable<RunResult> rs, Func<RunResult, bool> f)
    {
        var l = rs.ToList();
        return l.Count == 0 ? double.NaN : l.Count(f) / (double)l.Count;
    }

    static double At(RunResult r, int minute, Func<Minute, double> f) => r.ByMinute.Count >= minute ? f(r.ByMinute[minute - 1]) : double.NaN;

    static void Row(StringBuilder sb, params object[] cells) => sb.AppendLine("| " + string.Join(" | ", cells) + " |");

    static void Head(StringBuilder sb, params string[] cells)
    {
        Row(sb, cells);
        sb.AppendLine("|" + string.Concat(cells.Select(_ => "---|")));
    }

    static void Summary(StringBuilder sb, string label, IEnumerable<IGrouping<string, RunResult>> groups)
    {
        Head(sb, label, "runs", "won", "fell", "lived (min)", "ember 15", "ember 30", "boss TTK (s)", "herald TTK (s)", "fodder TTK 5/15/25 (s)", "dmg/min 25", "cards/min", "advancing", "complete at");
        foreach (var g in groups.OrderBy(g => g.Key))
        {
            var l = g.ToList();
            Row(sb, g.Key, l.Count, Pct(Rate(l, r => r.Won)), Pct(Rate(l, r => r.Died)), F(Median(l.Select(r => r.Minutes))),
                F(Median(l.Select(r => At(r, 15, m => m.Ember))), "0"), F(Median(l.Select(r => At(r, 30, m => m.Ember))), "0"),
                F(Median(l.Where(r => r.BossTtk != null).Select(r => r.BossTtk!.Value))), F(Median(l.SelectMany(r => r.HeraldTtk))),
                $"{F(Median(l.Select(r => At(r, 5, m => m.TtkFodder))), "0.00")} / {F(Median(l.Select(r => At(r, 15, m => m.TtkFodder))), "0.00")} / {F(Median(l.Select(r => At(r, 25, m => m.TtkFodder))), "0.00")}",
                F(Median(l.Select(r => At(r, 25, m => m.Damage))) / 1000, "0") + "k",
                F(Median(l.Select(r => r.Cards / Math.Max(1, r.Minutes)))), Pct(l.Sum(r => r.Advancing) / (double)Math.Max(1, l.Sum(r => r.NormalDrafts))),
                F(Median(l.Select(r => r.CompleteAt ?? double.NaN))));
        }
        sb.AppendLine();
    }

    public static string Arena(List<RunResult> runs)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"## Arenas: {runs.Count} runs\n");
        Summary(sb, "policy", runs.GroupBy(r => r.Spec.Policy));
        Summary(sb, "calling", runs.GroupBy(r => r.Spec.Calling));
        Summary(sb, "people", runs.GroupBy(r => r.Spec.People));
        if (runs.Select(r => r.Spec.Policy).Distinct().Count() > 1 && runs.Select(r => r.Spec.Calling).Distinct().Count() > 1)
            Summary(sb, "calling · policy", runs.GroupBy(r => $"{r.Spec.Calling} · {r.Spec.Policy}"));

        // The power curve, minute by minute.
        sb.AppendLine("### Over the minutes (medians)\n");
        Head(sb, "minute", "ember", "dmg/min", "kills/min", "alive", "fodder TTK (s)", "fodder TTK p90 (s)", "elite TTK (s)", "lowest health", "still standing");
        foreach (int m in new[] { 1, 2, 3, 5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 32, 35 })
        {
            var at = runs.Where(r => r.ByMinute.Count >= m).ToList();
            if (at.Count == 0) continue;
            Row(sb, m, F(Median(at.Select(r => (double)r.ByMinute[m - 1].Ember)), "0"), F(Median(at.Select(r => r.ByMinute[m - 1].Damage)) / 1000, "0.0") + "k",
                F(Median(at.Select(r => (double)r.ByMinute[m - 1].Kills)), "0"), F(Median(at.Select(r => (double)r.ByMinute[m - 1].Alive)), "0"),
                F(Median(at.Select(r => r.ByMinute[m - 1].TtkFodder)), "0.00"), F(Median(at.Select(r => r.ByMinute[m - 1].TtkFodder90)), "0.00"),
                F(Median(at.Select(r => r.ByMinute[m - 1].TtkElite)), "0.0"),
                Pct(Median(at.Select(r => r.ByMinute[m - 1].LowHp))), Pct(at.Count / (double)runs.Count));
        }
        sb.AppendLine();

        // Every card: how often offered, taken, and how runs that took it went.
        sb.AppendLine("### Cards (offered, taken, and the win rate of the runs that took one)\n");
        Head(sb, "card", "offered", "taken", "pick", "won taking", "won not", "delta", "lived taking (min)");
        var keys = runs.SelectMany(r => r.Offered.Keys.Concat(r.Taken.Keys)).Distinct().Where(k => !k.StartsWith("r:") && k is not ("heal" or "gold")).ToList();
        var rowsOut = new List<(string Key, double Delta, string[] Cells)>();
        foreach (var k in keys)
        {
            int offered = runs.Sum(r => r.Offered.GetValueOrDefault(k)), taken = runs.Sum(r => r.Taken.GetValueOrDefault(k));
            var took = runs.Where(r => r.Taken.ContainsKey(k)).ToList();
            var not = runs.Where(r => !r.Taken.ContainsKey(k)).ToList();
            double wt = Rate(took, r => r.Won), wn = Rate(not, r => r.Won);
            rowsOut.Add((k, wt - wn, [k, offered.ToString(), taken.ToString(), Pct(offered == 0 ? double.NaN : taken / (double)offered), Pct(wt), Pct(wn), F((wt - wn) * 100, "+0;-0;0"), F(Median(took.Select(r => r.Minutes)))]));
        }
        foreach (var (_, _, cells) in rowsOut.OrderBy(x => x.Key[..2]).ThenByDescending(x => double.IsNaN(x.Delta) ? -9 : x.Delta)) Row(sb, cells);
        sb.AppendLine();

        // Where the damage came from.
        sb.AppendLine("### Damage by source (mean share of a run's damage; runs it appears in)\n");
        Head(sb, "source", "share", "runs");
        var shares = new Dictionary<string, (double Sum, int N)>();
        foreach (var r in runs)
        {
            double total = r.DamageBy.Values.Sum();
            if (total <= 0) continue;
            foreach (var (k, v) in r.DamageBy)
            {
                var (s, n) = shares.GetValueOrDefault(k);
                shares[k] = (s + v / total, n + 1);
            }
        }
        foreach (var (k, (s, n)) in shares.OrderByDescending(x => x.Value.Sum).Take(45))
            Row(sb, k, Pct(s / Math.Max(1, n)), n);
        sb.AppendLine();

        sb.AppendLine("### Evolutions (how often, and when)\n");
        Head(sb, "evolution", "runs", "median minute");
        foreach (var g in runs.SelectMany(r => r.Evolved).GroupBy(e => e.Id).OrderByDescending(g => g.Count()))
            Row(sb, g.Key, g.Count(), F(Median(g.Select(e => e.At))));
        sb.AppendLine();

        sb.AppendLine("### What killed them\n");
        Head(sb, "killer", "runs", "median minute");
        foreach (var g in runs.Where(r => r.Died).GroupBy(r => r.KilledBy).OrderByDescending(g => g.Count()))
            Row(sb, g.Key, g.Count(), F(Median(g.Select(r => r.Minutes))));
        sb.AppendLine();
        sb.AppendLine($"Rerolls used {runs.Sum(r => r.Rerolls)}, banishes {runs.Sum(r => r.Banishes)}, respite drafts {runs.Sum(r => r.Respites)} of {runs.Sum(r => r.NormalDrafts)}.");
        return sb.ToString();
    }

    public static string Probes(List<ProbeResult> probes)
    {
        var sb = new StringBuilder();
        sb.AppendLine($"## Probes: {probes.Count}\n");
        Head(sb, "policy", "level", "n", "power", "crowd dps", "champion dps", "kills/s", "EHP", "weapons", "evolved", "on path");
        foreach (var g in probes.GroupBy(p => (p.Spec.Policy, p.Spec.Level)).OrderBy(g => g.Key.Level).ThenBy(g => g.Key.Policy))
        {
            var l = g.ToList();
            Row(sb, g.Key.Policy, g.Key.Level, l.Count, F(Median(l.Select(p => p.Power)), "0"), F(Median(l.Select(p => p.CrowdDps)), "0"), F(Median(l.Select(p => p.BossDps)), "0"),
                F(Median(l.Select(p => p.KillsPerSec)), "0.0"), F(Median(l.Select(p => p.Ehp)), "0"), F(Median(l.Select(p => (double)p.Weapons)), "0"),
                F(Median(l.Select(p => (double)p.Evolved)), "0"), F(Median(l.Select(p => (double)p.OnPath)), "0"));
        }
        sb.AppendLine();
        foreach (var lv in probes.Select(p => p.Spec.Level).Distinct().OrderBy(x => x))
        {
            var meds = probes.Where(p => p.Spec.Level == lv && p.Spec.Policy.StartsWith("path:")).GroupBy(p => p.Spec.Policy)
                .Select(g => (g.Key, Median(g.Select(p => p.Power)))).OrderBy(x => x.Item2).ToList();
            if (meds.Count > 1)
                sb.AppendLine($"Level {lv}: weakest path {meds[0].Key} {meds[0].Item2:0}, strongest {meds[^1].Key} {meds[^1].Item2:0}, spread ×{meds[^1].Item2 / meds[0].Item2:0.00}");
        }
        return sb.ToString();
    }
}
