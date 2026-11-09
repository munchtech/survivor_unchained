using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
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

    /// <summary>(M3) What a campaign survivor carries: each taught slot of a level up to `level` and past the levels already
    /// granted (CharacterData.TaughtUpTo) is learned and goes into the next free day slot, unless she already carries it (a
    /// slot she took off later is not put back). The carried taught skills then lead the day slots in the build's order (the
    /// grip on the first key). The skills newly carried, with their taught form.</summary>
    public static List<TaughtSlot> Grant(CharacterData ch, int level)
    {
        var got = new List<TaughtSlot>();
        if (Of(ch.Archetype) is not { } t || level <= ch.TaughtUpTo) return got;
        foreach (var s in t.Slots)
        {
            if (s.Level <= ch.TaughtUpTo || s.Level > level || !Weapons.All.ContainsKey(s.Skill) || !SkillBook.Carries(ch, s.Skill)) continue;
            if (!ch.Discovered.Contains(s.Skill)) ch.Discovered.Add(s.Skill);
            if (!ch.Skills.Contains(s.Skill)) ch.Skills.Add(s.Skill);
            if (ch.Slotted.Contains(s.Skill) || ch.Slotted.Count >= SkillBook.SlotsAt(level)) continue;
            ch.Slotted.Add(s.Skill);
            got.Add(s);
        }
        ch.TaughtUpTo = level;
        Order(ch, t);
        return got;
    }

    /// <summary>The build's carried skills first, in its order; the rest after, as they were.</summary>
    static void Order(CharacterData ch, TaughtBuild t)
    {
        int Rank(string id) { int i = t.Slots.FindIndex(s => s.Skill == id); return i < 0 ? int.MaxValue : i; }
        ch.Slotted = ch.Slotted.Select((id, i) => (id, i)).OrderBy(x => Rank(x.id)).ThenBy(x => x.i).Select(x => x.id).ToList();
    }

    /// <summary>A campaign fight's skills in key order: the taught build's (gear or learned) first in its order, then the
    /// rest as given (a worn skill the build does not name goes after it).</summary>
    public static List<(string Id, int Rank)> KeyOrder(string? calling, IEnumerable<(string Id, int Rank)> skills)
    {
        var list = skills.ToList();
        if (Of(calling) is not { } t) return list;
        int Rank(string id) { int i = t.Slots.FindIndex(s => s.Skill == id); return i < 0 ? int.MaxValue : i; }
        return list.Select((w, i) => (w, i)).OrderBy(x => Rank(x.w.Id)).ThenBy(x => x.i).Select(x => x.w).ToList();
    }
}
