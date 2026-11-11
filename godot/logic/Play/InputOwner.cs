namespace SurvivorUnchained.Play;

/* Who owns her input, and so the world's pause and the controls' capture (Codex audit SU-032, SU-033).
 * Whoever owns input decides, from the moment it is asked for: a storybook owns the pause from its fade,
 * not from when its player exists; a menu open owns the capture, and a hand-back's ease (the seam) holds
 * it until it lands, then gives it to whoever owns input then. The game (src/Game) asks these. */
public static class InputOwner
{
    /// <summary>A storybook up, or asked for and still fading in, or the story's beginning: menus are refused
    /// (Pause opened in the fade, then closed, ran the fight under the page).</summary>
    public static bool MenusRefused(bool storybookUp, bool storybookPending, bool beginning) =>
        storybookUp || storybookPending || beginning;

    /// <summary>A menu closed (or another hold let go): the world runs again only if nothing else holds it (no
    /// HUD mode up, no storybook up or fading in).</summary>
    public static bool RunsOnClose(string? hudMode, bool storybookUp, bool storybookPending) =>
        hudMode == null && !storybookUp && !storybookPending;

    /// <summary>A storybook's fade ended: it plays (and its `then` runs after it) only if the zone that asked
    /// for it is still the one up. Left during the fade, both are dropped: its `then` drives that zone.</summary>
    public static bool PageStillWanted(object? askedIn, object? now) => askedIn != null && ReferenceEquals(askedIn, now);

    /// <summary>A menu closed: the capture is let go, unless a hand-back's ease still holds it (it lands later and
    /// decides then).</summary>
    public static bool CapturedOnMenuClose(bool seamRunning) => seamRunning;

    /// <summary>A hand-back's ease landed (or gave way): the capture the zone asked for, or held if a menu is
    /// open (a menu opened during the ease keeps its capture; play input never runs under it).</summary>
    public static bool CapturedOnSeamEnd(bool zoneWants, bool menuOpen) => zoneWants || menuOpen;
}
