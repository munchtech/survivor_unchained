import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Rpg/Items.cs', [
("""    /// <summary>The least rarity it rolls on (skills come only on fine gear).</summary>
    public int MinRarity;
}""",
"""    /// <summary>The least rarity it rolls on (skills come only on fine gear).</summary>
    public int MinRarity;
    /// <summary>What it gives the night's ember beyond numbers (docs/SKILLS_DESIGN.md,
    /// "Gear and the ember"): spark, reroll, refusal, roads, omens, or stand:PASSIVE,
    /// which counts as that passive in an evolution's recipe. One to an item,
    /// two to a survivor.</summary>
    public string? Kindled;
}"""),
("""        new() { Id = "of_greed", Name = "of Greed", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet],""",
"""        /* Kindled: gear that shapes the ember without owning it. Rare and up,
         * one to an item, two to a survivor (Inventory.MaxKindled). */
        new() { Id = "of_the_first_spark", Name = "of the First Spark", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic], Kindled = "spark", MinRarity = 2,
            Text = _ => "Kindled: the ember starts a level higher" },
        new() { Id = "of_second_thoughts", Name = "of Second Thoughts", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Head], Kindled = "reroll", MinRarity = 2,
            Text = _ => "Kindled: one more redraw in the ember's drafts" },
        new() { Id = "of_refusal", Name = "of Refusal", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Head], Kindled = "refusal", MinRarity = 2,
            Text = _ => "Kindled: one more banishing in the ember's drafts" },
        new() { Id = "of_many_roads", Name = "of Many Roads", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Cloak], Kindled = "roads", MinRarity = 2,
            Text = _ => "Kindled: the ember's drafts show a fourth card" },
        new() { Id = "of_omens", Name = "of Omens", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic], Kindled = "omens", MinRarity = 2,
            Text = _ => "Kindled: great blessings offer a fourth choice" },
        Stand("of_the_whetstone", "of the Whetstone", "serration"),
        Stand("of_rime", "of Rime", "chilling"),
        Stand("of_the_censer", "of the Censer", "searing"),
        Stand("of_the_wide_field", "of the Wide Field", "expanse"),
        Stand("of_the_true_eye", "of the True Eye", "precision"),
        Stand("of_mending", "of Mending", "recovery"),
        Stand("of_the_ox", "of the Ox", "might"),
        Stand("of_the_evergreen", "of the Evergreen", "perennial"),
        Stand("of_the_adder", "of the Adder", "venom"),
        Stand("of_the_pack", "of the Pack", "kinship"),
        Stand("of_the_lodestone", "of the Lodestone", "conduit"),
        Stand("of_embers", "of Embers", "emberblood"),

        new() { Id = "of_greed", Name = "of Greed", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet],"""),
("""    public static AffixDef? Affix(string id) => Array.Find(Affixes, a => a.Id == id);""",
"""    public static AffixDef? Affix(string id) => Array.Find(Affixes, a => a.Id == id);

    /// <summary>A catalyst suffix: the gear stands in for a passive in the ember's
    /// recipes, so a survivor who plans an evolution by day reaches it with a
    /// passive slot to spare (never without the rank-8 climb).</summary>
    static AffixDef Stand(string id, string name, string passive) => new()
    {
        Id = id, Name = name, Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Cloak, ItemKind.Body], Kindled = $"stand:{passive}", MinRarity = 2,
        Text = _ => $"Kindled: counts as {Content.Boons.Find(passive)?.Name ?? passive} in the ember's evolutions",
    };"""),
])

edit('logic/Rpg/Character.cs', [
("""                var cands = pool.Where(a => !picked.Contains(a.Id) && (a.Prefix ? !hasPrefix || n > 2 : !hasSuffix || n > 2)).ToList();
                if (cands.Count == 0) break;
                // What answers the map comes four times as often; a skill worn is rare.
                double W(AffixDef x) => (lean?.Contains(x.Id) == true ? 4 : 1) * (x.Grants != null ? 0.35 : 1);""",
"""                // One kindling to an item.
                bool kindled = picked.Any(id => Items.Affix(id)?.Kindled != null);
                var cands = pool.Where(a => !picked.Contains(a.Id) && (a.Prefix ? !hasPrefix || n > 2 : !hasSuffix || n > 2) && !(kindled && a.Kindled != null)).ToList();
                if (cands.Count == 0) break;
                // What answers the map comes four times as often; a skill worn is rare, and a kindling rarer.
                double W(AffixDef x) => (lean?.Contains(x.Id) == true ? 4 : 1) * (x.Grants != null ? 0.35 : 1) * (x.Kindled != null ? 0.3 : 1);"""),
("""    public HashSet<StatusKind> GearStatuses = new();
    public int StartLevels, Revives, Rerolls = 3;
}""",
"""    public HashSet<StatusKind> GearStatuses = new();
    public int StartLevels, Revives, Rerolls = 3;
    /// <summary>What the kindled gear gives the ember (Items: AffixDef.Kindled):
    /// banishings beyond the two, a fourth card, a fourth great choice, and the
    /// passives it stands in for in a recipe.</summary>
    public int Banishes;
    public bool Roads, Omens;
    public HashSet<string> Stands = new();
    /// <summary>The kindled affixes in force (the first two worn; a third does nothing).</summary>
    public List<string> Kindled = new();
}"""),
("""            // Skills the gear grants, while there is room for them.
            foreach (var ar in it.Affixes)""",
"""            // Kindling: one to an item, two to the survivor.
            if (it.Affixes.Select(ar => Items.Affix(ar.Id)).FirstOrDefault(a => a?.Kindled != null) is { } kin && kit.Kindled.Count < Inventory.MaxKindled)
            {
                kit.Kindled.Add(kin.Id);
                Kindle(kit, kin.Kindled!);
            }
            // Skills the gear grants, while there is room for them.
            foreach (var ar in it.Affixes)"""),
("""    static readonly string[] CompareKeys =""",
"""    static void Kindle(CombatKit kit, string key)
    {
        switch (key)
        {
            case "spark": kit.StartLevels++; break;
            case "reroll": kit.Rerolls++; break;
            case "refusal": kit.Banishes++; break;
            case "roads": kit.Roads = true; break;
            case "omens": kit.Omens = true; break;
            default: if (key.StartsWith("stand:")) kit.Stands.Add(key[6..]); break;
        }
    }

    static readonly string[] CompareKeys ="""),
])
print('ok')
