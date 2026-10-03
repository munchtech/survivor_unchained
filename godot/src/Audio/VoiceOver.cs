using System.Collections.Generic;
using Godot;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Sound;

/// <summary>
/// Recorded voices (the voice pass: docs/voice/README.md). A line of a
/// conversation plays when it is shown and stops when the player moves on; a
/// bark is said from where the speaker stands; a line under the picture is
/// read. The music and the ambience step back while anyone speaks. Which
/// take, and whether it still matches the words, is VoiceLines' business:
/// with nothing recorded, or nothing recorded for these words, this does
/// nothing at all, and the subtitles are the game as it was.
/// </summary>
public partial class VoiceOver : Node
{
    public static VoiceOver? Instance { get; private set; }
    public const string BusName = "Voice";

    AudioStreamPlayer? line;
    readonly Queue<Take> queue = new();
    readonly List<AudioStreamPlayer3D> barks = new();
    readonly Dictionary<string, AudioStream?> streams = new();
    string? lastNode;
    bool off;

    public VoiceOver() { Instance = this; Name = "VoiceOver"; }

    public override void _Ready()
    {
        // Its own bus, so the voices have their own volume.
        if (AudioServer.GetBusIndex(BusName) < 0)
        {
            AudioServer.AddBus();
            int i = AudioServer.BusCount - 1;
            AudioServer.SetBusName(i, BusName);
            AudioServer.SetBusSend(i, "Master");
        }
        line = new AudioStreamPlayer { Bus = BusName };
        line.Finished += Next;
        AddChild(line);
    }

    /// <summary>How loud the voices are (0 for none).</summary>
    public void Volume(float v)
    {
        off = v <= 0;
        int i = AudioServer.GetBusIndex(BusName);
        if (i >= 0) AudioServer.SetBusVolumeDb(i, off ? -80 : Mathf.LinearToDb(v));
        if (off) { Stop(); StopBarks(); }
    }

    AudioStream? Stream(Take t)
    {
        if (streams.TryGetValue(t.File, out var s)) return s;
        if (streams.Count > 160) streams.Clear();
        // Imported by the editor, or (before it has been opened) the bare file.
        if (ResourceLoader.Exists(t.File)) s = GD.Load<AudioStream>(t.File);
        else if (FileAccess.FileExists(t.File)) s = AudioStreamOggVorbis.LoadFromFile(t.File);
        return streams[t.File] = s;
    }

    /// <summary>A conversation's line, now on screen; the same node shown again
    /// (back from a shop) is not said twice.</summary>
    public void Line(string convo, DNode node, Ctx ctx)
    {
        string key = convo + "." + node.Id;
        if (key == lastNode) return;
        Halt();
        lastNode = key;
        if (off || !VoiceLines.Any) return;
        foreach (var t in VoiceLines.ForNode(convo, node, ctx)) queue.Enqueue(t);
        Next();
    }

    /// <summary>Words under the picture (a zone's caption), if they were recorded.</summary>
    public void Narrate(string text)
    {
        if (off || !VoiceLines.Any || VoiceLines.ForText(text) is not { } t) return;
        Halt();
        queue.Enqueue(t);
        Next();
    }

    void Next()
    {
        if (line == null) return;
        while (queue.Count > 0)
        {
            if (Stream(queue.Dequeue()) is not { } s) continue;
            StopBarks();
            line.Stream = s;
            line.Play();
            return;
        }
    }

    /// <summary>The conversation ended (or was skipped out of).</summary>
    public void Stop()
    {
        Halt();
        lastNode = null;
    }

    /// <summary>Whatever is being said stops: the player has moved on.</summary>
    void Halt()
    {
        queue.Clear();
        if (line?.Playing == true) line.Stop();
    }

    void StopBarks()
    {
        foreach (var b in barks) if (IsInstanceValid(b)) b.QueueFree();
        barks.Clear();
    }

    /// <summary>Something said to the air, from where it was said. The hint
    /// picks the take: 'm' or 'f' for a passer-by, or a speaker's name.</summary>
    public void Bark(Node3D world, string text, Vector3 at, string? hint)
    {
        if (off || !VoiceLines.Any || line?.Playing == true) return;
        barks.RemoveAll(b => !IsInstanceValid(b) || !b.Playing);
        // Two voices at once at most: a square, not a crowd.
        if (barks.Count >= 2 || VoiceLines.ForText(text, hint) is not { } t || Stream(t) is not { } s) return;
        var p = new AudioStreamPlayer3D
        {
            Stream = s, Bus = BusName, UnitSize = 9, MaxDistance = 45, AttenuationModel = AudioStreamPlayer3D.AttenuationModelEnum.InverseDistance,
        };
        world.AddChild(p);
        p.GlobalPosition = at + Vector3.Up * 1.6f;
        p.Finished += p.QueueFree;
        p.Play();
        barks.Add(p);
    }

    public override void _Process(double delta)
    {
        bool speaking = line?.Playing == true;
        bool barking = false;
        foreach (var b in barks) if (IsInstanceValid(b) && b.Playing) barking = true;
        Synth.Instance?.DuckUnderVoice(speaking ? 0.45f : barking ? 0.8f : 1);
    }
}
