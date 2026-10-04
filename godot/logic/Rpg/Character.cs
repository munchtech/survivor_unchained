using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* The persistent character: everything about the survivor that outlives an
 * expedition. The ember build (weapon ranks, boons, evolutions) belongs to
 * the Battle and fades when you rest; this is what is left when it does.
 * Shaped as the web game's save is, field for field. */

public sealed class AffixRoll { public string Id = ""; public int Tier; }

public sealed class ItemInstance
{
    public string Uid = "", Def = "";
    public int Qty = 1, Rarity;
    public List<AffixRoll> Affixes = new();
    /// <summary>Given name for storied items ("Maeca's Last Arrow").</summary>
    public string? Name;
    /// <summary>Where it came from, one line per owner.</summary>
    public List<string>? History;
    /// <summary>How much more it can be worked (docs/CRAFTING_DESIGN.md, "Heat"): every
    /// craft spends some; at none it is set. Null on what can never be worked.</summary>
    public int? Heat;
    /// <summary>The heat it had when made, and what remaking added since: its bar's length.</summary>
    public int? HeatFull;
    /// <summary>How often it has been rekindled (each time dearer).</summary>
    public int? Rekindled;
    /// <summary>What the world can tell was worked into it ('wolf_pelts': the wolves smell it).</summary>
    public List<string>? Marks;
    /// <summary>How often its three coals have been drawn again today.</summary>
    public int? Draw;
    /// <summary>A Wayfinder's chart: the map it opens (docs/SKILLS_DESIGN.md §17.2).</summary>
    public Maps.Chart? Chart;
    /// <summary>The day it was last remade: a remade piece cools overnight before the next.</summary>
    public int? Remade;
    /// <summary>A trophy's power set into it (an affix id: Greymuzzle's fang), outside its seams:
    /// no grades, no heat, and its name leads the piece's.</summary>
    public string? Setting;
}

public enum ConditionId { Wounded, Blightsick, Poisoned, Blessed, Rested, Wolfscent, Hunted, Warmed }

public sealed class Condition { public ConditionId Id; public int Days; public string? Note; }

public sealed class Attributes { public int Might, Finesse, Wits, Resolve; }

public enum Sex { Male, Female }

/// <summary>What is worn and held, slot by slot.</summary>
public sealed class Equipment
{
    public ItemInstance? Weapon, Offhand, Head, Body, Cloak, Amulet, Ring1, Ring2, Relic;

    public ItemInstance? this[EquipSlot s]
    {
        get => s switch
        {
            EquipSlot.Weapon => Weapon, EquipSlot.Offhand => Offhand, EquipSlot.Head => Head, EquipSlot.Body => Body,
            EquipSlot.Cloak => Cloak, EquipSlot.Amulet => Amulet, EquipSlot.Ring1 => Ring1, EquipSlot.Ring2 => Ring2, _ => Relic,
        };
        set
        {
            switch (s)
            {
                case EquipSlot.Weapon: Weapon = value; break;
                case EquipSlot.Offhand: Offhand = value; break;
                case EquipSlot.Head: Head = value; break;
                case EquipSlot.Body: Body = value; break;
                case EquipSlot.Cloak: Cloak = value; break;
                case EquipSlot.Amulet: Amulet = value; break;
                case EquipSlot.Ring1: Ring1 = value; break;
                case EquipSlot.Ring2: Ring2 = value; break;
                default: Relic = value; break;
            }
        }
    }
}

public sealed class LifeStats
{
    public int Kills, Deaths, Expeditions, BossesSlain;
    public double GoldEarned;
    public List<string> Evolutions = new();
}

public sealed class CharacterData
{
    public int Version = 1;
    public string Id = "", Name = "", Archetype = "", Background = "", Model = "", Palette = "";
    /// <summary>Wears the calling's helm or hat.</summary>
    public bool? Headgear;
    /// <summary>Look: a dyed cloak (or none), skin, hair.</summary>
    public string? Cloak, Skin, Hair;
    /// <summary>The body: a man or a woman, their hair's cut, a beard, a woman's figure.</summary>
    public Sex? Sex;
    public string? HairStyle;
    public bool? Beard;
    /// <summary>A hero's own beard (Lore.Hero's beards), where their body has them.</summary>
    public string? BeardStyle;
    public double? Figure;
    /// <summary>A woman's face, eyes and face paint (her body's own: Loadouts.HerBody):
    /// her face's sliders (Lore.Hero's, -1 to 1; none set is her own face), her
    /// eyes' colour and the paint she wears (both Lore.Hero's).</summary>
    public Dictionary<string, double>? Face;
    public string? Eyes, Paint;
    /// <summary>The face she started from (Lore.Hero's faces): each its own
    /// painting of her skin, brows and lips, which her head wears (none: her own).</summary>
    public string? FaceShape;
    public int Level = 1;
    public double Xp;
    public Attributes Attributes = new();
    public int Points;
    public List<string> Traits = new();
    /// <summary>Trait picks owed from levels gained.</summary>
    public int TraitPicks;
    public List<string> Knowledge = new();
    public Equipment Equipment = new();
    public List<ItemInstance?> Pack = Inventory.NewPack();
    /// <summary>The materials pouch: crafting's materials by id, never in the pack's places.</summary>
    public Dictionary<string, int> Materials = new();
    public double Gold;
    /// <summary>The art in hand (the web game's id, 'shield_bash').</summary>
    public string Ability = "";
    /// <summary>Skills found in the arenas (taken as cards there): only these
    /// can be learned for the world.</summary>
    public List<string> Discovered = new();
    /// <summary>Combat skills learned for the day (Rpg/SkillBook.cs), and those carried.</summary>
    public List<string> Skills = new(), Slotted = new();
    /// <summary>Every art the survivor knows (Rpg/ArtBook.cs).</summary>
    public List<string> Known = new();
    /// <summary>How far each art has come, and its facets.</summary>
    public Dictionary<string, ArtState> Arts = new();
    public List<Condition> Conditions = new();
    /// <summary>Kills with each weapon, across every expedition.</summary>
    public Dictionary<string, int> Mastery = new();
    public LifeStats Stats = new();
    public bool Alive = true;
    public int CreatedDay = 1;
    public int NextUid = 1;

    public AbilityKind AbilityKind => Abilities.ById(Ability).Kind;
}

public sealed class CreationChoice
{
    public string Name = "", Archetype = "warden", Background = "hunter", Palette = "", WeaponItem = "", Ability = "";
    public string? Model, Cloak, Skin, Hair, HairStyle, Eyes, Paint, FaceShape, BeardStyle;
    public bool? Headgear, Beard;
    public Sex? Sex;
    public double? Figure;
    public Dictionary<string, double>? Face;
}

public static class Inventory
{
    public const int PackSize = 24;
    /// <summary>Kindled affixes a survivor's gear can bring to the ember at once.</summary>
    public const int MaxKindled = 2;
    /// <summary>The highest rank gear brings a skill in at: the smith starts it,
    /// the ember finishes it (ranks 5 to 8 and the evolution are the night's).</summary>
    public const int GearRankCap = 4;

    public static List<ItemInstance?> NewPack()
    {
        var p = new List<ItemInstance?>(PackSize);
        for (int i = 0; i < PackSize; i++) p.Add(null);
        return p;
    }

    static readonly Random loose = new();

    /// <summary>A new item; plain gear rolls its affixes.</summary>
    /// <param name="lean">Affixes it is likelier to roll (what answers the map it fell in).</param>
    /// <param name="dropped">It fell in the world: its heat is rolled (made or bought, it is full).</param>
    public static ItemInstance Make(CharacterData? ch, string defId, int qty = 1, int? rarity = null, uint? seed = null, List<AffixRoll>? affixes = null,
        IReadOnlyCollection<string>? lean = null, bool dropped = false)
    {
        var def = Items.Get(defId);
        string uid = ch != null ? $"i{ch.NextUid++}" : $"i{loose.Next(1_000_000_000):x}";
        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new() };
        if (Crafting.Workable(def)) it.Heat = it.HeatFull = Crafting.HeatAtMaking(it.Rarity, dropped ? new Rng(seed ?? (uint)loose.Next(1_000_000_000)) : null);
        if (def.Base && affixes == null)
        {
            var rng = new Rng(seed ?? (uint)loose.Next(1_000_000_000));
            int n = Math.Min(3, it.Rarity);
            var pool = Items.Affixes.Where(a => a.Slots.Contains(def.Kind) && it.Rarity >= a.MinRarity && !a.Unique).ToList();
            var picked = new HashSet<string>();
            bool hasPrefix = false, hasSuffix = false;
            // The passives the survivor's carried skills evolve with (the kindlings that would stand in for them).
            var wanted = ch == null ? new HashSet<string>() : SkillBook.Carried(ch)
                .SelectMany(w => Sim.LevelUp.EvolvesWith(w.Id).SelectMany(e => e.Passives)).Select(id => $"stand:{id}").ToHashSet();
            for (int k = 0; k < n && pool.Count > 0; k++)
            {
                // One kindling to an item.
                bool kindled = picked.Any(id => Items.Affix(id)?.Kindled != null);
                var cands = pool.Where(a => !picked.Contains(a.Id) && (a.Prefix ? !hasPrefix || n > 2 : !hasSuffix || n > 2) && !(kindled && a.Kindled != null)).ToList();
                if (cands.Count == 0) break;
                // What answers the map comes four times as often; a skill worn is rare, and a kindling rarer,
                // though one that stands in for what the survivor's carried skills evolve with comes twice as often.
                double W(AffixDef x) => (lean?.Contains(x.Id) == true ? 4 : 1) * (x.Grants != null ? 0.35 : 1) *
                    (x.Kindled == null ? 1 : 0.3 * (wanted.Contains(x.Kindled) ? 2 : 1));
                double total = cands.Sum(W), roll = rng.Next() * total;
                var a = cands[^1];
                foreach (var c in cands) { roll -= W(c); if (roll <= 0) { a = c; break; } }
                picked.Add(a.Id);
                if (a.Prefix) hasPrefix = true; else hasSuffix = true;
                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Max(0, Math.Min(3, it.Rarity - 1 + rng.Int(0, 1))) });
            }
        }
        return it;
    }

    public static string Name(ItemInstance it)
    {
        if (it.Name != null) return it.Name;
        var def = Items.Get(it.Def);
        var affs = it.Affixes.Select(a => Items.Affix(a.Id)).Where(a => a != null).ToList();
        // What is set in it leads: Greymuzzle's Worn Oathblade.
        if (it.Setting != null && Items.Affix(it.Setting) is { } set) affs.Insert(0, set);
        var pre = affs.FirstOrDefault(a => a!.Prefix);
        var suf = affs.FirstOrDefault(a => !a!.Prefix);
        return string.Join(" ", new[] { pre?.Name, def.Name, suf?.Name }.Where(s => !string.IsNullOrEmpty(s)));
    }

    public static string RarityName(ItemInstance it) => Items.RarityNames[Math.Min(Items.RarityNames.Count - 1, it.Rarity)];

    public static List<StatMod> Mods(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        string src = $"item:{it.Uid}";
        var o = (def.Mods ?? new()).Select(m => m with { Source = src }).ToList();
        foreach (var a in it.Affixes)
            if (Items.Affix(a.Id) is { } ad) o.AddRange(ad.Mods(a.Tier).Select(m => m with { Source = src }));
        if (it.Setting != null && Items.Affix(it.Setting) is { } set) o.AddRange(set.Mods(0).Select(m => m with { Source = src }));
        return o;
    }

    public static List<string> Lines(ItemInstance it) =>
        (it.Setting != null && Items.Affix(it.Setting) is { } set ? new[] { set.Text(0) } : Array.Empty<string>())
            .Concat(it.Affixes.Select(a => Items.Affix(a.Id)?.Text(a.Tier) ?? "")).ToList();

    public static bool AddToPack(CharacterData ch, ItemInstance it)
    {
        var def = Items.Get(it.Def);
        // Materials go in the pouch, which is never full.
        if (def.Kind == ItemKind.Material)
        {
            ch.Materials[it.Def] = ch.Materials.GetValueOrDefault(it.Def) + Math.Max(0, it.Qty);
            return true;
        }
        if (def.Stack is { } stack)
            foreach (var p in ch.Pack)
            {
                if (p == null || p.Def != it.Def || p.Qty >= stack) continue;
                int take = Math.Min(stack - p.Qty, it.Qty);
                p.Qty += take;
                it.Qty -= take;
                if (it.Qty <= 0) return true;
            }
        int i = ch.Pack.IndexOf(null);
        if (i < 0) return false;
        ch.Pack[i] = it;
        return true;
    }

    public static int Free(CharacterData ch) => ch.Pack.Count(p => p == null);

    /// <summary>How many more of a thing the pack could take (a material: any number, it goes in the pouch).</summary>
    public static int Room(CharacterData ch, string defId)
    {
        var def = Items.Get(defId);
        if (def.Kind == ItemKind.Material) return int.MaxValue;
        int stack = Math.Max(1, def.Stack ?? 1), n = Free(ch) * stack;
        foreach (var p in ch.Pack) if (p != null && p.Def == defId) n += Math.Max(0, stack - p.Qty);
        return n;
    }

    public static int Count(CharacterData ch, string defId)
    {
        int n = ch.Materials.GetValueOrDefault(defId);
        foreach (var p in ch.Pack) if (p?.Def == defId) n += p.Qty;
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s]?.Def == defId) n++;
        return n;
    }

    /// <summary>Take up to qty of an item from the pack; how many were taken.</summary>
    public static int Take(CharacterData ch, string defId, int qty = 1)
    {
        int left = qty;
        // The pouch first: that is where materials live.
        if (ch.Materials.TryGetValue(defId, out int have) && have > 0)
        {
            int t = Math.Min(left, have);
            left -= t;
            if (have - t > 0) ch.Materials[defId] = have - t; else ch.Materials.Remove(defId);
        }
        for (int i = 0; i < ch.Pack.Count && left > 0; i++)
        {
            var p = ch.Pack[i];
            if (p == null || p.Def != defId) continue;
            int t = Math.Min(left, p.Qty);
            p.Qty -= t;
            left -= t;
            if (p.Qty <= 0) ch.Pack[i] = null;
        }
        return qty - left;
    }

    /// <summary>The pouch as things to show and sell: one stack a material ('m:' and its id),
    /// in the materials' own order.</summary>
    public static List<ItemInstance> Pouch(CharacterData ch) =>
        ch.Materials.Where(kv => kv.Value > 0 && Items.Find(kv.Key) != null)
            .OrderBy(kv => Items.Get(kv.Key).Rarity).ThenBy(kv => Items.Get(kv.Key).Name)
            .Select(kv => new ItemInstance { Uid = PouchUid(kv.Key), Def = kv.Key, Qty = kv.Value, Rarity = Items.Get(kv.Key).Rarity }).ToList();

    public static string PouchUid(string defId) => $"m:{defId}";
    public static string? FromPouch(string uid) => uid.StartsWith("m:") ? uid[2..] : null;

    public sealed record Where(bool InPack, int Index, EquipSlot Slot, ItemInstance Item);

    public static Where? Find(CharacterData ch, string uid)
    {
        int i = ch.Pack.FindIndex(p => p?.Uid == uid);
        if (i >= 0) return new Where(true, i, default, ch.Pack[i]!);
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s]?.Uid == uid) return new Where(false, -1, s, ch.Equipment[s]!);
        return null;
    }

    /// <summary>Equip an item into a slot; whatever was there goes to the pack.</summary>
    public static bool Equip(CharacterData ch, ItemInstance it, EquipSlot slot)
    {
        var def = Items.Get(it.Def);
        if (!Items.Fits(def, slot)) return false;
        var loc = Find(ch, it.Uid);
        if (loc is { InPack: true }) ch.Pack[loc.Index] = null;
        if (loc is { InPack: false }) ch.Equipment[loc.Slot] = null;
        var prev = ch.Equipment[slot];
        ch.Equipment[slot] = it;
        if (prev != null)
        {
            if (loc is { InPack: true }) ch.Pack[loc.Index] = prev;
            else if (!AddToPack(ch, prev)) { ch.Equipment[slot] = prev; return false; }
        }
        return true;
    }

    public static bool Unequip(CharacterData ch, EquipSlot slot)
    {
        var it = ch.Equipment[slot];
        if (it == null || !AddToPack(ch, it)) return false;
        ch.Equipment[slot] = null;
        return true;
    }

    /// <summary>Everything the survivor has on them that the world can see.</summary>
    public static HashSet<string> WorldTags(CharacterData ch)
    {
        var tags = new HashSet<string>();
        foreach (var s in Items.EquipSlots)
        {
            if (ch.Equipment[s] is { } it && Items.Find(it.Def)?.Tags is { } t) tags.UnionWith(t);
            // What was worked into it shows too (a pelt worked into a coat: the wolves smell it).
            if (ch.Equipment[s]?.Marks is { } m) tags.UnionWith(m);
        }
        foreach (var p in ch.Pack)
            if (p != null && Items.Find(p.Def) is { Kind: ItemKind.Tool, Tags: { } t }) tags.UnionWith(t);
        foreach (var tr in ch.Traits) if (Callings.Trait(tr)?.Tags is { } t) tags.UnionWith(t);
        foreach (var k in ch.Knowledge) tags.Add($"knows:{k}");
        tags.Add($"bg:{ch.Background}");
        tags.Add($"class:{ch.Archetype}");
        return tags;
    }
}

/// <summary>The survivor as a fight needs them.</summary>
public sealed class CombatKit
{
    public StatBlock Stats = new();
    public List<(string Id, int Rank)> Weapons = new();
    /// <summary>Learned skills carried by day (not into the night's arenas: the ember starts from nothing).</summary>
    public List<(string Id, int Rank)> Learned = new();
    public List<(TriggerDef Def, string Source)> Triggers = new();
    public AbilityKind Ability;
    public int ArtRank = 1;
    public List<string> Facets = new();
    /// <summary>The Marks the gear carries (docs/items/CATALOGUE.md §4), each at its strength 0-1, and
    /// numbers on single skills, by skill id: worn in the Wayfinder's maps (Battle.Wear). Crafting
    /// fills them from the items.</summary>
    public Dictionary<string, double> Marks = new();
    public Dictionary<string, WeaponMods> SkillMods = new();
    public HashSet<string> GearIds = new();
    public HashSet<StatusKind> GearStatuses = new();
    public int StartLevels, Revives, Rerolls = 3;
    /// <summary>What the kindled gear gives the ember (Items: AffixDef.Kindled):
    /// banishings beyond the two, a fourth card, a fourth great choice, and the
    /// passives it stands in for in a recipe.</summary>
    public int Banishes;
    public bool Roads, Omens;
    public HashSet<string> Stands = new();
    /// <summary>The kindled affixes in force (the first two worn; a third does nothing).</summary>
    public List<string> Kindled = new();
}

public static class Character
{
    public static CharacterData Create(CreationChoice c, int day = 1, long? seed = null)
    {
        var a = Callings.Archetype(c.Archetype);
        var bg = Callings.Background(c.Background);
        long s = seed ?? DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        var ch = new CharacterData
        {
            Id = $"hero-{ToBase36(s)}", Name = string.IsNullOrWhiteSpace(c.Name) ? "Nameless" : c.Name.Trim(),
            Archetype = c.Archetype, Background = c.Background, Model = c.Model ?? a.Model, Palette = c.Palette,
            Headgear = c.Headgear ?? true, Cloak = c.Cloak, Skin = c.Skin, Hair = c.Hair, Sex = c.Sex, HairStyle = c.HairStyle,
            Beard = c.Beard, BeardStyle = c.BeardStyle, Figure = c.Figure, Attributes = Callings.StartAttributes(c.Archetype),
            // (only the sliders moved from her own face are kept)
            Face = c.Face?.Where(f => Math.Abs(f.Value) > 1e-3).ToDictionary(f => f.Key, f => Math.Round(Math.Clamp(f.Value, -1, 1), 3)) is { Count: > 0 } face ? face : null,
            Eyes = c.Eyes, Paint = c.Paint == "none" ? null : c.Paint, FaceShape = c.FaceShape is "own" or "" ? null : c.FaceShape,
            Knowledge = new(bg.Knowledge), Gold = 25, Ability = c.Ability, CreatedDay = day,
        };
        ch.Known = ArtBook.Starting(c.Archetype);
        if (c.Ability != "" && !ch.Known.Contains(c.Ability)) ch.Known.Add(c.Ability);
        Inventory.Equip(ch, Inventory.Make(ch, c.WeaponItem), EquipSlot.Weapon);
        foreach (var id in bg.Items)
        {
            var it = Inventory.Make(ch, id);
            var slot = Items.SlotFor(Items.Get(id));
            if (slot is { } sl && ch.Equipment[sl] == null) Inventory.Equip(ch, it, sl);
            else Inventory.AddToPack(ch, it);
        }
        Inventory.AddToPack(ch, Inventory.Make(ch, "health_draught", qty: 2));
        return ch;
    }

    static string ToBase36(long v)
    {
        const string digits = "0123456789abcdefghijklmnopqrstuvwxyz";
        if (v == 0) return "0";
        var sb = new System.Text.StringBuilder();
        for (ulong u = (ulong)Math.Abs(v); u > 0; u /= 36) sb.Insert(0, digits[(int)(u % 36)]);
        return sb.ToString();
    }

    public static double XpForLevel(int level) => MathX.Round(120 * Math.Pow(level, 1.55));

    /// <summary>Character experience from the fight; the levels gained.</summary>
    /// <summary>The survivor's last level (docs/SKILLS_DESIGN.md, "Decisions"): reached near
    /// the end of Act 3; past it the open axes are gear and the arena's depth, and the
    /// night's power stays the ember's.</summary>
    public const int MaxLevel = 30;

    public static int GainXp(CharacterData ch, double xp)
    {
        if (ch.Level >= MaxLevel) { ch.Xp = 0; return 0; }
        ch.Xp += xp;
        int gained = 0;
        while (ch.Level < MaxLevel && ch.Xp >= XpForLevel(ch.Level))
        {
            ch.Xp -= XpForLevel(ch.Level);
            ch.Level++;
            ch.Points += 2;
            if (ch.Level % 2 == 0) ch.TraitPicks++;
            gained++;
        }
        if (ch.Level >= MaxLevel) ch.Xp = 0;
        return gained;
    }

    /// <summary>The survivor as the Battle needs them: stats with every source folded in.</summary>
    public static CombatKit Kit(CharacterData ch)
    {
        var a = Callings.Archetype(ch.Archetype);
        var kit = new CombatKit { Ability = ch.AbilityKind, ArtRank = ArtBook.Rank(ch, ch.Ability), Facets = ArtBook.Facets(ch, ch.Ability) };
        var st = kit.Stats;
        var at = ch.Attributes;
        st.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = a.Base.MaxHealth + (ch.Level - 1) * 8, [Stat.Regen] = a.Base.Regen, [Stat.Armor] = a.Base.Armor,
            [Stat.MoveSpeed] = a.Base.MoveSpeed, [Stat.PickupRadius] = a.Base.PickupRadius, [Stat.CritChance] = a.Base.CritChance,
            [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        const string src = "attributes";
        st.AddAll([
            new(Stat.Damage, ModKind.Inc, at.Might * 0.025, src),
            new(Stat.MaxHealth, ModKind.Flat, at.Might * 4 + at.Resolve * 3, src),
            new(Stat.CritChance, ModKind.Flat, at.Finesse * 0.006, src),
            new(Stat.MoveSpeed, ModKind.Inc, at.Finesse * 0.01, src),
            new(Stat.ProjectileSpeed, ModKind.Inc, at.Finesse * 0.02, src),
            new(Stat.Cooldown, ModKind.More, -Math.Min(0.3, at.Wits * 0.01), src),
            new(Stat.Area, ModKind.Inc, at.Wits * 0.02, src),
            new(Stat.XpGain, ModKind.Inc, at.Wits * 0.02, src),
            new(Stat.Armor, ModKind.Flat, at.Resolve * 0.5, src),
            new(Stat.Regen, ModKind.Flat, at.Resolve * 0.08, src),
            new(Stat.Healing, ModKind.Inc, at.Resolve * 0.03, src),
        ]);
        foreach (var s in Items.EquipSlots)
        {
            var it = ch.Equipment[s];
            if (it == null) continue;
            var def = Items.Get(it.Def);
            kit.GearIds.Add(def.Id);
            st.AddAll(Inventory.Mods(it));
            foreach (var t in def.Triggers ?? new()) kit.Triggers.Add((t, $"item:{it.Uid}"));
            foreach (var k in def.Statuses ?? new()) kit.GearStatuses.Add(k);
            // Kindling: one to an item, two to the survivor.
            if (it.Affixes.Select(ar => Items.Affix(ar.Id)).FirstOrDefault(a => a?.Kindled != null) is { } kin && kit.Kindled.Count < Inventory.MaxKindled)
            {
                kit.Kindled.Add(kin.Id);
                Kindle(kit, kin.Kindled!);
            }
            // Skills the gear grants, while there is room for them.
            foreach (var ar in it.Affixes)
                if (Items.Affix(ar.Id)?.Grants is { } g && kit.Weapons.All(w => w.Id != g) && kit.Weapons.Count < Content.Weapons.MaxWeapons)
                    kit.Weapons.Add((g, 1 + ar.Tier / 2));
            if (def.Weapon != null && s is EquipSlot.Weapon or EquipSlot.Offhand)
            {
                // Mastery: every 60 kills with a weapon starts it a rank higher, to +2.
                int bonus = Math.Min(2, ch.Mastery.GetValueOrDefault(def.Weapon.Id) / 60);
                kit.Weapons.Add((def.Weapon.Id, Math.Min(Inventory.GearRankCap, def.Weapon.Rank + bonus + Math.Max(0, it.Rarity - def.Rarity))));
            }
        }
        foreach (var (id, rank) in SkillBook.Carried(ch))
            if (kit.Weapons.All(w => w.Id != id)) kit.Learned.Add((id, rank));
        foreach (var t in ch.Traits)
        {
            var td = Callings.Trait(t);
            if (td == null) continue;
            if (td.Mods != null) st.AddAll(td.Mods.Select(m => m with { Source = $"trait:{t}" }));
            foreach (var tr in td.Triggers ?? new()) kit.Triggers.Add((tr, $"trait:{t}"));
            if (td.Tags?.Contains("ember_start") == true) kit.StartLevels++;
            if (td.Tags?.Contains("revive") == true) kit.Revives++;
            if (td.Tags?.Contains("reroll") == true) kit.Rerolls++;
        }
        foreach (var c in ch.Conditions)
        {
            switch (c.Id)
            {
                case ConditionId.Wounded: st.Add(new(Stat.MaxHealth, ModKind.More, -0.2, "cond:wounded")); break;
                case ConditionId.Blightsick: st.Add(new(Stat.Regen, ModKind.Flat, -0.8, "cond:blightsick")); break;
                case ConditionId.Blessed: st.Add(new(Stat.DamageOf(School.Holy), ModKind.Inc, 0.15, "cond:blessed")); break;
                case ConditionId.Rested: st.Add(new(Stat.MaxHealth, ModKind.Inc, 0.05, "cond:rested")); break;
                case ConditionId.Warmed:
                    st.Add(new(Stat.Damage, ModKind.Inc, 0.08, "cond:warmed"));
                    st.Add(new(Stat.MoveSpeed, ModKind.Inc, 0.05, "cond:warmed"));
                    break;
            }
        }
        return kit;
    }

    static void Kindle(CombatKit kit, string key)
    {
        switch (key)
        {
            case "spark": kit.StartLevels++; break;
            case "reroll": kit.Rerolls++; break;
            case "refusal": kit.Banishes++; break;
            case "roads": kit.Roads = true; break;
            case "omens": kit.Omens = true; break;
            default: if (key.StartsWith("stand:")) kit.Stands.Add(key[6..]); break;
        }
    }

    static readonly string[] CompareKeys =
    [
        Stat.MaxHealth, Stat.Armor, Stat.Damage, Stat.Cooldown, Stat.Area, Stat.CritChance, Stat.MoveSpeed, Stat.Regen,
        Stat.DamageOf(School.Fire), Stat.DamageOf(School.Frost), Stat.DamageOf(School.Holy), Stat.DamageOf(School.Physical),
        Stat.ResistOf(School.Fire), Stat.ResistOf(School.Nature),
    ];

    /// <summary>Stat differences if `it` replaced what is in `slot`, for the compare view.</summary>
    public static List<(string Key, double Before, double After)> Compare(CharacterData ch, ItemInstance it, EquipSlot slot)
    {
        var before = Kit(ch).Stats;
        var clone = Json.Clone(ch);
        clone.Equipment[slot] = Json.Clone(it);
        var after = Kit(clone).Stats;
        var o = new List<(string, double, double)>();
        foreach (var k in CompareKeys)
        {
            bool raw = k.StartsWith("resist");
            double b = raw ? before.GetRaw(k) : before.Get(k), a = raw ? after.GetRaw(k) : after.Get(k);
            if (Math.Abs(a - b) > 1e-4) o.Add((k, b, a));
        }
        return o;
    }
}
