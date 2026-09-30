using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Maps;

/* What a map is sworn under, who lives there, and what it is called.
 *
 * An oath is a map's affix: it makes the map harder in one way and pays for
 * it in another. The denizens are the families the map is thick with, and
 * the boss that rules its last clearing. */

/// <summary>An oath a map is sworn under: what it asks, what it gives.</summary>
public sealed record OathDef(string Id, string Name, string Asks, string Gives,
    double PackSize = 1, double Elites = 1, int Levels = 0, double Ember = 1, double Gear = 1, int Waves = 0);

/// <summary>Who lives in a map: the rank and file (weighted), and the boss.</summary>
public sealed record Denizens(string Id, string Name, (string Def, double Weight)[] Horde, string Boss, string BossName, string BossTitle);

public static class MapOffers
{
    public static readonly OathDef[] Oaths =
    {
        new("swarm", "Oath of the Swarm", "Packs half again as large", "Half again the ember", PackSize: 1.5, Ember: 1.5),
        new("champions", "Oath of Champions", "Twice the champions", "More gear from them", Elites: 2, Gear: 1.6),
        new("deep", "Oath of the Deep Dark", "Foes two levels stronger", "Better gear", Levels: 2, Gear: 1.4, Ember: 1.2),
        new("vigil", "Oath of the Long Vigil", "Every altar calls a fourth wave", "An altar's hoard doubled", Waves: 1, Gear: 1.3),
    };

    public static OathDef Oath(string id) => Oaths.First(o => o.Id == id);

    public static readonly Denizens[] Peoples =
    {
        new("pack", "the Pack", new[] { ("wolf", 5.0), ("wolf_blighted", 2.0), ("boar", 1.0) }, "wolf_alpha", "The Pack-Mother", "Alpha of the Deep Wood"),
        new("dead", "the Risen", new[] { ("risen", 5.0), ("risen_warrior", 2.0), ("risen_archer", 2.0), ("grave_caller", 0.4) }, "barrow_knight", "The Barrow Lord", "Who Would Not Lie Down"),
        new("lamplings", "the Lamplings", new[] { ("lampling", 5.0), ("lampling_sapper", 1.5) }, "grimtunnel", "Grimtunnel's Get", "Foreman of the Under-Road"),
        new("kerchiefs", "the Kerchiefs", new[] { ("footpad", 5.0), ("pillager", 2.0), ("bruiser", 1.2) }, "enforcer", "The Red Hand", "Warlord of the Ravine"),
    };

    public static Denizens People(string id) => Peoples.First(p => p.Id == id);

    static readonly string[] Adjectives = { "Weeping", "Ashen", "Thorned", "Drowned", "Moonless", "Broken", "Gallows", "Whispering", "Hollow", "Bleeding", "Crooked", "Silent" };
    static readonly string[] Places = { "Wood", "Thicket", "Glade", "Tangle", "Barrow-Wood", "Deepwood", "Fen", "Holt", "Wilds", "Brake" };

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
                Seed = rng.Int(1, int.MaxValue - 1), Tier = t, Theme = theme, Oaths = oaths, Night = people.Id == "dead" || rng.Chance(0.6),
                Name = $"The {rng.Pick(Adjectives)} {rng.Pick(Places)}",
            };
            list.Add(new MapOffer(spec, people.Id));
        }
        return list;
    }

    /* The map in play lives in the world's facts, so a save made in it comes
     * back to the same map (made again from its seed). */

    public static void Remember(WorldState w, MapOffer o)
    {
        w.Facts["map.seed"] = o.Spec.Seed;
        w.Facts["map.tier"] = o.Spec.Tier;
        w.Facts["map.theme"] = o.Spec.Theme;
        w.Facts["map.night"] = o.Spec.Night;
        w.Facts["map.name"] = o.Spec.Name;
        w.Facts["map.oaths"] = string.Join(",", o.Spec.Oaths);
        w.Facts["map.people"] = o.People;
    }

    public static MapOffer? Current(WorldState w)
    {
        var seed = w.Fact("map.seed");
        if (seed.IsNull) return null;
        var oaths = w.Fact("map.oaths").Str;
        return new MapOffer(new MapSpec
        {
            Seed = (int)seed.Number, Tier = (int)w.Fact("map.tier").Number, Theme = w.Fact("map.theme").Str ?? "wood",
            Night = w.Fact("map.night").Truthy, Name = w.Fact("map.name").Str ?? "The Wood",
            Oaths = string.IsNullOrEmpty(oaths) ? new() : oaths.Split(',').ToList(),
        }, w.Fact("map.people").Str ?? "pack");
    }
}

/// <summary>A map on the table: the map and who lives there.</summary>
public sealed record MapOffer(MapSpec Spec, string People);
