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
}
