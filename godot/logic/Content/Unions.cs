using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Content;

/* Unions: two evolved combat skills that belong together become one.
 *
 * The draft offers a union once both are evolved (whichever branch), as it
 * offers an evolution: first, and not left to chance. Taken, the two go and
 * the union comes in their place at full rank, and a combat slot is free
 * again: the build that finished two things gets room for a seventh. Each
 * path has one, joining its two most its own; the hidden pairings (the
 * codex's Discoveries) hint at some of them long before. A union can be
 * honed, never evolved. Its weapon is in Weapons.All, not in the draft's pool. Both live in
 * data/content/skills.json. */

public sealed class UnionDef
{
    public string Id = "", Name = "", Description = "";
    /// <summary>The two combat skills it joins (both evolved).</summary>
    public string A = "", B = "";
    /// <summary>The weapon it becomes (Weapons.All).</summary>
    public string Into = "";
}

public static class Unions
{
    /// <summary>The unions, from data/content/skills.json ("unions").</summary>
    public static readonly UnionDef[] All = SkillsJson.File.Unions.ToArray();

    public static readonly Dictionary<string, UnionDef> ById = All.ToDictionary(u => u.Id);

    public static UnionDef? Find(string id) => ById.TryGetValue(id, out var u) ? u : null;

    /// <summary>The union a combat skill is half of, if any.</summary>
    public static UnionDef? Of(string weapon) => All.FirstOrDefault(u => u.A == weapon || u.B == weapon);
}
