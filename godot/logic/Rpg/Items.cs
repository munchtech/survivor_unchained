using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* Things the survivor can carry.
 *
 * The rule for this game's gear: an item should change how you play or how
 * the world treats you, not only what a number says. So beside stat mods,
 * items carry the weapon they put in your hands, rules they add to the
 * machine (triggers), what the WORLD sees (tags: a wolf-fang necklace is a
 * statement to a wolf), the statuses they apply, and the price, said
 * plainly. Plain drops roll affixes; named things never do.
 *
 * The items themselves are data (data/content/items.json, the web game's
 * own list); the affixes are rules, and are written here. */

public enum ItemKind { Weapon, Offhand, Head, Body, Cloak, Amulet, Ring, Relic, Material, Consumable, Quest, Tool, Trophy }
public enum EquipSlot { Weapon, Offhand, Head, Body, Cloak, Amulet, Ring1, Ring2, Relic }

public sealed class ItemWeapon { public string Id = ""; public int Rank = 1; }
public sealed class Consumable
{
    public double? Heal;
    public List<string>? Cure;
    public string? Buff;
    /// <summary>A manual: the art it teaches.</summary>
    public string? Teaches;
}

public sealed class ItemDef
{
    public string Id = "", Name = "", Icon = "", Description = "";
    public ItemKind Kind;
    public int Rarity;
    public double Value;
    public string? Lore, Downside;
    public ItemWeapon? Weapon;
    public List<StatMod>? Mods;
    public List<TriggerDef>? Triggers;
    public List<string>? Tags;
    public List<StatusKind>? Statuses;
    public int? Stack;
    /// <summary>Rolls affixes when it drops.</summary>
    public bool Base;
    public Consumable? Consumable;
    public bool Unique;
}

public sealed class AffixDef
{
    public string Id = "", Name = "";
    public bool Prefix;
    public ItemKind[] Slots = Array.Empty<ItemKind>();
    public Func<int, StatMod[]> Mods = _ => Array.Empty<StatMod>();
    public Func<int, string> Text = _ => "";
}

public static class Items
{
    sealed class File { public Dictionary<string, ItemDef> Items = new(); public List<string> Raritynames = new(); }

    static Dictionary<string, ItemDef>? all;
    static List<string>? rarityNames;

    static void Load()
    {
        var f = Json.Parse<File>(Json.ReadContent("items.json"));
        all = f.Items;
        rarityNames = f.Raritynames;
    }

    public static Dictionary<string, ItemDef> All { get { if (all == null) Load(); return all!; } }
    public static IReadOnlyList<string> RarityNames { get { if (rarityNames == null) Load(); return rarityNames!; } }
    public static readonly EquipSlot[] EquipSlots = EnumKey<EquipSlot>.All;

    public static ItemDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown item {id}");
    public static ItemDef? Find(string id) => All.TryGetValue(id, out var d) ? d : null;

    static StatMod M(string stat, ModKind kind, double value) => new(stat, kind, value, "item");
    static string Pct(double v) => $"{MathX.RoundInt(v * 100)}%";
    static string F1(double v) => v.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);

    public static readonly AffixDef[] Affixes =
    [
        new() { Id = "sturdy", Name = "Sturdy", Prefix = true, Slots = [ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Offhand],
            Mods = t => [M(Stat.Armor, ModKind.Flat, 1 + t)], Text = t => $"+{1 + t} armour" },
        new() { Id = "hale", Name = "Hale", Prefix = true, Slots = [ItemKind.Body, ItemKind.Amulet, ItemKind.Ring, ItemKind.Head],
            Mods = t => [M(Stat.MaxHealth, ModKind.Flat, 10 + t * 8)], Text = t => $"+{10 + t * 8} maximum health" },
        new() { Id = "fleet", Name = "Fleet", Prefix = true, Slots = [ItemKind.Cloak, ItemKind.Ring, ItemKind.Amulet],
            Mods = t => [M(Stat.MoveSpeed, ModKind.Inc, 0.03 + t * 0.02)], Text = t => $"+{Pct(0.03 + t * 0.02)} movement speed" },
        new() { Id = "keen", Name = "Keen", Prefix = true, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Head],
            Mods = t => [M(Stat.CritChance, ModKind.Flat, 0.02 + t * 0.015)], Text = t => $"+{F1(2 + t * 1.5)}% critical chance" },
        new() { Id = "searing", Name = "Searing", Prefix = true, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.DamageOf(School.Fire), ModKind.Inc, 0.08 + t * 0.05)], Text = t => $"+{Pct(0.08 + t * 0.05)} fire damage" },
        new() { Id = "rimed", Name = "Rimed", Prefix = true, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.DamageOf(School.Frost), ModKind.Inc, 0.08 + t * 0.05)], Text = t => $"+{Pct(0.08 + t * 0.05)} frost damage" },
        new() { Id = "honed", Name = "Honed", Prefix = true, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.DamageOf(School.Physical), ModKind.Inc, 0.08 + t * 0.05)], Text = t => $"+{Pct(0.08 + t * 0.05)} physical damage" },
        new() { Id = "hallowed", Name = "Hallowed", Prefix = true, Slots = [ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = t => [M(Stat.DamageOf(School.Holy), ModKind.Inc, 0.1 + t * 0.05)], Text = t => $"+{Pct(0.1 + t * 0.05)} holy damage" },
        new() { Id = "of_haste", Name = "of Haste", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Cloak],
            Mods = t => [M(Stat.Cooldown, ModKind.More, -(0.03 + t * 0.02))], Text = t => $"{Pct(0.03 + t * 0.02)} faster weapons" },
        new() { Id = "of_reach", Name = "of Reach", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Head],
            Mods = t => [M(Stat.Area, ModKind.Inc, 0.05 + t * 0.03)], Text = t => $"+{Pct(0.05 + t * 0.03)} area" },
        new() { Id = "of_the_wolf", Name = "of the Wolf", Prefix = false, Slots = [ItemKind.Cloak, ItemKind.Body, ItemKind.Head, ItemKind.Amulet],
            Mods = t => [M(Stat.FromOf(Family.Wolf), ModKind.Flat, 0.1 + t * 0.05)], Text = t => $"{Pct(0.1 + t * 0.05)} less damage from wolves" },
        new() { Id = "of_embers", Name = "of Embers", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Relic],
            Mods = t => [M(Stat.XpGain, ModKind.Inc, 0.05 + t * 0.03)], Text = t => $"+{Pct(0.05 + t * 0.03)} ember gained" },
        new() { Id = "of_mending", Name = "of Mending", Prefix = false, Slots = [ItemKind.Body, ItemKind.Amulet, ItemKind.Ring],
            Mods = t => [M(Stat.Regen, ModKind.Flat, 0.2 + t * 0.2)], Text = t => $"+{F1(0.2 + t * 0.2)} health per second" },
        new() { Id = "of_the_grave", Name = "of the Grave", Prefix = false, Slots = [ItemKind.Cloak, ItemKind.Body, ItemKind.Amulet],
            Mods = t => [M(Stat.ResistOf(School.Shadow), ModKind.Flat, 0.08 + t * 0.05), M(Stat.FromOf(Family.Undead), ModKind.Flat, 0.05 + t * 0.03)],
            Text = t => $"+{Pct(0.08 + t * 0.05)} shadow resistance; less from the dead" },
        new() { Id = "of_greed", Name = "of Greed", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet],
            Mods = t => [M(Stat.GoldGain, ModKind.Inc, 0.1 + t * 0.08), M(Stat.PickupRadius, ModKind.Flat, 0.5 + t * 0.3)],
            Text = t => $"+{Pct(0.1 + t * 0.08)} gold, longer reach for pickups" },
    ];

    public static AffixDef? Affix(string id) => Array.Find(Affixes, a => a.Id == id);

    /// <summary>The slot an item goes in by default.</summary>
    public static EquipSlot? SlotFor(ItemDef def) => def.Kind switch
    {
        ItemKind.Weapon => EquipSlot.Weapon,
        ItemKind.Offhand => EquipSlot.Offhand,
        ItemKind.Head => EquipSlot.Head,
        ItemKind.Body => EquipSlot.Body,
        ItemKind.Cloak => EquipSlot.Cloak,
        ItemKind.Amulet => EquipSlot.Amulet,
        ItemKind.Ring => EquipSlot.Ring1,
        ItemKind.Relic => EquipSlot.Relic,
        _ => null,
    };

    public static bool Fits(ItemDef def, EquipSlot slot) => slot switch
    {
        EquipSlot.Ring1 or EquipSlot.Ring2 => def.Kind == ItemKind.Ring,
        EquipSlot.Offhand => def.Kind == ItemKind.Offhand || (def.Kind == ItemKind.Weapon && def.Weapon != null),
        _ => def.Kind.Key() == slot.Key(),
    };
}
