using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-ui W9) One icon key per skill (SeatIcon.For), whatever its evolution's art says, so seat, card and tile never differ.</summary>
public sealed class SeatIconTests
{
    [Fact]
    public void An_evolved_skill_shows_its_own_glyph_not_the_neutral_mark()
    {
        Assert.Equal("shield_charge", SeatIcon.For("shield_charge", "shield_charge_slam"));
        foreach (var d in Weapons.All.Values.Where(d => d.Evolutions.Any()))
            foreach (var e in d.Evolutions)
                Assert.Equal(SeatIcon.For(d.Id, d.Art), SeatIcon.For(d.Id, e.Art));
    }

    [Fact]
    public void Every_new_key_cards_picture_key_is_its_seats_key()
    {
        foreach (var d in Weapons.All.Values) Assert.Equal(SeatIcon.For(d.Id, d.Art), LevelCards.PictureKey(d.Id));
    }

    [Fact]
    public void Bladestorm_has_its_own_whirl_glyph_not_the_leaps_arc()
    {
        var bs = Weapons.All["bladestorm"];
        string key = SeatIcon.For(bs.Id, bs.Art);
        Assert.Equal("bladestorm", key);
        Assert.True(GlyphPaths.Own(key));
        var leap = Weapons.All["heroic_leap"];
        Assert.NotEqual(GlyphPaths.PathFor(SeatIcon.For(leap.Id, leap.Art)), GlyphPaths.PathFor(key));
        // three blades and a hub: four subpaths
        Assert.Equal(4, GlyphPaths.PathFor(key).Count(c => c == 'M'));
    }

    [Fact]
    public void The_card_line_is_a_function_line_where_card_lines_json_has_one_else_the_description()
    {
        Assert.Equal("You charge 8 m behind your shield and gain a barrier of 15% of your health.", LevelCards.Line("shield_charge", Weapons.All["shield_charge"].Description));
        string vow = LevelCards.Line("iron_vow", Weapons.All["iron_vow"].Description);
        Assert.True(vow.Length < 70, vow);
        Assert.Equal(LevelCards.Line(Weapons.All["cleaver"].Description), LevelCards.Line("cleaver", Weapons.All["cleaver"].Description));
    }

    [Fact]
    public void A_storms_break_key_holds_the_bond_while_the_storm_runs()
    {
        var sim = MapSim.Survivor("warden", 12, 2, 2);
        var b = sim.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        var sunder = b.Weapons.Single(w => w.Id == "sunder");
        var storm = b.Weapons.Single(w => w.Id == "bladestorm");
        Assert.False(b.BreaksAStorm(sunder));
        storm.Channeling = true;
        Assert.True(b.BreaksAStorm(sunder));
        Assert.False(b.BreaksAStorm(storm));
    }
}
