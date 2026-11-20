using Godot;

namespace SurvivorUnchained.Sound;

/// <summary>
/// The title's song, the owner's recording (19 Nov 2026), streamed as Ogg on the engine's Master bus (so the
/// Sound setting's volume and mute reach it with everything else). Loaded in a thread when the title is shown,
/// faded in over 1.5 s once ready, kept through "create", faded out over 1.2 s when the title is left, then the
/// stream is freed. The song ends in its own fade, so it does not loop seamlessly: after it ends it waits 1.5 s
/// and starts again from the fade-in. If it fails to load, <see cref="Holds"/> is false and the synth Mood.Title plays.
/// </summary>
public sealed class TitleSong
{
    public const string Path = "res://art/sound/music_title_19nov.ogg";
    const double FadeIn = 1.5, FadeOut = 1.2, Gap = 1.5;
    enum St { Idle, Loading, Playing, Gap, Failed }

    readonly Node parent;
    St st = St.Idle;
    AudioStreamPlayer? player;
    double fade, gap;

    public TitleSong(Node parent) { this.parent = parent; }

    /// <summary>Whether the song has the title (loading, playing or between plays): the synth title mood keeps out.</summary>
    public bool Holds => st != St.Idle && st != St.Failed;

    public void Update(double dt, bool wanted)
    {
        switch (st)
        {
            case St.Idle:
                if (wanted && ResourceLoader.LoadThreadedRequest(Path) == Error.Ok) st = St.Loading;
                else if (wanted) st = St.Failed;
                break;
            case St.Loading:
                var status = ResourceLoader.LoadThreadedGetStatus(Path);
                if (status == ResourceLoader.ThreadLoadStatus.InProgress) break;
                var stream = status == ResourceLoader.ThreadLoadStatus.Loaded ? ResourceLoader.LoadThreadedGet(Path) as AudioStreamOggVorbis : null;
                if (stream == null) { st = St.Failed; break; }
                if (!wanted) { st = St.Idle; break; }   // left the title while it loaded: drop it
                stream.Loop = false;
                player = new AudioStreamPlayer { Stream = stream, Bus = "Master", VolumeDb = -80 };
                parent.AddChild(player);
                fade = 0;
                player.Play();
                st = St.Playing;
                break;
            case St.Playing:
                fade = wanted ? System.Math.Min(1, fade + dt / FadeIn) : System.Math.Max(0, fade - dt / FadeOut);
                player!.VolumeDb = fade <= 0.001 ? -80 : Mathf.LinearToDb((float)fade);
                if (!wanted && fade <= 0) { Free(); break; }
                if (!player.Playing) { gap = Gap; st = St.Gap; }
                break;
            case St.Gap:
                if (!wanted) { Free(); break; }
                gap -= dt;
                if (gap > 0) break;
                fade = 0; player!.VolumeDb = -80; player.Play(); st = St.Playing;
                break;
        }
    }

    void Free()
    {
        player?.Stop();
        player?.QueueFree();
        player = null;
        st = St.Idle;
    }
}
