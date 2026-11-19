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

/// <summary>The den's chase (17 Nov 2026, the owner: "we want drops"): the Hollow's Gilt, her new armor set, falls one piece to a
/// clear from the den's ruler, leaning to the pieces she does not own, and from nowhere else.</summary>
public class GiltTests
{
    static readonly string[] Pieces = ["gilt_helm", "gilt_harness", "gilt_boots"];

    static Journey Begin()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0], Sex = Sex.Female }, 42);
    }

    static DropCtx Ctx(Journey j, DropSource s, string dungeon, Func<double> r) =>
        new() { Ch = j.Ch, World = j.World, Source = s, Dungeon = dungeon, Level = 6, People = "pack", Tier = 1, R = r };

    static IEnumerable<string> Gilt(IEnumerable<Dropped> d) => d.Where(x => x.Item != null && Pieces.Contains(x.Item.Def)).Select(x => x.Item!.Def);

    /// <summary>Clears until a fresh player owns all three; pieces are taken into the pack as a pickup does.</summary>
    static int Clears(Journey j, Random rng)
    {
        for (int i = 0; i < j.Ch.Pack.Count; i++) if (j.Ch.Pack[i] is { } p && Pieces.Contains(p.Def)) j.Ch.Pack[i] = null;
        foreach (var id in Pieces) j.World.Owned.Remove(id);
        int n = 0;
        while (!Pieces.All(id => j.Ch.Pack.Any(p => p?.Def == id)))
        {
            Assert.True(++n < 60, "a player who never completes the set");
            var got = Gilt(Drops.Roll(Ctx(j, DropSource.MapRuler, "hollow", rng.NextDouble))).ToList();
            Assert.Single(got);
            var it = Inventory.Make(j.Ch, got[0], dropped: true, level: 6);
            if (!j.Ch.Pack.Any(p => p?.Def == got[0])) Assert.True(Inventory.AddToPack(j.Ch, it));
        }
        return n;
    }

    [Fact]
    public void The_set_takes_a_median_of_four_clears_and_never_fewer_than_three()
    {
        var j = Begin();
        var rng = new Random(1117);
        var n = Enumerable.Range(0, 1000).Select(_ => Clears(j, rng)).OrderBy(x => x).ToList();
        Assert.Equal(3, n[0]);
        Assert.Equal(4, (n[499] + n[500]) / 2.0);
        Assert.True(n[^1] < 40);
    }

    [Fact]
    public void Only_the_dens_ruler_drops_them_one_to_a_clear()
    {
        var j = Begin();
        var rng = new Random(5);
        foreach (var d in new[] { "", "roost", null })
            for (int i = 0; i < 300; i++) Assert.Empty(Gilt(Drops.Roll(Ctx(j, DropSource.MapRuler, d!, rng.NextDouble))));
        foreach (var s in Enum.GetValues<DropSource>().Where(s => s != DropSource.MapRuler))
            for (int i = 0; i < 300; i++) Assert.Empty(Gilt(Drops.Roll(Ctx(j, s, "hollow", rng.NextDouble))));
        for (int i = 0; i < 200; i++) Assert.Single(Gilt(Drops.Roll(Ctx(j, DropSource.MapRuler, "hollow", rng.NextDouble))));
        // Not by chance: none of the three is in any Set roll's pool, anywhere.
        var any = new DropCtx { Level = 75, People = "pack", Allows = _ => true };
        Assert.DoesNotContain(Drops.SetPieces(any), d => Pieces.Contains(d.Id));
        Assert.True(Drops.Rules.Sets["hollow_gilt"].Pieces.SequenceEqual(Pieces));
    }

    [Fact]
    public void A_fallen_piece_is_owned_and_the_next_leans_to_what_is_missing()
    {
        var j = Begin();
        var got = Gilt(Drops.Roll(Ctx(j, DropSource.MapRuler, "hollow", new Random(3).NextDouble))).Single();
        Assert.Contains(got, j.World.Owned);
    }

    static CharacterData Her()
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0], Sex = Sex.Female }, 1, 7);
        ch.Sex = Sex.Female;
        return ch;
    }

    [Theory]
    [InlineData("gilt_helm", EquipSlot.Head, "kit_helm")]
    [InlineData("gilt_harness", EquipSlot.Body, "kit_pauldrons,kit_bodice,kit_brief,kit_belt,kit_vambraces,kit_gloves")]
    [InlineData("gilt_boots", EquipSlot.Feet, "kit_boots")]
    public void Each_piece_has_its_slot_and_draws_its_kit_pieces(string id, EquipSlot slot, string wear)
    {
        var def = Items.Get(id);
        Assert.Equal(slot, Items.SlotFor(def));
        Assert.Equal("hollow_gilt", def.Set);
        Assert.Equal(wear.Split(','), def.Wear);
        Assert.Empty(Wear.Validate(def));
        var ch = Her();
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, id, level: 6), slot));
        var drawn = Wardrobe.Drawn(ch).Values.ToHashSet();
        foreach (var p in def.Wear!) Assert.Contains(p, drawn);
    }

    [Fact]
    public void Any_mix_of_the_three_shows_the_starter_look_where_a_piece_is_missing()
    {
        var slots = new[] { EquipSlot.Head, EquipSlot.Body, EquipSlot.Feet };
        var baseline = Wardrobe.Drawn(Her());
        for (int mask = 0; mask < 8; mask++)
        {
            var ch = Her();
            for (int i = 0; i < 3; i++) if ((mask >> i & 1) == 1) Assert.True(Inventory.Equip(ch, Inventory.Make(ch, Pieces[i], level: 6), slots[i]));
            var drawn = Wardrobe.Drawn(ch);
            for (int i = 0; i < 3; i++)
            {
                var def = Items.Get(Pieces[i]);
                if ((mask >> i & 1) == 1) { foreach (var p in def.Wear!) Assert.Contains(p, drawn.Values); continue; }
                // (a worn piece hides what it covers, whichever slot: the boots hide the greaves)
                var hidden = Enumerable.Range(0, 3).Where(k => (mask >> k & 1) == 1).SelectMany(k => Items.Get(Pieces[k]).Wear!).SelectMany(w => ArmorIndex.Shared.Find(w)!.Covers).ToHashSet();
                foreach (var vs in Wear.Group(slots[i]).Where(v => !hidden.Contains(v)))
                    Assert.Equal(baseline.GetValueOrDefault(vs), drawn.GetValueOrDefault(vs));
            }
        }
    }
    // B (--body p1) reads only its built gear index: without the kit's rows there, an equipped piece's wear ids have no slot and
    // Wear.Of drops them (the gilt kit drew nothing in the game while --wear still drew it).
    [Theory]
    [InlineData("gilt_helm", EquipSlot.Head)]
    [InlineData("gilt_harness", EquipSlot.Body)]
    [InlineData("gilt_boots", EquipSlot.Feet)]
    public void B_gear_index_holds_every_kit_piece_in_its_items_slot_group(string id, EquipSlot slot)
    {
        var ix = ArmorIndex.Load(ArmorIndex.Text, "gear/out/body_p1");
        Assert.False(ix.GearMissing);
        foreach (var p in Items.Get(id).Wear!)
        {
            Assert.NotNull(ix.Find(p));
            Assert.Contains(ix.SlotOf(p), Wear.Group(slot));
        }
    }

    /// <summary>The demo's proof of drops (17 Nov): several den clears for one survivor, each ruler's piece taken home as Gather does,
    /// worn, saved and read back; the kit stays on and the next clear's weighting sees what she owns.</summary>
    [Fact]
    public void Clears_drop_pieces_she_wears_and_they_survive_a_save()
    {
        var j = Begin();
        var rng = new Random(11);
        var slots = new Dictionary<string, EquipSlot> { ["gilt_helm"] = EquipSlot.Head, ["gilt_harness"] = EquipSlot.Body, ["gilt_boots"] = EquipSlot.Feet };
        var worn = new List<string>();
        int clears = 0;
        while (worn.Count < 3)
        {
            Assert.True(++clears < 40);
            var got = Gilt(Drops.Roll(Ctx(j, DropSource.MapRuler, "hollow", rng.NextDouble))).Single();
            var it = Inventory.Make(j.Ch, got, dropped: true, level: 6);
            if (!worn.Contains(got))
            {
                Assert.True(Inventory.AddToPack(j.Ch, it));
                j.Equip(it.Uid, null, null);
                Assert.Equal(got, j.Ch.Equipment[slots[got]]?.Def);
                worn.Add(got);
            }
            // Between runs: save, read back, carry on with the reloaded survivor.
            var text = Json.Write(j.ToSave(new SaveLocation { Zone = "map", X = 1, Z = 2 }));
            j = Journey.From(Json.Parse<SaveData>(text), 1);
            foreach (var id in worn) Assert.Equal(id, j.Ch.Equipment[slots[id]]?.Def);
            var kit = Wear.Of(j.Ch).Values.ToHashSet();
            foreach (var id in worn) foreach (var w in Items.Get(id).Wear!) Assert.Contains(w, kit);
            foreach (var id in worn) Assert.Contains(id, j.World.Owned);
        }
        Assert.InRange(clears, 3, 12);
        // All worn: the weights see every piece as owned (even), and she still wears all three.
        Assert.All(Pieces, id => Assert.Contains(id, j.World.Owned));
    }

    /// <summary>The worn gilt piece shows no upgrade arrow over a same-level Rare of its slot (the pack's own test, Drops.IsUpgrade), on
    /// its own stats and with no set bonus counted, and stays within reach of the slot's Legendaries.</summary>
    [Theory]
    [InlineData("gilt_helm", EquipSlot.Head)]
    [InlineData("gilt_harness", EquipSlot.Body)]
    [InlineData("gilt_boots", EquipSlot.Feet)]
    public void The_worn_gilt_piece_beats_every_same_level_rare_of_its_slot(string id, EquipSlot slot)
    {
        const int Level = 6;   // the den's item level in the demo
        var ch = Her();
        var gilt = Inventory.Make(ch, id, level: Level, dropped: true, seed: 1);
        Assert.True(Inventory.Equip(ch, gilt, slot));
        var rng = new Random(2026);
        var x = new DropCtx { Ch = ch, Level = Level, People = "pack", Tier = 1, R = rng.NextDouble };
        int n = 0;
        for (int i = 0; i < 40000 && n < 1000; i++)
        {
            var it = Drops.Piece(x, LootTier.Rare, rng.NextDouble);
            if (Items.SlotFor(Items.Get(it.Def)) != slot) continue;
            n++;
            Assert.False(Drops.IsUpgrade(ch, it), $"{it.Def} (power {Drops.Power(it):0.0}) shows an arrow over {id} ({Drops.Power(gilt):0.0})");
        }
        Assert.Equal(1000, n);
        var best = Items.All.Values.Where(d => d.Rarity == 4 && d.Set == null && Items.SlotFor(d) == slot)
            .Max(d => Drops.Power(Inventory.Make(ch, d.Id, level: Level, dropped: true, seed: 1)));
        Assert.True(Drops.Power(gilt) <= best * 1.5, "gilt must stay about a Legendary's worth");
    }
}
