import sys
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

patch('logic/Play/Zones/MapRun.cs', [
("""        foreach (var l in OnLoot(boss)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);""",
"""        foreach (var l in OnLoot(boss)) B!.Spill(l, x, z);"""),
("""    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    /// <summary>A rarity at the map's tier: rarer finds the higher it is, and under the chart's rarity.</summary>
    int RarityRoll(double bonus = 1)
    {
        double roll = R() / (Chart.RarityBonus * bonus);
        return roll < 0.03 + Chart.Tier * 0.01 ? 3 : roll < 0.18 + Chart.Tier * 0.02 ? 2 : roll < 0.62 ? 1 : 0;
    }

    Loot Gear(double bonus = 1, int floor = 0) =>
        new(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(floor, RarityRoll(bonus)), MapOffers.Lean(Chart.Map, people.Id));
""",
"""    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5): gear rolled whole at the map's
    /// level (its make climbs with the tier), under the chart's rarity and quantity, the people's
    /// material where a roll is not gear; extra: further rolls the atlas has earned.</summary>
    List<Loot> Gear(DropSource source, int extra = 0, int levelUp = 0) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = Chart.ItemLevel + levelUp, People = Chart.People, Lean = MapOffers.Lean(Chart.Map, people.Id),
        Luck = B!.Stats.Get(Stat.Luck), Rarity = Chart.RarityBonus, Quantity = Chart.Quantity, Extra = extra, Tier = Chart.Tier, R = R,
    });
"""),
("""            int n = 3 + (R() < 0.5 * q ? 1 : 0) + (R() < 0.25 * q ? 1 : 0) + Atlas.Rank(G.Journey.World, Atlas.RulersHoard);
            for (int k = 0; k < n; k++) o.Add(Gear(1.5, 1));""",
"""            o.AddRange(Gear(DropSource.MapRuler, Atlas.Rank(G.Journey.World, Atlas.RulersHoard)));"""),
("""            int n = grade switch { 3 => 2, 2 => 2, _ => 1 }
                + (grade == 3 ? Atlas.Rank(w, Atlas.KeepersDue) : 0)
                + (grade < 3 && R() < 0.5 * Atlas.Rank(w, Atlas.MarkedMen) / Atlas.MaxRank ? 1 : 0);
            for (int k = 0; k < n; k++) o.Add(Gear(grade >= 3 ? 1.4 : 1, grade >= 3 && R() < 0.35 ? 2 : 0));""",
"""            int extra = (grade == 3 ? Atlas.Rank(w, Atlas.KeepersDue) : 0)
                + (grade < 3 && R() < 0.5 * Atlas.Rank(w, Atlas.MarkedMen) / Atlas.MaxRank ? 1 : 0);
            o.AddRange(Gear(grade switch { 3 => DropSource.MapKeeper, 2 => DropSource.MapPackFine, _ => DropSource.MapPack }, extra));"""),
("""        var loot = new List<Loot>();
        int n = 3 + (R() < 0.5 * Chart.Quantity ? 1 : 0) + (R() < 0.25 * Chart.Quantity ? 1 : 0);
        for (int k = 0; k < n; k++) loot.Add(Gear(1.3, 1));""",
"""        var loot = Gear(DropSource.Strongbox, levelUp: 1);"""),
("""            if (B!.SpawnPickup(l.Kind, x + Math.Cos(a) * d, z + Math.Sin(a) * d, l.Value, l.Ref) is { } pk)
            {
                pk.Persistent = true;
                if (l.Rarity is { } r) pk.Tier = r;
                pk.Lean = l.Lean;
            }
            if (l.Ref == null) continue;""",
"""            B!.Spill(l with { Persistent = true }, x + Math.Cos(a) * d, z + Math.Sin(a) * d);
            if (l.Ref == null || l.Kind == PickupKind.Material) continue;"""),
])

patch('logic/Rpg/Loot.cs', [
("""    /// <summary>A story fight's boss: the first one a survivor beats pays a Legendary for certain.</summary>""",
"""    /// <summary>Rolls beyond the source's own (what the atlas has earned).</summary>
    public int Extra;
    /// <summary>A story fight's boss: the first one a survivor beats pays a Legendary for certain.</summary>"""),
("""        int rolls = src.Rolls + (x.Tier >= 3 ? src.Deep : 0);""",
"""        int rolls = src.Rolls + (x.Tier >= 3 ? src.Deep : 0) + Math.Max(0, x.Extra);"""),
])

# ---------------------------------------------------------------- Verge
patch('logic/Play/Zones/Verge.cs', [
("""        if (e.Elite && loot == "elite")
        {
            // Gear, rolled where it falls: better the stronger it was. The
            // column of light over it says how good.
            int lv = e.Level;
            double roll = R();
            int rarity = roll < 0.03 + lv * 0.008 ? 3 : roll < 0.16 + lv * 0.015 ? 2 : roll < 0.62 ? 1 : 0;
            out_.Add(new Loot(PickupKind.Item, PlainGear[(int)Math.Floor(R() * PlainGear.Length)], 1, true, rarity));
        }""",
"""        // Gear, rolled whole where it falls at the elite's level (docs/design/LOOT_DESIGN.md §5): the
        // column of light over it says how good; where it is not gear, its people's material.
        if (e.Elite && loot == "elite")
            out_.AddRange(G.Journey.Drops(new DropCtx { Source = DropSource.Elite, Level = e.Level, People = Drops.PeopleOf(e.Def.Family), Luck = B!.Stats.Get(Stat.Luck), R = R }));"""),
("""    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

""", ""),
])
print("ok")
