using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Loot (docs/design/LOOT_DESIGN.md): tiers, item level and make, the drop roll, the
/// slotless stores, the filter, sets and the first Legendaries.</summary>
public class LootTests
{
    static CreationChoice Choice(string calling = "warden", string bg = "hunter")
    {
        var a = Callings.Archetype(calling);
        return new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = bg, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        };
    }

    static Journey Begin(string calling = "warden") => Journey.Begin(Choice(calling), 42);

    static Func<double> Seq(int seed) { var r = new Random(seed); return r.NextDouble; }

    static ItemInstance At(string def, int rarity, int level, uint seed = 7) => Inventory.Make(null, def, rarity: rarity, seed: seed, level: level);

    /* ------------------------------------------------------------ tiers -- */

    [Fact]
    public void Every_kind_of_thing_has_its_tier_and_its_store()
    {
        Assert.Equal(LootTier.Common, Drops.TierOf(At("iron_helm", 0, 1)));
        Assert.Equal(LootTier.Epic, Drops.TierOf(At("iron_helm", 3, 1)));
        Assert.Equal(LootTier.Set, Drops.TierOf(Items.Get("watch_coif"), 3));
        Assert.Equal(LootTier.Legendary, Drops.TierOf(Items.Get("drowned_coat"), 4));
        Assert.Equal(LootTier.Storied, Drops.TierOf(Items.Get("iron_helm"), 5));
        Assert.Equal(LootTier.Material, Drops.TierOf(Items.Get("wolf_pelt"), 0));
        Assert.Equal(LootTier.Book, Drops.TierOf(Items.Get("manual_sprint"), 1));
        Assert.Equal(LootTier.Draught, Drops.TierOf(Items.Get("health_draught"), 0));
        Assert.Equal(LootTier.Quest, Drops.TierOf(Items.Get("pell_ledger"), 2));
        Assert.Equal(LootTier.Chart, Drops.TierOf(Items.Get(Maps.Charts.Item), 0));

        // The pack holds gear only; everything else has a store that never fills.
        foreach (var d in Items.All.Values)
        {
            var store = Drops.StoreOf(d, null);
            if (Items.SlotFor(d) != null) Assert.Equal(Store.Pack, store);
            else Assert.NotEqual(Store.Pack, store);
        }
        Assert.Equal(Store.Pouch, Drops.StoreOf(Items.Get("greymuzzle_fang"), null));
        Assert.Equal(Store.Satchel, Drops.StoreOf(Items.Get("keepers_office"), null));
        Assert.Equal(Store.Satchel, Drops.StoreOf(Items.Get(SkillBook.Tome("arcweb")), null));
        Assert.Equal(Store.Keys, Drops.StoreOf(Items.Get("lockpicks"), null));
        Assert.Equal(Store.Keys, Drops.StoreOf(Items.Get("coyle_strongbox"), null));
        Assert.Equal(Store.Belt, Drops.StoreOf(Items.Get("antidote"), null));
    }

    /* ---------------------------------------------------- level and make -- */

    [Fact]
    public void A_pieces_level_sets_its_make_and_the_make_multiplies_its_base()
    {
        Assert.Equal(Make.Worn, Drops.MakeOf(1));
        Assert.Equal(Make.Worn, Drops.MakeOf(7));
        Assert.Equal(Make.Sound, Drops.MakeOf(8));
        Assert.Equal(Make.Wrought, Drops.MakeOf(16));
        Assert.Equal(Make.Legion, Drops.MakeOf(24));
        Assert.Equal(Make.Heartwrought, Drops.MakeOf(32));
        Assert.Equal(Make.Heartwrought, Drops.MakeOf(40));

        double Armour(ItemInstance it) => Inventory.Mods(it).Where(m => m.Stat == Stat.Armor).Sum(m => m.Value);
        double Speed(ItemInstance it) => Inventory.Mods(it).Where(m => m.Stat == Stat.MoveSpeed).Sum(m => m.Value);
        var worn = At("iron_helm", 0, 1);
        var wrought = At("iron_helm", 0, 18);
        Assert.Equal(3, Armour(worn), 6);
        Assert.Equal(3 * 2.8, Armour(wrought), 6);
        // A downside is never multiplied: the helm is as heavy at any make.
        Assert.Equal(Speed(worn), Speed(wrought), 6);
        // A weapon's make is increased damage.
        Assert.DoesNotContain(Inventory.Mods(At("worn_oathblade", 0, 1)), m => m.Stat == Stat.Damage);
        Assert.Contains(Inventory.Mods(At("worn_oathblade", 0, 33)), m => m.Stat == Stat.Damage && m.Kind == ModKind.Inc && Math.Abs(m.Value - 0.7) < 1e-9);
        // What has no level (a save from before) reads as Worn, as it always did.
        var old = At("iron_helm", 0, 1);
        old.Level = null;
        Assert.Equal(Armour(worn), Armour(old), 6);
    }

    [Fact]
    public void A_late_common_beats_an_early_rare_and_the_latest_beats_an_early_epic()
    {
        // The owner: "common items in higher zones can be better than greens or even blues (or way later
        // commons even better than early purples)". Measured on every helm, body and cloak base, against
        // the average early roll (many seeds), with the power score.
        double Mean(string def, int rarity, int level) => Enumerable.Range(1, 200).Average(s => Drops.Power(At(def, rarity, level, (uint)(s * 7919))));
        foreach (var def in new[] { "iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "travelers_cloak" })
        {
            Assert.True(Mean(def, 0, 10) > Mean(def, 1, 3), $"{def}: a Sound Common beats a Worn Uncommon: {Mean(def, 0, 10):0.0} {Mean(def, 1, 3):0.0}");
            Assert.True(Mean(def, 0, 18) > Mean(def, 2, 3), $"{def}: a Wrought Common beats a Worn Rare: {Mean(def, 0, 18):0.0} {Mean(def, 2, 3):0.0}");
            Assert.True(Mean(def, 0, 34) > Mean(def, 3, 3), $"{def}: a Heartwrought Common beats a Worn Epic: {Mean(def, 0, 34):0.0} {Mean(def, 3, 3):0.0}");
        }
    }

    [Fact]
    public void Grades_are_as_they_were_below_level_25_and_rise_past_it()
    {
        double MeanGrade(int rarity, int level) => Enumerable.Range(1, 300)
            .SelectMany(s => At("copper_ring", rarity, level, (uint)(s * 104729)).Affixes).Where(a => Items.Affix(a.Id)?.Kindled == null && Items.Affix(a.Id)?.Grants == null)
            .Average(a => a.Tier);
        // Below 25 the rarity's two grades (Rare II-III: tiers 1 and 2).
        foreach (var s in Enumerable.Range(1, 100))
            Assert.All(At("copper_ring", 2, 12, (uint)s).Affixes, a => Assert.InRange(a.Tier, 1, 2));
        Assert.InRange(MeanGrade(2, 30) - MeanGrade(2, 20), 0.8, 1.4);
        Assert.All(Enumerable.Range(1, 100).SelectMany(s => At("copper_ring", 3, 40, (uint)s).Affixes), a => Assert.InRange(a.Tier, 4, 5));
    }

    /* ----------------------------------------------------------- drops -- */

    [Fact]
    public void Commons_thin_out_with_level_and_legendaries_stay_extremely_rare()
    {
        double Share(int level, int tier) { var w = Drops.Weights(level); return w[tier] / w.Sum(); }
        Assert.True(Share(1, 0) > Share(16, 0) && Share(16, 0) > Share(40, 0));
        Assert.InRange(Share(1, 0), 0.35, 0.45);
        Assert.InRange(Share(40, 0), 0.01, 0.05);
        Assert.InRange(Share(1, 5), 0.002, 0.008);
        Assert.True(Share(40, 3) > Share(1, 3), "Epic comes oftener the deeper");
    }

    [Fact]
    public void A_boss_hoard_starts_at_rare_and_a_miniboss_at_uncommon()
    {
        var j = Begin();
        for (int s = 0; s < 200; s++)
        {
            var boss = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 5, People = "pack", R = Seq(s) });
            Assert.True(boss[0].Item != null && (int)boss[0].Tier >= (int)LootTier.Rare, $"seed {s}: {boss[0].Tier}");
            var mb = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Miniboss, Level = 5, People = "pack", R = Seq(1000 + s) });
            Assert.True(mb[0].Item != null && mb[0].Tier != LootTier.Common);
        }
    }

    [Fact]
    public void A_champion_that_drops_no_gear_now_and_then_drops_its_peoples_material_or_iron()
    {
        var j = Begin();
        int gear = 0, none = 0, dust = 0, iron = 0, n = 4000;
        for (int s = 0; s < n; s++)
        {
            var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = 6, People = "dead", R = Seq(s) });
            if (d.Any(x => x.Item != null)) { gear++; continue; }
            none++;
            if (d.Any(x => x.Material == "bone_dust")) dust++;
            if (d.Any(x => x.Material == Drops.Iron)) iron++;
        }
        // Crafting's measured rates: a tenth the people's material, a fifth old iron.
        Assert.InRange(gear / (double)n, 0.40, 0.50);
        Assert.InRange(dust / (double)none, 0.07, 0.13);
        Assert.InRange(iron / (double)none, 0.16, 0.24);
    }

    [Fact]
    public void In_a_nights_arena_the_materials_wait_for_the_nights_end_and_a_fall_spills_half()
    {
        var j = Begin();
        int pickups = 0;
        for (int s = 0; s < 300; s++)
            pickups += j.Drops(new DropCtx { Source = DropSource.Champion, Level = 4, People = "pack", Tally = true, R = Seq(s) }).Count(l => l.Kind == PickupKind.Material);
        Assert.Equal(0, pickups);
        int tallied = j.NightTally.Values.Sum();
        Assert.True(tallied > 20);
        // In a map they are the ground's.
        int ground = Enumerable.Range(0, 300).Sum(s => j.Drops(new DropCtx { Source = DropSource.MapPack, Level = 10, People = "pack", R = Seq(s) }).Count(l => l.Kind == PickupKind.Material));
        Assert.True(ground > 20);
    }

    [Fact]
    public void Gear_falls_whole_at_the_carriers_level()
    {
        var j = Begin();
        var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 19, People = "kerchiefs", R = Seq(3) });
        foreach (var g in d.Where(x => x.Item != null))
        {
            Assert.Equal(19, g.Item!.Level);
            Assert.Equal(Make.Wrought, Drops.MakeOf(g.Item));
            if (Items.Get(g.Item.Def).Base) Assert.Equal(Crafting.Seams(g.Item), g.Item.Affixes.Count);
        }
    }

    [Fact]
    public void The_first_story_boss_beaten_pays_a_legendary_and_the_calling_leans_it()
    {
        foreach (var calling in new[] { "warden", "reaver", "arcanist", "stalker" })
        {
            var j = Begin(calling);
            Assert.False(j.World.FirstLegendary);
            var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 3, People = "pack", StoryBoss = true, R = Seq(5) });
            Assert.Equal(LootTier.Legendary, d[0].Tier);
            Assert.Contains(d[0].Item!.Def, Drops.EarlyLegendaries().Select(x => x.Id));
            Assert.True(j.World.FirstLegendary);
            // Paid once: the next story boss rolls as any boss does.
            int legend = Enumerable.Range(0, 50).Count(s =>
                Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 3, People = "pack", StoryBoss = true, R = Seq(100 + s) })[0].Tier == LootTier.Legendary);
            Assert.True(legend < 10);
        }
    }

    [Fact]
    public void The_darks_debt_pays_a_legendary_at_a_boss_and_clears()
    {
        var j = Begin();
        j.World.FirstLegendary = true;
        j.World.LootDebt = Drops.Rules.Debt;
        // A champion does not pay it: only a hoard.
        var c = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Miniboss, Level = 3, People = "pack", R = Seq(1) });
        Assert.True(j.World.LootDebt > Drops.Rules.Debt || c[0].Tier == LootTier.Legendary);
        var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 3, People = "pack", R = Seq(2) });
        Assert.Equal(LootTier.Legendary, d[0].Tier);
        Assert.True(j.World.LootDebt <= 2);
    }

    [Fact]
    public void A_legendary_falls_only_from_its_least_level_and_while_its_story_holds()
    {
        var x = new DropCtx { Level = 1, Allows = _ => false };
        var early = Drops.Legendaries(x).Select(d => d.Id).ToList();
        Assert.Contains("drowned_coat", early);
        Assert.DoesNotContain("kells_lamp", early);
        Assert.DoesNotContain("pelt_of_the_pack", Drops.Legendaries(new DropCtx { Level = 30, Allows = _ => false }).Select(d => d.Id));
        Assert.Contains("pelt_of_the_pack", Drops.Legendaries(new DropCtx { Level = 30, Allows = _ => true }).Select(d => d.Id));
        // The story's own, given and never rolled.
        Assert.DoesNotContain("moonsilver_circlet", Drops.Legendaries(new DropCtx { Level = 40, Allows = _ => true }).Select(d => d.Id));
    }

    [Fact]
    public void Act_one_pays_three_to_five_legendaries_on_average_and_a_handful_of_set_pieces()
    {
        // Act 1 as the design counts it (§5.3): about 18 nights of a dozen carriers and a boss, and ten
        // days of a few elites, at levels rising 1 to 12.
        double legends = 0, sets = 0, epics = 0, gear = 0;
        const int runs = 40;
        for (int run = 0; run < runs; run++)
        {
            var j = Begin(new[] { "warden", "reaver", "arcanist", "stalker" }[run % 4]);
            var R = Seq(run * 31 + 7);
            void Count(List<Dropped> d) { foreach (var x in d.Where(x => x.Item != null)) { gear++; if (x.Tier == LootTier.Legendary) legends++; if (x.Tier == LootTier.Set) sets++; if (x.Tier == LootTier.Epic) epics++; } }
            string[] peoples = ["pack", "dead", "lamplings", "kerchiefs"];
            for (int night = 0; night < 18; night++)
            {
                int level = 1 + night * 11 / 17;
                string people = peoples[night % 4];
                for (int k = 0; k < 12; k++) Count(Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Champion, Level = level + 2, People = people, R = R }));
                for (int k = 0; k < 3; k++) Count(Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Miniboss, Level = level + 3, People = people, R = R }));
                Count(Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = level + 4, People = people, StoryBoss = night % 3 == 0, R = R }));
            }
            for (int day = 0; day < 10; day++)
                for (int k = 0; k < 4; k++) Count(Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Elite, Level = 1 + day, People = peoples[k], R = R }));
        }
        Assert.InRange(gear / runs, 150, 260);
        Assert.InRange(legends / runs, 2.5, 5.5);
        Assert.InRange(sets / runs, 1.5, 5);
        Assert.InRange(epics / runs, 8, 25);
    }

    /* ---------------------------------------------------------- stores -- */

    [Fact]
    public void Things_that_should_stack_stack_and_nothing_but_gear_takes_a_place()
    {
        var j = Begin();
        var ch = j.Ch;
        int free = Inventory.Free(ch);
        Assert.True(j.GiveItem("manual_sprint"));
        Assert.True(j.GiveItem("manual_sprint"));
        Assert.True(j.GiveItem("lockpicks"));
        Assert.True(j.GiveItem("antidote", 3));
        Assert.True(j.GiveItem("wolf_pelt", 4));
        Assert.True(j.GiveItem("greymuzzle_fang"));
        Assert.True(j.GiveChart(new Maps.Chart { Tier = 2, People = "dead", Seed = 3, Name = "A" }));
        Assert.True(j.GiveChart(new Maps.Chart { Tier = 3, People = "dead", Seed = 4, Name = "B" }));
        Assert.Equal(free, Inventory.Free(ch));
        // Two manuals are one stack; two charts are two entries.
        Assert.Single(ch.Satchel, i => i.Def == "manual_sprint" && i.Qty == 2);
        Assert.Equal(2, ch.Satchel.Count(i => i.Chart != null));
        Assert.Equal(3, ch.Belt["antidote"]);
        Assert.Equal(4, ch.Materials["wolf_pelt"]);
        Assert.Equal(1, ch.Materials["greymuzzle_fang"]);
        Assert.Contains(ch.Keys, i => i.Def == "lockpicks");
        // Counted, taken and found wherever they are.
        Assert.Equal(2, Inventory.Count(ch, "manual_sprint"));
        Assert.Equal(1, Inventory.Take(ch, "manual_sprint"));
        Assert.Equal(1, Inventory.Count(ch, "manual_sprint"));
        Assert.Equal(Store.Belt, Inventory.Find(ch, "b:antidote")!.Store);
        Assert.True(Inventory.Holds(ch, ch.Keys[0].Uid));
        // A tool on the key ring still speaks to the world.
        Assert.Contains("lockpick", Inventory.WorldTags(ch));
        // The belt has a carry limit, not places.
        Assert.False(j.GiveItem("antidote", Drops.Rules.Belt));
        Assert.Equal(Drops.Rules.Belt, ch.Belt["antidote"]);
    }

    [Fact]
    public void A_book_is_read_from_the_satchel_and_a_draught_drunk_from_the_belt()
    {
        var j = Begin();
        Assert.True(j.GiveItem("manual_sprint"));
        var book = j.Ch.Satchel.First(i => i.Def == "manual_sprint");
        j.Use(book.Uid, null);
        Assert.True(ArtBook.Knows(j.Ch, "sprint"));
        Assert.DoesNotContain(j.Ch.Satchel, i => i.Def == "manual_sprint");
        int had = Inventory.Count(j.Ch, "health_draught");
        Assert.True(had > 0);
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        b.Player.Hp = b.MaxHp * 0.5;
        j.Quaff(b);
        Assert.Equal(had - 1, Inventory.Count(j.Ch, "health_draught"));
        // Sold from wherever it is: a lockpick off the key ring.
        Assert.True(j.GiveItem("lockpicks"));
        j.Drop(j.Ch.Keys.First(i => i.Def == "lockpicks").Uid);
        Assert.DoesNotContain(j.Ch.Keys, i => i.Def == "lockpicks");
    }

    static string Fixture(string name)
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
            if (File.Exists(Path.Combine(d.FullName, "saves", name))) return Path.Combine(d.FullName, "saves", name);
            else if (File.Exists(Path.Combine(d.FullName, "tests", "saves", name))) return Path.Combine(d.FullName, "tests", "saves", name);
        throw new FileNotFoundException(name);
    }

    [Fact]
    public void A_real_save_from_before_the_stores_moves_its_things_out_of_the_pack()
    {
        // Written by the game (version 3), mid-Act 1: draughts, a ring, Greymuzzle's fang and a tome in the pack.
        var d = Saves.Migrate(Json.Parse<SaveData>(File.ReadAllText(Fixture("before_stores_v3.json"))));
        var ch = d.Character;
        Assert.Equal(Saves.Version, d.Version);
        Assert.Equal(new[] { "copper_ring" }, ch.Pack.Where(p => p != null).Select(p => p!.Def).ToArray());
        Assert.Equal(3, ch.Belt["health_draught"]);
        Assert.Equal(1, ch.Materials["greymuzzle_fang"]);
        Assert.Equal(3, ch.Materials["ember_shard"]);
        Assert.Contains(ch.Satchel, i => i.Def == "tome_arcweb");
        // Its things read as they did: no level is Worn.
        Assert.Null(ch.Pack.First(p => p != null)!.Level);
        Assert.Equal(Make.Worn, Drops.MakeOf(ch.Pack.First(p => p != null)!));
        // The journey picks it up, and the draught key still finds its draughts.
        var j = Journey.From(d, 0);
        Assert.Equal(3, j.Draughts);
        Assert.NotNull(Character.Kit(j.Ch));
        // A second migration changes nothing.
        var again = Saves.Migrate(Json.Parse<SaveData>(Json.Write(d)));
        Assert.Equal(Json.Write(d.Character), Json.Write(again.Character));
    }

    /* ---------------------------------------------------------- filter -- */

    [Fact]
    public void The_default_filter_hides_plain_commons_but_never_a_jackpot_an_upgrade_or_a_first_sighting()
    {
        var j = Begin();
        var f = new LootFilter();
        var ch = j.Ch;
        ch.Equipment.Head = At("iron_helm", 2, 5);
        Assert.Equal(Verdict.Hidden, f.Judge(At("iron_helm", 0, 5), ch));
        Assert.Equal(Verdict.Shown, f.Judge(At("iron_helm", 0, 5), ch, firstSighting: true));
        Assert.Equal(Verdict.Shown, f.Judge(At("iron_helm", 1, 5), ch));
        Assert.Equal(Verdict.Emphasised, f.Judge(At("iron_helm", 3, 5), ch));
        Assert.Equal(Verdict.Emphasised, f.Judge(Inventory.Make(null, "drowned_coat", level: 2), ch));
        Assert.Equal(Verdict.Emphasised, f.Judge(Inventory.Make(null, "watch_coif", level: 2), ch));
        // A late common of a better make shows, and if it is better than what is worn, it says so.
        var late = At("iron_helm", 0, 34);
        Assert.True(Drops.IsUpgrade(ch, late));
        Assert.Equal(Verdict.Emphasised, f.Judge(late, ch));
        // Only the best hides even rares; a rule read first can show what the preset hides.
        f.Preset = FilterPreset.Best;
        f.Upgrades = false;
        var fire = new ItemInstance { Uid = "x", Def = "copper_ring", Rarity = 2, Level = 5, Affixes = [new AffixRoll { Id = "searing", Tier = 2 }] };
        Assert.Equal(Verdict.Hidden, f.Judge(fire, ch));
        f.Rules.Add(new FilterRule { Action = FilterAction.Emphasise, Affixes = ["searing"], MinGrade = 2 });
        Assert.Equal(Verdict.Emphasised, f.Judge(fire, ch));
        // Nothing hides a Legendary.
        f.Rules.Insert(0, new FilterRule { Action = FilterAction.Hide });
        Assert.Equal(Verdict.Emphasised, f.Judge(Inventory.Make(null, "drowned_coat", level: 2), ch));
        // Its landing is heard from Rare up, by default; the jackpots always.
        var g = new LootFilter();
        Assert.False(g.Heard(LootTier.Uncommon));
        Assert.True(g.Heard(LootTier.Rare));
        g.SoundsFrom = LootTier.Legendary;
        Assert.False(g.Heard(LootTier.Epic));
        Assert.True(g.Heard(LootTier.Set));
    }

    [Fact]
    public void What_the_filter_hides_is_not_taken_underfoot_and_a_fights_end_gathers_the_rest()
    {
        var j = Begin();
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        var shown = At("iron_helm", 2, 5);
        var hidden = At("leather_cap", 0, 5);
        var p1 = b.Spill(new Sim.Loot(PickupKind.Item, shown.Def, 1, true, shown.Rarity, null, shown, (int)LootTier.Rare, Verdict.Shown), 30, 30)!;
        var p2 = b.Spill(new Sim.Loot(PickupKind.Item, hidden.Def, 1, true, hidden.Rarity, null, hidden, (int)LootTier.Common, Verdict.Hidden), b.Player.X, b.Player.Z)!;
        Assert.Equal(Verdict.Hidden, p2.Look);
        for (int i = 0; i < 60; i++) b.Tick(1 / 30.0, 0, 0);
        Assert.True(p2.Alive, "hidden things are not taken by walking over them");
        double iron = Inventory.Count(j.Ch, Crafting.Iron);
        var g = j.Gather(b);
        Assert.Equal(1, g.Home);
        Assert.Equal(1, g.Broken);
        Assert.Contains(j.Ch.Pack, p => p?.Uid == shown.Uid);
        Assert.True(Inventory.Count(j.Ch, Crafting.Iron) > iron);
        Assert.False(p1.Alive);
    }

    [Fact]
    public void The_first_legendary_taken_is_told_once_with_where_it_lay()
    {
        var j = Begin();
        var told = new List<(string Def, double X, double Z)>();
        j.FirstLegendaryTaken = (it, x, z) => told.Add((it.Def, x, z));
        Assert.True(j.PickedUp(new Pickup(0) { Kind = PickupKind.Item, Ref = "iron_helm", Value = 1, X = 1, Z = 2, Payload = At("iron_helm", 3, 4) }));
        Assert.Empty(told);
        Assert.True(j.PickedUp(new Pickup(1) { Kind = PickupKind.Item, Ref = "drowned_coat", Value = 1, X = 3, Z = 4, Payload = Inventory.Make(null, "drowned_coat", level: 2) }));
        Assert.True(j.PickedUp(new Pickup(2) { Kind = PickupKind.Item, Ref = "kells_lamp", Value = 1, X = 5, Z = 6, Payload = Inventory.Make(null, "kells_lamp", level: 9) }));
        Assert.Equal(new[] { ("drowned_coat", 3.0, 4.0) }, told);
        Assert.True(j.World.FirstLegendaryTaken);
    }

    [Fact]
    public void Gear_rolled_where_it_fell_is_taken_whole()
    {
        var j = Begin();
        var it = At("chain_shirt", 3, 17);
        Assert.True(j.PickedUp(new Pickup(0) { Kind = PickupKind.Item, Ref = it.Def, Value = 1, Payload = it }));
        var got = j.Ch.Pack.First(p => p?.Def == "chain_shirt")!;
        Assert.Equal(17, got.Level);
        Assert.Equal(it.Affixes.Select(a => a.Id), got.Affixes.Select(a => a.Id));
    }

    /* ---------------------------------------------- sets and legendaries -- */

    [Fact]
    public void A_set_worn_far_enough_gives_its_bonuses()
    {
        var j = Begin();
        var ch = j.Ch;
        double armour = Character.Kit(ch).Stats.Get(Stat.Armor);
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, "watch_coif", level: 3), EquipSlot.Head));
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, "watch_hauberk", level: 3), EquipSlot.Body));
        Assert.Equal(2, Drops.SetsWorn(ch)["watch_kit"]);
        Assert.Single(Drops.SetBonuses(ch));
        double two = Character.Kit(ch).Stats.Get(Stat.Armor);
        Assert.True(two > armour);
        Assert.DoesNotContain("watch_kit", Inventory.WorldTags(ch));
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, "watch_shield", level: 3), EquipSlot.Offhand));
        Assert.Equal(2, Drops.SetBonuses(ch).Count());
        Assert.Contains("watch_kit", Inventory.WorldTags(ch));
        // The red: its third piece's rule is in the kit.
        var red = Begin("stalker").Ch;
        foreach (var (id, slot) in new[] { ("roost_hood", EquipSlot.Head), ("levy_colours", EquipSlot.Cloak), ("kerchief_knives", EquipSlot.Weapon) })
            Assert.True(Inventory.Equip(red, Inventory.Make(red, id, level: 6), slot));
        var kit = Character.Kit(red);
        Assert.Contains(kit.Triggers, t => t.Source.StartsWith("set:levy_red"));
        Assert.Contains("kerchief_colors", Inventory.WorldTags(red));
    }

    [Fact]
    public void Every_legendary_changes_how_you_play_has_a_home_and_a_line_and_is_never_worked()
    {
        var legends = Items.All.Values.Where(d => d.Rarity == 4 && Items.SlotFor(d) != null).ToList();
        Assert.True(legends.Count >= 8);
        Assert.True(Drops.EarlyLegendaries().Count() >= 4, "some reachable at the first levels");
        foreach (var d in legends)
        {
            // A rule, or a number that only holds while you play a certain way.
            Assert.True((d.Triggers?.Count ?? 0) > 0 || d.Mods?.Any(m => m.When != null) == true, $"{d.Id} only adds numbers");
            Assert.False(string.IsNullOrWhiteSpace(d.Lore), $"{d.Id} has no lore");
            Assert.False(Crafting.Workable(d), $"{d.Id} is somebody's work");
            if (d.Of != null) Assert.Equal(Items.Get(d.Of).Kind, d.Kind);
            if (d.Id != "moonsilver_circlet") Assert.NotNull(d.DropsFrom);
            Assert.All(d.Homes ?? new(), h => Assert.Contains(h, new[] { "pack", "dead", "lamplings", "kerchiefs" }));
            // No item grants a rise from death (the owner's rule for story fights and maps).
            Assert.DoesNotContain("revive", d.Tags ?? new());
        }
        foreach (var set in Drops.Rules.Sets.Values)
        {
            Assert.All(set.Pieces, p => Assert.Equal(set.Id, Items.Get(p).Set));
            Assert.All(set.Pieces, p => Assert.False(Crafting.Workable(Items.Get(p))));
        }
    }

    [Fact]
    public void A_deep_copys_flat_rules_grow_with_its_make_and_armour_grows_slower_at_the_top()
    {
        // Kell's Lamp by day was a flat 14 at any depth (combat): its make scales it as its base's numbers.
        double Flare(int level) => Drops.Triggers(Items.Get("kells_lamp"), level).SelectMany(t => t.Effects).OfType<Effect.Nova>().Single().Damage;
        Assert.Equal(14, Flare(1), 6);
        Assert.Equal(14 * 5.5, Flare(34), 6);
        // A rule that reads the blow already grows with it.
        Assert.Equal(0.5, Drops.Triggers(Items.Get("corrans_sword"), 34).SelectMany(t => t.Effects).OfType<Effect.Nova>().Single().Damage, 6);
        // Armour saturates, so its curve tops out lower than health's.
        Assert.True(Drops.Mult(Make.Heartwrought, Stat.Armor) < Drops.Mult(Make.Heartwrought, Stat.MaxHealth));
        // Nan's Cleaver's price is paid above four fifths of her health, not only at full (combat).
        Assert.Contains(Items.Get("nans_cleaver").Mods!, m => m.When == ModWhen.Healthy && m.Value < 0);
    }

    [Fact]
    public void The_drowned_coats_dash_leaves_black_water_that_slows()
    {
        var j = Begin();
        Assert.True(Inventory.Equip(j.Ch, Inventory.Make(j.Ch, "drowned_coat", level: 2), EquipSlot.Body));
        var kit = Character.Kit(j.Ch);
        Assert.Contains(kit.Triggers, t => t.Def.On == TriggerEvent.Dash && t.Def.Effects.Any(e => e is Effect.Zone z && z.Slow >= 0.4));
        // Built on a padded jerkin: its make is the jerkin's, so a later copy is a better one.
        double Health(ItemInstance it) => Inventory.Mods(it).Where(m => m.Stat == Stat.MaxHealth).Sum(m => m.Value);
        Assert.True(Health(Inventory.Make(null, "drowned_coat", level: 30)) > Health(Inventory.Make(null, "drowned_coat", level: 2)));
    }
}
