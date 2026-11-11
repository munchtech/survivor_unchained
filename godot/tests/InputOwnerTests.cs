using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Who owns her input decides the pause and the capture, from the moment it is asked for (Codex audit
/// SU-032, SU-033; Play/InputOwner.cs, asked by src/Game's menus, storybook and seam).</summary>
public class InputOwnerTests
{
    /// <summary>SU-032: the storybook owns the pause from its fade. Pause pressed in the fade is refused, and a menu
    /// already open closing then (or under the page) does not set the fight running under it.</summary>
    [Fact]
    public void A_storybook_fading_in_refuses_menus_and_keeps_the_world_paused()
    {
        // In the fade: no player yet, the ask pending.
        Assert.True(InputOwner.MenusRefused(storybookUp: false, storybookPending: true, beginning: false));
        Assert.False(InputOwner.RunsOnClose(hudMode: null, storybookUp: false, storybookPending: true));
        // Under the page.
        Assert.True(InputOwner.MenusRefused(true, false, false));
        Assert.False(InputOwner.RunsOnClose(null, true, false));
        // Nothing holding it: menus open, and closing one lets the world run (unless a HUD mode holds it).
        Assert.False(InputOwner.MenusRefused(false, false, false));
        Assert.True(InputOwner.RunsOnClose(null, false, false));
        Assert.False(InputOwner.RunsOnClose("draft", false, false));
    }

    /// <summary>SU-032: the zone left during the fade: the page and its `then` are dropped.</summary>
    [Fact]
    public void A_storybook_whose_zone_left_in_the_fade_is_dropped()
    {
        object asked = new(), next = new();
        Assert.True(InputOwner.PageStillWanted(asked, asked));
        Assert.False(InputOwner.PageStillWanted(asked, null));
        Assert.False(InputOwner.PageStillWanted(asked, next));
    }

    /// <summary>SU-033: an Inventory opened during a hand-back's ease keeps its capture when the ease lands (it ran
    /// play input under the open menu); closed during the ease, the ease holds input until it lands.</summary>
    [Fact]
    public void A_seam_landing_never_releases_a_capture_an_open_menu_holds()
    {
        Assert.True(InputOwner.CapturedOnSeamEnd(zoneWants: false, menuOpen: true));
        Assert.False(InputOwner.CapturedOnSeamEnd(false, false));
        Assert.True(InputOwner.CapturedOnSeamEnd(true, false));
        Assert.True(InputOwner.CapturedOnMenuClose(seamRunning: true));
        Assert.False(InputOwner.CapturedOnMenuClose(false));
    }
}
