"""Item level: gear from a map is made at its level, and rolls the finer grade of its rarity more often."""
from ed import sub
sub("logic/Rpg/Character.cs", [
    ("""    public string? Setting;
}""", """    public string? Setting;
    /// <summary>The level it was made at, where that was a Wayfinder's map (docs/CRAFTING_DESIGN.md 20.3):
    /// the harder the map, the more often its grades rolled the finer of its rarity's two. Null by day.</summary>
    public int? Level;
}"""),
    ("""    public static ItemInstance Make(CharacterData? ch, string defId, int qty = 1, int? rarity = null, uint? seed = null, List<AffixRoll>? affixes = null,
        IReadOnlyCollection<string>? lean = null, bool dropped = false)""",
     """    public static ItemInstance Make(CharacterData? ch, string defId, int qty = 1, int? rarity = null, uint? seed = null, List<AffixRoll>? affixes = null,
        IReadOnlyCollection<string>? lean = null, bool dropped = false, int? level = null)"""),
    ("""        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new() };""",
     """        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new(), Level = def.Base ? level : null };"""),
    ("""                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Max(0, Math.Min(3, it.Rarity - 1 + rng.Int(0, 1))) });""",
     """                // A rarity rolls one of two grades; made at a map's level, the finer comes oftener (a coin by day).
                int finer = it.Level is int lv ? (rng.Next() < Crafting.FinerGrade(lv) ? 1 : 0) : rng.Int(0, 1);
                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Max(0, Math.Min(3, it.Rarity - 1 + finer)) });"""),
])
sub("logic/Rpg/Crafting.cs", [
    ("""    /* ---------------------------------------------------------- shelves -- */""",
     """    /* ------------------------------------------------------- item level -- */

    /// <summary>The chance a piece made at this level rolls the finer of its rarity's two grades: an even
    /// coin at a first map's level (10, as by day), rising a fortieth a level to nine in ten (design 20.3).</summary>
    public static double FinerGrade(int level) => Math.Clamp(0.5 + (level - 10) * 0.025, 0.5, 0.9);

    /* ---------------------------------------------------------- shelves -- */"""),
])
sub("logic/Play/Journey.cs", [
    ("""        var it = Inventory.Make(Ch, defId, qty, rarity, lean: lean, dropped: dropped);
        var def = Items.Get(defId);""",
     """        // Found in a Wayfinder's map, gear is made at the map's level (design 20.3).
        var it = Inventory.Make(Ch, defId, qty, rarity, lean: lean, dropped: dropped, level: dropped ? World.Map?.ItemLevel : null);
        var def = Items.Get(defId);"""),
])
sub("src/Ui/ItemViews.cs", [
    ("""        kind.Alignment = BoxContainer.AlignmentMode.Begin;
        names.AddChild(kind);""",
     """        kind.Alignment = BoxContainer.AlignmentMode.Begin;
        // Made in a map: at its level (the harder the map, the finer its grades came).
        if (it.Level is int lv) kind.AddChild(Style.Label($"·  item level {lv}", Style.Ui, Style.Caption, Style.InkDim));
        names.AddChild(kind);"""),
])
