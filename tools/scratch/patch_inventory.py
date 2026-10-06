import sys
root = sys.argv[1]
p = root + '/Rpg/Character.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new)

# 1. Make: level for all gear, grade shift.
rep("""        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new(), Level = def.Base ? level : null };""",
"""        // Gear carries the level it was made at (docs/design/LOOT_DESIGN.md §4.1): given, or the survivor's.
        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new(), Level = Loot.Leveled(def) ? level ?? ch?.Level : null };""")
rep("""                // A rarity rolls one of two grades; made at a map's level, the finer comes oftener (a coin by day).
                int finer = it.Level is int lv ? (rng.Next() < Crafting.FinerGrade(lv) ? 1 : 0) : rng.Int(0, 1);
                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Max(0, Math.Min(3, it.Rarity - 1 + finer)) });""",
"""                // A rarity rolls one of two grades; the deeper it was made, the finer comes oftener (a coin to
                // level 10, read the same way as the coin was), and from level 25 the grades rise (Loot.GradeShift).
                int finer = it.Level is int lv ? (rng.Next() >= 1 - Crafting.FinerGrade(lv) ? 1 : 0) : rng.Int(0, 1);
                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Min(5, Math.Max(0, Math.Min(3, it.Rarity - 1 + finer)) + Loot.GradeShift(it.Level)) });""")

# 2. Mods with implicits at make.
rep("""        var o = (def.Mods ?? new()).Select(m => m with { Source = src }).ToList();
        foreach (var a in it.Affixes)""",
"""        // A base's own numbers (or the base a named piece is built on) at its make; a named piece's own after.
        var o = Loot.Implicit(def, it.Level).Select(m => m with { Source = src }).ToList();
        if (!def.Base) o.AddRange((def.Mods ?? new()).Select(m => m with { Source = src }));
        foreach (var a in it.Affixes)""")

# 3. Stores: replace AddToPack .. Find.
start = s.index("    public static bool AddToPack(CharacterData ch, ItemInstance it)")
end = s.index("    /// <summary>Equip an item into a slot; whatever was there goes to the pack.</summary>")
new = open(root + '/../../../../../AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/stores.cs.txt', encoding='utf-8').read() if False else open(sys.argv[2], encoding='utf-8').read()
s = s[:start] + new + s[end:]

# 4. Equip uses Worn
rep("""        if (loc is { InPack: false }) ch.Equipment[loc.Slot] = null;""",
"""        if (loc is { Worn: true }) ch.Equipment[loc.Slot] = null;""")

# 5. WorldTags: tools on the key ring, set bonuses.
rep("""        foreach (var p in ch.Pack)
            if (p != null && Items.Find(p.Def) is { Kind: ItemKind.Tool, Tags: { } t }) tags.UnionWith(t);""",
"""        foreach (var p in ch.Pack.Concat(ch.Keys))
            if (p != null && Items.Find(p.Def) is { Kind: ItemKind.Tool, Tags: { } t }) tags.UnionWith(t);
        // A set worn far enough says something too (the Watch's Kit: the Watch takes you for its own).
        foreach (var (_, bonus) in Loot.SetBonuses(ch)) if (bonus.Tags != null) tags.UnionWith(bonus.Tags);""")

# 6. CharacterData stores.
rep("""    /// <summary>The materials pouch: crafting's materials by id, never in the pack's places.</summary>
    public Dictionary<string, int> Materials = new();""",
"""    /// <summary>The materials pouch: crafting's materials and trophies by id, never in the pack's places.</summary>
    public Dictionary<string, int> Materials = new();
    /// <summary>The slotless stores (docs/design/LOOT_DESIGN.md §6): books, charts and the rulers'
    /// marked things in the satchel; quest things and tools on the key ring; draughts on the belt.</summary>
    public List<ItemInstance> Satchel = new(), Keys = new();
    public Dictionary<string, int> Belt = new();
    /// <summary>The survivor's item filter (docs/design/LOOT_DESIGN.md §7), and the bases seen at
    /// each make ("iron_helm@Wrought"): a first sighting always shows.</summary>
    public LootFilter Filter = new();
    public HashSet<string> Seen = new();""")
open(p, 'w', encoding='utf-8').write(s)
print("patched")
