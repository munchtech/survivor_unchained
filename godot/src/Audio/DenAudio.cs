using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The den's sound from the owner's recordings (docs/team/den_sound_events.md), the engine half of DenSound's rules:
/// the pits' loop placed in the world and falling off with distance, the pack heard far off before the first fight, the
/// recorded score (exploration from the entrance, the boss track from the Pack-Mother's arrival, the sting on her death,
/// then quiet) on the music bus, and the creatures' voices through the limiter. The synth score is silent while it plays.
/// </summary>
public sealed class DenAudio
{
    readonly Synth a;
    readonly DenSound.MusicRule rule = new();
    readonly DenSound.PackFarRule far = new();
    readonly DenSound.BigHitRule bigHit = new();
    readonly DenSound.VoiceLimiter limiter = new();
    readonly Random rng = new(11);
    readonly Dictionary<string, bool> known = new();
    /// <summary>Per id: how many voices played, how many the limiter held back (--soundlog prints it).</summary>
    public static readonly Dictionary<string, (int Played, int Dropped)> Counts = new();

    DenBed? pits, explore, boss, falls, packFar;
    double farUntil;
    float[]? pitKey;
    List<(double X, double Z, double R)> pitList = new();
    bool wasIn, warmed;
    double now, lastCombat = -99;

    public DenAudio(Synth a) { this.a = a; }

    /// <summary>The score is on (the synth's own is held silent), or just ended and the den is quiet.</summary>
    public bool InDen { get; private set; }
    public bool ScoreOn => InDen && rule.Want != DenSound.Track.None;

    /// <summary>A blow has landed or been taken: the pack is no longer far off, and the music steps back if it was big.</summary>
    public void Combat(IReadOnlyList<CombatEvent> evs, double herMaxHp)
    {
        if (!InDen) return;
        bool big = false;
        foreach (var e in evs)
        {
            if (e is Ev.Hit or Ev.PlayerHit) lastCombat = now;
            if (!big && DenSound.BigHit(e, herMaxHp)) big = true;
        }
        if (big && ScoreOn && bigHit.Admit(now)) a.DuckBeds(SoundBank.Duck("bighit", "music", 0.6f), 0.4);
    }

    /// <summary>The creatures' voices this frame, through the limiter, nearest first.</summary>
    public void Voices(IReadOnlyList<CombatEvent> evs, double px, double pz, Func<double, double, Sfx.Where> at)
    {
        if (!InDen) return;
        foreach (var w in DenSound.Wants(evs, px, pz))
        {
            string id = $"voice.{w.Kind}.{w.Moment}";
            if (!known.TryGetValue(id, out var has)) known[id] = has = SoundBank.Has(id);
            if (!has) continue;
            bool ok = limiter.Admit(w.Kind, w.Moment, now);
            var (p, d) = Counts.GetValueOrDefault(id);
            Counts[id] = ok ? (p + 1, d) : (p, d + 1);
            if (ok) SoundBank.Play(id, at(w.X, w.Z));
        }
    }

    /// <summary>Every frame: the den's loops, its far pack and its score.</summary>
    public void Update(double dt, SoundState s, int hostilesNear)
    {
        now += dt;
        bool inDen = s.Mode == "play" && s.Zone == "den";
        InDen = inDen;
        rule.Update(inDen, s.Boss, dt);
        if (!inDen)
        {
            if (wasIn) { SetAll(0); pitKey = null; }
            wasIn = false;
            return;
        }
        if (!wasIn) { wasIn = true; Warm(); }
        // The pits: one loop, at the nearest pit's rim, falling off with the distance, panned toward it.
        if (s.Holes is { } h && !ReferenceEquals(pitKey, h.Field))
        {
            pitKey = h.Field;
            pitList = DenSound.Pits(h.Field, h.Res, h.Half, h.Step);
        }
        if (pits != null)
        {
            double best = 0, pan = 0;
            foreach (var (x, z, r) in pitList)
            {
                double k = DenSound.Falloff(Math.Sqrt((x - s.Px) * (x - s.Px) + (z - s.Pz) * (z - s.Pz)), r);
                if (k > best) { best = k; pan = Math.Clamp((x - s.Px) / 18, -0.8, 0.8) * 0.7; }
            }
            pits.Target = (float)best;
            pits.Pan = (float)pan;
        }
        // The score.
        var want = rule.Want;
        if (explore != null) explore.Target = want == DenSound.Track.Explore ? 1 : 0;
        if (boss != null) boss.Target = want == DenSound.Track.Boss ? 1 : 0;
        if (falls != null) falls.Target = want == DenSound.Track.Falls ? 1 : 0;
        // The pack, far off, now and then, before the first fight and never during one.
        // It is a one-shot bed, so a fight beginning fades it out rather than letting it run over the blows.
        bool fighting = hostilesNear > 0 || now - lastCombat < 10 || s.Boss;
        if (packFar != null)
        {
            if (far.Admit(true, fighting, dt, rng.NextDouble()))
            {
                packFar.Pan = (float)((rng.NextDouble() - 0.5) * 1.4);
                packFar.Target = 1;
                farUntil = now + 26;
            }
            else if (fighting || now > farUntil) packFar.Target = 0;
        }
    }

    void SetAll(float t)
    {
        foreach (var b in new[] { pits, explore, boss, falls, packFar }) if (b != null) b.Target = t;
    }

    /// <summary>The den's takes, read and the beds started (silent) as she steps in, so nothing is read at the boss's arrival.</summary>
    void Warm()
    {
        if (warmed) return;
        warmed = true;
        double r = a.Rate;
        DenBed? Make(string id, string family, Bus bus, bool loop, float rise, float fall)
        {
            if (!SoundBank.Data.Events.TryGetValue(id, out var e) || e.Layers.Count == 0) return null;
            var take = family.StartsWith("music_") ? Recordings.Lazy(family) : Recordings.Pick(family);
            if (take == null) return null;
            var bed = new DenBed(take, r, (float)e.Layers[0].Gain, bus, loop, (float)(1 / (rise * r)), (float)(1 / (fall * r)));
            a.Add(bed);
            return bed;
        }
        pits = Make("den.pits", "den_pits", Bus.Amb, true, 1.2f, 1.2f);
        explore = Make("music.den.explore", "music_den_explore", Bus.Music, true, 2.5f, 2.5f);
        boss = Make("music.den.boss", "music_den_boss", Bus.Music, true, 2.5f, 0.8f);
        falls = Make("music.den.falls", "music_den_falls", Bus.Music, false, 0.05f, 1.0f);
        packFar = Make("den.pack_far", "den_pack_far", Bus.Amb, false, 0.6f, 0.8f);
    }

    public static void PrintLog()
    {
        foreach (var (id, (p, d)) in Counts.OrderBy(kv => kv.Key))
            GD.Print($"[denlog] {id} played {p} held {d}");
    }

    /// <summary>A recorded loop (or one-shot) as a bed: its own level, its own rise and fall, a pan across its two channels,
    /// on the music bus or the ambience. A one-shot rewinds while it is silent.</summary>
    sealed class DenBed : Synth.Bed
    {
        readonly float[] l;
        readonly float[]? r;
        readonly double step;
        readonly float gain, rise, fall;
        readonly bool loop;
        double pos;
        /// <summary>-1..1: toward the left or right ear.</summary>
        public float Pan;

        public DenBed(Recordings.Take take, double rate, float gain, Bus bus, bool loop, float rise, float fall)
        {
            l = take.Left ?? take.Data;
            r = take.Right;
            step = take.Rate / rate;
            this.gain = gain; this.loop = loop; this.rise = rise; this.fall = fall;
            Bus = bus;
            Wide = true;
        }

        static float At(double p, float[] d)
        {
            int i = (int)p;
            float k = (float)(p - i), x0 = d[i], x1 = d[i + 1 < d.Length ? i + 1 : 0];
            return x0 + (x1 - x0) * k;
        }

        public override float Sample(double t, float dt)
        {
            Level += (Target - Level) * (Target > Level ? rise : fall);
            if (Level < 1e-4f)
            {
                Right = 0;
                if (!loop && Target == 0) pos = 0;
                return 0;
            }
            pos += step;
            if (pos >= l.Length - 1)
            {
                if (!loop) { Right = 0; return 0; }
                pos -= l.Length - 1;
            }
            float g = gain * Level;
            float L = At(pos, l), R = r != null ? At(pos, r) : L;
            // Equal-power pan; centre is unity.
            double ang = (Pan + 1) * Math.PI / 4;
            Right = R * g * (float)(Math.Sin(ang) * Math.Sqrt(2));
            return L * g * (float)(Math.Cos(ang) * Math.Sqrt(2));
        }
    }
}
