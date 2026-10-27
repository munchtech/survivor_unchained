using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A package manifest's walk (NpcWalks): "lurch" is the crowd's zombie walk; anything else keeps the townsfolk's.</summary>
public class NpcWalksTests
{
    [Fact]
    public void LurchIsTheZombieWalk() => Assert.Equal("Zombie_Walk_Fwd_Loop", NpcWalks.GameClip(NpcWalks.Lurch));

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("stroll")]
    public void OtherWalksKeepTheFolkWalk(string? walk) => Assert.Null(NpcWalks.GameClip(walk));
}
