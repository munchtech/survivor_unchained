using System;

namespace SurvivorUnchained.Ui;

/// <summary>The trail behind a bar's fill: what was just lost, held a moment, then gone (no Godot types, so it is
/// tested). ONE rule for every bar that has a trail (her life, the strap under her, a boss's or a story bar), and it
/// runs by TIME in the HUD's own frame, never by how often the bar is fed: a bar fed once still settles, and the
/// frame rate does not change its pace (M4 lead 7: the boss bar's trail stepped 2 px per feed, so a bar staged once
/// at 6 of 10 read "half the bar is gold" for good, and a real one drained twice as fast at 120 fps).
/// The rule: the trail is never under the fill; a bar that appears, changes to another bar, or heals has NO trail
/// (Snap: nothing was lost on screen); after a blow it holds for Hold seconds, counted from when it parted from the
/// fill (later blows do not restart the wait, or a steady beating would hang it), then closes at Rate bars a
/// second. So the longest a trail can stand is Hold + 1 / Rate.</summary>
public struct BarTrail
{
    /// <summary>Seconds a trail holds after it parts from the fill, and how fast it then closes (bars per second).</summary>
    public const float Hold = 0.35f, Rate = 1.6f;

    float wait;
    bool fed;

    /// <summary>Where the trail stands (0..1 of the bar): the fill, or above it while a loss shows.</summary>
    public float At { get; private set; }

    /// <summary>No trail: the bar appeared, became another bar, or is held at a value.</summary>
    public void Snap(float fill)
    {
        At = Clean(fill);
        wait = 0;
        fed = true;
    }

    /// <summary>A frame: the fill now and the seconds since the last. Returns where the trail stands.</summary>
    public float Step(float fill, float dt)
    {
        fill = Clean(fill);
        if (!fed || At <= fill) { Snap(fill); return At; }
        wait += Math.Max(0, dt);
        if (wait > Hold) At = Math.Max(fill, At - Math.Max(0, dt) * Rate);
        if (At <= fill) wait = 0;
        return At;
    }

    static float Clean(float v) => float.IsNaN(v) ? 0 : Math.Clamp(v, 0, 1);
}
