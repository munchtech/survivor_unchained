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
    /// <summary>The finds that went to Rook's storeroom (the pack was full at the map's end: Journey.Gather),
    /// by uid: the page says where they are.</summary>
    public HashSet<string> Stored { get; init; } = new();

    /// <param name="stashBefore">Rook's storeroom as the map opened, and as it ended: what the
    /// gathering sent there is the map's pay too.</param>
    public static MapSpoils Between(CharacterData before, CharacterData after, IEnumerable<ItemInstance?>? stashBefore = null, IEnumerable<ItemInstance?>? stashAfter = null)
    {
        var had = Carried(before).Select(i => i.Uid).Concat((stashBefore ?? Enumerable.Empty<ItemInstance?>()).Where(i => i != null).Select(i => i!.Uid)).ToHashSet();
        var stored = (stashAfter ?? Enumerable.Empty<ItemInstance?>()).Where(i => i != null && !had.Contains(i.Uid)).Select(i => i!).ToList();
        var found = Carried(after).Where(i => !had.Contains(i.Uid)).Concat(stored).ToList();
        // Best last, as the night's result tells it: the page builds to its finest find.
        var gear = found.Where(i => i.Chart == null && Items.Find(i.Def)?.Kind != ItemKind.Material).OrderBy(i => i.Rarity).ToList();
        var charts = found.Where(i => i.Chart != null).OrderBy(i => i.Chart!.Tier).ThenBy(i => i.Chart!.Rarity).ToList();
        var materials = new Dictionary<string, int>();
        foreach (var (m, n) in after.Materials)
            if (n - before.Materials.GetValueOrDefault(m) is > 0 and var d) materials[m] = d;
        return new(gear, charts, materials, Math.Max(0, after.Gold - before.Gold)) { Stored = stored.Select(i => i.Uid).ToHashSet() };
    }

    static IEnumerable<ItemInstance> Carried(CharacterData ch) =>
        ch.Pack.Where(p => p != null).Select(p => p!).Concat(ch.Satchel).Concat(ch.Keys)
            .Concat(Items.EquipSlots.Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!)).Concat(Kits.Aside(ch).Select(a => a.Item));

    /// <summary>The atlas's line for a map's end ("The Lampless Howes, tier 1: cleared, the first
    /// time: a point for the atlas").</summary>
    public static string AtlasLine(Chart c, bool cleared, bool first) =>
        $"{c.Name}, tier {c.Tier}: " + (!cleared ? $"closed, {MapOffers.People(c.People).BossName} still standing"
            : first ? "cleared, the first time: a point for the atlas" : "cleared");
}
