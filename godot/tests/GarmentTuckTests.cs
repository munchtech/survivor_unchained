using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

public class GarmentTuckTests
{
    /// <summary>A flat patch of her: points every 5 mm on z = 0, normals +z, keyed by index.</summary>
    static SkinPoints Plane(int half = 20, float step = 0.005f)
    {
        var p = new List<float>();
        var n = new List<float>();
        var k = new List<long>();
        for (int i = -half; i <= half; i++)
            for (int j = -half; j <= half; j++)
            {
                p.AddRange(new[] { i * step, j * step, 0f });
                n.AddRange(new[] { 0f, 0f, 1f });
                k.Add(k.Count);
            }
        return new SkinPoints(p, n, k);
    }

    static float[] FieldWhere(SkinPoints s, Func<float, float, float> f)
    {
        var a = new float[s.Count];
        for (int i = 0; i < s.Count; i++) a[i] = f(s.P[i * 3], s.P[i * 3 + 1]);
        return a;
    }

    [Fact]
    public void Order_is_slot_maps()
    {
        var path = Path.Combine(DataFiles.Dir, "..", "..", "tools", "armor", "slot_map.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var order = doc.RootElement.GetProperty("order").EnumerateArray().Select(e => e.GetString()).ToArray();
        Assert.Equal(order, GarmentTuck.Order);
        Assert.Equal(Wear.VisualSlots.OrderBy(x => x), GarmentTuck.Order.OrderBy(x => x));
    }

    [Fact]
    public void Over_follows_the_order_and_spares_one_outfit()
    {
        ArmorPiece P(string id, string slot, string? outfit) => new() { Id = id, Slot = slot, Outfit = outfit };
        var belt = P("ranger.belt", "belt", "ranger");
        var skirt = P("warden.skirt", "skirt", "warden");
        var wbelt = P("warden.belt", "belt", "warden");
        var plate = P("plate_top_plain", "top", null);
        var ink = P("reaver.ink", "ink", "reaver");
        Assert.True(GarmentTuck.Over(belt, skirt));
        Assert.False(GarmentTuck.Over(skirt, belt));
        Assert.False(GarmentTuck.Over(wbelt, skirt));            // one outfit: fitted together
        Assert.True(GarmentTuck.Over(wbelt, plate));             // a new piece is no outfit's
        Assert.False(GarmentTuck.Over(P("plate_b", "top", null), plate));
        Assert.False(GarmentTuck.Over(belt, ink));
        Assert.False(GarmentTuck.Over(ink, skirt));
    }

    [Fact]
    public void Nearest_matches_a_brute_search()
    {
        var rng = new Random(3);
        var p = Enumerable.Range(0, 3000).Select(_ => (float)(rng.NextDouble() * 0.3 - 0.15)).ToArray();
        var s = new SkinPoints(p, Enumerable.Repeat(1f, p.Length).ToArray(), Enumerable.Range(0, 1000).Select(i => (long)i).ToArray());
        for (int q = 0; q < 200; q++)
        {
            float x = (float)(rng.NextDouble() * 0.36 - 0.18), y = (float)(rng.NextDouble() * 0.36 - 0.18), z = (float)(rng.NextDouble() * 0.36 - 0.18);
            int best = -1;
            float bd = 0.08f * 0.08f;
            for (int i = 0; i < 1000; i++)
            {
                float d = (p[i * 3] - x) * (p[i * 3] - x) + (p[i * 3 + 1] - y) * (p[i * 3 + 1] - y) + (p[i * 3 + 2] - z) * (p[i * 3 + 2] - z);
                if (d < bd) { bd = d; best = i; }
            }
            Assert.Equal(best, s.Nearest(x, y, z, 0.08f));
        }
    }

    [Fact]
    public void Split_copies_are_one_point()
    {
        var s = new SkinPoints(new[] { 0f, 0, 0, 0, 0, 0, 1, 0, 0 }, new[] { 1f, 0, 0, 0, 1, 0, 0, 0, 1 }, new long[] { 7, 7, 8 });
        Assert.Equal(2, s.Count);
        Assert.Equal((double)MathF.Sqrt(0.5f), (double)s.N[0], 4);
        Assert.Equal((double)MathF.Sqrt(0.5f), (double)s.N[1], 4);
    }

    [Fact]
    public void Field_takes_the_largest_and_spreads_falling_off()
    {
        var s = Plane();
        int c = s.ByKey[20 * 41 + 20];                           // (0, 0)
        var f = GarmentTuck.Field(s, new[] { new[] { ((long)c, 0.5f) }, new[] { ((long)c, 0.8f) } }, 0)!;
        Assert.Equal(0.8f, f[c]);
        Assert.Null(GarmentTuck.Field(s, new[] { Array.Empty<(long, float)>() }));
        var g = GarmentTuck.Field(s, new[] { new[] { ((long)c, 1f) } }, 0.02f)!;
        int at10 = s.ByKey[22 * 41 + 20];                        // 10 mm off: half
        Assert.Equal(0.5, (double)g[at10], 3);
        Assert.Equal(0f, g[s.ByKey[25 * 41 + 20]]);              // 25 mm off: none
    }

    [Fact]
    public void Lay_lies_down_by_the_footprint_never_lifts_and_removes_what_is_hidden()
    {
        var s = Plane();
        // (covered all of it at x < 0, a full 0.98; past 0.995 at x < -0.06; none from x > 0.03)
        var f = FieldWhere(s, (x, y) => x < -0.06f ? 1f : x < 0.0f ? 0.98f : x <= 0.03f ? 0.5f : 0f);
        var pos = new[]
        {
            -0.03f, 0, 0.012f,       // covered: down to Offset
            0.015f, 0, 0.012f,       // half: half way
            0.08f, 0, 0.012f,        // clear: unchanged
            -0.03f, 0.01f, 0.0001f,  // under Offset already: never lifted
            -0.08f, 0, 0.01f, -0.09f, 0, 0.01f, -0.08f, 0.01f, 0.01f,   // a hidden triangle
        };
        var idx = new[] { 0, 1, 2, 4, 5, 6 };
        var kept = GarmentTuck.Lay(s, f, pos, idx, out var anchor, out var t);
        Assert.NotNull(kept);
        Assert.Equal((double)GarmentTuck.Offset, (double)pos[2], 5);
        Assert.Equal(0.0003 + (0.012 - 0.0003) * 0.5, (double)pos[5], 4);
        Assert.Equal(0.012f, pos[8]);
        Assert.Equal(0.0001f, pos[11]);
        Assert.Equal(-0.03f, pos[0]);                            // along her normal only
        Assert.Equal(new[] { 0, 1, 2 }, kept);
        Assert.True(anchor[0] >= 0 && t[0] > 0.97f);
    }

    [Fact]
    public void Lay_leaves_an_uncovered_surface_alone()
    {
        var s = Plane();
        var f = FieldWhere(s, (x, y) => x < -0.09f ? 1f : 0f);
        var pos = new[] { 0.05f, 0, 0.01f, 0.06f, 0, 0.01f, 0.05f, 0.01f, 0.01f };
        Assert.Null(GarmentTuck.Lay(s, f, pos, new[] { 0, 1, 2 }, out _, out _));
        // (all of it hidden: one degenerate triangle keeps the surface)
        var all = FieldWhere(s, (x, y) => 1f);
        Assert.Equal(new[] { 0, 0, 0 }, GarmentTuck.Lay(s, all, pos, new[] { 0, 1, 2 }, out _, out _));
    }

    [Fact]
    public void BlendWeights_ends_are_A_and_B_and_the_middle_keeps_the_top_N()
    {
        int[] ja = [1, 2, 0, 0]; float[] wa = [0.6f, 0.4f, 0, 0];
        int[] jb = [3, 2, 0, 0]; float[] wb = [0.7f, 0.3f, 0, 0];
        var jo = new int[4]; var wo = new float[4];
        GarmentTuck.BlendWeights(ja, wa, jb, wb, 0f, jo, wo);
        Assert.Equal(new[] { 1, 2 }, jo.Take(2));
        Assert.Equal(0.6, wo[0], 4);
        GarmentTuck.BlendWeights(ja, wa, jb, wb, 1f, jo, wo);
        Assert.Equal(new[] { 3, 2 }, jo.Take(2));
        Assert.Equal(0.7, wo[0], 4);
        GarmentTuck.BlendWeights(ja, wa, jb, wb, 0.5f, jo, wo);
        Assert.Equal(1.0, wo.Sum(), 4);
        Assert.Equal(2, jo[0]);   // bone 2: 0.2 + 0.15 = 0.35, ties bone 3 (0.35), beats bone 1 (0.3); first seen wins
        var j2 = new int[2]; var w2 = new float[2];
        GarmentTuck.BlendWeights(ja, wa, jb, wb, 0.5f, j2, w2);
        Assert.Equal(1.0, w2.Sum(), 4);
        Assert.DoesNotContain(1, j2);
    }
}
