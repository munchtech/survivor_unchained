using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The recorded voices (art/vo, made by tools/vo): a conversation's line and
/// the narrator on one channel, in the middle and close, each new line
/// stopping the last; and what people say to the air in the world, from
/// where they stand, under it. Speech is on its own bus ("Voice"), with its
/// own volume and an off switch in the settings, and while anyone speaks the
/// music and the world's noise step back (Synth.DuckForVoice). The subtitles
/// never go: a line with no take, or a take made from older words than the
/// ones on screen, is read in silence (VoiceLines).
/// </summary>
public partial class VoiceOver : Node
{
    public static VoiceOver? Instance { get; private set; }
    AudioStreamPlayer line = null!;
    readonly List<AudioStreamPlayer3D> barks = new();
    readonly Dictionary<string, AudioStream?> streams = new();
    readonly Random rng = new();
    int bus = -1;
    /// <summary>The take now speaking on the line channel, and its id.</summary>
    public VoTake? Current { get; private set; }
    public string? CurrentId { get; private set; }

    public VoiceOver() { Instance = this; Name = "VoiceOver"; }

    public override void _Ready()
    {
        bus = AudioServer.GetBusIndex("Voice");
        if (bus < 0)
        {
            AudioServer.AddBus();
            bus = AudioServer.BusCount - 1;
            AudioServer.SetBusName(bus, "Voice");
            AudioServer.SetBusSend(bus, "Master");
        }
        line = new AudioStreamPlayer { Bus = "Voice" };
        AddChild(line);
        Apply();
        // --record PATH: everything that reaches the speakers, voices and all,
        // written to a WAV on exit (to check the mix without ears in the room).
        if (Args.Get("record") is string)
        {
            record = new AudioEffectRecord();
            AudioServer.AddBusEffect(0, record);
            record.SetRecordingActive(true);
        }
    }

    AudioEffectRecord? record;

    public override void _ExitTree()
    {
        if (record == null || Args.Get("record") is not string path) return;
        record.SetRecordingActive(false);
        var wav = record.GetRecording();
        wav?.SaveToWav(path);
        GD.Print($"recorded the mix to {path}");
    }

    /// <summary>The settings' voice volume and switch.</summary>
    public void Apply()
    {
        var s = Settings.Current;
        if (bus >= 0) AudioServer.SetBusVolumeDb(bus, s.VoiceVolume <= 0.001f ? -80 : Mathf.LinearToDb(s.VoiceVolume));
        if (!s.Voices) Stop();
    }

    static bool Live => Settings.Current.Voices && DisplayServer.GetName() != "headless";

    AudioStream? Stream(VoTake t)
    {
        if (streams.TryGetValue(t.File, out var s)) return s;
        var path = $"res://art/vo/{t.File}";
        s = ResourceLoader.Exists(path) ? GD.Load<AudioStream>(path) : FileAccess.FileExists(path) ? AudioStreamOggVorbis.LoadFromFile(path) : null;
        streams[t.File] = s;
        return s;
    }

    /// <summary>A conversation's line, by id and the words as written: the take,
    /// if there is one for exactly these words (it starts at once).</summary>
    public VoTake? Say(string? id, string? raw)
    {
        Stop();
        if (!Live || id == null || raw == null) return null;
        return Start(id, VoiceLines.Take(id, raw));
    }

    /// <summary>A line from the zone code (the narrator, or a voice it names), by its words.</summary>
    public VoTake? Narrate(string text)
    {
        if (!Live) return null;
        var take = VoiceLines.Take(VoiceLines.Said(text), text);
        if (take == null) return null;
        Stop();
        return Start(VoiceLines.Said(text), take);
    }

    /// <summary>A named voice in a fight or a scene (the Warden, Grimtunnel, Snib), over everything.</summary>
    public VoTake? Shout(string text)
    {
        if (!Live) return null;
        var id = VoiceLines.FightBark(text);
        var take = VoiceLines.Take(id, text);
        if (take == null) return null;
        Stop();
        return Start(id, take);
    }

    VoTake? Start(string id, VoTake? take)
    {
        if (take == null || Stream(take) is not { } s) return null;
        line.Stream = s;
        line.Play();
        Current = take;
        CurrentId = id;
        GD.Print($"voice {id} ({take.Sec:0.0} s)");
        return take;
    }

    public void Stop()
    {
        if (line != null && line.Playing) line.Stop();
        Current = null;
        CurrentId = null;
    }

    public bool Speaking => line != null && line.Playing && Current != null;

    /// <summary>Where the voice is in its line, in seconds (what has been heard,
    /// not what has been mixed).</summary>
    public double Position => Speaking ? Math.Max(0, line.GetPlaybackPosition() + AudioServer.GetTimeSinceLastMix() - AudioServer.GetOutputLatency()) : 0;

    /// <summary>How much of a line's text should be on screen: the words keep
    /// a little ahead of the voice, part by part (the narrator's aside, then
    /// the speaker). Null when no voice is reading it.</summary>
    public double? Reveal(VoTake take)
    {
        if (!Speaking || Current != take) return null;
        double t = Position + 0.25;
        if (take.Segs is { Count: > 0 } segs)
        {
            double f = 0;
            foreach (var g in segs)
            {
                if (t < g[0]) break;
                f = t >= g[1] ? g[3] : g[2] + (g[3] - g[2]) * (t - g[0]) / Math.Max(0.01, g[1] - g[0]);
            }
            return Math.Clamp(f, 0, 1);
        }
        return Math.Clamp(t / Math.Max(0.1, take.Sec), 0, 1);
    }

    /// <summary>Something said to the air, from where the speaker stands. Not
    /// over a conversation or the narrator, and one at a time from any one
    /// place. `who` picks among several takes of the same words: an npc id,
    /// or 'f'/'m' for a passer-by.</summary>
    public double Bark(string text, Node3D world, Vector3 at, string? who = null)
    {
        if (!Live || Speaking) return 0;
        var takes = VoiceLines.ByText(text);
        if (takes.Count == 0) return 0;
        var mine = takes.Where(t => who != null && (t.Id.StartsWith($"bark.{who}.") || t.Take.Voice == who || t.Take.Sex == who)).ToList();
        var (_, take) = (mine.Count > 0 ? mine : takes)[rng.Next(mine.Count > 0 ? mine.Count : takes.Count)];
        if (Stream(take) is not { } s) return 0;
        barks.RemoveAll(b => !IsInstanceValid(b));
        // A crowd speaks one at a time.
        if (barks.Count(b => b.Playing) >= 2) return 0;
        var p = barks.FirstOrDefault(b => !b.Playing && b.GetParent() == world);
        if (p == null)
        {
            p = new AudioStreamPlayer3D { Bus = "Voice", UnitSize = 9, MaxDistance = 42, AttenuationFilterCutoffHz = 9000, AttenuationFilterDb = -6, PanningStrength = 0.6f };
            world.AddChild(p);
            barks.Add(p);
        }
        p.GlobalPosition = at + Vector3.Up * 1.6f;
        p.Stream = s;
        p.Play();
        return take.Sec;
    }

    public override void _Process(double delta)
    {
        bool talking = Speaking;
        if (!talking && Current != null) { Current = null; CurrentId = null; }
        bool barking = barks.Any(b => IsInstanceValid(b) && b.Playing);
        // Music under speech as a mixer would ride it: down under a
        // conversation or the narrator (with the conversation's own dip,
        // about 10 dB in all, measured with --record), a little under a passer-by.
        Synth.Instance?.DuckForVoice(talking ? 0.6f : barking ? 0.8f : 1, talking ? 0.72f : barking ? 0.88f : 1);
    }
}
