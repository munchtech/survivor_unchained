using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>
/// Sounds recorded, not made (art/sound: Kenney's Impact Sounds, RPG Audio
/// and Interface Sounds, and field recordings from OpenGameArt, all CC0, as
/// mono 16-bit PCM): footsteps on grass, earth, stone and boards; flesh
/// struck, metal and plate rung, bodies falling; coins, cloth, a knife
/// drawn, a book's pages, doors; the clicks of the interface; an anvil; and
/// the ambience's long beds (bed_*: a river, a fire, crickets, birdsong). Each family has a few takes (sounds.json); a take is
/// never played twice running. Read once, on the main thread, and handed to
/// the mixer as plain samples.
/// </summary>
public static class Recordings
{
    public sealed record Take(float[] Data, int Rate);

    static readonly Dictionary<string, Take[]> families = new();
    static readonly Dictionary<string, int> last = new();
    static readonly Random rng = new(5);
    static bool loaded;

    /// <summary>Every take read into memory (a few megabytes).</summary>
    public static void Load()
    {
        if (loaded) return;
        loaded = true;
        var counts = Core.Json.Parse<Dictionary<string, int>>(FileAccess.GetFileAsString("res://art/sound/sounds.json"));
        foreach (var (name, n) in counts)
        {
            var takes = new List<Take>();
            for (int i = 0; i < n; i++)
                if (GD.Load<AudioStreamWav>($"res://art/sound/{name}_{i}.wav") is { Format: AudioStreamWav.FormatEnum.Format16Bits } w)
                {
                    var bytes = w.Data;
                    int channels = w.Stereo ? 2 : 1, frames = bytes.Length / 2 / channels;
                    var data = new float[frames];
                    for (int f = 0; f < frames; f++)
                    {
                        float s = 0;
                        for (int c = 0; c < channels; c++) s += BitConverter.ToInt16(bytes, (f * channels + c) * 2) / 32768f;
                        data[f] = s / channels;
                    }
                    takes.Add(new Take(data, w.MixRate));
                }
            if (takes.Count > 0) families[name] = takes.ToArray();
        }
    }

    /// <summary>A take of a family, not the one played last; null if there is none.</summary>
    /// <summary>Whether there are takes of a family.</summary>
    public static bool Has(string family) { Load(); return families.ContainsKey(family); }

    public static Take? Pick(string family)
    {
        if (!families.TryGetValue(family, out var takes)) return null;
        int prev = last.GetValueOrDefault(family, -1), i = rng.Next(takes.Length);
        if (takes.Length > 1 && i == prev) i = (i + 1) % takes.Length;
        last[family] = i;
        return takes[i];
    }
}
