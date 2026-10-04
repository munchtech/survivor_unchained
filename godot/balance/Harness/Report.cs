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
        if (runs.Select(r => r.Spec.Tier).Distinct().Count() > 1) Summary(sb, "tier", runs.GroupBy(r => $"tier {r.Spec.Tier}"));
        if (runs.Select(r => Oath(r)).Distinct().Count() > 1) Summary(sb, "oath", runs.GroupBy(Oath));
        if (runs.Select(r => r.Spec.Level).Distinct().Count() > 1) Summary(sb, "level", runs.GroupBy(r => $"level {r.Spec.Level}"));

        // How the losses come: before the boss, by five minutes; to the boss, with what was left of it.
        var lost = runs.Where(r => r.Died && !r.Won).ToList();
        if (lost.Count > 0)
        {
            sb.AppendLine("### When the losses come\n");
            var tiers = runs.Select(r => r.Spec.Tier).Distinct().OrderBy(t => t).ToList();
            Head(sb, ["minutes", .. tiers.Select(t => $"tier {t}")]);
            for (int b5 = 0; b5 < 7; b5++)
                Row(sb, [b5 < 6 ? $"{b5 * 5}-{b5 * 5 + 5}" : "the boss", .. tiers.Select(t => (object)lost.Count(r => r.Spec.Tier == t && (r.BossLeft >= 0 ? 6 : (int)Math.Min(5, r.Minutes / 5)) == b5))]);
            var toBoss = lost.Where(r => r.BossLeft >= 0).ToList();
            if (toBoss.Count > 0) sb.AppendLine($"\nFell to the boss: {toBoss.Count}, with a median {Pct(Median(toBoss.Select(r => r.BossLeft)))} of it left.");
            var kindled = runs.Where(r => r.CoreBroken != null).ToList();
            if (kindled.Count > 0)
                sb.AppendLine($"\nThe Kindling's core broken within its minute: {string.Join(", ", kindled.GroupBy(r => r.Spec.Policy).OrderBy(g => g.Key).Select(g => $"{g.Key} {Pct(Rate(g.ToList(), r => r.CoreBroken == true))}"))} (of {kindled.Count} that met it).");
            sb.AppendLine();
        }
        // Each people's boss: how its fights went, and whether its marked blows were read.
        var met = runs.Where(r => r.BossPhase >= 0).ToList();
        if (met.Count > 0)
        {
            sb.AppendLine("### The bosses\n");
            Head(sb, "people", "fights", "won", "fell to it", "TTK (s)", "TTK p10-p90 (s)", "grew wild", "blows landed / marked", "Break (of health)", "staggers", "phase reached");
            foreach (var g in met.GroupBy(r => r.Spec.People).OrderBy(g => g.Key))
            {
                var l = g.ToList();
                var ttk = l.Where(r => r.Won && r.BossTtk != null).Select(r => r.BossTtk!.Value).OrderBy(x => x).ToList();
                string spread = ttk.Count == 0 ? "–" : $"{F(ttk[(int)(ttk.Count * 0.1)], "0")}-{F(ttk[Math.Min(ttk.Count - 1, (int)(ttk.Count * 0.9))], "0")}";
                Row(sb, g.Key, l.Count, Pct(Rate(l, r => r.Won)), Pct(Rate(l, r => r.BossLeft >= 0)), F(Median(ttk), "0"), spread, Pct(Rate(l, r => r.BossSoft)),
                    $"{l.Sum(r => r.BossLanded)} / {l.Sum(r => r.BossMarked)}", Pct(Median(l.Select(r => r.BossBreak))), F(Median(l.Select(r => (double)r.BossStaggers)), "0"),
                    F(Median(l.Select(r => (double)r.BossPhase + 1)), "0"));
            }
            sb.AppendLine();
        }
        // The minibosses: met, killed, how long they took, and who they killed.
        var mbs = runs.SelectMany(r => r.MinibossesMet).GroupBy(d => d).ToList();
        if (mbs.Count > 0)
        {
            sb.AppendLine("### The minibosses\n");
            Head(sb, "miniboss", "met", "killed", "TTK (s)", "TTK p90 (s)", "minute killed", "runs it ended");
            foreach (var g in mbs.OrderBy(g => g.Key))
            {
                var kills = runs.SelectMany(r => r.Minibosses).Where(m => m.Def == g.Key).ToList();
                var ttk = kills.Select(m => m.Ttk).OrderBy(x => x).ToList();
                Row(sb, g.Key, g.Count(), kills.Count, F(Median(ttk), "0"), ttk.Count == 0 ? "–" : F(ttk[Math.Min(ttk.Count - 1, (int)(ttk.Count * 0.9))], "0"),
                    F(Median(kills.Select(m => m.At))), runs.Count(r => r.Died && r.KilledBy == g.Key));
            }
            sb.AppendLine();
        }
        // The long night: how far past the half hour the won runs got, and what ended them.
        var night = runs.Where(r => r.Won && r.Spec.Beyond > 0).ToList();
        if (night.Count > 0)
        {
            sb.AppendLine("### The long night (won runs, minutes past the half hour)\n");
            Head(sb, "calling", "runs", "fell", "median", "p10-p90", "furthest", "standing at +15/+30/+45/+60/+90", "returns met", "dark's oaths");
            foreach (var g in night.GroupBy(r => r.Spec.Calling).OrderBy(g => g.Key).Append(night.GroupBy(_ => "all").First()))
            {
                var l = g.ToList();
                var past = l.Select(r => r.Minutes - 30).OrderBy(x => x).ToList();
                string standing = string.Join(" / ", new[] { 15, 30, 45, 60, 90 }.Select(m => Pct(l.Count(r => r.Minutes - 30 >= m) / (double)l.Count)));
                Row(sb, g.Key, l.Count, Pct(Rate(l, r => r.Died)), F(Median(past), "0"), $"{F(past[(int)(past.Count * 0.1)], "0")}-{F(past[Math.Min(past.Count - 1, (int)(past.Count * 0.9))], "0")}",
                    F(past[^1], "0"), standing, F(Median(l.Select(r => (double)r.Returns)), "0"), F(Median(l.Select(r => (double)r.Dark)), "0"));
            }
            var killers = night.Where(r => r.Died).GroupBy(r => r.KilledBy).OrderByDescending(g => g.Count()).Take(6);
            sb.AppendLine("\nWhat ended them: " + string.Join(", ", killers.Select(g => $"{g.Key} {g.Count()}")) + "\n");
        }
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

        // The horde's charges, and how near the survivor came to falling (docs/SKILLS_DESIGN.md, "Encounters").
        sb.AppendLine("### Encounters over the minutes (means; dipped: runs below half health that minute)\n");
        Head(sb, "minute", "charges/min", "most at once", "s with 3+ at once", "spikes", "dipped below ½");
        foreach (int m in new[] { 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 35, 40, 45 })
        {
            var at = runs.Where(r => r.ByMinute.Count >= m).Select(r => r.ByMinute[m - 1]).ToList();
            if (at.Count == 0) continue;
            Row(sb, m, F(at.Average(x => x.Charges)), F(at.Average(x => x.ChargePeak)), F(at.Average(x => x.Overlap)), F(at.Average(x => x.Spikes), "0.00"),
                Pct(at.Count(x => x.LowHp < 0.5) / (double)at.Count));
        }
        sb.AppendLine();

        // Every card: how often offered, taken, and how runs that took it went.
        // Runs that took a card by the fifteenth minute against those that had not (nearly
        // every run lives that long, so long runs, which take more cards, do not flatter it).
        sb.AppendLine("### Cards (offered, taken, and how the runs that took one by minute 15 went)\n");
        Head(sb, "card", "offered", "taken", "pick", "won, taken by 15", "won, not by 15", "delta", "first taken (min)");
        var keys = runs.SelectMany(r => r.Offered.Keys.Concat(r.Taken.Keys)).Distinct().Where(k => !k.StartsWith("r:") && k is not ("heal" or "gold")).ToList();
        var rowsOut = new List<(string Key, double Delta, string[] Cells)>();
        foreach (var k in keys)
        {
            int offered = runs.Sum(r => r.Offered.GetValueOrDefault(k)), taken = runs.Sum(r => r.Taken.GetValueOrDefault(k));
            var took = runs.Where(r => r.Picks.Any(p => p.Card == k && p.Minute < 15)).ToList();
            var not = runs.Where(r => r.Picks.All(p => p.Card != k || p.Minute >= 15)).ToList();
            double wt = Rate(took, r => r.Won), wn = Rate(not, r => r.Won);
            var first = runs.Select(r => r.Picks.FirstOrDefault(p => p.Card == k)).Where(p => p.Card != null).Select(p => p.Minute);
            rowsOut.Add((k, wt - wn, [k, offered.ToString(), taken.ToString(), Pct(offered == 0 ? double.NaN : taken / (double)offered), Pct(wt), Pct(wn), F((wt - wn) * 100, "+0;-0;0"), F(Median(first))]));
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

    static string Oath(RunResult r) => r.Spec.Oaths is { Length: > 0 } o ? string.Join("+", o) : "none";

    static string Q(string s) => s.Contains(',') || s.Contains('"') ? $"\"{s.Replace("\"", "\"\"")}\"" : s;

    /// <summary>The runs as CSV (the balance lab's columns, for a spreadsheet): one row a run,
    /// and one a card taken.</summary>
    public static void Csv(List<RunResult> runs, string dir)
    {
        System.IO.Directory.CreateDirectory(dir);
        var o = new StringBuilder("run,key,policy,bot,seed,calling,weapon,art,tier,people,oath,level,won,win_min,died,minutes,killer,kills,ember,cards,low_hp,boss_ttk,boss_left,quaffs,greats,ember_curve,alive_curve,hp_curve,build\n");
        var cards = new StringBuilder("run,calling,tier,people,won,minutes,card,minute\n");
        for (int i = 0; i < runs.Count; i++)
        {
            var r = runs[i];
            var s = r.Spec;
            o.AppendLine(string.Join(",", new[]
            {
                i.ToString(), Q(s.Key), s.Policy, s.Deft ? "deft" : "plain", s.Seed.ToString(), s.Calling, s.Weapon.ToString(), s.Art.ToString(), s.Tier.ToString(), s.People, Oath(r), s.Level.ToString(),
                r.Won ? "1" : "0", r.WonAt is double w ? F(w, "0.00") : "", r.Died ? "1" : "0", F(r.Minutes, "0.00"), r.KilledBy, r.Kills.ToString(), r.Ember.ToString(), r.Cards.ToString(),
                F(r.LowHp, "0.000"), r.BossTtk is double bt ? F(bt, "0.0") : "", r.BossLeft < 0 ? "" : F(r.BossLeft, "0.000"), r.Quaffs.ToString(), Q(string.Join(" ", r.Greats)),
                Q(string.Join(" ", r.ByMinute.Select(m => m.Ember))), Q(string.Join(" ", r.ByMinute.Select(m => m.Alive))), Q(string.Join(" ", r.ByMinute.Select(m => F(m.LowHp, "0.00")))), Q(r.Build),
            }));
            foreach (var p in r.Picks) cards.AppendLine($"{i},{s.Calling},{s.Tier},{s.People},{(r.Won ? 1 : 0)},{F(r.Minutes, "0.00")},{p.Card},{F(p.Minute, "0.00")}");
        }
        System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "arena_runs.csv"), o.ToString());
        System.IO.File.WriteAllText(System.IO.Path.Combine(dir, "arena_cards.csv"), cards.ToString());
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
