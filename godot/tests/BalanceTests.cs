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
[Collection("Balance")]
public class BalanceTests(ITestOutputHelper log)
{
    /// <summary>Every path from the calling that leans toward it, many seeds,
    /// at the ember of the fifteenth minute. Shared by the tests (run once).</summary>
    static readonly Lazy<List<ProbeResult>> Probes = new(() => Run(spec => [spec]));

    /// <summary>The builds of the first twelve seeds through seven more rolls of
    /// the crowd (the champion's duel left out: the rule shares are the crowd's).</summary>
    static readonly Lazy<List<ProbeResult>> Rolls = new(() =>
        Run(spec => spec.Seed > 12 ? [] : Enumerable.Range(1, 7).Select(f => spec with { Fight = f, Champion = false })));

    // A hundred and ninety-two seeds: a path's median is of its builds, and builds come in lumps (a blessing
    // taken or not), so it settles slowly. At twelve, the host read 0.68 of the median on seeds 1-12 and 0.745 on
    // 13-36; at forty-eight, 0.692 on 1-48 and 0.714 on 49-96, so the host passed or failed by its seeds. At this
    // count two disjoint windows put the host's crowd within 1% of each other (0.720 and 0.724 on 1-192 and
    // 193-384; 0.738 and 0.733 on 385-768), and on 768 seeds it reads 0.728. The champion and toughness
    // medians still move 8-12% between windows, but none of them is within a third of its bar (12 November).
    const int Seeds = 192;

    static List<ProbeResult> Run(Func<ProbeSpec, IEnumerable<ProbeSpec>> each)
    {
        var specs = new List<ProbeSpec>();
        foreach (var p in Paths.All)
            for (int s = 1; s <= Seeds; s++)
                // Without the Wicks (P5a): only two skills have one yet, so lit they measure the rollout, not the paths
                // (dawn and hunt rose 4-5% and the median with them; the host sat at 0.699). The Classes lead re-measures
                // these floors with every skill wicked.
                // Nor the skills with no evolutions yet (the warden's four calling skills, P6: their evolutions are a
                // later phase). In, the dawn bot spent a sixth slot on Rebuke, which the probe's crowd seldom reaches
                // her to wake (32 a second on seed 6, so Consecration made 46% of that build), and dawn's crowd rose
                // 3% while the host's fell 4% to Creation's banked road skill (the second day slot, e74175465), which put the host 1% under its
                // floor. The Classes lead re-measures with them in as their evolutions land.
                specs.AddRange(each(new ProbeSpec(s, p.Callings[0], $"path:{p.Id}", Targets.LevelAt(15), Wicks: false, Unevolved: false)));
        var o = new ConcurrentBag<ProbeResult>();
        Parallel.ForEach(specs, spec => o.Add(Probe.Run(spec)));
        return o.ToList();
    }

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
        // The worst build of the first twelve seeds, as this bound was set: a worst case grows with the sample.
        // Each build's share is its mean over eight rolls of the crowd: one roll swung a rule's share by a
        // third (seed 6's dawn build, the same build through each: Consecration 46% on its own roll, 36% over
        // sixteen), so the worst of twelve single fights measured the dice, not the build.
        foreach (var build in Probes.Value.Where(p => p.Spec.Seed <= 12).Concat(Rolls.Value).GroupBy(p => p.Spec with { Fight = 0, Champion = true }))
        {
            var share = new Dictionary<string, double>();
            foreach (var p in build)
            {
                double total = p.DamageBy.Values.Sum();
                if (total <= 0) continue;
                foreach (var (k, v) in p.DamageBy)
                    if (k.StartsWith("boon:") || k.StartsWith("disc:"))
                        share[k] = share.GetValueOrDefault(k) + v / total / build.Count();
            }
            foreach (var (k, v) in share) worst[k] = Math.Max(worst.GetValueOrDefault(k), v);
        }
        foreach (var (k, v) in worst.OrderByDescending(x => x.Value).Take(8)) log.WriteLine($"{k} {v:P0}");
        Assert.All(worst, kv => Assert.True(kv.Value <= 0.45, $"{kv.Key} dealt {kv.Value:P0} of a build's damage"));
    }
}

/// <summary>The probes fill every core; run alone, after the rest, so the
/// tests that time themselves (MapGenTests) are not starved.</summary>
[CollectionDefinition("Balance", DisableParallelization = true)]
public class BalanceCollection { }
