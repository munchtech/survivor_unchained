using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests.Explorer;

/// <summary>The most a person's feeling can ever be, read from the content:
/// where they start (the best background for it), and everything that raises
/// it. A raise that can come again (a choice not once-only, a daily rule, a
/// zone script's) makes it unbounded; deeds count once each, for whoever
/// takes them personally and for everyone who hears.</summary>
static class Most
{
    static Dictionary<(string, Axis), double>? bounded;
    static HashSet<(string, Axis)>? endless;
    static readonly Axis[] Axes = [Axis.Trust, Axis.Affection, Axis.Respect, Axis.Fear];

    public static double Of(string npc, Axis axis)
    {
        Read();
        if (endless!.Contains((npc, axis)) || endless.Contains(("*", axis))) return double.PositiveInfinity;
        double start = Callings.Backgrounds.Values.Select(b => b.Npc.TryGetValue(npc, out var f) ? f.Of(axis) ?? 0 : 0).DefaultIfEmpty(0).Max();
        return Math.Min(100, Math.Max(0, start) + bounded!.GetValueOrDefault((npc, axis)) + bounded!.GetValueOrDefault(("*", axis)));
    }

    static void Read()
    {
        if (bounded != null) return;
        bounded = new(); endless = new();
        var deeds = new HashSet<string>();
        void Add(string npc, Axis a, double v, bool again)
        {
            if (v <= 0) return;
            if (again) endless!.Add((npc, a));
            else bounded![(npc, a)] = bounded.GetValueOrDefault((npc, a)) + v;
        }
        void Feel(string npc, Feel? f, bool again) { if (f != null) foreach (var a in Axes) Add(npc, a, f.Of(a) ?? 0, again); }
        void E(IEnumerable<Change>? es, bool again)
        {
            foreach (var e in es ?? Enumerable.Empty<Change>())
            {
                if (e.Rel != null) Feel(e.Rel.Npc, e.Rel, again);
                if (e.History is { } h && deeds.Add(h.Id))
                {
                    Feel("*", h.Sentiment, false);
                    foreach (var (who, f) in h.Reactions ?? new()) Feel(who, f, false);
                }
                E(e.Then, again); E(e.Else, again);
                if (e.Later != null) E(e.Later.Effect, again);
            }
        }
        foreach (var c in Dialogue.All.Values)
            foreach (var n in c.Nodes.Values)
            {
                E(n.Effects, true);
                foreach (var ch in n.Choices ?? new()) E(ch.Effects, ch.Once == null);
            }
        foreach (var r in Simulation.DailyRules) E(r.Effect, !r.Once);
        // The zone scripts' embedded changes: whatever they raise, counted as able to come again.
        var logic = Path.GetFullPath(Path.Combine(DataFiles.Dir, "..", "logic"));
        foreach (var f in Directory.EnumerateFiles(logic, "*.cs", SearchOption.AllDirectories))
        {
            var t = File.ReadAllText(f);
            foreach (Match m in Regex.Matches(t, @"""(\w+)""\s*:\s*\{([^{}]*)\}"))
            {
                var who = m.Groups[1].Value;
                var body = m.Groups[2].Value;
                if (who == "rel" && Regex.Match(body, @"""npc""\s*:\s*""(\w+)""") is { Success: true } rn) who = rn.Groups[1].Value;
                else if (who == "sentiment") who = "*";
                foreach (var a in Axes)
                    foreach (Match v in Regex.Matches(body, $@"""{a.ToString().ToLowerInvariant()}""\s*:\s*([^,}}\s]+)"))
                        if (!double.TryParse(v.Groups[1].Value, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var d) || d > 0)
                            Add(who, a, 1, true);
            }
        }
    }
}
