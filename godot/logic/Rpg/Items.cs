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
    /// <summary>A tome: the combat skill it teaches (one seen burning in an arena).</summary>
    public string? Skill;
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
    /// <summary>A quest thing the story may still ask for while this holds
    /// (always, when it is not written): until then it is neither sold over
    /// a counter nor dropped. Once its part is played it is only a keepsake.</summary>
    public World.Cond? Needed;
    /// <summary>A named piece the Waystation's hands may still work (one of their own making):
    /// plain bases and weapons always may (docs/CRAFTING_DESIGN.md, "Which pieces can be worked").</summary>
    public bool Workable;
    /// <summary>The name of several, in running text ("wolf pelts", "old iron"): a material's.</summary>
    public string? Plural;
}

public sealed class AffixDef
{
    public string Id = "", Name = "";
    public bool Prefix;
    public ItemKind[] Slots = Array.Empty<ItemKind>();
    public Func<int, StatMod[]> Mods = _ => Array.Empty<StatMod>();
    public Func<int, string> Text = _ => "";
    /// <summary>A skill (weapon) the gear grants while worn.</summary>
    public string? Grants;
    /// <summary>The least rarity it rolls on (skills come only on fine gear).</summary>
    public int MinRarity;
    /// <summary>Given, never rolled: a trophy's power set into a piece (Greymuzzle's fang), or what the
    /// slurry leaves in a steeped one.</summary>
    public bool Unique;
    /// <summary>The slurry's: strong, with a price; shown in its sick green.</summary>
    public bool Slurry;
    /// <summary>A Mark (Sim/Marks.cs; design 20.3): what a map's ruler leaves, inscribed by Vonnra. It
    /// changes how one skill or verb behaves in the Wayfinder's maps, and only there, read by id; its
    /// grade (I to VI) is its strength. It takes a seam; one to a piece, three worn at once.</summary>
    public bool Mark;
    /// <summary>What it gives the night's ember beyond numbers (docs/SKILLS_DESIGN.md,
    /// "Gear and the ember"): spark, reroll, refusal, roads, omens, or stand:PASSIVE,
    /// which counts as that passive in an evolution's recipe. One to an item,
    /// two to a survivor.</summary>
    public string? Kindled;
}

public static class Items
{
    sealed class File { public Dictionary<string, ItemDef> Items = new(); public List<string> Raritynames = new(); }

    static Dictionary<string, ItemDef>? all;
    static List<string>? rarityNames;

    static void Load()
    {
        var f = Json.Parse<File>(Json.ReadContent("items.json"));
        var items = f.Items;
        // A tome for every skill the ember can give: what was taken as a card in
        // an arena, written down to be learned by day.
        foreach (var id in Content.Weapons.Pool)
        {
            var w = Content.Weapons.All[id];
            items[SkillBook.Tome(id)] = new ItemDef
            {
                Id = SkillBook.Tome(id), Name = $"Tome: {w.Name}", Kind = ItemKind.Consumable, Rarity = 2, Icon = "book", Value = 140, Stack = 1,
                Description = $"Read it to learn {w.Name} for the day, if you have seen it burn in an arena. {w.Description}",
                Lore = "Someone came out of the dark knowing this, and wrote it down before it went.",
                Consumable = new Consumable { Skill = id },
            };
        }
        // Published only when whole: the tests read it from several threads at once.
        rarityNames = f.Raritynames;
        all = items;
    }

    public static Dictionary<string, ItemDef> All { get { if (all == null) Load(); return all!; } }
    public static IReadOnlyList<string> RarityNames { get { if (rarityNames == null) Load(); return rarityNames!; } }
    public static readonly EquipSlot[] EquipSlots = EnumKey<EquipSlot>.All;

    public static ItemDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown item {id}");
    public static ItemDef? Find(string id) => All.TryGetValue(id, out var d) ? d : null;

    /// <summary>So many of a thing, in running text: "1 wolf pelt", "3 wolf pelts", "4 old iron".</summary>
    public static string Several(string id, int n)
    {
        var d = Find(id);
        string one = (d?.Name ?? id).ToLowerInvariant();
        return $"{n} {(n == 1 ? one : d?.Plural ?? one)}";
    }

    static StatMod M(string stat, ModKind kind, double value) => new(stat, kind, value, "item");
    static string Pct(double v) => $"{MathX.RoundInt(v * 100)}%";
    static string F1(double v) => v.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);

    /// <summary>Every kind of piece that is worn (declared before the affixes, which read it).</summary>
    static readonly ItemKind[] Gear = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic];

    /// <summary>A Mark's strength from its grade: 0 at grade I, 1 at grade VI (combat lerps across it).</summary>
    public static double MarkStrength(int tier) => Math.Clamp(tier / 5.0, 0, 1);

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

        /* What answers a map: slayers of a people, resistances, sure footing, light. */
        new() { Id = "wolfbane", Name = "Wolfbane", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.VsOf(Family.Wolf), ModKind.Flat, 0.15 + t * 0.08), M(Stat.VsOf(Family.Beast), ModKind.Flat, 0.15 + t * 0.08), M(Stat.VsOf(Family.Boar), ModKind.Flat, 0.15 + t * 0.08)],
            Text = t => $"+{Pct(0.15 + t * 0.08)} damage to wolves and beasts" },
        new() { Id = "gravebane", Name = "Gravebane", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.VsOf(Family.Undead), ModKind.Flat, 0.15 + t * 0.08)], Text = t => $"+{Pct(0.15 + t * 0.08)} damage to the dead" },
        new() { Id = "lampsnuffer", Name = "Lampsnuffer's", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.VsOf(Family.Lampling), ModKind.Flat, 0.15 + t * 0.08), M(Stat.FromOf(Family.Lampling), ModKind.Flat, 0.05 + t * 0.03)],
            Text = t => $"+{Pct(0.15 + t * 0.08)} damage to lamplings, and less from them" },
        new() { Id = "watchmans", Name = "Watchman's", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Ring, ItemKind.Amulet, ItemKind.Offhand],
            Mods = t => [M(Stat.VsOf(Family.Kerchief), ModKind.Flat, 0.15 + t * 0.08), M(Stat.VsOf(Family.Human), ModKind.Flat, 0.1 + t * 0.05)],
            Text = t => $"+{Pct(0.15 + t * 0.08)} damage to Kerchiefs and outlaws" },
        new() { Id = "cruel", Name = "Cruel", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Ring, ItemKind.Amulet],
            Mods = t => [M(Stat.CritDamage, ModKind.Flat, 0.15 + t * 0.1)], Text = t => $"+{Pct(0.15 + t * 0.1)} critical damage" },
        new() { Id = "surefooted", Name = "Surefooted", Prefix = true, Slots = [ItemKind.Cloak, ItemKind.Body, ItemKind.Ring],
            Mods = t => [M(Stat.Tenacity, ModKind.Flat, 0.15 + t * 0.1)], Text = t => $"Slows on you {Pct(0.15 + t * 0.1)} shorter and weaker" },
        new() { Id = "of_the_hearth", Name = "of the Hearth", Prefix = false, Slots = [ItemKind.Cloak, ItemKind.Body, ItemKind.Head, ItemKind.Amulet],
            Mods = t => [M(Stat.ResistOf(School.Frost), ModKind.Flat, 0.1 + t * 0.06), M(Stat.Tenacity, ModKind.Flat, 0.08 + t * 0.04)],
            Text = t => $"+{Pct(0.1 + t * 0.06)} frost resistance; the cold slows you less" },
        new() { Id = "of_the_salamander", Name = "of the Salamander", Prefix = false, Slots = [ItemKind.Cloak, ItemKind.Body, ItemKind.Head, ItemKind.Ring],
            Mods = t => [M(Stat.ResistOf(School.Fire), ModKind.Flat, 0.12 + t * 0.07)], Text = t => $"+{Pct(0.12 + t * 0.07)} fire resistance" },
        new() { Id = "of_the_physician", Name = "of the Physician", Prefix = false, Slots = [ItemKind.Body, ItemKind.Amulet, ItemKind.Ring],
            Mods = t => [M(Stat.ResistOf(School.Nature), ModKind.Flat, 0.12 + t * 0.07), M(Stat.Healing, ModKind.Inc, 0.05 + t * 0.04)],
            Text = t => $"+{Pct(0.12 + t * 0.07)} poison resistance; +{Pct(0.05 + t * 0.04)} mending" },
        new() { Id = "of_the_lantern", Name = "of the Lantern", Prefix = false, Slots = [ItemKind.Head, ItemKind.Amulet, ItemKind.Relic],
            Mods = t => [M(Stat.LightRadius, ModKind.Inc, 0.15 + t * 0.1)], Text = t => $"Your light carries {Pct(0.15 + t * 0.1)} further" },
        new() { Id = "of_the_art", Name = "of the Art", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Head, ItemKind.Relic],
            Mods = t => [M(Stat.AbilityCooldown, ModKind.More, -(0.05 + t * 0.03)), M(Stat.AbilityPower, ModKind.Inc, 0.05 + t * 0.05)],
            Text = t => $"Your art {Pct(0.05 + t * 0.03)} sooner and {Pct(0.05 + t * 0.05)} stronger" },

        /* Set, never rolled: a trophy's power in a piece (docs/CRAFTING_DESIGN.md 10.1). */
        new() { Id = "greymuzzles", Name = "Greymuzzle's", Prefix = true, Slots = [ItemKind.Weapon, ItemKind.Amulet], Unique = true,
            Mods = _ => [M(Stat.VsOf(Family.Wolf), ModKind.Flat, 0.3), M(Stat.VsOf(Family.Beast), ModKind.Flat, 0.3), M(Stat.VsOf(Family.Boar), ModKind.Flat, 0.3)],
            Text = _ => "+30% damage to wolves and beasts" },

        /* The slurry's, past the seams (design 9): strong, and each with its price. */
        new() { Id = "fevered", Name = "Fevered", Prefix = true, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.Damage, ModKind.Inc, 0.2), M(Stat.Healing, ModKind.Inc, -0.15)], Text = _ => "+20% damage; you mend 15% less" },
        new() { Id = "of_the_sump", Name = "of the Sump", Prefix = false, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.Area, ModKind.Inc, 0.25), M(Stat.MoveSpeed, ModKind.Inc, -0.1)], Text = _ => "+25% area; you are 10% slower" },
        new() { Id = "pipe_lads", Name = "Pipe-Lad's", Prefix = true, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.CritChance, ModKind.Flat, 0.15), M(Stat.MaxHealth, ModKind.Inc, -0.1)], Text = _ => "+15% critical chance; 10% less health" },

        /* Marks (design 20.3; combat's behaviours in Sim/Marks.cs): inscribed, never rolled; a grade I to VI
         * is the Mark's strength, 0 to 1 across its bracket. They work in the Wayfinder's maps only. */
        new() { Id = Sim.Marks.Ravine, Name = "of the Long Chase", Prefix = false, Unique = true, Mark = true, Slots = Gear,
            Text = t => $"In the maps: Volley looses a second volley at the farthest foe in reach, for {Pct(Sim.Marks.Lerp(0.2, 0.9, MarkStrength(t)))} of it" },
        new() { Id = Sim.Marks.FallingStar, Name = "of the Falling Star", Prefix = false, Unique = true, Mark = true, Slots = Gear,
            Text = t => $"In the maps: Cinderfall's blast leaves burning ground for {Sim.Marks.Lerp(1, 4, MarkStrength(t)):0.#} s" },
        new() { Id = Sim.Marks.OpenGate, Name = "of the Open Gate", Prefix = false, Unique = true, Mark = true, Slots = Gear,
            Text = t => $"In the maps: your dash leaves a ring of holy fire for 3 s, burning for {Pct(Sim.Marks.Lerp(0.2, 0.9, MarkStrength(t)))} of your strongest skill's damage a second" },
        new() { Id = Sim.Marks.Gyre, Name = "of the Muster", Prefix = false, Unique = true, Mark = true, Slots = Gear,
            Text = t => $"In the maps: Axe Gyre gains an axe for every {MathX.RoundInt(Sim.Marks.Lerp(6, 3, MarkStrength(t)))} foes within 5 m, to three more" },

        /* Skills worn: fine gear that fights for you. */
        new() { Id = "of_motes", Name = "of Seeking Motes", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic, ItemKind.Ring], Grants = "seeking_motes", MinRarity = 2,
            Text = _ => "Grants the skill Seeking Motes" },
        new() { Id = "of_the_gyre", Name = "of the Gyre", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic, ItemKind.Ring], Grants = "axe_gyre", MinRarity = 2,
            Text = _ => "Grants the skill Axe Gyre" },
        new() { Id = "of_cinders", Name = "of Cinders", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic, ItemKind.Ring], Grants = "cinderfall", MinRarity = 2,
            Text = _ => "Grants the skill Cinderfall" },
        new() { Id = "of_dawn", Name = "of Dawn", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic, ItemKind.Ring], Grants = "dawnpulse", MinRarity = 2,
            Text = _ => "Grants the skill Dawnpulse" },
        new() { Id = "of_knives", Name = "of Knives", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic, ItemKind.Ring], Grants = "knifestorm", MinRarity = 2,
            Text = _ => "Grants the skill Knifestorm" },

        /* Kindled: gear that shapes the ember without owning it. Rare and up,
         * one to an item, two to a survivor (Inventory.MaxKindled). */
        new() { Id = "of_the_first_spark", Name = "of the First Spark", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic], Kindled = "spark", MinRarity = 2,
            Text = _ => "Kindled: the ember starts a level higher" },
        new() { Id = "of_second_thoughts", Name = "of Second Thoughts", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Head], Kindled = "reroll", MinRarity = 2,
            Text = _ => "Kindled: one more redraw in the ember's drafts" },
        new() { Id = "of_refusal", Name = "of Refusal", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Head], Kindled = "refusal", MinRarity = 2,
            Text = _ => "Kindled: one more banishing in the ember's drafts" },
        new() { Id = "of_many_roads", Name = "of Many Roads", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Cloak], Kindled = "roads", MinRarity = 2,
            Text = _ => "Kindled: the ember's drafts show a fourth card" },
        new() { Id = "of_omens", Name = "of Omens", Prefix = false, Slots = [ItemKind.Amulet, ItemKind.Relic], Kindled = "omens", MinRarity = 2,
            Text = _ => "Kindled: great blessings offer a fourth choice" },
        Stand("of_the_whetstone", "of the Whetstone", "serration"),
        Stand("of_rime", "of Rime", "chilling"),
        Stand("of_the_censer", "of the Censer", "searing"),
        Stand("of_the_wide_field", "of the Wide Field", "expanse"),
        Stand("of_the_true_eye", "of the True Eye", "precision"),
        Stand("of_the_root", "of the Root", "recovery"),
        Stand("of_the_ox", "of the Ox", "might"),
        Stand("of_the_evergreen", "of the Evergreen", "perennial"),
        Stand("of_the_adder", "of the Adder", "venom"),
        Stand("of_the_pack", "of the Pack", "kinship"),
        Stand("of_the_lodestone", "of the Lodestone", "conduit"),
        Stand("of_the_brand", "of the Brand", "emberblood"),

        new() { Id = "of_greed", Name = "of Greed", Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet],
            Mods = t => [M(Stat.GoldGain, ModKind.Inc, 0.1 + t * 0.08), M(Stat.PickupRadius, ModKind.Flat, 0.5 + t * 0.3)],
            Text = t => $"+{Pct(0.1 + t * 0.08)} gold, longer reach for pickups" },
    ];

    public static AffixDef? Affix(string id) => Array.Find(Affixes, a => a.Id == id);

    /// <summary>A catalyst suffix: the gear stands in for a passive in the ember's
    /// recipes, so a survivor who plans an evolution by day reaches it with a
    /// passive slot to spare (never without the rank-8 climb).</summary>
    static AffixDef Stand(string id, string name, string passive) => new()
    {
        Id = id, Name = name, Prefix = false, Slots = [ItemKind.Ring, ItemKind.Amulet, ItemKind.Cloak, ItemKind.Body], Kindled = $"stand:{passive}", MinRarity = 2,
        Text = _ => $"Kindled: counts as {Content.Boons.Find(passive)?.Name ?? passive} in the ember's evolutions",
    };

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
