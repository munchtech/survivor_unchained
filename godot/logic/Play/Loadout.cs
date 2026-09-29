using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* What the survivor looks like and visibly carries (the web game's
 * game/loadout.ts): a person in their calling's clothes, dyed its colours,
 * with the chosen skin and hair; the weapon in hand as a real model, the
 * stance they hold it in, and the swings the arm makes when the blade
 * fires. The view builds the figure from this. */

/// <summary>A person's weapons, by the item in hand: what each hand holds,
/// the stance, and library clips (Universal Animation Libraries).</summary>
public sealed record HeldArms(string Right, string? Left, string? Forearm, string Idle, string[] Attack, string Heavy, string? Cast = null);

public sealed record Loadout(PersonSpec Person, HeldArms Arms, string? Cloak);

public static class Loadouts
{
    static readonly string[] Sword = ["Sword_Regular_A", "Sword_Regular_B", "Sword_Regular_C"];

    static readonly Dictionary<string, HeldArms> Held = new()
    {
        ["worn_oathblade"] = new("chevalier_sword", null, "shield_round", "Sword_Idle", Sword, "Sword_Attack"),
        ["judgement_disc_item"] = new("viking_sword", null, "shield_round", "Sword_Idle", ["OverhandThrow"], "Sword_Attack"),
        ["butchers_cleaver"] = new("viking_axe", null, null, "Sword_Idle", ["Sword_Attack", "Sword_Regular_B"], "Sword_Heavy_Combo"),
        ["gyre_axes"] = new("viking_axe", "viking_axe", null, "Sword_Idle", ["Sword_Regular_A", "Sword_Regular_C"], "Sword_Heavy_Combo"),
        ["apprentice_wand"] = new("short_staff", null, null, "Idle_Loop", ["Spell_Simple_Shoot"], "Spell_Simple_Enter", "Spell_Simple_Shoot"),
        // A staff stands upright in both hands.
        ["ember_staff"] = new("mage_staff", null, null, "Pistol_Idle_Loop", ["Spell_Simple_Shoot"], "Spell_Simple_Enter", "Spell_Simple_Shoot"),
        ["rime_rod"] = new("mage_staff", null, null, "Pistol_Idle_Loop", ["Spell_Simple_Shoot"], "Spell_Simple_Enter", "Spell_Simple_Shoot"),
        ["hunting_bow"] = new("crossbow", null, null, "Pistol_Idle_Loop", ["Pistol_Shoot"], "Pistol_Shoot"),
        ["knife_belt"] = new("daggers", "dagger_b", null, "Sword_Idle", ["OverhandThrow"], "Sword_Regular_Combo"),
    };

    /// <summary>Each calling's clothes. The Reaver goes bare-chested; a
    /// hood, where worn, covers the hair.</summary>
    static List<string> OutfitOf(string archetype, Sex sex, bool hood) =>
        Lore.OutfitFor(sex, archetype == "reaver" ? "bare" : archetype == "arcanist" ? "peasant" : "ranger", hood, archetype == "warden");

    static string Darker(string hex)
    {
        int v = Convert.ToInt32(hex[1..], 16);
        int C(int shift) => (int)Math.Round(((v >> shift) & 255) * 0.45);
        return $"#{C(16):x2}{C(8):x2}{C(0):x2}";
    }

    /// <summary>The survivor as their character sheet has them.</summary>
    public static Loadout Of(CharacterData ch)
    {
        var a = Callings.Archetype(ch.Archetype);
        var item = ch.Equipment.Weapon?.Def ?? a.Weapons[0];
        var held = Held.TryGetValue(item, out var h) ? h : Held[a.Weapons[0]];
        var sex = ch.Sex ?? Sex.Male;
        // The Stalker's hood by their model; the Warden's and Arcanist's as their headgear.
        bool hood = ch.Archetype == "stalker" ? (ch.Model == "" ? "rogue_hooded" : ch.Model) == "rogue_hooded" : ch.Archetype != "reaver" && (ch.Headgear ?? true);
        var pal = a.Palettes.FirstOrDefault(p => p.Id == ch.Palette) ?? a.Palettes[0];
        string? skin = Lore.Skins.FirstOrDefault(s => s.Id == ch.Skin)?.Color;
        string? hair = Lore.Hairs.FirstOrDefault(x => x.Id == ch.Hair)?.Color;
        string? cloak = ch.Cloak == "none" ? null : Lore.CloakDyes.FirstOrDefault(d => d.Id == ch.Cloak)?.Color;
        var person = new PersonSpec
        {
            Sex = sex, Outfit = OutfitOf(ch.Archetype, sex, hood),
            Hair = hood || ch.HairStyle == "none" ? null : ch.HairStyle ?? Lore.HairStyles(sex)[0],
            Beard = sex == Sex.Male && (ch.Beard ?? true),
            HairColor = string.IsNullOrEmpty(hair) ? null : hair, Skin = string.IsNullOrEmpty(skin) ? null : skin, Figure = ch.Figure,
            // The calling's colours dye the cloth; trousers take the darker
            // colour (or the cloth's, darker still).
            Dye = pal.Paint.TryGetValue("cloth", out var cloth)
                ? new Dye { Cloth = cloth, Under = pal.Paint.TryGetValue("under", out var under) ? under : Darker(cloth) } : null,
        };
        return new Loadout(person, held, string.IsNullOrEmpty(cloak) ? null : cloak);
    }
}
