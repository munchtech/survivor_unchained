using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>Where a sound goes (effects unless said otherwise, as the web game).</summary>
/// <summary>Flare: the Flares' own sound (Sfx.Flare), at the effects' level but never under the duck it puts on them.</summary>
public enum Bus { Sfx, Music, Amb, Ui, Flare }
public enum Wave { Sine, Triangle, Square, Saw }

/// <summary>A tone: an oscillator through filters and an envelope (the web game's ToneOpts).</summary>
public struct Tone
{
    public double F, D, G;
    public Wave Type;
    public double? T, A, Hold, F2, Glide, Lp, Lp2, Q, Hp, Detune, Verb;
    public Bus Bus;
    public bool Lead;
    public double Pan;
}

/// <summary>Noise through filters and an envelope (the web game's NoiseOpts).</summary>
public struct Hiss
{
    public double D, G;
    public double? T, A, Bp, Bp2, Q, Lp, Lp2, Hp, Verb;
    public bool Brown;
    public Bus Bus;
    public bool Lead;
    public double Pan;
}

/// <summary>Two-operator FM: bells, clinks, chimes, anything struck.</summary>
public struct Fm
{
    public double F, Ratio, Index, D, G;
    public double? T, A, F2, Verb;
    public Bus Bus;
    public bool Lead;
    public double Pan;
}

/// <summary>A recording (Recordings): a take of a family, at a pitch, dulled by a low-pass if asked.</summary>
public struct Clip
{
    public string Of;
    public double G;
    public double? T, Pitch, Lp, Verb;
    public Bus Bus;
    public bool Lead;
    public double Pan;
    /// <summary>Play the take's two channels as recorded (when it has them), ignoring Pan.</summary>
    public bool Stereo;
    /// <summary>Cut the take after this many seconds with a short fade (a windup that must end when its blow lands); null: the whole take.</summary>
    public double? Len;
    /// <summary>With Len: play the take's loudest Len seconds (a swell's crest, wherever it lies in that take), faded in
    /// briefly, not its first Len seconds.</summary>
    public bool Tail;
}

/// <summary>
/// The sound of the world, made on the spot (the web game's audio/engine.ts):
/// built from oscillators and noise when it is needed, with a few
/// recordings (Recordings) laid under it where a real thing sounds best,
/// flesh struck, a footstep, coins; through four buses (music, ambience, effects, interface) that
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
    public readonly float[] Level = { 0.85f, 0.8f, 0.9f, 0.7f, 0.85f };
    /// <summary>--wav PATH --stems: each bus's dry contribution (after its level and the ducks, no room), in Bus order, then
    /// a sixth: the lead voices alone (LeadRule; part of the sfx stem too), so a tape measures her hit over the crowd.</summary>
    List<Vector2>[]? stems;
    readonly float[] stemAcc = new float[12];
    /// <summary>Each bus's send to the room; like Level, in Bus order, and set from data/content/sounds.json (SoundBank).</summary>
    public static readonly float[] Send = { 0.2f, 0.55f, 0.3f, 0.08f, 0.22f };
    public float Master = 0.85f;
    /// <summary>The master's makeup gain after its compressor, before the limiter (sounds.json buses.master.makeup, in dB).</summary>
    public float Makeup = 1f;
    float duck = 1, duckNow = 1, masterNow;
    /// <summary>The fight's own noise held down under a big moment (the boss's fall, an
    /// evolution, a chest): its depth, until when (seconds on the mixer's clock), and now.</summary>
    volatile float sfxDuck = 1;
    double sfxDuckUntil;
    float sfxDuckNow = 1;
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

    /// <summary>Seconds on the tape so far (--wav; 0 without one): a trace line's place on it.</summary>
    public double TapeSeconds => tape == null ? 0 : tape.Count / (double)Rate;
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
            Dynamics();
            if (Args.Has("stems")) { stems = new List<Vector2>[6]; for (int i = 0; i < 6; i++) stems[i] = new List<Vector2>(); }
            SoundBank.Load(this);
            SoundHooks.Cue = id => Sfx.Cue(id);
            return;
        }
        // Runs without a screen (tools) take no sound, unless asked (--sound).
        if ((DisplayServer.GetName() == "headless" && !Args.Has("sound")) || Args.Has("shot")) return;
        SoundBank.Load(this);
        SoundHooks.Cue = id => Sfx.Cue(id);
        Rate = AudioServer.GetMixRate();
        Dynamics();
        int room = AudioServer.GetBusIndex("Room");
        if (room < 0)
        {
            AudioServer.AddBus();
            room = AudioServer.BusCount - 1;
            AudioServer.SetBusName(room, "Room");
            AudioServer.SetBusSend(room, "Master");
            AudioServer.AddBusEffect(room, new AudioEffectReverb { RoomSize = 0.86f, Damping = 0.7f, Spread = 1, Dry = 0, Wet = 0.8f, PredelayMsec = 20, Hipass = 0.1f });
            // The master's compressor and limiter run in Mix (so tapes measure true); none on Godot's bus.
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
            if (n < Chunk) { Thread.Sleep(2); continue; }
            // A chunk at a time into the kept buffers: two fresh arrays a push
            // were half of all the garbage the game made in a fight.
            for (; n >= Chunk; n -= Chunk)
            {
                Mix(Chunk, chunkDry, chunkWet);
                d.PushBuffer(chunkDry);
                w.PushBuffer(chunkWet);
            }
        }
    }

    const int Chunk = 128;
    readonly Vector2[] chunkDry = new Vector2[Chunk], chunkWet = new Vector2[Chunk];

    AudioStreamGeneratorPlayback Player(string bus)
    {
        var p = new AudioStreamPlayer { Stream = new AudioStreamGenerator { MixRate = (float)Rate, BufferLength = 0.25f }, Bus = bus };
        AddChild(p);
        p.Play();
        return (AudioStreamGeneratorPlayback)p.GetStreamPlayback();
    }

    /// <summary>Lower the music under a conversation or a menu.</summary>
    public void DuckMusic(float k) => duck = k;

    /// <summary>Hold the fight's sounds down under a big moment for a while, so the moment is
    /// heard (docs/feel/SUGGESTIONS.md S-03): about a tenth of a second down, half a second back.</summary>
    public void DuckSfx(float k, double seconds)
    {
        sfxDuckUntil = Now + seconds;
        sfxDuck = k;
    }

    /// <summary>Hold the music and the world's noise down for a while under a moment that must be
    /// heard over them (a Legendary's toll), never the fight's own sounds, which carry its warnings.</summary>
    public void DuckBeds(float k, double seconds)
    {
        bedDuckUntil = Now + seconds;
        bedDuck = k;
    }

    volatile float bedDuck = 1;
    double bedDuckUntil;
    float bedDuckNow = 1;

    float voiceMusic = 1, voiceAmb = 1, voiceMusicNow = 1, voiceAmbNow = 1;
    /// <summary>Lower the music and the world's noise while someone speaks
    /// (VoiceOver): quickly down when a line starts, slowly back after.</summary>
    public void DuckForVoice(float music, float amb) { voiceMusic = music; voiceAmb = amb; }

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

    /// <summary>While a LeadFor scope is open (the main thread, one recipe), every voice asked for is a lead voice.</summary>
    static bool leadScope;
    public readonly struct LeadScope : IDisposable
    {
        readonly bool was;
        public LeadScope(bool on) { was = leadScope; leadScope = was || on; }
        public void Dispose() => leadScope = was;
    }
    public static LeadScope LeadFor(bool on) => new(on);

    public void Play(Tone o) { if (Live) { o.Lead |= leadScope; incoming.Enqueue(new ToneVoice(this, o)); } }
    public void Play(Hiss o) { if (Live) { o.Lead |= leadScope; incoming.Enqueue(new NoiseVoice(this, o)); } }
    public void Play(Fm o) { if (Live) { o.Lead |= leadScope; incoming.Enqueue(new FmVoice(this, o)); } }
    public void Play(Clip o) { if (Live && Recordings.Pick(o.Of) is { } take) { o.Lead |= leadScope; incoming.Enqueue(new ClipVoice(this, o, take)); } }
    public void Add(Bed b) => bedsIn.Enqueue(b);
    /// <summary>Every one-shot sound playing or asked for is dropped at the mixer's next
    /// chunk (a skipped storybook's tails must not ring on into what follows). Beds stay.</summary>
    public void Cut() => cut = true;
    volatile bool cut;

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
            var d = new Vector2[k];
            var w = new Vector2[k];
            Mix(k, d, w);
            // The room, roughly: the wet send folded in, as the reverb would return it.
            for (int i = 0; i < k; i++) tape.Add(d[i] + w[i] * 0.35f);
            return;
        }
    }

    /// <summary>The next n samples of everything playing, into the first n of
    /// each: dry, and the room's send.</summary>
    void Mix(int n, Vector2[] outDry, Vector2[] outWet)
    {
        ulong t0 = Time.GetTicksUsec();
        if (cut) { cut = false; voices.Clear(); incoming.Clear(); }
        while (incoming.TryDequeue(out var nv)) voices.Add(nv);
        while (bedsIn.TryDequeue(out var nb)) beds.Add(nb);
        if (!crowdRead) { crowdRead = true; CrowdDuck = SoundBank.Duck("lead", "sfx", 0.5f); CrowdDuckDeep = SoundBank.Duck("lead", "sfxDeep", CrowdDuck); CrowdVoicesLo = SoundBank.Duck("lead", "sfxVoicesLo", 4); CrowdVoicesHi = SoundBank.Duck("lead", "sfxVoicesHi", 12); LeadHold = SoundBank.Duck("lead", "seconds", 0.09f); }
        float dt = (float)(1 / Rate);
        for (int i = 0; i < n; i++)
        {
            double t = (clock + i) / Rate;
            duckNow += (duck - duckNow) * 0.00006f;
            float sfxTo = t < sfxDuckUntil ? sfxDuck : 1;
            sfxDuckNow += (sfxTo - sfxDuckNow) * (sfxTo < sfxDuckNow ? 0.00022f : 0.00005f);
            masterNow += (Master - masterNow) * 0.0002f;
            // (F1 lead 24: the duck deepens from CrowdDuck to CrowdDuckDeep as the live effects voices go from Lo to Hi, the count
            // of the sample before: a mass kill's pile-up no longer buries her crack)
            float crowdDepth = CrowdDuck + (CrowdDuckDeep - CrowdDuck) * Math.Clamp((sfxLive - CrowdVoicesLo) / Math.Max(1f, CrowdVoicesHi - CrowdVoicesLo), 0f, 1f);
            sfxLive = 0;
            float crowdTo = t < leadUntil ? crowdDepth : 1;
            crowdNow += (crowdTo - crowdNow) * (crowdTo < crowdNow ? crowdAtk : crowdRel);
            float bedTo = t < bedDuckUntil ? bedDuck : 1;
            bedDuckNow += (bedTo - bedDuckNow) * (bedTo < bedDuckNow ? 0.00022f : 0.00005f);
            // About 0.12 s down, 0.6 s back up.
            voiceMusicNow += (voiceMusic - voiceMusicNow) * (voiceMusic < voiceMusicNow ? 0.00019f : 0.000038f);
            voiceAmbNow += (voiceAmb - voiceAmbNow) * (voiceAmb < voiceAmbNow ? 0.00019f : 0.000038f);
            float dl = 0, dr = 0, wl = 0, wr = 0;
            for (int v = voices.Count - 1; v >= 0; v--)
            {
                var voice = voices[v];
                if (t < voice.Start) continue;
                if (t > voice.End) { voices.RemoveAt(v); continue; }
                if (voice.Lead && !voice.Led) { voice.Led = true; leadUntil = Math.Max(leadUntil, voice.Start + LeadHold); }
                if (voice.Bus == Bus.Sfx && !voice.Lead) sfxLive++;
                float s = voice.Sample(t, dt);
                float bus = Level[(int)voice.Bus] * (voice.Bus == Bus.Music ? duckNow * voiceMusicNow * bedDuckNow : voice.Bus == Bus.Amb ? voiceAmbNow * bedDuckNow : voice.Bus == Bus.Sfx ? sfxDuckNow * (voice.Lead ? 1 : crowdNow) : 1);
                float l = s * voice.L * bus, r = (voice.Wide ? voice.Right : s) * voice.R * bus;
                dl += l; dr += r;
                if (stems != null) { stemAcc[(int)voice.Bus * 2] += l; stemAcc[(int)voice.Bus * 2 + 1] += r; if (voice.Lead) { stemAcc[10] += l; stemAcc[11] += r; } }
                float send = Send[(int)voice.Bus] + voice.Verb;
                wl += l * send; wr += r * send;
            }
            foreach (var b in beds)
            {
                float s = b.Sample(t, dt), s2 = b.Wide ? b.Right : s;
                if (s == 0 && s2 == 0) continue;
                // (H7 fix: the beds under DuckBeds too, as its summary says: they were left out, so a Flare's
                // intake sat under the world's noise it ducked)
                float amb = Level[(int)Bus.Amb] * voiceAmbNow * bedDuckNow, l = s * amb, r = s2 * amb;
                dl += l; dr += r;
                if (stems != null) { stemAcc[(int)Bus.Amb * 2] += l; stemAcc[(int)Bus.Amb * 2 + 1] += r; }
                wl += l * Send[(int)Bus.Amb]; wr += r * Send[(int)Bus.Amb];
            }
            // The master's dynamics, in the mix itself so a tape (--wav) is what the speakers get: the compressor
            // that sat on Godot's master bus (-16 dB, 4:1, 4 ms, 250 ms), then a limiter at -1 dBFS (instant down,
            // 80 ms back), on the dry signal plus the room as the tape folds it in.
            float pk = Math.Max(Math.Abs(dl + wl * 0.35f), Math.Abs(dr + wr * 0.35f)) * masterNow;
            compEnv += (pk - compEnv) * (pk > compEnv ? compAtk : compRel);
            float over = compEnv > 1e-6f ? 20 * MathF.Log10(compEnv) - CompThreshold : -120;
            float dyn = over > 0 ? MathF.Pow(10, -over * (1 - 1 / CompRatio) / 20) : 1;
            dyn *= Makeup;
            float post = pk * dyn * limG;
            if (post > Ceiling) limG = Ceiling / (pk * dyn); else limG += (1 - limG) * limRel;
            dyn *= limG * masterNow;
            outDry[i] = new Vector2(dl, dr) * dyn;
            outWet[i] = new Vector2(wl, wr) * dyn;
            if (stems != null)
                for (int k = 0; k < 6; k++) { stems[k].Add(new Vector2(stemAcc[k * 2], stemAcc[k * 2 + 1]) * masterNow); stemAcc[k * 2] = stemAcc[k * 2 + 1] = 0; }
        }
        Interlocked.Add(ref clock, n);
        MixCost += (Time.GetTicksUsec() - t0) / 1e6;
        Mixed += n / Rate;
    }

    public int Voices => voices.Count;

    /// <summary>The crowd sidechain: while a lead voice sounds (and LeadHold after it starts), every non-lead effects voice is
    /// held to CrowdDuck (ducks.lead.sfx / .seconds in sounds.json); about 3 ms down, 150 ms back.</summary>
    public float CrowdDuck = 0.5f;
    /// <summary>The duck's depth with CrowdVoicesHi or more non-lead effects voices live (ducks.lead.sfxDeep; Lo or fewer: CrowdDuck).</summary>
    public float CrowdDuckDeep = 0.5f, CrowdVoicesLo = 4, CrowdVoicesHi = 12;
    int sfxLive;
    public double LeadHold = 0.09;
    bool crowdRead;
    double leadUntil;
    float crowdNow = 1, crowdAtk, crowdRel;
    const float CompThreshold = -16, CompRatio = 4, Ceiling = 0.891f;
    float compEnv, limG = 1, compAtk, compRel, limRel;
    void Dynamics() { crowdAtk = (float)(1 - Math.Exp(-1 / (0.003 * Rate))); crowdRel = (float)(1 - Math.Exp(-1 / (0.15 * Rate))); compAtk = (float)(1 - Math.Exp(-1 / (0.004 * Rate))); compRel = (float)(1 - Math.Exp(-1 / (0.25 * Rate))); limRel = (float)(1 - Math.Exp(-1 / (0.08 * Rate))); }

    public override void _ExitTree()
    {
        running = false;
        worker?.Join(200);
        SoundBank.PrintLog();
        if (tape == null || tapePath == null) return;
        WriteWav(tapePath, tape);
        if (stems != null)
        {
            string stem = tapePath.EndsWith(".wav", StringComparison.OrdinalIgnoreCase) ? tapePath[..^4] : tapePath;
            string[] names = ["sfx", "music", "ambience", "ui", "flare", "lead"];
            // (the lead and the effects first: the quit guard may cut the last ones short, 11 Nov a run lost the lead stem's end)
            foreach (int i in (int[])[5, 0, 1, 2, 3, 4]) WriteWav($"{stem}_{names[i]}.wav", stems[i]);
        }
        GD.Print($"wrote {tapePath}: {tape.Count / Rate:0.0}s of sound, mixed at {MixCost / Math.Max(1e-9, Mixed) * 100:0.0}% of real time");
    }

    /// <summary>16-bit stereo PCM.</summary>
    void WriteWav(string path, List<Vector2> samples)
    {
        using var f = new System.IO.BinaryWriter(new System.IO.BufferedStream(System.IO.File.Create(path), 1 << 20));
        int bytes = samples.Count * 4;
        f.Write("RIFF"u8); f.Write(36 + bytes); f.Write("WAVE"u8);
        f.Write("fmt "u8); f.Write(16); f.Write((short)1); f.Write((short)2); f.Write((int)Rate); f.Write((int)Rate * 4); f.Write((short)4); f.Write((short)16);
        f.Write("data"u8); f.Write(bytes);
        foreach (var v in samples)
        {
            f.Write((short)Math.Clamp(v.X * 32767, -32768, 32767));
            f.Write((short)Math.Clamp(v.Y * 32767, -32768, 32767));
        }
    }

    /* ----------------------------------------------------------- voices -- */

    /// <summary>A sound playing: when, where, and its next sample.</summary>
    public abstract class Voice
    {
        public double Start, End;
        public Bus Bus;
        /// <summary>A lead voice (her heavy hit, a rare drop, a telegraph) is never ducked by the crowd and holds the crowd down while it sounds.</summary>
        public bool Lead;
        public bool Led;
        public float L, R, Verb;
        /// <summary>A wide voice's right side, set by each Sample (which gives its left); only read when Wide.</summary>
        public float Right;
        public virtual bool Wide => false;
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
            Place(o.Bus, o.Pan, o.Verb); Lead = o.Lead;
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
            Place(o.Bus, o.Pan, o.Verb); Lead = o.Lead;
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

    sealed class ClipVoice : Voice
    {
        readonly float[] data;
        readonly double step;
        readonly float gain;
        readonly Biquad? lp, lpR;
        readonly double lpf;
        double pos;
        readonly double cut = double.MaxValue;
        const double CutFade = 0.12, TailFade = 0.03;

        readonly float[]? right;
        double fadeIn = double.MinValue;
        static readonly System.Collections.Generic.Dictionary<(float[], int), int> crests = new();

        /// <summary>Where the take's loudest n samples start (by energy), cached per take and length.</summary>
        static int Crest(float[] d, int n)
        {
            n = Math.Clamp(n / 480 * 480, 1, d.Length);
            lock (crests)
            {
                if (crests.TryGetValue((d, n), out int at)) return at;
                double e = 0, best = -1;
                for (int i = 0; i < n; i++) e += d[i] * d[i];
                for (int i = 0; ; i++)
                {
                    if (e > best) { best = e; at = i; }
                    if (i + n >= d.Length) break;
                    e += d[i + n] * d[i + n] - d[i] * d[i];
                }
                crests[(d, n)] = at;
                return at;
            }
        }
        public override bool Wide => right != null;

        public ClipVoice(Synth s, Clip o, Recordings.Take take)
        {
            data = take.Data;
            if (o.Stereo && take.Left != null && take.Right != null) { data = take.Left; right = take.Right; }
            double pitch = o.Pitch ?? 1;
            step = take.Rate / s.Rate * pitch;
            Start = o.T ?? s.Now;
            End = Start + data.Length / (take.Rate * pitch) + 0.01;
            if (o.Len is double len && Start + len < End)
            {
                // (H7 fix2: a swelling intake cut to the stop played only its near-silent start; Tail plays its crest)
                if (o.Tail) { pos = Crest(data, (int)(len * take.Rate * pitch)); if (pos > 0) fadeIn = Start + TailFade; }
                cut = Start + len; End = cut + 0.01;
            }
            gain = (float)o.G;
            if (o.Lp is double f) { lp = new Biquad(Biquad.Kind.Low, 0.707, s.Rate); lpR = right != null ? new Biquad(Biquad.Kind.Low, 0.707, s.Rate) : null; lpf = f; }
            Place(o.Bus, o.Pan, o.Verb); Lead = o.Lead;
        }

        public override float Sample(double t, float dt)
        {
            int i = (int)pos;
            if (i >= data.Length - 1) return 0;
            float k = (float)(pos - i), x = data[i] + (data[i + 1] - data[i]) * k;
            pos += step;
            if (right != null)
            {
                float xr = right[i] + (right[i + 1] - right[i]) * k;
                Right = (lpR != null ? lpR.Run(xr, lpf) : xr) * gain;
            }
            if (lp != null) x = lp.Run(x, lpf);
            if (t > cut - CutFade) { float f = (float)Math.Clamp((cut - t) / CutFade, 0, 1); x *= f; Right *= f; }
            if (t < fadeIn) { float f = (float)Math.Clamp(1 - (fadeIn - t) / TailFade, 0, 1); x *= f; Right *= f; }
            return x * gain;
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
            Place(o.Bus, o.Pan, o.Verb); Lead = o.Lead;
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
        /// <summary>A wide bed's right side, set by each Sample (which gives its
        /// left); a narrow one sounds the same on both.</summary>
        public bool Wide;
        public float Right;
        public abstract float Sample(double t, float dt);
    }
}
