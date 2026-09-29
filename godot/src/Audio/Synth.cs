using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>Where a sound goes (effects unless said otherwise, as the web game).</summary>
public enum Bus { Sfx, Music, Amb, Ui }
public enum Wave { Sine, Triangle, Square, Saw }

/// <summary>A tone: an oscillator through filters and an envelope (the web game's ToneOpts).</summary>
public struct Tone
{
    public double F, D, G;
    public Wave Type;
    public double? T, A, Hold, F2, Glide, Lp, Lp2, Q, Hp, Detune, Verb;
    public Bus Bus;
    public double Pan;
}

/// <summary>Noise through filters and an envelope (the web game's NoiseOpts).</summary>
public struct Hiss
{
    public double D, G;
    public double? T, A, Bp, Bp2, Q, Lp, Lp2, Hp, Verb;
    public bool Brown;
    public Bus Bus;
    public double Pan;
}

/// <summary>Two-operator FM: bells, clinks, chimes, anything struck.</summary>
public struct Fm
{
    public double F, Ratio, Index, D, G;
    public double? T, A, F2, Verb;
    public Bus Bus;
    public double Pan;
}

/// <summary>
/// The sound of the world, made on the spot (the web game's audio/engine.ts).
/// No samples: every sound is built from oscillators and noise when it is
/// needed, through four buses (music, ambience, effects, interface) that
/// share one room, a long dark reverb, so a sword ring in the Verge and a
/// bell in the Waystation sound like they happen in the same place; a
/// compressor on the way out keeps a hundred hits in a second from turning
/// into mud. Rendered here, a few hundredths of a second ahead, into two
/// streams: the dry mix, and what is sent to the room (Godot's reverb).
/// </summary>
public partial class Synth : Node
{
    public static Synth? Instance { get; private set; }
    public double Rate { get; private set; } = 44100;
    long clock;
    /// <summary>Where the next sample falls, in seconds: 'now' for scheduling.</summary>
    public double Now => Interlocked.Read(ref clock) / Rate;
    readonly List<Voice> voices = new();
    readonly List<Bed> beds = new();
    AudioStreamGeneratorPlayback? dry, wet;
    public readonly float[] Level = { 0.85f, 0.8f, 0.9f, 0.7f };
    static readonly float[] Send = { 0.2f, 0.55f, 0.3f, 0.08f };
    public float Master = 0.85f;
    float duck = 1, duckNow = 1, masterNow;
    readonly Dictionary<string, Queue<ulong>> gates = new();
    public static readonly float[] White = NoiseBuffer(false), Brown = NoiseBuffer(true);
    static readonly Random rng = new();
    public bool Live => dry != null || tape != null;
    /// <summary>--wav PATH: no speakers; what would be heard is written to a file on exit.</summary>
    List<Vector2>? tape;
    string? tapePath;
    double tapeOwed;
    /// <summary>Seconds of work spent mixing, and of sound mixed (for the log).</summary>
    public double MixCost, Mixed;

    public Synth() { Instance = this; Name = "Synth"; }

    static float[] NoiseBuffer(bool brown)
    {
        var d = new float[44100 * 2];
        var r = new Random(brown ? 7 : 3);
        float last = 0;
        for (int i = 0; i < d.Length; i++)
        {
            float w = (float)(r.NextDouble() * 2 - 1);
            if (brown) { last = (last + 0.02f * w) / 1.02f; d[i] = last * 3.5f; } else d[i] = w;
        }
        return d;
    }

    public override void _Ready()
    {
        if (Args.Get("wav") is string path)
        {
            tapePath = path;
            tape = new List<Vector2>();
            return;
        }
        // Runs without a screen (tools) take no sound, unless asked (--sound).
        if ((DisplayServer.GetName() == "headless" && !Args.Has("sound")) || Args.Has("shot")) return;
        Rate = AudioServer.GetMixRate();
        int room = AudioServer.GetBusIndex("Room");
        if (room < 0)
        {
            AudioServer.AddBus();
            room = AudioServer.BusCount - 1;
            AudioServer.SetBusName(room, "Room");
            AudioServer.SetBusSend(room, "Master");
            AudioServer.AddBusEffect(room, new AudioEffectReverb { RoomSize = 0.86f, Damping = 0.7f, Spread = 1, Dry = 0, Wet = 0.8f, PredelayMsec = 20, Hipass = 0.1f });
            AudioServer.AddBusEffect(0, new AudioEffectCompressor { Threshold = -16, Ratio = 4, AttackUs = 4000, ReleaseMs = 250, Gain = 0 });
        }
        dry = Player("Master");
        wet = Player("Room");
        // The mixer keeps the speakers fed from its own thread, as a browser's
        // audio does: a long frame (a place loading) never leaves a gap.
        running = true;
        worker = new Thread(Feed) { IsBackground = true, Name = "Synth", Priority = ThreadPriority.AboveNormal };
        worker.Start();
    }

    /// <summary>How much sound to keep queued ahead of the speakers, in frames:
    /// little (sounds land on time) until the speakers run dry, then more (a
    /// busy machine, a place loading), easing back once things are calm.</summary>
    public int Queue { get; private set; }

    void Feed()
    {
        var d = dry!; var w = wet!;
        int capacity = Math.Min(d.GetFramesAvailable(), w.GetFramesAvailable());
        int least = (int)(Rate * 0.045);
        Queue = least;
        long skips = 0;
        ulong calm = Time.GetTicksMsec();
        while (running)
        {
            long now = d.GetSkips();
            ulong ms = Time.GetTicksMsec();
            if (now != skips) { skips = now; Queue = Math.Min(capacity, (int)(Queue * 1.5)); calm = ms; }
            else if (ms - calm > 20000 && Queue > least) { Queue = Math.Max(least, (int)(Queue * 0.85)); calm = ms; }
            int free = Math.Min(d.GetFramesAvailable(), w.GetFramesAvailable());
            int n = Math.Min(free, Queue - (capacity - free));
            if (n < 128) { Thread.Sleep(2); continue; }
            var (outDry, outWet) = Mix(n);
            d.PushBuffer(outDry);
            w.PushBuffer(outWet);
        }
    }

    AudioStreamGeneratorPlayback Player(string bus)
    {
        var p = new AudioStreamPlayer { Stream = new AudioStreamGenerator { MixRate = (float)Rate, BufferLength = 0.25f }, Bus = bus };
        AddChild(p);
        p.Play();
        return (AudioStreamGeneratorPlayback)p.GetStreamPlayback();
    }

    /// <summary>Lower the music under a conversation or a menu.</summary>
    public void DuckMusic(float k) => duck = k;

    /// <summary>At most `max` of this sound per `ms`: a hundred hits a second
    /// must not become a hundred sounds.</summary>
    public bool Gate(string key, int max, int ms)
    {
        ulong now = Time.GetTicksMsec();
        if (!gates.TryGetValue(key, out var q)) gates[key] = q = new Queue<ulong>();
        while (q.Count > 0 && now - q.Peek() > (ulong)ms) q.Dequeue();
        if (q.Count >= max) return false;
        q.Enqueue(now);
        return true;
    }

    public static double R(double a, double b) => a + rng.NextDouble() * (b - a);

    public void Play(Tone o) { if (Live) incoming.Enqueue(new ToneVoice(this, o)); }
    public void Play(Hiss o) { if (Live) incoming.Enqueue(new NoiseVoice(this, o)); }
    public void Play(Fm o) { if (Live) incoming.Enqueue(new FmVoice(this, o)); }
    public void Add(Bed b) => bedsIn.Enqueue(b);

    /// <summary>Sounds asked for since the mixer last looked (the mixer runs on its own thread).</summary>
    readonly ConcurrentQueue<Voice> incoming = new();
    readonly ConcurrentQueue<Bed> bedsIn = new();
    Thread? worker;
    volatile bool running;
    /// <summary>Times the speakers ran dry (a gap in the sound).</summary>
    public int Skips => (int)(dryPlayer?.GetSkips() ?? 0);
    AudioStreamGeneratorPlayback? dryPlayer => dry;

    public override void _Process(double delta)
    {
        if (tape != null)
        {
            // On tape: as much sound as the frame was long.
            tapeOwed += delta * Rate;
            int k = (int)tapeOwed;
            tapeOwed -= k;
            if (k <= 0) return;
            var (d, w) = Mix(k);
            // The room, roughly: the wet send folded in, as the reverb would return it.
            for (int i = 0; i < k; i++) tape.Add(d[i] + w[i] * 0.35f);
            return;
        }
    }

    /// <summary>The next n samples of everything playing: dry, and the room's send.</summary>
    (Vector2[] Dry, Vector2[] Wet) Mix(int n)
    {
        ulong t0 = Time.GetTicksUsec();
        while (incoming.TryDequeue(out var nv)) voices.Add(nv);
        while (bedsIn.TryDequeue(out var nb)) beds.Add(nb);
        var outDry = new Vector2[n];
        var outWet = new Vector2[n];
        float dt = (float)(1 / Rate);
        for (int i = 0; i < n; i++)
        {
            double t = (clock + i) / Rate;
            duckNow += (duck - duckNow) * 0.00006f;
            masterNow += (Master - masterNow) * 0.0002f;
            float dl = 0, dr = 0, wl = 0, wr = 0;
            for (int v = voices.Count - 1; v >= 0; v--)
            {
                var voice = voices[v];
                if (t < voice.Start) continue;
                if (t > voice.End) { voices.RemoveAt(v); continue; }
                float s = voice.Sample(t, dt);
                float bus = Level[(int)voice.Bus] * (voice.Bus == Bus.Music ? duckNow : 1);
                float l = s * voice.L * bus, r = s * voice.R * bus;
                dl += l; dr += r;
                float send = Send[(int)voice.Bus] + voice.Verb;
                wl += l * send; wr += r * send;
            }
            foreach (var b in beds)
            {
                float s = b.Sample(t, dt);
                if (s == 0) continue;
                float l = s * Level[(int)Bus.Amb];
                dl += l; dr += l;
                wl += l * Send[(int)Bus.Amb]; wr += l * Send[(int)Bus.Amb];
            }
            outDry[i] = new Vector2(dl, dr) * masterNow;
            outWet[i] = new Vector2(wl, wr) * masterNow;
        }
        Interlocked.Add(ref clock, n);
        MixCost += (Time.GetTicksUsec() - t0) / 1e6;
        Mixed += n / Rate;
        return (outDry, outWet);
    }

    public int Voices => voices.Count;

    public override void _ExitTree()
    {
        running = false;
        worker?.Join(200);
        if (tape == null || tapePath == null) return;
        // 16-bit stereo PCM.
        using var f = new System.IO.BinaryWriter(System.IO.File.Create(tapePath));
        int bytes = tape.Count * 4;
        f.Write("RIFF"u8); f.Write(36 + bytes); f.Write("WAVE"u8);
        f.Write("fmt "u8); f.Write(16); f.Write((short)1); f.Write((short)2); f.Write((int)Rate); f.Write((int)Rate * 4); f.Write((short)4); f.Write((short)16);
        f.Write("data"u8); f.Write(bytes);
        foreach (var v in tape)
        {
            f.Write((short)Math.Clamp(v.X * 32767, -32768, 32767));
            f.Write((short)Math.Clamp(v.Y * 32767, -32768, 32767));
        }
        GD.Print($"wrote {tapePath}: {tape.Count / Rate:0.0}s of sound, mixed at {MixCost / Math.Max(1e-9, Mixed) * 100:0.0}% of real time");
    }

    /* ----------------------------------------------------------- voices -- */

    /// <summary>A sound playing: when, where, and its next sample.</summary>
    public abstract class Voice
    {
        public double Start, End;
        public Bus Bus;
        public float L, R, Verb;
        public abstract float Sample(double t, float dt);

        protected void Place(Bus bus, double pan, double? verb)
        {
            Bus = bus;
            // Equal-power pan, as the web game's stereo panner.
            double x = (Math.Clamp(pan, -1, 1) + 1) / 2;
            L = (float)Math.Cos(x * Math.PI / 2);
            R = (float)Math.Sin(x * Math.PI / 2);
            Verb = (float)(verb ?? 0);
        }
    }

    /// <summary>A linear rise to the peak, a hold, and an exponential fall to
    /// nothing, stepped a sample at a time (a multiply, not a power, per sample).</summary>
    public sealed class Envelope
    {
        readonly double peak, inc, k;
        readonly long rise, hold, fall;
        long i;
        double v = 0.0001;

        public Envelope(double a, double hold, double d, double peak, double rate)
        {
            this.peak = peak;
            rise = Math.Max(1, (long)(a * rate));
            this.hold = Math.Max(0, (long)(hold * rate));
            fall = Math.Max(1, (long)(d * rate));
            inc = (peak - 0.0001) / rise;
            k = Math.Pow(0.0001 / Math.Max(1e-6, peak), 1.0 / fall);
        }

        public float Next()
        {
            long n = i++;
            if (n < rise) return (float)(v += inc);
            if (n < rise + hold) return (float)(v = peak);
            if (n == rise + hold) v = peak;
            if (n < rise + hold + fall) return (float)(v *= k);
            return 0;
        }
    }

    /// <summary>A value gliding exponentially from one to another over a span,
    /// then holding (no target: fixed).</summary>
    public sealed class Glide
    {
        double v;
        readonly double k;
        long left;

        public Glide(double from, double? to, double span, double rate)
        {
            v = from;
            if (to is double target && span > 0 && from > 0)
            {
                left = Math.Max(1, (long)(span * rate));
                k = Math.Pow(Math.Max(1e-4, target) / from, 1.0 / left);
            }
        }

        public double Next()
        {
            if (left > 0) { left--; v *= k; }
            return v;
        }
    }

    /// <summary>A biquad filter (the audio cookbook's), its coefficients remade
    /// every few samples when its frequency moves.</summary>
    public sealed class Biquad
    {
        public enum Kind { Low, High, Band }
        readonly Kind kind;
        double b0, b1, b2, a1, a2, x1, x2, y1, y2, lastF = -1;
        readonly double q, rate;
        int count;

        public Biquad(Kind kind, double q, double rate) { this.kind = kind; this.q = q; this.rate = rate; }

        public float Run(float x, double f)
        {
            if (count-- <= 0 || lastF < 0) { if (Math.Abs(f - lastF) > 0.5) Set(f); count = 32; }
            double y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
            x2 = x1; x1 = x; y2 = y1; y1 = y;
            return (float)y;
        }

        void Set(double f)
        {
            lastF = f;
            double w = 2 * Math.PI * Math.Clamp(f, 10, rate * 0.45) / rate, cs = Math.Cos(w), alpha = Math.Sin(w) / (2 * q);
            double a0 = 1 + alpha;
            switch (kind)
            {
                case Kind.Low: b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = (1 - cs) / 2; break;
                case Kind.High: b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = (1 + cs) / 2; break;
                default: b0 = alpha; b1 = 0; b2 = -alpha; break;
            }
            a1 = -2 * cs; a2 = 1 - alpha;
            b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0;
        }
    }

    /// <summary>The web game's low- and high-pass Q is in decibels: here, as a Q.</summary>
    static double QOf(double? db) => db is double d ? Math.Max(0.5, Math.Pow(10, d / 20) * 0.707) : 0.707;

    static float Osc(Wave w, double phase)
    {
        double p = phase - Math.Floor(phase);
        return w switch
        {
            Wave.Triangle => (float)(4 * Math.Abs(p - 0.5) - 1),
            Wave.Square => p < 0.5 ? 1f : -1f,
            Wave.Saw => (float)(2 * p - 1),
            _ => (float)Math.Sin(p * 2 * Math.PI),
        };
    }

    sealed class ToneVoice : Voice
    {
        readonly Wave type;
        readonly Envelope env;
        readonly Glide f, lpf;
        readonly Biquad? lp, hp;
        readonly double hpf;
        double phase;
        readonly double detune;

        public ToneVoice(Synth s, Tone o)
        {
            double t = o.T ?? s.Now, a = o.A ?? 0.005, hold = o.Hold ?? 0;
            Start = t; End = t + a + hold + o.D + 0.02;
            type = o.Type;
            env = new Envelope(a, hold, o.D, o.G, s.Rate);
            f = new Glide(o.F, o.F2, o.Glide ?? a + o.D, s.Rate);
            lpf = new Glide(o.Lp ?? 0, o.Lp2, End - Start, s.Rate);
            if (o.Lp != null) lp = new Biquad(Biquad.Kind.Low, QOf(o.Q), s.Rate);
            if (o.Hp is double h) { hp = new Biquad(Biquad.Kind.High, 0.707, s.Rate); hpf = h; }
            detune = Math.Pow(2, (o.Detune ?? 0) / 1200);
            Place(o.Bus, o.Pan, o.Verb);
        }

        public override float Sample(double t, float dt)
        {
            phase += f.Next() * detune * dt;
            float x = Osc(type, phase);
            if (lp != null) x = lp.Run(x, lpf.Next());
            if (hp != null) x = hp.Run(x, hpf);
            return x * env.Next();
        }
    }

    sealed class NoiseVoice : Voice
    {
        readonly Envelope env;
        readonly Biquad? bp, lp, hp;
        readonly Glide bpf, lpf;
        readonly double hpf;
        readonly float[] buf;
        double pos;
        readonly double rate;

        public NoiseVoice(Synth s, Hiss o)
        {
            double t = o.T ?? s.Now, a = o.A ?? 0.003;
            Start = t; End = t + a + o.D + 0.02;
            env = new Envelope(a, 0, o.D, o.G, s.Rate);
            buf = o.Brown ? Synth.Brown : White;
            pos = rng.NextDouble() * buf.Length * 0.75;
            rate = (0.9 + rng.NextDouble() * 0.2) * 44100 / s.Rate;
            bpf = new Glide(o.Bp ?? 0, o.Bp2, End - Start, s.Rate);
            lpf = new Glide(o.Lp ?? 0, o.Lp2, End - Start, s.Rate);
            if (o.Bp != null) bp = new Biquad(Biquad.Kind.Band, o.Q ?? 1, s.Rate);
            if (o.Lp != null) lp = new Biquad(Biquad.Kind.Low, 0.707, s.Rate);
            if (o.Hp is double h) { hp = new Biquad(Biquad.Kind.High, 0.707, s.Rate); hpf = h; }
            Place(o.Bus, o.Pan, o.Verb);
        }

        public override float Sample(double t, float dt)
        {
            pos += rate;
            if (pos >= buf.Length) pos -= buf.Length;
            float x = buf[(int)pos];
            if (bp != null) x = bp.Run(x, bpf.Next());
            if (lp != null) x = lp.Run(x, lpf.Next());
            if (hp != null) x = hp.Run(x, hpf);
            return x * env.Next();
        }
    }

    sealed class FmVoice : Voice
    {
        readonly Envelope env;
        readonly Glide f, depth;
        readonly double modF;
        double car, mod;

        public FmVoice(Synth s, Fm o)
        {
            double t = o.T ?? s.Now, a = o.A ?? 0.002;
            Start = t; End = t + a + o.D + 0.02;
            env = new Envelope(a, 0, o.D, o.G, s.Rate);
            f = new Glide(o.F, o.F2, End - Start, s.Rate);
            depth = new Glide(o.F * o.Index, Math.Max(1, o.F * o.Index * 0.05), End - Start, s.Rate);
            modF = o.F * o.Ratio;
            Place(o.Bus, o.Pan, o.Verb);
        }

        public override float Sample(double t, float dt)
        {
            mod += modF * dt;
            double inst = f.Next() + depth.Next() * Math.Sin(mod * 2 * Math.PI);
            car += inst * dt;
            return (float)Math.Sin(car * 2 * Math.PI) * env.Next();
        }
    }

    /// <summary>A sound that runs as long as the game does (wind, water, a
    /// town's murmur), its level set from outside.</summary>
    public abstract class Bed
    {
        public float Target, Level;
        public abstract float Sample(double t, float dt);
    }
}
