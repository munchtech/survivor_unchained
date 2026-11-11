using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Balance;

public sealed record DensityWindow(double Start, double End, int Kills, double KillsPerMinute);
public sealed record DensitySpan(double Start, double End)
{
    public double Seconds => End - Start;
}
public sealed record DensityStats(int Count, double? Median, double? P90, double? Max)
{
    public static DensityStats Of(IEnumerable<double> values)
    {
        var s = values.OrderBy(x => x).ToArray();
        int n = s.Length;
        return n == 0 ? new(0, null, null, null) : new(n,
            n % 2 == 1 ? s[n / 2] : (s[n / 2 - 1] + s[n / 2]) / 2,
            s[(int)Math.Ceiling(n * 0.9) - 1], s[^1]);
    }
}
public sealed class DensityPack(string id)
{
    public string Id { get; } = id;
    public bool Elite { get; set; }
    public bool Cleared { get; set; }
    public double? FirstHit { get; set; }
    public double? LastKill { get; set; }
    public int Kills { get; set; }
}
public sealed record DensityGap(string From, string To, double LastKill, double FirstHit, bool AfterElite)
{
    // Negative gaps preserve overlapping fights instead of disguising them as lulls.
    public double Seconds => FirstHit - LastKill;
}
public sealed record DensityMeasures(double Seconds, int Kills, double KillsPerMinute,
    List<DensityWindow> Windows, DensityStats PackGapSeconds, DensityStats EliteIntervalSeconds,
    DensityStats AfterEliteGapSeconds, DensitySpan? LongestNoEnemy, List<DensityGap> Gaps,
    List<double> EliteIntervals, List<DensityPack> Packs, List<double> KillTimes, int UngroupedKills);

/// <summary>Only observations enter this recorder. It never changes a fight.</summary>
public sealed class DensityRecorder
{
    readonly Dictionary<string, DensityPack> packs = new();
    readonly List<double> kills = new();
    readonly List<DensitySpan> empty = new();
    double? emptyAt;
    double lastSample;
    bool sampled;
    int ungrouped;

    public DensityPack Pack(string id) => packs.TryGetValue(id, out var p) ? p : packs[id] = new(id);
    public void Hit(double time, string? pack)
    {
        if (pack == null) return;
        var p = Pack(pack);
        p.FirstHit = p.FirstHit is { } t ? Math.Min(t, time) : time;
    }
    public void Kill(double time, string? pack, bool byPlayer = true)
    {
        if (byPlayer) { kills.Add(time); if (pack == null) ungrouped++; }
        if (pack == null) return;
        var p = Pack(pack);
        p.LastKill = p.LastKill is { } t ? Math.Max(t, time) : time;
        if (byPlayer) p.Kills++;
    }
    public void Sample(double time, bool enemyInRange)
    {
        if (!double.IsFinite(time) || time < 0 || sampled && time < lastSample)
            throw new ArgumentOutOfRangeException(nameof(time));
        sampled = true;
        lastSample = time;
        if (!enemyInRange) emptyAt ??= time;
        else if (emptyAt is { } start) { empty.Add(new(start, time)); emptyAt = null; }
    }
    public DensityMeasures Finish(double seconds)
    {
        if (!double.IsFinite(seconds) || seconds < 0 || seconds < lastSample || kills.Any(t => t < 0 || t > seconds))
            throw new ArgumentOutOfRangeException(nameof(seconds));
        var windows = new List<DensityWindow>();
        int count = (int)Math.Ceiling(seconds / 30);
        var counts = new int[count];
        foreach (double t in kills)
            // The terminal instant belongs to the last nonempty-duration window.
            if (count > 0) counts[Math.Min(count - 1, (int)Math.Floor((t + 1e-8) / 30))]++;
        for (int i = 0; i < count; i++)
        {
            double end = Math.Min(seconds, (i + 1) * 30);
            windows.Add(new(i * 30, end, counts[i], counts[i] * 60 / (end - i * 30)));
        }
        var met = packs.Values.Where(p => p.FirstHit != null).OrderBy(p => p.FirstHit).ThenBy(p => p.Id, StringComparer.Ordinal).ToList();
        var gaps = new List<DensityGap>();
        for (int i = 1; i < met.Count; i++)
            if (met[i - 1] is { Cleared: true, LastKill: { } last })
                gaps.Add(new(met[i - 1].Id, met[i].Id, last, met[i].FirstHit!.Value, met[i - 1].Elite));
        var elites = met.Where(p => p.Elite).Select(p => p.FirstHit!.Value).ToArray();
        var intervals = elites.Skip(1).Select((t, i) => t - elites[i]).ToList();
        var spans = emptyAt is { } tail ? empty.Append(new DensitySpan(tail, seconds)) : empty;
        return new(seconds, kills.Count, seconds > 0 ? kills.Count * 60 / seconds : 0,
            windows, DensityStats.Of(gaps.Select(g => g.Seconds)), DensityStats.Of(intervals),
            DensityStats.Of(gaps.Where(g => g.AfterElite).Select(g => g.Seconds)), spans.MaxBy(s => s.Seconds),
            gaps, intervals, packs.Values.OrderBy(p => p.Id, StringComparer.Ordinal).ToList(), kills.OrderBy(t => t).ToList(), ungrouped);
    }
}
