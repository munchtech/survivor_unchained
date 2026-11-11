using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;

namespace SurvivorUnchained.Balance;

public sealed record DensityRun(string Zone, int Seed, string Calling, string Bot, int Tier, int StartLevel, int Day,
    bool Reached, int Falls, int Skipped, double PlaySeconds, DensityMeasures Density)
{
    public string Key => $"{Zone}/{Calling}/{Bot}/T{Tier}/s{Seed}";
}
public sealed record DensityRunFile(int SchemaVersion, string Date, string SourceRevision, DensityRun Run);

public static class DensityReport
{
    static string N(double? x) => x?.ToString("0.00", CultureInfo.InvariantCulture) ?? "n/a";
    public static string Markdown(IReadOnlyList<DensityRun> runs, string date, string revision, string command, IReadOnlyList<string> jsonFiles)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# Fight density baseline");
        sb.AppendLine();
        sb.AppendLine($"Measured {date}, source `{revision}` plus the density instrument. ARPG_FUN section 4, P0 item 3. Measurement only; no tuning.");
        sb.AppendLine();
        sb.AppendLine("```powershell");
        sb.AppendLine(command);
        sb.AppendLine("```");
        sb.AppendLine();
        sb.AppendLine("Low Ford uses the existing `zone` sim from wake to gate. The first story zone is Thornhollow Verge: the StoryPlay field-pack route, nearest pack then next nearest and back to the entry, with campaign pressing hands. The Verge starts on the stated level/day with starter gear; it is a separate run, not an imported Low Ford save. Quest camps encountered along the walk are measured too.");
        sb.AppendLine();
        sb.AppendLine("The Verge walk retains its player-radius path through combat pauses and uses it when a foe is separated by a wall. Its default wall-clock budget is 60 s; the regression test uses 20 s and 300 simulation seconds, with the stop reason, position and route progress included on failure.");
        sb.AppendLine();
        sb.AppendLine("The clock is elapsed simulation seconds, including travel, loot time, scripted holds, falls and the headless film captions. Low Ford's play-only clock is shown separately. Enemy proximity is sampled every 1/60 s, including the opening and terminal stretches: a living hostile, excluding dying/burrowed foes, whose edge is within `Pilot.EngageRange` (the feet's actual current-build reach, including its ranged-foe rule). This geometric test does not require a clear sight line or a roused foe.");
        sb.AppendLine();
        sb.AppendLine("Low Ford groups come from `Encounters.Packs` (waves keep their beat ID) and its separately placed `Champions` keys. Verge groups are retained where its spawner makes them: one `Pack` call including mixed foes and its leader, or a quest crew's existing tag. Pooled identities include their spawn seed. Ungrouped kills still count toward KPM; singleton bosses and unassigned summons are not invented into packs.");
        sb.AppendLine();
        sb.AppendLine("Pack gaps use consecutive packs ordered by first positive-damage hit: the previous pack's final death to the next pack's first hit, only if the previous pack cleared. Negative gaps mean the fights overlapped. A positive gap can contain an intervening singleton boss fight; it is not proof of a quiet lull. Elite cadence is first hit to first hit between groups containing a non-boss elite. After-elite gaps are the same pack gaps restricted to elite groups; a final elite with no next encounter is unpaired, not a measured lull. Empty samples are `n/a`; median averages the middle pair; p90 is nearest rank. No missing elite is reported as a zero-second cadence.");
        sb.AppendLine();
        sb.AppendLine("| Run | Through / falls / skipped | Elapsed / play s | Kills / KPM | Pack gap s: median / p90 / max (n) | Elite interval s: median / max (n) | After elite gap s: median / max (n) | Longest no enemy s (start-end) | Ungrouped kills |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|");
        foreach (var r in runs)
        {
            var d = r.Density; var g = d.PackGapSeconds; var e = d.EliteIntervalSeconds; var l = d.AfterEliteGapSeconds;
            string quiet = d.LongestNoEnemy is { } q ? $"{N(q.Seconds)} ({N(q.Start)}-{N(q.End)})" : "n/a";
            sb.AppendLine($"| {r.Key}, L{r.StartLevel} day {r.Day} | {r.Reached} / {r.Falls} / {r.Skipped} | {N(d.Seconds)} / {N(r.PlaySeconds)} | {d.Kills} / {N(d.KillsPerMinute)} | {N(g.Median)} / {N(g.P90)} / {N(g.Max)} ({g.Count}) | {N(e.Median)} / {N(e.Max)} ({e.Count}) | {N(l.Median)} / {N(l.Max)} ({l.Count}) | {quiet} | {d.UngroupedKills} |");
        }
        sb.AppendLine();
        sb.AppendLine("| Rhythm measure | Target to playtest | Today's observations |");
        sb.AppendLine("|---|---|---|");
        sb.AppendLine("| Last pack kill to next first hit | Next pack within 5-8 s | " + string.Join("; ", runs.Select(r => $"{r.Zone} s{r.Seed}: median {N(r.Density.PackGapSeconds.Median)} s, p90 {N(r.Density.PackGapSeconds.P90)} s")) + " |");
        sb.AppendLine("| Elite first hit to next elite first hit | An elite pack every 60-90 s | " + string.Join("; ", runs.Select(r => $"{r.Zone} s{r.Seed}: median {N(r.Density.EliteIntervalSeconds.Median)} s ({r.Density.Packs.Count(p => p.Elite && p.FirstHit != null)} encountered)")) + " |");
        sb.AppendLine("| After each elite | A designed lull; duration to playtest | " + string.Join("; ", runs.Select(r => $"{r.Zone} s{r.Seed}: {(r.Density.AfterEliteGapSeconds.Count == 0 ? "n/a (no paired elite exits)" : $"{r.Density.Gaps.Count(g => g.AfterElite && g.Seconds > 0)}/{r.Density.AfterEliteGapSeconds.Count} paired exits have a positive gap")}")) + " |");
        sb.AppendLine("| Kills/min and longest empty stretch | Baseline; no numeric target picked | Per-run figures above and windows below |");
        sb.AppendLine();
        sb.AppendLine("| Run | Window s | Kills | Kills/min |");
        sb.AppendLine("|---|---|---|---|");
        foreach (var r in runs)
            foreach (var w in r.Density.Windows)
                sb.AppendLine($"| {r.Zone} s{r.Seed} {r.Bot} | {N(w.Start)}-{N(w.End)} | {w.Kills} | {N(w.KillsPerMinute)} |");
        sb.AppendLine();
        sb.AppendLine("Windows are [start, end); a kill at the terminal instant belongs to the final window. The final partial window uses its actual duration. Sub-tick floating point drift at a 30 s boundary is snapped within 1e-8 s. JSON retains full precision, kill times, individual groups, gaps and elite intervals for inspection.");
        sb.AppendLine();
        sb.AppendLine("JSON output (git-ignored, one file per run):");
        foreach (string file in jsonFiles) sb.AppendLine($"- `{file}`");
        return sb.ToString();
    }
}
