namespace SurvivorUnchained.Rpg;

/* bd-ui W11: the plain-C# side of the socket panel (src/Ui/ArtsScreen.cs draws it): colours by gem kind, the head note,
 * the chooser's list, the "more room" levels, a Union's halves. No Godot types, so godot/tests can check it. */

public static class SocketModel
{
    /// <summary>A gem's colour as hex: takes any skill = clear, Shield first = sapphire, else garnet.</summary>
    public static string GemHex(SupportDef g) =>
        g.Fits.Count == 0 ? "#E6EEFF" : g.Fits[0].Equals("Shield", System.StringComparison.OrdinalIgnoreCase) ? "#3F7FD8" : "#C42B3A";
}
