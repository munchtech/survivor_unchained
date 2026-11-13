using System.Linq;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-080) A status counts for the blessings that ask for one when the build can lay it now: her
/// lamps', Hand's and board's statuses are asked of the rules that lay them, not of a list beside them.</summary>
public sealed class LitStatusesTests
{
    [Fact]
    public void Frostfire_on_a_fire_skill_counts_her_chill()
    {
        // old: BuildStatuses read the skills, triggers, boons and gear only: frostfire's chill never counted
        var b = BattleTests.Arena(1);
        b.Weapons.Clear();
        b.AddWeapon("cinderfall", 1);
        Assert.Equal(School.Fire, b.Weapons.Single().School);
        Assert.DoesNotContain(StatusKind.Chill, LevelUp.BuildStatuses(b));
        b.Lamps = new LampLoadout();
        b.Lamps.Add(LampRulesTests.Rule("frostfire"));
        Assert.Contains(StatusKind.Chill, LevelUp.BuildStatuses(b));
    }

    [Fact]
    public void A_true_strikes_poison_counts_only_with_a_skill_to_strike()
    {
        var b = BattleTests.Arena(1);
        b.Weapons.Clear();
        b.Lamps = new LampLoadout();
        b.Lamps.Add(LampRulesTests.Rule("true.poison", ("stacks", 1)));
        Assert.DoesNotContain(StatusKind.Poison, LevelUp.BuildStatuses(b));
        b.AddWeapon("knifestorm", 1);
        Assert.Contains(StatusKind.Poison, LevelUp.BuildStatuses(b));
    }
}
