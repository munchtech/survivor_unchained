using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// The balance lab: the arena and day-story bots, swept across the game's
/// whole space at once on every core, written down as CSV with a summary of
/// what it means (docs/cloud/balance-lab.md says how to read it). Only with
/// BALANCE_LAB=arena, story or all, since a full sweep takes an hour or more:
///
///   BALANCE_LAB=arena LAB_SEEDS=6 dotnet test --filter BalanceLab
///
/// The rest of the knobs (all optional) narrow or widen the sweep:
///   LAB_CALLINGS, LAB_TIERS, LAB_PEOPLES   comma lists (default: all of each, tiers 1-3)
///   LAB_OATHS     comma list of oath ids, 'none' for unsworn, 'all' for none and each
///                 oath alone (default: none)
///   LAB_SEEDS     seeds per cell (default 4); LAB_SEED0 the first (default 1000).
///                 The seed also turns the starting kit: weapon by seed, art by seed/weapons.
///   LAB_LEVEL     the survivor's level: a number, or 'tier' (default) for 1, 4, 7 by tier
///   LAB_MINUTES   where an arena is cut short (default 45: fifteen minutes of the endless)
///   LAB_BOT       'plain' (default) or 'deft' (it also dodges lunges and pots and closes
///                 on the throwers: nearer a player who knows the game)
///   LAB_POLICY    how cards are chosen (default 'first'; or greedy, random, path:ID, paths)
///
/// The arena half is the balance harness (godot/balance: the same arenas, hands,
/// drafting policies and report as `Balance.dll arena`), so there is one tool; the
/// day-story half walks the Verge with StoryPlay.
///   LAB_DAYS, LAB_LEVELS  the day-story walk's days and levels (default 1-4 and 1-5)
///   LAB_OUT       where the CSVs and summary go (default ../.lab/LABEL), LAB_LABEL its name
///   LAB_THREADS   how many at once (default: every core)
/// </summary>
public class BalanceLab(ITestOutputHelper log)
{
    static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) is { Length: > 0 } v ? v : d;
    static string[] List(string k, string d) => Env(k, d).Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static string F(double v, string f = "0.##") => v.ToString(f, Inv);

    static string Out()
    {
        string dir = Env("LAB_OUT", Path.Combine(DataRoot(), ".lab", Env("LAB_LABEL", "run")));
        Directory.CreateDirectory(dir);
        return dir;
    }

    /// <summary>godot/, found from wherever the tests run.</summary>
    static string DataRoot()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    [Fact]
    public void Sweep()
    {
        string mode = Env("BALANCE_LAB", "");
        if (mode == "") return;
        string dir = Out();
        var sum = new StringBuilder();
        sum.AppendLine($"# Balance lab: {Env("LAB_LABEL", "run")}").AppendLine();
        if (mode is "arena" or "all") Arena(dir, sum);
        if (mode is "story" or "all") Story(dir, sum);
        File.WriteAllText(Path.Combine(dir, "summary.md"), sum.ToString());
        log.WriteLine(sum.ToString());
        log.WriteLine($"written to {dir}");
    }

    /* ------------------------------------------------------------ the arena -- */

    static List<T> RunAll<T, TCase>(List<TCase> cases, Func<TCase, T> play, string dir, string name, ITestOutputHelper log)
    {
        int threads = int.Parse(Env("LAB_THREADS", Environment.ProcessorCount.ToString()));
        var done = new ConcurrentBag<(int, T)>();
        int n = 0;
        var clock = Stopwatch.StartNew();
        string progress = Path.Combine(dir, $"{name}_progress.txt");
        File.WriteAllText(progress, "");
        Parallel.ForEach(Enumerable.Range(0, cases.Count), new ParallelOptions { MaxDegreeOfParallelism = threads }, i =>
        {
            done.Add((i, play(cases[i])));
            int k = Interlocked.Increment(ref n);
            lock (done) File.AppendAllText(progress, $"{k}/{cases.Count} after {clock.Elapsed.TotalMinutes:0.0} min: {cases[i]}\n");
        });
        log.WriteLine($"{name}: {cases.Count} runs in {clock.Elapsed.TotalMinutes:0.0} min on {threads} threads");
        return done.OrderBy(d => d.Item1).Select(d => d.Item2).ToList();
    }

    void Arena(string dir, StringBuilder sum)
    {
        var callings = List("LAB_CALLINGS", "warden,reaver,arcanist,stalker");
        var tiers = List("LAB_TIERS", "1,2,3").Select(int.Parse).ToArray();
        var peoples = List("LAB_PEOPLES", "pack,dead,lamplings,kerchiefs");
        var oathList = List("LAB_OATHS", "none");
        if (oathList is ["all"]) oathList = new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray();
        var policies = List("LAB_POLICY", "first").SelectMany(x => x == "paths" ? Content.Paths.All.Select(q => $"path:{q.Id}") : [x]).ToArray();
        int seeds = int.Parse(Env("LAB_SEEDS", "4")), seed0 = int.Parse(Env("LAB_SEED0", "1000"));
        string level = Env("LAB_LEVEL", "tier");
        double minutes = double.Parse(Env("LAB_MINUTES", "45"), Inv);
        bool deft = Env("LAB_BOT", "plain") == "deft";
        var specs = new List<RunSpec>();
        foreach (var c in callings)
        {
            int weapons = Rpg.Callings.Archetype(c).Weapons.Count;
            foreach (var policy in policies)
                foreach (int tier in tiers)
                    foreach (var people in peoples)
                        foreach (var oath in oathList)
                            for (int s = 0; s < seeds; s++)
                                specs.Add(new RunSpec(seed0 + s * 7919 + tier * 31 + Array.FindIndex(MapOffers.Peoples, d => d.Id == people) * 3, c, policy, tier, people,
                                    oath == "none" ? null : oath.Split('+'), Cap: minutes, Beyond: Math.Max(0, minutes - 30), Weapon: s % weapons, Art: s / weapons % 2,
                                    Level: level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level), Deft: deft));
        }
        // Everything the runs touch read in once, before the threads share it.
        ArenaSim.Play(specs[0] with { Cap = 0.05 });
        var runs = RunAll(specs, ArenaSim.Play, dir, "arena", log);
        Report.Csv(runs, dir);
        sum.AppendLine(Report.Arena(runs));
    }

    static string Q(string s) => s.Contains(',') || s.Contains('"') ? $"\"{s.Replace("\"", "\"\"")}\"" : s;

    static double Median(IEnumerable<double> xs)
    {
        var a = xs.OrderBy(x => x).ToArray();
        return a.Length == 0 ? double.NaN : a.Length % 2 == 1 ? a[a.Length / 2] : (a[a.Length / 2 - 1] + a[a.Length / 2]) / 2;
    }

    static string Pct(int k, int n) => n == 0 ? "-" : $"{100.0 * k / n:0}%";
    static string M(double v, string f = "0.0") => double.IsNaN(v) ? "-" : F(v, f);

    /* ------------------------------------------------------- the day story -- */

    sealed record Walk(int Seed, string Calling, int Level, int Day);

    void Story(string dir, StringBuilder sum)
    {
        var callings = List("LAB_CALLINGS", "warden,reaver,arcanist,stalker");
        var levels = List("LAB_LEVELS", "1,2,3,4,5").Select(int.Parse).ToArray();
        var days = List("LAB_DAYS", "1,2,3,4").Select(int.Parse).ToArray();
        int seeds = int.Parse(Env("LAB_SEEDS", "4")), seed0 = int.Parse(Env("LAB_SEED0", "1000"));
        var cases = new List<Walk>();
        foreach (var c in callings) foreach (int lv in levels) foreach (int d in days) for (int s = 0; s < seeds; s++) cases.Add(new Walk(seed0 + s * 7919 + lv * 13 + d, c, lv, d));
        StoryPlay.Walk(cases[0].Seed, cases[0].Calling, 1, 1);
        var rows = RunAll(cases, w => (W: w, R: StoryPlay.Walk(w.Seed, w.Calling, w.Level, w.Day)), dir, "story", log);
        var o = new StringBuilder("seed,calling,level,day,fell,minutes,packs_reached,packs,kills,levels_gained,xp,low_hp,quaffs,killer,killer_level,top_hurt\n");
        foreach (var (w, r) in rows)
            o.Append($"{w.Seed},{w.Calling},{w.Level},{w.Day},{(r.Died ? 1 : 0)},{F(r.Minutes, "0.00")},{r.Places},{r.Packs},{r.Kills},{r.Levels},{F(r.Xp, "0")},{F(r.LowHp, "0.000")}," +
                $"{r.Quaffs},{r.Killer},{r.KillerLevel},{Q(string.Join(" ", r.Hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key}:{h.Value:0}")))}\n");
        File.WriteAllText(Path.Combine(dir, "story_runs.csv"), o.ToString());

        sum.AppendLine($"## Day story (the Verge by day): {rows.Count} walks").AppendLine();
        void T(string title, IEnumerable<IGrouping<string, (Walk W, StoryPlay.Result R)>> groups)
        {
            sum.AppendLine($"### {title}").AppendLine();
            sum.AppendLine("| | walks | fell | packs reached (median) | kills (median) | lowest health (median) | draughts drunk (mean) | xp (median) |").AppendLine("|---|---|---|---|---|---|---|---|");
            foreach (var g in groups)
            {
                var l = g.ToList();
                sum.AppendLine($"| {g.Key} | {l.Count} | {Pct(l.Count(x => x.R.Died), l.Count)} | {M(Median(l.Select(x => (double)x.R.Places)), "0")} of {l[0].R.Packs} | " +
                    $"{M(Median(l.Select(x => (double)x.R.Kills)), "0")} | {M(Median(l.Select(x => x.R.LowHp * 100)), "0")}% | {M(l.Average(x => x.R.Quaffs))} | {M(Median(l.Select(x => x.R.Xp)), "0")} |");
            }
            sum.AppendLine();
        }
        T("By calling", rows.GroupBy(x => x.W.Calling).OrderBy(g => g.Key));
        T("By level", rows.GroupBy(x => $"level {x.W.Level}").OrderBy(g => g.Key));
        T("By day", rows.GroupBy(x => $"day {x.W.Day}").OrderBy(g => g.Key));
        T("By calling and level", rows.GroupBy(x => $"{x.W.Calling} lv{x.W.Level}").OrderBy(g => g.Key));
        sum.AppendLine("### What kills them by day").AppendLine();
        sum.AppendLine("| killer | deaths |").AppendLine("|---|---|");
        foreach (var g in rows.Where(x => x.R.Died).GroupBy(x => $"{x.R.Killer} (lv {x.R.KillerLevel})").OrderByDescending(g => g.Count()))
            sum.AppendLine($"| {g.Key} | {g.Count()} |");
        sum.AppendLine();
    }
}
