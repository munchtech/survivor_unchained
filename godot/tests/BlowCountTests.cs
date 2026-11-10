using System;
using System.Collections.Generic;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Counts that take parts of a blow (Sim/Blows.cs; M3 MR 3: a chain's cut is a share of the written blow).</summary>
public sealed class BlowCountTests
{
    /// <summary>The firings (1-based) that complete the every-th blow: lights of weight w, a completing one counted at wHeavy.</summary>
    static List<int> Completing(int firings, int every, double w, double? wHeavy = null)
    {
        var at = new List<int>();
        int n = 0; double part = 0;
        for (int i = 1; i <= firings; i++)
        {
            bool heavy = Blows.Completes(n, part, every, w);
            if (heavy) at.Add(i);
            Blows.Count(ref n, ref part, heavy ? wHeavy ?? w : w);
        }
        return at;
    }

    [Fact]
    public void At_weight_one_it_is_the_whole_count()
    {
        for (int every = 1; every <= 6; every++)
            for (int n = 0; n <= 40; n++)
            {
                Assert.Equal((n + 1) % every == 0, Blows.Completes(n, 0, every, 1));
                int m = n; double part = 0;
                Blows.Count(ref m, ref part, 1);
                Assert.Equal((n + 1, 0.0), (m, part));
            }
        Assert.False(Blows.Completes(3, 0, 0, 1));
    }

    [Fact]
    public void Sunders_cuts_complete_every_fourth_blow_with_no_drift()
    {
        var at = Completing(1000, 4, 0.4375);
        Assert.Equal(new[] { 10, 19, 28, 37 }, at.GetRange(0, 4));
        Assert.Equal(109, at.Count);
        for (int k = 1; k < at.Count; k++) Assert.InRange(at[k] - at[k - 1], 9, 10);
    }

    [Fact]
    public void A_heavy_cut_counted_at_its_longer_share_brings_the_next_sooner()
    {
        Assert.Equal(new[] { 10, 18, 27, 36, 45, 54, 63, 72, 80 }, Completing(80, 4, 0.4375, 0.5625));
    }

    [Fact]
    public void Oathblades_cuts_complete_every_third_blow_with_no_drift()
    {
        Assert.InRange(Completing(3000, 3, 0.70 / 1.05).Count, 666, 667);
    }

    [Fact]
    public void A_chance_per_blow_compounds_over_the_cuts_of_a_blow()
    {
        double c = Blows.Chance(0.2, 0.4375);
        Assert.Equal(0.2, 1 - Math.Pow(1 - c, 1 / 0.4375), 12);
        Assert.Equal(1.0, Blows.Chance(1, 0.4375));
        Assert.Equal(0.0, Blows.Chance(0, 0.4375));
        Assert.Equal(0.37, Blows.Chance(0.37, 1));
    }
}
