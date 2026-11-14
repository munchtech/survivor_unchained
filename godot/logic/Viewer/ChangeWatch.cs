using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace SurvivorUnchained.Viewer;

/// <summary>A file as the watch sees it: its path, size and last write (ticks).</summary>
public readonly record struct FileStat(string Path, long Size, long Written);

/// <summary>Lists the files under the watched roots (recursively); a root that is a file lists itself, a missing root nothing.</summary>
public interface IFileStats
{
    IEnumerable<FileStat> List(string root);
}

/// <summary>
/// The live package's change detection: the files under its roots (sizes and write times), polled; a change is
/// handed on only once nothing has moved for StableSeconds (300 ms), so a glb still being written is never loaded.
/// Poll says when there is a settled change not yet replayed; Taken marks the snapshot it saw as replayed.
/// </summary>
public sealed class ChangeWatch
{
    readonly IFileStats stats;
    readonly string[] roots;
    public readonly double StableSeconds;
    string? seen, taken;
    double seenAt = double.NegativeInfinity;

    public ChangeWatch(IFileStats stats, IEnumerable<string> roots, double stableSeconds = 0.3)
    {
        this.stats = stats;
        this.roots = roots.ToArray();
        StableSeconds = stableSeconds;
    }

    public string Snapshot()
    {
        var sb = new StringBuilder();
        foreach (var r in roots)
            foreach (var f in stats.List(r).OrderBy(f => f.Path, StringComparer.Ordinal))
                sb.Append(f.Path).Append('|').Append(f.Size).Append('|').Append(f.Written).Append('\n');
        return sb.ToString();
    }

    /// <summary>True when the files differ from the last replayed and have stood still StableSeconds (now: seconds).</summary>
    public bool Poll(double now)
    {
        var s = Snapshot();
        if (s != seen) { seen = s; seenAt = now; return false; }
        return s != taken && now - seenAt >= StableSeconds;
    }

    /// <summary>The snapshot Poll last saw counts as replayed.</summary>
    public void Taken() => taken = seen;

    /// <summary>Forget what was replayed: the next settled poll fires again (F5).</summary>
    public void Again() => taken = null;

    /// <summary>When the files last moved (seconds, Poll's clock): the change-to-frame latency is measured from here.</summary>
    public double ChangedAt => seenAt;
}

/// <summary>The capture requests in requests/: ID.json files with no ID.done.json or ID.failed.json, settled
/// (unwritten for StableSeconds), oldest first.</summary>
public static class RequestQueue
{
    public static List<string> Pending(IEnumerable<FileStat> files, long nowTicks, double stableSeconds = 0.3)
    {
        var all = files.ToList();
        var names = new HashSet<string>(all.Select(f => System.IO.Path.GetFileName(f.Path)), StringComparer.OrdinalIgnoreCase);
        return all
            .Where(f => f.Path.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
            .Select(f => (f, id: System.IO.Path.GetFileNameWithoutExtension(f.Path)))
            .Where(x => !x.id.EndsWith(".done", StringComparison.OrdinalIgnoreCase) && !x.id.EndsWith(".failed", StringComparison.OrdinalIgnoreCase))
            .Where(x => !names.Contains(x.id + ".done.json") && !names.Contains(x.id + ".failed.json"))
            .Where(x => (nowTicks - x.f.Written) / (double)TimeSpan.TicksPerSecond >= stableSeconds)
            .OrderBy(x => x.f.Written).ThenBy(x => x.id, StringComparer.Ordinal)
            .Select(x => x.id).ToList();
    }
}
