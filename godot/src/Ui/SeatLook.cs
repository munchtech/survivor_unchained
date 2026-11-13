using System;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/* bd-ui W7: the key seats' pure side (no Godot: the tests compile it). A seat on cooldown keeps its icon (half
 * brightness, 60% of its colour) under a clockwise wipe over the share still to wait; a locked seat says the level it opens at. */
public static class SeatLook
{
    /// <summary>The share of the circle the cooling wipe covers, clockwise from 12 o'clock (the share not yet ready).</summary>
    public static float WipeShare(double ready) => (float)Math.Clamp(1 - ready, 0, 1);

    /// <summary>A colour pulled toward its own luma: keep = 1 whole, 0.6 sixty percent of its colour (Rec. 709 weights).</summary>
    public static (float R, float G, float B) Desaturate(float r, float g, float b, float keep)
    {
        float l = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        return (l + (r - l) * keep, l + (g - l) * keep, l + (b - l) * keep);
    }

    /// <summary>The first level at which key slot (0-based) is open (KeysAt(L) &gt; slot); for an auto slot, the first
    /// level AutosAt(L) &gt; its index among the autos. 0 when none (never).</summary>
    public static int OpensAt(int slot, int maxKeys)
    {
        bool auto = slot >= maxKeys;
        int need = auto ? slot - maxKeys : slot;
        for (int lv = 1; lv <= 99; lv++)
            if ((auto ? SkillBook.AutosAt(lv) : SkillBook.KeysAt(lv)) > need) return lv;
        return 0;
    }
}
