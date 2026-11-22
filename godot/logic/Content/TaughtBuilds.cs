using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* Each calling's taught build in Act 1 (data/content/taught_builds.json; BUILD_DIRECTION.md rounds 7-8, BUILD_UNLOCKS.md;
 * the hands rule): the four pressed keys (the basic attack held in the first), each with its cast form and the
 * level it is taught at; the stance her second weapon set opens at; what comes later; the first Union. The tutorial and
 * the lamp offer read it (M6/M7). */
public sealed class TaughtSlot
{
    public string Skill = "", Cast = "";
    public int Level = 1;
}

public sealed class TaughtUnion
{
    public string Id = "", Note = "";
}

/// <summary>(bd-keys) The second weapon set: the level it opens at (the ladder's), the stance she takes up then unless she
/// chose another, and those her calling is offered (data/content/stances.json ids).</summary>
public sealed class TaughtStance
{
    public int Level = 8;
    public string Default = "";
    public string[] Offers = System.Array.Empty<string>();
}

public sealed class TaughtBuild
{
    /// <summary>The basic attack: the first key's skill.</summary>
    public string Grip = "";
    /// <summary>The keys in key order.</summary>
    public List<TaughtSlot> Keys = new();
    public TaughtStance? Stance;
    public string[] Later = System.Array.Empty<string>();
    public TaughtUnion? Union;

    /// <summary>Every taught skill in the order the ladder opens them (key order on a level they share).</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public List<TaughtSlot> Slots => Keys.OrderBy(s => s.Level).ToList();
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

    /// <summary>The calling a build belongs to (null when it is none of them).</summary>
    public static string? CallingOf(TaughtBuild? build) => build == null ? null : All.FirstOrDefault(kv => ReferenceEquals(kv.Value, build)).Key;

    public static TaughtBuild? Of(string? calling) => calling != null && All.TryGetValue(calling, out var t) ? t : null;

    /// <summary>A build's pressed keys: its keys whose cast is press or channel (the basic attack, a hold, is not counted).</summary>
    public static int PressedSlots(TaughtBuild t) => t.Keys.Count(s => s.Skill != t.Grip && s.Cast is "press" or "channel");

    /// <summary>The bar's shape this code carries (CharacterData.Bar): five pressed keys (3 was four pressed keys; 2 was four keys and three auto slots).</summary>
    public const int BarShape = 4;

    /// <summary>(M3; bd-keys) What a campaign survivor carries: each taught key of a level up to `level` and
    /// past the levels already granted (CharacterData.TaughtUpTo) is learned and goes into the next free key, unless she
    /// already carries it (a skill she took off or swapped out later is not put back). A save from an older bar is re-cut
    /// once: her carried skills and every layout's are cleared and the build is granted again into the five keys. The
    /// skills newly carried, with their taught form.</summary>
    public static List<TaughtSlot> Grant(CharacterData ch, int level)
    {
        var got = new List<TaughtSlot>();
        if (Of(ch.Archetype) is not { } t) return got;
        bool recut = false;
        var had = new HashSet<string>();
        if (ch.Bar < BarShape)
        {
            had.UnionWith(ch.Slotted);
            ch.Slotted.Clear();
            if (ch.Lamps?.Layouts is { } layouts) foreach (var l in layouts) l.Carried = new();
            ch.TaughtUpTo = 0;
            ch.Bar = BarShape;
            recut = true;
        }
        if (level <= ch.TaughtUpTo) return got;
        bool first = ch.TaughtUpTo == 0;
        foreach (var s in t.Slots)
        {
            if (s.Level <= ch.TaughtUpTo || s.Level > level || !Weapons.All.ContainsKey(s.Skill) || !SkillBook.Carries(ch, s.Skill)) continue;
            if (!ch.Discovered.Contains(s.Skill)) ch.Discovered.Add(s.Skill);
            if (!ch.Skills.Contains(s.Skill)) ch.Skills.Add(s.Skill);
            if (ch.Slotted.Contains(s.Skill)) continue;
            if (!SkillBook.HasRoom(ch, s.Skill, level)) continue;
            ch.Slotted.Add(s.Skill);
            if (!had.Contains(s.Skill)) got.Add(s);   // (a skill she carried before the re-cut is carried again, not newly taught)
        }
        ch.TaughtUpTo = level;
        if (first) Order(ch, t);
        // A re-cut save's layouts start from the new bar, so a swap of layouts never brings the old autos back.
        if (recut && ch.Lamps?.Layouts is { } ls) foreach (var l in ls) l.Carried = ch.Slotted.ToList();
        return got;
    }

    /// <summary>On the first grant only, the build's carried skills lead, in its order (the grip on the first key); the
    /// rest after, as they were. Later grants append, so a key she has swapped keeps its number.</summary>
    static void Order(CharacterData ch, TaughtBuild t)
    {
        var slots = t.Slots;
        int Rank(string id) { int i = slots.FindIndex(s => s.Skill == id); return i < 0 ? int.MaxValue : i; }
        ch.Slotted = ch.Slotted.Select((id, i) => (id, i)).OrderBy(x => Rank(x.id)).ThenBy(x => x.i).Select(x => x.id).ToList();
    }
}
