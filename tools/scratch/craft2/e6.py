from js import load, save
from ed import sub
d = load("items")
it = d["items"]
# Insert the new things after their kin, so the file reads in order.
new = {}
for k, v in it.items():
    new[k] = v
    if k == "health_draught":
        new["moonpetal_draught"] = {
            "id": "moonpetal_draught", "name": "Moonpetal Draught", "kind": "consumable", "rarity": 2, "icon": "moon_draught",
            "value": 45, "stack": 10, "description": "Heals 60% of your health.", "consumable": {"heal": 0.6},
            "lore": "Silver, and cold as the night it was picked in.",
        }
    if k == "greymuzzle_fang":
        new["shed_fur_braid"] = {
            "id": "shed_fur_braid", "name": "Braid of Shed Fur", "kind": "amulet", "rarity": 2, "icon": "fur_braid", "value": 90,
            "description": "30% less from wolves.",
            "mods": [{"stat": "from.wolf", "kind": "flat", "value": 0.3, "source": "item"}],
            "lore": "Grey and grey and white, bitten off at the end.",
        }
new["wennas_flask"] = {
    "id": "wennas_flask", "name": "Wenna's Flask", "kind": "tool", "rarity": 1, "icon": "flask", "value": 120,
    "description": "Each night you sleep at the inn, Rook tops your health draughts up to three, a bitterroot a draught.",
    "lore": "Pewter, a lid that fits, her mark on the bottom.",
}
d["items"] = new
save("items", d)

sub('logic/Rpg/Items.cs', [
("""    /// <summary>The least rarity it rolls on (skills come only on fine gear).</summary>
    public int MinRarity;""",
"""    /// <summary>The least rarity it rolls on (skills come only on fine gear).</summary>
    public int MinRarity;
    /// <summary>Given, never rolled: a trophy's power set into a piece (Greymuzzle's fang).</summary>
    public bool Unique;"""),
("""        /* Skills worn: fine gear that fights for you. */""",
"""        /* Set, never rolled: a trophy's power in a piece (docs/CRAFTING_DESIGN.md 10.1). */
        new() { Id = "greymuzzles", Name = "Greymuzzle's", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Amulet], Unique = true,
            Mods = _ => [M(Stat.VsOf(Family.Wolf), ModKind.Flat, 0.3), M(Stat.VsOf(Family.Beast), ModKind.Flat, 0.3), M(Stat.VsOf(Family.Boar), ModKind.Flat, 0.3)],
            Text = _ => "+30% damage to wolves and beasts" },

        /* Skills worn: fine gear that fights for you. */"""),
])
sub('logic/Rpg/Character.cs', [
("""            var pool = Items.Affixes.Where(a => a.Slots.Contains(def.Kind) && it.Rarity >= a.MinRarity).ToList();""",
"""            var pool = Items.Affixes.Where(a => a.Slots.Contains(def.Kind) && it.Rarity >= a.MinRarity && !a.Unique).ToList();"""),
])
