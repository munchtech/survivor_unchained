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
