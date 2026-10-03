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
 * honed, never evolved. Its weapon is in Weapons.All, not in the draft's pool. */

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
    public static readonly UnionDef[] All =
    [
        new() { Id = "frostfire_comet", Name = "Frostfire Comet", A = "cinderfall", B = "rimeshard", Into = "frostfire_comet",
            Description = "Fire and frost in one falling star: it bursts, freezes what it does not burn, and the frozen it finds explode." },
        new() { Id = "the_tempest", Name = "The Tempest", A = "arcweb", B = "thunderhead", Into = "the_tempest",
            Description = "The storm and its lightning are one: bolts fall on the crowd and leap from every shocked thing they strike." },
        new() { Id = "rotwood", Name = "Rotwood", A = "blightfield", B = "thornbloom", Into = "rotwood",
            Description = "The blight grows thorns: a wide, slow thicket that holds what it rots, and spreads the rot from what dies in it." },
        new() { Id = "butchers_wheel", Name = "Butcher's Wheel", A = "axe_gyre", B = "cleaver", Into = "butchers_wheel",
            Description = "The axes become cleavers and never stop turning: every cut a wound, and wounds that deepen." },
        new() { Id = "hail_of_steel", Name = "Hail of Steel", A = "volley", B = "knifestorm", Into = "hail_of_steel",
            Description = "Arrows and knives together, in every direction at once, opening wounds." },
        new() { Id = "dawns_judgement", Name = "Dawn's Judgement", A = "dawnpulse", B = "judgement_disc", Into = "dawns_judgement",
            Description = "Two shields of morning that ricochet through the crowd, and break into light wherever they strike." },
        new() { Id = "barrow_host", Name = "The Barrow Host", A = "gravecall", B = "spirit_herd", Into = "barrow_host",
            Description = "The barrows send their knights, and the herd runs with them: a host that does not lie down." },
        new() { Id = "soul_lantern", Name = "Soul Lantern", A = "umbral_bolt", B = "grave_tether", Into = "soul_lantern",
            Description = "Shadow that passes through everything, marks it for the grave, and brings a little of it back to you." },
        new() { Id = "starfall", Name = "Starfall", A = "seeking_motes", B = "moonbrand", Into = "starfall",
            Description = "Moons fall among them and break into motes that hunt the strongest." },
    ];

    public static readonly Dictionary<string, UnionDef> ById = All.ToDictionary(u => u.Id);

    public static UnionDef? Find(string id) => ById.TryGetValue(id, out var u) ? u : null;

    /// <summary>The union a combat skill is half of, if any.</summary>
    public static UnionDef? Of(string weapon) => All.FirstOrDefault(u => u.A == weapon || u.B == weapon);
}
