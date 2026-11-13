using System.Linq;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>bd-ui2: the mace stance has its own line glyph (it read as a fist).</summary>
public sealed class MaceGlyphTests
{
    [Fact]
    public void Mace_stance_maps_to_the_mace_glyph() => Assert.Equal("mace", StanceText.Glyph("mace"));

    [Fact]
    public void Twin_blades_stance_maps_to_its_own_glyph() => Assert.Equal("twin_blades", StanceText.Glyph("twin_blades"));

    [Fact]
    public void Mace_glyph_exists_in_glyphs_json()
    {
        var dir = System.AppContext.BaseDirectory;
        while (dir != null && !System.IO.File.Exists(System.IO.Path.Combine(dir, "data", "content", "glyphs.json"))) dir = System.IO.Path.GetDirectoryName(dir);
        Assert.NotNull(dir);
        var json = System.IO.File.ReadAllText(System.IO.Path.Combine(dir!, "data", "content", "glyphs.json"));
        Assert.Contains("\"mace\":", json);
        Assert.Contains("\"twin_blades\":", json);
    }

    [Fact]
    public void Road_glyphs_are_distinct_and_groundbreaker_keeps_its_painting()
    {
        // (bd-ui2) Bell of the Morning and Watch Bell, Groundbreaker and Sunder, never share an outline; no mace_c temp keys remain.
        foreach (var k in new[] { "dawn_bell", "watch_bell", "groundbreaker", "sunder", "boot", "mace" }) Assert.True(GlyphPaths.Own(k), k);
        Assert.NotEqual(GlyphPaths.PathFor("dawn_bell"), GlyphPaths.PathFor("watch_bell"));
        Assert.NotEqual(GlyphPaths.PathFor("groundbreaker"), GlyphPaths.PathFor("sunder"));
        Assert.False(GlyphPaths.Own("mace_c1") || GlyphPaths.Own("mace_c2"));
        Assert.Equal("groundbreaker", GlyphPaths.ForSkill("groundbreaker", "slash_quake"));
        Assert.Equal("slash_quake", GlyphPaths.IconKey("groundbreaker"));
        Assert.Equal("groundbreaker", GlyphPaths.LineKey("groundbreaker"));
    }

    [Fact]
    public void Mace_glyph_is_five_flanges_round_head_straight_shaft_knob_pommel_symmetric_about_the_shaft()
    {
        // (bd-ui2) subpaths: shaft (one line), pommel knob, head ring, solid inner ring, and 5 flange triangles.
        var subs = GlyphPaths.PathFor("mace").Split('M', System.StringSplitOptions.RemoveEmptyEntries);
        Assert.Equal(9, subs.Length);
        static double[] Nums(string p) => System.Text.RegularExpressions.Regex.Matches(p, @"-?\d+(\.\d+)?").Select(m => double.Parse(m.Value, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
        var shaft = Nums(subs[0]);
        Assert.Equal(4, shaft.Length); // a straight line: two points
        var flanges = subs.Skip(4).Select(Nums).ToArray();
        Assert.Equal(5, flanges.Length);
        Assert.All(flanges, f => Assert.Equal(6, f.Length)); // triangles
        // the head centre (the inner ring's middle) lies on the shaft's axis
        var inner = Nums(subs[3]);
        double cx = (inner.Where((_, i) => i % 2 == 0).Min() + inner.Where((_, i) => i % 2 == 0).Max()) / 2;
        double cy = (inner.Where((_, i) => i % 2 == 1).Min() + inner.Where((_, i) => i % 2 == 1).Max()) / 2;
        double dx = shaft[2] - shaft[0], dy = shaft[3] - shaft[1];
        double off = ((cx - shaft[0]) * dy - (cy - shaft[1]) * dx) / System.Math.Sqrt(dx * dx + dy * dy);
        Assert.True(System.Math.Abs(off) < 0.1, $"head centre {off:0.00} off the shaft axis");
        // the flange tips are symmetric about that axis: each tip's mirror lies on another tip
        var tips = flanges.Select(f => (x: f[2], y: f[3])).ToArray();
        double len = System.Math.Sqrt(dx * dx + dy * dy);
        foreach (var t in tips)
        {
            double d = ((t.x - shaft[0]) * dy - (t.y - shaft[1]) * dx) / len;
            double mx = t.x - 2 * d * dy / len, my = t.y + 2 * d * dx / len;
            Assert.Contains(tips, o => System.Math.Abs(o.x - mx) < 0.15 && System.Math.Abs(o.y - my) < 0.15);
        }
    }
}
