using System;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The Flares' own sound (docs/design/FLARE_LOOK.md §2.2, §2.3): made here, nothing borrowed from a spell or a
/// recording the spells use ("flares should be unique"). Every Flare: the catch when the meter fills, the confirm
/// on the press, the inhale through the Draw and the Hold with its held-breath gap, and the Spend in four layers
/// (transient, body, sub, the valley's answer). Burns Twice's material is ice and ember: the frost snaps and
/// shimmers out across the reach, each ember whistles down and lands as a crack, a whump and a hiss, and the last
/// is the full BOOM with the ice tinkling, embers crackling and steam hissing after it.
///
/// It plays on its own bus (Bus.Flare), so it rides over the duck it puts on the world (−12 dB) and on the music
/// and ambience (−9 dB), which come back over about a second after the last blow.
/// </summary>
public static partial class Sfx
{
    // The music's home (Music.cs: D) and its fifth, so the catch and the stinger never clash.
    const double FlareHome = 146.83, FlareFifth = 220.0;

    /// <summary>One of the Flare's cues (FlareFx.Cue): its name, where (panned and distanced from her), a size
    /// (the catch: 1.4 when the ember answers at low health; the inhale: the Hold's length in seconds), and the
    /// night (the valley answers only in the open at night).</summary>
    public static void Flare(string cue, Where w, float k, bool night)
    {
        if (A is not { } a) return;
        double p = w.Pan, t = Now, near = 0.55 + 0.45 * w.Near;
        switch (cue)
        {
            case "catch":
            {
                // A wick catching (fwmp) over a warm low tone on the home note; the answer at low health louder,
                // with a rush. The core never varies; the tail does a little.
                bool answer = k > 1.05f;
                double g = answer ? 1.6 : 1;
                a.Play(new Hiss { A = 0.035, D = 0.28, G = 0.07 * g, Lp = 380, Lp2 = R(1500, 1900), Brown = true, Bus = Bus.Flare });
                a.Play(new Tone { F = FlareHome, Type = Wave.Triangle, A = 0.03, D = 0.34, G = 0.05 * g, Bus = Bus.Flare, Verb = 0.15 });
                a.Play(new Fm { T = t + 0.02, F = FlareFifth * 2, Ratio = 2, Index = 0.5, A = 0.01, D = R(0.3, 0.42), G = 0.012 * g, Bus = Bus.Flare, Verb = 0.4 });
                if (answer) a.Play(new Hiss { A = 0.12, D = 0.25, G = 0.05, Bp = 600, Bp2 = 3200, Q = 1.2, Bus = Bus.Flare });
                return;
            }
            case "confirm":
                // A flint struck and an ember popping, peaking inside 30 ms: the hand knows it worked.
                a.Play(new Hiss { A = 0.001, D = 0.014, G = 0.15, Hp = 3500, Bp = 6200, Q = 2.5, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = 2600, F2 = 1300, Type = Wave.Triangle, A = 0.001, D = 0.03, G = 0.05, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { T = t + 0.012, F = 190, F2 = 70, A = 0.002, D = 0.07, G = 0.12, Pan = p, Bus = Bus.Flare });
                return;
            case "inhale":
            {
                // The riser: air drawn in, its band climbing, and a low saw rising a fifth under it, so it and the
                // BOOM are one sound; the sub-drop of an ember catching under the press; the stinger on top.
                // It stops clean 0.1 s before the release: the held breath.
                double len = Math.Max(0.25, k), rise = Math.Max(0.1, len - 0.1);
                a.Play(new Hiss { A = rise, D = 0.025, G = 0.17, Bp = 280, Bp2 = 2600, Q = 1.4, Bus = Bus.Flare });
                a.Play(new Hiss { A = rise, D = 0.025, G = 0.1, Lp = 200, Lp2 = 900, Brown = true, Bus = Bus.Flare });
                a.Play(new Tone { F = FlareHome / 2, F2 = FlareFifth / 2, Glide = rise, Type = Wave.Saw, A = rise, D = 0.025, G = 0.09, Lp = 260, Lp2 = 1500, Q = 2, Bus = Bus.Flare });
                a.Play(new Tone { F = 58, F2 = 31, A = 0.004, D = 0.55, G = 0.3, Bus = Bus.Flare });
                a.Play(new Fm { F = FlareHome * 2, Ratio = 1.5, Index = 1.2, A = 0.004, D = 0.6, G = 0.03, Bus = Bus.Flare, Verb = 0.5 });
                a.Play(new Fm { T = t + 0.09, F = FlareFifth * 2, Ratio = 2, Index = 0.9, A = 0.004, D = 0.7, G = 0.024, Bus = Bus.Flare, Verb = 0.5 });
                // The world −12 dB and the music and ambience −9 dB, through the Flare (each blow re-arms it).
                a.DuckSfx(0.25f, len + 1.6);
                a.DuckBeds(0.355f, len + 1.6);
                return;
            }
            case "frost":
            {
                // The release: ice snapping at her feet, a cold whump, and the frost racing out as a shimmer of
                // small high clinks thinning over 0.45 s, swept down a crackling band.
                a.Play(new Hiss { A = 0.001, D = 0.012, G = 0.32, Hp = 2800, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = 95, F2 = 44, A = 0.003, D = 0.4, G = 0.32, Pan = p, Bus = Bus.Flare });
                a.Play(new Hiss { A = 0.01, D = 0.5, G = 0.12, Bp = 7000, Bp2 = 2200, Q = 1.6, Pan = p, Bus = Bus.Flare });
                a.Play(new Fm { F = FlareFifth * 4, Ratio = 2.76, Index = 1.6, A = 0.002, D = 0.5, G = 0.03, Pan = p, Bus = Bus.Flare, Verb = 0.6 });
                for (int i = 0; i < 18; i++)
                {
                    double at = t + 0.02 + Math.Pow(i / 18.0, 1.4) * 0.45;
                    a.Play(new Fm { T = at, F = R(2400, 5200), Ratio = R(1.38, 1.45), Index = R(0.8, 2), A = 0.001, D = R(0.05, 0.16), G = 0.022 * (1 - i / 24.0), Pan = Math.Clamp(p + R(-0.6, 0.6), -0.9, 0.9), Bus = Bus.Flare, Verb = 0.35 });
                }
                a.DuckSfx(0.25f, 3.2);
                a.DuckBeds(0.355f, 3.2);
                return;
            }
            case "ember_fall":
                // Out of the night: a falling roar and a whistle bending down over the fall (0.26 s).
                if (!a.Gate("flare:fall", 3, 120)) return;
                a.Play(new Hiss { A = 0.2, D = 0.07, G = 0.07 * near, Bp = 3200, Bp2 = 900, Q = 2.2, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = R(1500, 1700), F2 = 700, Type = Wave.Sine, A = 0.18, D = 0.08, G = 0.012 * near, Pan = p, Bus = Bus.Flare });
                return;
            case "ember_land":
            {
                // Each lesser blow: ice cracking, a fire's whump, a short sub, steam spitting, a few shards ringing.
                if (!a.Gate("flare:land", 3, 90)) return;
                a.Play(new Hiss { A = 0.001, D = 0.01, G = 0.3 * near, Hp = 3000, Pan = p, Bus = Bus.Flare });
                a.Play(new Hiss { A = 0.004, D = 0.42, G = 0.3 * near, Lp = 2400, Lp2 = 180, Brown = true, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = 64, F2 = 34, A = 0.003, D = 0.32, G = 0.26 * near, Pan = p, Bus = Bus.Flare });
                a.Play(new Hiss { T = t + 0.04, A = 0.06, D = 0.8, G = 0.035 * near, Bp = 5200, Q = 0.8, Pan = p, Bus = Bus.Flare });
                for (int i = 0; i < 4; i++)
                    a.Play(new Fm { T = t + R(0.12, 0.6), F = R(2800, 5000), Ratio = 1.41, Index = 1.2, A = 0.001, D = R(0.05, 0.12), G = 0.014 * near, Pan = Math.Clamp(p + R(-0.4, 0.4), -0.9, 0.9), Bus = Bus.Flare });
                return;
            }
            case "ember_last" or "boom":
            {
                bool burns = cue == "ember_last";
                // The Spend, four layers on one frame. Transient: the ice's crack (and the flint again, bigger).
                a.Play(new Hiss { A = 0.001, D = 0.012, G = 0.7, Hp = 2500, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = 3200, F2 = 1100, Type = Wave.Triangle, A = 0.001, D = 0.04, G = 0.07, Pan = p, Bus = Bus.Flare });
                // Body (to ~0.4 s and on): the fire's mass going up, a stone-deep thump, never a generic boom.
                a.Play(new Hiss { A = 0.004, D = 0.95, G = 0.95, Lp = 3200, Lp2 = 140, Brown = true, Pan = p, Bus = Bus.Flare });
                a.Play(new Tone { F = 130, F2 = 58, Type = Wave.Triangle, A = 0.002, D = 0.3, G = 0.5, Pan = p, Bus = Bus.Flare });
                a.Play(new Hiss { A = 0.03, D = 0.6, G = 0.12, Bp = 900, Bp2 = 300, Q = 1, Pan = p, Bus = Bus.Flare });
                // Sub: 60 to 30 Hz, kin to the elite's kill (70 to 28), deeper and longer.
                a.Play(new Tone { F = 60, F2 = 30, A = 0.004, D = 0.62, G = 0.85, Bus = Bus.Flare });
                // Tail: the valley answers at night in the open, one dark filtered echo off the hills.
                if (night)
                {
                    double e = t + R(0.38, 0.5);
                    a.Play(new Hiss { T = e, A = 0.03, D = 1.3, G = 0.14, Lp = 900, Lp2 = 110, Brown = true, Pan = -p * 0.5, Bus = Bus.Flare, Verb = 0.7 });
                    a.Play(new Tone { T = e, F = 52, F2 = 30, A = 0.02, D = 0.6, G = 0.12, Bus = Bus.Flare });
                }
                if (burns)
                {
                    // Debris: ice tinkling down, embers crackling, steam hissing off the craters.
                    for (int i = 0; i < 16; i++)
                        a.Play(new Fm { T = t + 0.4 + Math.Pow(R(0, 1), 1.6) * 2.4, F = R(2600, 5600), Ratio = R(1.38, 1.45), Index = R(0.8, 1.8), A = 0.001, D = R(0.04, 0.14), G = R(0.008, 0.02), Pan = R(-0.7, 0.7), Bus = Bus.Flare });
                    for (int i = 0; i < 22; i++)
                        a.Play(new Hiss { T = t + 0.35 + R(0, 2.4), A = 0.001, D = R(0.006, 0.02), G = R(0.03, 0.08), Bp = R(1800, 4200), Q = 3, Pan = R(-0.7, 0.7), Bus = Bus.Flare });
                    a.Play(new Hiss { T = t + 0.2, A = 0.35, D = 2.6, G = 0.06, Bp = 4800, Q = 0.7, Bus = Bus.Flare });
                }
                // The world comes back over about a second.
                a.DuckSfx(0.25f, 0.35);
                a.DuckBeds(0.355f, 0.35);
                return;
            }
        }
    }
}
