using System;
using System.Collections.Generic;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The world's own noise, underneath everything (the web game's
/// audio/ambience.ts): beds that run as long as the game does (wind in the
/// trees, water, a town's murmur, a fire, the blight's hum, crickets), each
/// noise shaped by filters and slow wobbles, each at a level the zone sets
/// every frame from where the survivor stands. On top, the things that
/// happen now and then: a bird, an owl, a crackle, the smith's hammer.
/// </summary>
public sealed class Ambience
{
    readonly Synth a;
    readonly Dictionary<string, Synth.Bed> beds = new();
    AmbienceMix target = new(), cur = new();
    readonly Dictionary<string, double> next = new();
    static readonly Random rng = new();

    public Ambience(Synth a)
    {
        this.a = a;
        double rate = a.Rate;
        const double Tau = Math.Tau;
        Add("wind", new NoiseBed(true, rate, 0.2f, Synth.Biquad.Kind.Low, 0.8, t => (420 + 220 * Math.Sin(t * 0.06 * Tau), 0, 0.7 + 0.3 * Math.Sin(t * 0.11 * Tau))));
        Add("leaves", new NoiseBed(false, rate, 0.018f, Synth.Biquad.Kind.Band, 0.5, t => (3800, 0, 0.6 + 0.45 * Math.Sin(t * 0.09 * Tau))));
        Add("water", new NoiseBed(false, rate, 0.09f, Synth.Biquad.Kind.Band, 0.8, t => (650 + 180 * Math.Sin(t * 3.1 * Tau), 1900 + 400 * Math.Sin(t * 5.3 * Tau), 1), band2Q: 1.6));
        Add("town", new NoiseBed(true, rate, 0.12f, Synth.Biquad.Kind.Band, 1.2, t => (380 + 90 * Math.Sin(t * 0.37 * Tau), 0, 0.7 + 0.3 * Math.Sin(t * 0.23 * Tau))));
        Add("fire", new NoiseBed(true, rate, 0.1f, Synth.Biquad.Kind.Low, 0.8, t => (260, 0, 0.8 + 0.25 * Math.Sin(t * 1.7 * Tau))));
        Add("hum", new HumBed(rate));
        Add("crickets", new CricketBed());
    }

    void Add(string key, Synth.Bed b) { beds[key] = b; a.Add(b); }

    public void Set(AmbienceMix m) => target = m;

    static double Get(AmbienceMix m, string k) => k switch
    {
        "wind" => m.Wind, "leaves" => m.Leaves, "water" => m.Water, "town" => m.Town, "fire" => m.Fire, "hum" => m.Hum,
        "crickets" => m.Crickets, "birds" => m.Birds, "owl" => m.Owl, "smithy" => m.Smithy, _ => 0,
    };

    static readonly string[] Keys = { "wind", "leaves", "water", "town", "fire", "hum", "crickets", "birds", "owl", "smithy" };
    readonly Dictionary<string, double> level = new();

    public void Update(double dt)
    {
        foreach (var k in Keys)
        {
            double v = level.GetValueOrDefault(k);
            v += (Get(target, k) - v) * Math.Min(1, dt * 1.2);
            level[k] = v;
            if (beds.TryGetValue(k, out var b)) b.Target = (float)v;
        }
        void Every(string key, double lvl, double lo, double hi, Action fn)
        {
            if (lvl < 0.02) return;
            next[key] = (next.TryGetValue(key, out var n) ? n : rng.NextDouble() * hi) - dt * lvl;
            if (next[key] <= 0) { next[key] = lo + rng.NextDouble() * (hi - lo); fn(); }
        }
        Every("crackle", level["fire"], 0.05, 0.35, () => a.Play(new Hiss { D = 0.01 + rng.NextDouble() * 0.03, G = 0.03 + rng.NextDouble() * 0.05, Bp = 1800 + rng.NextDouble() * 4000, Q = 2, Bus = Bus.Amb, Pan = rng.NextDouble() - 0.5 }));
        Every("bird", level["birds"], 2.5, 7, Bird);
        Every("owl", level["owl"], 18, 40, Owl);
        Every("smithy", level["smithy"], 1.8, 4.5, Hammer);
        Every("creak", level["wind"] * level["leaves"], 8, 20, () => a.Play(new Tone { F = 180 + rng.NextDouble() * 80, F2 = 150, Type = Wave.Saw, A = 0.3, D = 0.6, G = 0.008, Lp = 700, Bus = Bus.Amb, Pan = rng.NextDouble() - 0.5 }));
    }

    void Bird()
    {
        double pan = rng.NextDouble() * 1.6 - 0.8, b = 2600 + rng.NextDouble() * 1600, style = rng.NextDouble();
        int n = 2 + rng.Next(5);
        double t = a.Now;
        for (int i = 0; i < n; i++)
        {
            t += 0.09 + rng.NextDouble() * 0.06;
            double f = b * (1 + (style < 0.5 ? i * 0.04 : -i * 0.05) + (rng.NextDouble() - 0.5) * 0.08);
            a.Play(new Tone { T = t, F = f, F2 = f * (style < 0.5 ? 1.3 : 0.75), D = 0.05 + rng.NextDouble() * 0.05, G = 0.024 * level["birds"], Bus = Bus.Amb, Pan = pan, Verb = 0.4 });
        }
    }

    void Owl()
    {
        double pan = rng.NextDouble() * 1.4 - 0.7;
        foreach (var (dt, len) in new[] { (0.0, 0.35), (0.55, 0.22), (0.85, 0.5) })
            a.Play(new Tone { T = a.Now + dt, F = 390, F2 = 350, A = 0.06, D = len, G = 0.025 * level["owl"], Bus = Bus.Amb, Pan = pan, Verb = 0.7 });
    }

    void Hammer()
    {
        int n = 2 + rng.Next(4);
        for (int i = 0; i < n; i++) a.Play(new Fm { T = a.Now + i * 0.42, F = 1650 + rng.NextDouble() * 120, Ratio = 2.76, Index = 2.2, D = 0.5, G = 0.02 * level["smithy"], Bus = Bus.Amb, Pan = 0.3, Verb = 0.5 });
    }

    /// <summary>A bed of noise through a filter (and, for water, a second band
    /// beside it), its frequencies and loudness wobbled slowly: the wobble is
    /// worked out every 64 samples, the filtering every sample.</summary>
    sealed class NoiseBed : Synth.Bed
    {
        readonly float[] buf;
        readonly Synth.Biquad f1;
        readonly Synth.Biquad? f2;
        readonly Func<double, (double F1, double F2, double Gain)> wobble;
        readonly float scale;
        double pos, fr1, fr2;
        float gain, gainTo;
        readonly double step;
        int count;

        public NoiseBed(bool brown, double rate, float scale, Synth.Biquad.Kind kind, double q, Func<double, (double, double, double)> wobble, double band2Q = 0)
        {
            buf = brown ? Synth.Brown : Synth.White;
            pos = rng.NextDouble() * buf.Length;
            step = 44100 / rate;
            this.scale = scale;
            this.wobble = wobble;
            f1 = new Synth.Biquad(kind, q, rate);
            if (band2Q > 0) f2 = new Synth.Biquad(Synth.Biquad.Kind.Band, band2Q, rate);
        }

        public override float Sample(double t, float dt)
        {
            Level += (Target - Level) * 0.0002f;
            if (Level < 1e-4f) return 0;
            if (count-- <= 0)
            {
                count = 64;
                double g;
                (fr1, fr2, g) = wobble(t);
                gainTo = (float)g;
            }
            // The loudness slides between wobble points, so it never steps.
            gain += (gainTo - gain) * 0.02f;
            pos += step;
            if (pos >= buf.Length) pos -= buf.Length;
            float n = buf[(int)pos];
            float x = f1.Run(n, fr1);
            if (f2 != null) x += f2.Run(n, fr2);
            return x * gain * Level * scale;
        }
    }

    /// <summary>The blight's hum near the Dig: something electrical in the water.</summary>
    sealed class HumBed : Synth.Bed
    {
        double p1, p2;
        readonly Synth.Biquad low;
        public HumBed(double rate) { low = new Synth.Biquad(Synth.Biquad.Kind.Low, 0.707, rate); }

        public override float Sample(double t, float dt)
        {
            Level += (Target - Level) * 0.0002f;
            if (Level < 1e-4f) return 0;
            p1 += 55 * dt; p2 += 55.6 * dt;
            float x = (float)(2 * (p1 - Math.Floor(p1)) - 1 + 2 * (p2 - Math.Floor(p2)) - 1);
            return low.Run(x, 300 + 120 * Math.Sin(t * 0.2 * Math.Tau)) * Level * 0.03f;
        }
    }

    /// <summary>Crickets: a high tone chopped into chirps, in waves.</summary>
    sealed class CricketBed : Synth.Bed
    {
        double p, chop;
        public override float Sample(double t, float dt)
        {
            Level += (Target - Level) * 0.0002f;
            if (Level < 1e-4f) return 0;
            p += 4400 * dt; chop += 26 * dt;
            float x = (float)Math.Sin(p * Math.Tau);
            float c = (chop - Math.Floor(chop)) < 0.5 ? 1 : 0;
            float wave = (float)(0.5 + 0.5 * Math.Sin(t * 0.7 * Math.Tau));
            return x * c * wave * Level * 0.012f;
        }
    }
}
