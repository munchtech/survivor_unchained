using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Weapon sockets by kind (Play/WeaponSockets.cs): the kind table, the tag reader, the scabbard length from the
/// anchors or the bounds, and the clearance file with its defaults.</summary>
public class WeaponSocketsTests
{
    [Theory]
    [InlineData(WeaponKind.Shield, "back")]
    [InlineData(WeaponKind.Blade1H, "hip_blade")]
    [InlineData(WeaponKind.Blunt, "hip_loop")]
    [InlineData(WeaponKind.Axe, "hip_loop")]
    [InlineData(WeaponKind.Wand, "hip_belt")]
    [InlineData(WeaponKind.Dagger, "belt_back")]
    [InlineData(WeaponKind.Crossbow, "sling")]
    [InlineData(WeaponKind.Blade2H, "back_diag")]
    [InlineData(WeaponKind.Axe2H, "back_diag")]
    public void KindsRideInTheirSockets(WeaponKind kind, string socket) => Assert.Equal(socket, WeaponSockets.SocketOf(kind));

    [Fact]
    public void AStaffStaysInHand()
    {
        Assert.Null(WeaponSockets.SocketOf(WeaponKind.Staff));
        Assert.Null(WeaponSockets.SocketOf(WeaponKind.None));
    }

    [Theory]
    [InlineData("blade1h", WeaponKind.Blade1H)]
    [InlineData("longsword.Blade1H", WeaponKind.Blade1H)]
    [InlineData("kind=axe2h", WeaponKind.Axe2H)]
    [InlineData("snake_axe_axe2h", WeaponKind.Axe2H)]
    [InlineData("Dagger", WeaponKind.Dagger)]
    [InlineData("nonsense", WeaponKind.None)]
    [InlineData("", WeaponKind.None)]
    [InlineData(null, WeaponKind.None)]
    public void TagsNameAKind(string? tag, WeaponKind kind) => Assert.Equal(kind, WeaponSockets.Parse(tag));

    [Fact]
    public void ScabbardFollowsTheBladeFromTheBoundsFallback()
    {
        // No anchors: the sheath point is the grip (0), the tip at Length * (1 - Grip); a sword of 1.0 / 0.1 as before.
        Assert.Equal(0.8, (double)WeaponSockets.BladeLength(1.0f * (1 - 0.1f), 0, 0.10f), 5);
        Assert.True(WeaponSockets.BladeLength(1.05f * (1 - 0.22f), 0, 0.10f) < WeaponSockets.BladeLength(1.6f * (1 - 0.2f), 0, 0.10f));
    }

    [Fact]
    public void ScabbardFromAnchorsMeasuresSheathPointToTip()
    {
        Assert.Equal(0.76, (double)WeaponSockets.BladeLength(0.9f, 0.04f, 0.10f), 5);
        Assert.Equal(0.05, (double)WeaponSockets.BladeLength(0.1f, 0f, 0.10f), 5);
    }

    [Fact]
    public void ClearanceReadsTheFileAndDefaultsToZero()
    {
        var c = WeaponSockets.Clearance.Parse("{\"warden\": {\"back\": 0.012, \"hip_blade\": 0.02}, \"none\": {\"back\": 0.005}}");
        Assert.Equal(0.012, (double)c.Metres("warden", "back"), 5);
        Assert.Equal(0.02, (double)c.Metres("warden", "hip_blade"), 5);
        Assert.Equal(0f, c.Metres("warden", "sling"));
        Assert.Equal(0f, c.Metres("reaver", "back"));
        Assert.Equal(0.005, (double)c.Metres("", "back"), 5);
        Assert.Equal(0f, c.Metres(null, "sling"));
    }

    [Fact]
    public void ClearanceBadOrMissingFileIsAllZero()
    {
        Assert.Equal(0f, WeaponSockets.Clearance.Parse(null).Metres("warden", "back"));
        Assert.Equal(0f, WeaponSockets.Clearance.Parse("not json").Metres("warden", "back"));
        Assert.Equal(0f, WeaponSockets.Clearance.Parse("[1,2]").Metres("warden", "back"));
    }

    [Fact]
    public void StalkerIsTheRangerInTheFile()
    {
        var c = WeaponSockets.Clearance.Parse("{\"ranger\": {\"back\": 0.01}}");
        Assert.Equal(0.01, (double)c.Metres("stalker", "back"), 5);
    }
}
