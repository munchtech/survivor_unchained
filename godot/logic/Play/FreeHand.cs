namespace SurvivorUnchained.Play;

/// <summary>
/// Whether her hands are empty, for a clip made for empty hands (catch_breath: her hands on her knees, then her left
/// pushing her hair back). A shield on the forearm swung across her head and throat (Armor 18, judge RJ1), and any
/// piece in a fist went through her thigh on the knee (armscheck: 41-100% of the clip, every set), so it plays only
/// when nothing is in her hands: every held piece sheathed at a socket. A piece with no socket (WeaponSockets.SocketOf
/// null: the staff) stays in the hand even sheathed.
/// </summary>
public static class FreeHand
{
    /// <param name="arms">The calling's held pieces ("" or null: none in that hand).</param>
    /// <param name="sheathed">Her pieces are at their sockets (a safe place, PlayerView's Sheath).</param>
    /// <param name="socketed">Whether a piece (an Arms id) has a sheathed socket.</param>
    public static bool Both(HeldArms arms, bool sheathed, System.Func<string, bool> socketed) =>
        Off(arms.Right, sheathed, socketed) && Off(arms.Left, sheathed, socketed) && Off(arms.Forearm, sheathed, socketed);

    static bool Off(string? piece, bool sheathed, System.Func<string, bool> socketed) =>
        string.IsNullOrEmpty(piece) || (sheathed && socketed(piece));
}
