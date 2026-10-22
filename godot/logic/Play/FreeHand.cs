namespace SurvivorUnchained.Play;

/// <summary>
/// Whether her left hand is empty, for the clips that use it (catch_breath pushes her hair back with it). A shield
/// on the forearm or a piece in the left fist would swing across her head and throat (Armor 18, judge RJ1), so such
/// a clip plays only when nothing is there: no left piece, or every left piece sheathed at a socket. A piece with no
/// socket (WeaponSockets.SocketOf null: the staff) stays in the hand even sheathed.
/// </summary>
public static class FreeHand
{
    /// <param name="arms">The calling's held pieces.</param>
    /// <param name="sheathed">Her pieces are at their sockets (a safe place, PlayerView's Sheath).</param>
    /// <param name="socketed">Whether a piece (an Arms id) has a sheathed socket.</param>
    public static bool Left(HeldArms arms, bool sheathed, System.Func<string, bool> socketed) =>
        Off(arms.Left, sheathed, socketed) && Off(arms.Forearm, sheathed, socketed);

    static bool Off(string? piece, bool sheathed, System.Func<string, bool> socketed) =>
        piece == null || (sheathed && socketed(piece));
}
