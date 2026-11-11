using System;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M9) The Ford-Warden's first kill leaves one designed Legendary: The Ford-Warden's Evening Chain.</summary>
public class LootM9WardenTests
{
    const string Id = Prologue.WardenGrant;

    static Journey Warden(int level = 10) => MapSim.Survivor("warden", level, 1, 5);
    static Func<double> Seq(int seed) { var r = new Random(seed); return r.NextDouble; }

    [Fact]
    public void A_grant_makes_the_first_Legendary_that_piece_once()
    {
        for (int s = 0; s < 300; s++)
        {
            var j = Warden(5);
            var first = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 7, People = "kerchiefs", Floor = (int)LootTier.Legendary, Grant = Id, R = Seq(s) });
            var legends = first.Where(d => d.Tier == LootTier.Legendary).ToList();
            var one = legends[0];
            Assert.Equal(Id, one.Item!.Def);
            Assert.Single(first, d => d.Item?.Def == Id);
            Assert.Equal(7, one.Item.Level);
            Assert.True(j.World.FirstLegendary);
            Assert.Contains(Id, j.World.Owned);
            var again = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 7, People = "kerchiefs", Floor = (int)LootTier.Legendary, Grant = Id, R = Seq(s + 5000) });
            Assert.DoesNotContain(again, d => d.Item?.Def == Id);
        }
    }

    [Fact]
    public void An_unknown_grant_is_ignored()
    {
        var j = Warden(5);
        var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 5, Grant = "no_such_piece", R = Seq(1) });
        Assert.DoesNotContain(d, x => x.Item?.Def == "no_such_piece");
    }

    [Fact]
    public void It_never_falls_by_chance()
    {
        Assert.Null(Items.Get(Id).DropsFrom);
        int n = 0;
        for (int s = 0; s < 500; s++)
        {
            var j = Warden(5);
            var d = Drops.Roll(new DropCtx { Ch = j.Ch, World = j.World, Source = DropSource.Boss, Level = 3 + s % 10, People = "dead", StoryBoss = s % 2 == 0, Floor = s % 3 == 0 ? (int)LootTier.Legendary : 0, R = Seq(s) });
            n += d.Count(x => x.Item?.Def == Id);
        }
        Assert.Equal(0, n);
    }

    [Fact]
    public void The_real_warden_first_kill_leaves_the_chain()
    {
        var s = MapSim.Survivor("warden", 6, 1, 5);
        var def = Items.Get(Id);
        Assert.Equal(ItemKind.Amulet, def.Kind);
        Assert.Equal(4, def.Rarity);
        Assert.Equal(1, def.Plus!["heroic_leap"]);
        // the Prologue path hands the same Grant: a first-kill ctx with it leaves the piece (PrologueTests asserts the fact and a Legendary).
        var d = Drops.Roll(new DropCtx { Ch = s.Ch, World = s.World, Source = DropSource.Boss, Level = 4, Floor = (int)LootTier.Legendary, Grant = Prologue.WardenGrant, R = Seq(9) });
        Assert.Equal(Id, d.First(x => x.Tier == LootTier.Legendary).Item!.Def);
    }

    [Fact]
    public void Worn_it_raises_Heroic_Leap_adds_its_mods_and_carries_its_trigger()
    {
        var j = Warden(10);
        var ch = j.Ch;
        ch.Discovered.Add("heroic_leap");
        SkillBook.Learn(ch, "heroic_leap");
        SkillBook.Slot(ch, "heroic_leap");
        Assert.True(SkillBook.Carried(ch).Any(c => c.Id == "heroic_leap"), "a level-10 warden carries Heroic Leap");
        int rank = SkillBook.RankOf(ch, "heroic_leap");
        double armor = Character.Kit(ch).Stats.Get(Stat.Armor), hp = Character.Kit(ch).Stats.Get(Stat.MaxHealth);
        Assert.True(Inventory.Equip(ch, Inventory.Make(ch, Id, dropped: true, level: 8), EquipSlot.Amulet));
        Assert.Equal(Math.Min(Weapons.MaxRank, rank + 1), SkillBook.RankOf(ch, "heroic_leap"));
        var kit = Character.Kit(ch);
        Assert.Equal(armor + 12, kit.Stats.Get(Stat.Armor), 6);
        Assert.True(kit.Stats.Get(Stat.MaxHealth) > hp + 15, $"{hp} -> {kit.Stats.Get(Stat.MaxHealth)}");
        var t = kit.Triggers.Single(x => x.Def.When?.Weapon == "heroic_leap");
        Assert.Equal(TriggerEvent.Hit, t.Def.On);
        Assert.Equal(1.5, t.Def.Icd);
    }
}
