using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Tests.Explorer;

/// <summary>Who the explorer plays: a calling, a background and who people
/// take the survivor for.</summary>
sealed record Root(string Calling, string Background, Sex Sex)
{
    public override string ToString() => $"{Calling}/{Background}/{Sex.ToString().ToLowerInvariant()}";
}

/// <summary>What the survivor is doing: walking about, in a conversation, or
/// in one of the screens a conversation opens.</summary>
enum Mode { Roam, Talk, Shop, Rest, Maps, Arena }

/// <summary>One thing done, as the explorer names it (and replays it): the
/// key it is chosen by, and words for a person reading the trace.</summary>
sealed record Step(string Key, string Words);

/// <summary>The steps since a zone was entered, shared tail-first between a
/// state and everything explored from it.</summary>
sealed class Steps
{
    public readonly Step Step;
    public readonly Steps? Before;
    public readonly int Count;

    public Steps(Step step, Steps? before) { Step = step; Before = before; Count = (before?.Count ?? 0) + 1; }

    public static IEnumerable<Step> List(Steps? s)
    {
        var all = new List<Step>();
        for (; s != null; s = s.Before) all.Add(s.Step);
        all.Reverse();
        return all;
    }
}

/// <summary>Where a zone visit stands: the zone, how it was entered, the
/// journey as it was then, and what has been done since. Replaying that
/// rebuilds the zone exactly, the things a zone keeps only while you are in
/// it (a cage opened, a camp roused) with it.</summary>
sealed record Visit(string Zone, string? From, (double X, double Z, double Facing)? At, string EntrySave, Steps? Done, string ZoneMark);

/// <summary>A state the explorer has reached.</summary>
sealed class Node
{
    public int Id;
    public Node? Parent;
    public Step? Step;
    public int Depth;
    /// <summary>How far into the story: journal lines, things known, words the world keeps.</summary>
    public int Progress;
    /// <summary>The zone's own progress (Playthrough.Flags), while in it.</summary>
    public string Flags = "";
    public Root Root = null!;
    /// <summary>The journey, saved.</summary>
    public string Save = "";
    public Mode Mode;
    /// <summary>In a conversation: with whom, at which node. In a shop: whose.</summary>
    public string? Npc, At;
    /// <summary>In an arena: the arena (JSON).</summary>
    public string? Arena;
    public Visit Visit = null!;
    public string Hash = "";
    public bool Expanded;
    public readonly List<int> Next = new();
    /// <summary>Each quest's place: its status and journal, as a word.</summary>
    public Dictionary<string, string> Quests = new();
    public string[] Held = Array.Empty<string>();
    /// <summary>Items a choice on show asked for and the survivor lacked.</summary>
    public HashSet<string>? Wants;

    public List<Step> Trace()
    {
        var list = new List<Step>();
        for (var n = this; n?.Step != null; n = n.Parent) list.Add(n.Step);
        list.Reverse();
        return list;
    }

    public string Where => Mode switch
    {
        Mode.Talk => $"{Visit.Zone}, talking to {Npc} at {At}",
        Mode.Shop => $"{Visit.Zone}, {Npc}'s wares",
        Mode.Arena => $"{Visit.Zone}, pulled into an arena",
        _ => $"{Visit.Zone} ({Mode.ToString().ToLowerInvariant()})",
    };
}

/// <summary>Something wrong with the story, found by playing it.</summary>
sealed record Finding(string Kind, string Key, string Text, string File, Root Root, List<Step> Trace)
{
    /// <summary>The step-by-step way to it, for the report and for replay.</summary>
    public string Replay => Trace.Count == 0 ? "(at the start)" : string.Join("\n", Trace.Select((s, i) => $"{i + 1}. {s.Words}"));
}
