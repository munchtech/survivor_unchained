using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// The pad in the hands (docs/feel/SUGGESTIONS.md, S-14): the moments that should be felt, summed
/// into the two motors once a frame, clamped and rate-limited, and only when a pad is in hand.
/// The low (strong) motor is weight: a blow taken, a boss down. The high (weak) motor is snap: a
/// critical, a perfect dodge. Never per ordinary kill; at most one rumble that is not a blow on
/// her in a quarter of a second; nothing over 0.8 but a boss falling or her death.
/// </summary>
public sealed class Haptics
{
    float strong, weak, length;
    bool big, hurt;
    double now, lastSoft;
    /// <summary>Pulses asked for later (a level's two beats).</summary>
    readonly List<(double At, float Strong, float Weak, float Seconds)> later = new();

    /// <summary>A rumble asked for: the low motor, the high, how long; a blow on her (not
    /// rate-limited), and whether it may pass the ceiling (a boss's fall, her death).</summary>
    public void Add(float lowMotor, float highMotor, float seconds, bool blow = false, bool peak = false)
    {
        strong = Math.Max(strong, lowMotor);
        weak = Math.Max(weak, highMotor);
        length = Math.Max(length, seconds);
        big |= peak;
        hurt |= blow;
    }

    public void After(double seconds, float lowMotor, float highMotor, float length) => later.Add((now + seconds, lowMotor, highMotor, length));

    /// <summary>Once a frame: what was asked for, felt (or not, by the setting and the device).</summary>
    public void Update(double dt, string setting, bool pad)
    {
        now += dt;
        for (int i = later.Count - 1; i >= 0; i--)
            if (now >= later[i].At) { var l = later[i]; later.RemoveAt(i); Add(l.Strong, l.Weak, l.Seconds); }
        if (length <= 0) return;
        float s = strong, w = weak, d = length;
        bool blow = hurt, peak = big;
        strong = weak = length = 0;
        big = hurt = false;
        if (setting == "off" || !pad) return;
        if (!blow && now - lastSoft < 0.25 && !peak) return;
        if (!blow) lastSoft = now;
        float cap = peak ? 1 : 0.8f, k = setting == "low" ? 0.5f : 1;
        var pads = Input.GetConnectedJoypads();
        if (pads.Count == 0) return;
        Input.StartJoyVibration(pads[0], Math.Min(cap, w) * k, Math.Min(cap, s) * k, d);
    }
}
