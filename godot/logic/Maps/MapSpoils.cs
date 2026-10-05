using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Maps;

/// <summary>
/// What a map paid, for its result page (docs/EXPERIENCE_AUDIT.md, "A map's shape"): the gear,
/// the charts, the materials and the gold that came out. Read as the difference between the
/// survivor as the map opened and as it ended. A map pays through the ordinary pickups, so
/// nothing in the fight has to keep count, and what was spilled falling is already gone.
/// </summary>
public sealed record MapSpoils(List<ItemInstance> Gear, List<ItemInstance> Charts, Dictionary<string, int> Materials, double Gold)
{
    public static MapSpoils Between(CharacterData before, CharacterData after)
    {
        var had = Carried(before).Select(i => i.Uid).ToHashSet();
        var found = Carried(after).Where(i => !had.Contains(i.Uid)).ToList();
        // Best last, as the night's result tells it: the page builds to its finest find.
        var gear = found.Where(i => i.Chart == null && Items.Find(i.Def)?.Kind != ItemKind.Material).OrderBy(i => i.Rarity).ToList();
        var charts = found.Where(i => i.Chart != null).OrderBy(i => i.Chart!.Tier).ThenBy(i => i.Chart!.Rarity).ToList();
        var materials = new Dictionary<string, int>();
        foreach (var (m, n) in after.Materials)
            if (n - before.Materials.GetValueOrDefault(m) is > 0 and var d) materials[m] = d;
        return new(gear, charts, materials, Math.Max(0, after.Gold - before.Gold));
    }

    static IEnumerable<ItemInstance> Carried(CharacterData ch) =>
        ch.Pack.Where(p => p != null).Select(p => p!).Concat(Items.EquipSlots.Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!));

    /// <summary>The atlas's line for a map's end ("The Lampless Howes, tier 1: cleared, the first
    /// time: a point for the atlas").</summary>
    public static string AtlasLine(Chart c, bool cleared, bool first) =>
        $"{c.Name}, tier {c.Tier}: " + (!cleared ? $"closed, {MapOffers.People(c.People).BossName} still standing"
            : first ? "cleared, the first time: a point for the atlas" : "cleared");
}
