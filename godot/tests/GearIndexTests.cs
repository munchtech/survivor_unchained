using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>P2 gear: with --body p1 the game reads B's built gear index (art/gear/out/BODY/gear_index.json, tools/armor/
/// gear_fit.py build) instead of A's two, and every path a row names resolves in that folder.</summary>
public class GearIndexTests
{
    const string GearDir = "gear/out/body_p1";

    const string Gear = """
    {"body": "body_p1", "body_hash": "x", "rows": [
     {"id": "warden.top", "outfit": "warden", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["warden.top.steel"],
      "file": "res://art/gear/out/body_p1/warden.top.gltf", "a_file": "godot/art/people/heroine_outfit_warden.gltf",
      "lod_file": "res://art/gear/out/body_p1/warden.lod.gltf", "tuck": "armor_tuck/warden.top.bin", "tuck_count": 996, "cover_count": 1098},
     {"id": "plate_pauldrons_warden", "outfit": null, "slot": "pauldrons", "layer": 3, "covers": ["pauldrons"], "meshes": ["plate_pauldrons_warden.pauldrons.steel"],
      "replaces": "warden.pauldrons", "file": "res://art/gear/out/body_p1/plate_pauldrons_warden.gltf", "tuck": "armor_tuck/plate_pauldrons_warden.bin"},
     {"id": "warden.lod", "outfit": "warden", "slot": null, "lod": true, "meshes": ["lod_steel", "lod_shadow"], "file": "res://art/gear/out/body_p1/warden.lod.gltf"}
    ]}
    """;

    const string A = """[{"id": "warden.top", "outfit": "warden", "slot": "top", "layer": 1, "meshes": ["warden.top.steel"], "tuck": "armor_tuck/warden.top.bin"}]""";
    const string AArmor = """[{"id": "plate_top_plain", "slot": "top", "layer": 1, "meshes": ["plate_top_plain.top.steel"], "file": "res://art/armor/plate_top_plain.gltf", "tuck": "armor_tuck/plate_top_plain.bin"}]""";

    static System.Func<string, string?> Files(bool gear) => rel => rel switch
    {
        "people/armor_index.json" => A,
        "armor/armor_index.json" => AArmor,
        GearDir + "/gear_index.json" when gear => Gear,
        _ => null,
    };

    [Fact]
    public void With_a_gear_folder_the_built_body_index_replaces_both_A_indexes()
    {
        var ix = ArmorIndex.Load(Files(true), GearDir);
        Assert.False(ix.GearMissing);
        Assert.Equal(new[] { "plate_pauldrons_warden", "warden.top" }, ix.Pieces.Keys.OrderBy(k => k).ToArray());
        Assert.Null(ix.Find("plate_top_plain"));   // (A's armor index is not read)
        Assert.Null(ix.Find("warden.lod"));        // (the calling's play-tier unit is no piece)
        Assert.All(ix.Pieces.Values, r => { Assert.Equal(GearDir, r.Dir); Assert.True(r.Gear); });
        Assert.Equal("warden.top", ix.Calling("warden")["top"]);
        Assert.Equal("warden.pauldrons", ix.Find("plate_pauldrons_warden")!.Replaces);
    }

    [Fact]
    public void A_gear_rows_paths_resolve_in_its_body_folder()
    {
        var r = ArmorIndex.Load(Files(true), GearDir).Find("warden.top")!;
        Assert.Equal("res://art/gear/out/body_p1/warden.top.gltf", r.File);
        Assert.Equal("res://art/gear/out/body_p1/armor_tuck/warden.top.bin", r.TuckPath);
        Assert.Equal("res://art/gear/out/body_p1/armor_cover/warden.top.bin", r.CoverPath);
        Assert.Equal("res://art/gear/out/body_p1/warden.lod.gltf", r.LodFile);
        Assert.Equal(996, r.TuckCount);
    }

    [Fact]
    public void Without_a_gear_folder_A_reads_as_before()
    {
        var ix = ArmorIndex.Load(Files(true));
        Assert.Equal(new[] { "plate_top_plain", "warden.top" }, ix.Pieces.Keys.OrderBy(k => k).ToArray());
        var w = ix.Find("warden.top")!;
        Assert.Equal("people", w.Dir);
        Assert.False(w.Gear);
        Assert.Equal("res://art/people/armor_tuck/warden.top.bin", w.TuckPath);
        Assert.Equal("res://art/people/armor_cover/warden.top.bin", w.CoverPath);
        Assert.Equal("res://art/armor/armor_tuck/plate_top_plain.bin", ix.Find("plate_top_plain")!.TuckPath);
    }

    [Fact]
    public void A_gear_folder_with_no_built_index_falls_back_to_A()
    {
        var ix = ArmorIndex.Load(Files(false), GearDir);
        Assert.True(ix.GearMissing);
        Assert.Equal("people", ix.Find("warden.top")!.Dir);
        Assert.NotNull(ix.Find("plate_top_plain"));
    }

    [Fact]
    public void The_built_body_p1_index_when_present_parses_with_every_row_in_its_folder()
    {
        string? text = ArmorIndex.Text($"{GearDir}/gear_index.json");
        if (text == null) return;   // (git-ignored build output: a fresh checkout has none)
        var ix = new ArmorIndex().AddGear(text, GearDir);
        Assert.True(ix.Pieces.Count >= 30);
        foreach (var c in new[] { "warden", "ranger", "arcanist", "reaver" })
            Assert.NotEmpty(ix.Calling(c));
        Assert.All(ix.Pieces.Values, r => Assert.StartsWith("res://art/gear/out/body_p1/", r.File));
    }
}
