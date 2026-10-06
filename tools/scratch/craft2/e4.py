from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""/// <summary>A trophy set into a piece: a power of its own, outside the seams (Greymuzzle's
/// fang), and what the world can tell of it.</summary>""",
"""/// <summary>A trophy set into a piece: a power of its own, outside the seams (Greymuzzle's
/// fang), and what the world can tell of it. Moment keys its lines ("fang.set", "history.fang").</summary>"""),
])
sub('logic/Rpg/Character.cs', [
("""    /// <summary>The day it was last remade: a remade piece cools overnight before the next.</summary>
    public int? Remade;
}""",
"""    /// <summary>The day it was last remade: a remade piece cools overnight before the next.</summary>
    public int? Remade;
    /// <summary>A trophy's power set into it (an affix id: Greymuzzle's fang), outside its seams:
    /// no grades, no heat, and its name leads the piece's.</summary>
    public string? Setting;
}"""),
("""        var affs = it.Affixes.Select(a => Items.Affix(a.Id)).Where(a => a != null).ToList();
        var pre = affs.FirstOrDefault(a => a!.Prefix);""",
"""        var affs = it.Affixes.Select(a => Items.Affix(a.Id)).Where(a => a != null).ToList();
        // What is set in it leads: Greymuzzle's Worn Oathblade.
        if (it.Setting != null && Items.Affix(it.Setting) is { } set) affs.Insert(0, set);
        var pre = affs.FirstOrDefault(a => a!.Prefix);"""),
("""        foreach (var a in it.Affixes)
            if (Items.Affix(a.Id) is { } ad) o.AddRange(ad.Mods(a.Tier).Select(m => m with { Source = src }));
        return o;
    }

    public static List<string> Lines(ItemInstance it) => it.Affixes.Select(a => Items.Affix(a.Id)?.Text(a.Tier) ?? "").ToList();""",
"""        foreach (var a in it.Affixes)
            if (Items.Affix(a.Id) is { } ad) o.AddRange(ad.Mods(a.Tier).Select(m => m with { Source = src }));
        if (it.Setting != null && Items.Affix(it.Setting) is { } set) o.AddRange(set.Mods(0).Select(m => m with { Source = src }));
        return o;
    }

    public static List<string> Lines(ItemInstance it) =>
        (it.Setting != null && Items.Affix(it.Setting) is { } set ? new[] { set.Text(0) } : Array.Empty<string>())
            .Concat(it.Affixes.Select(a => Items.Affix(a.Id)?.Text(a.Tier) ?? "")).ToList();"""),
("""    public static int Free(CharacterData ch) => ch.Pack.Count(p => p == null);""",
"""    public static int Free(CharacterData ch) => ch.Pack.Count(p => p == null);

    /// <summary>How many more of a thing the pack could take (a material: any number, it goes in the pouch).</summary>
    public static int Room(CharacterData ch, string defId)
    {
        var def = Items.Get(defId);
        if (def.Kind == ItemKind.Material) return int.MaxValue;
        int stack = Math.Max(1, def.Stack ?? 1), n = Free(ch) * stack;
        foreach (var p in ch.Pack) if (p != null && p.Def == defId) n += Math.Max(0, stack - p.Qty);
        return n;
    }"""),
])
