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
    public void AnAnchorSetsTheShaftNotTheBounds()
    {
        // The bound staff: its coil leans the bounds' long axis 4 degrees off the rod; the anchor's -Y is the rod.
        var tilt = 4f * System.MathF.PI / 180f;
        var pcaLong = new System.Numerics.Vector3(System.MathF.Sin(tilt), System.MathF.Cos(tilt), 0);
        var pcaMid = new System.Numerics.Vector3(System.MathF.Cos(tilt), -System.MathF.Sin(tilt), 0);
        var rod = new System.Numerics.Vector3(0, -2f, 0); // anchor -Y, unnormalised (a scaled node)
        var (lng, mid) = WeaponSockets.ShaftAxes(pcaLong, pcaMid, rod);
        Assert.Equal(-1.0, (double)lng.Y, 5);
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Dot(lng, mid), 5);
        Assert.Equal(1.0, (double)mid.Length(), 5);
        Assert.True(mid.X > 0.99f);
        // No anchor: the bounds stand.
        Assert.Equal(pcaLong, WeaponSockets.ShaftAxes(pcaLong, pcaMid, null).Long);
        // A side axis along the shaft falls back to another square to it.
        var (l2, m2) = WeaponSockets.ShaftAxes(pcaLong, new System.Numerics.Vector3(0, 1, 0), rod);
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Dot(l2, m2), 5);
    }

    [Fact]
    public void AnAnchoredPieceSitsOnTheFistsLine()
    {
        // hand_r's mount (Arms.MountTransform): the piece's X along hand +Y, its shaft (+Y) along hand +Z, at (-25, 75, 0) mm.
        System.Numerics.Vector3 mx = new(0, 1, 0), my = new(0, 0, 1), mz = new(1, 0, 0), o = new(-0.025f, 0.075f, 0);
        var (turn, at) = WeaponSockets.FistSeat(mx, my, mz, o);
        System.Numerics.Vector3 Hand(System.Numerics.Vector3 m) => o + mx * m.X + my * m.Y + mz * m.Z;
        // The grip point lands on the pocket; the shaft runs along the fist's line (6.6 degrees off the mount's).
        var grip = Hand(at);
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(grip, WeaponSockets.FistAtR), 6);
        var shaft = Hand(System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitY, turn)) - o;
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(shaft, WeaponSockets.FistDirR), 6);
        // A point a metre up the shaft is a metre up the fist's line.
        var up = Hand(at + System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitY, turn));
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(up, WeaponSockets.FistAtR + WeaponSockets.FistDirR), 5);
        // The least turn: the piece's +Z (its edge or face) stays square to the shaft and keeps its side.
        var face = System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitZ, turn);
        Assert.True(face.Z > 0.99f);
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
