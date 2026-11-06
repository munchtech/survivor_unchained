using System;
using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>What the bank did for an event: nothing (play the synth recipe), played AND the recipe plays too, or played and the recipe is skipped.</summary>
public enum Banked { None, Under, Replace }

/// <summary>
/// The sound bank as data (data/content/sounds.json, SoundBankData.cs): any event gets a sound from a
/// line of data, as layers of recorded takes (Recordings). The synth recipes in Sfx*.cs ask the bank
/// first and keep to their own sound when the event has no takes yet. Play only enqueues voices (as
/// Synth.Play does), so it is for the main thread; the mixer on its own thread is untouched.
/// </summary>
public static class SoundBank
{
    static SoundBankData? data;
    static readonly Dictionary<string, bool> banked = new();
    static bool applied;

    /// <summary>The data, read once (an empty bank if the file is missing or broken).</summary>
    public static SoundBankData Data
    {
        get
        {
            if (data != null) return data;
            try { data = SoundBankData.Parse(FileAccess.GetFileAsString("res://data/content/sounds.json")); }
            catch (Exception e) { GD.PushWarning($"sounds.json: {e.Message}"); data = new SoundBankData(); }
            return data;
        }
    }

    /// <summary>Read the data and put its buses on the mixer (Level, Send, Master). Called by the mixer once the takes are loaded.</summary>
    public static void Load(Synth s)
    {
        Recordings.Load();
        if (applied) return;
        applied = true;
        var d = Data;
        for (int i = 0; i < SoundBankData.BusNames.Length; i++)
            if (d.Buses.TryGetValue(SoundBankData.BusNames[i], out var b))
            {
                s.Level[i] = (float)b.Level;
                Synth.Send[i] = (float)b.Send;
            }
        if (d.Buses.TryGetValue("master", out var m)) { s.Master = (float)m.Level; s.Makeup = (float)Math.Pow(10, m.Makeup / 20); }
    }

    /// <summary>Whether the event exists and every layer of it has takes.</summary>
    public static bool Has(string id)
    {
        if (Log) lock (Asked) Asked[id] = Asked.GetValueOrDefault(id) + 1;
        if (banked.TryGetValue(id, out var v)) return v;
        return banked[id] = !Off && Data.Banked(id, Recordings.Has);
    }

    /// <summary>--nobank: every event plays its made recipe, as before the bank (the "before" of a listening sheet).</summary>
    static readonly bool Off = Args.Has("nobank");
    /// <summary>--soundlog: every id a recipe asked the bank for, and how often, printed when the mixer stops
    /// (which events a night really fires, banked or not).</summary>
    public static readonly bool Log = Args.Has("soundlog");
    public static readonly Dictionary<string, int> Asked = new();

    public static void PrintLog()
    {
        if (!Log) return;
        KeyValuePair<string, int>[] all;
        lock (Asked) all = Asked.OrderByDescending(kv => kv.Value).ToArray();
        foreach (var (id, n) in all)
            GD.Print($"[soundlog] {id} {n} {(banked.GetValueOrDefault(id) ? "banked" : "synth")}");
    }

    /// <summary>A duck depth from data (ducks.talk.music), today's number if the data has none.</summary>
    public static float Duck(string name, string bus, float fallback) => (float)Data.Duck(name, bus, fallback);

    /// <summary>The material a creature family sounds like.</summary>
    public static string MaterialOf(Sim.Family family) => Data.MaterialOf(family.ToString());

    /// <summary>The first of the ids that the bank can play, or null.</summary>
    public static string? FirstBanked(params string[] ids) => ids.FirstOrDefault(Has);

    /// <summary>Play the first banked of the ids (a fallback chain: hit.bone.crit, hit.bone, hit.flesh).</summary>
    public static Banked PlayFirst(Sfx.Where w, double gain, double pitch, bool gated, params string[] ids) =>
        FirstBanked(ids) is { } id ? Play(id, w, gain, null, pitch, gated) : Banked.None;

    /// <summary>PlayFirst, every layer cut after len seconds (a windup that ends when its blow lands).</summary>
    public static Banked PlayFirstFor(double? len, Sfx.Where w, params string[] ids) =>
        FirstBanked(ids) is { } id ? Play(id, w, len: len) : Banked.None;

    /// <summary>The first banked event of these, each layer's LAST len seconds (Clip.Tail: a swell ends on its crest).</summary>
    public static Banked PlayTailFor(double len, Sfx.Where w, params string[] ids) =>
        FirstBanked(ids) is { } id ? Play(id, w, len: len, tail: true) : Banked.None;

    static readonly Bus[] Buses = [Bus.Sfx, Bus.Music, Bus.Amb, Bus.Ui, Bus.Flare];

    /// <param name="at">Absolute mixer time to start at (like Clip.T), null for now.</param>
    /// <param name="gated">False skips the event's own gate, for recipes that have gated already.</param>
    /// <param name="len">Cut every layer after this many seconds, with a short fade (null: whole takes).</param>
    public static Banked Play(string id, Sfx.Where w = default, double gain = 1, double? at = null, double pitch = 1, bool gated = true, double? len = null, bool tail = false)
    {
        if (Synth.Instance is not { Live: true } s || !Has(id)) return Banked.None;
        var e = Data.Events[id];
        var mode = e.Synth == "under" ? Banked.Under : Banked.Replace;
        if (gated && e.Gate is { Length: 2 } g && !s.Gate(e.GateKey ?? id, g[0], g[1])) return mode;
        int bi = Math.Max(0, Array.IndexOf(SoundBankData.BusNames, e.Bus));
        double near = e.Near + (1 - e.Near) * w.Near, t0 = at ?? s.Now;
        foreach (var l in e.Layers)
        {
            double gl = l.Gain * gain * near;
            if (l.Vary > 0) gl *= Math.Pow(10, Synth.R(-l.Vary, l.Vary) / 20);
            double p = (l.Pitch is { Length: 2 } pr ? Synth.R(pr[0], pr[1]) : 1) * pitch;
            s.Play(new Clip
            {
                Of = l.Take, G = gl, Pitch = p, Lp = l.Lp, Verb = l.Verb, Bus = Buses[bi],
                T = at != null || l.Delay > 0 ? t0 + l.Delay : null,
                Pan = l.Stereo ? 0 : w.Pan + (l.Pan ?? 0), Stereo = l.Stereo,
                Len = len is double n ? Math.Max(0.05, n - l.Delay) : null, Tail = tail,
            });
        }
        if (e.Duck is { } d) s.DuckSfx((float)d.Sfx, d.Seconds);
        return mode;
    }
}
