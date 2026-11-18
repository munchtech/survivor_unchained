using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Sound;

/// <summary>
/// Which recorded sound a piece put on makes, by the slot it goes to (the owner's gear sounds, 16 Nov 2026). Godot-free so a test
/// can hold it: the body is plate, the head and the feet are helm-and-boots, anything else (a weapon, an off-hand, a ring, an
/// amulet, a gem in a socket) is the interface's own equip. The chain is tried in order and the first banked event plays.
/// </summary>
public static class EquipCue
{
    public static string[] Chain(EquipSlot? slot) => slot switch
    {
        EquipSlot.Body => ["equip.plate", "ui.equip"],
        EquipSlot.Head or EquipSlot.Feet => ["equip.helm_boots", "ui.equip"],
        _ => ["ui.equip"],
    };

    /// <summary>The wardrobe's look slots ("head", "body", "feet") are the same three.</summary>
    public static EquipSlot? OfLook(string look) => look switch { "head" => EquipSlot.Head, "body" => EquipSlot.Body, "feet" => EquipSlot.Feet, _ => null };
}
