from ed import sub

sub("logic/Rpg/Crafting.cs", [
("""    public List<int> BreakDown = new();
    public List<CraftStep> Temper = new();""",
"""    public List<int> BreakDown = new();
    /// <summary>Ember shards a Legendary gives besides its iron, broken down (agreed with loot): the light in it.</summary>
    public int LegendaryShards = 3;
    public List<CraftStep> Temper = new();"""),
("""        int iron = Rules.BreakDown[RarityIx(it.Rarity)];
        if (!gear) q.Blocked = "Only gear breaks down.";
        else if (def.Unique || it.Rarity >= 5) q.Blocked = "You can't bring yourself to.";
        else if (iron <= 0) q.Blocked = "Nothing in it worth the breaking.";
        else if (Inventory.Find(x.Ch, it.Uid) is not { InPack: true }) q.Blocked = "Take it off first.";
        q.Gives[Iron] = iron;
        int coals = it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null);
        if (coals > 0) q.Gives[Shard] = coals;
        return q;
    }""",
"""        foreach (var (m, n) in Yield(it)) q.Gives[m] = n;
        if (!gear) q.Blocked = "Only gear breaks down.";
        else if (def.Unique || it.Rarity >= 5) q.Blocked = "You can't bring yourself to.";
        else if (q.Gives.GetValueOrDefault(Iron) <= 0) q.Blocked = "Nothing in it worth the breaking.";
        else if (Inventory.Find(x.Ch, it.Uid) is not { InPack: true }) q.Blocked = "Take it off first.";
        return q;
    }

    /// <summary>What a piece breaks down to, wherever it is broken (at the bench, from the pack, at a
    /// fight's end): its rarity's old iron, a shard for each caged coal, and from a Legendary the
    /// light in it as well (an old copy is worth the breaking, not only the selling).</summary>
    public static Dictionary<string, int> Yield(ItemInstance it)
    {
        var o = new Dictionary<string, int> { [Iron] = Rules.BreakDown[RarityIx(it.Rarity)] };
        int shards = it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null)
            + (Drops.TierOf(it) == LootTier.Legendary ? Rules.LegendaryShards : 0);
        if (shards > 0) o[Shard] = shards;
        return o;
    }"""),
])
sub("logic/Play/JourneyLoot.cs", [
("""                int n = Crafting.Rules.BreakDown[Math.Clamp(it.Rarity, 0, Crafting.Rules.BreakDown.Count - 1)];
                int c = it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null);""",
"""                // (crafting's yield, the same as at the bench)
                var yield = Crafting.Yield(it);
                int n = yield.GetValueOrDefault(Crafting.Iron), c = yield.GetValueOrDefault(Crafting.Shard);"""),
])
