using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Rpg;

/* What she is seen wearing, read from what she has equipped (docs/handoff/armor.md item 1).
 * An item slot names a fixed group of visual slots; an item's Wear lists piece ids
 * ("warden.pauldrons" = <outfit>.<visual slot>), each of which must sit in its item slot's group.
 * A visual slot with no piece is left out: the view fills it from her calling's outfit. */
public static class Wear
{
    public static readonly string[] VisualSlots = ["top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots", "pauldrons", "cloak", "head"];

    static readonly string[] None = [];

    /// <summary>The visual slots an item slot covers (none for weapons, amulets, rings, relic).</summary>
    public static IReadOnlyList<string> Group(EquipSlot s) => s switch
    {
        EquipSlot.Head => ["head"],
        EquipSlot.Shoulders => ["pauldrons"],
        EquipSlot.Body => ["top", "collar"],
        EquipSlot.Bracers => ["bracers"],
        EquipSlot.Hands => ["gloves"],
        EquipSlot.Belt => ["belt", "skirt"],
        EquipSlot.Legs => ["bottom", "legwear", "greaves"],
        EquipSlot.Feet => ["boots"],
        EquipSlot.Cloak => ["cloak"],
        _ => None,
    };

    /// <summary>The visual slot a piece id is for: the part after the last dot.</summary>
    public static string SlotOf(string pieceId) => pieceId[(pieceId.LastIndexOf('.') + 1)..];

    /// <summary>Visual slot -> piece id, from what is equipped. Pieces outside their item slot's group are ignored.</summary>
    public static Dictionary<string, string> Of(Equipment eq, System.Func<string, ItemDef?>? find = null)
    {
        find ??= Items.Find;
        var r = new Dictionary<string, string>();
        foreach (var s in Items.EquipSlots)
        {
            if (eq[s] is not { } it || find(it.Def)?.Wear is not { } wear) continue;
            var group = Group(s);
            foreach (var p in wear) if (group.Contains(SlotOf(p))) r[SlotOf(p)] = p;
        }
        return r;
    }

    public static Dictionary<string, string> Of(CharacterData ch, System.Func<string, ItemDef?>? find = null) => Of(ch.Equipment, find);

    /// <summary>The piece ids of a def that its own item slot's group does not allow (or that name no visual slot).</summary>
    public static List<string> Validate(ItemDef def)
    {
        var bad = new List<string>();
        if (def.Wear == null) return bad;
        var slot = Items.SlotFor(def);
        var group = slot is EquipSlot s ? Group(s) : None;
        foreach (var p in def.Wear) if (!VisualSlots.Contains(SlotOf(p)) || !group.Contains(SlotOf(p))) bad.Add(p);
        return bad;
    }
}
