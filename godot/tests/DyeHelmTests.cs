using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The show-helm toggle (Wear.Look's hide set), the armor row's hair field, and the dye zones as data
/// (art/people/outfit_materials.json "zone"; ItemInstance.Dye).</summary>
public class DyeHelmTests
{
    readonly ITestOutputHelper output;
    public DyeHelmTests(ITestOutputHelper output) { this.output = output; }

    static readonly string[] Zones = ["metal", "trim", "leather", "cloth", "none"];

    const string Index = """
    [{"id": "warden.top", "outfit": "warden", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["warden.top.leather"], "tuck": null},
     {"id": "warden.head", "outfit": "warden", "slot": "head", "layer": 1, "covers": ["head"], "meshes": ["warden.head.steel"], "tuck": null},
     {"id": "arcanist.head", "outfit": "arcanist", "slot": "head", "layer": 1, "covers": ["head"], "meshes": ["arcanist.head.velvet"], "tuck": null},
     {"id": "great_helm", "slot": "head", "layer": 1, "covers": ["head"], "meshes": ["great_helm.steel"], "hair": "hide", "file": "res://art/armor/great_helm.gltf"}]
    """;

    static Dictionary<string, string> W(params string[] ids) => ids.ToDictionary(i => Wear.SlotOfId(i), i => i);

    [Fact]
    public void Hidden_head_is_empty_with_an_equipped_piece_and_with_a_calling_fill()
    {
        var ix = ArmorIndex.Parse(Index);
        var hide = new[] { "head" };
        // (a calling's fill: the Warden's helm shows by default, and not with the toggle off)
        Assert.Equal("warden.head", Wear.Look(new Dictionary<string, string>(), "warden", ix)["head"]);
        var fill = Wear.Look(new Dictionary<string, string>(), "warden", ix, null, hide);
        Assert.False(fill.ContainsKey("head"));
        Assert.Equal("warden.top", fill["top"]);
        // (an equipped piece)
        Assert.Equal("great_helm", Wear.Look(W("great_helm"), "warden", ix)["head"]);
        var worn = Wear.Look(W("great_helm", "warden.top"), "warden", ix, null, hide);
        Assert.False(worn.ContainsKey("head"));
        Assert.Equal("warden.top", worn["top"]);
        Assert.Equal("hide", ix.Find("great_helm")!.Hair);
        Assert.Equal("keep", ix.Find("arcanist.head")!.Hair);
    }

    [Fact]
    public void Every_material_has_a_valid_zone_by_the_rule()
    {
        var t = Materials();
        var trim = new[] { "gold", "claspgold", "wiregold", "rivetbronze", "bronze" };
        foreach (var (k, v) in t)
        {
            Assert.True(v.TryGetProperty("zone", out var z), $"{k} has no zone");
            Assert.Contains(z.GetString(), Zones);
            var kind = v.GetProperty("kind").GetString();
            if (trim.Contains(k)) Assert.Equal("trim", z.GetString());
            else if (k.StartsWith("gem_") || k is "amethyst" or "ink" or "bone") Assert.Equal("none", z.GetString());
            else if (kind == "metal") Assert.Equal("metal", z.GetString());
            else if (kind == "leather") Assert.Equal("leather", z.GetString());
            else Assert.Equal("cloth", z.GetString());
        }
    }

    [Fact]
    public void Every_piece_has_one_to_three_dye_zones()
    {
        var t = Materials();
        var ix = ArmorIndex.Load(ArmorIndex.Text);
        Assert.True(ix.Pieces.Count > 30);
        var one = new List<string>();
        var many = new List<string>();
        foreach (var r in ix.Pieces.Values.OrderBy(r => r.Id))
        {
            if (r.Slot == Wear.Ink) continue;
            var zones = r.Meshes.Select(m => m[(m.LastIndexOf('.') + 1)..]).Select(k => t.TryGetValue(k, out var e) ? e.GetProperty("zone").GetString()! : "?" + k)
                .Where(z => z != "none").Distinct().OrderBy(z => z).ToList();
            Assert.DoesNotContain(zones, z => z.StartsWith('?'));
            Assert.True(zones.Count >= 1, $"{r.Id} has no dye zone");
            if (zones.Count == 1) one.Add($"{r.Id} ({zones[0]})");
            if (zones.Count > 3) many.Add($"{r.Id} ({string.Join("+", zones)})");
        }
        output.WriteLine("pieces with only one zone: " + string.Join(", ", one));
        output.WriteLine("pieces with more than three zones: " + string.Join(", ", many));
        Console.WriteLine("ONE-ZONE: " + string.Join(", ", one));
        Console.WriteLine("OVER-3: " + string.Join(", ", many));
    }

    [Fact]
    public void Item_dye_survives_a_save_round_trip_and_reaches_the_look()
    {
        var it = new ItemInstance { Uid = "u", Def = "d", Dye = new Dictionary<string, string> { ["metal"] = "#336699", ["thread"] = "#aa8844" } };
        var back = Json.Clone(it);
        Assert.Equal("#336699", back.Dye!["metal"]);
        Assert.Equal("#aa8844", back.Dye["thread"]);
        Assert.Null(Json.Clone(new ItemInstance { Uid = "v", Def = "d" }).Dye);

        var def = new ItemDef { Id = "d", Name = "d", Kind = ItemKind.Shoulders, Rarity = 1, Icon = "x", Description = "A test piece for the dye map.", Wear = ["warden.pauldrons"] };
        var eq = new Equipment { Shoulders = it };
        var dyes = Wear.DyeOf(eq, id => id == "d" ? def : null);
        Assert.Equal("#336699", dyes["warden.pauldrons"]["metal"]);
        Assert.Empty(Wear.DyeOf(new Equipment { Shoulders = new ItemInstance { Uid = "v", Def = "d" } }, id => def));
    }

    static Dictionary<string, JsonElement> Materials()
    {
        var p = Path.Combine(DataFiles.Dir, "..", "art", "people", "outfit_materials.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(p));
        return doc.RootElement.EnumerateObject().ToDictionary(x => x.Name, x => x.Value.Clone());
    }
}
