using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The wardrobe (bd-ui W18): looks collected from gear found, shown over any piece, dyes as data.</summary>
public class WardrobeTests
{
    static ItemDef Reg(string id, ItemKind kind, string[]? wear, params string[] tags)
    {
        var d = new ItemDef { Id = id, Name = id, Kind = kind, Rarity = 1, Icon = "x", Description = "A wardrobe test piece.", Wear = wear?.ToList(), Tags = tags.Length > 0 ? tags.ToList() : null };
        Items.Register(d);
        return d;
    }

    static CharacterData Her()
    {
        Reg("wt_top_a", ItemKind.Body, ["wt.top", "wt.belt"]);
        Reg("wt_top_b", ItemKind.Body, ["wtb.top"]);
        Reg("wt_top_his", ItemKind.Body, ["wth.top"], "male");
        Reg("wt_boots", ItemKind.Feet, ["wt.boots"]);
        var ch = Character.Create(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id, WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0], Sex = Sex.Female }, 1, 7);
        ch.Sex = Sex.Female;
        return ch;
    }

    static ItemInstance Own(CharacterData ch, string id) => Inventory.Make(ch, id);

    [Fact]
    public void Collect_takes_only_looks_of_her_cut()
    {
        var ch = Her();
        Assert.True(Wardrobe.Collect(ch, "wt_top_a"));
        Assert.False(Wardrobe.Collect(ch, "wt_top_a"));
        Assert.False(Wardrobe.Collect(ch, "wt_top_his"));
        Assert.False(Wardrobe.Collect(ch, "health_draught"));
        Reg("wt_ring", ItemKind.Ring, null);
        Assert.False(Wardrobe.Collect(ch, "wt_ring"));
        Assert.Contains("wt_top_a", ch.Looks);
        Assert.DoesNotContain("wt_top_his", Wardrobe.All(ch, "body").Select(d => d.Id));
    }

    [Fact]
    public void Gear_entering_her_keeping_is_found()
    {
        var ch = Her();
        Her();
        Assert.True(Inventory.AddToPack(ch, Own(ch, "wt_boots")));
        Assert.Contains("wt_boots", ch.Looks);
        var top = Own(ch, "wt_top_b");
        Inventory.AddToPack(ch, top);
        Assert.True(Inventory.Equip(ch, top, EquipSlot.Body));
        Assert.Contains("wt_top_b", ch.Looks);
    }

    [Fact]
    public void Shown_replaces_the_groups_pieces_and_keeps_the_equipments_stats()
    {
        var ch = Her();
        var a = Own(ch, "wt_top_a"); Inventory.AddToPack(ch, a); Inventory.Equip(ch, a, EquipSlot.Body);
        Wardrobe.Collect(ch, "wt_top_b");
        var before = Character.Kit(ch).Stats.Get(Stat.Armor);
        Wardrobe.SetShown(ch, "body", "wt_top_b");
        var worn = Wear.Of(ch);
        Assert.Equal("wtb.top", worn["top"]);
        Assert.False(worn.ContainsKey("belt"));
        Assert.Same(a, ch.Equipment.Body);
        Assert.Equal(before, Character.Kit(ch).Stats.Get(Stat.Armor));
    }

    [Fact]
    public void Shown_over_an_empty_slot_dresses_it()
    {
        var ch = Her();
        Wardrobe.Collect(ch, "wt_boots");
        Assert.Null(ch.Equipment.Feet);
        Wardrobe.SetShown(ch, "feet", "wt_boots");
        Assert.Equal("wt.boots", Wear.Of(ch)["boots"]);
    }

    [Fact]
    public void A_look_not_collected_is_ignored_even_if_shown()
    {
        var ch = Her();
        ch.Shown["feet"] = "wt_boots";
        Assert.False(Wear.Of(ch).ContainsKey("boots"));
        ch.Shown["body"] = "wt_top_his";
        ch.Looks.Add("wt_top_his");
        Assert.False(Wear.Of(ch).ContainsKey("top") && Wear.Of(ch)["top"] == "wth.top");
    }

    [Fact]
    public void A_dye_overrides_only_its_zone()
    {
        var ch = Her();
        var a = Own(ch, "wt_top_a");
        a.Dye = new Dictionary<string, string> { ["cloth"] = "#111111", ["metal"] = "#222222" };
        Inventory.AddToPack(ch, a); Inventory.Equip(ch, a, EquipSlot.Body);
        Wardrobe.SetDye(ch, "body", "metal", "steel");
        var d = Wear.DyeOf(ch)["wt.top"];
        Assert.Equal("#aab0b8:metal", d["metal"]);
        Assert.Equal("#111111", d["cloth"]);
        // a dye the zone does not take is not applied
        Wardrobe.SetDye(ch, "body", "cloth", "steel");
        Assert.Equal("#111111", Wear.DyeOf(ch)["wt.top"]["cloth"]);
    }

    [Fact]
    public void An_unknown_dye_is_not_offered_until_learned()
    {
        var ch = Her();
        Assert.DoesNotContain(Wardrobe.Offered(ch), d => d.Id == "bronze");
        Assert.Contains(Wardrobe.Offered(ch), d => d.Id == "steel");
        // (metal-dye, 13 Nov: gilt and silvered read as metal now, released from their hold; a held dye is never offered)
        Assert.DoesNotContain(Wardrobe.Dyes, d => d.Hold);
        Assert.Contains(Wardrobe.Offered(ch), d => d.Id == "gilt");
        Assert.Contains(Wardrobe.Offered(ch), d => d.Id == "silvered");
        Wardrobe.SetDye(ch, "body", "metal", "bronze");
        var a = Own(ch, "wt_top_a"); Inventory.AddToPack(ch, a); Inventory.Equip(ch, a, EquipSlot.Body);
        Assert.False(Wear.DyeOf(ch).ContainsKey("wt.top"));
        Assert.True(Wardrobe.LearnDye(ch, "bronze"));
        Assert.Contains(Wardrobe.Offered(ch), d => d.Id == "bronze");
        Assert.Equal("#a8683a:metal", Wear.DyeOf(ch)["wt.top"]["metal"]);
        Assert.False(Wardrobe.LearnDye(ch, "gilt"));
    }

    [Fact]
    public void Dyes_data_is_a_careful_palette()
    {
        Assert.InRange(Wardrobe.Dyes.Count, 16, 22);
        Assert.InRange(Wardrobe.Dyes.Count(d => d.Known), 10, 14);
        Assert.All(Wardrobe.Dyes, d => Assert.Matches("^#[0-9a-f]{6}(:metal)?$", d.Hex));
    }

    [Fact]
    public void An_old_save_without_the_fields_loads()
    {
        var ch = Her();
        var json = Json.Write(ch);
        var node = System.Text.Json.Nodes.JsonNode.Parse(json)!.AsObject();
        foreach (var k in new[] { "Looks", "Shown", "Dyes", "DyesKnown" }) node.Remove(k);
        var back = Json.Parse<CharacterData>(node.ToJsonString());
        Assert.NotNull(back.Looks);
        Wardrobe.BackFill(back);
        Assert.Empty(back.Dyes);
        Assert.NotNull(Wear.Of(back));
    }

    [Fact]
    public void Items_wearing_the_same_pieces_are_one_look()
    {
        var ch = Her();
        Reg("wt_top_twin", ItemKind.Body, ["wt.belt", "wt.top"]);
        var body = Wardrobe.All(ch, "body");
        Assert.Contains(body, d => d.Id == "wt_top_a");
        Assert.DoesNotContain(body, d => d.Id == "wt_top_twin");
        // finding the twin finds the look
        Assert.True(Wardrobe.Collect(ch, "wt_top_twin"));
        Assert.Contains(Wardrobe.Found(ch, "body"), d => d.Id == "wt_top_a");
        // and no two looks of a slot in the game's own data wear the same pieces
        foreach (var slot in new[] { "head", "body", "feet" })
        {
            var keys = Wardrobe.All(ch, slot).Select(d => string.Join("|", d.Wear!.OrderBy(x => x, System.StringComparer.Ordinal))).ToList();
            Assert.Equal(keys.Count, keys.Distinct().Count());
        }
    }

    [Fact]
    public void A_piece_with_no_wear_draws_the_callings_kit_and_is_one_tile_with_the_look_that_draws_the_same()
    {
        var ch = Her();
        ch.Equipment.Body = Own(ch, "padded_jerkin");
        Assert.False(Wardrobe.OwnHasLook(ch, "body"));
        Wardrobe.BackFill(ch);
        // nothing found draws what her own does yet: no merged tile
        Assert.Null(Wardrobe.OwnLook(ch, "body"));
        Assert.True(Wardrobe.Collect(ch, "warden_plate"));
        var same = Wardrobe.OwnLook(ch, "body");
        Assert.NotNull(same);
        Assert.Equal(Wardrobe.OwnDrawn(ch, "body"), Wardrobe.LookDrawn(ch, same!, "body"));
    }

    [Theory]
    [InlineData("body", "padded_jerkin")]
    [InlineData("head", "leather_cap")]
    public void A_piece_with_no_look_offers_the_dyes_of_the_kit_it_draws(string slot, string item)
    {
        var ch = Her();
        var eq = slot == "body" ? EquipSlot.Body : EquipSlot.Head;
        ch.Equipment[eq] = Own(ch, item);
        Assert.False(Wardrobe.OwnHasLook(ch, slot));
        Assert.Null(ch.Shown?.GetValueOrDefault(slot));
        var zones = Wardrobe.ZonesOfSlot(ch, slot);
        if (slot == "head")
        {
            // (the warden's kit draws no head piece: a cap with no look of its own draws nothing, so there is nothing to dye; what is offered is what is drawn)
            Assert.Equal(Wardrobe.PiecesOf(ch, slot).SelectMany(p => Wardrobe.ZonesOf(p)).Distinct().Count(), zones.Count);
            if (zones.Count == 0) return;
        }
        Assert.NotEmpty(zones);
        if (slot == "body") { Assert.Contains("metal", zones); Assert.Contains("trim", zones); Assert.Contains("leather", zones); }
        var zone = zones.Contains("metal") ? "metal" : zones[0];
        var dye = Wardrobe.Offered(ch).First(d => d.Zones.Contains(zone));
        Wardrobe.SetDye(ch, slot, zone, dye.Id);
        var group = Wear.Group(eq);
        var drawn = Wardrobe.PiecesOf(ch, slot);
        var dyes = Wear.DyeOf(ch);
        Assert.Contains(drawn, p => dyes.TryGetValue(p, out var d) && d.ContainsKey(zone) && d[zone] == dye.Hex);
        // survives switching state (a look shown, then her own again)
        Wardrobe.SetShown(ch, slot, null);
        Assert.Contains(Wardrobe.PiecesOf(ch, slot), p => Wear.DyeOf(ch).TryGetValue(p, out var d) && d.ContainsKey(zone));
    }
}
