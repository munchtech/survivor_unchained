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
///   LAB_BOT       'plain' (default: the arena bot as it was) or 'deft' (it also dodges
///                 lunges and pots and closes on the throwers: nearer a player who knows the game)
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

    sealed record Row(ArenaPlay.Case Case, ArenaPlay.Result R)
    {
        public bool Won => R.WonAt != null;
        public string Oath => Case.Oaths.Length == 0 ? "none" : string.Join("+", Case.Oaths);
        /// <summary>Fell before the boss was dead.</summary>
        public bool Lost => !Won && R.Died;
    }

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
        int seeds = int.Parse(Env("LAB_SEEDS", "4")), seed0 = int.Parse(Env("LAB_SEED0", "1000"));
        string level = Env("LAB_LEVEL", "tier");
        double minutes = double.Parse(Env("LAB_MINUTES", "45"), Inv);
        bool deft = Env("LAB_BOT", "plain") == "deft";
        var cases = new List<ArenaPlay.Case>();
        foreach (var c in callings)
        {
            int weapons = Rpg.Callings.Archetype(c).Weapons.Count;
            foreach (int tier in tiers)
                foreach (var people in peoples)
                    foreach (var oath in oathList)
                        for (int s = 0; s < seeds; s++)
                            cases.Add(new ArenaPlay.Case(seed0 + s * 7919 + tier * 31 + Array.FindIndex(MapOffers.Peoples, d => d.Id == people) * 3, c, tier, people,
                                oath == "none" ? [] : oath.Split('+'), level == "tier" ? 1 + 3 * (tier - 1) : int.Parse(level),
                                s % weapons, s / weapons % 2, minutes, deft));
        }
        // Everything the bots touch read in once, before the threads share it.
        ArenaPlay.Play(cases[0] with { MaxMinutes = 0.05 });
        var rows = RunAll(cases, c => new Row(c, ArenaPlay.Play(c)), dir, "arena", log);
        WriteArenaCsv(dir, rows);
        ArenaSummary(rows, sum);
    }

    static string Q(string s) => s.Contains(',') || s.Contains('"') ? $"\"{s.Replace("\"", "\"\"")}\"" : s;

    static void WriteArenaCsv(string dir, List<Row> rows)
    {
        var o = new StringBuilder("run,bot,seed,calling,weapon,ability,tier,people,oath,level,won,win_min,died,minutes,death_cause,killer_level,kills,ember,cards,cards_per_min," +
            "low_hp,low_hp_before_win,boss_max_hp,boss_seconds,boss_left,quaffs,heralds,greats,top_hurt,ember_curve,alive_curve,hp_curve,build\n");
        var cards = new StringBuilder("run,calling,tier,people,won,minutes,card,kind,minute\n");
        for (int i = 0; i < rows.Count; i++)
        {
            var (c, r) = (rows[i].Case, rows[i].R);
            o.Append(string.Join(",", new[]
            {
                i.ToString(), c.Deft ? "deft" : "plain", c.Seed.ToString(), c.Calling, r.Weapon, r.Ability, c.Tier.ToString(), c.People, rows[i].Oath, c.Level.ToString(),
                rows[i].Won ? "1" : "0", r.WonAt is double w ? F(w, "0.00") : "", r.Died ? "1" : "0", F(r.Minutes, "0.00"), r.Killer, r.KillerLevel.ToString(),
                r.Kills.ToString(), r.Ember.ToString(), r.Cards.ToString(), F(r.Cards / Math.Max(1, r.Minutes)),
                F(r.LowHp, "0.000"), F(r.LowHpBefore, "0.000"), F(r.BossMaxHp, "0"), F(r.BossSeconds, "0.0"), r.BossLeft < 0 ? "" : F(r.BossLeft, "0.000"),
                r.Quaffs.ToString(), r.Heralds.ToString(), Q(string.Join(" ", r.Greats)),
                Q(string.Join(" ", r.Hurt.OrderByDescending(h => h.Value).Take(4).Select(h => $"{h.Key}:{h.Value:0}"))),
                Q(string.Join(" ", r.EmberAt)), Q(string.Join(" ", r.AliveAt)), Q(string.Join(" ", r.HpAt.Select(h => F(h)))), Q(r.Build),
            })).Append('\n');
            foreach (var p in r.Picks)
                cards.Append($"{i},{c.Calling},{c.Tier},{c.People},{(rows[i].Won ? 1 : 0)},{F(r.Minutes, "0.00")},{p.Id},{p.Kind},{F(p.Minute, "0.00")}\n");
        }
        File.WriteAllText(Path.Combine(dir, "arena_runs.csv"), o.ToString());
        File.WriteAllText(Path.Combine(dir, "arena_cards.csv"), cards.ToString());
    }

    static double Median(IEnumerable<double> xs)
    {
        var a = xs.OrderBy(x => x).ToArray();
        return a.Length == 0 ? double.NaN : a.Length % 2 == 1 ? a[a.Length / 2] : (a[a.Length / 2 - 1] + a[a.Length / 2]) / 2;
    }

    static string Pct(int k, int n) => n == 0 ? "-" : $"{100.0 * k / n:0}%";
    static string M(double v, string f = "0.0") => double.IsNaN(v) ? "-" : F(v, f);

    /// <summary>Win rates and the shape of the losses, one line per group.</summary>
    static void Table(StringBuilder sum, string title, IEnumerable<IGrouping<string, Row>> groups)
    {
        sum.AppendLine($"### {title}").AppendLine();
        sum.AppendLine("| | runs | won | fell before the boss | median death (min) | boss kill (s) | fell to the boss | lowest health before the win | cards/min |");
        sum.AppendLine("|---|---|---|---|---|---|---|---|---|");
        foreach (var g in groups)
        {
            var l = g.ToList();
            var lost = l.Where(r => r.Lost).ToList();
            var won = l.Where(r => r.Won).ToList();
            var atBoss = l.Where(r => r.R.BossLeft > 0).ToList();
            sum.AppendLine($"| {g.Key} | {l.Count} | {Pct(won.Count, l.Count)} | {Pct(lost.Count, l.Count)} | {M(Median(lost.Select(r => r.R.Minutes)))} | " +
                $"{M(Median(won.Select(r => r.R.BossSeconds)), "0")} | {(atBoss.Count > 0 ? $"{atBoss.Count} fell to it, {M(Median(atBoss.Select(r => r.R.BossLeft * 100)), "0")}% left" : "-")} | " +
                $"{M(Median(l.Select(r => r.R.LowHpBefore * 100)), "0")}% | {M(Median(l.Select(r => r.R.Cards / Math.Max(1, r.R.Minutes))), "0.00")} |");
        }
        sum.AppendLine();
    }

    static void ArenaSummary(List<Row> rows, StringBuilder sum)
    {
        sum.AppendLine($"## Arena: {rows.Count} runs").AppendLine();
        Table(sum, "By calling and tier", rows.GroupBy(r => $"{r.Case.Calling} t{r.Case.Tier}").OrderBy(g => g.Key));
        Table(sum, "By calling", rows.GroupBy(r => r.Case.Calling).OrderBy(g => g.Key));
        Table(sum, "By starting weapon", rows.GroupBy(r => $"{r.Case.Calling} {r.R.Weapon}").OrderBy(g => g.Key));
        Table(sum, "By people and tier", rows.GroupBy(r => $"{r.Case.People} t{r.Case.Tier}").OrderBy(g => g.Key));
        Table(sum, "By tier", rows.GroupBy(r => $"tier {r.Case.Tier}").OrderBy(g => g.Key));
        if (rows.Select(r => r.Oath).Distinct().Count() > 1) Table(sum, "By oath", rows.GroupBy(r => r.Oath).OrderBy(g => g.Key));

        // When they fall: five-minute buckets, before the win.
        sum.AppendLine("### When the losses come (minute fallen, before the win)").AppendLine();
        var lost = rows.Where(r => r.Lost).ToList();
        sum.AppendLine("| minutes | " + string.Join(" | ", rows.Select(r => r.Case.Tier).Distinct().OrderBy(t => t).Select(t => $"tier {t}")) + " |");
        sum.AppendLine("|---|" + string.Concat(rows.Select(r => r.Case.Tier).Distinct().Select(_ => "---|")));
        for (int b = 0; b < 7; b++)
            sum.AppendLine($"| {b * 5}-{b * 5 + 5} | " + string.Join(" | ", rows.Select(r => r.Case.Tier).Distinct().OrderBy(t => t)
                .Select(t => lost.Count(r => r.Case.Tier == t && (int)Math.Min(6, r.R.Minutes / 5) == b).ToString())) + " |");
        sum.AppendLine();

        sum.AppendLine("### What kills them (before the win)").AppendLine();
        sum.AppendLine("| killer | deaths | median minute |").AppendLine("|---|---|---|");
        foreach (var g in lost.GroupBy(r => r.R.Killer).OrderByDescending(g => g.Count()))
            sum.AppendLine($"| {g.Key} | {g.Count()} | {M(Median(g.Select(r => r.R.Minutes)))} |");
        sum.AppendLine();

        // The endless: how long a winner lasts past the half hour (cut short at LAB_MINUTES).
        var won = rows.Where(r => r.Won).ToList();
        if (won.Count > 0)
        {
            double cap = won.Max(r => r.Case.MaxMinutes);
            sum.AppendLine("### After the win").AppendLine();
            sum.AppendLine("| tier | winners | still standing at the cut | median minutes past the win (of those who fell) |").AppendLine("|---|---|---|---|");
            foreach (var g in won.GroupBy(r => r.Case.Tier).OrderBy(g => g.Key))
                sum.AppendLine($"| {g.Key} | {g.Count()} | {g.Count(r => !r.R.Died)} | {M(Median(g.Where(r => r.R.Died).Select(r => r.R.Minutes - r.R.WonAt!.Value)))} |");
            sum.AppendLine();
        }

        // The horde and the ember, minute by minute (the mean of every run still going).
        sum.AppendLine("### The horde by minute (mean of runs still going)").AppendLine();
        sum.AppendLine("| minute | runs | ember | alive | health | creature level |").AppendLine("|---|---|---|---|---|---|");
        int most = rows.Max(r => r.R.EmberAt.Length);
        for (int m = 0; m < most; m += m < 10 ? 1 : 2)
        {
            var at = rows.Where(r => r.R.EmberAt.Length > m).ToList();
            sum.AppendLine($"| {m + 1} | {at.Count} | {M(at.Average(r => r.R.EmberAt[m]))} | {M(at.Average(r => r.R.AliveAt[m]), "0")} | " +
                $"{M(at.Average(r => r.R.HpAt[m]) * 100, "0")}% | {M(at.Average(r => r.R.LevelAt[m]))} |");
        }
        sum.AppendLine();

        // The great blessings: each run takes the first of three offered, so taking one is near enough chance.
        sum.AppendLine("### Great blessings (first choice, as the arena begins)").AppendLine();
        sum.AppendLine("| blessing | runs | won | fell before the boss | median minutes lived (losses) |").AppendLine("|---|---|---|---|---|");
        foreach (var g in rows.Where(r => r.R.Greats.Count > 0).GroupBy(r => r.R.Greats[0]).OrderByDescending(g => (double)g.Count(r => r.Won) / g.Count()))
            sum.AppendLine($"| {g.Key} | {g.Count()} | {Pct(g.Count(r => r.Won), g.Count())} | {Pct(g.Count(r => r.Lost), g.Count())} | {M(Median(g.Where(r => r.Lost).Select(r => r.R.Minutes)))} |");
        sum.AppendLine();

        // Every card: how often offered, how often taken, and how the runs that took
        // it in the first quarter hour went (nearly every run lives that long, so
        // the comparison is not flattered by the long runs taking more cards).
        sum.AppendLine("### Cards (offered, taken, and how the runs that took one early went)").AppendLine();
        sum.AppendLine("| card | offered | taken (runs) | median minute first taken | taken by minute 15 | won when taken by 15 | won when not |").AppendLine("|---|---|---|---|---|---|---|");
        var offered = rows.SelectMany(r => r.R.Offered).GroupBy(x => x).ToDictionary(g => g.Key, g => g.Count());
        var ids = rows.SelectMany(r => r.R.Picks.Select(p => p.Id)).Concat(offered.Keys.Where(k => !k.StartsWith("evolve:"))).Distinct()
            .Concat(Content.Weapons.Pool).Concat(Content.Boons.All.Keys).Distinct().OrderBy(x => x).ToList();
        foreach (var id in ids)
        {
            var took = rows.Where(r => r.R.Picks.Any(p => p.Id == id)).ToList();
            var early = rows.Where(r => r.R.Picks.Any(p => p.Id == id && p.Minute < 15)).ToList();
            var not = rows.Where(r => r.R.Picks.All(p => p.Id != id || p.Minute >= 15)).ToList();
            int off = offered.GetValueOrDefault(id) + offered.GetValueOrDefault($"evolve:{id}");
            sum.AppendLine($"| {id} | {off} | {took.Count} | {M(Median(took.Select(r => r.R.Picks.First(p => p.Id == id).Minute)))} | {early.Count} | " +
                $"{Pct(early.Count(r => r.Won), early.Count)} | {Pct(not.Count(r => r.Won), not.Count)} |");
        }
        sum.AppendLine();
    }

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
