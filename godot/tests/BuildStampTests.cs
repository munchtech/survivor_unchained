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
    [Fact]
    public void The_reaver_hand_flipping_below_half_moves_the_stamp()
    {
        // (Codex audit 11 L1) old: the Hand's area bonus moved the card's radius but not its key
        var b = BattleTests.Arena(3, ("cleaver", 1));
        b.Lamps = new LampLoadout();
        b.Calling = "reaver";
        Assert.Equal(1, b.HandAreaMul(b.Weapons[0]));
        long s0 = b.BuildStamp;
        b.Player.Hp = b.MaxHp * 0.4;
        Assert.NotEqual(1, b.HandAreaMul(b.Weapons[0]));
        Assert.NotEqual(s0, b.BuildStamp);
        b.Player.Hp = b.MaxHp;
        Assert.Equal(s0, b.BuildStamp);
    }
}
