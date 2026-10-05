using System;
using Godot;
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
    /// <summary>The world darkened under the fall's choices: its own layer, between the world and
    /// the HUD, so the choices stay bright (the screen's fade sat over them).</summary>
    CanvasLayer? fallLayer;
    TextureRect? fallShade;

    void ShadeWorld(float to, double seconds)
    {
        if (fallShade == null)
        {
            fallLayer = new CanvasLayer { Layer = 5 };
            AddChild(fallLayer);
            // Dark at the edges, a little light left round her: the eye goes to where she lies.
            fallShade = new TextureRect
            {
                ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = Control.MouseFilterEnum.Ignore,
                Texture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(0.02f, 0.01f, 0.02f, 0.35f), new Color(0.02f, 0.01f, 0.02f, 0.55f), new Color(0.01f, 0.0f, 0.01f, 0.88f)], Offsets = [0f, 0.3f, 1f] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1.05f, 0.5f), Width = 256, Height = 256,
                },
                Size = new Vector2(1920, 1080), Modulate = Colors.Transparent,
            };
            fallLayer.AddChild(fallShade);
        }
        var tw = CreateTween();
        tw.TweenProperty(fallShade, "modulate:a", to, Math.Max(0.01, seconds));
    }

    /// <summary>IZoneHost: she fell in a story night; `risesLeft` is the runtime's count.</summary>
    public void StoryFall(int risesLeft, Action rise, Action letGo)
    {
        if (scene == null) { letGo(); return; }
        hud.Prompt(promptShown = null);
        ShadeWorld(1, 0.9);
        // Nothing prints over the fall while it is staged (the experience director: a loss's quest
        // line printed over the still-moving fight before its result). The notices wait, their time
        // not running, and are told whole after: on getting up, or once she wakes from the loss.
        hud.HoldToasts = true;
        // She goes down where she stands (the fight only holds her at a breath of life).
        scene.Player?.Fall();
        if (risesLeft <= 0)
        {
            // No rise left: the night is lost, and the fall says so on its own. The world stays dark
            // until the night's result is over it; it stands down (StoryNight.StandDown), her controls held.
            Wait(1.6, () => { controls.Captured = true; letGo(); });
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
            // The two choices as type on the darkened world, a click or a key choosing (no prompt box).
            hud.Fall(risesLeft, () => FallKey(Act.Confirm), () => FallKey(Act.Cancel));
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
        // Let go: the night stands down (StoryNight.StandDown) and her controls are held until its result.
        else if (a is Act.Cancel) { var l = fallLetGo; EndFall(); controls.Captured = true; l?.Invoke(); }
        return true;
    }

    /// <summary>The fall's shade lifted from under a result (the night lost): the result's own
    /// ground takes over from it.</summary>
    void LiftFall()
    {
        if (fallShade != null && fallShade.Modulate.A > 0) ShadeWorld(0, 0.6);
    }

    void EndFall()
    {
        fallRise = fallLetGo = null;
        hudMode = null;
        if (scene != null) scene.SimPaused = false;
        hud.Prompt(promptShown = null);
        hud.Fall(null);
    }

    /// <summary>Up again: dark for a breath, then the checkpoint, the light back, and the words.</summary>
    void GetUp(Action rise)
    {
        hud.Fade(1, 0.45);
        Wait(0.5, () =>
        {
            ShadeWorld(0, 0.01);
            rise();
            hud.HoldToasts = false;
            scene?.Player?.Revive();
            hud.Fade(0, 1.0);
        });
    }
}
