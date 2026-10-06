import sys
root = sys.argv[1]

def patch(path, pairs):
    p = root + '/' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

# ---------------------------------------------------------------- ArenaRun
patch('logic/Play/Zones/ArenaRun.cs', [
("""        if (b != null) foreach (var l in OnLoot(b)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);""",
"""        if (b != null) foreach (var l in OnLoot(b)) B!.Spill(l, x, z);"""),
("""    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    int Rarity(double luck)
    {
        double roll = R() / luck;
        return roll < 0.04 + Spec.Tier * 0.01 ? 3 : roll < 0.2 + Spec.Tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        // Gear from what carries something (a champion's turn, a captain, a herald, a miniboss),
        // never from the champions that turn up in the crowd: those were hundreds a night, and the
        // items plan wants a handful (docs/CRAFTING_DESIGN.md).
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier && e != boss && R() < 0.6 * gear)
            o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Rarity(gear), lean));
        if (e == boss)
        {
            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0) + returns;
            o.Add(new Loot(PickupKind.Chest, "boss", n, true));
            for (int k = 0; k < 2 + Spec.Tier / 2; k++)
                o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(1, Rarity(gear * 1.5)), lean));""",
"""    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5): gear rolled whole at the
    /// carrier's level, fewer and better than before, the people's material where it is not gear;
    /// deeper past the half hour, the better.</summary>
    List<Loot> Gear(Enemy e, DropSource source) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = e.Level, People = Spec.People, Lean = lean, Luck = B!.Stats.Get(Stat.Luck), Gear = gear,
        Depth = Beyond, Tier = Spec.Tier, StoryBoss = Spec.Story && source == DropSource.Boss, R = R,
    });

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        // Gear from what carries something (a champion's turn, a captain, a herald, a miniboss),
        // never from the champions that turn up in the crowd: those were hundreds a night, and the
        // items plan wants a handful (docs/CRAFTING_DESIGN.md).
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier && e != boss)
            o.AddRange(Gear(e, small ? DropSource.Miniboss : e == herald || e == keeper ? DropSource.Herald : DropSource.Champion));
        if (e == boss)
        {
            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0) + returns;
            o.Add(new Loot(PickupKind.Chest, "boss", n, true));
            o.AddRange(Gear(e, DropSource.Boss));"""),
])

# ---------------------------------------------------------------- StoryNight
patch('logic/Play/Zones/StoryNight.cs', [
("""        if (boss != null) foreach (var l in Hoard()) B.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);""",
"""        if (boss != null) foreach (var l in Hoard()) B.Spill(l, x, z);"""),
("""    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    int Rarity(double luck)
    {
        double roll = R() / luck;
        return roll < 0.04 + Spec.Tier * 0.01 ? 3 : roll < 0.2 + Spec.Tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier && R() < 0.6) o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Rarity(1), lean));
        return o;
    }""",
"""    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5), rolled whole at its level; the
    /// story's boss pays the survivor's first Legendary for certain.</summary>
    List<Loot> Gear(int level, DropSource source) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = level, People = Spec.People, Lean = lean, Luck = B!.Stats.Get(Stat.Luck), Tier = Spec.Tier,
        StoryBoss = source == DropSource.Boss, R = R,
    });

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier) o.AddRange(Gear(e.Level, small ? DropSource.Miniboss : DropSource.Champion));
        return o;
    }"""),
("""        o.Add(new Loot(PickupKind.Chest, "boss", n, true));
        for (int k = 0; k < 2 + Spec.Tier / 2; k++)
            o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(1, Rarity(1.5)), lean));
        return o;""",
"""        o.Add(new Loot(PickupKind.Chest, "boss", n, true));
        o.AddRange(Gear(Level, DropSource.Boss));
        return o;"""),
])
print("ok")
