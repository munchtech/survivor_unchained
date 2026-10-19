using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>art/weapons/weapons.json (Play/WeaponsData.cs): a row parses to a Spec's fields, its kind from the string,
/// its lean by kind unless given.</summary>
public class WeaponsDataTests
{
    const string Json = """
    {"oathbrand": {"file": "oathbrand", "length": 1.02, "kind": "blade1h", "node": null, "pistol": false, "lean": null, "grip": 0.15},
     "pike": {"file": "pike", "length": 2.0, "kind": "Staff", "node": "Cube", "pistol": false, "lean": 12, "grip": 0.4},
     "bolt": {"file": "bolt", "length": 0.8, "kind": "crossbow", "pistol": true},
     "bad": {"length": 1}, "worse": {"file": "x", "length": 0}}
    """;

    [Fact]
    public void ARowMerges()
    {
        var rows = WeaponsData.Parse(Json);
        Assert.Equal(3, rows.Count);
        var o = rows.Find(r => r.Id == "oathbrand")!;
        Assert.Equal("oathbrand", o.File);
        Assert.Equal(1.02f, o.Length);
        Assert.Equal(0.15f, o.Grip);
        Assert.Null(o.Node);
        Assert.False(o.Pistol);
    }

    [Fact]
    public void TheKindParsesAndLeanDefaultsByKind()
    {
        var rows = WeaponsData.Parse(Json);
        Assert.Equal(WeaponKind.Blade1H, rows.Find(r => r.Id == "oathbrand")!.Kind);
        Assert.Equal(35, rows.Find(r => r.Id == "oathbrand")!.Lean);
        var pike = rows.Find(r => r.Id == "pike")!;
        Assert.Equal(WeaponKind.Staff, pike.Kind);
        Assert.Equal(12, pike.Lean);
        Assert.Equal("Cube", pike.Node);
        var bolt = rows.Find(r => r.Id == "bolt")!;
        Assert.True(bolt.Pistol);
        Assert.Equal(0, bolt.Lean);
        Assert.Equal(30, WeaponsData.DefaultLean(WeaponKind.Dagger));
    }

    [Fact]
    public void ACSharpIdIsNotOverwritten()
    {
        var table = new System.Collections.Generic.Dictionary<string, string> { ["oathbrand"] = "csharp" };
        int added = WeaponsData.Merge(table, WeaponsData.Parse(Json), r => "json");
        Assert.Equal(2, added);
        Assert.Equal("csharp", table["oathbrand"]);
        Assert.Equal("json", table["pike"]);
    }

    [Fact]
    public void NothingOrJunkGivesNoRows()
    {
        Assert.Empty(WeaponsData.Parse(null));
        Assert.Empty(WeaponsData.Parse("{not json"));
        Assert.Empty(WeaponsData.Parse("[]"));
    }

    /// <summary>An item that names its art carries the art's kind too (logic can't read weapons.json): the two
    /// must agree, and the art must be a known weapon, so they can't drift apart.</summary>
    [Fact]
    public void EveryItemsArtKindMatchesItsWeaponsRow()
    {
        var path = System.IO.Path.Combine(SurvivorUnchained.Core.DataFiles.Dir, "..", "art", "weapons", "weapons.json");
        var rows = System.Linq.Enumerable.ToDictionary(WeaponsData.Parse(System.IO.File.ReadAllText(path)), r => r.Id);
        foreach (var d in SurvivorUnchained.Rpg.Items.All.Values)
        {
            if (d.Art == null || !rows.TryGetValue(d.Art, out var row)) continue;   // (a C# Arms row: not ours to check)
            Assert.Equal(row.Kind, WeaponSockets.Parse(d.ArtKind));
        }
        Assert.Contains("oathbrand", rows.Keys);
    }
}
