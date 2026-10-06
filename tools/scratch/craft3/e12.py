"""The story lead's words for scar-glass and Rook's shelves, verbatim; the first glass said at the night's end."""
from ed import sub
sub("data/content/items.json", [
    ("""   "description": "What a deep scar leaves for one who stays past the hour, once the stream runs clean. Steep a piece in it, from the pack: a grade past what the forge can do, or something strong with a price, or only the veins, or a grade lost. It sets the piece for good."
  },""",
     """   "description": "Steep a piece of gear in it by hand, as in a slurry jar: a grade past the forge, a power with a price, only the veins, or a grade lost. A night's scar leaves a piece for every hour you stay past winning it.",
   "lore": "Ground that a scar burned until it ran, gone to dark glass. It only forms where somebody stayed too long. Held to the light it is the blue of the ford lamps, and it is never quite cold."
  },"""),
])
sub("data/content/crafting.json", [
    ("""  "glassEvery": 60,
""", """  "glassEvery": 60,
  "glassFirst": "Where you stood longest, the ground has run and gone to glass. You break a piece off. It is still warm when you get home.",
"""),
    (""" "_charts": "Working charts""",
     """ "_rook": "Rook's words over a shelf sold (the story lead's), for the storeroom's page: the first, then any after.",
 "rook": { "shelf": "There. That shelf's yours, pet. Twenty-four things, and I've counted, so don't try for twenty-five.", "shelfMore": "Another? You'll have me sleeping in the yard. ...Go on, then. It's yours." },
 "_charts": "Working charts"""),
])
sub("logic/Rpg/Crafting.cs", [
    ("""    public int DeepFrom = 30, GlassFrom = 60, GlassEvery = 60;
    public string Glass = "scar_glass";""",
     """    public int DeepFrom = 30, GlassFrom = 60, GlassEvery = 60;
    public string Glass = "scar_glass";
    /// <summary>Said at the night's end the first time scar-glass is carried out (the story lead's).</summary>
    public string? GlassFirst;"""),
    ("""    public ShelfRules Shelves = new();""", """    public ShelfRules Shelves = new();
    /// <summary>Rook's words over a shelf sold: the first, then any after (the story lead's).</summary>
    public RookLines Rook = new();"""),
    ("""public sealed class ShelfRules {""", """public sealed class RookLines { public string? Shelf, ShelfMore; }
public sealed class ShelfRules {"""),
    ("""    /// <summary>The next shelf bought, paid for and empty (false if it cannot be).</summary>
    public static bool BuyShelf(CraftCtx x)
    {
        if (ShelfPrice(x) is not int gold || x.Ch.Gold < gold) return false;
        x.Ch.Gold -= gold;
        for (int i = 0; i < World.WorldState.Shelf; i++) x.World.Stash.Add(null);
        return true;
    }""",
     """    /// <summary>The next shelf bought, paid for and empty (false if it cannot be).</summary>
    public static bool BuyShelf(CraftCtx x)
    {
        if (ShelfPrice(x) is not int gold || x.Ch.Gold < gold) return false;
        x.Ch.Gold -= gold;
        for (int i = 0; i < World.WorldState.Shelf; i++) x.World.Stash.Add(null);
        return true;
    }

    /// <summary>What Rook says over the shelf just sold: the second shelf's line, then the later ones'.</summary>
    public static string? ShelfSaid(WorldState w) => w.Shelves <= 2 ? Rules.Rook.Shelf : Rules.Rook.ShelfMore ?? Rules.Rook.Shelf;"""),
])
sub("logic/Arena/Arena.cs", [
    ("""    public Dictionary<string, int> Carried { get; init; } = new();
    public Dictionary<string, int> Spilled { get; init; } = new();""",
     """    public Dictionary<string, int> Carried { get; init; } = new();
    public Dictionary<string, int> Spilled { get; init; } = new();
    /// <summary>What the haul looked like, said once (the first scar-glass carried out).</summary>
    public string? HaulSeen { get; init; }"""),
    ("""            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled,""",
     """            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled, HaulSeen = glassSeen,"""),
    ("""        j.Carry(carry, spec.Name);""",
     """        j.Carry(carry, spec.Name);
        // The first scar-glass carried out is said, once (the story lead's words).
        string? glassSeen = null;
        if (carry.Kept.ContainsKey(Crafting.Rules.Night.Glass) && !j.World.Fact("glass.seen").Truthy)
        {
            j.World.Facts["glass.seen"] = true;
            glassSeen = Crafting.Rules.Night.GlassFirst;
        }"""),
])
sub("src/Ui/ArenaResult.cs", [
    ("""        if (r.Carried.Count > 0 || r.Spilled.Count > 0) Next(Haul(r.Carried, r.Spilled, "Carried out, for the Waystation's hands"), () => Sound.Sfx.Loot(), 0.55);""",
     """        if (r.Carried.Count > 0 || r.Spilled.Count > 0) Next(Haul(r.Carried, r.Spilled, "Carried out, for the Waystation's hands"), () => Sound.Sfx.Loot(), 0.55);
        if (r.HaulSeen is { } seen) Next(Style.Label(seen, Style.TextItalic, Style.Small, Style.InkDim, true), null, 0.5);"""),
])
sub("src/Ui/Pack.cs", [
    ("""                if (!Crafting.BuyShelf(G.Journey.Craft)) { Sound.Sfx.Deny(); return; }
                Sound.Sfx.Loot(false);
                Refresh();""",
     """                if (!Crafting.BuyShelf(G.Journey.Craft)) { Sound.Sfx.Deny(); return; }
                Sound.Sfx.Loot(false);
                said = Crafting.ShelfSaid(G.Journey.World);
                Refresh();"""),
    ("""            store.AddChild(Style.H(Style.Gap3, buy, Style.Label(can ? $"{WorldState.Shelf} more places" : $"{price} gold; you have {Math.Floor(ch.Gold)}", Style.TextItalic, Style.Small, can ? Style.InkDim : Style.Bad)));
        }""",
     """            store.AddChild(Style.H(Style.Gap3, buy, Style.Label(can ? $"{WorldState.Shelf} more places" : $"{price} gold; you have {Math.Floor(ch.Gold)}", Style.TextItalic, Style.Small, can ? Style.InkDim : Style.Bad)));
        }
        // What Rook said over the shelf she just sold.
        if (said != null) store.AddChild(Style.Label($"“{said}”", Style.TextItalic, Style.Body, Style.Ink, true));"""),
    ("""    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }""",
     """    public StashScreen(Game g) : base(g) { Nav.Prefer = "mine:0"; }

    /// <summary>Rook's words over a shelf just sold.</summary>
    string? said;"""),
])
