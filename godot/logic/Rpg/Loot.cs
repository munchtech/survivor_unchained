using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* What falls, how good it is, and where it goes (docs/design/LOOT_DESIGN.md).
 *
 * Gear comes only from what visibly carries it, and is rolled whole where it
 * falls, so the filter and the beam know what it is before it is taken. A
 * piece carries the level of what dropped it; the level sets its make, and
 * the make multiplies its base's own numbers, so a late Common can beat an
 * early Epic. Rarity still means something: the affixes keep crafting's
 * fixed grades, and rise only past level 25. The numbers are data
 * (data/content/loot.json). */

/// <summary>A drop's tier for the eye: the rarity's, with Set apart; then what is not gear.</summary>
public enum LootTier { Common, Uncommon, Rare, Epic, Set, Legendary, Storied, Material, Book, Chart, Draught, Quest }

/// <summary>How well a base was made, by its level: the word on its tooltip.</summary>
public enum Make { Worn, Sound, Wrought, Legion, Heartwrought }

/// <summary>Where a carried thing lives: the pack's places (gear only), what is worn, and the
/// slotless stores that never fill (docs/design/LOOT_DESIGN.md §6).</summary>
public enum Store { Pack, Worn, Pouch, Satchel, Keys, Belt }

/// <summary>What carried the gear: each pays its own way (§5.1).</summary>
public enum DropSource { Champion, Miniboss, Herald, Boss, Elite, MapPack, MapPackFine, MapKeeper, MapRuler, Strongbox }

/// <summary>A source's terms: the chance each roll is gear, how many rolls, the least tier of
/// the first, how much likelier Rare and up are, and what it gives when a roll is not gear.</summary>
public sealed class SourceRule
{
    public double Chance = 1;
    public int Rolls = 1;
    /// <summary>Rolls added at the arena's third tier and up (a boss's hoard).</summary>
    public int Deep;
    /// <summary>The least tier of the first roll (0 Common, 1 Uncommon, 2 Rare).</summary>
    public int Floor;
    public double Quality = 1, Legendary = 1;
    /// <summary>Given beside the gear, always: the people's material.</summary>
    public int Materials;
}

/// <summary>What a set gives at so many pieces worn.</summary>
public sealed class SetBonus
{
    public int Worn;
    public string Text = "";
    public List<StatMod>? Mods;
    public List<TriggerDef>? Triggers;
    public List<string>? Tags;
}

public sealed class SetDef
{
    public string Id = "", Name = "";
    public List<string> Pieces = new();
    public List<SetBonus> Bonuses = new();
    public string? Lore;
}

public sealed class LootRules
{
    /// <summary>The level each make starts at, its multiplier on a base's own numbers, and the
    /// increased damage a weapon of it carries.</summary>
    public List<int> MakeFrom = new() { 1, 8, 16, 24, 32 };
    public List<double> MakeMult = new() { 1, 1.8, 2.8, 4.0, 5.5 };
    public List<double> MakeDamage = new() { 0, 0.1, 0.25, 0.45, 0.7 };
    /// <summary>A stat's own make curve where the general one is too steep for it (armour saturates).</summary>
    public Dictionary<string, List<double>> Curves = new();
    /// <summary>A base's numbers the make never scales (a shield's block rank, speed).</summary>
    public List<string> Unscaled = new() { "block", "moveSpeed" };
    public int MaxLevel = 40;
    /// <summary>The levels from which a drop's grades rise one, then two (to VI at most).</summary>
    public List<int> GradeUp = new() { 25, 35 };

    /* A gear roll's tier, by level L: Common = CommonBase × CommonFall^(L−1); Uncommon flat;
     * Rare and Epic = Base + Per × L; Set and Legendary flat, when one may drop here. */
    public double CommonBase = 40, CommonFall = 0.93, Uncommon = 34, RareBase = 18, RarePer = 0.5, EpicBase = 3.5, EpicPer = 0.2;
    public double Set = 0.9, Legendary = 0.4;
    /// <summary>The share of what luck adds above 1 that raises Rare and up.</summary>
    public double LuckShare = 0.5;
    /// <summary>A base roll is a weapon this often; that weapon is of the survivor's calling this often.</summary>
    public double WeaponShare = 0.25, CallingShare = 0.67;
    /// <summary>A Set or Legendary piece never owned is this much likelier; one whose home is here this much.</summary>
    public double Unowned = 4, Home = 2;
    /// <summary>The dark's debt: gear rolls without a Legendary before a boss's hoard holds one for certain.</summary>
    public int Debt = 120;
    /// <summary>The scars past the half hour: Rare and up likelier by this a minute, to this much more.</summary>
    public double DepthPerMinute = 0.02, DepthCap = 1;
    /// <summary>A carrier that drops no gear: its people's material, and old iron this often.</summary>
    public int Material = 1;
    public double Iron = 0.5;
    /// <summary>A draught kind's carry limit on the belt.</summary>
    public int Belt = 20;
    /// <summary>An upgrade must beat what is worn by this much (and a little more).</summary>
    public double UpgradeMargin = 1.05;
    /// <summary>What a unit of each stat is worth to the power score: "stat:kind", "stat", "prefix.*".</summary>
    public Dictionary<string, double> Power = new();
    /// <summary>Each source's terms, by its key ("champion", "mapRuler").</summary>
    public Dictionary<string, SourceRule> Sources = new();
    public Dictionary<string, SetDef> Sets = new();
}

/// <summary>Everything a drop roll needs to know about where it falls.</summary>
public sealed class DropCtx
{
    public CharacterData? Ch;
    public World.WorldState? World;
    public DropSource Source;
    /// <summary>The level of what carried it (its item level).</summary>
    public int Level = 1;
    /// <summary>The people it fell among (pack, dead, lamplings, kerchiefs): homes and materials.</summary>
    public string? People;
    public IReadOnlyCollection<string>? Lean;
    public double Luck = 1, Rarity = 1, Quantity = 1, Gear = 1;
    /// <summary>The scars: minutes past the half hour.</summary>
    public double Depth;
    /// <summary>The arena's tier (a hoard's extra rolls from the third).</summary>
    public int Tier = 1;
    /// <summary>Rolls beyond the source's own (what the atlas has earned).</summary>
    public int Extra;
    /// <summary>A story fight's boss: the first one a survivor beats pays a Legendary for certain.</summary>
    public bool StoryBoss;
    /// <summary>Whether a story condition holds (a piece's DropsWhen).</summary>
    public Func<World.Cond?, bool>? Allows;
    public Func<double> R = () => Random.Shared.NextDouble();
}

/// <summary>A thing rolled to fall: gear (rolled whole) or a material, with its tier.</summary>
public sealed record Dropped(ItemInstance? Item, string? Material, int Qty, LootTier Tier);

public static class Drops
{
    static LootRules? rules;
    public static LootRules Rules => rules ??= Json.Parse<LootRules>(Json.ReadContent("loot.json"));

    public const string Iron = "old_iron";

    /// <summary>The story lead's words (WRITING_PASS §25): the HUD's line when a Legendary falls, the
    /// debt's label, and its line when it pays.</summary>
    public const string NamedFalls = "This one has a name.", DebtLabel = "What the dark owes you", DebtPaid = "The dark settles up.";

    /* ----------------------------------------------------------- tiers -- */

    public static LootTier TierOf(ItemDef def, int rarity)
    {
        if (Items.SlotFor(def) != null)
        {
            if (rarity >= 5) return LootTier.Storied;
            if (def.Set != null) return LootTier.Set;
            return rarity switch { <= 0 => LootTier.Common, 1 => LootTier.Uncommon, 2 => LootTier.Rare, 3 => LootTier.Epic, _ => LootTier.Legendary };
        }
        return StoreOf(def, null) switch
        {
            Store.Pouch => LootTier.Material,
            Store.Belt => LootTier.Draught,
            Store.Satchel => def.Id == Maps.Charts.Item ? LootTier.Chart : def.Kind == ItemKind.Trophy ? LootTier.Material : LootTier.Book,
            _ => LootTier.Quest,
        };
    }

    public static LootTier TierOf(ItemInstance it) => TierOf(Items.Get(it.Def), it.Rarity);

    /// <summary>Gear the eye should never lose: these the filter can never hide.</summary>
    public static bool Jackpot(LootTier t) => t is LootTier.Set or LootTier.Legendary or LootTier.Storied or LootTier.Quest;

    /* ---------------------------------------------------------- stores -- */

    /// <summary>Where a thing is carried: gear in the pack; materials and trophies in the pouch;
    /// books, charts and the rulers' marked things in the satchel; draughts on the belt; quest
    /// things and tools on the key ring.</summary>
    public static Store StoreOf(ItemDef def, ItemInstance? it)
    {
        if (Items.SlotFor(def) != null) return Store.Pack;
        switch (def.Kind)
        {
            case ItemKind.Material: return Store.Pouch;
            // A ruler's thing carries its Mark at a grade, so it is kept whole, with the charts.
            case ItemKind.Trophy: return def.Tags?.Contains("mark") == true || it?.Affixes.Count > 0 ? Store.Satchel : Store.Pouch;
            case ItemKind.Consumable:
                return def.Consumable is { Teaches: null, Skill: null } c && (c.Heal != null || c.Cure != null || c.Buff != null) ? Store.Belt : Store.Satchel;
            case ItemKind.Tool: return def.Id == Maps.Charts.Item || it?.Chart != null ? Store.Satchel : Store.Keys;
            case ItemKind.Quest: return Store.Keys;
            default: return Store.Pack;
        }
    }

    /* ------------------------------------------------- level and make -- */

    public static int LevelOf(ItemInstance it) => Math.Clamp(it.Level ?? 1, 1, Rules.MaxLevel);

    public static Make MakeOf(int level)
    {
        var from = Rules.MakeFrom;
        int m = 0;
        for (int i = 0; i < from.Count; i++) if (level >= from[i]) m = i;
        return (Make)Math.Min(m, (int)Make.Heartwrought);
    }

    public static Make MakeOf(ItemInstance it) => MakeOf(LevelOf(it));

    /// <summary>Whether a piece carries a level and a make: anything worn.</summary>
    public static bool Leveled(ItemDef def) => Items.SlotFor(def) != null;

    /// <summary>How many grades a drop's affixes rise for its level (none below 25).</summary>
    public static int GradeShift(int? level) => level is int l ? Rules.GradeUp.Count(f => l >= f) : 0;

    /// <summary>The base a piece's own numbers come from: itself if it is a base, or the base a
    /// named piece is built on.</summary>
    public static ItemDef? BaseOf(ItemDef def) => def.Base ? def : def.Of != null ? Items.Find(def.Of) : null;

    /// <summary>A piece's implicits at its make: its base's own numbers multiplied (downsides and
    /// a few numbers never are), and a weapon's increased damage.</summary>
    public static List<StatMod> Implicit(ItemDef def, int? level)
    {
        var o = new List<StatMod>();
        var make = MakeOf(Math.Clamp(level ?? 1, 1, Rules.MaxLevel));
        if (BaseOf(def) is { Mods: { } mods })
            foreach (var m in mods)
                o.Add(m.Value > 0 && !Rules.Unscaled.Contains(m.Stat) ? m with { Value = m.Value * Mult(make, m.Stat) } : m);
        if (def.Kind == ItemKind.Weapon && def.Weapon != null && Rules.MakeDamage[(int)make] > 0)
            o.Add(new StatMod(Stat.Damage, ModKind.Inc, Rules.MakeDamage[(int)make], "item"));
        return o;
    }

    /// <summary>What the make multiplies a stat by: its own curve, or the general one.</summary>
    public static double Mult(Make make, string stat) =>
        (Rules.Curves.TryGetValue(stat, out var c) ? c : Rules.MakeMult)[(int)make];

    /// <summary>A piece's rules at its make: a flat number in them (a lamp's flare, black water's
    /// bite) grows as its base's numbers do, so a deep copy is not a toy (combat's ask). Rules
    /// reading the blow or the weapon already grow with what they read.</summary>
    public static List<TriggerDef> Triggers(ItemDef def, int? level)
    {
        double k = Mult(MakeOf(Math.Clamp(level ?? 1, 1, Rules.MaxLevel)), "trigger");
        if (def.Triggers == null) return new();
        if (k == 1) return def.Triggers;
        Effect Scale(Effect e) => e switch
        {
            Effect.Nova n when n.Basis == Basis.Flat => n with { Damage = n.Damage * k },
            Effect.Explode x when x.Basis == Basis.Flat => x with { Damage = x.Damage * k },
            Effect.Zone z when z.Basis == Basis.Flat => z with { Dps = z.Dps * k },
            Effect.Strike s when s.Basis == Basis.Flat => s with { Damage = s.Damage * k },
            Effect.Missiles m when m.Basis == Basis.Flat => m with { Damage = m.Damage * k },
            Effect.Chain c when c.Basis == Basis.Flat => c with { Damage = c.Damage * k },
            _ => e,
        };
        return def.Triggers.Select(t => new TriggerDef { On = t.On, Chance = t.Chance, Icd = t.Icd, When = t.When, Text = t.Text, Effects = t.Effects.Select(Scale).ToArray() }).ToList();
    }

    /* ----------------------------------------------------------- power -- */

    static double Weight(StatMod m)
    {
        var p = Rules.Power;
        string kind = m.Kind.Key();
        if (p.TryGetValue($"{m.Stat}:{kind}", out var w) || p.TryGetValue(m.Stat, out w)) return w;
        int dot = m.Stat.IndexOf('.');
        if (dot > 0 && (p.TryGetValue($"{m.Stat[..dot]}.*:{kind}", out w) || p.TryGetValue($"{m.Stat[..dot]}.*", out w))) return w;
        return 0;
    }

    /// <summary>What a piece is worth, in one number never shown: its numbers by their value, its
    /// rules, its kindling and skills, its weapon's rank. The filter's upgrade test and the
    /// tile's arrow read it.</summary>
    public static double Power(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        double s = 0;
        foreach (var m in Inventory.Mods(it))
            s += Weight(m) * m.Value * (m.When != null ? 0.5 : 1);
        s += (def.Triggers?.Count ?? 0) * 5;
        foreach (var a in it.Affixes)
            if (Items.Affix(a.Id) is { } ad) s += ad.Kindled != null ? 4 : ad.Grants != null ? 6 : 0;
        if (def.Weapon != null) s += 8 * Inventory.WeaponRank(it);
        return s;
    }

    /// <summary>Better than what is worn where it would go (the weaker ring for a ring; an empty
    /// place is always bettered). A weapon only against a weapon of its own skill: another skill
    /// is another way to play, not an upgrade.</summary>
    public static bool IsUpgrade(CharacterData ch, ItemInstance it)
    {
        var def = Items.Get(it.Def);
        if (Items.SlotFor(def) is not EquipSlot slot) return false;
        var worn = slot == EquipSlot.Ring1
            ? new[] { ch.Equipment.Ring1, ch.Equipment.Ring2 }.OrderBy(r => r == null ? -1 : Power(r)).First()
            : ch.Equipment[slot];
        if (worn == null) return def.Kind != ItemKind.Weapon;
        if (worn.Uid == it.Uid) return false;
        if (def.Kind == ItemKind.Weapon && Items.Get(worn.Def).Weapon?.Id != def.Weapon?.Id) return false;
        return Power(it) > Power(worn) * Rules.UpgradeMargin + 0.5;
    }

    /// <summary>A better make than what is worn in that place (the anvil mark).</summary>
    public static bool BetterMake(CharacterData ch, ItemInstance it)
    {
        var def = Items.Get(it.Def);
        if (Items.SlotFor(def) is not EquipSlot slot) return false;
        var worn = slot == EquipSlot.Ring1 ? ch.Equipment.Ring1 ?? ch.Equipment.Ring2 : ch.Equipment[slot];
        return worn != null && MakeOf(it) > MakeOf(worn);
    }

    /* ------------------------------------------------------------ sets -- */

    public static SetDef? SetOf(ItemDef def) => def.Set != null ? Rules.Sets.GetValueOrDefault(def.Set) : null;

    /// <summary>How many of each set the survivor wears (each piece once, however many copies).</summary>
    public static Dictionary<string, int> SetsWorn(CharacterData ch)
    {
        var o = new Dictionary<string, HashSet<string>>();
        foreach (var s in Items.EquipSlots)
            if (ch.Equipment[s] is { } it && Items.Find(it.Def) is { Set: { } set } d)
                (o.TryGetValue(set, out var h) ? h : o[set] = new()).Add(d.Id);
        return o.ToDictionary(kv => kv.Key, kv => kv.Value.Count);
    }

    /// <summary>The bonuses in force: every one of a set whose count is reached.</summary>
    public static IEnumerable<(SetDef Set, SetBonus Bonus)> SetBonuses(CharacterData ch) =>
        SetsWorn(ch).SelectMany(kv => Rules.Sets.TryGetValue(kv.Key, out var sd)
            ? sd.Bonuses.Where(b => kv.Value >= b.Worn).Select(b => (sd, b)) : Enumerable.Empty<(SetDef, SetBonus)>());

    /* ----------------------------------------------------------- drops -- */

    /// <summary>A Set or Legendary piece that may fall here: its least level met, its story
    /// condition holding.</summary>
    static bool MayDrop(ItemDef d, DropCtx x) =>
        d.DropsFrom is int from && x.Level >= from && (d.DropsWhen == null || x.Allows?.Invoke(d.DropsWhen) == true);

    public static IEnumerable<ItemDef> Legendaries(DropCtx x) =>
        Items.All.Values.Where(d => d.Rarity == 4 && d.Set == null && Leveled(d) && MayDrop(d, x));

    public static IEnumerable<ItemDef> SetPieces(DropCtx x) =>
        Items.All.Values.Where(d => d.Set != null && MayDrop(d, x));

    /// <summary>The early pool: the Legendaries that drop from the first levels (the certain first).</summary>
    public static IEnumerable<ItemDef> EarlyLegendaries() =>
        Items.All.Values.Where(d => d.Rarity == 4 && d.Set == null && d.DropsFrom is <= 3 && d.DropsWhen == null && Leveled(d));

    /// <summary>The tier weights at a level, before a source's or a chart's multipliers.</summary>
    public static double[] Weights(int level)
    {
        var r = Rules;
        int l = Math.Clamp(level, 1, r.MaxLevel);
        return
        [
            r.CommonBase * Math.Pow(r.CommonFall, l - 1), r.Uncommon, r.RareBase + r.RarePer * l, r.EpicBase + r.EpicPer * l, r.Set, r.Legendary,
        ];
    }

    /// <summary>One gear roll's tier (LootTier Common to Legendary), the source's floor applied.</summary>
    public static LootTier RollTier(DropCtx x, SourceRule src, int floor, Func<double> R)
    {
        var w = Weights(x.Level);
        double depth = Math.Min(Rules.DepthCap, x.Depth * Rules.DepthPerMinute);
        double q = src.Quality * x.Rarity * (1 + Math.Max(0, x.Luck - 1) * Rules.LuckShare) * (1 + depth);
        for (int i = 2; i < w.Length; i++) w[i] *= q;
        w[5] *= src.Legendary * (1 + depth);
        bool sets = SetPieces(x).Any(), legends = Legendaries(x).Any();
        if (!sets) { w[3] += w[4]; w[4] = 0; }
        if (!legends) { w[3] += w[5]; w[5] = 0; }
        for (int i = 0; i < Math.Min(floor, 3); i++) w[i] = 0;
        double total = w.Sum(), roll = R() * total;
        for (int i = 0; i < w.Length; i++) { roll -= w[i]; if (roll < 0) return (LootTier)i; }
        return (LootTier)Array.FindLastIndex(w, v => v > 0);
    }

    static bool Owned(CharacterData? ch, World.WorldState? w, string def) =>
        ch != null && (ch.Equipment is var e && Items.EquipSlots.Any(s => e[s]?.Def == def) || ch.Pack.Any(p => p?.Def == def))
        || w != null && (w.Owned.Contains(def) || w.Stash.Any(p => p?.Def == def));

    static ItemDef PickNamed(IEnumerable<ItemDef> pool, DropCtx x, Func<double> R)
    {
        var list = pool.ToList();
        double W(ItemDef d) => (Owned(x.Ch, x.World, d.Id) ? 1 : Rules.Unowned) * (x.People != null && d.Homes?.Contains(x.People) == true ? Rules.Home : 1);
        double total = list.Sum(W), roll = R() * total;
        foreach (var d in list) { roll -= W(d); if (roll < 0) return d; }
        return list[^1];
    }

    /// <summary>The weapons that drop: every calling's, the survivor's own two times in three.</summary>
    static string PickBase(DropCtx x, Func<double> R)
    {
        if (R() < Rules.WeaponShare)
        {
            var all = Callings.Archetypes.Values.SelectMany(a => a.Weapons).Distinct().OrderBy(id => id, StringComparer.Ordinal).ToList();
            var mine = x.Ch != null ? Callings.Archetype(x.Ch.Archetype).Weapons : new List<string>();
            var pool = mine.Count > 0 && R() < Rules.CallingShare ? mine : all;
            return pool[(int)(R() * pool.Count) % pool.Count];
        }
        var bases = Items.All.Values.Where(d => d.Base && Leveled(d)).Select(d => d.Id).OrderBy(id => id, StringComparer.Ordinal).ToList();
        return bases[(int)(R() * bases.Count) % bases.Count];
    }

    /// <summary>One piece of gear at a tier, rolled whole: its base or named piece, level, rarity, affixes.</summary>
    public static ItemInstance Piece(DropCtx x, LootTier tier, Func<double> R)
    {
        int level = Math.Clamp(x.Level, 1, Rules.MaxLevel);
        uint seed = (uint)(R() * int.MaxValue);
        if (tier == LootTier.Legendary)
        {
            var d = PickNamed(Legendaries(x), x, R);
            return Inventory.Make(x.Ch, d.Id, seed: seed, dropped: true, level: level);
        }
        if (tier == LootTier.Set)
        {
            var d = PickNamed(SetPieces(x), x, R);
            return Inventory.Make(x.Ch, d.Id, seed: seed, dropped: true, level: level);
        }
        string id = PickBase(x, R);
        return Inventory.Make(x.Ch, id, rarity: (int)tier, seed: seed, lean: x.Lean, dropped: true, level: level);
    }

    /// <summary>What a carrier leaves: its gear rolls (each gear at the source's chance, else the
    /// people's material and now and then old iron), the source's own materials, the certain
    /// first Legendary of a story boss, and the dark's debt paid at a boss.</summary>
    public static List<Dropped> Roll(DropCtx x)
    {
        var R = x.R;
        var src = Rules.Sources.GetValueOrDefault(x.Source.Key()) ?? new SourceRule();
        var o = new List<Dropped>();
        var w = x.World;
        int rolls = src.Rolls + (x.Tier >= 3 ? src.Deep : 0) + Math.Max(0, x.Extra);
        // A chart's quantity: each part over one is a further roll as often.
        double extra = Math.Max(0, x.Quantity - 1) * rolls;
        rolls += (int)extra + (R() < extra % 1 ? 1 : 0);
        bool hoard = x.Source is DropSource.Boss or DropSource.MapRuler;
        bool owed = hoard && w != null && w.LootDebt >= Rules.Debt;
        bool first = x.StoryBoss && w != null && !w.FirstLegendary && EarlyLegendaries().Any();
        string? material = x.People != null ? PeopleMaterial(x.People) : null;
        for (int k = 0; k < rolls; k++)
        {
            bool gear = R() < Math.Min(1, src.Chance * x.Gear);
            if (!gear)
            {
                if (material != null) o.Add(new Dropped(null, material, Rules.Material, LootTier.Material));
                if (R() < Rules.Iron) o.Add(new Dropped(null, Iron, 1, LootTier.Material));
                continue;
            }
            LootTier tier;
            ItemInstance it;
            if (k == 0 && first)
            {
                // The first story boss beaten: a Legendary from the early pool, the calling's own likelier.
                var pool = EarlyLegendaries().ToList();
                var mine = x.Ch != null ? pool.Where(d => d.Of != null && Callings.Archetype(x.Ch.Archetype).Weapons.Contains(d.Of)).ToList() : new();
                var d = mine.Count > 0 && R() < 0.75 ? mine[(int)(R() * mine.Count) % mine.Count] : PickNamed(pool, x, R);
                it = Inventory.Make(x.Ch, d.Id, seed: (uint)(R() * int.MaxValue), dropped: true, level: Math.Clamp(x.Level, 1, Rules.MaxLevel));
                tier = LootTier.Legendary;
                w!.FirstLegendary = true;
            }
            else
            {
                tier = k == 0 && owed && Legendaries(x).Any() ? LootTier.Legendary : RollTier(x, src, k == 0 ? src.Floor : 0, R);
                it = Piece(x, tier, R);
                tier = TierOf(it);
            }
            if (w != null)
            {
                if (tier == LootTier.Legendary) { w.LootDebt = 0; w.FirstLegendary = true; }
                else w.LootDebt++;
                if (tier is LootTier.Legendary or LootTier.Set) w.Owned.Add(it.Def);
            }
            o.Add(new Dropped(it, null, 1, tier));
        }
        if (src.Materials > 0 && material != null) o.Add(new Dropped(null, material, src.Materials, LootTier.Material));
        return o;
    }

    /// <summary>The material a people's carriers drop (crafting's night yields, by people).</summary>
    public static string? PeopleMaterial(string people) => people switch
    {
        "pack" => "wolf_pelt", "dead" => "bone_dust", "lamplings" => "ember_shard", "kerchiefs" => "kerchief_cloth", _ => null,
    };

    /// <summary>The people a creature's family belongs to, for homes by day.</summary>
    public static string? PeopleOf(Family f) => f switch
    {
        Family.Wolf or Family.Boar or Family.Beast => "pack", Family.Undead => "dead", Family.Lampling => "lamplings",
        Family.Kerchief or Family.Human => "kerchiefs", _ => null,
    };

    /// <summary>Drops as the fight spawns them: gear carries its whole piece (Payload), its tier
    /// and the filter's word on it; a material is a material pickup.</summary>
    public static List<Sim.Loot> AsLoot(IEnumerable<Dropped> drops, Func<ItemInstance, Verdict>? judge = null) =>
        drops.Select(d => d.Item is { } it
            ? new Sim.Loot(PickupKind.Item, it.Def, 1, true, it.Rarity, null, it, (int)d.Tier, judge?.Invoke(it) ?? Verdict.Shown)
            : new Sim.Loot(PickupKind.Material, d.Material, d.Qty, false, 0, null, null, (int)LootTier.Material, Verdict.Shown)).ToList();
}
