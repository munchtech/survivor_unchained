using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Sound;

public enum Mood { Silence, Title, Explore, Town, Night, Combat, Boss, Mystery }

/// <summary>
/// The score, composed as it plays (the web game's audio/music.ts). D minor,
/// mostly, because it is that kind of story. A slow bed of pads walks a
/// four-chord progression; over it a plucked line wanders near the chord
/// tones, sparse on the road and busier in town. When the fighting starts, a
/// frame drum and a low ostinato come in under it, as loud as the fight is
/// thick; a boss brings a brass drone and a heavier drum. All of it is
/// scheduled a little ahead on a sixteenth-note grid, so it never drifts
/// however the frame rate wobbles.
/// </summary>
public sealed class Music
{
    const double D = 146.83; // D3
    static double St(double n) => D * Math.Pow(2, n / 12);

    enum Voice { Pluck, Bell, Flute }

    sealed record Style(double Bpm, int[][] Chords, int[] Scale, double Pluck, double Pad, double Drums, double Brass, Voice Voice);

    static readonly Dictionary<Mood, Style> Styles = new()
    {
        [Mood.Title] = new(64, new[] { new[] { 0, 3, 7 }, new[] { -2, 3, 5 }, new[] { -5, 2, 7 }, new[] { -3, 1, 4 } }, new[] { 0, 2, 3, 5, 7, 8, 10, 12, 14, 15 }, 0.35, 1, 0, 0, Voice.Bell),
        [Mood.Explore] = new(76, new[] { new[] { 0, 3, 7 }, new[] { -4, 0, 3 }, new[] { -2, 2, 5 }, new[] { -5, -1, 2 } }, new[] { 0, 2, 3, 5, 7, 9, 10, 12, 14 }, 0.22, 0.85, 0, 0, Voice.Pluck),
        [Mood.Night] = new(60, new[] { new[] { 0, 3, 7 }, new[] { -4, 0, 3 }, new[] { -7, -3, 0 }, new[] { -5, -2, 2 } }, new[] { 0, 3, 5, 7, 10, 12, 15 }, 0.12, 0.8, 0, 0, Voice.Flute),
        [Mood.Town] = new(88, new[] { new[] { 3, 7, 10 }, new[] { -2, 2, 5 }, new[] { 0, 3, 7 }, new[] { -4, 0, 3 } }, new[] { 0, 2, 3, 5, 7, 9, 10, 12, 14, 15 }, 0.45, 0.7, 0, 0, Voice.Pluck),
        [Mood.Combat] = new(104, new[] { new[] { 0, 3, 7 }, new[] { 0, 3, 7 }, new[] { -4, 0, 3 }, new[] { -2, 2, 5 } }, new[] { 0, 2, 3, 5, 7, 8, 10, 12 }, 0.1, 0.7, 1, 0, Voice.Pluck),
        [Mood.Boss] = new(112, new[] { new[] { 0, 3, 7 }, new[] { 1, 5, 8 }, new[] { 0, 3, 7 }, new[] { -1, 2, 5 } }, new[] { 0, 1, 3, 5, 7, 8, 10, 12 }, 0.08, 0.8, 1, 1, Voice.Pluck),
        [Mood.Mystery] = new(56, new[] { new[] { 0, 3, 6 }, new[] { -1, 3, 6 }, new[] { 0, 4, 7 }, new[] { -2, 1, 6 } }, new[] { 0, 1, 3, 6, 7, 9, 12 }, 0.14, 0.9, 0, 0, Voice.Bell),
    };

    // Combat grooves, sixteenths: 2 = accent, 1 = ghost.
    static readonly int[] Tom = { 2, 0, 0, 1, 0, 0, 2, 0, 2, 0, 0, 1, 0, 1, 0, 0 };
    static readonly int[] Slap = { 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 2, 0, 1, 0 };
    static readonly int[] Ostinato = { 0, 0, 3, 0, 2, 0, 0, -2 };

    readonly Synth a;
    static readonly Random rng = new();
    public Mood Mood { get; private set; } = Mood.Silence;
    Style? style;
    int step, chordIx, melodyAt = 7;
    double nextT;
    /// <summary>0..1: how thick the fighting is; drives the drums.</summary>
    public double Intensity;
    double drumLevel;
    /// <summary>How far ahead of the render head notes are placed. The synth
    /// renders ahead of the ear already, so this only needs to cover a frame.</summary>
    const double Ahead = 0.25;

    public Music(Synth a) { this.a = a; }

    public void Set(Mood m)
    {
        if (m == Mood) return;
        Mood = m;
        style = m == Mood.Silence ? null : Styles[m];
        // A new piece starts on its first chord, at the next bar.
        step = 0;
        chordIx = 0;
    }

    public void Update(double dt)
    {
        if (!a.Live) return;
        double want = style is { Drums: > 0 } ? Math.Min(1, Intensity) : 0;
        drumLevel += (want - drumLevel) * Math.Min(1, dt * 0.8);
        var s = style;
        double now = a.Now;
        if (s == null) { nextT = now; return; }
        double sixteenth = 60 / s.Bpm / 4;
        if (nextT < now - 0.2)
        {
            // Fell behind (a long frame): skip what was missed so the grid
            // stays on time, and if a chord change was skipped, bring it in now.
            int missed = (int)Math.Ceiling((now - nextT) / sixteenth);
            int before = step / 32;
            step += missed;
            nextT += missed * sixteenth;
            if (step / 32 != before || step % 32 == 0)
            {
                var chord = s.Chords[chordIx % s.Chords.Length];
                chordIx++;
                double left = (32 - step % 32) * sixteenth;
                Pad(chord, now + 0.02, Math.Max(2, left), s.Pad);
                if (s.Brass > 0) Brass(chord[0], now + 0.02, Math.Max(2, left));
                if (step % 32 == 0) step++;
            }
        }
        while (nextT < now + Ahead)
        {
            Play(s, step, nextT, sixteenth);
            step++;
            nextT += sixteenth;
        }
    }

    void Play(Style s, int step, double t, double sx)
    {
        int inBar = step % 16, bar = step / 16;
        // Chords change every two bars.
        if (inBar == 0 && bar % 2 == 0)
        {
            var c = s.Chords[chordIx % s.Chords.Length];
            chordIx++;
            Pad(c, t, sx * 32, s.Pad);
            if (s.Brass > 0) Brass(c[0], t, sx * 32);
        }
        var chord = s.Chords[(chordIx - 1 + s.Chords.Length) % s.Chords.Length];
        // The melody: sparse, on eighths, leaning on chord tones.
        if (inBar % 2 == 0 && rng.NextDouble() < s.Pluck * (inBar == 0 ? 1.6 : 1))
        {
            var tones = s.Scale;
            if (rng.NextDouble() < 0.55)
            {
                int target = chord[rng.Next(chord.Length)] + 12;
                int best = 0;
                for (int i = 1; i < tones.Length; i++) if (Math.Abs(tones[i] - target) < Math.Abs(tones[best] - target)) best = i;
                melodyAt = best;
            }
            else melodyAt = Math.Clamp(melodyAt + (rng.NextDouble() < 0.5 ? -1 : 1), 0, tones.Length - 1);
            double note = St(tones[Math.Min(melodyAt, tones.Length - 1)] + 12);
            switch (s.Voice)
            {
                case Voice.Bell: a.Play(new Fm { T = t, F = note, Ratio = 3.5, Index = 0.3, A = 0.004, D = 2.6, G = 0.06, Bus = Bus.Music, Verb = 0.6 }); break;
                case Voice.Flute: a.Play(new Tone { T = t, F = note, Type = Wave.Sine, A = 0.12, D = 1.4, G = 0.055, Bus = Bus.Music, Verb = 0.5 }); break;
                default: Pluck(note, t); break;
            }
        }
        // Drums and ostinato, as loud as the fighting.
        double dl = drumLevel;
        if (dl > 0.03)
        {
            int tom = Tom[inBar], slap = Slap[inBar];
            if (tom > 0) a.Play(new Tone { T = t, F = 110, F2 = 46, D = 0.28, G = (tom == 2 ? 0.26 : 0.12) * dl, Bus = Bus.Music });
            if (slap > 0 && dl > 0.3) a.Play(new Hiss { T = t, D = 0.11, G = (slap == 2 ? 0.07 : 0.03) * dl, Bp = 1300, Q = 0.9, Bus = Bus.Music });
            if (inBar % 2 == 0)
            {
                int n = Ostinato[inBar / 2 % Ostinato.Length] + chord[0];
                a.Play(new Tone { T = t, F = St(n - 12), Type = Wave.Saw, A = 0.005, D = sx * 1.6, G = 0.045 * dl, Lp = 700 + 900 * dl, Q = 3, Bus = Bus.Music });
            }
            if (s.Brass > 0 && inBar == 0) a.Play(new Tone { T = t, F = 58, F2 = 30, D = 0.9, G = 0.35 * dl, Bus = Bus.Music });
        }
    }

    void Pad(int[] chord, double t, double len, double level)
    {
        foreach (int n in chord)
            foreach (int det in new[] { -7, 6 })
                a.Play(new Tone { T = t, F = St(n), Type = Wave.Saw, A = 1.8, Hold = Math.Max(0, len - 1.8), D = 2.6, G = 0.024 * level, Lp = 520, Lp2 = 950, Detune = det, Bus = Bus.Music, Pan = det < 0 ? -0.3 : 0.3 });
        a.Play(new Tone { T = t, F = St(chord[0] - 12), Type = Wave.Triangle, A = 1.2, Hold = Math.Max(0, len - 1.2), D = 2.2, G = 0.09 * level, Bus = Bus.Music });
    }

    void Brass(int root, double t, double len)
    {
        foreach (int k in new[] { 0, 7 })
            a.Play(new Tone { T = t, F = St(root - 12 + k), Type = Wave.Saw, A = 0.8, Hold = Math.Max(0, len - 1.6), D = 1.4, G = 0.03, Lp = 300, Lp2 = 1100, Q = 1.5, Bus = Bus.Music, Detune = k != 0 ? 4 : -4 });
    }

    /// <summary>A plucked string: a bright attack, a quick fall, a darker ring.</summary>
    void Pluck(double f, double t)
    {
        a.Play(new Tone { T = t, F = f, Type = Wave.Triangle, A = 0.003, D = 1.3, G = 0.09, Lp = 2600, Lp2 = 500, Bus = Bus.Music, Verb = 0.35 });
        a.Play(new Tone { T = t, F = f * 2, Type = Wave.Sine, A = 0.002, D = 0.25, G = 0.025, Bus = Bus.Music });
        a.Play(new Hiss { T = t, D = 0.02, G = 0.015, Bp = f * 4, Q = 2, Bus = Bus.Music });
    }
}
