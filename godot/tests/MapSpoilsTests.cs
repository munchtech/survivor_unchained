using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>What a map's result page tells (Maps/MapSpoils.cs): what came out of it, read from
/// the survivor before and after, best last, and the atlas's line.</summary>
public class MapSpoilsTests
{
    static CharacterData Survivor()
    {
        var a = Callings.Archetype("warden");
        return Character.Create(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 1, 7);
    }

    [Fact]
    public void A_map_pays_what_came_out_of_it_best_last()
    {
        var before = Survivor();
        before.Materials["wolf_pelt"] = 3;
        before.Gold = 100;
        var after = Core.Json.Clone(before);
        Inventory.AddToPack(after, Inventory.Make(after, "iron_helm", rarity: 3));
        Inventory.AddToPack(after, Inventory.Make(after, "copper_ring", rarity: 1));
        var chart = Inventory.Make(after, Charts.Item, 1, 2);
        chart.Chart = new Chart { Tier = 2, People = "pack", Name = "The Ashen Holt" };
        Inventory.AddToPack(after, chart);
        after.Materials["wolf_pelt"] = 7;
        after.Materials["ember_shard"] = 2;
        after.Gold = 460;

        var s = MapSpoils.Between(before, after);
        Assert.Equal(new[] { "copper_ring", "iron_helm" }, s.Gear.Select(g => g.Def));
        Assert.Equal("The Ashen Holt", Assert.Single(s.Charts).Chart!.Name);
        Assert.Equal(4, s.Materials["wolf_pelt"]);
        Assert.Equal(2, s.Materials["ember_shard"]);
        Assert.Equal(360, s.Gold);
        // What she walked in with is not what the map paid.
        Assert.Empty(MapSpoils.Between(after, after).Gear);
        // What the end of the map sent to Rook's storeroom is still its pay, and the page knows where it went.
        var shelf = new List<ItemInstance?> { null, null };
        var sent = Inventory.Make(after, "chain_shirt", rarity: 3);
        var later = new List<ItemInstance?> { sent, null };
        var t = MapSpoils.Between(before, after, shelf, later);
        Assert.Contains(t.Gear, g => g.Uid == sent.Uid);
        Assert.Contains(sent.Uid, t.Stored);
        Assert.Empty(MapSpoils.Between(after, after, later, later).Gear);
    }

    [Fact]
    public void A_chart_set_on_the_table_leaves_the_pack()
    {
        var ch = Survivor();
        var w = new World.WorldState();
        Assert.False(Atlas.IsOpen(w, ch));
        var low = Inventory.Make(ch, Charts.Item, 1, 0);
        low.Chart = new Chart { Tier = 1, People = "pack", Name = "The Hollow Holt" };
        var high = Inventory.Make(ch, Charts.Item, 1, 1);
        high.Chart = new Chart { Tier = 2, People = "dead", Name = "The Sunken Dene" };
        Inventory.AddToPack(ch, low);
        Inventory.AddToPack(ch, high);
        // A chart carried opens the atlas; the highest tier is offered first.
        Assert.True(Atlas.IsOpen(w, ch));
        Assert.Equal(new[] { "The Sunken Dene", "The Hollow Holt" }, Charts.Carried(ch).Select(c => c.Chart!.Name));
        Assert.Equal("The Hollow Holt", Charts.TakeOut(ch, low.Uid)!.Name);
        Assert.Null(Charts.TakeOut(ch, low.Uid));
        Assert.Single(Charts.Carried(ch));
    }

    [Fact]
    public void The_atlas_line_says_what_the_map_did()
    {
        var c = new Chart { Tier = 2, People = "lamplings", Name = "The Hollow Dene" };
        Assert.Equal("The Hollow Dene, tier 2: cleared, the first time: a point for the atlas", MapSpoils.AtlasLine(c, true, true));
        Assert.Equal("The Hollow Dene, tier 2: cleared", MapSpoils.AtlasLine(c, true, false));
        Assert.Equal("The Hollow Dene, tier 2: closed, Gutterwick still standing", MapSpoils.AtlasLine(c, false, false));
    }
}
