using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-062, SU-063) A wick's rules and its built Turn follow what is lit now: a weapon drafted onto a
/// lit path has its lamps' rules at once, and an evolution a Turn granted goes when a new layout takes the Turn away
/// (an earned one stays).</summary>
public sealed class WickGrantTests
{
    static readonly string[] Ram = ["shield_charge.ram.1", "shield_charge.ram.2", "shield_charge.ram.3", "shield_charge.ram.4"];
    static readonly string[] NoTurn = ["shield_charge.ram.1", "shield_charge.ram.2", "shield_charge.ram.3"];

    [Fact]
    public void A_cleaver_drafted_onto_laid_open_bleeds_by_it_at_once()
    {
        var b = BattleTests.Arena(4);
        b.WickPaths["cleaver"] = ["cleaver.wound.1"];
        Assert.False(b.Lamps.Has("cleaver.laid_open"));
        Assert.NotNull(b.AddWeapon("cleaver"));
        Assert.True(b.Lamps.Has("cleaver.laid_open"));
    }

    [Fact]
    public void A_turns_pile_driver_goes_when_a_layout_takes_the_turn_away()
    {
        var b = BattleTests.Arena(4, ("shield_charge", 4));
        var w = b.Weapons.Single(x => x.Id == "shield_charge");
        b.SetWickPath("shield_charge", Ram);
        Assert.Equal("pile_driver", w.Evolution?.Id);
        Assert.Equal(w.Evolution!.Triggers.Length, b.Triggers.Count(t => t.Source == "evo:pile_driver"));
        b.SetWickPath("shield_charge", NoTurn);
        Assert.Null(w.Evolution);
        Assert.DoesNotContain(b.Triggers, t => t.Source == "evo:pile_driver");
        Assert.Null(w.Wick?.Evolve);
        b.Events.Drain();
        b.SetWickPath("shield_charge", Ram);
        Assert.Equal("pile_driver", w.Evolution?.Id);
        Assert.Single(b.Events.Drain().OfType<Ev.Evolve>());
    }

    [Fact]
    public void An_earned_pile_driver_stays_whatever_the_layout()
    {
        var b = BattleTests.Arena(4, ("shield_charge", 4));
        var w = b.Weapons.Single(x => x.Id == "shield_charge");
        b.Evolve("shield_charge", "pile_driver", chest: true);
        b.SetWickPath("shield_charge", Ram);
        b.SetWickPath("shield_charge", NoTurn);
        Assert.Equal("pile_driver", w.Evolution?.Id);
    }
}
