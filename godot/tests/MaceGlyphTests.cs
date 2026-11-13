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
}
