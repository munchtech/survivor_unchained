using System;
using Godot;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* The dawn's card (H8, N24; Play.DawnCard): what the ember takes and what she keeps, on one storybook
 * page over the dawn, held until a click. The world holds still under it as under a freeze callout
 * (the sim paused, the figures and effects stilled), the HUD gone and the notices waiting; a click,
 * Enter, Space or the use key closes it once it has been up 1.0 s. */
public partial class Game
{
    DawnCardView? dawnCard;
    Action? dawnClosed;
    double dawnAt;

    /// <summary>The dawn's card is up (the autopilot clicks it through).</summary>
    public bool DawnUp => hudMode == "dawn";
    /// <summary>IZoneHost: a dialogue, a card or a menu is over the world.</summary>
    public bool ScreenUp => hudMode != null || screens.Current != null;
    /// <summary>Real seconds the dawn's card has been up.</summary>
    public double DawnFor => DawnUp ? Time.GetTicksMsec() / 1000.0 - dawnAt : 0;

    /// <summary>IZoneHost: the dawn's card, then `closed`.</summary>
    public void DawnCard(DawnCard card, Action closed)
    {
        if (scene == null || hudMode != null) { closed(); return; }
        // (--dawn-skills A,B: those names on the card, for pictures of a full night's from a --quick start that drafted none)
        if (Args.Get("dawn-skills") is string ds) card = card with { Takes = Play.DawnCard.Build(ds.Split(','), null).Takes };
        hudMode = "dawn";
        dawnClosed = closed;
        dawnAt = Time.GetTicksMsec() / 1000.0;
        scene.SimPaused = true;
        scene.Hold = 1;
        scene.FxStill = true;
        scene.Fx.Frozen = true;
        scene.Fx.Hits.Visible = false;
        hud.HoldToasts = true;
        hud.HoldTip = true;
        hud.Prompt(promptShown = null);
        controls.ClearLatches();
        dawnCard = hud.Dawn(card, DawnDown);
        GD.Print($"DAWNCARD {string.Join(" | ", card.Words())}");
        if (Args.Has("shot")) Shots.Want("dawn_card", 1.6);
    }

    /// <summary>A key while the card is up: Enter, Space or the use key closes it once it listens; every key is spent.</summary>
    bool DawnKey(Act a)
    {
        if (a is Act.Confirm or Act.Interact or Act.Dash) dawnCard?.Go();
        return true;
    }

    void DawnDown()
    {
        dawnCard = null;
        hud.Dawn(null);
        hudMode = null;
        if (scene != null)
        {
            scene.Hold = 0; scene.FxStill = false; scene.Fx.Frozen = false; scene.Fx.Hits.Visible = true;
            if (screens.Current == null && cine == null && teacher?.Current is not { Kind: CalloutKind.Freeze }) scene.SimPaused = false;
        }
        hud.HoldToasts = false;
        hud.HoldTip = false;
        controls.ClearLatches();
        if (Args.Has("shot")) Shots.Want("dawn_card_after", 0.5);
        var c = dawnClosed;
        dawnClosed = null;
        c?.Invoke();
    }
}
