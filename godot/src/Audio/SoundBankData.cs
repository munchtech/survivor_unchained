using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The sound bank as data (data/content/sounds.json), Godot-free so the tests can read it: the buses'
/// levels and sends, the ducks, which material a creature family sounds like, and the events, each a
/// list of layers of recorded takes. SoundBank.cs plays it; the synth recipes in Sfx*.cs are the fallback
/// for an event with no takes yet.
/// </summary>
public sealed class SoundBankData
{
    public sealed class BusDef { public double Level { get; set; } = 1; public double Send { get; set; } /** master only: dB of makeup after the compressor. */ public double Makeup { get; set; } }

    public sealed class LayerDef
    {
        public string Take { get; set; } = "";
        public double Gain { get; set; } = 1;
        /// <summary>Gain jitter in dB, plus or minus.</summary>
        public double Vary { get; set; }
        public double[]? Pitch { get; set; }
        public double Delay { get; set; }
        public double? Lp { get; set; }
        public double? Verb { get; set; }
        public double? Pan { get; set; }
        public bool Stereo { get; set; }
    }

    public sealed class DuckDef { public double Sfx { get; set; } = 1; public double Seconds { get; set; } = 0.5; }

    public sealed class EventDef
    {
        public string Bus { get; set; } = "sfx";
        public int[]? Gate { get; set; }
        public string? GateKey { get; set; }
        public double Near { get; set; } = 0.5;
        public string Synth { get; set; } = "replace";
        public DuckDef? Duck { get; set; }
        public List<LayerDef> Layers { get; set; } = new();
    }

    public static readonly string[] BusNames = ["sfx", "music", "ambience", "ui", "flare"];

    public Dictionary<string, BusDef> Buses { get; set; } = new();
    public Dictionary<string, Dictionary<string, double>> Ducks { get; set; } = new();
    public Dictionary<string, string> Materials { get; set; } = new();
    public Dictionary<string, EventDef> Events { get; set; } = new();

    static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
        NumberHandling = JsonNumberHandling.AllowReadingFromString,
    };

    public static SoundBankData Parse(string json) => JsonSerializer.Deserialize<SoundBankData>(json, Options) ?? new SoundBankData();

    /// <summary>The material a creature family sounds like (by the family's name), "flesh" if unlisted.</summary>
    public string MaterialOf(string family) => Materials.TryGetValue(family, out var m) ? m : "flesh";

    /// <summary>The first of the ids that is an event, or null.</summary>
    public string? First(params string[] ids) => ids.FirstOrDefault(i => Events.ContainsKey(i));

    /// <summary>A duck depth for a name and bus (ducks.talk.music), or the fallback.</summary>
    public double Duck(string name, string bus, double fallback) =>
        Ducks.TryGetValue(name, out var d) && d.TryGetValue(bus, out var v) ? v : fallback;

    /// <summary>What is wrong with the data (not what is merely not recorded yet: see Pending).</summary>
    public List<string> Problems(Func<string, bool> hasFamily)
    {
        var p = new List<string>();
        foreach (var (name, b) in Buses)
            if (name != "master" && !BusNames.Contains(name)) p.Add($"buses.{name}: unknown bus");
        foreach (var (id, e) in Events)
        {
            if (!BusNames.Contains(e.Bus)) p.Add($"{id}: unknown bus '{e.Bus}'");
            if (e.Gate is { } g && (g.Length != 2 || g[0] <= 0 || g[1] <= 0)) p.Add($"{id}: gate must be [max > 0, ms > 0]");
            if (e.Synth is not ("replace" or "under")) p.Add($"{id}: synth must be 'replace' or 'under'");
            if (e.Near is < 0 or > 1) p.Add($"{id}: near must be 0..1");
            if (e.Layers.Count == 0) p.Add($"{id}: no layers");
            for (int i = 0; i < e.Layers.Count; i++)
            {
                var l = e.Layers[i];
                if (string.IsNullOrEmpty(l.Take)) p.Add($"{id}[{i}]: no take");
                if (l.Gain <= 0 || l.Gain > 4) p.Add($"{id}[{i}]: gain {l.Gain} outside (0, 4]");
                if (l.Pitch is { } pt && (pt.Length != 2 || pt[0] > pt[1] || pt[0] <= 0)) p.Add($"{id}[{i}]: pitch must be [lo, hi] with 0 < lo <= hi");
                if (l.Delay < 0) p.Add($"{id}[{i}]: negative delay");
            }
        }
        return p;
    }

    /// <summary>Events with a layer whose family has no takes yet (waiting to be generated), as "id: family".</summary>
    public List<string> Pending(Func<string, bool> hasFamily) =>
        Events.SelectMany(kv => kv.Value.Layers.Where(l => !hasFamily(l.Take)).Select(l => $"{kv.Key}: {l.Take}")).Distinct().ToList();

    /// <summary>An event is banked when it exists and every layer's family has takes.</summary>
    public bool Banked(string id, Func<string, bool> hasFamily) =>
        Events.TryGetValue(id, out var e) && e.Layers.Count > 0 && e.Layers.All(l => hasFamily(l.Take));
}
