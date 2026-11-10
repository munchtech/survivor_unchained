using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 (the seats' glyphs, src/Ui/GlyphPaths.cs): every skill a calling is taught shows a line glyph of its own
/// on the bar: never the neutral mark, and no two skills of one taught build the same drawing.</summary>
public sealed class SeatGlyphTests
{
    static string Line(string id) => GlyphPaths.LinePath(GlyphPaths.ForSkill(id, Weapons.All[id].Art));

    [Fact]
    public void Every_taught_skill_has_a_line_glyph_that_is_not_the_neutral_mark()
    {
        string neutral = GlyphPaths.PathFor(GlyphPaths.Neutral);
        Assert.NotEmpty(TaughtBuilds.All);
        foreach (var (calling, build) in TaughtBuilds.All)
            foreach (var id in build.Slots.Select(s => s.Skill).Concat(build.Later))
            {
                Assert.True(Weapons.All.ContainsKey(id), $"{calling}: {id} is not a skill");
                Assert.False(Line(id) == neutral, $"{calling}: {id} shows the neutral mark (no glyph for its art \"{Weapons.All[id].Art}\")");
            }
    }

    [Fact]
    public void No_two_skills_of_one_taught_build_share_a_line_glyph()
    {
        foreach (var (calling, build) in TaughtBuilds.All)
        {
            var seen = new Dictionary<string, string>();
            foreach (var id in build.Slots.Select(s => s.Skill).Concat(build.Later).Distinct())
            {
                string path = Line(id);
                Assert.False(seen.TryGetValue(path, out var other), $"{calling}: {id} and {other} show the same glyph");
                seen[path] = id;
            }
        }
    }

    [Fact]
    public void A_line_render_draws_the_keys_own_glyph_before_a_borrowed_one()
    {
        // (Heroic Leap borrows the Leap's painting; its line is its own entry. The three taught skills had no entry and no
        // family, and drew the neutral star.)
        Assert.Equal("leap", GlyphPaths.IconKey("heroic_leap"));
        Assert.Equal("heroic_leap", GlyphPaths.LineKey("heroic_leap"));
        Assert.Equal("shield", GlyphPaths.IconKey("shield_charge"));
        Assert.NotEqual(GlyphPaths.PathFor("shield"), GlyphPaths.LinePath("shield_charge"));
        Assert.Equal("fist", GlyphPaths.IconKey("iron_vow"));
        Assert.NotEqual(GlyphPaths.PathFor("fist"), GlyphPaths.LinePath("iron_vow"));
    }

    [Fact]
    public void Sunder_and_the_Cleaver_share_an_art_and_not_a_glyph()
    {
        Assert.Equal(Weapons.All["sunder"].Art, Weapons.All["cleaver"].Art);
        Assert.NotEqual(Line("sunder"), Line("cleaver"));
        // (a skill with no line of its own shows its art's)
        Assert.Equal("slash_quake", GlyphPaths.ForSkill("groundbreaker", "slash_quake"));
    }
}
