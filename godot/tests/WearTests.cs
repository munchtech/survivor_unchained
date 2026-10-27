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
        new() { Id = id, Name = id, Kind = kind, Rarity = 1, Icon = "x", Description = "A test piece for the wear slots.", Wear = wear.Length == 0 ? null : wear.ToList() };

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
    public void Every_wear_id_in_items_is_in_an_armor_index()
    {
        // (read from items.json itself: other tests register throwaway defs)
        using var doc = System.Text.Json.JsonDocument.Parse(Json.ReadContent("items.json"));
        foreach (var it in doc.RootElement.GetProperty("items").EnumerateObject())
            if (it.Value.TryGetProperty("wear", out var wear))
                foreach (var p in wear.EnumerateArray())
                    Assert.True(ArmorIndex.Shared.Find(p.GetString()!) != null, $"{it.Name} wears '{p}', which is in neither armor index");
    }

    [Fact]
    public void A_built_piece_id_without_a_dot_takes_its_slot_from_its_index_row()
    {
        Assert.Equal("top", Wear.SlotOf("plate_top_plain"));
        var body = Def("t_plate", ItemKind.Body, "plate_top_plain");
        Assert.Empty(Wear.Validate(body));
        Assert.Equal(new[] { "plate_top_plain" }, Wear.Validate(Def("t_plate_feet", ItemKind.Feet, "plate_top_plain")));
        var eq = new Equipment();
        eq.Body = new ItemInstance { Uid = "9", Def = "t_plate" };
        Assert.Equal("plate_top_plain", Wear.Of(eq, id => id == "t_plate" ? body : null)["top"]);
    }

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
    const string Index = """
    [
     {"id": "warden.top", "outfit": "warden", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["warden.top.steel"], "tuck": "armor_tuck/warden.top.bin", "hold": {"amount": 0.55, "squash": 0}},
     {"id": "warden.bottom", "outfit": "warden", "slot": "bottom", "layer": 1, "covers": ["bottom"], "meshes": ["warden.bottom.thread"], "tuck": null},
     {"id": "warden.boots", "outfit": "warden", "slot": "boots", "layer": 2, "covers": ["boots"], "meshes": ["warden.boots.steel"], "tuck": null},
     {"id": "ranger.bottom", "outfit": "ranger", "slot": "bottom", "layer": 1, "covers": ["bottom", "legwear"], "meshes": ["ranger.bottom.leather"], "tuck": null},
     {"id": "arcanist.legwear", "outfit": "arcanist", "slot": "legwear", "layer": 1, "covers": ["legwear"], "meshes": ["arcanist.legwear.sheer"], "tuck": null},
     {"id": "reaver.top", "outfit": "reaver", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["reaver.top.leather"], "tuck": null},
     {"id": "reaver.ink", "outfit": "reaver", "slot": "ink", "layer": 0, "covers": ["ink"], "meshes": ["reaver.ink.ink"], "tuck": null}
    ]
    """;

    const string Index2 = """
    [{"id": "plate_top_plain", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["plate_top_plain.steel"], "tuck": "armor_tuck/plate_top_plain.bin", "file": "res://art/armor/plate_top_plain.gltf", "tier": "plain"}]
    """;

    const string HangIndex = """
    [
     {"id": "warden.skirt", "outfit": "warden", "slot": "skirt", "layer": 1, "covers": ["skirt"], "meshes": ["warden.skirt.steel"], "tuck": null},
     {"id": "warden.belt", "outfit": "warden", "slot": "belt", "layer": 1, "covers": ["belt"], "meshes": ["warden.belt.steel"], "tuck": null},
     {"id": "ranger.belt", "outfit": "ranger", "slot": "belt", "layer": 1, "covers": ["belt"], "meshes": ["ranger.belt.leather"], "tuck": null}
    ]
    """;

    [Fact]
    public void A_skirt_does_not_hang_from_another_sources_belt()
    {
        var ix = ArmorIndex.Parse(HangIndex);
        var notes = new List<string>();
        var l = Wear.Look(W("ranger.belt"), "warden", ix, notes);
        Assert.Equal("ranger.belt", l["belt"]);
        Assert.False(l.ContainsKey("skirt"));
        Assert.Contains(notes, n => n.Contains("hangs from belt"));
    }

    [Fact]
    public void A_skirt_fills_with_its_own_belt_or_an_empty_belt_slot()
    {
        var ix = ArmorIndex.Parse(HangIndex);
        var l = Wear.Look(W(), "warden", ix);
        Assert.Equal("warden.skirt", l["skirt"]);
        Assert.Equal("warden.belt", l["belt"]);
        l = Wear.Look(W("warden.belt"), "warden", ix);
        Assert.Equal("warden.skirt", l["skirt"]);
    }

    static Dictionary<string, string> W(params string[] ids) => ids.ToDictionary(i => Wear.SlotOfId(i), i => i);

    [Fact]
    public void Index_rows_parse_with_their_hold_and_folder()
    {
        var ix = ArmorIndex.Parse(Index).Add(Index2, "armor");
        Assert.Equal(0.55, ix.Find("warden.top")!.Hold!.Amount);
        Assert.Null(ix.Find("warden.boots")!.Hold);
        Assert.Equal("top", ix.SlotOf("plate_top_plain"));
        Assert.Equal("armor", ix.Find("plate_top_plain")!.Dir);
        Assert.Equal("res://art/armor/plate_top_plain.gltf", ix.Find("plate_top_plain")!.File);
        Assert.Equal("gloves", ix.SlotOf("nobody.gloves"));
    }

    [Fact]
    public void Look_fills_from_the_calling()
    {
        var ix = ArmorIndex.Parse(Index);
        var l = Wear.Look(W(), "warden", ix);
        Assert.Equal(new Dictionary<string, string> { ["top"] = "warden.top", ["bottom"] = "warden.bottom", ["boots"] = "warden.boots" }, l);
        Assert.True(Wear.IsCallingSet(l, "warden", ix));
    }

    const string ReplIndex = """
    [
     {"id": "warden.pauldrons", "outfit": "warden", "slot": "pauldrons", "layer": 1, "covers": ["pauldrons"], "meshes": ["warden.pauldrons.steel"], "tuck": null},
     {"id": "ranger.pauldrons", "outfit": "ranger", "slot": "pauldrons", "layer": 1, "covers": ["pauldrons"], "meshes": ["ranger.pauldrons.steel"], "tuck": null},
     {"id": "plate_pauldrons_warden", "slot": "pauldrons", "layer": 1, "covers": ["pauldrons"], "meshes": ["plate_pauldrons_warden.steel"], "tuck": null, "replaces": "warden.pauldrons"}
    ]
    """;

    [Fact]
    public void A_row_that_replaces_a_calling_row_is_that_callings_fill()
    {
        var ix = ArmorIndex.Parse(ReplIndex);
        var w = Wear.Look(W(), "warden", ix);
        Assert.Equal("plate_pauldrons_warden", w["pauldrons"]);
        Assert.False(Wear.IsCallingSet(w, "warden", ix));
        Assert.Equal("ranger.pauldrons", Wear.Look(W(), "ranger", ix)["pauldrons"]);
        Assert.Equal("plate_pauldrons_warden", ix.Calling("warden")["pauldrons"]);
        Assert.Equal("warden.pauldrons", Wear.Look(new Dictionary<string, string> { ["pauldrons"] = "warden.pauldrons" }, "ranger", ix)["pauldrons"]);
    }

    [Fact]
    public void The_game_index_dresses_the_warden_in_the_brass_pauldrons_and_the_others_as_before()
    {
        ArmorIndex.Reset();
        var ix = ArmorIndex.Shared;
        Assert.Equal("warden.pauldrons", ix.Find("plate_pauldrons_warden")?.Replaces);
        Assert.Equal("plate_pauldrons_warden", Wear.Look(W(), "warden", ix)["pauldrons"]);
        foreach (var c in new[] { "ranger", "arcanist", "reaver" })
            foreach (var (slot, id) in ix.Calling(c)) Assert.Equal($"{c}.{slot}", id);
    }

    [Fact]
    public void A_displaced_arcanist_top_leaves_the_forged_gstring_under_it()
    {
        // (armor 13 g1: the plate set's designed bottom, plate_gstring_plain; it covers belt and skirt, so no belt)
        ArmorIndex.Reset();
        var ix = ArmorIndex.Shared;
        var cu = new Dictionary<string, string> { ["top"] = "plate_cuirass_plain" };
        var l = Wear.Look(cu, "arcanist", ix);
        Assert.Equal("plate_gstring_plain", l["bottom"]);
        Assert.False(l.ContainsKey("belt"));
        Assert.Equal("plate_cuirass_plain", l["top"]);
        Assert.DoesNotContain("arcanist.top", l.Values);
        var none = Wear.Look(W(), "arcanist", ix);
        Assert.Equal("arcanist.bottom", none["bottom"]);
        Assert.Equal("arcanist.top", none["top"]);
        Assert.False(none.ContainsKey("belt"));
        var l2 = Wear.Look(new Dictionary<string, string> { ["top"] = "plate_cuirass_plain", ["belt"] = "reaver.belt" }, "arcanist", ix);
        Assert.Equal("reaver.belt", l2["belt"]);
        Assert.Equal("plate_gstring_plain", l2["bottom"]);
        var w = Wear.Look(cu, "warden", ix);
        Assert.Equal("warden.bottom", w["bottom"]);
        Assert.Equal("warden.belt", w["belt"]);
        Assert.Equal("plate_cuirass_plain", w["top"]);
    }

    [Fact]
    public void An_equipped_piece_replaces_the_callings()
    {
        var ix = ArmorIndex.Parse(Index).Add(Index2, "armor");
        var l = Wear.Look(new Dictionary<string, string> { ["top"] = "plate_top_plain" }, "warden", ix);
        Assert.Equal("plate_top_plain", l["top"]);
        Assert.Equal("warden.bottom", l["bottom"]);
        Assert.False(Wear.IsCallingSet(l, "warden", ix));
    }

    [Fact]
    public void Covers_hide_what_they_cover_whatever_else_is_worn()
    {
        var ix = ArmorIndex.Parse(Index);
        var l = Wear.Look(W("ranger.bottom", "arcanist.legwear"), "warden", ix);
        Assert.Equal("ranger.bottom", l["bottom"]);
        Assert.False(l.ContainsKey("legwear"));
        Assert.Equal("warden.boots", l["boots"]);
    }

    [Fact]
    public void An_equipped_piece_wins_over_the_callings_fill()
    {
        // (the ranger's pants fill covers legwear: equipped legwear drops it, a bottom that covers only bottom comes in)
        var ix = ArmorIndex.Parse(Index);
        var notes = new List<string>();
        var l = Wear.Look(W("arcanist.legwear"), "ranger", ix, notes);
        Assert.Equal("arcanist.legwear", l["legwear"]);
        Assert.Equal("warden.bottom", l["bottom"]);
        Assert.Contains("ranger.bottom", Assert.Single(notes));
        // (no fallback: the slot is left empty, with a note)
        var bare = ArmorIndex.Parse(Index.Replace("\"warden.bottom\", \"outfit\": \"warden\", \"slot\": \"bottom\"", "\"warden.bottomx\", \"outfit\": \"warden\", \"slot\": \"bottomx\""));
        notes.Clear();
        l = Wear.Look(W("arcanist.legwear"), "ranger", bare, notes);
        Assert.Equal("arcanist.legwear", l["legwear"]);
        Assert.False(l.ContainsKey("bottom"));
        Assert.Contains("left empty", Assert.Single(notes));
    }

    [Fact]
    public void An_equipped_suit_hides_an_equipped_slot()
    {
        var ix = ArmorIndex.Parse(Index);
        var l = Wear.Look(W("ranger.bottom", "arcanist.legwear"), "ranger", ix);
        Assert.Equal("ranger.bottom", l["bottom"]);
        Assert.False(l.ContainsKey("legwear"));
    }

    [Fact]
    public void The_shipped_index_shows_equipped_legwear_on_the_ranger()
    {
        var ix = ArmorIndex.Shared;
        var l = Wear.Look(W("arcanist.legwear"), "ranger", ix);
        Assert.Equal("arcanist.legwear", l["legwear"]);
        Assert.Equal(["bottom"], ix.Find(l["bottom"])!.Covers);
    }

    [Fact]
    public void Ink_stays_with_its_calling()
    {
        var ix = ArmorIndex.Parse(Index);
        var l = Wear.Look(W("warden.top"), "reaver", ix);
        Assert.Equal("reaver.ink", l["ink"]);
        Assert.Equal("warden.top", l["top"]);
        var notes = new List<string>();
        Assert.False(Wear.Look(W("reaver.ink"), "warden", ix, notes).ContainsKey("ink"));
        Assert.Contains("ink", notes.Single());
    }

    [Fact]
    public void An_unknown_piece_is_left_off_with_a_note()
    {
        var ix = ArmorIndex.Parse(Index);
        var notes = new List<string>();
        var l = Wear.Look(W("ghost.top"), "warden", ix, notes);
        Assert.Equal("warden.top", l["top"]);
        Assert.Contains("ghost.top", Assert.Single(notes));
        Assert.Contains("no armor index", notes[0]);
    }

    [Fact]
    public void The_shipped_index_gives_every_calling_its_set()
    {
        var ix = ArmorIndex.Shared;
        foreach (var c in new[] { "warden", "arcanist", "ranger", "reaver" })
        {
            var l = Wear.Look(W(), c, ix);
            Assert.True(l.Count >= 6, c);
            Assert.All(l.Values, id => Assert.True(id.StartsWith(c + ".") || ix.Find(id)!.Replaces?.StartsWith(c + ".") == true, id));
            Assert.All(l.Values, id => Assert.NotEmpty(ix.Find(id)!.Meshes));
        }
        Assert.Equal("reaver.ink", Wear.Look(W(), "reaver", ix)["ink"]);
        Assert.Equal(0.55, ix.Find("warden.top")!.Hold!.Amount);
        Assert.Equal(0.0, ix.Find("warden.top")!.Hold!.Squash);
    }
}
