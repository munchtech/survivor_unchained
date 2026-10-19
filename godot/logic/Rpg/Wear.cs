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

    /// <summary>The visual slot a piece id is for: its armor index row's (ArmorIndex.Shared), else the part after the last dot.</summary>
    public static string SlotOf(string pieceId) => ArmorIndex.Shared.SlotOf(pieceId);

    /// <summary>The part of a piece id after its last dot (a calling's piece: "warden.top" is for "top").</summary>
    public static string SlotOfId(string pieceId) => pieceId[(pieceId.LastIndexOf('.') + 1)..];

    /// <summary>Her calling's tattoos: part of her skin with that calling, always worn, never an equip slot.</summary>
    public const string Ink = "ink";

    /// <summary>What she is seen wearing (docs/handoff/armor.md item 7): visual slot -> piece id. `worn` is what her
    /// equipment (Of) or a shot's --wear puts on her; every visual slot left empty is filled from her calling's own pieces
    /// (CALLING.SLOT where the index has one), her calling's ink is always on, and each piece's covers hide the other
    /// visual slots it covers whatever else is worn. A piece the index does not know is left off, with a note why.</summary>
    public static Dictionary<string, string> Look(IReadOnlyDictionary<string, string> worn, string calling, ArmorIndex ix, List<string>? notes = null)
    {
        var r = new Dictionary<string, string>();
        foreach (var (vs, id) in worn)
        {
            if (ix.Find(id) is not { } row) { notes?.Add($"wear: piece '{id}' (for {vs}) is in no armor index; left off"); continue; }
            if (row.Slot == Ink) { notes?.Add($"wear: piece '{id}' is ink, which comes with its calling; left off"); continue; }
            r[row.Slot] = id;
        }
        var own = ix.Calling(calling);
        foreach (var (slot, id) in own)
            if (slot == Ink || !r.ContainsKey(slot)) r[slot] = id;
        var hidden = new HashSet<string>();
        foreach (var (slot, id) in r)
            foreach (var c in ix.Find(id)!.Covers)
                if (c != slot && c != Ink) hidden.Add(c);
        foreach (var h in hidden) r.Remove(h);
        return r;
    }

    /// <summary>The look's visual slots the calling's own full set wears exactly (and nothing else).</summary>
    public static bool IsCallingSet(IReadOnlyDictionary<string, string> look, string calling, ArmorIndex ix)
    {
        var full = Look(new Dictionary<string, string>(), calling, ix);
        return full.Count == look.Count && full.All(kv => look.TryGetValue(kv.Key, out var v) && v == kv.Value);
    }

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
