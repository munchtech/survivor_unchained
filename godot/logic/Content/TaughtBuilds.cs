using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* Each calling's taught build in Act 1 (data/content/taught_builds.json; BUILD_DIRECTION.md rounds 7-8, BUILD_UNLOCKS.md;
 * the hands rule): the four keys (the basic attack in the first) and the three auto slots, each with its cast form and the
 * level it is taught at; the stance her second weapon set opens at; what comes later; the first Union. The tutorial and
 * the lamp offer read it (M6/M7); Character.Bar and Battle.SetForm put a cast on a carried skill. */
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
    /// <summary>The keys in key order, then the auto slots in the order they open.</summary>
    public List<TaughtSlot> Keys = new(), Autos = new();
    public TaughtStance? Stance;
    public string[] Later = System.Array.Empty<string>();
    public TaughtUnion? Union;

    /// <summary>Every taught skill in the order the ladder opens them (the keys first on a level they share).</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public List<TaughtSlot> Slots => Keys.Select((s, i) => (s, k: 0, i)).Concat(Autos.Select((s, i) => (s, k: 1, i)))
        .OrderBy(x => x.s.Level).ThenBy(x => x.k).ThenBy(x => x.i).Select(x => x.s).ToList();
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

    /// <summary>A build's pressed keys: its keys whose cast is press or channel (the basic attack, a hold, is not counted).</summary>
    public static int PressedSlots(TaughtBuild t) => t.Keys.Count(s => s.Skill != t.Grip && s.Cast is "press" or "channel");

    /// <summary>The taught forms on what she carries (campaign: a skill without its record is left as it is). The skills
    /// set, by id.</summary>
    public static List<string> Apply(Battle b, string? calling)
    {
        var set = new List<string>();
        if (Of(calling) is not { } t) return set;
        foreach (var s in t.Slots) if (b.SetForm(s.Skill, s.Cast)) set.Add(s.Skill);
        return set;
    }

    /// <summary>The bar's shape this code carries (CharacterData.Bar): four keys and three auto slots.</summary>
    public const int BarShape = 2;

    /// <summary>(M3; bd-keys) What a campaign survivor carries: each taught key and auto slot of a level up to `level` and
    /// past the levels already granted (CharacterData.TaughtUpTo) is learned, takes its taught form (a kindled one runs in
    /// an auto slot: ch.AutoForm) and goes into the next free key or auto slot, unless she already carries it (a skill she
    /// took off or swapped out later is not put back). A save from the six keys is re-cut once: its taught autos go to the
    /// auto slots and the build is granted again into the new bar. The skills newly carried, with their taught form.</summary>
    public static List<TaughtSlot> Grant(CharacterData ch, int level)
    {
        var got = new List<TaughtSlot>();
        if (Of(ch.Archetype) is not { } t) return got;
        if (ch.Bar < BarShape)
        {
            foreach (var s in t.Autos) if (s.Cast == "kindle") SkillBook.SetAuto(ch, s.Skill, true);
            ch.TaughtUpTo = 0;
            ch.Bar = BarShape;
        }
        if (level <= ch.TaughtUpTo) return got;
        foreach (var s in t.Slots)
        {
            if (s.Level <= ch.TaughtUpTo || s.Level > level || !Weapons.All.ContainsKey(s.Skill) || !SkillBook.Carries(ch, s.Skill)) continue;
            if (!ch.Discovered.Contains(s.Skill)) ch.Discovered.Add(s.Skill);
            if (!ch.Skills.Contains(s.Skill)) ch.Skills.Add(s.Skill);
            if (ch.Slotted.Contains(s.Skill)) continue;
            SkillBook.SetAuto(ch, s.Skill, s.Cast == "kindle");
            if (!SkillBook.HasRoom(ch, s.Skill, level)) continue;
            ch.Slotted.Add(s.Skill);
            got.Add(s);
        }
        ch.TaughtUpTo = level;
        return got;
    }
}
