using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Tests.Explorer;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The story played by a bot (Explorer/StoryExplorer.cs): every
/// choice it can reach, through the game's own logic, looking for the story
/// stuck, contradicting itself, or asking for what cannot be. A quick run
/// goes with every `dotnet test`; the whole of it, every calling and
/// background through the prologue, with STORY_EXPLORE=full (and
/// STORY_EXPLORE_OUT a file to write the report to). How to read it:
/// docs/cloud/story-explorer.md.</summary>
public class StoryExplorerTests(ITestOutputHelper log)
{
    /// <summary>Findings known and accepted, each with why. A key ending in
    /// '*' accepts every finding that starts with it.</summary>
    static readonly (string Key, string Why)[] Accepted =
    [
    ];

    static string? Why(Finding f) =>
        Accepted.FirstOrDefault(a => a.Key.EndsWith('*') ? f.Key.StartsWith(a.Key[..^1], StringComparison.Ordinal) : a.Key == f.Key).Why;

    /// <summary>Gates nobody explored got through, though the content could
    /// add up to them ("unseen"), are reported and never fail. Claims about every road (a gate never met, a quest that never
    /// moves, a thing never got back): only the whole run makes them.</summary>
    static bool Searched(Finding f) => f.Kind is "gate" or "softlock" || f.Key.StartsWith("contradiction:gone:") || f.Key.EndsWith(":loop");

    static Options Quick() => new()
    {
        Roots = [new Root("warden", "hunter", Sex.Male), new Root("arcanist", "scholar", Sex.Female)],
        MaxStates = 220, Beam = 5, MaxDay = 4, Confirm = 0,
    };

    static Options Full()
    {
        var o = new Options
        {
            MaxStates = int.Parse(Environment.GetEnvironmentVariable("STORY_STATES") ?? "6000"),
            Beam = int.Parse(Environment.GetEnvironmentVariable("STORY_BEAM") ?? "16"),
            MaxDay = 8, Prologue = true, Confirm = 1500,
        };
        foreach (var c in Callings.Archetypes.Keys)
            foreach (var b in Callings.Backgrounds.Keys)
                o.Roots.Add(new Root(c, b, (c.Length + b.Length) % 2 == 0 ? Sex.Female : Sex.Male));
        return o;
    }

    void Tell(StoryExplorer x)
    {
        log.WriteLine($"{x.Nodes.Count} states, {x.Expanded} expanded, deepest {x.Nodes.Max(n => n.Depth)}, {x.Clock.Elapsed.TotalSeconds:0.0} s");
        foreach (var l in Reporting.Lines(x)) log.WriteLine($"  {l.Reached}/{l.Of} {l.What}");
        foreach (var f in x.Findings.Values) log.WriteLine($"[{f.Kind}{(Why(f) != null ? ", accepted" : "")}] {f.Key}: {f.Text} ({f.Root})\n{f.Replay}\n");
    }

    static List<string> New(StoryExplorer x, bool whole) => x.Findings.Values
        .Where(f => Why(f) == null && f.Kind != "unseen" && (whole || !Searched(f)))
        .Select(f => $"[{f.Kind}] {f.Text} ({f.Root}; {f.Trace.Count} steps; the replay is in the test output)").ToList();

    [Fact]
    public void A_quick_play_of_the_story_finds_nothing_new()
    {
        var x = new StoryExplorer(Quick()).Run();
        Tell(x);
        // The bot is still playing: it talks, walks, travels and gets somewhere.
        var lines = Reporting.Lines(x).ToDictionary(l => l.What);
        Assert.True(lines["Conversations started"].Reached >= 10, "the explorer hardly talked to anyone");
        Assert.True(lines["Dialogue nodes reached"].Reached >= 60, "the explorer reached few dialogue nodes");
        Assert.True(lines["Journal lines written"].Reached >= 15, "the explorer wrote few journal lines");
        Assert.Empty(New(x, false));
    }

    [Fact]
    public void What_the_explorer_reaches_is_what_playing_the_steps_reaches()
    {
        // Its short cuts (one zone tried many ways, a visit found fresh again,
        // a conversation without its zone) come to what doing the steps one
        // after another comes to, so every trace in the report replays.
        var x = new StoryExplorer(new Options { Roots = [new Root("stalker", "outcast", Sex.Female)], MaxStates = 120, Beam = 4, MaxDay = 3, Confirm = 0, Keep = true }).Run();
        var some = x.Nodes.Where(n => n.Mode == Mode.Roam).OrderByDescending(n => n.Depth).Take(3)
            .Concat(x.Nodes.Where(n => n.Mode == Mode.Talk).OrderByDescending(n => n.Depth).Take(2)).ToList();
        Assert.True(some.Count >= 3);
        foreach (var n in some)
        {
            var (_, canon) = x.Replay(n.Root, n.Trace());
            Assert.Equal(StoryExplorer.Canon(Playthrough.Load(n.Save)), canon);
        }
    }

    [Fact]
    public void Probe()
    {
        if (Environment.GetEnvironmentVariable("STORY_PROBE") is not { } n) return;
        var o = Full();
        o.Roots = o.Roots.Take(int.Parse(Environment.GetEnvironmentVariable("STORY_ROOTS") ?? "1")).ToList();
        o.MaxStates = int.Parse(n);
        var x = new StoryExplorer(o).Run();
        Tell(x);
    }

    [Fact]
    public void The_whole_story_explored_finds_nothing_new()
    {
        if (Environment.GetEnvironmentVariable("STORY_EXPLORE") != "full") return;
        var x = new StoryExplorer(Full()).Run();
        Tell(x);
        if (Environment.GetEnvironmentVariable("STORY_EXPLORE_OUT") is { Length: > 0 } path) File.WriteAllText(path, Reporting.Markdown(x, Why));
        foreach (var (key, _) in Accepted.Where(a => !x.Findings.Values.Any(f => Why(f) == a.Why)))
            log.WriteLine($"accepted, and no longer found: {key}");
        Assert.Empty(New(x, true));
    }
}
