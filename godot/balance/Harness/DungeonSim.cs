using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace SurvivorUnchained.Balance;

/// <summary>(dungeon-fights, 15 Nov) The dungeon report: one block a dungeon, one row a bot, against the lane's targets.
/// Runs come from MapSim (the dungeon spec), played at the dungeon's entry level with the kit she has there.</summary>
public static class DungeonSim
{
    static double Pct(IEnumerable<double> xs, double q)
    {
        var a = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList();
        if (a.Count == 0) return double.NaN;
        double i = q * (a.Count - 1); int lo = (int)Math.Floor(i), hi = (int)Math.Ceiling(i);
        return a[lo] + (a[hi] - a[lo]) * (i - lo);
    }
    static string F(double x, string f = "0") => double.IsNaN(x) ? "-" : x.ToString(f);
    static double Max(IEnumerable<double> xs) { var a = xs.ToList(); return a.Count == 0 ? double.NaN : a.Max(); }

    public static string Report(List<MapRunResult> rs)
    {
        var sb = new StringBuilder();
        foreach (var dg in rs.GroupBy(r => r.Spec.Dungeon + (r.Spec.AtBoss ? " (boss alone)" : "")).OrderBy(g => g.Key))
        {
            sb.AppendLine($"### {dg.Key} (level {dg.First().Spec.Level}, gear {dg.First().Spec.GearRarity})");
            sb.AppendLine();
            sb.AppendLine("| bot | runs | cleared | deaths | min p10 / med / p90 (cleared) | min p10 / med / p90 (all) | boss TTK med (s) | marks per fight-min: rooms / boss | longest fight stretch with no mark (s), median / worst: rooms ; boss | heavy marks per fight-min: rooms / boss | longest fight stretch with no heavy mark (s), median / worst: rooms ; boss | fight share of run |");
            sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|");
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var l = g.ToList();
                var cl = l.Where(r => r.Cleared).ToList();
                double rm = l.Sum(r => r.FightRoomSec) / 60, bm = l.Sum(r => r.FightBossSec) / 60;
                var gr = l.Where(r => r.FightRoomSec > 30).Select(r => r.GapRoom).ToList();
                var gb = l.Where(r => r.FightBossSec > 20).Select(r => r.GapBoss).ToList();
                sb.AppendLine($"| {g.Key} | {l.Count} | {100 * cl.Count / l.Count}% | {100 * l.Count(r => r.Closed) / l.Count}% | {F(Pct(cl.Select(r => r.Minutes), .1), "0.0")} / {F(Pct(cl.Select(r => r.Minutes), .5), "0.0")} / {F(Pct(cl.Select(r => r.Minutes), .9), "0.0")} | {F(Pct(l.Select(r => r.Minutes), .1), "0.0")} / {F(Pct(l.Select(r => r.Minutes), .5), "0.0")} / {F(Pct(l.Select(r => r.Minutes), .9), "0.0")} | {F(Pct(l.Where(r => r.BossTtk != null).Select(r => r.BossTtk!.Value), .5))} | {F(l.Sum(r => r.MarksRoom) / Math.Max(1e-6, rm), "0.0")} / {F(l.Sum(r => r.MarksBoss) / Math.Max(1e-6, bm), "0.0")} | {F(Pct(gr, .5))} / {F(Max(gr))} ; {F(Pct(gb, .5))} / {F(Max(gb))} | {F(l.Sum(r => r.HeavyRoom) / Math.Max(1e-6, rm), "0.0")} / {F(l.Sum(r => r.HeavyBoss) / Math.Max(1e-6, bm), "0.0")} | {F(Pct(l.Where(r => r.FightRoomSec > 30).Select(r => r.HeavyGapRoom), .5))} / {F(Max(l.Where(r => r.FightRoomSec > 30).Select(r => r.HeavyGapRoom)))} ; {F(Pct(l.Where(r => r.FightBossSec > 20).Select(r => r.HeavyGapBoss), .5))} / {F(Max(l.Where(r => r.FightBossSec > 20).Select(r => r.HeavyGapBoss)))} | {F(100 * l.Sum(r => r.FightSec) / Math.Max(1, l.Sum(r => r.Minutes * 60)))}% |");
            }
            sb.AppendLine();
            sb.AppendLine("Where she falls (room role; plan; killer; ruler phase):");
            sb.AppendLine();
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var dead = g.Where(r => r.Closed).ToList();
                if (dead.Count == 0) { sb.AppendLine($"- {g.Key}: no falls"); continue; }
                string By(Func<MapRunResult, string> f, int n = 5) => string.Join(", ", dead.GroupBy(f).OrderByDescending(x => x.Count()).Take(n).Select(x => $"{x.Key} {x.Count()}"));
                sb.AppendLine($"- {g.Key} ({dead.Count}): room {By(r => r.DeathRoom == "" ? "?" : r.DeathRoom)}; plan {By(r => r.DeathPlan == "" ? "-" : r.DeathPlan, 4)}; killer {By(r => r.KilledBy, 6)}; ruler phase {By(r => r.DeathBossPhase < 0 ? "not up" : "phase " + r.DeathBossPhase)}");
            }
            sb.AppendLine();
            sb.AppendLine("Her damage by source (mean share of run, %):");
            sb.AppendLine();
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var l = g.ToList();
                var d = l.SelectMany(r => r.Measures.DamageShare).GroupBy(kv => kv.Key).ToDictionary(x => x.Key, x => x.Sum(kv => kv.Value) / l.Count);
                var bs = l.SelectMany(r => r.BossShare).GroupBy(kv => kv.Key).ToDictionary(x => x.Key, x => x.Sum(kv => kv.Value) / Math.Max(1, l.Count(r => r.BossShare.Count > 0)));
                double noFlare = d.Where(kv => kv.Key != "flare").Sum(kv => kv.Value);
                sb.AppendLine($"- {g.Key}: {string.Join(", ", d.OrderByDescending(kv => kv.Value).Select(kv => $"{kv.Key} {kv.Value:0}"))}; bladestorm of all non-Flare damage {F(100 * d.GetValueOrDefault("bladestorm") / Math.Max(1e-6, noFlare))}%; ruler's life lost by: {string.Join(", ", bs.OrderByDescending(kv => kv.Value).Select(kv => $"{kv.Key} {kv.Value:0}"))}");
            }
            sb.AppendLine();
            sb.AppendLine("XP, levels, drops per run (cleared runs; gear picked up by rarity 0..5, mean):");
            sb.AppendLine();
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var l = g.Where(r => r.Cleared).ToList(); if (l.Count == 0) l = g.ToList();
                var ups = l.Select(r => r.LevelEnd - r.LevelStart).ToList();
                var drops = Enumerable.Range(0, 6).Select(k => l.Average(r => r.DropsByRarity[k]));
                sb.AppendLine($"- {g.Key}: xp {F(Pct(l.Select(r => r.XpGained), .5))} (p10 {F(Pct(l.Select(r => r.XpGained), .1))}, p90 {F(Pct(l.Select(r => r.XpGained), .9))}), levels gained mean {ups.Average():0.00} (0: {ups.Count(u => u == 0)}, 1: {ups.Count(u => u == 1)}, 2+: {ups.Count(u => u >= 2)}), first level-up at min {F(Pct(l.Where(r => r.LevelUpAt.Count > 0).Select(r => r.LevelUpAt[0]), .5), "0.0")}; gear {string.Join("/", drops.Select(x => x.ToString("0.0")))} total {l.Average(r => r.Items):0.0}, charts {l.Average(r => r.Charts):0.0}, packs placed {l.Average(r => r.Packs):0} cleared {l.Average(r => r.PacksCleared):0}");
            }
            sb.AppendLine();
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var l = g.Where(r => r.Cleared).ToList(); if (l.Count == 0) continue;
                var tops = l.SelectMany(r => r.Taught).Select(x => string.Join(" ", x.Split(' ').Skip(1))).GroupBy(x => x).OrderByDescending(x => x.Count()).Take(6).Select(x => $"{x.Key} x{x.Count()}");
                sb.AppendLine($"- {g.Key} taught in cleared runs: {string.Join("; ", tops)}");
            }
            sb.AppendLine();
            sb.AppendLine("By room role, pooled per bot: share of her time / fight share of it / marks per fight-min / quiet visits (entered, no mark laid on her) / damage taken per visit (max lives):");
            sb.AppendLine();
            foreach (var g in dg.GroupBy(r => r.Spec.Bot).OrderBy(g => g.Key))
            {
                var l = g.ToList();
                double tot = l.Sum(r => r.Roles.Values.Sum(x => x.Sec));
                var roles = l.SelectMany(r => r.Roles).GroupBy(kv => kv.Key).OrderBy(x => x.Key);
                sb.AppendLine($"- {g.Key}: " + string.Join("; ", roles.Select(x =>
                {
                    double sec = x.Sum(kv => kv.Value.Sec), fs = x.Sum(kv => kv.Value.FightSec); int v = x.Sum(kv => kv.Value.Visits), q = x.Sum(kv => kv.Value.QuietVisits);
                    return $"{x.Key} {100 * sec / Math.Max(1, tot):0}% of time, fight {100 * fs / Math.Max(1, sec):0}%, marks/min {x.Sum(kv => kv.Value.Marks) / Math.Max(1e-6, fs / 60):0.0}, quiet visits {q}/{v}, dmg/visit {x.Sum(kv => kv.Value.Dmg) / Math.Max(1, v):0.00}";
                })));
            }
            sb.AppendLine();
        }
        return sb.ToString();
    }
}
