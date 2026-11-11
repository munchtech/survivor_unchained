using System;
using System.Linq;
using SurvivorUnchained.Balance;
using Xunit;

namespace SurvivorUnchained.Tests;

public class DensityRecorderTests
{
    [Fact]
    public void Scripted_timeline_measures_rhythm_and_the_terminal_empty_stretch()
    {
        var r = new DensityRecorder();
        void Pack(string id, bool elite, double hit, params double[] kills)
        {
            r.Pack(id).Elite = elite;
            r.Hit(hit, id);
            foreach (double t in kills) r.Kill(t, id);
            r.Pack(id).Cleared = true;
        }
        Pack("a", false, 0, 5, 10);
        Pack("b", true, 16, 20, 25);
        Pack("c", false, 30, 35);
        Pack("d", true, 80, 85);
        Pack("e", false, 150, 155);
        Pack("f", true, 160, 170);
        r.Hit(18, "b");
        r.Sample(0, false); r.Sample(5, true); r.Sample(20, false); r.Sample(30, true);
        r.Sample(90, false); r.Sample(150, true); r.Sample(175, false);
        var d = r.Finish(180);
        Assert.Equal(8, d.Kills);
        Assert.Equal(8 / 3.0, d.KillsPerMinute, 9);
        Assert.Equal(new[] { 4, 1, 1, 0, 0, 2 }, d.Windows.Select(w => w.Kills));
        Assert.Equal(new[] { 6.0, 5, 45, 65, 5 }, d.Gaps.Select(g => g.Seconds));
        Assert.Equal(new DensityStats(5, 6, 65, 65), d.PackGapSeconds);
        Assert.Equal(new[] { 64.0, 80 }, d.EliteIntervals);
        Assert.Equal(new DensityStats(2, 72, 80, 80), d.EliteIntervalSeconds);
        Assert.Equal(new DensityStats(2, 35, 65, 65), d.AfterEliteGapSeconds);
        Assert.Equal(new DensitySpan(90, 150), d.LongestNoEnemy);
    }

    [Fact]
    public void Window_boundaries_and_partial_window_use_their_actual_duration()
    {
        var r = new DensityRecorder();
        foreach (double t in new[] { 0.0, 29.999, 30, 60, 75 }) r.Kill(t, null);
        var d = r.Finish(75);
        Assert.Equal(new[] { 2, 1, 2 }, d.Windows.Select(w => w.Kills));
        Assert.Equal(new[] { 4.0, 2, 8 }, d.Windows.Select(w => w.KillsPerMinute));
        Assert.Equal(4.0, d.KillsPerMinute);
        Assert.Equal(5, d.UngroupedKills);
        var full = new DensityRecorder(); full.Kill(60, null);
        Assert.Equal(new[] { 0, 1 }, full.Finish(60).Windows.Select(w => w.Kills));
    }

    [Fact]
    public void Overlaps_are_signed_and_uncleared_packs_do_not_claim_a_final_kill()
    {
        var r = new DensityRecorder();
        r.Hit(0, "a"); r.Kill(20, "a"); r.Pack("a").Cleared = true;
        r.Hit(10, "b"); r.Kill(15, "b");
        r.Hit(30, "c");
        var d = r.Finish(40);
        Assert.Single(d.Gaps);
        Assert.Equal(-10.0, d.PackGapSeconds.Median);
        Assert.Null(d.EliteIntervalSeconds.Median);
    }

    [Fact]
    public void No_kills_no_elites_and_zero_duration_are_finite_and_unpaired()
    {
        var r = new DensityRecorder();
        r.Sample(0, false);
        var d = r.Finish(0);
        Assert.Equal(0.0, d.KillsPerMinute);
        Assert.Empty(d.Windows);
        Assert.Equal(new DensityStats(0, null, null, null), d.PackGapSeconds);
        Assert.Null(d.EliteIntervalSeconds.Max);
        Assert.Null(d.AfterEliteGapSeconds.Max);
        Assert.Equal(12, r.Finish(12).LongestNoEnemy!.Seconds);
    }

    [Fact]
    public void Cleanup_deaths_set_pack_end_without_inflating_player_kills()
    {
        var r = new DensityRecorder();
        r.Hit(0, "a"); r.Kill(1, "a"); r.Kill(3, "a", byPlayer: false);
        r.Pack("a").Cleared = true; r.Hit(8, "b");
        var d = r.Finish(10);
        Assert.Equal(1, d.Kills);
        Assert.Equal(5.0, d.PackGapSeconds.Max);
    }

    [Fact]
    public void Percentile_is_nearest_rank_and_samples_must_be_monotonic()
    {
        Assert.Equal(new DensityStats(10, 5.5, 9, 10), DensityStats.Of(Enumerable.Range(1, 10).Select(i => (double)i)));
        var r = new DensityRecorder(); r.Sample(5, true);
        Assert.Throws<ArgumentOutOfRangeException>(() => r.Sample(4, false));
        Assert.Throws<ArgumentOutOfRangeException>(() => r.Finish(4));
    }
}
