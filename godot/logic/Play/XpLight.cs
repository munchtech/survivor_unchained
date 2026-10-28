using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play;

/// <summary>
/// UI 18, the Drowned Girl's experience (--hud drowned; the owner's pick (c): "no XP on screen until it moves"). At
/// rest nothing shows. A gain runs a cool light along her hair and the river from her hair (0) to the meter's
/// fraction (the eddy = full) in Run seconds, holds it there Hold seconds, and fades it in Fade. Gains batch: a new run
/// starts at most once every Gap seconds; while gains keep coming the held light stays up and its front slides forward,
/// so in a fight it reads as a meter. A level-up lights all of her hair and the river for its moment (Whole), and the
/// run starts again from her hair on the next gain. By day it is her experience, by night the ember; a change of
/// either (or a loss: a death's toll, a new night) puts it out without a word. Pure: DgRiver draws what it says.
/// </summary>
public sealed class XpLight
{
    public const double Run = 0.6, Hold = 1.5, Fade = 0.5, Gap = 1.0;
    /// <summary>A level-up's light: up in WholeUp, held to WholeHold, gone at WholeEnd (seconds).</summary>
    public const double WholeUp = 0.12, WholeHold = 0.45, WholeEnd = 1.15;
    /// <summary>The held light coming back up when a gain catches it fading (seconds from 0 to full).</summary>
    public const double Relight = 0.15;
    /// <summary>The front sliding on to a newer fraction while held (per second, exponential).</summary>
    public const double Slide = 7;

    enum Phase { Rest, Run, Hold, Fade }
    Phase phase;
    double t, target, sinceRun = 99, wholeT = 99, strength;
    bool pending, known, ember;
    double lastF;
    int lastLv;

    /// <summary>Where the front stands (a fraction of the run, 0 her hair, 1 the eddy).</summary>
    public double Front { get; private set; }
    /// <summary>The run's light (its tail and its front), 0..1.</summary>
    public double Strength => strength;
    /// <summary>A level-up's light over all of it, 0..1.</summary>
    public double Whole => wholeT < WholeEnd ? WholeAt(wholeT) : 0;
    /// <summary>Anything lit: false at rest (the shader does nothing).</summary>
    public bool Lit => strength > 0 || Whole > 0;
    /// <summary>A level-up was seen at the last Feed (the HUD names it and plays its sound once).</summary>
    public bool Rose { get; private set; }

    static double WholeAt(double t) => t < WholeUp ? t / WholeUp : t < WholeHold ? 1 : Math.Max(0, 1 - (t - WholeHold) / (WholeEnd - WholeHold));

    /// <summary>What the meter reads now (fraction 0..1 of this level, the level, night or day). Call it every
    /// frame; it lights only on change.</summary>
    public void Feed(double fraction, int level, bool ember)
    {
        double f = Math.Clamp(fraction, 0, 1);
        Rose = false;
        if (!known || ember != this.ember || level < lastLv)
        {
            Out();
            known = true; this.ember = ember; lastLv = level; lastF = f; target = f;
            return;
        }
        if (level > lastLv)
        {
            // the whole sculpture lights; the run starts again from her hair on the next gain
            Rose = true;
            phase = Phase.Rest; strength = 0; pending = false;
            wholeT = 0; sinceRun = 0;
            target = f; Front = 0;
        }
        else if (f > lastF + 1e-5) Gain(f);
        else if (f < lastF - 1e-5) { target = f; Front = Math.Min(Front, f); }
        lastLv = level; lastF = f;
    }

    void Out()
    {
        phase = Phase.Rest; strength = 0; pending = false; wholeT = 99; Front = 0; t = 0;
    }

    void Gain(double f)
    {
        target = f;
        switch (phase)
        {
            case Phase.Rest:
                if (sinceRun >= Gap && Whole <= 0) Start(); else pending = true;
                break;
            case Phase.Run: break;                       // the run stretches to the newer fraction
            case Phase.Hold: t = 0; break;               // stays up; the front slides on
            case Phase.Fade: phase = Phase.Hold; t = 0; break;  // comes back up where it is
        }
    }

    void Start()
    {
        phase = Phase.Run; t = 0; sinceRun = 0; pending = false; Front = 0;
    }

    /// <summary>The run's front at u (0..1 of Run): quick out of her hair, easing into the hold.</summary>
    public static double Ease(double u) { u = Math.Clamp(u, 0, 1); return 1 - (1 - u) * (1 - u) * (1 - u); }

    public void Step(double dt)
    {
        if (dt <= 0) return;
        sinceRun += dt;
        if (wholeT < WholeEnd) wholeT += dt;
        if (pending && phase == Phase.Rest && sinceRun >= Gap && Whole <= 0) Start();
        switch (phase)
        {
            case Phase.Rest: strength = 0; break;
            case Phase.Run:
                t += dt;
                strength = Math.Min(1, strength + dt / 0.08);
                Front = target * Ease(t / Run);
                if (t >= Run) { phase = Phase.Hold; t = 0; Front = target; }
                break;
            case Phase.Hold:
                t += dt;
                strength = Math.Min(1, strength + dt / Relight);
                Front += (target - Front) * (1 - Math.Exp(-Slide * dt));
                if (t >= Hold) { phase = Phase.Fade; t = 0; }
                break;
            case Phase.Fade:
                t += dt;
                Front += (target - Front) * (1 - Math.Exp(-Slide * dt));
                strength = Math.Min(strength, Math.Max(0, 1 - t / Fade));
                if (t >= Fade) { phase = Phase.Rest; strength = 0; }
                break;
        }
    }

    /// <summary>Pictures (--hud-pin xp=...): the light as it stands sec seconds after a gain to f from rest (or,
    /// rise: after a level-up).</summary>
    public static XpLight Posed(double f, double sec, bool rise = false)
    {
        var x = new XpLight();
        x.Feed(rise ? 0.9 : 0, 1, true);
        x.Step(5);
        x.Feed(f, rise ? 2 : 1, true);
        for (double k = 0; k < sec - 1e-9; k += 1 / 120.0) x.Step(Math.Min(1 / 120.0, sec - k));
        return x;
    }

    /* ---- where the run lies on the screen (1080 px) ---- */

    /// <summary>The run coordinate of a screen point: the light sweeps the bar left to right, leaning with her hair
    /// where it falls (y 830-980), level along the river below.</summary>
    public static double S(double x, double y) => x - 500 + 0.5 * (Math.Clamp(y, 830, 980) - 830);

    /// <summary>The front's s for fraction f of the run (s0 her hair, s1 the eddy).</summary>
    public static double FrontS(double f, double s0, double s1) => s0 + Math.Clamp(f, 0, 1) * (s1 - s0);

    /// <summary>The point on the river's crest (left to right) where the run coordinate is s, or null where s lies
    /// before the crest begins (the front is on her hair) or past its end.</summary>
    public static (double X, double Y)? OnCrest(IReadOnlyList<(double X, double Y)> crest, double s)
    {
        if (crest.Count < 2) return null;
        double prev = S(crest[0].X, crest[0].Y);
        if (s < prev) return null;
        for (int i = 1; i < crest.Count; i++)
        {
            double cur = S(crest[i].X, crest[i].Y);
            if (s <= cur)
            {
                double k = cur - prev > 1e-9 ? (s - prev) / (cur - prev) : 0;
                return (crest[i - 1].X + k * (crest[i].X - crest[i - 1].X), crest[i - 1].Y + k * (crest[i].Y - crest[i - 1].Y));
            }
            prev = cur;
        }
        return null;
    }

    /* ---- the numbers ---- */

    /// <summary>The numbers' card shows while the pointer is on the river or the hold key or button is down, never
    /// over a screen or a conversation.</summary>
    public static bool TipShown(bool hover, bool held, bool captured) => !captured && (hover || held);

    /// <summary>The hold key and pad button (Controls.Defaults and Pad).</summary>
    public const string HoldKey = "AltLeft", HoldPad = "LB";

    /// <summary>The card's lines: title, percent, the count, what is left (by day her experience, by night the ember).</summary>
    public static (string Title, string Pct, string Count, string Left) Lines(bool ember, int level, double have, double need, bool last)
    {
        string N(double v) => Math.Floor(Math.Max(0, v)).ToString("#,0", System.Globalization.CultureInfo.InvariantCulture);
        int pct = need > 0 ? (int)Math.Floor(Math.Clamp(have / need, 0, 1) * 100) : 100;
        if (last) return (ember ? $"Ember {level}" : $"Level {level}", "", ember ? "the ember is full" : "the last level", "");
        return ember
            ? ($"Ember {level}", $"{pct}%", $"{N(have)} / {N(need)} ember tonight", $"{N(need - have)} to ember {level + 1}")
            : ($"Level {level}", $"{pct}%", $"{N(have)} / {N(need)} experience", $"{N(need - have)} to level {level + 1}");
    }
}
