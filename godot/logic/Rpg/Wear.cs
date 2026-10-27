using System;
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

    /// <summary>A slot whose piece hangs from another slot's piece (a skirt hangs from its belt): slot -> slot it hangs from.</summary>
    public static readonly IReadOnlyDictionary<string, string> Hangs = new Dictionary<string, string> { ["skirt"] = "belt" };

    static string SourceOf(ArmorIndex ix, string id) => ix.Find(id)?.Outfit ?? id[..Math.Max(id.LastIndexOf('.'), 0)];

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

    /// <summary>The callings, in the order a fill's fallback is looked for (OutfitChannels' order).</summary>
    public static readonly string[] FallbackOrder = ["warden", "arcanist", "reaver", "ranger"];

    /// <summary>What she is seen wearing (docs/handoff/armor.md item 7): visual slot -> piece id. `worn` is what her
    /// equipment (Of) or a shot's --wear puts on her; every visual slot left empty is filled from her calling's own pieces
    /// (CALLING.SLOT where the index has one), and her calling's ink is always on. An equipped piece's covers hide the
    /// other visual slots it covers, equipped or not (a suit hides what it covers). A fill never hides an equipped piece
    /// (loot the player put on must show): a fill whose covers reach a slot an equipped piece shows in is dropped, and
    /// its own slot is filled by the first calling in FallbackOrder whose piece for that slot covers that slot only, or
    /// left empty with a note. A calling row displaced by an equipped piece puts its `under` pieces on in its place (the
    /// arcanist's leotard top leaves the warden's bottom and belt), each in its own slot unless that is equipped or hidden.
    /// A piece the index does not know is left off, with a note why.</summary>
    public static Dictionary<string, string> Look(IReadOnlyDictionary<string, string> worn, string calling, ArmorIndex ix, List<string>? notes = null, IReadOnlyCollection<string>? hide = null)
    {
        // (`hide`: visual slots left empty, no equipped piece and no fill: her show-helm toggle off leaves "head" bare)
        bool Hid(string slot) => hide != null && hide.Contains(slot);
        var eq = new Dictionary<string, string>();
        foreach (var (vs, id) in worn)
        {
            if (ix.Find(id) is not { } row) { notes?.Add($"wear: piece '{id}' (for {vs}) is in no armor index; left off"); continue; }
            if (row.Slot == Ink) { notes?.Add($"wear: piece '{id}' is ink, which comes with its calling; left off"); continue; }
            if (Hid(row.Slot)) continue;
            eq[row.Slot] = id;
        }
        // (what equipped pieces hide: each other too)
        var hidden = new HashSet<string>();
        foreach (var (slot, id) in eq)
            foreach (var c in ix.Find(id)!.Covers)
                if (c != slot && c != Ink) hidden.Add(c);
        var r = eq.Where(kv => !hidden.Contains(kv.Key)).ToDictionary(kv => kv.Key, kv => kv.Value);
        bool HidesEquipped(string slot, string id) => ix.Find(id)!.Covers.Any(c => c != slot && c != Ink && r.ContainsKey(c) && eq.ContainsKey(c));
        foreach (var (slot, id) in ix.Calling(calling))
        {
            if (slot == Ink) { r[slot] = id; continue; }
            if (eq.ContainsKey(slot) || hidden.Contains(slot) || Hid(slot)) continue;
            if (Hangs.TryGetValue(slot, out var from) && eq.TryGetValue(from, out var held) && SourceOf(ix, held) != SourceOf(ix, id))
            {
                notes?.Add($"wear: {calling}'s '{id}' hangs from {from}, which holds '{held}'; {slot} left empty");
                continue;
            }
            if (!HidesEquipped(slot, id)) { r[slot] = id; continue; }
            var fb = FallbackOrder.Select(c => ix.Find($"{c}.{slot}")).FirstOrDefault(p => p is { } p_ && p_.Covers.Count == 1 && p_.Covers[0] == slot);
            if (fb != null) { r[slot] = fb.Id; notes?.Add($"wear: {calling}'s '{id}' would hide an equipped piece; {slot} filled with '{fb.Id}'"); }
            else notes?.Add($"wear: {calling}'s '{id}' would hide an equipped piece, and no calling has a {slot} that covers only {slot}; {slot} left empty");
        }
        // (a calling row displaced by an equipped piece leaves its `under` pieces in its place)
        foreach (var (slot, id) in ix.Calling(calling))
        {
            if (slot == Ink || ix.Find(id) is not { Under: { Count: > 0 } under }) continue;
            if (!(eq.ContainsKey(slot) || hidden.Contains(slot))) continue;
            foreach (var u in under)
            {
                if (ix.Find(u) is not { } ur) { notes?.Add($"wear: {calling}'s '{id}' lists unknown under piece '{u}'; skipped"); continue; }
                if (eq.ContainsKey(ur.Slot) || hidden.Contains(ur.Slot) || Hid(ur.Slot)) continue;
                r[ur.Slot] = u;
                notes?.Add($"wear: {calling}'s '{id}' is displaced; '{u}' worn under it");
            }
        }
        // (and what the fills kept hide, of the other fills)
        foreach (var (slot, id) in r.ToList())
        {
            if (eq.ContainsKey(slot)) continue;
            foreach (var c in ix.Find(id)!.Covers)
                if (c != slot && c != Ink && !eq.ContainsKey(c)) r.Remove(c);
        }
        if (hide != null) foreach (var h in hide) r.Remove(h);
        return r;
    }

    /// <summary>The look's visual slots the calling's own full set wears exactly (and nothing else).</summary>
    public static bool IsCallingSet(IReadOnlyDictionary<string, string> look, string calling, ArmorIndex ix)
    {
        // (a stand-in piece (a row's `replaces`) is not the calling's own outfit file: not its full set)
        if (look.Values.Any(id => ix.Find(id)?.Replaces != null)) return false;
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

    /// <summary>Splits a dye string: "#rrggbb", "#rrggbb:metal" or "#rrggbb:paint" (suffix case-insensitive, whitespace trimmed).
    /// An explicit suffix wins. With none, Metal is true only for a near-neutral light colour (HSV saturation under 0.15 and
    /// value at least 0.5: silver, steel, pewter); every other colour is paint. Gold, bronze and brass dyes must carry ":metal"
    /// (a hue can't tell gold from yellow paint). Hex comes back without the suffix.</summary>
    public static (string Hex, bool Metal) DyeFinish(string dye)
    {
        var parts = dye.Split(':', 2);
        var hex = parts[0].Trim();
        if (parts.Length == 2)
        {
            var sfx = parts[1].Trim();
            if (sfx.Equals("metal", StringComparison.OrdinalIgnoreCase)) return (hex, true);
            if (sfx.Equals("paint", StringComparison.OrdinalIgnoreCase)) return (hex, false);
        }
        var h = hex.TrimStart('#');
        if (h.Length < 6 || !int.TryParse(h.AsSpan(0, 6), System.Globalization.NumberStyles.HexNumber, null, out var v)) return (hex, false);
        double r = (v >> 16 & 255) / 255.0, g = (v >> 8 & 255) / 255.0, b = (v & 255) / 255.0;
        double mx = Math.Max(r, Math.Max(g, b)), mn = Math.Min(r, Math.Min(g, b));
        double sat = mx <= 0 ? 0 : (mx - mn) / mx;
        return (hex, sat < 0.15 && mx >= 0.5);
    }

    /// <summary>The darker bronze her trim takes under a gold plate dye (Body 18 judge 1: #8a5c30 read as flat tarnished brown; warmer toward copper and ~10% lighter. A trial hex can replace it: env GOLD_TRIM, read in HerWear).</summary>
    public const string GoldTrimBronze = "#9c6434:metal";

    /// <summary>Why: a gold metal dye on the "metal" zone makes the plate the same colour as the gold trim (trim zone: gold, claspgold,
    /// wiregold, bronze, rivetbronze), which swallows the trim. When the "metal" entry is a metal dye whose colour is gold or brass
    /// (HSV hue 25-65 deg, saturation at least 0.3, value at least 0.45) and the dict has no "trim" entry, returns a copy with
    /// "trim" set to GoldTrimBronze. An explicit "trim" dye always wins. Any other dye comes back as the same instance.</summary>
    public static IReadOnlyDictionary<string, string> TrimUnderGold(IReadOnlyDictionary<string, string> dye)
    {
        if (dye.ContainsKey("trim") || !dye.TryGetValue("metal", out var m)) return dye;
        var (hex, metal) = DyeFinish(m);
        var h = hex.TrimStart('#');
        if (!metal || h.Length < 6 || !int.TryParse(h.AsSpan(0, 6), System.Globalization.NumberStyles.HexNumber, null, out var v)) return dye;
        double r = (v >> 16 & 255) / 255.0, g = (v >> 8 & 255) / 255.0, b = (v & 255) / 255.0;
        double mx = Math.Max(r, Math.Max(g, b)), mn = Math.Min(r, Math.Min(g, b)), d = mx - mn;
        if (d <= 0 || d / mx < 0.3 || mx < 0.45) return dye;
        double hue = mx == r ? 60 * (((g - b) / d + 6) % 6) : mx == g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
        if (hue < 25 || hue > 65) return dye;
        return new Dictionary<string, string>(dye) { ["trim"] = GoldTrimBronze };
    }

    /// <summary>Piece id -> dye zone -> "#rrggbb", from the equipped items that wear pieces and carry a dye (ItemInstance.Dye).</summary>
    public static Dictionary<string, Dictionary<string, string>> DyeOf(Equipment eq, System.Func<string, ItemDef?>? find = null)
    {
        find ??= Items.Find;
        var r = new Dictionary<string, Dictionary<string, string>>();
        foreach (var s in Items.EquipSlots)
        {
            if (eq[s] is not { Dye: { Count: > 0 } dye } it || find(it.Def)?.Wear is not { } wear) continue;
            var group = Group(s);
            foreach (var p in wear) if (group.Contains(SlotOf(p))) r[p] = new Dictionary<string, string>(dye);
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
