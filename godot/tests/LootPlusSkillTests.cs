using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M9, ARPG.md 9) "+1 to a skill": a worn piece raises one skill she carries a rank, so its wick lights one
/// more lamp (Items.Affixes' plus_ suffixes, ItemDef.Plus, Character.SkillPlus, SkillBook.RankOf, Battle.SetRank).</summary>
public class LootPlusSkillTests
{
    static ItemInstance Ring(string skill, uint seed = 3) =>
        Inventory.Make(null, "copper_ring", rarity: 2, seed: seed, affixes: new List<AffixRoll> { new() { Id = Items.PlusId(skill), Tier = 0 } });

    static Journey Warden(int level = 10) => MapSim.Survivor("warden", level, 1, 5);

    [Fact]
    public void A_plus_suffix_is_made_for_each_listed_skill_and_only_those()
    {
        foreach (var id in Drops.Rules.PlusSkills.Where(Weapons.All.ContainsKey))
        {
            var a = Items.Affix(Items.PlusId(id));
            Assert.NotNull(a);
            Assert.Equal(id, a!.Plus);
            Assert.False(a.Prefix);
            Assert.Equal(2, a.MinRarity);
            Assert.Equal($"+1 to {Weapons.All[id].Name}", a.Text(0));
            Assert.Contains(ItemKind.Ring, a.Slots);
            Assert.DoesNotContain(ItemKind.Weapon, a.Slots);
        }
        Assert.Equal("of the Leap", Items.Affix("plus_heroic_leap")!.Name);
        // one to a skill, never for one not listed (another calling's)
        Assert.Null(Items.Affix("plus_knifestorm"));
        Assert.Equal(Items.Affixes.Length, Items.Affixes.Select(a => a.Id).Distinct().Count());
        Assert.All(Items.Affixes.Where(a => a.Plus != null), a => Assert.False(Crafting.Bindable(a)));
    }

    [Fact]
    public void Gear_rolled_for_a_survivor_never_raises_a_skill_her_calling_cannot_carry()
    {
        var plus = Items.Affixes.Where(a => a.Plus != null).ToList();
        var other = Callings.Archetypes.Keys.FirstOrDefault(c => plus.Any(a => !Weapons.CanCarry(c, a.Plus!)));
        Assert.NotNull(other);
        foreach (var calling in new[] { "warden", other! })
        {
            var ch = Journey.Begin(new CreationChoice
            {
                Name = "Ashe", Archetype = calling, Background = "hunter", Palette = Callings.Archetype(calling).Palettes[0].Id,
                WeaponItem = Callings.Archetype(calling).Weapons[0], Ability = Callings.Archetype(calling).Abilities[0],
            }, 9).Ch;
            int seen = 0;
            for (uint s = 1; s <= 600; s++)
                foreach (var def in new[] { "copper_ring", "bone_amulet", "iron_helm" })
                    foreach (var r in Inventory.Make(ch, def, rarity: 3, seed: s).Affixes)
                        if (Items.Affix(r.Id)?.Plus is { } skill) { seen++; Assert.True(Weapons.CanCarry(calling, skill), $"{calling} rolled {r.Id}"); }
            if (calling == "warden") Assert.True(seen > 0, "a warden's fine gear rolls a +1 now and then");
        }
    }

    [Fact]
    public void Two_pieces_add_two_and_the_rank_caps_at_eight()
    {
        var j = Warden(10);
        var ch = j.Ch;
        var (skill, rank) = SkillBook.Carried(ch).First();
        Assert.Equal(SkillBook.Rank(ch), rank);
        Assert.Equal(0, Character.SkillPlus(ch, skill));
        Assert.True(Inventory.Equip(ch, Ring(skill, 1), EquipSlot.Ring1));
        Assert.True(Inventory.Equip(ch, Ring(skill, 2), EquipSlot.Ring2));
        Assert.Equal(2, Character.SkillPlus(ch, skill));
        Assert.Equal(SkillBook.Rank(ch) + 2, SkillBook.RankOf(ch, skill));
        Assert.Equal(SkillBook.Rank(ch) + 2, SkillBook.Carried(ch).Single(c => c.Id == skill).Rank);
        Assert.Equal(SkillBook.Rank(ch) + 2, WickBook.RankIn(ch, skill, night: false));
        // another carried skill is not raised
        foreach (var (id, r) in SkillBook.Carried(ch).Where(c => c.Id != skill)) Assert.Equal(SkillBook.Rank(ch), r);

        var high = Warden(22);
        var (s2, _) = SkillBook.Carried(high.Ch).First();
        Assert.Equal(Weapons.MaxRank, SkillBook.Rank(high.Ch));
        Assert.True(Inventory.Equip(high.Ch, Ring(s2), EquipSlot.Ring1));
        Assert.Equal(Weapons.MaxRank, SkillBook.RankOf(high.Ch, s2));
    }

    [Fact]
    public void In_a_campaign_fight_putting_it_on_lights_a_lamp_and_taking_it_off_puts_it_out()
    {
        var j = Warden(10);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        Assert.True(b.Campaign);
        var carried = SkillBook.Carried(j.Ch).Select(c => c.Id).ToHashSet();
        var w = b.Weapons.First(x => carried.Contains(x.Id) && (x.Wick?.Lit.Length ?? 0) > 0 && x.Rank < Weapons.MaxRank);
        int rank = w.Rank, lit = w.Wick!.Lit.Length;
        Assert.Equal(SkillBook.Rank(j.Ch), rank);

        Assert.True(Inventory.Equip(j.Ch, Ring(w.Id), EquipSlot.Ring1));
        j.RefreshKit(b);
        Assert.Equal(rank + 1, w.Rank);
        Assert.True(w.Wick!.Lit.Length >= lit);

        Assert.True(Inventory.Unequip(j.Ch, EquipSlot.Ring1));
        j.RefreshKit(b);
        Assert.Equal(rank, w.Rank);
        Assert.Equal(lit, w.Wick!.Lit.Length);
    }

    [Fact]
    public void A_named_pieces_own_plus_counts()
    {
        // TEST-ONLY def (the Legendary that carries one is another step's).
        Items.Register(new ItemDef
        {
            Id = "test_plus_band", Name = "Test Band", Kind = ItemKind.Ring, Rarity = 4, Icon = "ring",
            Plus = new Dictionary<string, int> { ["heroic_leap"] = 2 },
        });
        var ch = Warden(10).Ch;
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, "test_plus_band"), EquipSlot.Ring1));
        Assert.True(Inventory.Equip(ch, Ring("heroic_leap"), EquipSlot.Ring2));
        Assert.Equal(3, Character.SkillPlus(ch, "heroic_leap"));
        Assert.Equal(0, Character.SkillPlus(ch, "sunder"));
        Assert.Equal(System.Math.Min(Weapons.MaxRank, SkillBook.Rank(ch) + 3), SkillBook.RankOf(ch, "heroic_leap"));
    }

    [Fact]
    public void A_plus_adds_to_power_and_has_no_grades()
    {
        var plain = Inventory.Make(null, "copper_ring", rarity: 2, seed: 3, affixes: new List<AffixRoll>());
        Assert.Equal(Drops.Power(plain) + 5, Drops.Power(Ring("sunder")), 6);
    }
}
