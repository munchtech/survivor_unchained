using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The balance the design aims at (docs/SKILLS_DESIGN.md, "Targets"),
/// held by the harness's probes (godot/balance): every path drafted by a bot
/// that holds to it, to the fifteenth minute's ember, then put through the
/// standard crowd and champion. Each path must reach its power; none may run
/// away from the rest; no single rule may carry a build.</summary>
public class BalanceTests(ITestOutputHelper log)
{
    /// <summary>Every path from the calling that leans toward it, a few seeds,
    /// at the ember of the fifteenth minute. Shared by the tests (run once).</summary>
    static readonly Lazy<List<ProbeResult>> Probes = new(() =>
    {
        var specs = new List<ProbeSpec>();
        foreach (var p in Paths.All)
            for (int s = 1; s <= 4; s++)
                specs.Add(new ProbeSpec(s, p.Callings[0], $"path:{p.Id}", Targets.LevelAt(15)));
        var o = new ConcurrentBag<ProbeResult>();
        Parallel.ForEach(specs, spec => o.Add(Probe.Run(spec)));
        return o.ToList();
    });

    static double Median(IEnumerable<double> xs) => Report.Median(xs);

    static Dictionary<string, (double Crowd, double Champion, double Ehp)> ByPath() =>
        Probes.Value.GroupBy(p => p.Spec.Policy[5..]).ToDictionary(g => g.Key,
            g => (Median(g.Select(p => p.CrowdDps)), Median(g.Select(p => p.BossDps)), Median(g.Select(p => p.Ehp))));

    void Show(Dictionary<string, (double Crowd, double Champion, double Ehp)> paths)
    {
        foreach (var (k, v) in paths.OrderBy(x => x.Key)) log.WriteLine($"{k,-6} crowd {v.Crowd,6:0} champion {v.Champion,6:0} ehp {v.Ehp,5:0}");
    }

    [Fact]
    public void Every_path_reaches_its_power()
    {
        var paths = ByPath();
        Show(paths);
        double crowd = Median(paths.Values.Select(v => v.Crowd)), champ = Median(paths.Values.Select(v => v.Champion)), ehp = Median(paths.Values.Select(v => v.Ehp));
        foreach (var (k, v) in paths)
        {
            // Clears the horde of the fifteenth minute as well as most paths do...
            Assert.True(v.Crowd >= 0.7 * crowd, $"{k}: crowd {v.Crowd:0} against a median of {crowd:0}");
            // ...has an answer to a champion, if not the best...
            Assert.True(v.Champion >= 0.25 * champ, $"{k}: champion {v.Champion:0} against a median of {champ:0}");
            // ...and can stand up to the horde.
            Assert.True(v.Ehp >= 0.55 * ehp, $"{k}: toughness {v.Ehp:0} against a median of {ehp:0}");
        }
    }

    [Fact]
    public void No_path_runs_away_from_the_rest()
    {
        var paths = ByPath();
        Show(paths);
        double crowd = Median(paths.Values.Select(v => v.Crowd)), champ = Median(paths.Values.Select(v => v.Champion));
        foreach (var (k, v) in paths)
        {
            Assert.True(v.Crowd <= 1.35 * crowd, $"{k}: crowd {v.Crowd:0} against a median of {crowd:0}");
            // The boss-killers may kill bosses best, not everything best: one index of both.
            double index = 0.6 * v.Crowd / crowd + 0.4 * v.Champion / champ;
            Assert.True(index <= 1.9, $"{k}: power {index:0.00} of the median");
        }
    }

    [Fact]
    public void No_single_rule_carries_a_build()
    {
        // A blessing's rule, a hidden pairing, a status: none should outdo the
        // weapons it rides on. What any one of them deals, as a share of a build's damage.
        var worst = new Dictionary<string, double>();
        foreach (var p in Probes.Value)
        {
            double total = p.DamageBy.Values.Sum();
            if (total <= 0) continue;
            foreach (var (k, v) in p.DamageBy)
                if (k.StartsWith("boon:") || k.StartsWith("disc:"))
                    worst[k] = Math.Max(worst.GetValueOrDefault(k), v / total);
        }
        foreach (var (k, v) in worst.OrderByDescending(x => x.Value).Take(8)) log.WriteLine($"{k} {v:P0}");
        Assert.All(worst, kv => Assert.True(kv.Value <= 0.45, $"{kv.Key} dealt {kv.Value:P0} of a build's damage"));
    }
}
