using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>ArmorUnder (armor 4 r3, F5): a top's strap undrawn under a pauldron only while the pauldrons slot holds one.</summary>
public class ArmorUnderTests
{
    const string Row = """
        [{"id": "plate_top_plain", "slot": "top", "layer": 1, "meshes": ["plate_top_plain.top.darkleather"],
          "under": {"pauldrons": {"warden.pauldrons": "armor_under/w.bin", "*": "armor_under/any.bin"}}}]
        """;

    static ArmorPiece Top() => ArmorIndex.Parse(Row, "armor").Find("plate_top_plain")!;

    [Fact]
    public void NoPauldronsDrawsTheWholeStrap()
    {
        Assert.Empty(ArmorUnder.Files(Top(), new Dictionary<string, string> { ["top"] = "plate_top_plain", ["bracers"] = "warden.bracers" }));
    }

    [Fact]
    public void AKnownPauldronUsesItsOwnCut()
    {
        Assert.Equal(new[] { "armor_under/w.bin" }, ArmorUnder.Files(Top(), new Dictionary<string, string> { ["top"] = "plate_top_plain", ["pauldrons"] = "warden.pauldrons" }));
    }

    [Fact]
    public void AnyOtherPauldronUsesTheSharedCut()
    {
        Assert.Equal(new[] { "armor_under/any.bin" }, ArmorUnder.Files(Top(), new Dictionary<string, string> { ["pauldrons"] = "new_spiked.pauldrons" }));
    }

    [Fact]
    public void ARowWithoutUnderHidesNothing()
    {
        var r = ArmorIndex.Parse("""[{"id": "warden.top", "outfit": "warden", "slot": "top", "meshes": []}]""").Find("warden.top")!;
        Assert.Null(r.Under);
        Assert.Empty(ArmorUnder.Files(r, new Dictionary<string, string> { ["pauldrons"] = "warden.pauldrons" }));
    }

    [Fact]
    public void KeepDropsOnlyTrianglesWhollyHidden()
    {
        // (four points; triangle 0-1-2 all hidden, 1-2-3 half: only the first goes)
        var pts = new[] { (0.10, 1.50, 0.0), (0.11, 1.50, 0.0), (0.10, 1.51, 0.0), (0.11, 1.40, 0.0) };
        var keys = pts.Select(p => ArmorUnder.Key(p.Item1, p.Item2, p.Item3)).ToArray();
        var file = new byte[4 + 3 * 12];
        BitConverter.GetBytes(3).CopyTo(file, 0);
        for (int i = 0; i < 3; i++)
        {
            BitConverter.GetBytes((int)Math.Round(pts[i].Item1 * 1e5)).CopyTo(file, 4 + i * 12);
            BitConverter.GetBytes((int)Math.Round(pts[i].Item2 * 1e5)).CopyTo(file, 8 + i * 12);
            BitConverter.GetBytes((int)Math.Round(pts[i].Item3 * 1e5)).CopyTo(file, 12 + i * 12);
        }
        var hidden = ArmorUnder.Read(file);
        Assert.Equal(3, hidden.Count);
        Assert.Equal(new[] { 1, 2, 3 }, ArmorUnder.Keep(new[] { 0, 1, 2, 1, 2, 3 }, keys, hidden));
        Assert.Null(ArmorUnder.Keep(new[] { 1, 2, 3 }, keys, hidden));
        Assert.Null(ArmorUnder.Keep(new[] { 0, 1, 2 }, keys, new HashSet<long>()));
    }

    [Fact]
    public void TheBuiltTopsNameTheirCuts()
    {
        // (the built index: each plate top's under-pauldron cuts are there, the shared one among them)
        foreach (var id in new[] { "plate_top_plain", "plate_top_etched", "plate_top_gilded" })
        {
            var r = ArmorIndex.Shared.Find(id);
            if (r == null) continue;
            Assert.NotNull(r.Under);
            Assert.True(r.Under!["pauldrons"].ContainsKey("*"), id);
        }
    }
}
