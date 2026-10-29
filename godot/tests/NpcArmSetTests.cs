using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A package's arm set over the shared clips (NpcArmSet): the turn in never takes an arm past Floor from
/// hanging straight, and manifest values are clamped.</summary>
public class NpcArmSetTests
{
    [Theory]
    [InlineData(20f, 12f, 12f)]   // an arm well out: the whole ask
    [InlineData(10f, 12f, 4f)]    // close in already: only to Floor
    [InlineData(3f, 12f, 0f)]     // inside Floor: nothing
    [InlineData(80f, 50f, 30f)]   // the ask clamped to MaxIn
    public void TurnInStopsAtTheFloor(float abduction, float want, float expect) =>
        Assert.Equal((double)expect, (double)NpcArmSet.TurnIn(abduction, want), 3);

    [Fact]
    public void ParseReadsInAndWrist() => Assert.Equal((12f, 0.5f), NpcArmSet.Parse("12,0.5"));

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("x")]
    public void ParseNoneIsZero(string? s) => Assert.Equal((0f, 0f), NpcArmSet.Parse(s));

    [Fact]
    public void ParseClamps() => Assert.Equal((NpcArmSet.MaxIn, 1f), NpcArmSet.Parse("90,3"));
}
