using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>NPC 17: the Low Ford's risen as a pack, not clones (Sim.Vary), and the town's walkers kept apart
/// (Play.FolkSpacing).</summary>
public class CrowdVaryTests
{
    static readonly Random R = new(17);
    static IEnumerable<double> Draws(int n) => Enumerable.Range(0, n).Select(_ => R.NextDouble());

    [Fact]
    public void RisenPaceSpreadsSeventeenPercentAboutItsOwn()
    {
        var risen = Enemies.Get("risen");
        Assert.Equal(0.17, risen.Spread);
        var paces = Draws(4000).Select(r => Vary.Pace(r, risen.Spread!.Value)).ToList();
        Assert.InRange(paces.Min(), 0.83, 0.85);
        Assert.InRange(paces.Max(), 1.15, 1.17);
        Assert.InRange(paces.Average(), 0.99, 1.01);  // the pack's mean pace is the kind's: no balance change
        Assert.Equal(1 - 0.08, Vary.Pace(0, 0.08), 9);  // the others keep the old +-8%
        Assert.Equal(1 + 0.08, Vary.Pace(1, 0.08), 9);
    }

    [Fact]
    public void RisenSizeSpreadsEightPercentAndDoesNotTrackPace()
    {
        var seeds = Draws(4000).ToList();
        var sizes = seeds.Select(s => Vary.Size(s, 0.08)).ToList();
        Assert.True(sizes.All(x => x >= 0.92 - 1e-9 && x <= 1.08 + 1e-9));
        Assert.InRange(sizes.Min(), 0.92, 0.925);
        Assert.InRange(sizes.Max(), 1.075, 1.08);
        Assert.InRange(sizes.Average(), 0.99, 1.01);
        // (a seed's size is not its pace's draw: the two read from the same stream)
        double mx = seeds.Average(), my = sizes.Average();
        double cov = seeds.Zip(sizes, (a, b) => (a - mx) * (b - my)).Average();
        double corr = cov / Math.Sqrt(seeds.Average(a => (a - mx) * (a - mx)) * sizes.Average(b => (b - my) * (b - my)));
        Assert.InRange(corr, -0.1, 0.1);
        Assert.Equal(1, Vary.Size(0.5, 0));
        Assert.Null(Enemies.Get("risen_warrior").Size);  // the folk-sized and the rest keep their one size
    }

    [Fact]
    public void WeaveStaysWithinItsDegreesAndDiffersCopyToCopy()
    {
        double lim = 16 * Math.PI / 180 + 1e-9;
        var a = Enumerable.Range(0, 600).Select(i => Vary.Weave(i * 0.05, 0.123, 16)).ToList();
        var b = Enumerable.Range(0, 600).Select(i => Vary.Weave(i * 0.05, 0.789, 16)).ToList();
        Assert.True(a.All(x => Math.Abs(x) <= lim) && b.All(x => Math.Abs(x) <= lim));
        Assert.True(a.Max() - a.Min() > 10 * Math.PI / 180);  // it really weaves
        Assert.True(a.Zip(b, (x, y) => Math.Abs(x - y)).Average() > 4 * Math.PI / 180);  // two copies are not in step
    }

    [Fact]
    public void ApartTakesTwoWalkersOutToTheGap()
    {
        // (both sides take their half: the centres end Gap apart)
        var (ax, az) = FolkSpacing.Apart(0, 0, 0.5, 0, 0.5);
        var (bx, bz) = FolkSpacing.Apart(0.5, 0, 0, 0, 0.5);
        Assert.Equal(FolkSpacing.Gap, (0.5 + bx) - ax, 6);
        Assert.Equal(0, az + bz, 9);
        Assert.Equal((0.0, 0.0), FolkSpacing.Apart(0, 0, 1.0, 0, 0.5));
        // (one at a stall holds; the walker steps the whole way round)
        Assert.Equal(0, FolkSpacing.Share(true, false));
        Assert.Equal(1, FolkSpacing.Share(false, true));
        var (cx, _) = FolkSpacing.Apart(0, 0, 0.3, 0, FolkSpacing.Share(false, true));
        Assert.Equal(-0.6, cx, 6);
        // (coincident: parted along the walker's own tie)
        var (tx, tz) = FolkSpacing.Apart(1, 1, 1, 1, 0.5, 0, 1);
        Assert.Equal(0, tx, 9); Assert.Equal(FolkSpacing.Gap / 2, tz, 9);
    }

    [Fact]
    public void SomeoneWhereSheArrivesIsMovedOutToHerRoom()
    {
        // (a townswoman 0.3 m from her spawn takes the whole move: out to 1.5 m, along the line from her)
        var (mx, mz) = FolkSpacing.Apart(0.3, 0, 0, 0, 1, 1, 0, FolkSpacing.HerRoom);
        Assert.Equal(FolkSpacing.HerRoom, 0.3 + mx, 9); Assert.Equal(0, mz, 9);
        Assert.Equal((0.0, 0.0), FolkSpacing.Apart(1.6, 0, 0, 0, 1, 1, 0, FolkSpacing.HerRoom));
        Assert.True(FolkSpacing.HerRoom >= 1.5);
    }

    [Fact]
    public void ThreeWalkersSqueezedTogetherSettleAtTheGap()
    {
        // (three on one lane in lockstep, a hand's breadth apart, as the judge saw them: a few frames of Apart)
        var p = new[] { (X: 0.0, Z: 0.0), (X: 0.2, Z: 0.05), (X: 0.35, Z: -0.05) };
        for (int it = 0; it < 30; it++)
            for (int i = 0; i < p.Length; i++)
                for (int j = 0; j < p.Length; j++)
                {
                    if (i == j) continue;
                    var (mx, mz) = FolkSpacing.Apart(p[i].X, p[i].Z, p[j].X, p[j].Z, 0.5, Math.Cos(i * 2.399), Math.Sin(i * 2.399));
                    p[i] = (p[i].X + mx, p[i].Z + mz);
                }
        double least = double.MaxValue;
        for (int i = 0; i < p.Length; i++)
            for (int j = i + 1; j < p.Length; j++)
                least = Math.Min(least, Math.Sqrt(Math.Pow(p[i].X - p[j].X, 2) + Math.Pow(p[i].Z - p[j].Z, 2)));
        Assert.True(least >= FolkSpacing.Gap - 0.02, $"least spacing {least:0.000}");
    }

    [Fact]
    public void SomeoneAheadIsPassedNotTailed()
    {
        // (walking +Z; someone 1 m ahead, 0.1 m off my line at +X)
        var (sx, sz, cap) = FolkSpacing.Ahead(0, 0, 0, 1, 0.1, 1.0, 0, 1.4);
        Assert.True(sx < 0);  // they are at +X of my line: I turn toward -X
        Assert.Equal(0, sz, 9);
        Assert.Equal(1.4 * 0.9, cap, 9);  // never at their heels at their pace
        var (_, _, none) = FolkSpacing.Ahead(0, 0, 0, 1, 0, -1, 0, 1.4);  // behind me
        Assert.True(double.IsPositiveInfinity(none));
        var (wx, _, wide) = FolkSpacing.Ahead(0, 0, 0, 1, 1.2, 1, 0, 1.4);  // well to the side
        Assert.True(double.IsPositiveInfinity(wide) && wx == 0);
        var (_, _, still) = FolkSpacing.Ahead(0, 0, 0, 1, 0, 1, 0, 0);  // standing: go round, no cap
        Assert.True(double.IsPositiveInfinity(still));
    }

    [Fact]
    public void StoopsAndCompanions()
    {
        Assert.True(FolkSpacing.BendsOver("Interact") && FolkSpacing.BendsOver("PickUp"));
        Assert.False(FolkSpacing.BendsOver("Cheer") || FolkSpacing.BendsOver("Wave"));
        Assert.Equal(0.35, FolkSpacing.Lag(0), 9);
        Assert.Equal(0.8, FolkSpacing.Lag(1), 9);
    }
}
