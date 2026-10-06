PAIRS = [
("""            var col = tier switch
            {
                LootTier.Set => new Color("#3fd6c0"),
                LootTier.Material or LootTier.Draught => Style.InkDim,
                LootTier.Chart or LootTier.Book => new Color("#e8d8b0"),
                LootTier.Quest => Style.GoldHi,
                LootTier.Legendary => Style.RarityOf(4),
                LootTier.Storied => Style.RarityOf(5),
                _ => Style.RarityOf((int)tier),
            };""",
"""            // The tiers' colours from the one table the tiles and cards use (ItemViews.TierColour).
            var col = tier is LootTier.Material or LootTier.Draught ? Style.InkDim : ItemViews.TierColour(tier);"""),
]
