using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace SurvivorUnchained.Core;

/// <summary>One in-game bug report: report.json beside shot.png, clip.avi, the log and the save.</summary>
public sealed class BugReport
{
    public string? Title { get; set; }
    public string? Description { get; set; }
    public string? Tester { get; set; }
    public int Number { get; set; }
    public string? Build { get; set; }
    public string? Sha { get; set; }
    public string? Flavor { get; set; }
    public string? TimeLocal { get; set; }
    public string? TimeUtc { get; set; }
    public string? Zone { get; set; }
    public string? ZoneName { get; set; }
    public long? Seed { get; set; }
    public string? Mode { get; set; }
    public int? Level { get; set; }
    public double? X { get; set; }
    public double? Y { get; set; }
    public double? Z { get; set; }
    public int? DenClears { get; set; }
    public string? Os { get; set; }
    public string? Cpu { get; set; }
    public string? Gpu { get; set; }
    public string? GpuDriver { get; set; }
    public string? Ram { get; set; }
    public string? Screen { get; set; }
    public string? Renderer { get; set; }
    public double? FrameMsAvg { get; set; }
    public double? FrameMsP99 { get; set; }
    public double? FrameMsMax { get; set; }
    public int ClipFrames { get; set; }
    public double ClipFps { get; set; }
    public double ClipSeconds { get; set; }
    public List<string> Files { get; set; } = new();
    public Dictionary<string, string> Extra { get; set; } = new();
}

public static class BugReports
{
    // Json.Options is camelCase; report.json is snake_case, so its own options.
    static readonly JsonSerializerOptions Opts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        WriteIndented = true,
        AllowTrailingCommas = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
    };

    static readonly Regex NamePattern = new(@"_BR(\d{4,})_", RegexOptions.Compiled);

    static string Clean(string? s, string fallback)
    {
        var sb = new StringBuilder();
        foreach (char c in s ?? "")
            sb.Append(c < 128 && char.IsAsciiLetterOrDigit(c) ? c : '-');
        string t = Regex.Replace(sb.ToString(), "-+", "-").Trim('-');
        if (t.Length > 24) t = t.Substring(0, 24).Trim('-');
        return t.Length == 0 ? fallback : t;
    }

    public static string FolderName(string tester, int number, DateTime local, string zone) =>
        $"{Clean(tester, "tester")}_BR{number:0000}_{local.ToString("yyyyMMdd-HHmm", CultureInfo.InvariantCulture)}_{Clean(zone, "title")}";

    public static int NextNumber(IEnumerable<string> existingFolderNames)
    {
        int max = 0;
        foreach (var n in existingFolderNames)
        {
            var m = NamePattern.Match(n ?? "");
            if (m.Success && int.TryParse(m.Groups[1].Value, out int v)) max = Math.Max(max, v);
        }
        return max + 1;
    }

    public static string ToJson(BugReport r) => JsonSerializer.Serialize(r, Opts);

    public static BugReport FromJson(string json) =>
        JsonSerializer.Deserialize<BugReport>(json, Opts) ?? throw new JsonException("no bug report in the JSON");

    public static (double Avg, double P99, double Max) FrameStats(IReadOnlyList<double> frameMs)
    {
        if (frameMs.Count == 0) return (0, 0, 0);
        var s = frameMs.OrderBy(x => x).ToList();
        int i = Math.Min(s.Count - 1, (int)Math.Ceiling(s.Count * 0.99) - 1);
        return (frameMs.Average(), s[Math.Max(0, i)], s[^1]);
    }
}
