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
        // (Butcher's Cleaver shows its art's painting, slash_heavy.png; its line is its own entry. Heroic Leap, Shield
        // Charge and Iron Vow borrowed the Leap's, the shield's and the fist's paintings until they had their own.)
        Assert.Equal("slash_heavy", GlyphPaths.IconKey("butchers_cleaver"));
        Assert.Equal("butchers_cleaver", GlyphPaths.LineKey("butchers_cleaver"));
        foreach (var key in new[] { "heroic_leap", "shield_charge", "iron_vow", "sunder" })
        {
            Assert.Equal(key, GlyphPaths.IconKey(key));
            Assert.Equal(key, GlyphPaths.LineKey(key));
        }
        Assert.NotEqual(GlyphPaths.PathFor("shield"), GlyphPaths.LinePath("shield_charge"));
        Assert.NotEqual(GlyphPaths.PathFor("fist"), GlyphPaths.LinePath("iron_vow"));
    }

    static string GodotRoot()
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? System.IO.Directory.GetCurrentDirectory();
    }

    /// <summary>The painted icon a skill shows on every screen: the key ForSkill gives, through IconKey.</summary>
    static string Painted(string id) => GlyphPaths.IconKey(GlyphPaths.ForSkill(id, Weapons.All[id].Art));

    [Fact]
    public void The_wardens_skills_and_the_cleaver_each_show_a_painting_of_their_own()
    {
        // (picked by SKILL, not by its art: Sunder and Butcher's Cleaver are both slash_heavy and showed one painting)
        string[] skills = ["sunder", "groundbreaker", "heroic_leap", "shield_charge", "iron_vow", "watch_bell", "cleaver"];
        var keys = skills.Select(Painted).ToList();
        Assert.Equal(keys.Count, keys.Distinct().Count());
        // (none shows the Leap's, the shield's or the fist's painting any more)
        Assert.DoesNotContain("leap", keys);
        Assert.DoesNotContain("shield", keys);
        Assert.DoesNotContain("fist", keys);
        Assert.Equal("sunder", Painted("sunder"));
        Assert.Equal("slash_heavy", Painted("cleaver"));
        var missing = keys.Where(k => !System.IO.File.Exists(System.IO.Path.Combine(GodotRoot(), "art", "ui", "icons", "glyph_color", k + ".png"))).ToList();
        Assert.True(missing.Count == 0, "no painting at art/ui/icons/glyph_color/ for: " + string.Join(", ", missing));
    }

    [Fact]
    public void Sunder_and_the_Cleaver_share_an_art_and_not_a_glyph()
    {
        Assert.Equal(Weapons.All["sunder"].Art, Weapons.All["cleaver"].Art);
        Assert.NotEqual(Line("sunder"), Line("cleaver"));
        // (a skill with no line of its own shows its art's; bd-ui2: Groundbreaker has its own now, its painting stays slash_quake's)
        Assert.Equal("slash_quake", GlyphPaths.ForSkill("no_such_skill", "slash_quake"));
        Assert.Equal("groundbreaker", GlyphPaths.ForSkill("groundbreaker", "slash_quake"));
    }

    [Fact]
    public void An_arena_offers_card_shows_the_skills_own_glyph()
    {
        // (the draft's offers carry the skill's ART as their icon, Sim/LevelUp: Sunder's and the Cleaver's are the same)
        string art = Weapons.All["sunder"].Art;
        foreach (var kind in new[] { Sim.OfferKind.Weapon, Sim.OfferKind.Rank, Sim.OfferKind.Hone, Sim.OfferKind.Evolve })
        {
            Assert.Equal("sunder", GlyphPaths.ForOffer(new Sim.Offer { Kind = kind, Id = "sunder", Icon = art }));
            Assert.Equal("butchers_cleaver", GlyphPaths.ForOffer(new Sim.Offer { Kind = kind, Id = "cleaver", Icon = art }));
            // (a skill with no glyph of its own: the art it carries, an evolution's where it has one)
            Assert.Equal("slash_quake", GlyphPaths.ForOffer(new Sim.Offer { Kind = kind, Id = "no_such_skill", Icon = "slash_quake" }));
            Assert.Equal("groundbreaker", GlyphPaths.ForOffer(new Sim.Offer { Kind = kind, Id = "groundbreaker", Icon = "slash_quake" }));
        }
        // a union: the skill it becomes
        var un = Unions.All[0];
        Assert.Equal(GlyphPaths.ForSkill(un.Into, Weapons.All[un.Into].Art),
            GlyphPaths.ForOffer(new Sim.Offer { Kind = Sim.OfferKind.Union, Id = un.Id, Icon = Weapons.All[un.Into].Art }));
        // a passive, a blessing, a respite: the icon it carries, whatever its id
        Assert.Equal("heart", GlyphPaths.ForOffer(new Sim.Offer { Kind = Sim.OfferKind.Heal, Id = "heal", Icon = "heart" }));
        Assert.Equal("slash_heavy", GlyphPaths.ForOffer(new Sim.Offer { Kind = Sim.OfferKind.Boon, Id = "sunder", Icon = "slash_heavy" }));
    }
}
