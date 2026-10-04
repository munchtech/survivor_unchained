using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Crafting (docs/CRAFTING_DESIGN.md): the pouch, heat, Brannoc's forge, the night's
/// yield, and the save that carries them.</summary>
public class CraftingTests
{
    static Journey Make(string calling = "warden")
    {
        var a = Callings.Archetype(calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        // Brannoc is met, by day, and the purse is full enough that only the materials decide.
        j.World.Npc("brannoc").Flags["met"] = true;
        j.World.Time = TimeOfDay.Day;
        j.Ch.Gold = 5000;
        return j;
    }

    static ItemInstance Piece(Journey j, string def, int rarity, params (string Id, int Tier)[] affixes)
    {
        var it = Inventory.Make(j.Ch, def, rarity: rarity, affixes: affixes.Select(a => new AffixRoll { Id = a.Id, Tier = a.Tier }).ToList());
        Assert.True(Inventory.AddToPack(j.Ch, it));
        return it;
    }

    static void Give(Journey j, string m, int n) => Inventory.AddToPack(j.Ch, Inventory.Make(j.Ch, m, n));

    static readonly Rng Roll = new(7);

    [Fact]
    public void Every_affix_id_is_its_own()
    {
        // Two affixes with one id: the second could never be read back (the Bitterroot and
        // Emberblood stand-ins were lost that way).
        var dup = Items.Affixes.GroupBy(a => a.Id).Where(g => g.Count() > 1).Select(g => g.Key).ToList();
        Assert.Empty(dup);
        Assert.Equal("stand:recovery", Items.Affix("of_the_root")!.Kindled);
        Assert.Equal("stand:emberblood", Items.Affix("of_the_brand")!.Kindled);
    }

    [Fact]
    public void Every_material_works_into_affixes_that_exist_and_every_crafter_is_whole()
    {
        foreach (var (m, r) in Crafting.Rules.Materials)
        {
            Assert.Equal(ItemKind.Material, Items.Get(m).Kind);
            Assert.NotEmpty(r.Into);
            foreach (var a in r.Into) Assert.NotNull(Items.Affix(a));
            Assert.NotNull(Crafting.Crafter(r.Crafter));
        }
        Assert.Equal(ItemKind.Material, Items.Get(Crafting.Iron).Kind);
        Assert.Equal(6, Crafting.Rules.Heat.Count);
        Assert.Equal(3, Crafting.Rules.Temper.Count);
        Assert.Equal(Crafting.Rules.RemakeCap, Crafting.Rules.Remake.Count);
        foreach (var (people, list) in Crafting.Rules.Night.Peoples)
        {
            Assert.Contains(Maps.MapOffers.Peoples, p => p.Id == people);
            foreach (var y in list) Assert.True(EnumKey<Family>.TryParse(y.Family, out _), y.Family);
        }
    }

    [Fact]
    public void Materials_go_in_the_pouch_and_the_story_still_reads_and_takes_them()
    {
        var j = Make();
        int free = Inventory.Free(j.Ch);
        j.GiveItem("wolf_pelt", 4);
        Assert.Equal(free, Inventory.Free(j.Ch));
        Assert.Equal(4, j.Ch.Materials["wolf_pelt"]);
        // The story's own words for it: hasItem, take, give.
        Assert.True(Rules.Test(new Cond { HasItem = "wolf_pelt", Qty = 4 }, j.Ctx));
        Rules.Apply([new Change { Take = "wolf_pelt", Qty = 3 }, new Change { Give = "bone_dust", Qty = 2 }], j.Ctx);
        Assert.Equal(1, Inventory.Count(j.Ch, "wolf_pelt"));
        Assert.Equal(2, j.Ch.Materials["bone_dust"]);
        Assert.Contains(Inventory.Pouch(j.Ch), p => p.Def == "bone_dust" && p.Qty == 2);
        // A shop that buys materials buys the whole stack from the pouch.
        j.OpenShop("brannoc", new Random(1));
        var uid = Inventory.PouchUid("bone_dust");
        int price = j.PriceOf("brannoc", uid, buying: false)!.Value;
        double gold = j.Ch.Gold;
        j.Sell("brannoc", uid);
        Assert.Equal(gold + price, j.Ch.Gold);
        Assert.Equal(0, Inventory.Count(j.Ch, "bone_dust"));
    }

    [Fact]
    public void A_piece_has_heat_by_its_rarity_rolled_where_it_fell()
    {
        var j = Make();
        Assert.Equal(6, j.Ch.Equipment.Weapon!.Heat);
        Assert.Equal(new[] { 6, 10, 14, 18, 22, 22 }, Crafting.Rules.Heat);
        var seen = new HashSet<int>();
        for (int i = 0; i < 200; i++)
        {
            var it = Inventory.Make(j.Ch, "iron_helm", rarity: 2, dropped: true, seed: (uint)(i + 1));
            Assert.InRange(it.Heat!.Value, 11, 17);
            Assert.Equal(it.Heat, it.HeatFull);
            seen.Add(it.Heat.Value);
        }
        Assert.True(seen.Count >= 4);
        // Made or bought, full; materials and named pieces have none.
        Assert.Equal(14, Inventory.Make(j.Ch, "iron_helm", rarity: 2).Heat);
        Assert.Null(Inventory.Make(j.Ch, "wolf_pelt").Heat);
        Assert.Null(Inventory.Make(j.Ch, "wolf_fang_necklace").Heat);
        Assert.Equal(14, Inventory.Make(j.Ch, "wolfhide_cloak").Heat);
    }

    [Fact]
    public void Tempering_raises_a_grade_to_the_cap_for_iron_gold_and_heat()
    {
        var j = Make();
        var it = Piece(j, "iron_helm", 2, ("hale", 0));
        var q = Crafting.Temper(j.Craft, it, 0);
        Assert.False(q.Ok);
        Assert.Contains("old iron", q.Blocked);
        Give(j, Crafting.Iron, 20);
        q = Crafting.Temper(j.Craft, it, 0);
        Assert.True(q.Ok, q.Blocked);
        Assert.Equal(2, q.Takes[Crafting.Iron]);
        Assert.Equal((2, 4), (q.HeatLo, q.HeatHi));
        Assert.Equal("+10 maximum health", q.Before);
        Assert.Equal("+18 maximum health", q.After);
        double gold = j.Ch.Gold;
        Assert.True(j.Work(it.Uid, q, null));
        Assert.Equal(1, it.Affixes[0].Tier);
        Assert.Equal(18, Inventory.Count(j.Ch, Crafting.Iron));
        Assert.True(gold > j.Ch.Gold);
        Assert.InRange(it.Heat!.Value, 14 - 4, 14 - 2);
        // To III: as high as a rare piece goes.
        Assert.True(j.Work(it.Uid, Crafting.Temper(j.Craft, it, 0), null));
        var last = Crafting.Temper(j.Craft, it, 0);
        Assert.False(last.Ok);
        Assert.Contains("as high as", last.Blocked);
    }

    [Fact]
    public void Working_in_a_material_fills_a_seam_or_takes_a_place_and_a_pelt_marks_it()
    {
        var j = Make();
        Give(j, "wolf_pelt", 6);
        // A cloak with an open seam (uncommon, no affix yet).
        var cloak = Piece(j, "travelers_cloak", 1);
        Assert.Equal(1, Crafting.OpenSeams(cloak));
        Assert.Contains(("wolf_pelt", "of_the_wolf"), Crafting.WorkInChoices(cloak));
        Assert.DoesNotContain(("wolf_pelt", "wolfbane"), Crafting.WorkInChoices(cloak));
        var q = Crafting.WorkIn(j.Craft, cloak, "wolf_pelt", "of_the_wolf");
        Assert.True(q.Ok, q.Blocked);
        Assert.True(j.Work(cloak.Uid, q, null));
        Assert.Equal("of_the_wolf", cloak.Affixes[0].Id);
        Assert.Equal(0, cloak.Affixes[0].Tier);
        Assert.Equal(3, Inventory.Count(j.Ch, "wolf_pelt"));
        // Worn, the wolves smell it.
        Assert.DoesNotContain("wolf_pelts", Inventory.WorldTags(j.Ch));
        j.Equip(cloak.Uid, EquipSlot.Cloak, null);
        Assert.Contains("wolf_pelts", Inventory.WorldTags(j.Ch));
        // No open seam: it goes over a chosen place, which is lost.
        var full = Piece(j, "travelers_cloak", 1, ("fleet", 1));
        Give(j, "boar_hide", 3);
        Assert.False(Crafting.WorkIn(j.Craft, full, "boar_hide", "sturdy").Ok);
        q = Crafting.WorkIn(j.Craft, full, "boar_hide", "sturdy", replace: 0);
        Assert.True(q.Ok, q.Blocked);
        Assert.True(j.Work(full.Uid, q, null));
        Assert.Equal(new[] { "sturdy" }, full.Affixes.Select(a => a.Id));
        // On an epic piece it enters a grade higher.
        var epic = Piece(j, "bone_amulet", 3, ("keen", 2), ("of_reach", 2));
        Give(j, "bone_dust", 3);
        q = Crafting.WorkIn(j.Craft, epic, "bone_dust", "of_the_grave");
        Assert.True(j.Work(epic.Uid, q, null));
        Assert.Equal(1, epic.Affixes.Single(a => a.Id == "of_the_grave").Tier);
    }

    [Fact]
    public void A_coal_is_one_of_three_that_fit_and_lean_to_the_skills_carried()
    {
        var j = Make();
        var ring = Piece(j, "silver_ring", 2, ("keen", 1));
        Give(j, Crafting.Shard, 20);
        var coals = Crafting.Coals(j.Ch, ring, j.World.Day);
        Assert.Equal(3, coals.Count);
        Assert.Equal(3, coals.Distinct().Count());
        Assert.All(coals, id => Assert.Contains(ItemKind.Ring, Items.Affix(id)!.Slots));
        Assert.All(coals, id => Assert.NotNull(Items.Affix(id)!.Kindled));
        // The same three until a shard draws three more, or a day passes.
        Assert.Equal(coals, Crafting.Coals(j.Ch, ring, j.World.Day));
        Assert.True(j.Work(ring.Uid, Crafting.Redraw(j.Craft, ring), null));
        Assert.Equal(19, Inventory.Count(j.Ch, Crafting.Shard));
        var before = coals;
        coals = Crafting.Coals(j.Ch, ring, j.World.Day);
        Assert.NotEqual(before, coals);
        // Only a coal on offer can be caged.
        Assert.False(Crafting.Cage(j.Craft, ring, Items.Affixes.First(a => a.Kindled != null && a.Slots.Contains(ItemKind.Ring) && !coals.Contains(a.Id)).Id).Ok);
        // Caged in the open seam; a second coal takes the first one's place.
        var q = Crafting.Cage(j.Craft, ring, coals[0]);
        Assert.True(q.Ok, q.Blocked);
        Assert.True(j.Work(ring.Uid, q, null));
        Assert.Contains(ring.Affixes, a => a.Id == coals[0]);
        Assert.Contains(ring.History!, h => h.Contains("coal"));
        var next = Crafting.Coals(j.Ch, ring, j.World.Day).First();
        Assert.True(j.Work(ring.Uid, Crafting.Cage(j.Craft, ring, next), null));
        Assert.Single(ring.Affixes, a => Items.Affix(a.Id)?.Kindled != null);
        Assert.Contains(ring.Affixes, a => a.Id == "keen");
        // Plain pieces hold no coal.
        var plain = Piece(j, "copper_ring", 1);
        Assert.False(Crafting.Cage(j.Craft, plain, Crafting.Coals(j.Ch, plain, 1).FirstOrDefault() ?? "of_refusal").Ok);
    }

    [Fact]
    public void Coals_for_what_the_weapon_evolves_with_come_twice_as_often()
    {
        var j = Make();
        var wanted = Crafting.Wanted(j.Ch);
        Assert.NotEmpty(wanted);
        var ring = Piece(j, "silver_ring", 2);
        int hits = 0, n = 400;
        for (int d = 1; d <= n; d++) hits += Crafting.Coals(j.Ch, ring, d).Count(id => wanted.Contains(Items.Affix(id)!.Kindled!));
        var pool = Items.Affixes.Where(a => a.Kindled != null && a.Slots.Contains(ItemKind.Ring)).ToList();
        double share = pool.Count(a => wanted.Contains(a.Kindled!)) / (double)pool.Count;
        // Drawn three without replacement, a wanted coal shows more often than its share of the pool.
        Assert.True(hits / (3.0 * n) > share * 1.2, $"{hits / (3.0 * n):0.00} against {share:0.00}");
    }

    [Fact]
    public void Remaking_raises_the_pattern_opens_a_seam_adds_heat_and_ranks_the_weapon()
    {
        var j = Make();
        var w = j.Ch.Equipment.Weapon!;
        int rank = Character.Kit(j.Ch).Weapons.First(x => x.Id == Items.Get(w.Def).Weapon!.Id).Rank;
        Give(j, Crafting.Iron, 40);
        var q = Crafting.Remake(j.Craft, w);
        Assert.True(q.Ok, q.Blocked);
        Assert.True(j.Work(w.Uid, q, null));
        Assert.Equal(1, w.Rarity);
        Assert.Equal(10, w.Heat);
        Assert.Equal(10, w.HeatFull);
        Assert.Equal(1, Crafting.OpenSeams(w));
        Assert.Equal(rank + 1, Character.Kit(j.Ch).Weapons.First(x => x.Id == Items.Get(w.Def).Weapon!.Id).Rank);
        // A weapon takes a slayer in its new seam.
        Give(j, "wolf_pelt", 3);
        Assert.True(j.Work(w.Uid, Crafting.WorkIn(j.Craft, w, "wolf_pelt", "wolfbane"), null));
        Assert.True(j.Work(w.Uid, Crafting.Remake(j.Craft, w), null));
        Assert.True(j.Work(w.Uid, Crafting.Remake(j.Craft, w), null));
        Assert.Equal(3, w.Rarity);
        // Epic is the forge's last pattern in Act 1.
        Assert.False(Crafting.Remake(j.Craft, w).Ok);
        Assert.Contains(w.History!, h => h.StartsWith("Remade by Brannoc"));
    }

    [Fact]
    public void Heat_runs_out_and_the_piece_is_set_but_never_broken_and_rekindling_gets_dearer()
    {
        var j = Make();
        var it = Piece(j, "iron_helm", 3, ("hale", 0), ("sturdy", 0), ("keen", 0));
        Give(j, Crafting.Iron, 200);
        int crafts = 0;
        while (it.Heat > 0 && crafts < 20)
        {
            var q = Enumerable.Range(0, 3).Select(i => Crafting.Temper(j.Craft, it, i)).FirstOrDefault(x => x.Ok);
            if (q == null) break;
            Assert.True(j.Work(it.Uid, q, null));
            crafts++;
        }
        Assert.Equal(0, it.Heat);
        Assert.Equal(3, it.Affixes.Count);
        Assert.InRange(crafts, 3, 6);
        Assert.Contains("set", Crafting.Temper(j.Craft, it, 0).Blocked ?? Crafting.Temper(j.Craft, it, 1).Blocked);
        // Rekindled: half its full heat back, for shards that double each time.
        Give(j, Crafting.Shard, 50);
        var r1 = Crafting.Rekindle(j.Craft, it);
        Assert.Equal(3, r1.Takes[Crafting.Shard]);
        Assert.True(j.Work(it.Uid, r1, null));
        Assert.Equal(9, it.Heat);
        Assert.Equal(6, Crafting.Rekindle(j.Craft, it).Takes[Crafting.Shard]);
    }

    [Fact]
    public void Breaking_down_gives_old_iron_and_a_shard_for_a_coal_and_asks_the_piece_off_first()
    {
        var j = Make();
        var it = Piece(j, "silver_ring", 2, ("keen", 1), ("of_refusal", 0));
        var q = Crafting.BreakDown(j.Craft, it);
        Assert.True(q.Ok);
        Assert.Equal(4, q.Gives[Crafting.Iron]);
        Assert.Equal(1, q.Gives[Crafting.Shard]);
        Assert.True(j.Work(it.Uid, q, null));
        Assert.Null(Inventory.Find(j.Ch, it.Uid));
        Assert.Equal(4, Inventory.Count(j.Ch, Crafting.Iron));
        Assert.Equal(1, Inventory.Count(j.Ch, Crafting.Shard));
        Assert.False(Crafting.BreakDown(j.Craft, j.Ch.Equipment.Weapon!).Ok);
        Assert.False(Crafting.BreakDown(j.Craft, Piece(j, "wardens_lampiron", 3)).Ok);
    }

    [Fact]
    public void The_forge_is_banked_at_night_and_a_smith_likes_being_brought_work()
    {
        var j = Make();
        var it = Piece(j, "iron_helm", 2, ("hale", 0));
        Give(j, Crafting.Iron, 50);
        j.World.Time = TimeOfDay.Night;
        Assert.NotNull(Crafting.Closed("brannoc", j.Ctx));
        Assert.False(j.Work(it.Uid, Crafting.Temper(j.Craft, it, 0), null));
        Assert.Equal(0, it.Affixes[0].Tier);
        j.World.Time = TimeOfDay.Day;
        double respect = j.World.Npc("brannoc").Respect;
        Assert.True(j.Work(it.Uid, Crafting.Temper(j.Craft, it, 0), null));
        Assert.Equal(respect + 1, j.World.Npc("brannoc").Respect);
        // Unmet, he will not work for you at all.
        var k = Make();
        k.World.Npc("brannoc").Flags.Remove("met");
        Assert.NotNull(Crafting.Closed("brannoc", k.Ctx));
    }

    [Fact]
    public void Brannocs_respect_shortens_the_heat_and_saves_iron()
    {
        var j = Make();
        var it = Piece(j, "iron_helm", 2, ("hale", 0));
        Give(j, Crafting.Iron, 50);
        var plain = Crafting.Temper(j.Craft, it, 0);
        j.World.Npc("brannoc").Respect = 45;
        var kind = Crafting.Temper(j.Craft, it, 0);
        Assert.Equal(plain.HeatHi - 1, kind.HeatHi);
        Assert.Equal(plain.Takes[Crafting.Iron] - 1, kind.Takes[Crafting.Iron]);
        Assert.Equal(2, Crafting.TermLines("brannoc", j.Ctx).Count);
    }

    [Fact]
    public void Wenna_will_not_work_gear_while_the_stream_is_green()
    {
        var j = Make();
        j.World.Npc("wenna").Flags["met"] = true;
        Assert.NotNull(Crafting.Closed("wenna", j.Ctx));
        j.World.Facts["stream.clear"] = true;
        Assert.Null(Crafting.Closed("wenna", j.Ctx));
    }

    [Fact]
    public void The_night_pays_shards_for_the_ember_and_the_people_for_their_champions_and_a_fall_spills_half()
    {
        var champs = new Dictionary<Family, int> { [Family.Wolf] = 950, [Family.Boar] = 220 };
        var y = Crafting.Night("pack", 1, false, 52, 0, true, false, champs);
        Assert.Equal(5, y.Kept[Crafting.Shard]);
        Assert.Equal(6, y.Kept["wolf_pelt"]);
        Assert.Equal(1, y.Kept["boar_hide"]);
        Assert.Empty(y.Spilled);
        // Five minutes past the half hour: two more; a story fight won: two more; tier three: two more.
        Assert.Equal(5 + 2 + 2 + 2, Crafting.Night("pack", 3, true, 52, 5, true, false, champs).Kept[Crafting.Shard]);
        // Fallen there: half of everything.
        var fell = Crafting.Night("pack", 3, true, 52, 5, true, true, champs);
        Assert.Equal(5, fell.Kept[Crafting.Shard]);
        Assert.Equal(6, fell.Spilled[Crafting.Shard]);
        Assert.Equal(3, fell.Kept["wolf_pelt"]);
        // Lost: no minutes past and no story bonus.
        var lost = Crafting.Night("dead", 1, true, 20, 0, false, true, new Dictionary<Family, int> { [Family.Undead] = 400 });
        Assert.Equal(0, lost.Kept.GetValueOrDefault(Crafting.Shard));
        Assert.Equal(1, lost.Spilled[Crafting.Shard]);
        Assert.Equal(1, lost.Kept["bone_dust"]);
        // Capped at eight a kind.
        Assert.Equal(8, Crafting.Night("kerchiefs", 3, false, 80, 0, true, false, new Dictionary<Family, int> { [Family.Kerchief] = 5000 }).Kept["kerchief_cloth"]);
    }

    [Fact]
    public void An_older_save_moves_its_materials_to_the_pouch_and_gives_its_gear_heat()
    {
        var j = Make();
        var helm = Piece(j, "iron_helm", 2, ("hale", 1));
        var text = Json.Write(j.ToSave(new SaveLocation { Zone = "waystation" }));
        var d = Json.Parse<SaveData>(text);
        // As a version 2 save was: materials in the pack, no heat anywhere.
        d.Version = 2;
        d.Character.Materials = null!;
        int at = d.Character.Pack.FindIndex(p => p == null);
        d.Character.Pack[at] = new ItemInstance { Uid = "old1", Def = "bone_dust", Qty = 5 };
        foreach (var it in d.Character.Pack.Concat(Items.EquipSlots.Select(s => d.Character.Equipment[s])))
            if (it != null) { it.Heat = null; it.HeatFull = null; }
        var back = Saves.Migrate(Json.Parse<SaveData>(Json.Write(d)));
        Assert.Equal(Saves.Version, back.Version);
        Assert.Equal(5, back.Character.Materials["bone_dust"]);
        Assert.DoesNotContain(back.Character.Pack, p => p?.Def == "bone_dust");
        Assert.Equal(14, back.Character.Pack.First(p => p?.Uid == helm.Uid)!.Heat);
        Assert.Equal(6, back.Character.Equipment.Weapon!.Heat);
    }
}
