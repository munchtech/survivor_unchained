using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Kindled gear: what the day's gear may give the night's ember
/// beyond numbers (docs/SKILLS_DESIGN.md, "Gear and the ember"). One to an
/// item, two to a survivor; it shapes the draft and never owns it.</summary>
public class KindledTests
{
    static Play.Journey Warden(uint seed = 7) => Play.Journey.Begin(new CreationChoice
    {
        Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
        WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = "shield_bash",
    }, seed);

    static void Wear(Play.Journey j, string def, string affix, EquipSlot slot)
    {
        var it = Inventory.Make(j.Ch, def, 1, 3, affixes: [new AffixRoll { Id = affix, Tier = 2 }]);
        Assert.True(Inventory.AddToPack(j.Ch, it));
        j.Equip(it.Uid, slot, null);
    }

    [Fact]
    public void Two_kindlings_take_hold_and_a_third_does_nothing()
    {
        var j = Warden();
        Wear(j, "bone_amulet", "of_many_roads", EquipSlot.Amulet);
        Wear(j, "silver_ring", "of_the_whetstone", EquipSlot.Ring1);
        Wear(j, "copper_ring", "of_refusal", EquipSlot.Ring2);
        var kit = Character.Kit(j.Ch);
        Assert.Equal(2, kit.Kindled.Count);
        Assert.True(kit.Roads);
        Assert.Contains("serration", kit.Stands);
        Assert.Equal(0, kit.Banishes);
    }

    [Fact]
    public void Gear_stands_in_for_a_passive_in_a_recipe_but_not_for_the_ranks()
    {
        var j = Warden();
        Wear(j, "silver_ring", "of_the_whetstone", EquipSlot.Ring1);
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.Contains("serration", b.Stands);
        Assert.False(b.Boons.ContainsKey("serration"));
        var w = b.Weapons.First(x => x.Id == "oathblade");
        // The climb is the ember's own: below rank 8 nothing is earned.
        Assert.Empty(LevelUp.EarnedBranches(b, "oathblade"));
        w.Rank = Weapons.MaxRank;
        Assert.Contains(LevelUp.EarnedBranches(b, "oathblade"), e => e.Id == "graveedge");
    }

    [Fact]
    public void Many_roads_deal_a_fourth_card_and_omens_a_fourth_great()
    {
        var j = Warden();
        Wear(j, "bone_amulet", "of_omens", EquipSlot.Amulet);
        Wear(j, "silver_ring", "of_second_thoughts", EquipSlot.Ring1);
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.Equal(Character.Kit(Warden().Ch).Rerolls + 1, b.Rerolls);
        b.GreatOwed = 1;
        Assert.Equal(4, LevelUp.Draft(b).Count);

        var r = Warden(9);
        Wear(r, "bone_amulet", "of_many_roads", EquipSlot.Amulet);
        var rb = r.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        rb.GreatOwed = 0;
        rb.GainEmber(rb.EmberNext - rb.EmberXp + 0.01);
        Assert.True(LevelUp.SkillNext(rb));
        Assert.Equal(4, LevelUp.Draft(rb).Count);
    }

    [Fact]
    public void An_item_rolls_at_most_one_kindling()
    {
        var ch = Warden().Ch;
        for (uint seed = 1; seed <= 400; seed++)
        {
            var it = Inventory.Make(ch, "silver_ring", 1, 3, seed: seed);
            Assert.True(it.Affixes.Count(a => Items.Affix(a.Id)?.Kindled != null) <= 1);
        }
    }
}
