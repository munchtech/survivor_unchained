using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Maps;

/* What a map is sworn under, who lives there, and what it is called.
 *
 * An oath is a map's affix: it makes the map harder in one way and pays for
 * it in another. The denizens are the families the map is thick with, and
 * the boss that rules its last clearing. */

/// <summary>An oath a map is sworn under: what it asks, what it gives, what
/// answers it (the gear and arts that make it easier), and the rule it puts
/// on the fight. A map's gear leans toward its answers (Lean: affix ids), so
/// a survivor who runs a kind of map comes to be dressed for it.</summary>
public sealed record OathDef(string Id, string Name, string Asks, string Gives,
    double PackSize = 1, double Elites = 1, int Levels = 0, double Ember = 1, double Gear = 1, int Waves = 0,
    string Answer = "", string[]? Lean = null, Action<MapRules>? Rule = null);

/// <summary>Who lives in a map: the rank and file (weighted), the boss, and
/// the gear that answers them (slayers, resistances). In an arena: its kinds by the minute
/// they may join (Arena), its champion, the Signs its champions wear from the first, and the
/// stretches of the night (Stretches).</summary>
public sealed record Denizens(string Id, string Name, (string Def, double Weight)[] Horde, string Boss, string BossName, string BossTitle, string[] Lean,
    (string Def, double Weight, double From)[] Arena, string Champion, string[] Signs, Stretch[] Stretches);

/// <summary>A stretch of an arena's night (docs/SKILLS_DESIGN.md, "Encounters"): at its minute of a
/// thirty-minute night, a miniboss comes wearing the stretch's verb; the kinds that carry the verb
/// (Joins) join the horde only once it has come (or a little after its minute, if it was held
/// back), and champions may wear its Signs from then. The owner: "mechanics that ramp along with the
/// level time and don't appear till certain mini bosses and minion types show up".</summary>
public sealed record Stretch(double At, string Miniboss, string[] Joins, string[] Signs);

public static class MapOffers
{
    public static readonly OathDef[] Oaths =
    {
        new("swarm", "Oath of the Swarm", "Packs half again as large", "Half again the ember", PackSize: 1.5, Ember: 1.5,
            Answer: "reach and area", Lean: ["of_reach", "of_haste"]),
        new("champions", "Oath of Champions", "Twice the champions", "More gear from them", Elites: 2, Gear: 1.3,
            Answer: "critical strikes, a mark", Lean: ["keen", "cruel"]),
        new("deep", "Oath of the Deep Dark", "Foes two levels stronger", "Better gear", Levels: 2, Gear: 1.4, Ember: 1.2,
            Answer: "health and armour", Lean: ["hale", "sturdy"]),
        new("vigil", "Oath of the Long Vigil", "The horde's turns come twice as often", "More champions, and finer gear", Waves: 1, Gear: 1.3,
            Answer: "area and mending", Lean: ["of_reach", "of_mending"]),
        new("winter", "Oath of the Long Winter", "Their blows chill you to a crawl", "Gear half again as fine", Gear: 1.5,
            Answer: "frost resistance, sure footing, a sprint or a charge", Lean: ["of_the_hearth", "surefooted"], Rule: r => r.HitChill = true),
        new("blight", "Oath of the Blight", "Their blows poison, and you mend a third less", "Two fifths more ember, and finer gear", Ember: 1.4, Gear: 1.6,
            Answer: "poison resistance, mending, draughts", Lean: ["of_the_physician", "of_mending"], Rule: r => { r.HitPoison = true; r.HealCut = 0.33; }),
        new("embers", "Oath of Embers", "Their dead leave the ground burning", "Better gear", Gear: 1.4,
            Answer: "fire resistance, pace", Lean: ["of_the_salamander", "fleet"], Rule: r => r.DeathFire = true),
        new("hunt", "Oath of the Hunt", "They are a fifth faster", "More ember and gear", Ember: 1.25, Gear: 1.2,
            Answer: "pace, a vault or a chain, things that hold them", Lean: ["fleet", "surefooted"], Rule: r => r.FoeSpeed = 1.2),
        new("iron", "Oath of Iron", "They shrug off a third of any blow that is not a critical", "Gear finer still", Gear: 1.5,
            Answer: "critical strikes", Lean: ["keen", "cruel"], Rule: r => r.IronSkin = 0.33),
        new("moonless", "Oath of the Moonless", "Your light carries half as far", "Champions, and what they carry", Elites: 1.3, Gear: 1.3,
            Answer: "a lantern's reach", Lean: ["of_the_lantern"], Rule: r => r.Light = 0.5),
        new("ruin", "Oath of Ruin", "Their dead may burst where they fall", "Half again the ember", Ember: 1.5,
            Answer: "reach, armour, a dash in time", Lean: ["sturdy", "of_reach"], Rule: r => r.DeathBurst = true),
    };

    public static OathDef Oath(string id) => Oaths.First(o => o.Id == id);

    public static readonly Denizens[] Peoples =
    {
        // Each night's stretches at 3, 7, 12, 16 and 22 minutes: just after the experience lead's
        // releases (ArenaPacing), one verb each, shown first on a miniboss.
        new("pack", "the Pack", new[] { ("wolf", 5.0), ("wolf_blighted", 2.0), ("boar", 1.0) }, "boss_pack", "The Pack-Mother", "Who Keeps the Den", ["wolfbane", "of_the_wolf"],
            [("wolf", 5, 0), ("boar", 2, 3), ("wolf_runner", 2.5, 7), ("wolf_blighted", 3, 12), ("boar_slurry", 1.5, 16), ("wolf_howler", 0.4, 22)], "wolf_alpha",
            ["swift"],
            [
                new(3, "mb_old_tusk", ["boar"], ["ironbound"]),                    // the charge
                new(7, "mb_whitethroat", ["wolf_runner"], []),                     // the ring
                new(12, "mb_blight_mother", ["wolf_blighted"], ["volatile", "brood"]), // the burst
                new(16, "mb_outflow_sow", ["boar_slurry"], ["kindled"]),           // the slurry
                new(22, "mb_caller", ["wolf_howler"], ["bannered"]),               // the howl
            ]),
        new("dead", "the Risen", new[] { ("risen", 5.0), ("risen_warrior", 2.0), ("risen_archer", 2.0), ("grave_caller", 0.4) }, "boss_dead", "The Barrow Lord", "Who Would Not Lie Down", ["gravebane", "of_the_grave", "hallowed"],
            [("risen", 5, 0), ("risen_archer", 2, 3), ("risen_warrior", 3, 7), ("legionary", 1.5, 7), ("bone_heap", 1.5, 12), ("drowned", 1.2, 16), ("grave_caller", 0.6, 22), ("risen_bell", 0.4, 22)], "barrow_knight",
            ["ironbound"],
            [
                new(3, "mb_old_quarrel", ["risen_archer"], []),                    // the volley
                new(7, "mb_decurion", ["risen_warrior", "legionary"], ["shielded"]), // the shield line
                new(12, "mb_the_heap", ["bone_heap"], ["brood"]),                 // the heap
                new(16, "mb_drowned_reeve", ["drowned"], ["rimed"]),              // the cold
                new(22, "mb_ford_bell", ["grave_caller", "risen_bell"], ["gravebound", "bannered"]), // the bell
            ]),
        new("lamplings", "the Lamplings", new[] { ("lampling", 5.0), ("lampling_sapper", 1.5) }, "boss_lamplings", "Gutterwick", "Second-Best in the Dig", ["lampsnuffer", "of_the_salamander"],
            [("lampling", 5, 0), ("lampling_wick", 3, 3), ("lampling_sapper", 3.5, 7), ("lampling_lamp", 1.5, 12), ("lampling_fuse", 1.2, 16)], "lampling",
            ["swift"],
            [
                new(3, "mb_wick_mother", ["lampling_wick"], []),                   // the swarm from below
                new(7, "mb_bombardier", ["lampling_sapper"], ["kindled"]),         // the pots
                new(12, "mb_lamplighter", ["lampling_lamp"], ["ironbound"]),       // the fans of flame
                new(16, "mb_fuse_boss", ["lampling_fuse"], ["volatile"]),          // the crates
                new(22, "mb_gaffer", [], ["brood"]),                               // the ground opens
            ]),
        new("kerchiefs", "the Kerchiefs", new[] { ("footpad", 5.0), ("pillager", 2.0), ("bruiser", 1.2) }, "boss_kerchiefs", "The Red Hand", "Who Takes What Is Owed", ["watchmans", "sturdy"],
            [("footpad", 5, 0), ("pillager", 2.5, 3), ("levy_pike", 2, 7), ("bruiser", 1.5, 12), ("levy_crossbow", 1.5, 16), ("kerchief_drummer", 0.3, 22)], "enforcer",
            ["swift"],
            [
                new(3, "mb_firepot_nan", ["pillager"], ["kindled"]),               // the pots
                new(7, "mb_pike_captain", ["levy_pike"], []),                      // the pikes
                new(12, "mb_barn_door", ["bruiser"], ["shielded", "ironbound"]),   // the wall
                new(16, "mb_levy_sergeant", ["levy_crossbow"], []),                // the volley
                new(22, "mb_drum_major", ["kerchief_drummer"], ["bannered"]),      // the drum
            ]),
    };

    public static Denizens People(string id) => Peoples.First(p => p.Id == id);

    /// <summary>What a map's gear leans toward: what answers its oaths and its people.</summary>
    public static string[] Lean(MapSpec spec, string people) =>
        spec.Oaths.SelectMany(o => Oath(o).Lean ?? []).Concat(People(people).Lean).Distinct().ToArray();

    /// <summary>The oaths as rules of the fight.</summary>
    public static MapRules Rules(MapSpec spec)
    {
        var r = new MapRules();
        foreach (var o in spec.Oaths) { Oath(o).Rule?.Invoke(r); r.EmberGain *= Oath(o).Ember; }
        return r;
    }

    // A map is named in the valley's own words for its people's kind of ground (the story bible,
    // "The nights"), so the name says whose place it is before the sheet does. Lampless, Quiet and
    // Praying are seeds: the Order's call, the dead's word, and Tam's.
    static readonly Dictionary<string, (string[] Adjectives, string[] Places)> Names = new()
    {
        ["dead"] = (["Lampless", "Quiet", "Morrow", "Drowned", "Long", "Cold"], ["Howes", "Lows", "Lych-Way", "Chesters"]),
        ["pack"] = (["Grey", "Bitter", "Thorn", "Bracken", "Whelping", "Elder"], ["Dene", "Clough", "Holt", "Shaw"]),
        ["kerchiefs"] = (["Red", "Salt", "Toll", "Gallows", "Hungry", "Widow's"], ["Ruts", "Drove", "Cutting", "Gap"]),
        ["lamplings"] = (["Praying", "Gold", "Warm", "Black", "Deep", "Lamplit"], ["Sump", "Delph", "Sough", "Spoil"]),
    };

    /// <summary>A map's name, drawn from its people's words.</summary>
    public static string Name(string people, Rng rng)
    {
        var (adjectives, places) = Names[people];
        return $"The {rng.Pick(adjectives)} {rng.Pick(places)}";
    }

    /// <summary>The maps the table offers today: three, each of its own
    /// people and oaths, the tier the survivor has earned (and one higher).</summary>
    public static List<MapOffer> Today(int day, int tier, int drawn)
    {
        var rng = new Rng((uint)(day * 7919 + drawn * 104729 + 17));
        var list = new List<MapOffer>();
        for (int k = 0; k < 3; k++)
        {
            int t = Math.Max(1, tier + (k == 2 ? 1 : 0));
            var people = Peoples[rng.Int(0, Peoples.Length - 1)];
            var oaths = new List<string>();
            int n = t <= 1 ? (k == 0 ? 0 : 1) : Math.Min(3, 1 + t / 2);
            foreach (var o in rng.Shuffle(Oaths.Select(o => o.Id).ToList()).Take(n)) oaths.Add(o);
            string theme = people.Id == "dead" ? (rng.Chance(0.5) ? "blight" : "wood") : rng.Chance(0.3) ? "autumn" : "wood";
            var spec = new MapSpec
            {
                Seed = rng.Int(1, int.MaxValue - 1), Tier = t, Theme = theme, Oaths = oaths, Night = true,
                Name = Name(people.Id, rng),
            };
            list.Add(new MapOffer(spec, people.Id));
        }
        return list;
    }
}

/// <summary>A map on the table: the map and who lives there.</summary>
public sealed record MapOffer(MapSpec Spec, string People);
