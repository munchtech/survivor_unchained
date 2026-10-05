using System;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* A fall in a story night, staged (docs/design/STORY_NIGHTS_AND_TIME.md, "Falling and getting up";
 * the owner: one rise a fight in Act 1, none later without the rise's power). The night holds her
 * (StoryNight: nothing reaches her) while the picture darkens; with a rise left, two choices wait
 * on the screen, no page: get up, or let the night go. Getting up is a short fade and she is at
 * the checkpoint; letting it go, or falling with no rise left, is the night lost, and its result
 * follows (then Chid's bench, a day on). */
public partial class Game
{
    Action? fallRise, fallLetGo;

    /// <summary>IZoneHost: she fell in a story night; `risesLeft` is the runtime's count.</summary>
    public void StoryFall(int risesLeft, Action rise, Action letGo)
    {
        if (scene == null) { letGo(); return; }
        hud.Prompt(promptShown = null);
        hud.Fade(0.55f, 0.9);
        if (risesLeft <= 0)
        {
            // No rise left: the night is lost, and the fall says so on its own.
            Wait(1.6, () => { hud.Fade(0, 0.6); letGo(); });
            return;
        }
        // The autopilot (runs and pictures) gets up, as a player mostly would.
        if (auto != null && !Args.Has("choose")) { Wait(1.4, () => GetUp(rise)); return; }
        Wait(0.9, () =>
        {
            if (scene == null) return;
            fallRise = rise;
            fallLetGo = letGo;
            hudMode = "fall";
            scene.SimPaused = true;
            controls.ClearLatches();
            hud.Prompt(new PromptView(controls.UsingPad ? "A" : KeyLabel("interact"), "Get up", "",
                $"{KeyLabel("cancel")}: Let the night go", null, Act.Confirm));
            Shots.Want("fall", 0.6);
            // --choose rise|letgo: the choice made for a run, after the card has been seen.
            if (Args.Get("choose") is string ch) Wait(2.0, () => { if (hudMode == "fall") FallKey(ch == "letgo" ? Act.Cancel : Act.Confirm); });
        });
    }

    /// <summary>The keys while the fall's choices wait: confirm (or the use key) gets her up, back lets
    /// the night go; nothing else.</summary>
    bool FallKey(Act a)
    {
        if (a is Act.Confirm or Act.Interact) { var r = fallRise; EndFall(); if (r != null) GetUp(r); }
        else if (a is Act.Cancel) { var l = fallLetGo; EndFall(); hud.Fade(0, 0.6); l?.Invoke(); }
        return true;
    }

    void EndFall()
    {
        fallRise = fallLetGo = null;
        hudMode = null;
        if (scene != null) scene.SimPaused = false;
        hud.Prompt(promptShown = null);
    }

    /// <summary>Up again: dark for a breath, then the checkpoint, the light back, and the words.</summary>
    void GetUp(Action rise)
    {
        hud.Fade(1, 0.45);
        Wait(0.5, () =>
        {
            rise();
            hud.Fade(0, 1.0);
        });
    }
}
