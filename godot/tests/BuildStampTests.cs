using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-070) A skill card's cache keys on the build: a stat changed, a skill ranked up or a new
/// fight each move the stamp, so a card never keeps a number from before.</summary>
public sealed class BuildStampTests
{
    [Fact]
    public void A_stat_a_rank_or_a_new_fight_moves_the_stamp()
    {
        // old: the card key was skill and slot alone, so none of these rebuilt the card
        var b = BattleTests.Arena(4);
        var w = b.AddWeapon("knifestorm", 1)!;
        long s0 = b.BuildStamp;
        Assert.Equal(s0, b.BuildStamp);
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, 0.2, "test"));
        long s1 = b.BuildStamp;
        Assert.NotEqual(s0, s1);
        w.Rank++;
        Assert.NotEqual(s1, b.BuildStamp);
        Assert.NotEqual(b.BuildStamp, BattleTests.Arena(4).BuildStamp);
    }
}
