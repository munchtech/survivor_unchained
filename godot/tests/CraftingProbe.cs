using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// What a night pays, measured for the crafting economy (docs/CRAFTING_DESIGN.md,
/// "The economy"): arenas played headless by the balance harness's bots, and the
/// gold, champions, slain by family, ember and minutes they came out with. Only
/// with CRAFT_PROBE=1, since it plays dozens of arenas:
///
///   CRAFT_PROBE=1 dotnet test --filter CraftingProbe --logger "console;verbosity=detailed"
///
/// CRAFT_SEEDS (default 2) seeds a cell; CRAFT_BEYOND minutes past the half hour (default 5).
/// </summary>
public class CraftingProbe(ITestOutputHelper log)
{
    static string Env(string k, string d) => Environment.GetEnvironmentVariable(k) is { Length: > 0 } v ? v : d;
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    static double Median(IEnumerable<double> xs)
    {
        var s = xs.OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s[s.Count / 2];
    }

    [Fact]
    public void Nights()
    {
        if (Env("CRAFT_PROBE", "") == "") return;
        int seeds = int.Parse(Env("CRAFT_SEEDS", "2"));
        double beyond = double.Parse(Env("CRAFT_BEYOND", "5"), Inv);
        var specs = new List<RunSpec>();
        foreach (var c in new[] { "warden", "reaver", "arcanist", "stalker" })
            foreach (int tier in new[] { 1, 2, 3 })
                foreach (var people in new[] { "pack", "dead", "lamplings", "kerchiefs" })
                    for (int s = 0; s < seeds; s++)
                        specs.Add(new RunSpec(2000 + s * 7919 + tier * 31 + people.Length * 3, c, "greedy", tier, people,
                            Cap: 30 + beyond, Beyond: beyond, Weapon: s, Level: 1 + 3 * (tier - 1), Deft: true));
        ArenaSim.Play(specs[0] with { Cap = 0.05 });
        var done = new ConcurrentBag<RunResult>();
        Parallel.ForEach(specs, sp => done.Add(ArenaSim.Play(sp)));
        var runs = done.ToList();
        var outLines = new List<string>();
        void Log(string s) { log.WriteLine(s); outLines.Add(s); }
        foreach (var r in runs.OrderBy(r => r.Spec.Tier).ThenBy(r => r.Spec.People))
            outLines.Add(string.Format(Inv, "run t{0} {1} {2} won={3} min={4:0.0} ember={5} kills={6} champs={7} gold={8:0} {9}", r.Spec.Tier, r.Spec.People, r.Spec.Calling,
                r.Won, r.Minutes, r.Ember, r.Kills, r.Champions, r.Gold, string.Join(" ", r.KillsBy.Select(kv => $"{kv.Key}:{kv.Value}"))));
        log.WriteLine("tier people     n  won  min   ember  kills  champs  gold   people-kills");
        foreach (var g in runs.GroupBy(r => (r.Spec.Tier, r.Spec.People)).OrderBy(g => g.Key))
        {
            var fam = g.SelectMany(r => r.KillsBy).GroupBy(kv => kv.Key).Select(x => $"{x.Key}:{x.Sum(y => y.Value) / g.Count()}");
            Log(string.Format(Inv, "{0,4} {1,-9} {2,2} {3,4:0%} {4,5:0.0} {5,6:0} {6,6:0} {7,7:0} {8,6:0}   {9}", g.Key.Tier, g.Key.People, g.Count(),
                g.Count(r => r.Won) / (double)g.Count(), Median(g.Select(r => r.Minutes)), Median(g.Select(r => (double)r.Ember)),
                Median(g.Select(r => (double)r.Kills)), Median(g.Select(r => (double)r.Champions)), Median(g.Select(r => r.Gold)), string.Join(" ", fam)));
        }
        foreach (var g in runs.GroupBy(r => r.Spec.Tier).OrderBy(g => g.Key))
            Log(string.Format(Inv, "tier {0}: won {1:0%}, gold median {2:0} (p25 {3:0}, p75 {4:0}), champions {5:0}, ember {6:0}", g.Key,
                g.Count(r => r.Won) / (double)g.Count(), Median(g.Select(r => r.Gold)),
                g.Select(r => r.Gold).OrderBy(x => x).ElementAt(g.Count() / 4), g.Select(r => r.Gold).OrderBy(x => x).ElementAt(g.Count() * 3 / 4),
                Median(g.Select(r => (double)r.Champions)), Median(g.Select(r => (double)r.Ember))));
        if (Environment.GetEnvironmentVariable("CRAFT_OUT") is { Length: > 0 } path) System.IO.File.WriteAllLines(path, outLines);
    }
}
