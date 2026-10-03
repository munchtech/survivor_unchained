using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The paths a night's build can take: the archetypes the skills are made
 * for. A path is a way of fighting (steel close in, fire that spreads, a
 * host that fights for you), not a class: any survivor can walk any path,
 * and most builds walk two. The draft reads them to lean toward what the
 * build is already doing, the cards name the path they belong to, and the
 * balance harness plays each one to keep them even (docs/SKILLS_DESIGN.md).
 *
 * Every combat skill belongs to at least one path, every passive skill and
 * blessing serves at least two builds, and every path has its own capstone
 * evolutions. */

public sealed class PathDef
{
    public string Id = "", Name = "", Text = "";
    /// <summary>Its combat skills, the most its own first.</summary>
    public string[] Weapons = [];
    /// <summary>The passive skills it wants.</summary>
    public string[] Passives = [];
    /// <summary>The milestone blessings that key off it.</summary>
    public string[] Blessings = [];
    /// <summary>The great blessings that suit it best.</summary>
    public string[] Great = [];
    /// <summary>The evolutions that crown it.</summary>
    public string[] Capstones = [];
    /// <summary>The callings that lean toward it.</summary>
    public string[] Callings = [];
}

public static class Paths
{
    public static readonly PathDef[] All =
    [
        new() { Id = "steel", Name = "Steel and Blood", Text = "Blades close in; wounds that bleed; finishing what bleeds.",
            Weapons = ["oathblade", "cleaver", "axe_gyre", "iron_palms", "reaving_arc", "gale_chakram"],
            Passives = ["might", "ferocity", "serration", "ironhide", "haste", "fleetfoot"],
            Blessings = ["blood_scent", "butchers_mark"], Great = ["bloodthirst", "momentum", "duelists_grace"],
            Capstones = ["graveedge", "whirlwind", "bonesplitter", "reavers_wheel", "gyrestorm", "temple_breaker"],
            Callings = ["reaver", "warden"] },
        new() { Id = "hunt", Name = "The Hunt", Text = "Thrown and shot steel, many at once; marks and sure strikes.",
            Weapons = ["volley", "knifestorm", "gale_chakram", "judgement_disc", "moonbrand", "seeking_motes"],
            Passives = ["duplicity", "precision", "ferocity", "velocity", "haste", "might"],
            Blessings = ["blood_scent"], Great = ["hunters_mark", "glass_cannon", "duelists_grace"],
            Capstones = ["arrowfall", "predators_volley", "steel_flurry", "thousand_cuts", "razorgale", "reckoning"],
            Callings = ["stalker", "warden"] },
        new() { Id = "pyre", Name = "The Pyre", Text = "Fire that bursts, spreads from the dying, and leaves the ground burning.",
            Weapons = ["cinderfall", "hallowed_ring", "dawnpulse", "seeking_motes", "verdant_lance"],
            Passives = ["expanse", "haste", "perennial", "searing", "might"],
            Blessings = ["kindling", "pyre_burst", "emberseekers", "fracture"], Great = ["cinderwake", "arcane_overflow"],
            Capstones = ["fallen_star", "living_flame", "pyre_of_faith"],
            Callings = ["arcanist"] },
        new() { Id = "rime", Name = "The Long Winter", Text = "Chill until they freeze; the frozen take more and shatter when they die.",
            Weapons = ["rimeshard", "gale_chakram", "blightfield", "thornbloom", "seeking_motes"],
            Passives = ["chilling", "haste", "velocity", "expanse"],
            Blessings = ["deep_chill", "shatter", "fracture"], Great = ["stormborn", "arcane_overflow"],
            Capstones = ["deepwinter", "glacier_spear", "hailwheel", "blighted_earth", "strangleroot"],
            Callings = ["arcanist"] },
        new() { Id = "storm", Name = "The Storm", Text = "Lightning that leaps, forks and falls; the shocked take more.",
            Weapons = ["arcweb", "iron_palms", "seeking_motes", "rimeshard"],
            Passives = ["precision", "haste", "expanse", "duplicity"],
            Blessings = ["static_charge", "storm_caller"], Great = ["stormborn", "arcane_overflow"],
            Capstones = ["skybreak", "tempest_coil", "thunder_palm"],
            Callings = ["arcanist", "reaver"] },
        new() { Id = "dawn", Name = "Dawn's Light", Text = "Holy rings and hallowed ground; the seared burn; light that mends.",
            Weapons = ["dawnpulse", "hallowed_ring", "judgement_disc", "verdant_lance", "oathblade"],
            Passives = ["searing", "ironhide", "vitality", "recovery", "warding", "expanse"],
            Blessings = ["sanctify", "consecration"], Great = ["iron_vow", "bloodthirst"],
            Capstones = ["circle_of_dawn", "sunbreak", "sanctified_earth", "aegis_wheel", "sunlance", "oathkeeper"],
            Callings = ["warden"] },
        new() { Id = "grave", Name = "The Grave", Text = "Shadow that drinks: wounds that mend you, the dead on your side.",
            Weapons = ["umbral_bolt", "grave_tether", "reaving_arc", "blightfield"],
            Passives = ["recovery", "vitality", "wisdom", "might"],
            Blessings = ["soul_harvest", "grave_call", "plague_bearer"], Great = ["bloodthirst", "spirit_companion"],
            Capstones = ["soul_siphon", "ruin_bolt", "tether_of_anguish", "deathcoil", "rend_and_mend", "harrowing"],
            Callings = ["reaver", "arcanist"] },
        new() { Id = "wild", Name = "The Wild", Text = "Brambles, blight and green fire: ground that holds them and rots them.",
            Weapons = ["thornbloom", "blightfield", "verdant_lance", "spirit_herd", "hallowed_ring"],
            Passives = ["perennial", "expanse", "thorns", "chilling"],
            Blessings = ["plague_bearer", "pack_leader"], Great = ["spirit_companion", "iron_vow"],
            Capstones = ["everbloom", "strangleroot", "plaguebloom", "verdant_gaze", "great_herd", "wild_hunt"],
            Callings = ["stalker"] },
        new() { Id = "host", Name = "The Host", Text = "Spirit beasts and risen dead that fight for you.",
            Weapons = ["spirit_herd", "reaving_arc", "thornbloom"],
            Passives = ["perennial", "vitality", "recovery"],
            Blessings = ["dread_command", "pack_leader", "soul_harvest", "grave_call"], Great = ["spirit_companion"],
            Capstones = ["great_herd", "harrowing"],
            Callings = ["stalker", "reaver"] },
        new() { Id = "weave", Name = "The Weave", Text = "Seeking motes and moonfire in volleys; spells fired over and over.",
            Weapons = ["seeking_motes", "moonbrand", "umbral_bolt", "arcweb", "rimeshard", "cinderfall"],
            Passives = ["duplicity", "haste", "precision", "wisdom"],
            Blessings = ["emberseekers"], Great = ["arcane_overflow", "glass_cannon"],
            Capstones = ["mote_cascade", "starseeker", "moonfall", "lunar_brand"],
            Callings = ["arcanist"] },
    ];

    public static readonly Dictionary<string, PathDef> ById = All.ToDictionary(p => p.Id);

    public static PathDef? Find(string id) => ById.TryGetValue(id, out var p) ? p : null;

    /// <summary>The paths a combat skill belongs to.</summary>
    public static IEnumerable<PathDef> OfWeapon(string id) => All.Where(p => p.Weapons.Contains(id));
}
