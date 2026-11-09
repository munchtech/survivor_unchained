using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* Each calling's taught build in Act 1 (data/content/taught_builds.json; ARPG.md 3.1, the hands rule): the grip, the six
 * keys with their cast forms and the level each is taught at, what comes later, the first Union. The tutorial and the lamp
 * offer read it (M6/M7); Battle.SetForm puts a cast on a carried skill. */
public sealed class TaughtSlot
{
    public string Skill = "", Cast = "";
    public int Level = 1;
}

public sealed class TaughtUnion
{
    public string Id = "", Note = "";
}

public sealed class TaughtBuild
{
    public string Grip = "";
    public List<TaughtSlot> Slots = new();
    public string[] Later = System.Array.Empty<string>();
    public TaughtUnion? Union;
}

public static class TaughtBuilds
{
    static Dictionary<string, TaughtBuild>? all;

    /// <summary>The taught builds by calling ("_" keys are notes).</summary>
    public static IReadOnlyDictionary<string, TaughtBuild> All => all ??= Parse(Json.ReadContent("taught_builds.json"));

    public static Dictionary<string, TaughtBuild> Parse(string json)
    {
        var d = new Dictionary<string, TaughtBuild>();
        foreach (var (k, v) in JsonNode.Parse(json)!.AsObject())
            if (!k.StartsWith('_') && v != null) d[k] = v.Deserialize<TaughtBuild>(Json.Options)!;
        return d;
    }

    public static TaughtBuild? Of(string? calling) => calling != null && All.TryGetValue(calling, out var t) ? t : null;

    /// <summary>A build's pressed keys: its slots whose cast is press or channel (the grip, a hold, is not counted).</summary>
    public static int PressedSlots(TaughtBuild t) => t.Slots.Count(s => s.Skill != t.Grip && s.Cast is "press" or "channel");

    /// <summary>The taught forms on what she carries (campaign: a skill without its record is left as it is). The skills
    /// set, by id.</summary>
    public static List<string> Apply(Battle b, string? calling)
    {
        var set = new List<string>();
        if (Of(calling) is not { } t) return set;
        foreach (var s in t.Slots) if (b.SetForm(s.Skill, s.Cast)) set.Add(s.Skill);
        return set;
    }
}
