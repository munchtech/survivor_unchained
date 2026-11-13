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
    /// <summary>Dye zones of the pieces it wears (outfit_materials.json "zone": metal, trim, leather, cloth, or thread) -> "#rrggbb" (sRGB), optionally with ":metal" or ":paint" (Wear.DyeFinish; metal-zone dyes: light neutrals stay metal, colours paint the enamel, gold needs ":metal"). Null: as made.</summary>
    public Dictionary<string, string>? Dye;
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
    /// <summary>The level it was made at, where that was a Wayfinder's map (docs/CRAFTING_DESIGN.md 20.3):
    /// the harder the map, the more often its grades rolled the finer of its rarity's two. Null by day.</summary>
    public int? Level;
}

public enum ConditionId { Wounded, Blightsick, Poisoned, Blessed, Rested, Wolfscent, Hunted, Warmed }

public sealed class Condition { public ConditionId Id; public int Days; public string? Note; }

public sealed class Attributes { public int Might, Finesse, Wits, Resolve; }

public enum Sex { Male, Female }

/// <summary>What is worn and held, slot by slot: the eight places (Items.EquipSlots).</summary>
public sealed class Equipment
{
    public ItemInstance? Weapon, Offhand, Head, Body, Feet, Amulet, Ring1, Ring2;

    /// <summary>What an old save wrote in a place the 13 November cut removed (cloak, relic, shoulders, bracers, hands, belt, legs),
    /// kept as read until the migration (Inventory.Mend) puts it in the pack or the stash; null after.</summary>
    [System.Text.Json.Serialization.JsonExtensionData]
    public Dictionary<string, System.Text.Json.JsonElement>? Retired { get; set; }

    public ItemInstance? this[EquipSlot s]
    {
        get => s switch
        {
            EquipSlot.Weapon => Weapon, EquipSlot.Offhand => Offhand, EquipSlot.Head => Head, EquipSlot.Body => Body,
            EquipSlot.Feet => Feet, EquipSlot.Amulet => Amulet, EquipSlot.Ring1 => Ring1, _ => Ring2,
        };
        set
        {
            switch (s)
            {
                case EquipSlot.Weapon: Weapon = value; break;
                case EquipSlot.Offhand: Offhand = value; break;
                case EquipSlot.Head: Head = value; break;
                case EquipSlot.Body: Body = value; break;
                case EquipSlot.Feet: Feet = value; break;
                case EquipSlot.Amulet: Amulet = value; break;
                case EquipSlot.Ring1: Ring1 = value; break;
                default: Ring2 = value; break;
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
    /// <summary>Her hair's highlights, a second colour on some of her locks (World.Lore.HighlightColor): null off,
    /// "auto" her hair colour's own, or a highlight's id.</summary>
    public string? HairHighlight;
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
    /// <summary>The two kits (Rpg/Kits.cs): the night kit's own slots, the kit not on now's pieces in
    /// them, and whether the night's is on. Equipment is always what is on now.</summary>
    [System.Text.Json.Serialization.JsonConverter(typeof(EquipSlotListConverter))]
    public List<EquipSlot>? NightOwn;
    public Equipment? OtherKit;
    public bool NightOn;
    public List<ItemInstance?> Pack = Inventory.NewPack();
    /// <summary>The materials pouch: crafting's materials and trophies by id, never in the pack's places.</summary>
    public Dictionary<string, int> Materials = new();
    /// <summary>The slotless stores (docs/design/LOOT_DESIGN.md §6): books, charts and the rulers'
    /// marked things in the satchel; quest things and tools on the key ring; draughts on the belt.</summary>
    public List<ItemInstance> Satchel = new(), Keys = new();
    public Dictionary<string, int> Belt = new();
    /// <summary>The survivor's item filter (docs/design/LOOT_DESIGN.md §7), and the bases seen at
    /// each make ("iron_helm@Wrought"): a first sighting always shows.</summary>
    public LootFilter Filter = new();
    public HashSet<string> Seen = new();
    public double Gold;
    /// <summary>The art in hand (the web game's id, 'shield_bash').</summary>
    public string Ability = "";
    /// <summary>Skills found in the arenas (taken as cards there): only these
    /// can be learned for the world.</summary>
    public List<string> Discovered = new();
    /// <summary>Combat skills learned for the day (Rpg/SkillBook.cs), and those carried.</summary>
    public List<string> Skills = new(), Slotted = new();
    /// <summary>(M3) The taught build's levels granted so far (Content/TaughtBuilds.Grant): a slot the player took off
    /// is not put back.</summary>
    public int TaughtUpTo;
    /// <summary>(bd-keys) Skills offered both ways (pressed or kindled) that she runs in an auto slot (Rpg/SkillBook.IsAuto);
    /// every other skill's place is its own record's.</summary>
    public List<string> AutoForm = new();
    /// <summary>(bd-keys) Her second weapon set's stance (data/content/stances.json), or "" for her calling's taught one; it
    /// opens at the ladder's level (SkillBook.StanceOf).</summary>
    public string Stance = "";
    /// <summary>(bd-keys) The bar this save was carried under: 0 the six keys, 2 four keys and three auto slots (an older
    /// save's taught build is granted again into the new bar: Content/TaughtBuilds.Grant).</summary>
    public int Bar;
    /// <summary>Every art the survivor knows (Rpg/ArtBook.cs).</summary>
    public List<string> Known = new();
    /// <summary>How far each art has come, and its facets.</summary>
    public Dictionary<string, ArtState> Arts = new();
    /// <summary>The dash's steps taken (Content/DashSteps.cs), in the order taken; a repeatable one once a time.</summary>
    public List<string> DashSteps = new();
    /// <summary>The Unions she has learned (Rpg/UnionJoin.cs: paid for once); which are joined is the lamp layout's.</summary>
    public List<string> UnionsKnown = new();
    /// <summary>(bd-sockets) Her support gems: copies owned and what sits in each skill's sockets (Rpg/Supports.cs).</summary>
    public SupportState Gems = new();

    /// <summary>Take a step of the dash's growth (the design lead's route calls this, a Wick or a level-up; or
    /// Journey.GrantDashStep, which also tells the fight). False if unknown or already taken as often as it may be.</summary>
    public bool GrantDashStep(string id)
    {
        if (!Content.DashSteps.CanTake(DashSteps, id)) return false;
        DashSteps.Add(id);
        return true;
    }
    /// <summary>The Lamps lit, in three layouts (Rpg/LampBook.cs); null in a save from before them.</summary>
    public LampState? Lamps;
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
    /// <summary>The road, named at creation: only the harness, tests and dev runs name one (a survivor walks it from the
    /// start). Empty, as the creation screen leaves it: she walks no road until she chooses one at level 6
    /// (LampBook.RoadLevel, BUILD_UNLOCKS). A foreign road is as empty.</summary>
    public string Type = "";
    public string? Model, Cloak, Skin, Hair, HairStyle, Eyes, Paint, FaceShape, BeardStyle, HairHighlight;
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
        IReadOnlyCollection<string>? lean = null, bool dropped = false, int? level = null)
    {
        var def = Items.Get(defId);
        string uid = ch != null ? $"i{ch.NextUid++}" : $"i{loose.Next(1_000_000_000):x}";
        // Gear carries the level it was made at (docs/design/LOOT_DESIGN.md §4.1): given, or the survivor's.
        var it = new ItemInstance { Uid = uid, Def = defId, Qty = qty, Rarity = rarity ?? def.Rarity, Affixes = affixes ?? new(), Level = Drops.Leveled(def) ? level ?? ch?.Level : null };
        if (Crafting.Workable(def)) it.Heat = it.HeatFull = Crafting.HeatAtMaking(it.Rarity, dropped ? new Rng(seed ?? (uint)loose.Next(1_000_000_000)) : null);
        // A ruler's thing carries its Mark at the grade it fell at (its rarity, I to VI).
        if (affixes == null && Crafting.MarkOf(defId) is { } mark) it.Affixes.Add(new AffixRoll { Id = mark, Tier = Math.Clamp(it.Rarity, 0, 5) });
        if (def.Base && affixes == null)
        {
            var rng = new Rng(seed ?? (uint)loose.Next(1_000_000_000));
            int n = Math.Min(3, it.Rarity);
            // A skill worn that the survivor's calling may not carry rolls something else.
            var pool = Items.Affixes.Where(a => a.Slots.Contains(def.Kind) && it.Rarity >= a.MinRarity && !a.Unique
                && (a.Grants == null || ch == null || Content.Weapons.CanCarry(ch.Archetype, a.Grants))
                && (a.Plus == null || ch == null || Content.Weapons.CanCarry(ch.Archetype, a.Plus))).ToList();
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
                double W(AffixDef x) => (lean?.Contains(x.Id) == true ? 4 : 1) * (x.Grants != null || x.Plus != null ? 0.35 : 1) *
                    (x.Kindled == null ? 1 : 0.3 * (wanted.Contains(x.Kindled) ? 2 : 1));
                double total = cands.Sum(W), roll = rng.Next() * total;
                var a = cands[^1];
                foreach (var c in cands) { roll -= W(c); if (roll <= 0) { a = c; break; } }
                picked.Add(a.Id);
                if (a.Prefix) hasPrefix = true; else hasSuffix = true;
                // A rarity rolls one of two grades; the deeper it was made, the finer comes oftener (a coin to
                // level 10, read the same way as the coin was), and from level 25 the grades rise (Drops.GradeShift).
                int finer = it.Level is int lv ? (rng.Next() >= 1 - Crafting.FinerGrade(lv) ? 1 : 0) : rng.Int(0, 1);
                it.Affixes.Add(new AffixRoll { Id = a.Id, Tier = Math.Min(5, Math.Max(0, Math.Min(3, it.Rarity - 1 + finer)) + Drops.GradeShift(it.Level)) });
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
        // A base's own numbers (or the base a named piece is built on) at its make; a named piece's own after.
        var o = Drops.Implicit(def, it.Level).Select(m => m with { Source = src }).ToList();
        if (!def.Base) o.AddRange((def.Mods ?? new()).Select(m => m with { Source = src }));
        foreach (var a in it.Affixes)
            if (Items.Affix(a.Id) is { } ad) o.AddRange(ad.Mods(a.Tier).Select(m => m with { Source = src }));
        if (it.Setting != null && Items.Affix(it.Setting) is { } set) o.AddRange(set.Mods(0).Select(m => m with { Source = src }));
        return o;
    }

    public static List<string> Lines(ItemInstance it) =>
        (it.Setting != null && Items.Affix(it.Setting) is { } set ? new[] { set.Text(0) } : Array.Empty<string>())
            .Concat(it.Affixes.Select(a => Items.Affix(a.Id)?.Text(a.Tier) ?? "")).ToList();

    /// <summary>The rank a weapon brings its skill in at: its own, a rank a rarity above its making, to
    /// the gear's cap (mastery is added in the kit).</summary>
    public static int WeaponRank(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        return def.Weapon == null ? 0 : Math.Min(GearRankCap, def.Weapon.Rank + Math.Max(0, it.Rarity - def.Rarity));
    }

    /// <summary>Carry a thing: gear into the pack's places, everything else into its store, which
    /// never fills (docs/design/LOOT_DESIGN.md §6). False if there was no room (the pack's places,
    /// or a draught kind's carry limit on the belt); a stack only partly taken keeps the rest.</summary>
    public static bool AddToPack(CharacterData ch, ItemInstance it)
    {
        var def = Items.Get(it.Def);
        switch (Drops.StoreOf(def, it))
        {
            case Store.Pouch:
                ch.Materials[it.Def] = ch.Materials.GetValueOrDefault(it.Def) + Math.Max(0, it.Qty);
                return true;
            case Store.Belt:
            {
                int have = ch.Belt.GetValueOrDefault(it.Def), take = Math.Min(Math.Max(0, it.Qty), Math.Max(0, Drops.Rules.Belt - have));
                if (take > 0) ch.Belt[it.Def] = have + take;
                it.Qty -= take;
                return it.Qty <= 0;
            }
            case Store.Satchel: Shelve(ch.Satchel, it, def); return true;
            case Store.Keys: Shelve(ch.Keys, it, def); return true;
            case Store.Gems:
            {
                var gid = Supports.OfItem(it.Def)!.Id;
                ch.Gems.Owned[gid] = ch.Gems.Owned.GetValueOrDefault(gid) + Math.Max(1, it.Qty);
                return true;
            }
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

    /// <summary>Where a delivered thing went: her pack, Rook's shelves, or held by Rook's door.</summary>
    public enum Landed { Pack, Shelf, Door }

    /// <summary>(Codex audit SU-087: a reward is never lost) A thing given to her that must reach her: the pack, else a
    /// free place on Rook's shelves, else Rook holds it by the door (World.Held, shelved as room is made). Always lands.</summary>
    public static Landed Deliver(CharacterData ch, World.WorldState w, ItemInstance it)
    {
        if (AddToPack(ch, it)) return Landed.Pack;
        int j = w.Stash.IndexOf(null);
        if (j >= 0) { w.Stash[j] = it; return Landed.Shelf; }
        w.Held.Add(it);
        return Landed.Door;
    }

    /// <summary>The line that says truthfully where a delivered thing went when it missed the pack.</summary>
    public static string WhereSaid(Landed l, string name) => l switch
    {
        Landed.Shelf => $"{name} was sent to Rook's storeroom - your pack is full.",
        Landed.Door => $"{name}: your pack and Rook's shelves are full. Rook is holding it by the door until you make room.",
        _ => name,
    };

    /// <summary>Into a list store: onto a stack of its kind while there is room in it (a chart or a
    /// marked thing is always its own entry), else its own entry.</summary>
    static void Shelve(List<ItemInstance> store, ItemInstance it, ItemDef def)
    {
        if (def.Stack is { } stack && stack > 1 && it.Chart == null && it.Affixes.Count == 0)
            foreach (var p in store)
            {
                if (p.Def != it.Def || p.Qty >= stack || p.Chart != null || p.Affixes.Count > 0) continue;
                int take = Math.Min(stack - p.Qty, it.Qty);
                p.Qty += take;
                it.Qty -= take;
                if (it.Qty <= 0) return;
            }
        if (it.Qty > 0) store.Add(it);
    }

    public static int Free(CharacterData ch) => ch.Pack.Count(p => p == null);

    /// <summary>How many more of a thing could be carried (the slotless stores: any number, but the belt's limit).</summary>
    public static int Room(CharacterData ch, string defId)
    {
        var def = Items.Get(defId);
        switch (Drops.StoreOf(def, null))
        {
            case Store.Belt: return Math.Max(0, Drops.Rules.Belt - ch.Belt.GetValueOrDefault(defId));
            case Store.Pouch or Store.Satchel or Store.Keys or Store.Gems: return int.MaxValue;
        }
        int stack = Math.Max(1, def.Stack ?? 1), n = Free(ch) * stack;
        foreach (var p in ch.Pack) if (p != null && p.Def == defId) n += Math.Max(0, stack - p.Qty);
        return n;
    }

    public static int Count(CharacterData ch, string defId)
    {
        int n = ch.Materials.GetValueOrDefault(defId) + ch.Belt.GetValueOrDefault(defId);
        if (Supports.OfItem(defId) is { } gd) n += ch.Gems.Owned.GetValueOrDefault(gd.Id);
        foreach (var p in ch.Pack) if (p?.Def == defId) n += p.Qty;
        foreach (var p in ch.Satchel) if (p.Def == defId) n += p.Qty;
        foreach (var p in ch.Keys) if (p.Def == defId) n += p.Qty;
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s]?.Def == defId) n++;
        return n;
    }

    /// <summary>Take up to qty of a thing from wherever it is carried; how many were taken.</summary>
    public static int Take(CharacterData ch, string defId, int qty = 1)
    {
        int left = qty;
        // The counted stores first: that is where materials and draughts live.
        foreach (var counts in new[] { ch.Materials, ch.Belt })
            if (left > 0 && counts.TryGetValue(defId, out int have) && have > 0)
            {
                int t = Math.Min(left, have);
                left -= t;
                if (have - t > 0) counts[defId] = have - t; else counts.Remove(defId);
            }
        foreach (var store in new[] { ch.Satchel, ch.Keys })
            for (int i = 0; i < store.Count && left > 0; i++)
            {
                if (store[i].Def != defId) continue;
                int t = Math.Min(left, store[i].Qty);
                store[i].Qty -= t;
                left -= t;
                if (store[i].Qty <= 0) store.RemoveAt(i--);
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
    public static List<ItemInstance> Pouch(CharacterData ch) => Counted(ch.Materials, "m:");

    /// <summary>The belt as things to show, drink and sell: one stack a draught ('b:' and its id).</summary>
    public static List<ItemInstance> Belt(CharacterData ch) => Counted(ch.Belt, "b:");

    static List<ItemInstance> Counted(Dictionary<string, int> counts, string prefix) =>
        counts.Where(kv => kv.Value > 0 && Items.Find(kv.Key) != null)
            .OrderBy(kv => Items.Get(kv.Key).Rarity).ThenBy(kv => Items.Get(kv.Key).Name)
            .Select(kv => new ItemInstance { Uid = prefix + kv.Key, Def = kv.Key, Qty = kv.Value, Rarity = Items.Get(kv.Key).Rarity }).ToList();

    public static string PouchUid(string defId) => $"m:{defId}";
    public static string? FromPouch(string uid) => uid.StartsWith("m:") ? uid[2..] : null;
    public static string? FromBelt(string uid) => uid.StartsWith("b:") ? uid[2..] : null;

    /// <summary>Where a thing is: its store, its place in the pack or list (-1 in a counted store or
    /// worn), the slot it is worn in, and the thing (a counted store's: the whole stack).</summary>
    public sealed record Where(Store Store, int Index, EquipSlot Slot, ItemInstance Item)
    {
        /// <summary>In the pack's places (not worn, not in a store).</summary>
        public bool InPack => Store == Store.Pack;
        public bool Worn => Store == Store.Worn;
        /// <summary>Worn in the kit not on now (Rpg/Kits.cs).</summary>
        public bool Aside => Store == Store.Kit;
        /// <summary>Carried, anywhere but on the body (or set aside in the other kit).</summary>
        public bool Carried => Store is not (Store.Worn or Store.Kit);
    }

    public static Where? Find(CharacterData ch, string uid)
    {
        if (FromPouch(uid) is { } m) return ch.Materials.GetValueOrDefault(m) > 0 ? new Where(Store.Pouch, -1, default, Pouch(ch).First(x => x.Def == m)) : null;
        if (FromBelt(uid) is { } b) return ch.Belt.GetValueOrDefault(b) > 0 ? new Where(Store.Belt, -1, default, Belt(ch).First(x => x.Def == b)) : null;
        int i = ch.Pack.FindIndex(p => p?.Uid == uid);
        if (i >= 0) return new Where(Store.Pack, i, default, ch.Pack[i]!);
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s]?.Uid == uid) return new Where(Store.Worn, -1, s, ch.Equipment[s]!);
        foreach (var (s, it) in Kits.Aside(ch)) if (it.Uid == uid) return new Where(Store.Kit, -1, s, it);
        i = ch.Satchel.FindIndex(p => p.Uid == uid);
        if (i >= 0) return new Where(Store.Satchel, i, default, ch.Satchel[i]);
        i = ch.Keys.FindIndex(p => p.Uid == uid);
        if (i >= 0) return new Where(Store.Keys, i, default, ch.Keys[i]);
        return null;
    }

    /// <summary>Carried, not worn: in the pack or a store.</summary>
    public static bool Holds(CharacterData ch, string uid) => Find(ch, uid) is { Carried: true };

    /// <summary>Take a carried thing out of wherever it is (qty of a stack, all of it if null):
    /// what was taken, or null. Worn things are not taken.</summary>
    public static ItemInstance? Remove(CharacterData ch, string uid, int? qty = null)
    {
        if (Find(ch, uid) is not { Carried: true } loc) return null;
        var it = loc.Item;
        int n = Math.Min(it.Qty, qty ?? it.Qty);
        if (loc.Store is Store.Pouch or Store.Belt)
        {
            var counts = loc.Store == Store.Pouch ? ch.Materials : ch.Belt;
            int left = counts.GetValueOrDefault(it.Def) - n;
            if (left > 0) counts[it.Def] = left; else counts.Remove(it.Def);
            return new ItemInstance { Uid = $"i{ch.NextUid++}", Def = it.Def, Qty = n, Rarity = it.Rarity };
        }
        if (n < it.Qty)
        {
            it.Qty -= n;
            var part = Json.Clone(it);
            part.Uid = $"i{ch.NextUid++}";
            part.Qty = n;
            return part;
        }
        switch (loc.Store)
        {
            case Store.Pack: ch.Pack[loc.Index] = null; break;
            case Store.Satchel: ch.Satchel.RemoveAt(loc.Index); break;
            case Store.Keys: ch.Keys.RemoveAt(loc.Index); break;
        }
        return it;
    }

    /// <summary>Every whole thing carried and worn (the counted stores' stacks too).</summary>
    public static IEnumerable<ItemInstance> Everything(CharacterData ch) =>
        ch.Pack.Where(p => p != null).Select(p => p!).Concat(ch.Satchel).Concat(ch.Keys).Concat(Pouch(ch)).Concat(Belt(ch))
            .Concat(Items.EquipSlots.Select(s => ch.Equipment[s]).Where(x => x != null).Select(x => x!)).Concat(Kits.Aside(ch).Select(a => a.Item));

    /// <summary>Equip an item into a slot; whatever was there goes to the pack.</summary>
    public static bool Equip(CharacterData ch, ItemInstance it, EquipSlot slot)
    {
        var def = Items.Get(it.Def);
        if (!Items.Fits(def, slot)) return false;
        var loc = Find(ch, it.Uid);
        // (a piece in the other kit is moved by the kits, never pulled out from under them)
        if (loc is { Aside: true }) return false;
        if (loc is { InPack: true }) ch.Pack[loc.Index] = null;
        if (loc is { Worn: true }) ch.Equipment[loc.Slot] = null;
        var prev = ch.Equipment[slot];
        ch.Equipment[slot] = it;
        if (prev != null)
        {
            if (loc is { InPack: true }) ch.Pack[loc.Index] = prev;
            else if (!AddToPack(ch, prev)) { ch.Equipment[slot] = prev; return false; }
        }
        return true;
    }

    /// <summary>Migration: a worn item whose kind no longer matches its slot moves to its kind's slot
    /// if that is empty, else to the pack (else stays). Safe to run any number of times.</summary>
    public static void Reslot(CharacterData ch)
    {
        foreach (var s in Items.EquipSlots)
        {
            if (ch.Equipment[s] is not { } it || Items.Find(it.Def) is not { } def || Items.Fits(def, s)) continue;
            if (Items.SlotFor(def) is EquipSlot k && Items.Fits(def, k) && ch.Equipment[k] == null) { ch.Equipment[s] = null; ch.Equipment[k] = it; }
            else if (AddToPack(ch, it)) ch.Equipment[s] = null;
        }
    }

    /// <summary>Migration for the 13 November 2026 cut (15 equipment places to 8): what an old save wore in a place that is gone
    /// (Equipment.Retired, read as it was written) goes to the pack, else the stash, else is let go; a piece whose id the cut removed
    /// becomes what Items.Retired says or is let go, wherever it sits (worn, either kit, pack, satchel, key ring, stash, a shop's
    /// shelf, the ground, a corpse, a nemesis). Safe to run any number of times; never throws on what it cannot read.</summary>
    public static void Mend(CharacterData ch, World.WorldState? w = null)
    {
        var salvage = new List<ItemInstance>();
        foreach (var eq in new[] { ch.Equipment, ch.OtherKit })
        {
            if (eq?.Retired is not { } old) continue;
            foreach (var (slot, el) in old)
            {
                if (!Items.RetiredSlots.Contains(slot, StringComparer.OrdinalIgnoreCase)) continue;
                try { if (el.ValueKind == System.Text.Json.JsonValueKind.Object && System.Text.Json.JsonSerializer.Deserialize<ItemInstance>(el.GetRawText(), Json.Options) is { } it) salvage.Add(it); }
                catch (System.Text.Json.JsonException) { }
            }
            eq.Retired = null;
        }
        // (a retired id: its replacement, or null to let it go)
        ItemInstance? Fix(ItemInstance? it)
        {
            if (it == null || !Items.Retired.TryGetValue(it.Def, out var to)) return it;
            if (to == null) return null;
            it.Def = to;
            return it;
        }
        foreach (var s in Items.EquipSlots)
        {
            ch.Equipment[s] = Fix(ch.Equipment[s]);
            if (ch.OtherKit != null) ch.OtherKit[s] = Fix(ch.OtherKit[s]);
        }
        for (int i = 0; i < ch.Pack.Count; i++) ch.Pack[i] = Fix(ch.Pack[i]);
        ch.Satchel.RemoveAll(it => Fix(it) == null);
        ch.Keys.RemoveAll(it => Fix(it) == null);
        if (w != null)
        {
            for (int i = 0; i < w.Stash.Count; i++) w.Stash[i] = Fix(w.Stash[i]);
            foreach (var shop in w.Shops.Values) shop.Stock.RemoveAll(it => Fix(it) == null);
            w.GroundItems.RemoveAll(g => Fix(g.Item) == null);
            w.Corpse?.Items.RemoveAll(it => Fix(it) == null);
            w.Nemesis?.Carries.RemoveAll(it => Fix(it) == null);
        }
        foreach (var it in salvage.Select(Fix).OfType<ItemInstance>())
        {
            if (Items.Find(it.Def) == null) continue;
            if (w != null) Deliver(ch, w, it);
            else AddToPack(ch, it);
        }
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
        foreach (var p in ch.Pack.Concat(ch.Keys))
            if (p != null && Items.Find(p.Def) is { Kind: ItemKind.Tool, Tags: { } t }) tags.UnionWith(t);
        // A set worn far enough says something too (the Watch's Kit: the Watch takes you for its own).
        foreach (var (_, bonus) in Drops.SetBonuses(ch)) if (bonus.Tags != null) tags.UnionWith(bonus.Tags);
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
    /// <summary>The auto skills her gear grants (ItemDef.Auto), each at its rank: on top of her auto slots, no limit, whatever her
    /// calling may carry (13 Nov build direction; the Battle runs them).</summary>
    public List<(string Id, int Rank)> AutoSkills = new();
    /// <summary>(bd-keys) A campaign fight's skills in the order the battle takes them up (Character.Bar): her keys in key
    /// order, her auto slots, then the auto skills her gear grants (no cap); and those that run themselves (kindled).</summary>
    public List<(string Id, int Rank)> Bar = new();
    public HashSet<string> Autos = new();
    public List<(TriggerDef Def, string Source)> Triggers = new();
    public AbilityKind Ability;
    public int ArtRank = 1;
    public List<string> Facets = new();
    /// <summary>The dash's steps taken (CharacterData.DashSteps), into BattleSetup.DashSteps.</summary>
    public List<string> DashSteps = new();
    /// <summary>What the lit lamps bring (by day or by night), and the reflexes' ranks (ArtBook's).</summary>
    public LampLoadout Lamps = LampLoadout.None;
    public Dictionary<string, int> ReflexRanks = new();
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
    /// <summary>(M9, ARPG.md 9) The ranks her worn gear adds to one skill: +1 for each rolled "+1 to a skill" affix
    /// (AffixDef.Plus) and a named piece's own (ItemDef.Plus). The one seam the ranks read (SkillBook.RankOf);
    /// M7's points fold in here.</summary>
    public static int SkillPlus(CharacterData ch, string skill)
    {
        int n = 0;
        foreach (var s in Items.EquipSlots)
        {
            if (ch.Equipment[s] is not { } it) continue;
            foreach (var a in it.Affixes)
                if (Items.Affix(a.Id)?.Plus == skill) n++;
            if (Items.Find(it.Def)?.Plus is { } own && own.TryGetValue(skill, out var k)) n += k;
        }
        return n;
    }

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
            HairHighlight = string.IsNullOrEmpty(c.HairHighlight) || c.HairHighlight == "off" ? null : c.HairHighlight,
            Beard = c.Beard, BeardStyle = c.BeardStyle, Figure = c.Figure, Attributes = Callings.StartAttributes(c.Archetype),
            // (only the sliders moved from her own face are kept)
            Face = c.Face?.Where(f => Math.Abs(f.Value) > 1e-3).ToDictionary(f => f.Key, f => Math.Round(Math.Clamp(f.Value, -1, 1), 3)) is { Count: > 0 } face ? face : null,
            Eyes = c.Eyes, Paint = c.Paint == "none" ? null : c.Paint, FaceShape = c.FaceShape is "own" or "" ? null : c.FaceShape,
            Knowledge = new(bg.Knowledge), Gold = 25, Ability = c.Ability, CreatedDay = day,
        };
        ch.Known = ArtBook.Starting(c.Archetype);
        if (c.Ability != "" && !ch.Known.Contains(c.Ability)) ch.Known.Add(c.Ability);
        ArtBook.HoldKin(ch);
        // (her road: none until level 6, BUILD_UNLOCKS; a road named here is the harness's or a test's, walked from the start)
        if (Content.Lamps.Roads.GetValueOrDefault(c.Type)?.Calling == c.Archetype) LampBook.Begin(ch, c.Type);
        else LampBook.BeginRoadless(ch);
        Inventory.Equip(ch, Inventory.Make(ch, c.WeaponItem), EquipSlot.Weapon);
        LearnFirstCalling(ch, a, c.WeaponItem);
        foreach (var id in bg.Items)
        {
            var it = Inventory.Make(ch, id);
            var slot = Items.SlotFor(Items.Get(id));
            if (slot is { } sl && ch.Equipment[sl] == null) Inventory.Equip(ch, it, sl);
            else Inventory.AddToPack(ch, it);
        }
        Inventory.AddToPack(ch, Inventory.Make(ch, "health_draught", qty: 2));
        LampBook.CarryOnAll(ch);
        return ch;
    }

    static string? SkillOfItem(string? item) => item != null && Items.All.ContainsKey(item) ? Items.Get(item).Weapon?.Id : null;

    /// <summary>The type's first calling skill the calling can carry that is not the grip's own skill
    /// (what creation teaches; the creation screen names it). Null when the road has none.</summary>
    public static string? FirstCallingSkill(string archetype, string type, string? gripItem)
    {
        string? grip = SkillOfItem(gripItem);
        // (no road yet, bd-ranks: creation still teaches the calling's first road's first skill, the one every Warden starts with)
        var road = Content.Lamps.Roads.GetValueOrDefault(type) is { } r && r.Calling == archetype ? r : Content.Lamps.RoadsOf(archetype).FirstOrDefault();
        return (road?.Skills ?? []).FirstOrDefault(id => id != grip && Content.Weapons.All.ContainsKey(id) && Weapons.CanCarry(archetype, id));
    }

    /// <summary>The second day skill at level 1 (CLASS_IDENTITY_AND_TALENTS.md §3.7): her type's first
    /// calling skill that she can carry and does not already hold as her grip; else her archetype's
    /// other starting weapon's skill. Creation only: old saves are untouched.</summary>
    static void LearnFirstCalling(CharacterData ch, Archetype a, string? gripItem)
    {
        string? grip = SkillOfItem(gripItem);
        var pick = FirstCallingSkill(ch.Archetype, ch.Lamps?.Now.Type ?? "", gripItem);
        pick ??= a.Weapons.Select(SkillOfItem).FirstOrDefault(id => id != null && id != grip && Content.Weapons.All.ContainsKey(id) && SkillBook.Carries(ch, id));
        if (pick == null) return;
        if (!ch.Discovered.Contains(pick)) ch.Discovered.Add(pick);
        if (!SkillBook.Learn(ch, pick) && !SkillBook.Knows(ch, pick))
        {
            ch.Skills.Add(pick);
            SkillBook.TakeUp(ch, pick);
        }
    }

    static string ToBase36(long v)
    {
        const string digits = "0123456789abcdefghijklmnopqrstuvwxyz";
        if (v == 0) return "0";
        var sb = new System.Text.StringBuilder();
        for (ulong u = (ulong)Math.Abs(v); u > 0; u /= 36) sb.Insert(0, digits[(int)(u % 36)]);
        return sb.ToString();
    }

    /// <summary>The experience a level asks before the next (BUILD_DIRECTION "Progression": PoE-style to the cap, each level
    /// slower than the last). Levels 1 to 12 cost what they always did (120 L^1.55), so Act 1 still ends near level 12
    /// (BUILD_UNLOCKS: Act 1 is levels 1-12); from level 12 on each level also asks 4% more than the curve (Stretch), so
    /// the XP that used to make level 20 makes 19 and the old cap's (30) makes 26, and 75 is the endgame's long climb.</summary>
    public static double XpForLevel(int level) =>
        MathX.Round(120 * Math.Pow(level, 1.55) * (level > StretchFrom ? Math.Exp(Stretch * (level - StretchFrom)) : 1));

    /// <summary>The last level whose cost is the old curve's (reaching level 12 costs exactly what it did).</summary>
    public const int StretchFrom = 11;
    /// <summary>Past StretchFrom, each level's cost grows by e^Stretch (about 4%) on top of the curve.</summary>
    public const double Stretch = 0.04;

    /// <summary>The survivor's last level (BUILD_DIRECTION "Progression", 13 Nov 2026; it was 30): PoE-style, the board gives
    /// a lamp a level all the way (LampBook.Earned), and the levels past the campaign are the endgame's.</summary>
    public const int MaxLevel = 75;

    /// <summary>Traits come every second level up to here (fifteen picks, as at the old cap of 30): there are sixteen
    /// traits, so past it a level's power is its lamp and its attribute points.</summary>
    public const int LastTraitLevel = 30;

    /// <summary>Character experience from the fight; the levels gained.</summary>

    public static int GainXp(CharacterData ch, double xp)
    {
        if (ch.Level >= MaxLevel) { ch.Xp = 0; return 0; }
        ch.Xp += xp;
        int gained = 0, from = ch.Level;
        var had = SkillBook.Carried(ch).Select(c => c.Id).ToHashSet();
        while (ch.Level < MaxLevel && ch.Xp >= XpForLevel(ch.Level))
        {
            ch.Xp -= XpForLevel(ch.Level);
            ch.Level++;
            ch.Points += 2;
            if (ch.Level % 2 == 0 && ch.Level <= LastTraitLevel) ch.TraitPicks++;
            gained++;
        }
        if (ch.Level >= MaxLevel) ch.Xp = 0;
        // M7a: the points the levels earned wait on her carried skills until she lights them (WickBook.Grew).
        if (gained > 0) WickBook.Grew(ch, from, ch.Level, had);
        return gained;
    }

    /// <summary>Her calling's own health at her level: what she is before her attributes, her gear and
    /// whatever a night drafts her. A story boss's blows are measured against it (StoryBoss.Teeth).</summary>
    public static double OwnHealth(CharacterData ch) => Callings.Archetype(ch.Archetype).Base.MaxHealth + (ch.Level - 1) * 8;

    /// <summary>The survivor as the Battle needs them: stats with every source folded in.</summary>
    /// <param name="night">The lamps by night (the table's arenas, story fights): sizes at a quarter (CLASSES.md §2.10).</param>
    public static CombatKit Kit(CharacterData ch, bool night = false)
    {
        var a = Callings.Archetype(ch.Archetype);
        var lamps = LampBook.Loadout(ch, night);
        // The art in hand is the dash form. A way of moving takes its facets from the lamps and the dash's
        // steps alone (the steps ride BattleSetup.DashSteps); any other art keeps the facets its ranks opened (ArtBook).
        var kit = new CombatKit
        {
            Ability = ch.AbilityKind, ArtRank = ArtBook.Rank(ch, ch.Ability), Lamps = lamps,
            Facets = ch.Ability == lamps.Kin || ArtBook.Movement(ch.Ability) ? new() : ArtBook.Facets(ch, ch.Ability),
            DashSteps = ch.DashSteps.ToList(),
        };
        foreach (var r in lamps.Reflexes) kit.ReflexRanks[r.Art] = ArtBook.Rank(ch, r.Art);
        var st = kit.Stats;
        // The attribute lamps add their points by day and in maps (by night they only lean the draft).
        var at = new Attributes
        {
            Might = ch.Attributes.Might + lamps.Attributes.GetValueOrDefault("might"),
            Finesse = ch.Attributes.Finesse + lamps.Attributes.GetValueOrDefault("finesse"),
            Wits = ch.Attributes.Wits + lamps.Attributes.GetValueOrDefault("wits"),
            Resolve = ch.Attributes.Resolve + lamps.Attributes.GetValueOrDefault("resolve"),
        };
        st.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = OwnHealth(ch), [Stat.Regen] = a.Base.Regen, [Stat.Armor] = a.Base.Armor,
            [Stat.MoveSpeed] = a.Base.MoveSpeed, [Stat.PickupRadius] = a.Base.PickupRadius, [Stat.CritChance] = a.Base.CritChance,
            [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        const string src = "attributes";
        st.AddAll([
            new(Stat.Damage, ModKind.Inc, at.Might * 0.025, src),
            new(Stat.MaxHealth, ModKind.Flat, at.Might * 4 + at.Resolve * 3, src),
            // Finesse is for what is thrown or shot (its weapons' own attribute, SkillBook): its damage in a bucket
            // of its own. Through crit alone a point was worth about 0.3% against Might's 2.5%, and a stalker who
            // put every point in it hit little harder for them.
            new(Stat.DamageOf(Tag.Projectile), ModKind.Inc, at.Finesse * 0.02, src),
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
            foreach (var t in Drops.Triggers(def, it.Level)) kit.Triggers.Add((t, $"item:{it.Uid}"));
            foreach (var k in def.Statuses ?? new()) kit.GearStatuses.Add(k);
            // Kindling: one to an item, two to the survivor.
            if (it.Affixes.Select(ar => Items.Affix(ar.Id)).FirstOrDefault(a => a?.Kindled != null) is { } kin && kit.Kindled.Count < Inventory.MaxKindled)
            {
                kit.Kindled.Add(kin.Id);
                Kindle(kit, kin.Kindled!);
            }
            GearSkills(ch, it, def, s, kit.Weapons);
            // Auto skills a great piece grants: every one worn, stacked, none refused for her calling.
            foreach (var (skill, rank) in def.Auto ?? new())
                if (Content.Weapons.All.ContainsKey(skill) && kit.AutoSkills.All(w => w.Id != skill)) kit.AutoSkills.Add((skill, rank));
            // Marks, worn into the maps (Battle.Wear): one to a piece, three at once, and the same Mark
            // twice is the finer of the two (design 20.3).
            if (it.Affixes.FirstOrDefault(ar => Items.Affix(ar.Id)?.Mark == true) is { } mk
                && (kit.Marks.ContainsKey(mk.Id) || kit.Marks.Count < Crafting.Rules.Mark.Worn))
                kit.Marks[mk.Id] = Math.Max(kit.Marks.GetValueOrDefault(mk.Id), Items.MarkStrength(mk.Tier));
        }
        // A set worn far enough: each bonus reached, its numbers and its rules (docs/design/LOOT_DESIGN.md §10.2).
        foreach (var (set, b) in Drops.SetBonuses(ch))
        {
            string from = $"set:{set.Id}:{b.Worn}";
            if (b.Mods != null) st.AddAll(b.Mods.Select(m => m with { Source = from }));
            foreach (var t in b.Triggers ?? new()) kit.Triggers.Add((t, from));
        }
        foreach (var (id, rank) in SkillBook.Carried(ch))
            if (kit.Weapons.All(w => w.Id != id)) kit.Learned.Add((id, rank));
        kit.Bar = Bar(ch, kit.Weapons, kit.Autos);
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
        st.AddAll(lamps.Mods);
        // Cold, Then Not held in the art's place: once a fight, a killing blow does not end her.
        if (ch.Ability == "cold_then_not") kit.Revives = Math.Max(kit.Revives, 1);
        foreach (var c in ch.Conditions)
        {
            switch (c.Id)
            {
                case ConditionId.Wounded: st.Add(new(Stat.MaxHealth, ModKind.More, -0.2, "cond:wounded")); break;
                case ConditionId.Blightsick: st.Add(new(Stat.Regen, ModKind.Flat, -0.8, "cond:blightsick")); break;
                case ConditionId.Blessed: st.Add(new(Stat.DamageOf(School.Holy), ModKind.Inc, 0.15, "cond:blessed")); break;
                case ConditionId.Rested: st.Add(new(Stat.MaxHealth, ModKind.Inc, 0.05, "cond:rested")); break;
                // Warmed (a love scene's night) only says the night happened: the owner's call, so
                // sex earns nothing in a fight (Australia's R18+; docs/legal/LEGAL_BRIEF.md, issue 7).
                case ConditionId.Warmed: break;
            }
        }
        return kit;
    }

    /// <summary>The skills one worn piece brings a fight, into the kit's list: those its affixes grant (while there is
    /// room), then its weapon's own (Kit and DaySkills share it).</summary>
    static void GearSkills(CharacterData ch, ItemInstance it, ItemDef def, EquipSlot s, List<(string Id, int Rank)> into)
    {
        // Skills the gear grants (bd-keys: no cap here; Character.Bar puts a pressed one in a free key, and an auto one
        // runs beside her three auto slots, as many as she wears).
        foreach (var ar in it.Affixes)
            if (Items.Affix(ar.Id)?.Grants is { } g && SkillBook.Carries(ch, g) && into.All(w => w.Id != g))
                into.Add((g, 1 + ar.Tier / 2));
        // A weapon whose skill the calling may not carry is worn for its numbers; its skill lies idle.
        if (def.Weapon != null && s is (EquipSlot.Weapon or EquipSlot.Offhand) && SkillBook.Carries(ch, def.Weapon.Id))
        {
            // Mastery: every 60 kills with a weapon starts it a rank higher, to +2.
            int bonus = Math.Min(2, ch.Mastery.GetValueOrDefault(def.Weapon.Id) / 60);
            into.Add((def.Weapon.Id, Math.Min(Inventory.GearRankCap, def.Weapon.Rank + bonus + Math.Max(0, it.Rarity - def.Rarity))));
        }
    }

    /// <summary>The skills she fights with by day, in the order the fight takes them up (Character.Bar: her keys, her auto
    /// slots, her gear's auto skills), each at its rank: the Battle's Weapons before any draft.</summary>
    /// <param name="gearOnly">Only the gear's, every one (by night these come in at their ranks; the rest the ember drafts).</param>
    public static List<(string Id, int Rank)> DaySkills(CharacterData ch, bool gearOnly = false)
    {
        var gear = new List<(string Id, int Rank)>();
        foreach (var s in Items.EquipSlots)
            if (ch.Equipment[s] is { } it) GearSkills(ch, it, Items.Get(it.Def), s, gear);
        if (!gearOnly) return Bar(ch, gear, new HashSet<string>());
        var o = new List<(string Id, int Rank)>();
        foreach (var (id, rank) in gear)
            if (o.All(w => w.Id != id) && Content.Weapons.All.ContainsKey(id)) o.Add((id, rank));
        return o;
    }

    /// <summary>(bd-keys) Her gear grants this skill now (an affix's or its weapon's): she may carry it while she wears it.</summary>
    public static bool Worn(CharacterData ch, string id) => DaySkills(ch, gearOnly: true).Any(w => w.Id == id);

    /// <summary>(bd-keys, BUILD_DIRECTION.md rounds 7-8) Her bar for a campaign fight, in the order the battle takes it up:
    /// the keys open at her level in key order (ch.Slotted's: learned skills, and worn ones she put in a key), a pressed
    /// skill her gear grants in a key still free, her auto slots open at her level, then every auto skill her gear grants
    /// (item auto skills stack with no cap). A skill learned and worn takes its learned rank. `autos` gets what runs itself.</summary>
    public static List<(string Id, int Rank)> Bar(CharacterData ch, List<(string Id, int Rank)> gear, HashSet<string> autos)
    {
        var learned = new Dictionary<string, int>();
        foreach (var (id, rank) in SkillBook.Carried(ch)) learned[id] = rank;
        var worn = new Dictionary<string, int>();
        foreach (var (id, rank) in gear) if (!worn.ContainsKey(id) && Content.Weapons.All.ContainsKey(id)) worn[id] = rank;
        int keys = SkillBook.KeysAt(ch.Level), mine = SkillBook.AutosAt(ch.Level);
        var keyed = new List<(string Id, int Rank)>();
        var auto = new List<(string Id, int Rank)>();
        bool On(string id) => keyed.Exists(w => w.Id == id) || auto.Exists(w => w.Id == id);
        foreach (var id in ch.Slotted.ToList())
        {
            if (On(id) || !SkillBook.Carries(ch, id)) continue;
            int rank;
            if (learned.TryGetValue(id, out var lr)) rank = lr;
            else if (!SkillBook.Knows(ch, id) && worn.TryGetValue(id, out var wr)) rank = wr;
            else continue;
            if (SkillBook.IsAuto(ch, id)) { if (mine-- > 0) auto.Add((id, rank)); }
            else if (Content.Weapons.SlotCost(id) <= keys) { keys -= Content.Weapons.SlotCost(id); keyed.Add((id, rank)); }
        }
        var items = new List<(string Id, int Rank)>();
        foreach (var (id, rank) in worn)
        {
            if (On(id) || items.Exists(w => w.Id == id)) continue;
            // A pressed skill she wears and has not put anywhere takes a key still free; one that can run itself runs.
            if (Content.Weapons.KeyOnly(id) || Content.Weapons.IsUnion(id))
            {
                if (Content.Weapons.SlotCost(id) <= keys) { keys -= Content.Weapons.SlotCost(id); keyed.Add((id, rank)); }
            }
            else items.Add((id, rank));
        }
        autos.Clear();
        foreach (var (id, _) in auto.Concat(items)) autos.Add(id);
        return keyed.Concat(auto).Concat(items).ToList();
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
