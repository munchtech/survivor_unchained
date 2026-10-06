"""Rook's storeroom by shelves of 24 (the owner's approval of UI design's proposal): one free, more bought."""
from ed import sub
sub("logic/World/State.cs", [
    ("""    public const int StashSize = 48;
    static List<ItemInstance?> NewStash() { var s = new List<ItemInstance?>(StashSize); for (int i = 0; i < StashSize; i++) s.Add(null); return s; }""",
     """    /// <summary>A shelf of Rook's storeroom: one comes with the room, more are bought from her
    /// (Crafting.ShelfPrice). A save from before shelves kept 48 places: two shelves.</summary>
    public const int Shelf = 24;
    public int Shelves => Math.Max(1, Stash.Count / Shelf);
    static List<ItemInstance?> NewStash() { var s = new List<ItemInstance?>(Shelf); for (int i = 0; i < Shelf; i++) s.Add(null); return s; }"""),
])
sub("logic/World/Save.cs", [
    ("""        while (d.World.Stash.Count < WorldState.StashSize) d.World.Stash.Add(null);""",
     """        // Whole shelves, at least the one that comes with the room (a save from before shelves had two).
        while (d.World.Stash.Count < WorldState.Shelf || d.World.Stash.Count % WorldState.Shelf != 0) d.World.Stash.Add(null);"""),
])
sub("logic/Rpg/Crafting.cs", [
    ("""public sealed class MarkDrop { public string Item = "", Mark = ""; }""",
     """public sealed class MarkDrop { public string Item = "", Mark = ""; }
/// <summary>Rook's shelves (the storeroom grows by shelves of 24): the price of each after the first, then
/// of every one beyond those, and the most there can be.</summary>
public sealed class ShelfRules { public string Seller = "rook"; public List<int> Prices = new() { 300, 1000, 2500 }; public int Then = 5000, Most = 8; }"""),
    ("""    public ChartRules Charts = new();""", """    public ChartRules Charts = new();
    public ShelfRules Shelves = new();"""),
])
sub("logic/Rpg/CraftingCharts.cs", [
    ("""    /// <summary>A chart's heat as it drops, by its rarity (plain, fine, rare).</summary>""",
     """    /// <summary>What Rook asks for the storeroom's next shelf (her prices follow how she feels about you),
    /// or null if it has as many as it can hold. Priced against the economy: the second is about a
    /// Kerchief night's gold, the third and fourth the atlas's, the rest a long sink.</summary>
    public static int? ShelfPrice(CraftCtx x)
    {
        var r = Rules.Shelves;
        int have = x.World.Shelves;
        if (have >= r.Most) return null;
        int k = have - 1;
        return Price(x, r.Seller, k < r.Prices.Count ? r.Prices[k] : r.Then);
    }

    /// <summary>The next shelf bought, paid for and empty (false if it cannot be).</summary>
    public static bool BuyShelf(CraftCtx x)
    {
        if (ShelfPrice(x) is not int gold || x.Ch.Gold < gold) return false;
        x.Ch.Gold -= gold;
        for (int i = 0; i < World.WorldState.Shelf; i++) x.World.Stash.Add(null);
        return true;
    }

    /// <summary>A chart's heat as it drops, by its rarity (plain, fine, rare).</summary>"""),
])
sub("data/content/crafting.json", [
    (""" "_charts": "Working charts""",
     """ "_shelves": "Rook's storeroom by shelves of 24 (the owner's approval): one with the room; the next cost these, then 'then' each, to 'most'. Her prices follow how she feels about you.",
 "shelves": { "seller": "rook", "prices": [300, 1000, 2500], "then": 5000, "most": 8 },
 "_charts": "Working charts"""),
])
