using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-061) Capacity never loses value: a drop made while the pickup pool is full is kept, exactly
/// as rolled, laid down when a slot frees, and counted by a fight's end and a zone left like anything lying.</summary>
public sealed class PickupCapacityTests
{
    static Journey Begin()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
    }

    static void Fill(Battle b)
    {
        while (b.Pickups.Count < b.Pickups.Capacity) b.SpawnPickup(PickupKind.Gold, 50, 50, 1);
    }

    static Loot Rare(ItemInstance it) => new(PickupKind.Item, it.Def, 1, true, it.Rarity, null, it, (int)Drops.TierOf(it), Verdict.Shown);

    [Fact]
    public void A_drop_with_the_pool_full_is_held_and_laid_down_as_a_slot_frees()
    {
        var b = BattleTests.Arena(1);
        Fill(b);
        var it = Inventory.Make(null, "iron_helm", rarity: 2, seed: 1, level: 5);
        var pk = b.Spill(Rare(it), 30, 30);
        Assert.NotNull(pk);
        Assert.Same(pk, Assert.Single(b.Held));
        Assert.Same(it, pk!.Payload);
        Assert.True(pk.Persistent);
        b.Pickups.Release(b.Pickups.Items.First(k => k.Alive && k.Kind == PickupKind.Gold));
        b.Tick(1 / 60.0, 0, 0);
        Assert.Empty(b.Held);
        Assert.True(pk.Alive);
        Assert.Same(pk, b.Pickups.Items[pk.Id]);
        Assert.Same(it, pk.Payload);
    }

    [Fact]
    public void A_held_rare_reaches_rooks_storeroom_when_the_zone_is_left()
    {
        var j = Begin();
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        Fill(b);
        var it = Inventory.Make(null, "iron_helm", rarity: 2, seed: 1, level: 5);
        b.Spill(Rare(it), 30, 30);
        Assert.Equal(1, j.Abandon(b));
        Assert.Contains(it, j.World.Stash);
        Assert.Empty(b.Held);
    }

    [Fact]
    public void The_hoard_stones_first_ember_with_the_pool_full_is_kept()
    {
        var b = BattleTests.Arena(1);
        b.Player.Iframes = 1e9;
        while (b.Pickups.Count < Battle.EmberCap + 20) b.SpawnPickup(PickupKind.Ember, 50, 50, 1);
        var e = b.SpawnEnemy("risen", -40, -40)!;
        Fill(b);
        b.Tick(1 / 60.0, 0, 0);
        Assert.True(b.EmbersLying >= Battle.EmberCap);
        double xp = e.Def.Xp * Enemies.ScaleFor(e.Level).Xp * b.Rules.EmberGain * b.Rules.KillEmber;
        Assert.True(xp > 0);
        b.KillEnemy(e, true, null);
        var hoard = b.HoardStone;
        Assert.NotNull(hoard);
        Assert.Equal(xp, hoard!.Value, 6);
    }
}
