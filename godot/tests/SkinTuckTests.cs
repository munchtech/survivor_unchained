using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>P2 gear, tuck depth as data: a look's skin tuck merged in millimetres (SkinTuck), a row's full scale from its
/// gear_index "tuck_depth_mm" (10 when it says none), and a look all at 10 mm exactly what it was.</summary>
public class SkinTuckTests
{
    const string GearDir = "gear/out/body_p1";

    const string Gear = """
    {"body": "body_p1", "body_hash": "x", "rows": [
     {"id": "warden.top", "outfit": "warden", "slot": "top", "layer": 1, "covers": ["top"], "meshes": ["warden.top.steel"],
      "file": "res://art/gear/out/body_p1/warden.top.gltf", "tuck": "armor_tuck/warden.top.bin", "tuck_count": 996},
     {"id": "plate_pauldrons_warden", "outfit": null, "slot": "pauldrons", "layer": 3, "covers": ["pauldrons"], "meshes": ["plate_pauldrons_warden.pauldrons.steel"],
      "file": "res://art/gear/out/body_p1/plate_pauldrons_warden.gltf", "tuck": "armor_tuck/plate_pauldrons_warden.bin", "tuck_depth_mm": 18.0}
    ]}
    """;

    static IEnumerable<(long Key, float T)> R(params (long, float)[] r) => r;

    /// <summary>HerWear.TuckMap before the depth was data: the largest raw mark a point, then eight bits.</summary>
    static Dictionary<long, float> Before(IEnumerable<IEnumerable<(long Key, float T)>> rows)
    {
        var at = new Dictionary<long, float>();
        foreach (var recs in rows)
            foreach (var (k, t) in recs)
                if (!at.TryGetValue(k, out var o) || t > o) at[k] = t;
        return at.ToDictionary(kv => kv.Key, kv => MathF.Round(Math.Clamp(kv.Value, 0f, 1f) * 255f) / 255f);
    }

    [Fact]
    public void A_row_reads_its_tuck_depth_and_is_10_mm_when_it_says_none()
    {
        var ix = ArmorIndex.Load(rel => rel == GearDir + "/gear_index.json" ? Gear : null, GearDir);
        Assert.Equal(18f, ix.Find("plate_pauldrons_warden")!.TuckDepth);
        Assert.Equal(10f, ix.Find("warden.top")!.TuckDepth);
        Assert.Equal(10f, new ArmorPiece { TuckDepthMm = 0 }.TuckDepth);
    }

    [Fact]
    public void A_look_all_at_10_mm_is_the_map_and_the_uniform_it_was_bit_for_bit()
    {
        var rng = new Random(7);
        float[] edge = [0f, 0.5f, 0.8f, 0.97f, 0.973f, 0.9745f, 0.98f, 0.99f, 0.994f, 0.996f, 1f, 1.2f, -0.1f, 1f / 255f, 0.0019f];
        var rows = new List<List<(long Key, float T)>>();
        for (int r = 0; r < 4; r++)
        {
            var l = new List<(long, float)>();
            for (int i = 0; i < 4000; i++)
                l.Add((rng.Next(0, 3000), rng.Next(4) == 0 ? edge[rng.Next(edge.Length)] : (float)rng.NextDouble()));
            rows.Add(l);
        }
        float look = SkinTuck.LookMm(rows.Take(3).Select(_ => 10f), under: true);
        Assert.Equal(10f, look);
        Assert.Equal(BitConverter.SingleToInt32Bits(0.010f), BitConverter.SingleToInt32Bits(SkinTuck.Uniform(look)));
        // (three pieces and the garment tuck's `under`, all 10 mm)
        var got = SkinTuck.Merge(rows.Select(l => (10f, (IEnumerable<(long, float)>)l)), look);
        var was = Before(rows);
        Assert.Equal(was.Count, got.Count);
        foreach (var (k, t) in was)
            Assert.Equal(BitConverter.SingleToInt32Bits(t), BitConverter.SingleToInt32Bits(got[k]));
        Assert.Contains(got.Values, t => t >= GarmentTuck.Gone);
        Assert.Contains(got.Values, t => t > GarmentTuck.Full && t < GarmentTuck.Gone);
    }

    [Fact]
    public void The_look_s_scale_is_its_deepest_row_s_and_goes_to_the_uniform()
    {
        Assert.Equal(18f, SkinTuck.LookMm([10f, 18f, 10f]));
        Assert.Equal(18f, SkinTuck.LookMm([18f], under: true));
        Assert.Equal(10f, SkinTuck.LookMm([]));
        Assert.Equal(6f, SkinTuck.LookMm([6f]));
        Assert.Equal(10f, SkinTuck.LookMm([6f], under: true));   // (the garment tuck's values are 10 mm marks)
        Assert.Equal(0.018f, SkinTuck.Uniform(18f), 1e-6f);
        Assert.Equal(0.010f, SkinTuck.Uniform(10f));
    }

    [Fact]
    public void A_mixed_look_merges_in_millimetres_the_deepest_a_point()
    {
        float q(float t) => SkinTuck.Quantise(t);
        var deep = R((1, 0.5f), (2, 0.98f), (3, 0.2f), (6, 1f), (8, 0.3f));          // (18 mm: 9, 18, 3.6, not drawn, 5.4)
        var base10 = R((1, 0.98f), (2, 0.98f), (3, 0.3f), (4, 0.4f), (5, 1f), (8, 1f));   // (10 mm: 10, 10, 3, 4, not drawn x2)
        var under = R((7, 0.98f), (3, 0.39f));                                       // (10 mm marks: 10, 3.9)
        float look = SkinTuck.LookMm([18f, 10f], under: true);
        var m = SkinTuck.Merge([(18f, deep), (10f, base10), (10f, under)], look);
        Assert.Equal(18f, look);

        Assert.Equal(10f / 18f, m[1], 1e-6f);                                 // (10 mm of the 10 row beats 9 of the deep one)
        Assert.Equal((10f, false), Round(SkinTuck.Read(m[1], look)));
        Assert.Equal(q(0.98f), m[2]);                                     // (the deep row's full: its mark as it is)
        Assert.Equal((18f, false), Round(SkinTuck.Read(m[2], look)));
        Assert.Equal(3.9f / 18f, m[3], 2e-3f);                                // (the garment tuck's 3.9 mm, the deepest of three)
        Assert.Equal(q(0.4f) * 10f / 18f, m[4], 1e-6f);                       // (a 10 mm row's 4 mm is 4 mm in the deep look)
        Assert.Equal(4f, SkinTuck.Read(m[4], look).Mm, 0.1f);
        Assert.Equal(10f / 18f, m[7], 1e-6f);                                 // (her skin under a laid garment: 10 mm, not 18)

        // (not drawn by the 10 mm row: discarded, and moved 10 mm as before, not the look's 18)
        Assert.Equal(2f - 10f / 18f, m[5], 1e-6f);
        Assert.Equal((10f, true), Round(SkinTuck.Read(m[5], look)));
        Assert.Equal((10f, true), Round(SkinTuck.Read(m[8], look)));      // (… the deep row's 5.4 mm there is shallower)
        Assert.Equal(1f, m[6]);                                           // (not drawn by the deep row: its mark as it is)
        Assert.Equal((18f, true), Round(SkinTuck.Read(m[6], look)));
        Assert.All(m.Values.Where(t => t <= 1f && t >= GarmentTuck.Gone), t => Assert.Equal(1f, t));

        // (a shallower depth that would read as the look's full is written as a full mark, never as not drawn)
        var close = SkinTuck.Merge([(10.02f, R((1, 0.1f))), (10f, R((1, 0.98f)))], 10.02f);
        Assert.Equal(SkinTuck.FullMark, close[1]);
        Assert.False(SkinTuck.Read(close[1], 10.02f).Gone);
    }

    static (float, bool) Round((float Mm, bool Gone) r) => (MathF.Round(r.Mm * 100f) / 100f, r.Gone);

    [Fact]
    public void The_footprint_is_10_mm_marks_whatever_the_row_s_scale()
    {
        foreach (float t in new[] { 0f, 0.3f, 0.8f, 0.98f, 0.99f, 1f })
            Assert.Equal(t, SkinTuck.Foot(t, 10f));                       // (a 10 mm row: as it was)
        // (gear_tuck.py writes a deep row's general-rule mark as mark10 / 1.8: the footprint reads mark10 back)
        Assert.Equal(0.8f, SkinTuck.Foot(0.8f / 1.8f, 18f), 1e-5f);
        Assert.Equal(0.45f, SkinTuck.Foot(0.25f, 18f), 1e-5f);
        Assert.Equal(1f, GarmentTuck.Amount(SkinTuck.Foot(0.98f / 1.8f, 18f)), 1e-5f);    // (10 mm of 18: lies all the way down)
        Assert.Equal(0.98f, SkinTuck.Foot(0.98f, 18f));                   // (18 mm: all the way, never removed by depth alone)
        Assert.Equal(0.98f, SkinTuck.Foot(0.7f, 18f));
        Assert.Equal(1f, SkinTuck.Foot(1f, 18f));                         // (not drawn stays not drawn)
        Assert.True(SkinTuck.Foot(0.98f, 18f) < GarmentTuck.Gone);
    }
}
