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

/// <summary>A journey as the game keeps it (Play/Journey.cs, the web game's
/// game.ts without the drawing).</summary>
public class JourneyTests
{
    static CreationChoice Choice(string bg = "hunter")
    {
        var a = Callings.Archetype("warden");
        return new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = bg, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        };
    }

    static (Journey J, List<Toast> Toasts) Make(string bg = "hunter")
    {
        var j = Journey.Begin(Choice(bg), 42);
        var toasts = new List<Toast>();
        j.OnToast = toasts.Add;
        return (j, toasts);
    }

    static Battle Fight(Journey j, bool combat = true) => j.StartBattle(combat, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 7);

    [Fact]
    public void A_new_journey_starts_on_the_road_with_a_draught()
    {
        var (j, _) = Make();
        // One more than the background packs.
        var bare = Character.Create(Choice(), 1, 42);
        Assert.Equal(Inventory.Count(bare, "health_draught") + 1, Inventory.Count(j.Ch, "health_draught"));
        Assert.Equal(60, j.World.Fact("beasts.population").Number);
        // Where you came from decides how the world first reads you.
        var bg = Callings.Background("hunter");
        foreach (var (f, v) in bg.Standing) Assert.Equal(v, j.World.Factions[f].Standing);
    }

    [Fact]
    public void A_journey_saves_and_comes_back_the_same()
    {
        var (j, _) = Make();
        j.Ch.Gold = 37;
        var b = Fight(j);
        b.GainEmber(b.EmberNext * 3);
        j.Capture(b);
        var text = Json.Write(j.ToSave(new SaveLocation { Zone = "verge", X = 3, Z = 4 }));
        var back = Journey.From(Json.Parse<SaveData>(text), 1);
        Assert.Equal(37, back.Ch.Gold);
        Assert.Equal(j.Ch.Name, back.Ch.Name);
        Assert.Equal(j.Expedition!.Level, back.Expedition!.Level);
        Assert.Equal(j.Expedition.Hp, back.Expedition.Hp);
    }

    [Fact]
    public void The_ember_is_carried_into_the_next_zone_and_not_into_town()
    {
        var (j, _) = Make();
        var b = Fight(j);
        // Blessings are the arenas' own: nothing is given for the road.
        Assert.DoesNotContain(b.Boons.Keys, Content.Boons.IsGreat);
        for (int i = 0; i < 4; i++) b.GainEmber(b.EmberNext);
        var extra = Content.Weapons.All.Keys.First(id => !b.Weapons.Any(w => w.Id == id));
        b.AddWeapon(extra, 2);
        j.Capture(b);
        var next = Fight(j);
        Assert.Equal(b.EmberLevel, next.EmberLevel);
        Assert.Contains(next.Weapons, w => w.Id == extra && w.Rank == 2);
        // A town is not an expedition: no ember there, and none captured.
        var town = Fight(j, combat: false);
        Assert.Equal(1, town.EmberLevel);
        j.Capture(town);
        Assert.Equal(b.EmberLevel, j.Expedition!.Level);
    }

    [Fact]
    public void Falling_costs_gold_a_thing_carried_and_makes_a_nemesis()
    {
        var (j, _) = Make();
        j.Ch.Gold = 51;
        j.GiveItem("wolf_pelt", 2);
        var b = Fight(j);
        var wolf = b.SpawnEnemy("wolf", 3, 3)!;
        b.Player.LastKiller = wolf;
        j.Fell("verge", "the Verge", wolf.Def.Name, b.Player, new Random(1));
        Assert.Equal(26, j.Ch.Gold);
        Assert.Equal(25, j.World.Corpse!.Gold);
        Assert.Equal("verge", j.World.Corpse.Zone);
        var n = j.World.Nemesis!;
        Assert.EndsWith("Who Took Your Light", n.Title);
        Assert.Equal(wolf.Level + 2, n.Level);
        // It took something that was not a draught.
        Assert.Single(n.Carries);
        Assert.NotEqual("health_draught", n.Carries[0].Def);
        Assert.Contains(j.Ch.Conditions, c => c.Id == ConditionId.Wounded);
        Assert.Contains("risen_once", j.Ch.Traits);
        Assert.True(j.World.Fact("player.just_died").Truthy);
        Assert.Contains(j.World.History, h => h.Id.StartsWith("fell_"));
        Assert.Null(j.Expedition);
    }

    [Fact]
    public void A_shop_sells_restocks_and_buys_back()
    {
        var (j, toasts) = Make();
        var shop = Lore.Shops.Keys.First(id => Lore.Shops[id].Lines.Any(l => l.When == null && l.Chance == null));
        var st = j.OpenShop(shop, new Random(3))!;
        Assert.NotEmpty(st.Stock);
        var it = st.Stock.First();
        int price = j.PriceOf(shop, it.Uid, buying: true)!.Value;
        j.Ch.Gold = price - 1;
        j.Buy(shop, it.Uid);
        Assert.Contains(toasts, t => t.Kind == ToastKind.Warning && t.Text.Contains("costs"));
        j.Ch.Gold = price + 10;
        int had = Inventory.Count(j.Ch, it.Def);
        j.Buy(shop, it.Uid);
        Assert.Equal(10, j.Ch.Gold);
        Assert.Equal(had + 1, Inventory.Count(j.Ch, it.Def));
        // The same stock until its days are up.
        Assert.Same(st, j.OpenShop(shop, new Random(4)));
        j.World.Day += Lore.Shops[shop].RestockDays;
        Assert.NotSame(st, j.OpenShop(shop, new Random(4)));
    }

    [Fact]
    public void Selling_pelts_to_the_smith_is_remembered()
    {
        var (j, _) = Make();
        j.GiveItem("wolf_pelt", 3);
        var pelt = j.Ch.Pack.First(p => p?.Def == "wolf_pelt")!;
        if (!Lore.Shops.ContainsKey("brannoc")) return;
        j.OpenShop("brannoc", new Random(1));
        j.Ch.Gold = 0;
        var price = j.PriceOf("brannoc", pelt.Uid, buying: false);
        Assert.NotNull(price);
        j.Sell("brannoc", pelt.Uid);
        Assert.Equal(price!.Value, j.Ch.Gold);
        Assert.Equal(3, j.World.Fact("beasts.pelts_sold").Number);
    }

    [Fact]
    public void The_storeroom_keeps_what_is_put_in_it()
    {
        var (j, _) = Make();
        var d = j.Ch.Pack.First(p => p != null)!;
        j.ToStash(d.Uid);
        Assert.DoesNotContain(j.Ch.Pack, p => p?.Uid == d.Uid);
        Assert.Contains(j.World.Stash, p => p?.Uid == d.Uid);
        j.FromStash(d.Uid);
        Assert.Contains(j.Ch.Pack, p => p?.Uid == d.Uid);
    }

    [Fact]
    public void Sleeping_moves_the_world_on_and_puts_the_ember_out()
    {
        var (j, _) = Make();
        j.Ch.Gold = 20;
        var b = Fight(j);
        j.Capture(b);
        b.Player.Hp = 1;
        int day = j.World.Day;
        var lines = j.Sleep(b, hadEmber: true, H.Lcg(0.3))!;
        Assert.Equal(day + 1, j.World.Day);
        Assert.Equal(TimeOfDay.Day, j.World.Time);
        Assert.Equal(15, j.Ch.Gold);
        Assert.Null(j.Expedition);
        Assert.Equal(b.MaxHp, b.Player.Hp);
        Assert.Contains(lines, l => l.Contains("ember went out"));
        // Rook's friends sleep free; nobody sleeps on credit.
        j.World.Npc("rook").Affection = 40;
        Assert.Equal(0, j.RestCost);
        j.World.Npc("rook").Affection = 0;
        j.Ch.Gold = 2;
        Assert.Null(j.Sleep(b, false, H.Lcg(0.1)));
    }

    [Fact]
    public void A_draught_heals_and_is_gone()
    {
        var (j, toasts) = Make();
        var b = Fight(j);
        j.Quaff(b);
        Assert.Contains(toasts, t => t.Text == "You are unhurt");
        int n = Inventory.Count(j.Ch, "health_draught");
        b.Player.Hp = b.MaxHp * 0.2;
        j.Quaff(b);
        Assert.True(b.Player.Hp > b.MaxHp * 0.5);
        Assert.Equal(n - 1, Inventory.Count(j.Ch, "health_draught"));
        for (int i = 1; i < n; i++) { b.Player.Hp = 1; j.Quaff(b); }
        Assert.Equal(0, Inventory.Count(j.Ch, "health_draught"));
        b.Player.Hp = 1;
        j.Quaff(b);
        Assert.Contains(toasts, t => t.Text == "No draughts left");
    }

    [Fact]
    public void Walking_clears_the_map_where_you_went()
    {
        var (j, _) = Make();
        Assert.True(j.Walk("verge", 290, 0, 0));
        Assert.False(j.Walk("verge", 290, 0, 0));
        var seen = j.World.Zone("verge")["seen"].Str!;
        Assert.Equal(Journey.FogN * Journey.FogN, seen.Length);
        // The middle is walked; a corner is not.
        Assert.Equal('1', seen[(Journey.FogN / 2) * Journey.FogN + Journey.FogN / 2]);
        Assert.Equal('0', seen[0]);
    }

    [Fact]
    public void Gear_changes_fold_into_the_running_fight()
    {
        var (j, _) = Make();
        var b = Fight(j);
        double armour = b.Stats.Get(Stat.Armor);
        var chest = Items.All.Values.First(d => d.Kind == ItemKind.Body && (d.Mods ?? new()).Any(m => m.Stat == Stat.Armor && m.Value > 0) && j.Ch.Equipment.Body?.Def != d.Id);
        j.GiveItem(chest.Id);
        var it = j.Ch.Pack.First(p => p?.Def == chest.Id)!;
        j.Equip(it.Uid, null, b);
        Assert.True(b.Stats.Get(Stat.Armor) > armour);
        j.Unequip(EquipSlot.Body, b);
        Assert.Equal(armour, b.Stats.Get(Stat.Armor), 6);
    }
}
