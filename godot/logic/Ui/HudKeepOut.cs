using System;

namespace SurvivorUnchained.Ui;

/// <summary>What the ground labels give way to under the bottom HUD (no Godot types, so it is tested): the instrument's
/// own pieces, never one rectangle around it all. The girl (her head to the foot, to the bar's left end), the bar with the
/// buff shelf over it, and the keeper; the open ground between the two statues stays the ground's (gems judge round 4: a
/// gem's name there faded to 14% under the old single rectangle). Rects are (x, y, w, h) in the 1080 px bottom-HUD space,
/// before HudBottom.Map.</summary>
public static class HudKeepOut
{
    /// <summary>The buff shelf's height over the bar (px).</summary>
    public const float Shelf = 40;

    public static (float X, float Y, float W, float H)[] Pieces((float X, float Y) girlTop, (float X, float Y, float W, float H) bar,
        (float X, float Y, float W, float H) keeper, float foot = 1080)
    {
        var girl = (girlTop.X, girlTop.Y, Math.Max(0, bar.X - girlTop.X), foot - girlTop.Y);
        var shelf = (bar.X, bar.Y - Shelf, bar.W, foot - (bar.Y - Shelf));
        return [girl, shelf, keeper];
    }

    /// <summary>Whether a label's box (grown by pad) touches any piece: it fades there.</summary>
    public static bool Under((float X, float Y, float W, float H) label, (float X, float Y, float W, float H)[] pieces, float pad = 4)
    {
        foreach (var p in pieces)
            if (label.X - pad < p.X + p.W && label.X + label.W + pad > p.X && label.Y - pad < p.Y + p.H && label.Y + label.H + pad > p.Y)
                return true;
        return false;
    }
}
