using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Rpg;

/// <summary>The two kits a survivor keeps (docs/CRAFTING_DESIGN.md 20.2).</summary>
public enum KitKind { Day, Night }

/// <summary>
/// The two kits (docs/CRAFTING_DESIGN.md 20.2): what is worn by day (the Verge, the Wayfinder's maps,
/// where the Marks work) and what is worn by night (wherever the ember burns: the scars and the story
/// nights, where the caged coals work). A coal does nothing in a map and a map's answers are wasted
/// where the ember carries the build, so without two kits every coal is a seam lost to the build.
///
/// The night kit holds only what differs: a slot it has nothing of its own in wears the day's piece,
/// so a survivor who never thinks about it is dressed the same day and night, and nobody dresses
/// twice. The kit goes on by itself with the place (Journey.StartBattle), so there is no swap to
/// remember.
///
/// Kept as: <see cref="CharacterData.Equipment"/> is what is on now; <see cref="CharacterData.NightOwn"/>
/// the slots where the night kit has a piece of its own; <see cref="CharacterData.OtherKit"/>, for
/// those slots only, the piece of the kit not on (the night's own by day; the day's, or nothing, by
/// night). Every other place in the game reads what is worn now, and is right in either kit.
/// </summary>
public static class Kits
{
    public static KitKind On(CharacterData ch) => ch.NightOn ? KitKind.Night : KitKind.Day;

    static bool Own(CharacterData ch, EquipSlot s) => ch.NightOwn?.Contains(s) == true;

    /// <summary>The kit the place wants put on: the night's where the ember burns.</summary>
    public static void Wear(CharacterData ch, KitKind k)
    {
        Tidy(ch);
        bool night = k == KitKind.Night;
        if (ch.NightOn == night) return;
        foreach (var s in ch.NightOwn ?? new())
            (ch.Equipment[s], ch.OtherKit![s]) = (ch.OtherKit![s], ch.Equipment[s]);
        ch.NightOn = night;
    }

    /// <summary>What a kit wears in a slot: by night, the day's piece where it has none of its own.</summary>
    public static ItemInstance? Piece(CharacterData ch, KitKind k, EquipSlot s) =>
        k == KitKind.Night ? Own(ch, s) ? NightPiece(ch, s) : DayPiece(ch, s) : DayPiece(ch, s);

    /// <summary>Whether that kit has a piece of its own there (the day always does, or nothing).</summary>
    public static bool HasOwn(CharacterData ch, KitKind k, EquipSlot s) => k == KitKind.Day ? DayPiece(ch, s) != null : Own(ch, s);

    static ItemInstance? DayPiece(CharacterData ch, EquipSlot s) => ch.NightOn && Own(ch, s) ? ch.OtherKit![s] : ch.Equipment[s];
    static ItemInstance? NightPiece(CharacterData ch, EquipSlot s) => !Own(ch, s) ? null : ch.NightOn ? ch.Equipment[s] : ch.OtherKit![s];

    static void SetDay(CharacterData ch, EquipSlot s, ItemInstance? it)
    {
        if (ch.NightOn && Own(ch, s)) ch.OtherKit![s] = it;
        else ch.Equipment[s] = it;
    }

    /// <summary>Every piece set aside in the kit not on now (worn, but not this moment).</summary>
    public static IEnumerable<(EquipSlot Slot, ItemInstance Item)> Aside(CharacterData ch) =>
        (ch.NightOwn ?? new()).Where(s => ch.OtherKit?[s] != null).Select(s => (s, ch.OtherKit![s]!));

    /// <summary>A piece from the pack worn in a kit's slot (whatever the kit wore there goes back into
    /// the pack, into the place the piece came out of). The night's own piece in a slot it had none in
    /// stops it wearing the day's there.</summary>
    public static bool Put(CharacterData ch, KitKind k, ItemInstance it, EquipSlot s)
    {
        if (!Items.Fits(Items.Get(it.Def), s) || Inventory.Find(ch, it.Uid) is not { InPack: true } from) return false;
        if (k == KitKind.Day && On(ch) == KitKind.Day || k == KitKind.Night && On(ch) == KitKind.Night && Own(ch, s))
            return Inventory.Equip(ch, it, s);
        var prev = k == KitKind.Day ? DayPiece(ch, s) : NightPiece(ch, s);
        ch.Pack[from.Index] = prev;
        if (k == KitKind.Day) SetDay(ch, s, it);
        else
        {
            ch.OtherKit ??= new();
            if (!Own(ch, s)) (ch.NightOwn ??= new()).Add(s);
            if (ch.NightOn) { ch.OtherKit[s] = ch.Equipment[s]; ch.Equipment[s] = it; }
            else ch.OtherKit[s] = it;
        }
        return true;
    }

    /// <summary>A kit's piece taken off into the pack. Off the night kit, the slot wears the day's piece again.</summary>
    public static bool Clear(CharacterData ch, KitKind k, EquipSlot s)
    {
        if (k == KitKind.Day)
        {
            if (DayPiece(ch, s) is not { } d || !Inventory.AddToPack(ch, d)) return false;
            SetDay(ch, s, null);
            return true;
        }
        if (NightPiece(ch, s) is not { } n || !Inventory.AddToPack(ch, n)) return false;
        if (ch.NightOn) ch.Equipment[s] = ch.OtherKit![s];
        ch.OtherKit![s] = null;
        ch.NightOwn!.Remove(s);
        return true;
    }

    /// <summary>Whether the two kits are worth showing yet: once a coal or a Mark is owned, or the night
    /// kit holds anything (until then the night's kit is the day's).</summary>
    public static bool Shown(CharacterData ch) =>
        ch.NightOwn is { Count: > 0 } || Inventory.Everything(ch).Any(it => it.Affixes.Any(a => Items.Affix(a.Id) is { } d && (d.Kindled != null || d.Mark)));

    /// <summary>A slot the night kit holds that has lost its piece (taken off as it was worn, by a
    /// screen that knows nothing of kits) wears the day's again.</summary>
    static void Tidy(CharacterData ch)
    {
        if (ch.NightOwn == null) return;
        foreach (var s in ch.NightOwn.ToList())
            if (NightPiece(ch, s) == null)
            {
                if (ch.NightOn) ch.Equipment[s] = ch.OtherKit?[s];
                if (ch.OtherKit != null) ch.OtherKit[s] = null;
                ch.NightOwn.Remove(s);
            }
    }
}
