"""The economy simulation with the loot lead's fewer drops (a9a9c345a35e1fcad, loot.json): champions drop gear 45%
of the time and otherwise one of their people's material and half the time an old iron; the boss two materials."""
from ed import sub
T = "tests/CraftingEconomy.cs"
sub(T, [
    ("""    static Tally Play(int days, int[] kerchiefGold, uint seed, bool stay)
    {""",
     """    /// <summary>The loot lead's drop rule (loot.json, at a9a9c345a35e1fcad@2404bf9f): a carrier's roll is gear 45% of
    /// the time; a roll that is not gear gives one of its people's material, and half the time an old iron; the
    /// boss two of its people's material besides. False: the arena's rule before it (gear 60%, nothing else).</summary>
    static Tally Play(int days, int[] kerchiefGold, uint seed, bool stay, bool fewer = true)
    {"""),
    ("""            var drops = new List<ItemInstance>();
            int carriers = 20;
            for (int k = 0; k < carriers; k++)
                if (rng.Next() < 0.6) drops.Add(Inventory.Make(j.Ch, PlainGear[rng.Int(0, PlainGear.Length - 1)], rarity: Rarity(rng, tier, 1), seed: (uint)rng.Int(1, int.MaxValue - 1), dropped: true));""",
     """            var drops = new List<ItemInstance>();
            int carriers = 20;
            string material = people switch { "pack" => "wolf_pelt", "dead" => "bone_dust", "lamplings" => "ember_shard", _ => "kerchief_cloth" };
            for (int k = 0; k < carriers; k++)
                if (rng.Next() < (fewer ? 0.45 : 0.6)) drops.Add(Inventory.Make(j.Ch, PlainGear[rng.Int(0, PlainGear.Length - 1)], rarity: Rarity(rng, tier, 1), seed: (uint)rng.Int(1, int.MaxValue - 1), dropped: true));
                else if (fewer)
                {
                    Give(j, material, 1);
                    if (rng.Next() < 0.5) Give(j, Crafting.Iron, 1);
                }
            if (fewer) Give(j, material, 2);"""),
    ("""        var runs = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0)).ToList();""",
     """        var runs = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0)).ToList();
        // Before the loot lead's fewer drops (every carrier's roll gear 60% of the time, nothing else), for comparison.
        var more = Enumerable.Range(0, 8).Select(s => Play(days, KerchiefGold, (uint)(101 + s * 7), s % 2 == 0, fewer: false)).ToList();"""),
    ("""        Report("before the arena's gold was cut", before);
        Report("an arena's gold today", runs);""",
     """        Report("before the arena's gold was cut", before);
        Report("before fewer drops", more);
        Report("today (fewer drops, materials and iron in their place)", runs);"""),
    ("""            $"gold spent {Med(rs.Select(r => r.Spent / Math.Max(1, r.Earned))):0%} of {Med(rs.Select(r => r.Earned)):0} earned, shards a night {Med(rs.SelectMany(r => r.ShardsByNight))}");""",
     """            $"gold spent {Med(rs.Select(r => r.Spent / Math.Max(1, r.Earned))):0%} of {Med(rs.Select(r => r.Earned)):0} earned, shards a night {Med(rs.SelectMany(r => r.ShardsByNight))}, " +
            $"left at the end: iron {Med(rs.Select(r => (double)r.IronLeft)):0}, the people's {Med(rs.Select(r => (double)r.PeoplesLeft)):0}");"""),
    ("""        public int Worked;""", """        public int Worked, IronLeft, PeoplesLeft;"""),
    ("""        t.Worked = Items.EquipSlots""", """        t.IronLeft = Inventory.Count(j.Ch, Crafting.Iron);
        t.PeoplesLeft = new[] { "wolf_pelt", "boar_hide", "bone_dust", "kerchief_cloth" }.Sum(m => Inventory.Count(j.Ch, m));
        t.Worked = Items.EquipSlots"""),
])
