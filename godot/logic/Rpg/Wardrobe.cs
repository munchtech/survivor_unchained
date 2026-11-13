using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Rpg;

/// <summary>One dye (data/content/dyes.json): a colour a zone of a worn piece can take. Hex is Wear.DyeFinish's string
/// ("#rrggbb", or "#rrggbb:metal" for a metal finish). Unknown ones are learned (Wardrobe.LearnDye).</summary>
public sealed class DyeDef
{
    public string Id = "", Name = "", Hex = "";
    public List<string> Zones = new();
    public bool Known;
    /// <summary>Held back: the screen does not offer it yet (it reads wrong on the art).</summary>
    public bool Hold;
}

public sealed class DyesFile { public List<DyeDef> Dyes = new(); }

/* The wardrobe (bd-ui W18): looks collected from gear she has found, shown over any piece of the same place (head, body,
 * feet), and dyes, as data. It changes how she looks, never what she wears: her stats come from her equipment alone.
 * Her only: a look is listed or collected only for the sex whose cut it is (no cross-gender swap). The cloak is not
 * here: ch.Cloak is read into the Loadout and drawn by nothing today. */
public static class Wardrobe
{
    public static readonly string[] LookSlots = ["head", "body", "feet"];
    public static readonly string[] ZoneOrder = ["metal", "trim", "leather", "cloth"];

    public static EquipSlot EquipOf(string look) => look switch { "head" => EquipSlot.Head, "feet" => EquipSlot.Feet, _ => EquipSlot.Body };

    static DyesFile? file;
    public static IReadOnlyList<DyeDef> Dyes => (file ??= Json.Parse<DyesFile>(Json.ReadContent("dyes.json"))).Dyes;
    public static DyeDef? Dye(string? id) => id == null ? null : Dyes.FirstOrDefault(d => d.Id == id);

    /// <summary>The look slot ("head", "body", "feet") an item def is a look for, or null: not a look (no pieces, or not a place a look covers).</summary>
    public static string? SlotOf(ItemDef? def)
    {
        if (def?.Wear is not { Count: > 0 } || Items.SlotFor(def) is not EquipSlot s) return null;
        return s switch { EquipSlot.Head => "head", EquipSlot.Body => "body", EquipSlot.Feet => "feet", _ => null };
    }

    /// <summary>The sex a look is cut for: a def tagged "male" is his; every wearable cut so far is hers.</summary>
    public static Sex CutFor(ItemDef def) => def.Tags?.Contains("male") == true ? Sex.Male : Sex.Female;

    /// <summary>Is this def a look she (her sex) may collect and list?</summary>
    public static bool IsLookFor(CharacterData ch, ItemDef? def) => def != null && SlotOf(def) != null && CutFor(def) == (ch.Sex ?? Sex.Male);

    /// <summary>Adds the look of an item def she has found. False if it is not a look, not her cut, or already had.</summary>
    public static bool Collect(CharacterData ch, string defId)
    {
        if (!IsLookFor(ch, Items.Find(defId))) return false;
        ch.Looks ??= new();
        bool added = ch.Looks.Add(defId);
        // (two items that wear the same pieces are one look: the first of them stands for both, judge round 1 found two
        // identical tiles)
        if (Items.Find(defId) is { } d && Canonical(d) is { } c && c.Id != defId) added |= ch.Looks.Add(c.Id);
        return added;
    }

    static string PiecesKey(ItemDef d) => string.Join("|", (d.Wear ?? new()).OrderBy(x => x, StringComparer.Ordinal));

    /// <summary>The item that stands for a look: the first item (data order) of its slot wearing the same pieces.</summary>
    public static ItemDef? Canonical(ItemDef d)
    {
        if (SlotOf(d) is not { } slot) return null;
        var key = PiecesKey(d);
        return Items.All.Values.FirstOrDefault(o => SlotOf(o) == slot && o.Wear is { Count: > 0 } && PiecesKey(o) == key);
    }

    /// <summary>Everything worn and carried is found (old saves, starting gear).</summary>
    public static void BackFill(CharacterData ch)
    {
        ch.Looks ??= new(); ch.Shown ??= new(); ch.Dyes ??= new(); ch.DyesKnown ??= new();
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s] is { } e) Collect(ch, e.Def);
        foreach (var p in ch.Pack) if (p != null) Collect(ch, p.Def);
    }

    /// <summary>Every look of her cut in the game for a look slot, found or not, in item order.</summary>
    public static List<ItemDef> All(CharacterData ch, string slot) =>
        Items.All.Values.Where(d => SlotOf(d) == slot && IsLookFor(ch, d)).GroupBy(PiecesKey).Select(g => g.First()).ToList();

    public static List<ItemDef> Found(CharacterData ch, string slot) => All(ch, slot).Where(d => ch.Looks?.Contains(d.Id) == true).ToList();

    static string Calling(CharacterData ch) => ch.Archetype == "stalker" ? "ranger" : ch.Archetype;

    /// <summary>What a place draws for a set of worn pieces: the calling's own pieces fill what they leave, as HerWear lays them
    /// (a piece with no `wear` list leaves the whole group to the calling's kit). A sorted "slot=piece" key for the group.</summary>
    static string DrawnKey(CharacterData ch, Dictionary<string, string> worn, string slot)
    {
        var group = Wear.Group(EquipOf(slot));
        var look = Wear.Look(worn, Calling(ch), ArmorIndex.Shared);
        return string.Join("|", look.Where(kv => group.Contains(kv.Key)).OrderBy(kv => kv.Key, StringComparer.Ordinal).Select(kv => kv.Key + "=" + kv.Value));
    }

    /// <summary>The pieces "Your own" draws for a place (her equipped item's, else her calling's kit), as a key.</summary>
    public static string OwnDrawn(CharacterData ch, string slot) => DrawnKey(ch, Wear.Of(ch.Equipment), slot);

    /// <summary>The pieces a look draws for its place (over the calling's kit where it leaves gaps), as a key.</summary>
    public static string LookDrawn(CharacterData ch, ItemDef def, string slot)
    {
        var group = Wear.Group(EquipOf(slot));
        var w = new Dictionary<string, string>();
        foreach (var p in def.Wear ?? new()) if (group.Contains(Wear.SlotOf(p))) w[Wear.SlotOf(p)] = p;
        return DrawnKey(ch, w, slot);
    }

    /// <summary>A found look that draws exactly what "Your own" draws for this place: the two are one picture, so the screen shows one tile.</summary>
    public static ItemDef? OwnLook(CharacterData ch, string slot)
    {
        var key = OwnDrawn(ch, slot);
        return Found(ch, slot).FirstOrDefault(d => LookDrawn(ch, d, slot) == key);
    }

    /// <summary>Does her own piece of this place have a look of its own (a `wear` list)? False for none worn too.</summary>
    public static bool OwnHasLook(CharacterData ch, string slot) =>
        ch.Equipment[EquipOf(slot)] is { } w && Items.Find(w.Def)?.Wear is { Count: > 0 };

    public static (int Found, int Total) Count(CharacterData ch)
    {
        int f = 0, t = 0;
        foreach (var s in LookSlots) { t += All(ch, s).Count; f += Found(ch, s).Count; }
        return (f, t);
    }

    /// <summary>The look shown over a slot, if she has found it and it is hers (a look not collected is ignored).</summary>
    public static ItemDef? ShownDef(CharacterData ch, string slot, Func<string, ItemDef?>? find = null)
    {
        find ??= Items.Find;
        if (ch.Shown == null || !ch.Shown.TryGetValue(slot, out var id) || ch.Looks?.Contains(id) != true) return null;
        var def = find(id);
        return def != null && SlotOf(def) == slot && CutFor(def) == (ch.Sex ?? Sex.Male) ? def : null;
    }

    /// <summary>Wear.Of's look over the equipment: each shown look's pieces replace the group's pieces, even over an empty slot.</summary>
    public static void Overlay(CharacterData ch, Dictionary<string, string> worn, Func<string, ItemDef?>? find = null)
    {
        foreach (var slot in LookSlots)
        {
            if (ShownDef(ch, slot, find) is not { } def) continue;
            var group = Wear.Group(EquipOf(slot));
            foreach (var g in group) worn.Remove(g);
            foreach (var p in def.Wear!) if (group.Contains(Wear.SlotOf(p))) worn[Wear.SlotOf(p)] = p;
        }
    }

    /// <summary>Wear.DyeOf's wardrobe dyes: a known dye set on a look slot's zone wins over the worn item's own dye for that zone.</summary>
    public static void OverlayDyes(CharacterData ch, Dictionary<string, Dictionary<string, string>> dyes, Func<string, ItemDef?>? find = null)
    {
        if (ch.Dyes == null || ch.Dyes.Count == 0) return;
        var worn = Wear.Of(ch, find);
        var offered = Offered(ch);
        foreach (var slot in LookSlots)
        {
            if (!ch.Dyes.TryGetValue(slot, out var zones) || zones.Count == 0) continue;
            var group = Wear.Group(EquipOf(slot));
            foreach (var (vs, piece) in worn)
            {
                if (!group.Contains(vs)) continue;
                var d = dyes.TryGetValue(piece, out var own) ? new Dictionary<string, string>(own) : new();
                foreach (var (zone, id) in zones)
                    if (Dye(id) is { } dd && offered.Contains(dd) && dd.Zones.Contains(zone)) d[zone] = dd.Hex;
                if (d.Count > 0) dyes[piece] = d;
            }
        }
    }

    /// <summary>The dyes she may use: the known ones and those she has learned.</summary>
    public static List<DyeDef> Offered(CharacterData ch) => Dyes.Where(d => !d.Hold && (d.Known || ch.DyesKnown?.Contains(d.Id) == true)).ToList();

    public static bool LearnDye(CharacterData ch, string id)
    {
        if (Dye(id) is not { } d || d.Known) return false;
        ch.DyesKnown ??= new();
        return ch.DyesKnown.Add(id);
    }

    /// <summary>The pieces of a look slot as drawn now: the shown look's, else the equipped item's.</summary>
    public static List<string> PiecesOf(CharacterData ch, string slot, Func<string, ItemDef?>? find = null)
    {
        var group = Wear.Group(EquipOf(slot));
        return Wear.Of(ch, find).Where(kv => group.Contains(kv.Key)).Select(kv => kv.Value).ToList();
    }

    static Dictionary<string, string>? zoneOfKey;

    /// <summary>The dye zones a piece actually has (metal, trim, leather, cloth), from its meshes' material keys in outfit_materials.json.</summary>
    public static List<string> ZonesOf(string pieceId, ArmorIndex? ix = null)
    {
        if (zoneOfKey == null)
        {
            zoneOfKey = new();
            if (ArmorIndex.Text("people/outfit_materials.json") is string json)
                using (var doc = JsonDocument.Parse(json))
                    foreach (var p in doc.RootElement.EnumerateObject())
                        if (p.Value.TryGetProperty("zone", out var z) && z.GetString() is { } zs) zoneOfKey[p.Name] = zs;
        }
        var found = new HashSet<string>();
        foreach (var m in (ix ?? ArmorIndex.Shared).Find(pieceId)?.Meshes ?? new())
            if (zoneOfKey.TryGetValue(m[(m.LastIndexOf('.') + 1)..], out var z)) found.Add(z);
        return ZoneOrder.Where(found.Contains).ToList();
    }

    /// <summary>The zones of everything a look slot draws now, in order.</summary>
    public static List<string> ZonesOfSlot(CharacterData ch, string slot) =>
        PiecesOf(ch, slot).SelectMany(p => ZonesOf(p)).Distinct().OrderBy(z => Array.IndexOf(ZoneOrder, z)).ToList();

    public static void SetShown(CharacterData ch, string slot, string? defId)
    {
        ch.Shown ??= new();
        if (defId == null) ch.Shown.Remove(slot); else ch.Shown[slot] = defId;
    }

    public static void SetDye(CharacterData ch, string slot, string zone, string? dyeId)
    {
        ch.Dyes ??= new();
        if (dyeId == null)
        {
            if (ch.Dyes.TryGetValue(slot, out var z)) { z.Remove(zone); if (z.Count == 0) ch.Dyes.Remove(slot); }
            return;
        }
        if (!ch.Dyes.TryGetValue(slot, out var zones)) ch.Dyes[slot] = zones = new();
        zones[zone] = dyeId;
    }
}
