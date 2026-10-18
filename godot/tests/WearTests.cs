using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

public class WearTests
{
    static ItemDef Def(string id, ItemKind kind, params string[] wear) =>
        new() { Id = id, Name = id, Kind = kind, Rarity = 1, Icon = "x", Wear = wear.Length == 0 ? null : wear.ToList() };

    static ItemDef Reg(ItemDef d) { Items.Register(d); return d; }

    [Fact]
    public void Groups_cover_every_visual_slot_exactly_once()
    {
        var all = Items.EquipSlots.SelectMany(Wear.Group).OrderBy(x => x).ToList();
        Assert.Equal(Wear.VisualSlots.OrderBy(x => x).ToList(), all);
        Assert.Equal("pauldrons", Wear.SlotOf("warden.pauldrons"));
    }

    [Fact]
    public void Of_reads_pieces_and_ignores_the_wrong_group()
    {
        var defs = new Dictionary<string, ItemDef>
        {
            ["a"] = Def("a", ItemKind.Shoulders, "warden.pauldrons"),
            ["b"] = Def("b", ItemKind.Hands, "warden.gloves", "warden.boots"),
            ["c"] = Def("c", ItemKind.Body, "ash.top", "ash.collar"),
        };
        var eq = new Equipment();
        eq.Shoulders = new ItemInstance { Uid = "1", Def = "a" };
        eq.Hands = new ItemInstance { Uid = "2", Def = "b" };
        eq.Body = new ItemInstance { Uid = "3", Def = "c" };
        var w = Wear.Of(eq, id => defs.GetValueOrDefault(id));
        Assert.Equal("warden.pauldrons", w["pauldrons"]);
        Assert.Equal("warden.gloves", w["gloves"]);
        Assert.False(w.ContainsKey("boots"));
        Assert.Equal(4, w.Count);
        Assert.Equal(new[] { "warden.boots" }, Wear.Validate(defs["b"]));
        Assert.Empty(Wear.Of(new Equipment()));
    }

    [Fact]
    public void Every_item_def_validates() =>
        Assert.All(Items.All.Values, d => Assert.Empty(Wear.Validate(d)));

    [Fact]
    public void Hands_equip_and_unequip_through_the_game_path()
    {
        Reg(Def("zz_test_gloves", ItemKind.Hands, "test.gloves"));
        var s = Make();
        var it = Inventory.Make(s.Ch, "zz_test_gloves");
        Assert.True(Inventory.AddToPack(s.Ch, it));
        Assert.Equal(EquipSlot.Hands, Items.SlotFor(Items.Get("zz_test_gloves")));
        Assert.False(Inventory.Equip(s.Ch, it, EquipSlot.Body));
        Assert.True(Inventory.Equip(s.Ch, it, EquipSlot.Hands));
        Assert.Same(it, s.Ch.Equipment.Hands);
        Assert.Equal("test.gloves", Wear.Of(s.Ch)["gloves"]);
        Assert.True(Inventory.Unequip(s.Ch, EquipSlot.Hands));
        Assert.Null(s.Ch.Equipment.Hands);
        Assert.False(Wear.Of(s.Ch).ContainsKey("gloves"));
    }

    [Fact]
    public void Kind_strings_parse_and_an_old_character_shape_loads()
    {
        var d = Json.Parse<ItemDef>("{\"id\":\"q\",\"kind\":\"shoulders\"}");
        Assert.Equal(ItemKind.Shoulders, d.Kind);
        foreach (var k in new[] { "bracers", "hands", "belt", "legs", "feet", "body" }) Assert.NotNull(Json.Parse<ItemDef>("{\"kind\":\"" + k + "\"}"));
        var ch = Json.Parse<CharacterData>("{\"name\":\"Old\",\"equipment\":{\"head\":{\"uid\":\"a\",\"def\":\"iron_helm\"},\"body\":{\"uid\":\"b\",\"def\":\"chain_shirt\"},\"cloak\":{\"uid\":\"c\",\"def\":\"travelers_cloak\"}}}");
        Assert.Equal("chain_shirt", ch.Equipment.Body!.Def);
        Assert.Equal("iron_helm", ch.Equipment.Head!.Def);
        Assert.Equal("travelers_cloak", ch.Equipment.Cloak!.Def);
        Assert.Null(ch.Equipment.Feet);
    }

    [Fact]
    public void Migration_moves_a_misplaced_piece_to_its_slot_or_the_pack()
    {
        Reg(Def("zz_test_boots", ItemKind.Feet, "test.boots"));
        var s = Make();
        var a = Inventory.Make(s.Ch, "zz_test_boots");
        var b = Inventory.Make(s.Ch, "zz_test_boots");
        s.Ch.Equipment.Body = a;
        s.Ch.Equipment.Cloak = b;
        Inventory.Reslot(s.Ch);
        Assert.Same(a, s.Ch.Equipment.Feet);
        Assert.Null(s.Ch.Equipment.Body);
        Assert.Null(s.Ch.Equipment.Cloak);
        Assert.Contains(s.Ch.Pack, p => p == b);
        Inventory.Reslot(s.Ch);
        Assert.Same(a, s.Ch.Equipment.Feet);
    }
}
