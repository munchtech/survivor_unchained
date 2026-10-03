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
 * evolutions and a union of its own (Content/Unions.cs) to crown it. */

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
            Weapons = ["oathblade", "cleaver", "axe_gyre", "iron_palms", "reaving_arc", "knifestorm", "gale_chakram", "dawnpulse", "butchers_wheel"],
            Passives = ["might", "ferocity", "serration", "ironhide", "haste", "fleetfoot", "evasion", "thorns", "venom", "conduit"],
            Blessings = ["blood_scent", "butchers_mark", "frostbite", "shatter", "static_charge", "sanctify"],
            Great = ["bloodthirst", "momentum", "duelists_grace", "restless_hands", "cinderwake"],
            Capstones = ["graveedge", "whirlwind", "bonesplitter", "reavers_wheel", "gyrestorm", "temple_breaker", "butchers_wheel"],
            Callings = ["reaver", "warden"] },
        new() { Id = "hunt", Name = "The Hunt", Text = "Thrown and shot, many at once; marks, wounds and sure strikes.",
            Weapons = ["volley", "knifestorm", "gale_chakram", "judgement_disc", "firepot", "moonbrand", "hail_of_steel"],
            Passives = ["duplicity", "precision", "ferocity", "velocity", "haste", "serration", "fortune", "evasion"],
            Blessings = ["blood_scent", "butchers_mark", "deaths_due", "pyre_burst", "dark_bargain"],
            Great = ["hunters_mark", "glass_cannon", "duelists_grace", "momentum", "bloodthirst"],
            Capstones = ["arrowfall", "predators_volley", "steel_flurry", "thousand_cuts", "razorgale", "reckoning", "powder_keg", "hail_of_steel"],
            Callings = ["stalker", "warden"] },
        new() { Id = "pyre", Name = "The Pyre", Text = "Fire that bursts, spreads from the dying, and leaves the ground burning.",
            Weapons = ["cinderfall", "firepot", "hallowed_ring", "thunderhead", "seeking_motes", "verdant_lance", "frostfire_comet"],
            Passives = ["emberblood", "expanse", "perennial", "haste", "venom", "might", "searing", "vitality", "warding"],
            Blessings = ["kindling", "pyre_burst", "emberseekers", "fracture", "overload"],
            Great = ["from_the_ashes", "cinderwake", "arcane_overflow"],
            Capstones = ["fallen_star", "living_flame", "wildfire", "powder_keg", "pyre_of_faith", "frostfire_comet"],
            Callings = ["arcanist"] },
        new() { Id = "rime", Name = "The Long Winter", Text = "Chill until they freeze; the frozen take more, and shatter when they die.",
            Weapons = ["rimeshard", "hoarfrost", "gale_chakram", "blightfield", "thornbloom", "seeking_motes", "cleaver", "frostfire_comet"],
            Passives = ["chilling", "haste", "velocity", "expanse", "warding"],
            Blessings = ["deep_chill", "shatter", "fracture", "frostbite"],
            Great = ["stormborn", "iron_vow", "restless_hands", "rootbind"],
            Capstones = ["deepwinter", "glacier_spear", "hailwheel", "winter_ward", "absolute_zero", "blighted_earth", "strangleroot", "bonesplitter", "frostfire_comet"],
            Callings = ["arcanist"] },
        new() { Id = "storm", Name = "The Storm", Text = "Lightning that leaps, forks and falls; the shocked take more.",
            Weapons = ["arcweb", "thunderhead", "iron_palms", "seeking_motes", "rimeshard", "axe_gyre", "the_tempest"],
            Passives = ["conduit", "precision", "haste", "expanse", "duplicity", "vitality"],
            Blessings = ["static_charge", "storm_caller", "overload"],
            Great = ["grounding", "stormborn", "arcane_overflow"],
            Capstones = ["skybreak", "tempest_coil", "thunder_palm", "eye_of_the_storm", "thunderclap", "the_tempest"],
            Callings = ["arcanist", "reaver"] },
        new() { Id = "dawn", Name = "Dawn's Light", Text = "Holy rings and hallowed ground; the seared burn; light that mends and wards.",
            Weapons = ["dawnpulse", "hallowed_ring", "judgement_disc", "verdant_lance", "oathblade", "hoarfrost", "dawns_judgement"],
            Passives = ["searing", "ironhide", "vitality", "recovery", "warding", "expanse", "emberblood"],
            Blessings = ["sanctify", "consecration", "kindling"],
            Great = ["iron_vow", "bloodthirst", "from_the_ashes"],
            Capstones = ["circle_of_dawn", "sunbreak", "sanctified_earth", "aegis_wheel", "sunlance", "oathkeeper", "winter_ward", "dawns_judgement"],
            Callings = ["warden"] },
        new() { Id = "grave", Name = "The Grave", Text = "Shadow that drinks: wounds that mend you, rot, and the dead on your side.",
            Weapons = ["umbral_bolt", "grave_tether", "reaving_arc", "blightfield", "gravecall", "soul_lantern"],
            Passives = ["recovery", "vitality", "wisdom", "might", "venom", "kinship"],
            Blessings = ["soul_harvest", "grave_call", "plague_bearer", "contagion", "dread_command"],
            Great = ["bloodthirst", "spirit_companion", "go_for_the_throat"],
            Capstones = ["soul_siphon", "ruin_bolt", "tether_of_anguish", "deathcoil", "rend_and_mend", "harrowing", "barrow_legion", "soul_lantern"],
            Callings = ["reaver", "arcanist"] },
        new() { Id = "wild", Name = "The Wild", Text = "Brambles, blight and green fire: ground that holds them, poison that spreads.",
            Weapons = ["thornbloom", "blightfield", "verdant_lance", "spirit_herd", "hallowed_ring", "volley", "rotwood"],
            Passives = ["perennial", "expanse", "thorns", "venom", "chilling", "fleetfoot", "evasion"],
            Blessings = ["plague_bearer", "contagion", "pack_leader", "consecration", "deep_chill"],
            Great = ["rootbind", "spirit_companion", "iron_vow"],
            Capstones = ["everbloom", "strangleroot", "plaguebloom", "verdant_gaze", "great_herd", "wild_hunt", "blighted_earth", "rotwood"],
            Callings = ["stalker"] },
        new() { Id = "host", Name = "The Host", Text = "Spirit beasts and risen dead that fight for you, while brambles hold the rest.",
            Weapons = ["gravecall", "spirit_herd", "reaving_arc", "thornbloom", "barrow_host"],
            Passives = ["kinship", "perennial", "vitality", "recovery", "ironhide", "greed"],
            Blessings = ["dread_command", "pack_leader", "soul_harvest", "grave_call"],
            Great = ["go_for_the_throat", "spirit_companion", "iron_vow", "ember_tithe"],
            Capstones = ["barrow_legion", "bone_knights", "great_herd", "harrowing", "barrow_host"],
            Callings = ["stalker", "reaver"] },
        new() { Id = "weave", Name = "The Weave", Text = "Seeking motes and moonfire in volleys; spells fired over and over.",
            Weapons = ["seeking_motes", "moonbrand", "umbral_bolt", "arcweb", "rimeshard", "grave_tether", "starfall"],
            Passives = ["duplicity", "haste", "precision", "wisdom", "fortune", "greed", "recovery", "warding"],
            Blessings = ["emberseekers", "deaths_due", "storm_caller", "dark_bargain"],
            Great = ["arcane_overflow", "glass_cannon", "hunters_mark", "ember_tithe", "grounding"],
            Capstones = ["mote_cascade", "starseeker", "moonfall", "lunar_brand", "starfall"],
            Callings = ["arcanist"] },
    ];

    public static readonly Dictionary<string, PathDef> ById = All.ToDictionary(p => p.Id);

    public static PathDef? Find(string id) => ById.TryGetValue(id, out var p) ? p : null;

    /// <summary>The paths a combat skill belongs to.</summary>
    public static IEnumerable<PathDef> OfWeapon(string id) => All.Where(p => p.Weapons.Contains(id));
}
