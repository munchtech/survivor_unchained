PAIRS = [
("""        var gear = spoils.Gear.OrderByDescending(Drops.TierOf).ThenByDescending(Drops.LevelOf).ToList();
        var noted = gear.Where(it => Drops.TierOf(it) >= LootTier.Epic).ToList();""",
"""        // The best first: a Legendary or Storied piece, a set's, an Epic, a ruler's marked thing; then the rest.
        static int Rank(ItemInstance it) => Drops.TierOf(it) switch
        {
            LootTier.Storied => 9, LootTier.Legendary => 8, LootTier.Set => 7, LootTier.Epic => 6, LootTier.Book or LootTier.Chart or LootTier.Quest => 5,
            LootTier.Rare => 3, LootTier.Uncommon => 2, LootTier.Common => 1, _ => 0,
        };
        var gear = spoils.Gear.OrderByDescending(Rank).ThenByDescending(Drops.LevelOf).ToList();
        var noted = gear.Where(it => Rank(it) >= 5).ToList();"""),
("""        foreach (var c in spoils.Charts) { left.AddChild(Beat(ChartFound(c), cue, () => Sound.Sfx.Loot(true))); cue += 0.45; }
        if (spoils.Materials.Count > 0 || r.Spilled.Count > 0) { left.AddChild(Beat(Haul(spoils.Materials, r.Spilled, "Carried out"), cue, () => Sound.Sfx.Loot())); cue += 0.4; }
        if (spoils.Gold >= 1) { left.AddChild(Beat(Line("coin", $"{spoils.Gold:N0} gold", Style.GoldHi), cue, Sound.Sfx.Gold)); cue += 0.35; }

        // Beat three: the atlas, and the mark the map left on it.
        right.AddChild(Kit.Head("The atlas"));""",
"""        // What else came out sits under the atlas, so the two columns are of a height.
        if (spoils.Charts.Count > 0 || spoils.Materials.Count > 0 || r.Spilled.Count > 0 || spoils.Gold >= 1)
        {
            right.AddChild(Kit.Head("And besides"));
            foreach (var c in spoils.Charts) { right.AddChild(Beat(ChartFound(c), cue, () => Sound.Sfx.Loot(true))); cue += 0.45; }
            if (spoils.Materials.Count > 0 || r.Spilled.Count > 0) { right.AddChild(Beat(Haul(spoils.Materials, r.Spilled, "Carried out"), cue, () => Sound.Sfx.Loot())); cue += 0.4; }
            if (spoils.Gold >= 1) { right.AddChild(Beat(Line("coin", $"{spoils.Gold:N0} gold", Style.GoldHi), cue, Sound.Sfx.Gold)); cue += 0.35; }
            right.AddChild(Style.Gap(Style.Gap2));
        }

        // Beat three: the atlas, and the mark the map left on it.
        right.AddChild(Kit.Head("The atlas"));"""),
("""        var (left, right) = Columns(v, 380);""", """        var (left, right) = Columns(v, 430);"""),
]
