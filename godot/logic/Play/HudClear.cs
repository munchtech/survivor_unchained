using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play;

/* Two small rules of the HUD's cards (lane E lead 9, judge 6 fix 1), pure: a floating damage number keeps clear of the text of any
 * card up (a "1202" sat on the Lamps tip's [L] key, a "139" on the boss card's "Fire"), and an unlock tip waits out a fight. */
public static class HudClear
{
    /// <summary>How far a damage number keeps from a card's text (px at 1080).</summary>
    public const float Gap = 12;
    /// <summary>The quiet an unlock tip waits for after the last blow dealt or taken (s).</summary>
    public const double TipQuiet = 2;

    public readonly record struct Box(float X0, float Y0, float X1, float Y1)
    {
        public float W => X1 - X0;
        public float H => Y1 - Y0;
        public Box Moved(float dx, float dy) => new(X0 + dx, Y0 + dy, X1 + dx, Y1 + dy);
        public bool Hits(Box o, float gap) => X0 < o.X1 + gap && X1 > o.X0 - gap && Y0 < o.Y1 + gap && Y1 > o.Y0 - gap;
    }

    /// <summary>The (dx, dy) that takes a number's box off every card rect by `gap`: for each card it is on, the shortest of up,
    /// left and right (never down: the number rises); 0,0 when it is clear. Cards are checked in turn, up to a few passes.</summary>
    public static (float Dx, float Dy) Shift(Box num, IReadOnlyList<Box> cards, float gap = Gap)
    {
        float dx = 0, dy = 0;
        for (int pass = 0; pass < 4; pass++)
        {
            bool moved = false;
            foreach (var c in cards)
            {
                var n = num.Moved(dx, dy);
                if (!n.Hits(c, gap)) continue;
                float up = n.Y1 - (c.Y0 - gap), left = n.X1 - (c.X0 - gap), right = c.X1 + gap - n.X0;
                if (up <= left && up <= right) dy -= up;
                else if (left <= right) dx -= left;
                else dx += right;
                moved = true;
            }
            if (!moved) break;
        }
        return (dx, dy);
    }

    /// <summary>An unlock tip waits while a blow was struck (dealt or taken) less than TipQuiet ago, unless it is already showing
    /// (a tip up when the fight starts may stay). `last` is the time of the last blow (negative infinity: none).</summary>
    public static bool TipWaits(double now, double last, bool showing) => !showing && now - last < TipQuiet;
}
