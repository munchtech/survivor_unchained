using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>World tiers I-IV (ARPG.md 7.3; Content/WorldTiers.cs, data/content/world_tiers.json) and where they land.</summary>
public class WorldTiersTests
{
    static Battle Fight(double health, double damage)
    {
        var b = new Battle(new BattleSetup { Seed = 1, Collision = new CollisionWorld(120), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
        b.WorldHealth = health; b.WorldDamage = damage;
        return b;
    }

    static string Foe() => Enemies.All.Values.First(d => d.Faction == Faction.Pack).Id;

    [Fact]
    public void The_default_is_tier_two()
    {
        var w = new WorldState();
        Assert.Equal(2, WorldTiers.Of(w));
        Assert.Equal(1, WorldTiers.Get(2).Health);
    }

    [Fact]
    public void Tier_three_is_locked_until_its_fact()
    {
        var w = new WorldState();
        Assert.False(WorldTiers.Open(w, 3));
        Assert.False(WorldTiers.Set(w, 3));
        Assert.Equal(2, WorldTiers.Of(w));
        w.Facts[WorldTiers.Get(3).Opens!] = true;
        Assert.True(WorldTiers.Set(w, 3));
        Assert.Equal(3, WorldTiers.Of(w));
        Assert.True(WorldTiers.Set(w, 1));
    }

    [Fact]
    public void A_foe_on_tier_one_has_less_health_and_damage()
    {
        var a = Fight(1, 1).SpawnEnemy(Foe(), 5, 0)!;
        var b = Fight(0.7, 0.6).SpawnEnemy(Foe(), 5, 0)!;
        Assert.Equal(a.MaxHp * 0.7, b.MaxHp, 6);
        Assert.Equal(a.Damage * 0.6, b.Damage, 6);
    }

    [Fact]
    public void An_ally_is_unscaled()
    {
        var o = new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally };
        var a = Fight(1, 1).SpawnEnemy(Foe(), 5, 0, o)!;
        var b = Fight(6, 3).SpawnEnemy(Foe(), 5, 0, new Battle.SpawnOpts { Faction = Faction.Ally, Disposition = Disposition.Ally })!;
        Assert.Equal(a.MaxHp, b.MaxHp, 6);
        Assert.Equal(a.Damage, b.Damage, 6);
    }

    static Play.Journey New()
    {
        var a = Callings.Archetype("warden");
        return Play.Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 42);
    }

    [Fact]
    public void An_arena_battle_is_unscaled_and_a_story_fight_is_scaled()
    {
        var j = New();
        j.World.Facts[WorldTiers.Get(3).Opens!] = true;
        j.World.Facts[WorldTiers.Get(4).Opens!] = true;
        Assert.True(WorldTiers.Set(j.World, 4));
        var arena = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1, arena: true);
        Assert.Equal(1, arena.WorldHealth);
        Assert.Equal(1, arena.KitDamageMul);
        Assert.False(j.WorldTierOn);
        var story = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1);
        Assert.Equal(6, story.WorldHealth);
        Assert.Equal(3, story.WorldDamage);
        Assert.Equal(1.3, story.KitDamageMul);
        Assert.True(j.WorldTierOn);
        var map = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1, worldTier: false);
        Assert.Equal(1, map.WorldHealth);
    }

    [Fact]
    public void The_drop_wrapper_raises_rarity_and_level_on_tier_four()
    {
        var j = New();
        j.World.Facts[WorldTiers.Get(3).Opens!] = true;
        j.World.Facts[WorldTiers.Get(4).Opens!] = true;
        WorldTiers.Set(j.World, 4);
        j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 1);
        var x = new DropCtx { Source = DropSource.Champion, Level = 5, People = "pack", R = new System.Random(1).NextDouble };
        j.Drops(x);
        Assert.Equal(2, x.Rarity, 6);
        Assert.Equal(2.5, x.LegendaryMul, 6);
        Assert.Equal(15, x.Level);
    }
}
