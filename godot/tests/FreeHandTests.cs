using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Her hands empty for catch_breath (logic/Play/FreeHand.cs): never with a piece drawn in either hand or a
/// shield on the forearm; sheathed at their sockets they are free; a piece with no socket stays in the hand.</summary>
public class FreeHandTests
{
    static HeldArms Arms(string right, string? left = null, string? forearm = null) => new(right, left, forearm, "Idle", ["Attack"], "Heavy");
    static bool Socketed(string id) => id != "staff";

    [Fact]
    public void EmptyHandsAreFree()
    {
        Assert.True(FreeHand.Both(Arms(""), false, Socketed));
        Assert.True(FreeHand.Both(Arms(""), true, Socketed));
    }

    [Fact]
    public void AnythingDrawnBlocksIt()
    {
        Assert.False(FreeHand.Both(Arms("axe"), false, Socketed));
        Assert.False(FreeHand.Both(Arms("sword", null, "shield_round"), false, Socketed));
        Assert.False(FreeHand.Both(Arms("daggers", "dagger_b"), false, Socketed));
        Assert.False(FreeHand.Both(Arms("", null, "shield_round"), false, Socketed));
    }

    [Fact]
    public void SheathedAtSocketsFreesThem()
    {
        Assert.True(FreeHand.Both(Arms("sword", null, "shield_round"), true, Socketed));
        Assert.True(FreeHand.Both(Arms("daggers", "dagger_b"), true, Socketed));
        Assert.True(FreeHand.Both(Arms("axe"), true, Socketed));
    }

    [Fact]
    public void APieceWithNoSocketStaysInTheHandSheathed()
    {
        Assert.False(FreeHand.Both(Arms("staff"), true, Socketed));
        Assert.False(FreeHand.Both(Arms("", "staff"), true, Socketed));
        Assert.False(FreeHand.Both(Arms("sword", null, "staff"), true, Socketed));
    }
}
