using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her left hand free for catch_breath's hair push (logic/Play/FreeHand.cs): never with a shield on the
/// forearm or a piece in the left fist, unless sheathed at a socket.</summary>
public class FreeHandTests
{
    static HeldArms Arms(string? left, string? forearm) => new("sword", left, forearm, "Idle", ["Attack"], "Heavy");
    static bool Socketed(string id) => id != "staff";

    [Fact]
    public void RightHandOnlyIsFreeDrawnOrSheathed()
    {
        Assert.True(FreeHand.Left(Arms(null, null), false, Socketed));
        Assert.True(FreeHand.Left(Arms(null, null), true, Socketed));
    }

    [Fact]
    public void ShieldOrOffhandBlocksItDrawn()
    {
        Assert.False(FreeHand.Left(Arms(null, "shield_round"), false, Socketed));
        Assert.False(FreeHand.Left(Arms("dagger", null), false, Socketed));
        Assert.False(FreeHand.Left(Arms("dagger", "shield_round"), false, Socketed));
    }

    [Fact]
    public void SheathedAtASocketFreesIt()
    {
        Assert.True(FreeHand.Left(Arms(null, "shield_round"), true, Socketed));
        Assert.True(FreeHand.Left(Arms("dagger", "shield_round"), true, Socketed));
    }

    [Fact]
    public void APieceWithNoSocketStaysInTheHandSheathed()
    {
        Assert.False(FreeHand.Left(Arms("staff", null), true, Socketed));
        Assert.False(FreeHand.Left(Arms(null, "staff"), true, Socketed));
    }
}
