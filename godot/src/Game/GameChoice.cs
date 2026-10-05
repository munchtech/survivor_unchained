using System;
using System.Collections.Generic;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* A choice the story puts to her wherever she stands (StoryChoice: Redcowl on his knee, Greymuzzle on his
 * side), staged over the live world: named, each answer on its own key, and answered from anywhere on the
 * ground (the experience director's finding: as a prompt at his side, a player across the camp stalled at
 * his sliver of health, not knowing there was a choice). A key is held a moment to choose, so a blow still
 * being pressed as he goes down never answers it; a click on an answer chooses at once. */
public partial class Game
{
    /// <summary>The keys of a choice's answers, in order: the use key, then her art's (pad B, then X).</summary>
    public static readonly Act[] ChoiceKeys = [Act.Interact, Act.Ability];
    /// <summary>Its keys count only this long after it comes up, and are held this long to choose.</summary>
    const double ChoiceArm = 0.8, ChoiceHold = 0.6;
    StoryChoice? choiceUp;
    double choiceT, choiceHeldT;
    int choiceHeld = -1;
    /// <summary>Keys already down when it came up: let go before they count.</summary>
    readonly HashSet<Act> choiceStale = new();

    /// <summary>The choice on screen while one waits and nothing is over the game; its held key.</summary>
    void UpdateChoice(double dt)
    {
        var c = zone != null && Overlay == null && cine == null && !inTransit && Battle is { Player.Alive: true } ? zone.Choice : null;
        if (c != choiceUp)
        {
            choiceUp = c;
            choiceT = choiceHeldT = 0;
            choiceHeld = -1;
            choiceStale.Clear();
            if (c != null) foreach (var a in ChoiceKeys) if (controls.Held(a)) choiceStale.Add(a);
            hud.Choice(c, ChoiceKeys, AnswerChoice);
            if (c != null) Shots.Want("choice", 1.6);
        }
        if (c == null) return;
        choiceT += dt;
        int held = -1;
        for (int i = 0; i < Math.Min(c.Answers.Count, ChoiceKeys.Length); i++)
        {
            if (!controls.Held(ChoiceKeys[i])) { choiceStale.Remove(ChoiceKeys[i]); continue; }
            if (held < 0 && !choiceStale.Contains(ChoiceKeys[i])) held = i;
        }
        if (held != choiceHeld) { choiceHeld = held; choiceHeldT = 0; }
        if (held >= 0 && choiceT >= ChoiceArm) choiceHeldT += dt;
        hud.ChoiceHeld(held, choiceHeldT / ChoiceHold);
        if (held >= 0 && choiceHeldT >= ChoiceHold) AnswerChoice(held);
    }

    /// <summary>A press of one of the choice's keys, taken and not passed on to the fight.</summary>
    bool Swallow(Act a)
    {
        controls.Pressed(a);
        return false;
    }

    /// <summary>The waiting choice answered (a held key, a click, the autopilot): its answer by place.</summary>
    public void AnswerChoice(int i)
    {
        if (zone?.Choice is not { } c || i < 0 || i >= c.Answers.Count) return;
        zone.Answer(c.Answers[i].Id);
        zone.Touched();
        UpdateChoice(0);
    }
}
