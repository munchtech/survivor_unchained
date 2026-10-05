using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Maps;

/* The Wayfinder's charts: the maps, the permanent ARPG arenas (docs/SKILLS_DESIGN.md §17).
 *
 * The owner: "end game is two types of arenas - permanent and our normal arenas. permanent
 * is our arpg build maps like poe and the normal arenas are for mindless survivors fun".
 * A chart is used up when its map opens. It says who holds the ground, how hard it is, and
 * what it is sworn under: prefixes strengthen the foe, suffixes weaken the survivor, and
 * each pays in quantity, rarity and pack size. Reading them, re-rolling them and choosing
 * which to run is the loop; the answers are made in gear. */

/// <summary>A chart's mod. Prefixes strengthen the foe (the table's oaths, and the map's own);
/// suffixes weaken the survivor. What each pays: more found, finer, and bigger packs.</summary>
public sealed record ChartMod(string Id, string Name, string Says, bool Prefix,
    double Quantity, double Rarity, double PackSize, Action<MapRules>? Rule = null, string? Oath = null);

/// <summary>A Wayfinder's chart: one map, used up when it opens. The same chart always opens the
/// same ground.</summary>
public sealed class Chart
{
    /// <summary>1 to 16: the creature level and what drops, and which kinds and mods can come.</summary>
    public int Tier = 1;
    public string People = "pack";
    public int Seed = 1;
    /// <summary>0 plain (no mods), 1 fine (one or two), 2 rare (three to five).</summary>
    public int Rarity;
    public List<string> Mods = new();
    /// <summary>Crafting's: one more percent found a point, to 20.</summary>
    public int Quality;
    /// <summary>Crafting's: the mod held through a burn and redraw at the Wayfinder's table (one a chart).</summary>
    public string? Pinned;
    public string Name = "";
    public string Theme = "wood";

    /// <summary>Its creatures' level: tier 1 is Act 1's end (10), tier 16 the Depths (40).</summary>
    [JsonIgnore] public int Level => 8 + 2 * Tier;
    /// <summary>What drops is made at this level.</summary>
    [JsonIgnore] public int ItemLevel => Math.Min(40, Level);

    [JsonIgnore] public IEnumerable<ChartMod> Rolled => Mods.Select(Charts.Mod);
    [JsonIgnore] public double Quantity => 1 + Rolled.Sum(m => m.Quantity) + Quality * 0.01;
    [JsonIgnore] public double RarityBonus => 1 + Rolled.Sum(m => m.Rarity);
    [JsonIgnore] public double PackSize => 1 + Rolled.Sum(m => m.PackSize);
    public bool Has(string mod) => Mods.Contains(mod);

    /// <summary>The ground: MapGen's winding way, with its oaths for the look.</summary>
    [JsonIgnore] public MapSpec Map => new()
    {
        Seed = Seed, Tier = Tier, Theme = Theme, Night = false, Name = Name, Arena = false, People = People,
        // The experience lead's shape: three clearings before the ruler's at tiers 1-2, four at 3-5,
        // five from 6; an altar (the map's event) in each but the first, to three.
        Clearings = Tier <= 2 ? 3 : Tier <= 5 ? 4 : 5, AltarCount = Tier <= 2 ? 1 : Tier <= 5 ? 2 : 3,
        Oaths = Rolled.Where(m => m.Oath != null).Select(m => m.Oath!).ToList(),
    };

    /// <summary>The mods as rules of the fight.</summary>
    public MapRules Rules()
    {
        var r = new MapRules();
        foreach (var m in Rolled) m.Rule?.Invoke(r);
        return r;
    }
}

public static class Charts
{
    /// <summary>The item a chart is carried as (its map in ItemInstance.Chart).</summary>
    public const string Item = "wayfinder_chart";

    /// <summary>The prefixes come from the table's oaths (the questions a player has met at night,
    /// asked again of the whole build), and the map's own; the suffixes weaken the survivor. The
    /// Long Vigil has no turns to double here, and the moonless is a suffix: a choice on a chart,
    /// never the long night's weather.</summary>
    public static readonly ChartMod[] All = Build();

    static ChartMod[] Build()
    {
        var o = new List<ChartMod>();
        foreach (var oath in MapOffers.Oaths.Where(x => x.Id is not ("vigil" or "moonless")))
            o.Add(new ChartMod(oath.Id, oath.Name, oath.Asks, true, 0.10, 0.06, oath.PackSize > 1 ? 0.0 : 0.05, oath.Rule, oath.Id));
        o.AddRange(
        [
            new("signed", "Signed", "Every champion wears one more Sign", true, 0.12, 0.10, 0.0),
            new("twin", "Twin guardians", "Two minibosses at each altar", true, 0.14, 0.08, 0.0),
            new("contested", "Contested", "A second people's packs hold a third of the ground", true, 0.14, 0.06, 0.10),
            new("restless", "Restless", "Its ruler comes again, at half its strength", true, 0.12, 0.12, 0.0),
            new("hardened", "Hardened", "Every pack is led by one wearing its people's Sign", true, 0.10, 0.08, 0.05),
            new("thin_blood", "of Thin Blood", "You mend a third less", false, 0.08, 0.05, 0.05, r => r.HealCut = Math.Max(r.HealCut, 0.33)),
            new("brittle", "of the Brittle", "Your armour counts for two fifths less", false, 0.08, 0.05, 0.05, r => r.ArmourMul *= 0.6),
            new("leaden", "of Lead", "Your dash comes back two fifths slower", false, 0.08, 0.05, 0.05, r => r.DashRecharge *= 0.6),
            new("sleepless", "of No Rest", "You do not regenerate", false, 0.08, 0.05, 0.05, r => r.RegenMul = 0),
            new("moonless", "of the Moonless", "Your light carries half as far", false, 0.10, 0.08, 0.0, r => r.Light *= 0.5),
            new("sour", "of Sour Draughts", "Draughts mend half as much", false, 0.08, 0.05, 0.05, r => r.DraughtMul *= 0.5),
        ]);
        return o.ToArray();
    }

    public static ChartMod Mod(string id) => All.FirstOrDefault(m => m.Id == id) ?? throw new KeyNotFoundException($"no chart mod '{id}'");

    /// <summary>Mods that cannot share a chart: two that cut mending, and the map's two-people mod
    /// below the eighth tier (a second people's packs is a late question).</summary>
    public static bool Fits(Chart c, ChartMod m) =>
        !c.Mods.Contains(m.Id)
        && !(m.Id == "contested" && c.Tier < 8)
        && !(m.Id == "thin_blood" && c.Mods.Contains("blight")) && !(m.Id == "blight" && c.Mods.Contains("thin_blood"))
        && !(m.Id == "hunt" && c.Mods.Contains("winter")) && !(m.Id == "winter" && c.Mods.Contains("hunt"));

    /// <summary>A chart as it drops: its rarity rolled (rarer with the rarity found), and its mods.</summary>
    public static Chart Roll(Rng rng, int tier, string people, double rarity = 1)
    {
        double r = rng.Next() / rarity;
        var c = new Chart
        {
            Tier = Math.Clamp(tier, 1, 16), People = people, Seed = rng.Int(1, int.MaxValue - 1),
            Rarity = r < 0.18 ? 2 : r < 0.6 ? 1 : 0,
            Theme = people == "dead" ? (rng.Chance(0.5) ? "blight" : "wood") : rng.Chance(0.3) ? "autumn" : "wood",
        };
        int n = c.Rarity switch { 2 => rng.Int(3, 5), 1 => rng.Int(1, 2), _ => 0 };
        AddMods(c, rng, n);
        c.Name = NameOf(c, rng);
        return c;
    }

    /// <summary>`n` more mods, prefixes and suffixes as they fall (at most three of either).</summary>
    public static void AddMods(Chart c, Rng rng, int n)
    {
        for (int k = 0; k < n; k++)
        {
            int pre = c.Rolled.Count(m => m.Prefix), suf = c.Mods.Count - pre;
            var pool = All.Where(m => Fits(c, m) && (m.Prefix ? pre < 3 : suf < 3)).ToList();
            if (pool.Count == 0) return;
            c.Mods.Add(pool[rng.Int(0, pool.Count - 1)].Id);
        }
    }

    /// <summary>A chart is named as the table's maps are, in the valley's words for its people's
    /// ground (ArenaPlaces, story's): never a weeping wood or a whispering fen.</summary>
    static string NameOf(Chart c, Rng rng) => MapOffers.Name(c.People, rng);

    /// <summary>A chart as a pickup carries it (Pickup.Ref): read back by FromRef when it is picked up.</summary>
    public static string Ref(Chart c) => $"chart:{c.Tier}:{c.People}:{c.Seed}:{c.Rarity}:{string.Join(",", c.Mods)}:{c.Theme}:{c.Name}";

    public static Chart? FromRef(string r)
    {
        var f = r.Split(':', 8);
        if (f.Length < 8 || f[0] != "chart") return null;
        return new Chart
        {
            Tier = int.Parse(f[1]), People = f[2], Seed = int.Parse(f[3]), Rarity = int.Parse(f[4]),
            Mods = f[5].Length == 0 ? new() : f[5].Split(',').ToList(), Theme = f[6], Name = f[7],
        };
    }

    /// <summary>A chart carried, taken out of the satchel to be set on the table (it is used up as its
    /// map opens); null if it is not there.</summary>
    public static Chart? TakeOut(Rpg.CharacterData ch, string uid)
    {
        int i = ch.Satchel.FindIndex(p => p.Uid == uid && p.Chart != null);
        if (i < 0) return null;
        var c = ch.Satchel[i].Chart;
        ch.Satchel.RemoveAt(i);
        return c;
    }

    /// <summary>The charts carried, the highest tier first, then the finest.</summary>
    public static System.Collections.Generic.List<Rpg.ItemInstance> Carried(Rpg.CharacterData ch) =>
        ch.Satchel.Where(p => p.Chart != null).OrderByDescending(p => p.Chart!.Tier).ThenByDescending(p => p.Chart!.Rarity).ToList();

    /// <summary>What a chart is called in the pack: its tier, who holds it, and its name.</summary>
    public static string Title(Chart c) => $"{c.Name} (tier {c.Tier}, {MapOffers.People(c.People).Name})";

    /// <summary>The kinds a map of this tier fields: the people's base kinds and the first two
    /// stretches' at tier 1, the next stretch every two tiers, the whole roster by tier 9 (the
    /// night's rule, "a verb is shown before it spreads", becomes the atlas's).</summary>
    public static int StretchesOpen(int tier) => Math.Min(5, 2 + (tier - 1) / 2);

    public static IEnumerable<(string Def, double Weight)> Kinds(Denizens people, int tier)
    {
        int open = StretchesOpen(tier);
        var joins = people.Stretches.Take(open).SelectMany(s => s.Joins).ToHashSet();
        var later = people.Stretches.Skip(open).SelectMany(s => s.Joins).ToHashSet();
        foreach (var h in people.Arena)
            if (!later.Contains(h.Def) || joins.Contains(h.Def)) yield return (h.Def, h.Weight);
    }

    /// <summary>The Signs a map's champions may wear at this tier: the people's own, then each open stretch's.</summary>
    public static List<string> Signs(Denizens people, int tier) =>
        people.Signs.Concat(people.Stretches.Take(StretchesOpen(tier)).SelectMany(s => s.Signs)).Distinct().ToList();

    /// <summary>The minibosses that may guard a map's altars at this tier.</summary>
    public static List<string> Guardians(Denizens people, int tier) =>
        people.Stretches.Take(StretchesOpen(tier)).Select(s => s.Miniboss).ToList();
}

/// <summary>The Wayfinder's atlas: which peoples' maps have been cleared at which tier. The first
/// clear of each pair gives a point; the points will buy the atlas's biases (§17.6, with the
/// experience lead).</summary>
public static class Atlas
{
    static string Key(string people, int tier) => $"atlas.{people}.{tier}";

    public static bool Done(World.WorldState w, string people, int tier) => w.Fact(Key(people, tier)).Truthy;

    /// <summary>The atlas is open once a chart is carried (Vonnra's fortune at Act 1's end gives
    /// the first) or a map has been cleared.</summary>
    public static bool IsOpen(World.WorldState w, Rpg.CharacterData? ch = null) =>
        Best(w) > 0 || ch != null && ch.Satchel.Any(p => p.Chart != null);

    /// <summary>The highest tier cleared of any people, and the points the first clears gave.</summary>
    public static int Best(World.WorldState w) => (int)w.Fact("atlas.best").Number;
    public static int Points(World.WorldState w) => (int)w.Fact("atlas.points").Number;

    /* The atlas's biases (the experience lead's first five): a point a rank, three ranks each,
     * bought with the points the first clears give. Hooks only for now; the table shows them. */
    public const string PeoplesRoad = "peoples_road", TwiceLit = "twice_lit", KeepersDue = "keepers_due", RulersHoard = "rulers_hoard", MarkedMen = "marked_men";
    public const int MaxRank = 3;

    /// <summary>The biases, as the atlas shows them: id, name, what a rank does.</summary>
    public static readonly (string Id, string Name, string Rank)[] Biases =
    [
        (PeoplesRoad, "The people's road", "A fifth more of the charts that drop are of the people you follow"),
        (TwiceLit, "Twice lit", "A third more chance that a second altar's lighting brings its people's question too"),
        (KeepersDue, "The keeper's due", "An altar's keeper carries one thing more"),
        (RulersHoard, "The ruler's hoard", "A map's ruler leaves one thing more"),
        (MarkedMen, "Marked men", "Half again the chance that a magic or rare pack's leader carries one thing more"),
    ];

    public static int Rank(World.WorldState w, string bias) => (int)w.Fact($"atlas.bias.{bias}").Number;
    public static int Unspent(World.WorldState w) => Points(w) - Biases.Sum(b => Rank(w, b.Id));

    /// <summary>A rank more in a bias, for a point: false if none is to spend or it is at three.</summary>
    public static bool Raise(World.WorldState w, string bias)
    {
        if (Unspent(w) <= 0 || Rank(w, bias) >= MaxRank || Biases.All(b => b.Id != bias)) return false;
        w.Facts[$"atlas.bias.{bias}"] = Rank(w, bias) + 1;
        return true;
    }

    /// <summary>The people the road follows (null: none chosen).</summary>
    public static string? Road(World.WorldState w) => w.Fact("atlas.road").IsNull ? null : w.Fact("atlas.road").Str;
    public static void Follow(World.WorldState w, string people) => w.Facts["atlas.road"] = people;

    /// <summary>A map's ruler is down: its (people, tier) is marked. True if it is the first time.</summary>
    public static bool Complete(World.WorldState w, Chart c)
    {
        bool first = !Done(w, c.People, c.Tier);
        w.Facts[Key(c.People, c.Tier)] = true;
        w.Facts["atlas.cleared"] = w.Fact("atlas.cleared").Number + 1;
        if (first)
        {
            w.Facts["atlas.points"] = Points(w) + 1;
            w.Facts["atlas.best"] = Math.Max(Best(w), c.Tier);
        }
        return first;
    }
}
