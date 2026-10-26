using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Weapon sockets by kind (Play/WeaponSockets.cs): the kind table, the tag reader, the scabbard length from the
/// anchors or the bounds, and the clearance file with its defaults.</summary>
public class WeaponSocketsTests
{
    [Theory]
    [InlineData("back", false)]
    [InlineData("hip_blade", true)]
    [InlineData("hip_loop", true)]
    [InlineData("hip_belt", true)]
    [InlineData("belt_back", true)]
    [InlineData("sling", false)]
    [InlineData("back_diag", false)]
    [InlineData("back_staff", false)]
    [InlineData(null, false)]
    public void OnlyWaistSocketsAreAtTheWaist(string? socket, bool waist) => Assert.Equal(waist, WeaponSockets.AtWaist(socket));

    [Fact]
    public void EverySocketIsClassified()
    {
        foreach (var s in WeaponSockets.All) Assert.Equal(s is "hip_blade" or "hip_loop" or "hip_belt" or "belt_back", WeaponSockets.AtWaist(s));
    }

    [Fact]
    public void WaistAndBackThroughTheKind()
    {
        Assert.True(WeaponSockets.AtWaist(WeaponSockets.SocketOf(WeaponKind.Blade1H)));
        Assert.False(WeaponSockets.AtWaist(WeaponSockets.SocketOf(WeaponKind.Shield)));
    }

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
    public void AnAnchorBelongsOnlyToThePieceItLiesUnder()
    {
        // daggers.glb: two pieces, Cube_004 (daggers) and Cube_004_01 (dagger_b). An anchor under one is not the other's.
        Assert.True(WeaponSockets.AnchorIsPiece("Cube_004", new[] { "Scene", "Cube_004" }));
        Assert.False(WeaponSockets.AnchorIsPiece("Cube_004_01", new[] { "Scene", "Cube_004" }));
        Assert.True(WeaponSockets.AnchorIsPiece("Cube_004_01", new[] { "Scene", "Cube_004_01", "Grip" }));
        // At the file's root (no node above it) it is no one piece's in a shared file...
        Assert.False(WeaponSockets.AnchorIsPiece("Cube_004", System.Array.Empty<string>()));
        // ...and a whole-file piece takes any anchor.
        Assert.True(WeaponSockets.AnchorIsPiece(null, System.Array.Empty<string>()));
        Assert.True(WeaponSockets.AnchorIsPiece(null, new[] { "Scene", "Cube_004" }));
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
        // The grip point lands on the pocket; the shaft runs along the fist's line (27.7 degrees off the mount's).
        var grip = Hand(at);
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(grip, WeaponSockets.FistAtR), 6);
        var shaft = Hand(System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitY, turn)) - o;
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(shaft, WeaponSockets.FistDirR), 6);
        // A point a metre up the shaft is a metre up the fist's line.
        var up = Hand(at + System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitY, turn));
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(up, WeaponSockets.FistAtR + WeaponSockets.FistDirR), 5);
        // The least turn: the piece's +Z (its edge or face) stays square to the shaft and keeps its side.
        var face = System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitZ, turn);
        Assert.True(face.Z > 0.97f);  // 0.977 on the 27.7 degree fist (was > 0.99 on the 8.2 degree one)
    }

    [Fact]
    public void TheFistsPocketIsTheHollowItsFingersCloseRound()
    {
        // In hand_r's space (+Y along the fingers, +Z the thumb's side, the palm toward -X): the pocket lies under the
        // knuckles (on the body build F0 her knuckle pivots are 100-105 mm from the wrist), the leather's 13.65 mm plus
        // the glove off the palm (-X), not at the thumb's root (31 mm); the shaft on the diagonal (27.7 deg off hand +Z, 18 Oct) so the little finger reaches it.
        var at = WeaponSockets.FistAtR;
        Assert.InRange(at.Y, 0.074f, 0.094f);
        Assert.InRange(at.X, -0.043f, -0.023f);
        Assert.InRange(at.Z, -0.020f, 0.0f);
        var dir = WeaponSockets.FistDirR;
        Assert.InRange((double)dir.Length(), 0.99999, 1.00001);
        Assert.InRange(Math.Acos(dir.Z) * 180 / Math.PI, 26.7, 28.7);
    }

    [Fact]
    public void ABladeSitsOnItsOwnPocketInTheLeanItsClipsAreKeyedTo()
    {
        // Her sword mount as held (Arms.MountTransform, Lean 35): the shaft (+Y) is hand +Z turned 35 degrees about hand +X
        // toward the fingers. The blade's pocket keeps that line's direction (the clips aim the blade by it, keyed.py
        // GRIP["sword"]), so the seat only moves the hilt, never turns it.
        float s = MathF.Sin(35 * MathF.PI / 180), c = MathF.Cos(35 * MathF.PI / 180);
        System.Numerics.Vector3 mx = new(0, c, -s), my = new(0, s, c), o = new(-0.025f, 0.075f, 0);
        var mz = System.Numerics.Vector3.Cross(mx, my);
        var pocket = WeaponSockets.PocketR(WeaponKind.Blade1H);
        Assert.NotNull(pocket);
        var (pAt, pDir) = pocket!.Value;
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(pDir, my), 6);
        var (turn, at) = WeaponSockets.FistSeat(mx, my, mz, o, pAt, pDir);
        Assert.True(System.Numerics.Quaternion.Dot(turn, System.Numerics.Quaternion.Identity) > 0.999999f);
        System.Numerics.Vector3 Hand(System.Numerics.Vector3 m) => o + mx * m.X + my * m.Y + mz * m.Z;
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(Hand(at), pAt), 6);
        // The hollow under her knuckles (100-105 mm from the wrist on the body build F0), toward the palm (-X): not the
        // old mount point.
        Assert.InRange(pAt.Y, 0.070f, 0.105f);
        Assert.InRange(pAt.X, -0.045f, -0.030f);
    }

    [Fact]
    public void OnlyFittedKindsHaveAPocket()
    {
        Assert.Equal((WeaponSockets.FistAtR, WeaponSockets.FistDirR), WeaponSockets.PocketR(WeaponKind.Staff));
        Assert.NotNull(WeaponSockets.PocketR(WeaponKind.Blade1H));
        Assert.Equal((WeaponSockets.DaggerAtR, WeaponSockets.DaggerDirR), WeaponSockets.PocketR(WeaponKind.Dagger));
        // The one-handed axe: its haft conformed to the blade's fist (anim-40).
        Assert.Equal((WeaponSockets.BladeAtR, WeaponSockets.BladeDirR), WeaponSockets.PocketR(WeaponKind.Axe));
        Assert.Equal((WeaponSockets.CrossbowAtR, WeaponSockets.CrossbowDirR), WeaponSockets.PocketR(WeaponKind.Crossbow));
        // The wand is held in the one-handed blade's fist (Made.Wand's grip is the Blade1H's, anim-40).
        Assert.Equal((WeaponSockets.BladeAtR, WeaponSockets.BladeDirR), WeaponSockets.PocketR(WeaponKind.Wand));
        foreach (var k in new[] { WeaponKind.None, WeaponKind.Shield })
            Assert.Null(WeaponSockets.PocketR(k));
    }

    [Fact]
    public void ACrossbowSitsOnItsPistolGripWithTheStockAlongTheHandAndItsTopUp()
    {
        // The plain pistol mount in her hand (Arms.MountTransform, Lean 0): mount X = hand +Y, Y = hand +Z, Z = hand +X.
        System.Numerics.Vector3 mx = new(0, 1, 0), my = new(0, 0, 1), o = new(-0.025f, 0.075f, 0);
        var mz = System.Numerics.Vector3.Cross(mx, my);
        var (pAt, pDir) = WeaponSockets.PocketR(WeaponKind.Crossbow)!.Value;
        var (turn, at) = WeaponSockets.PistolSeat(mx, my, mz, o, pAt, pDir);
        System.Numerics.Vector3 Hand(System.Numerics.Vector3 m) => o + mx * m.X + my * m.Y + mz * m.Z;
        System.Numerics.Vector3 Dir(System.Numerics.Vector3 m) => mx * m.X + my * m.Y + mz * m.Z;
        System.Numerics.Vector3 Turned(System.Numerics.Vector3 v) => Dir(System.Numerics.Vector3.Transform(v, turn));
        // The grip point on the pocket, the grip's own line (the rake in the piece) on the fist's line.
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(Hand(at), pAt), 6);
        float r = WeaponSockets.PistolRake * MathF.PI / 180;
        var grip = Turned(new System.Numerics.Vector3(0, MathF.Sin(r), MathF.Cos(r)));
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(grip, System.Numerics.Vector3.Normalize(pDir)), 5);
        // Its line is the rake itself, so the stock (+Y) runs along hand +Y (the fingers, the forearm: the bow forward)
        // and its top (+Z) out of the thumb side (hand +Z), as the plain pistol mount held it: the clips' aim is kept.
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(Turned(System.Numerics.Vector3.UnitY), System.Numerics.Vector3.UnitY), 5);
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(Turned(System.Numerics.Vector3.UnitZ), System.Numerics.Vector3.UnitZ), 5);
        // A fist's line leaning off the rake still lays the grip on it exactly, the stock square to the bow's limbs and
        // turned toward the fingers (never back up the forearm).
        var lean = System.Numerics.Vector3.Normalize(new System.Numerics.Vector3(-0.1f, 0.45f, 0.88f));
        (turn, at) = WeaponSockets.PistolSeat(mx, my, mz, o, pAt, lean);
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(Turned(new System.Numerics.Vector3(0, MathF.Sin(r), MathF.Cos(r))), lean), 5);
        Assert.True(Turned(System.Numerics.Vector3.UnitY).Y > 0.9f);
    }

    [Fact]
    public void TheMirrorIsAReflectionNearAPlainXFlip()
    {
        // Rl^T diag(-1, 1, 1) Rr off her rest skeleton: orthonormal, det -1, and within a degree of x -> -x (each axis
        // 0.4-0.5 off it).
        var m = WeaponSockets.MirrorRL;
        for (int i = 0; i < 3; i++)
            for (int j = 0; j < 3; j++)
                Assert.Equal(i == j ? 1.0 : 0.0, (double)System.Numerics.Vector3.Dot(m[i], m[j]), 4);
        double det = System.Numerics.Vector3.Dot(m[0], System.Numerics.Vector3.Cross(m[1], m[2]));
        Assert.Equal(-1.0, det, 4);
        var flip = new[] { new System.Numerics.Vector3(-1, 0, 0), System.Numerics.Vector3.UnitY, System.Numerics.Vector3.UnitZ };
        for (int i = 0; i < 3; i++)
            Assert.True(System.Numerics.Vector3.Dot(m[i], flip[i]) > MathF.Cos(1f * MathF.PI / 180));
    }

    [Fact]
    public void TheLeftDaggerPocketIsItsLineMirrored()
    {
        var l = WeaponSockets.PocketL(WeaponKind.Dagger);
        Assert.NotNull(l);
        var (at, dir) = l!.Value;
        // Mapped back by the mirror's transpose, it is its line as given in hand_r's frame.
        var m = WeaponSockets.MirrorRL;
        System.Numerics.Vector3 Back(System.Numerics.Vector3 v) => m[0] * v.X + m[1] * v.Y + m[2] * v.Z;
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(Back(at), WeaponSockets.DaggerLeftAt), 5);
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(Back(dir), System.Numerics.Vector3.Normalize(WeaponSockets.DaggerLeftDir)), 5);
        Assert.Equal(1.0, (double)dir.Length(), 5);
        // Toward her left palm (+X in hand_l, where hand_r's palm is -X), under her knuckles as the right's is.
        Assert.InRange(at.X, 0.025f, 0.045f);
        Assert.InRange(at.Y, 0.060f, 0.090f);
        // A left dagger seated on the plain left mount (Arms.MountTransform: the same as the right's, Lean 30): its grip
        // point on the left pocket and its shaft along the left line.
        float s = MathF.Sin(30 * MathF.PI / 180), c = MathF.Cos(30 * MathF.PI / 180);
        System.Numerics.Vector3 mx = new(0, c, -s), my = new(0, s, c), o = new(-0.025f, 0.075f, 0);
        var mz = System.Numerics.Vector3.Cross(mx, my);
        var (turn, pos) = WeaponSockets.FistSeat(mx, my, mz, o, at, dir);
        System.Numerics.Vector3 Hand(System.Numerics.Vector3 v) => o + mx * v.X + my * v.Y + mz * v.Z;
        Assert.Equal(0.0, (double)System.Numerics.Vector3.Distance(Hand(pos), at), 6);
        var shaft = System.Numerics.Vector3.Transform(System.Numerics.Vector3.UnitY, turn);
        Assert.Equal(1.0, (double)System.Numerics.Vector3.Dot(System.Numerics.Vector3.Normalize(Hand(shaft) - o), dir), 5);
    }

    [Fact]
    public void OnlyTheDaggerHasALeftPocketAndOnlyTheHandsHavePockets()
    {
        foreach (WeaponKind k in Enum.GetValues(typeof(WeaponKind)))
        {
            Assert.Equal(WeaponSockets.PocketR(k), WeaponSockets.Pocket(k, "hand_r"));
            Assert.Equal(WeaponSockets.PocketL(k), WeaponSockets.Pocket(k, "hand_l"));
            Assert.Null(WeaponSockets.Pocket(k, "lowerarm_l"));
            if (k != WeaponKind.Dagger) Assert.Null(WeaponSockets.PocketL(k));
        }
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
