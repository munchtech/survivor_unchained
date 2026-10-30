using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Godot;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Storybook;
using SurvivorUnchained.Ui;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>What the storybook borrows from the game: the voice, the score, the
/// buttons held, and the survivor its lines are read for.</summary>
public sealed record StoryHost(VoiceOver? Voice, SoundBridge? Sound, Func<bool> SkipHeld, Ctx Ctx);

/// <summary>
/// Plays a storybook (docs/storybook/README.md): its plates drawn each into
/// its own picture and mixed by the transitions under the cinema bars, its
/// cues heard through the game's own voice, sounds and score, and skipped by
/// holding as a cinematic is. Only the plates being drawn exist; the next
/// one's textures load on a thread a few seconds ahead. Its clock is its own
/// (the frame's delta), so with a fixed frame rate (--fixed-fps, Movie Maker)
/// the same second always gives the same picture.
/// </summary>
public partial class StoryPlayer : Node
{
    /// <summary>Seconds ahead of a plate that its textures start loading.</summary>
    const double Ahead = 3.0;
    /// <summary>Above the world and the HUD's play layer, under the bars (20) and the fade (30).</summary>
    public const int ScreenLayer = 19;

    public readonly StoryFile File;
    public readonly StoryTimeline Line;
    public readonly CinemaBars Bars;
    readonly StoryHost host;
    readonly Action<bool> done;
    readonly bool seen;
    readonly Dictionary<int, PlateView> live = new();
    readonly HashSet<int> preloaded = new();
    readonly CanvasLayer layer = new() { Layer = ScreenLayer, Name = "StoryScreen" };
    readonly ColorRect screen = new() { MouseFilter = Control.MouseFilterEnum.Ignore, Color = Colors.Black };
    readonly ShaderMaterial compose = new();
    readonly Dictionary<string, (AudioStreamPlayer P, string Bus)> sounds = new();
    readonly List<(double T0, double T1, Action<double> Apply)> tweens = new();
    AudioEffectLowPassFilter? low;
    AudioEffectAmplify? amp;
    double t, last = -1e-6, skipHeld;
    bool over, ownsBars;
    public bool Skipped { get; private set; }
    public double T => t;
    /// <summary>--sb-shots: the moments to save, and one asked for once this frame is drawn.</summary>
    readonly Queue<double> shots = new();
    string? shotDue;
    /// <summary>--sb-skip-at S: the skip done at storybook time S, as the hold does it (checks of the skip).</summary>
    readonly double? skipAtArg = Args.Has("sb-skip-at") ? Args.Num("sb-skip-at", 0) : null;

    public StoryPlayer(StoryFile file, StoryHost host, Action<bool> done, CinemaBars? bars = null, double from = 0)
    {
        File = file;
        Line = new StoryTimeline(file);
        this.host = host;
        this.done = done;
        Name = $"Storybook_{file.Id}";
        ProcessMode = ProcessModeEnum.Always;
        seen = Settings.Current.SeenCinematics.Contains(file.Id);
        ownsBars = bars == null;
        Bars = bars ?? new CinemaBars();
        t = Math.Max(0, from);
        last = t - 1e-6;
        if (Args.Get("sb-shots") is string list)
            foreach (var s in list.Split(',', StringSplitOptions.RemoveEmptyEntries).Select(x => double.Parse(x, CultureInfo.InvariantCulture)).Order())
                if (s >= t) shots.Enqueue(s);
    }

    public override void _Ready()
    {
        compose.Shader = StoryArt.Compose;
        screen.Material = compose;
        screen.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        layer.AddChild(screen);
        AddChild(layer);
        if (ownsBars) AddChild(Bars);
        // The bars fully in from the first frame, over black.
        Bars.Frame(1, 0);
        // The profile's flag: seen once, it may be skipped at once next time (docs/story/storybook, "Trigger").
        if (!seen) { Settings.Current.SeenCinematics.Add(File.Id); Settings.Current.Save(); }
        // Its own muffle and level, on the way out of everything (the underwater close, the well at the end).
        int master = 0;
        low = new AudioEffectLowPassFilter { CutoffHz = 20000, Resonance = 0.5f };
        amp = new AudioEffectAmplify { VolumeDb = 0 };
        AudioServer.AddBusEffect(master, low);
        AudioServer.AddBusEffect(master, amp);
        if (t > 0) Seek(t);
        GD.Print($"storybook: {File.Id} ({File.End:0.0} s, {File.Plates.Count} plates){(t > 0 ? $" from {t:0.0}" : "")}");
        Frame(0);
        RenderingServer.FramePostDraw += PostDraw;
    }

    public override void _ExitTree()
    {
        RenderingServer.FramePostDraw -= PostDraw;
        Unmuffle();
        StoryArt.Release();
    }

    /// <summary>A run started late (--sb-from): what lasts (the score, the bus) set as it would
    /// stand; one-shot sounds and lines before it are not heard.</summary>
    void Seek(double at)
    {
        foreach (var c in Line.Cues.Where(c => c.T <= at && c.Cue.Do is "music" or "bus"))
            Do(c, instant: true);
    }

    public override void _Process(double delta)
    {
        if (over) return;
        t += delta;
        Frame(delta);
    }

    void Frame(double delta)
    {
        if (Skipped)
        {
            // Only the sound's fade runs on; then it is over.
            Tweens();
            if (t >= skipAt + 0.15) { host.Voice?.Stop(); Synth.Instance?.Cut(); Finish(); }
            return;
        }
        if (StoryTimeline.SkipDue(t, skipAtArg)) { GD.Print($"storybook: --sb-skip-at {skipAtArg:0.00}: skipping at {t:0.00}s"); Skip(); }
        else Skipping(delta);
        if (Skipped || over) return;
        foreach (var c in Line.Between(last, t).ToList()) Do(c);
        last = t;
        Tweens();
        Plates();
        if (shots.Count > 0 && t >= shots.Peek() - 1e-6) shotDue = $"sb_{File.Id}_{shots.Dequeue().ToString("0.00", CultureInfo.InvariantCulture)}";
        if (t >= File.End) Finish();
    }

    void Tweens()
    {
        for (int i = tweens.Count - 1; i >= 0; i--)
        {
            var (t0, t1, apply) = tweens[i];
            double k = t1 <= t0 ? 1 : Math.Clamp((t - t0) / (t1 - t0), 0, 1);
            apply(k);
            if (k >= 1) tweens.RemoveAt(i);
        }
    }

    /// <summary>Which plates exist (loaded ahead, freed after) and the composite's inputs.</summary>
    void Plates()
    {
        var size = (Vector2I)GetViewport().GetVisibleRect().Size;
        foreach (var s in Line.Spans)
        {
            bool drawn = t >= s.Start && t < s.DrawEnd;
            if (!preloaded.Contains(s.Index) && t >= s.Start - Ahead && t < s.DrawEnd) { preloaded.Add(s.Index); StoryArt.Preload(s.Plate); }
            if (drawn && !live.ContainsKey(s.Index))
            {
                var v = new PlateView(File, s, size, t - s.Start);
                AddChild(v);
                live[s.Index] = v;
            }
            else if (!drawn && live.TryGetValue(s.Index, out var gone))
            {
                live.Remove(s.Index);
                gone.QueueFree();
            }
        }
        foreach (var v in live.Values) v.Show(t - v.Span.Start);
        var mix = Line.Mix(t);
        Input("under", mix.Under);
        Input("over", mix.Over);
        compose.SetShaderParameter("k", mix.K);
        if (mix.Over is { } o)
        {
            var tr = o.Plate.In;
            compose.SetShaderParameter("kind", Array.IndexOf(new[] { "cut", "fade", "dissolve", "ink", "light", "waterline" }, tr.Kind));
            compose.SetShaderParameter("origin", tr.Origin is { Length: 2 } og ? new Vector2((float)og[0], (float)og[1]) : new Vector2(0.5f, 0.5f));
            var map = tr.Map != null ? StoryArt.Tex(tr.Map) : null;
            compose.SetShaderParameter("has_map", map != null);
            if (map != null) compose.SetShaderParameter("ink_map", map);
            var edge = StoryArt.Col(tr.Edge, tr.Kind == "light" ? new Color("#ffc677") : new Color("#0b0a09"));
            compose.SetShaderParameter("edge", new Vector3(edge.R, edge.G, edge.B));
            compose.SetShaderParameter("soft", tr.Soft);
            var dip = StoryArt.Col(tr.Color, Colors.Black);
            compose.SetShaderParameter("dip", new Vector3(dip.R, dip.G, dip.B));
            compose.SetShaderParameter("wave", tr.Wave);
        }
        compose.SetShaderParameter("t", t);
        compose.SetShaderParameter("aspect", (float)size.X / Math.Max(1, size.Y));
        compose.SetShaderParameter("screen", new Vector2(size.X, size.Y));
        compose.SetShaderParameter("grain", File.Grain);
        compose.SetShaderParameter("vignette", File.Vignette);
    }

    void Input(string which, PlateSpan? s)
    {
        compose.SetShaderParameter($"has_{which}", s != null && live.ContainsKey(s.Index));
        if (s == null || !live.TryGetValue(s.Index, out var v)) return;
        compose.SetShaderParameter($"{which}_tex", v.GetTexture());
        var g = v.Grade(t - s.Start);
        compose.SetShaderParameter($"{which}_es", new Vector2((float)g.Exposure, (float)g.Sat));
        compose.SetShaderParameter($"{which}_tint", new Vector3((float)g.R, (float)g.G, (float)g.B));
        var oc = StoryArt.Col(s.Plate.Out?.Color, Colors.Black);
        compose.SetShaderParameter($"{which}_fade", new Vector4(oc.R, oc.G, oc.B, (float)StoryTimeline.OutFade(s, t)));
    }

    /* ------------------------------------------------------------ cues -- */

    void Do(TimedStoryCue tc, bool instant = false)
    {
        var c = tc.Cue;
        try
        {
            switch (c.Do)
            {
                case "line":
                {
                    var id = c.Str("id")!;
                    if (!id.Contains('.')) id = $"{File.Conversation}.{id}";
                    var l = CineLines.Find(id, host.Ctx);
                    if (l.Raw == "") break;
                    var take = host.Voice?.Say(l.VoId, l.Raw);
                    // Labelled only where the file tags it; the sung line in italics.
                    // Gone by the time the picture is black (the end, a plate's fade out to black); into a
                    // plate's fade to black it fades out with the picture.
                    double secs = (take?.Sec ?? CineLines.Reading(l.Text)) + c.Num("linger", 0.7);
                    Say(l.Text, c.Str("tag"), Line.SubtitleFor(tc.T, secs), l.Sung, l.Sung, Line.SubtitleFade(tc.T, secs));
                    break;
                }
                case "say":
                {
                    var text = c.Str("text") ?? "";
                    bool sung = c.Bool("sung");
                    double secs = c.Num("dur", CineLines.Reading(text));
                    Say(text, c.Str("speaker"), Line.SubtitleFor(tc.T, secs), sung, sung || c.Bool("italic"), Line.SubtitleFade(tc.T, secs));
                    break;
                }
                case "sfx":
                    Sfx.Cine(c.Str("name")!, c.Num("gain", 1), c.Num("pan"));
                    break;
                case "music":
                {
                    if (host.Sound is not { } snd) break;
                    var mood = c.Str("mood") ?? "silence";
                    snd.CineMood = mood == "game" ? null : Enum.Parse<Mood>(mood, true);
                    double from = snd.CineIntensity, to = c.Num("intensity", 0.5), over = instant ? 0 : c.Num("over");
                    if (over > 0) tweens.Add((tc.T, tc.T + over, k => snd.CineIntensity = from + (to - from) * k));
                    else snd.CineIntensity = to;
                    break;
                }
                case "bus":
                {
                    double over = instant ? 0 : c.Num("over");
                    if (c.Has("lowpass") && low != null)
                    {
                        // Moved in octaves, so a muffle closes evenly to the ear.
                        double f0 = Math.Log2(low.CutoffHz), f1 = Math.Log2(Math.Clamp(c.Num("lowpass"), 20, 20000));
                        var lp = low;
                        tweens.Add((tc.T, tc.T + over, k => lp.CutoffHz = (float)Math.Pow(2, f0 + (f1 - f0) * k)));
                    }
                    if (c.Has("gain") && amp != null)
                    {
                        double g0 = amp.VolumeDb, g1 = c.Num("gain");
                        var a = amp;
                        tweens.Add((tc.T, tc.T + over, k => a.VolumeDb = (float)(g0 + (g1 - g0) * k)));
                    }
                    break;
                }
                case "sound":
                    Sound(c, tc.T);
                    break;
                case "stop":
                    if (c.Str("id") is string sid && sounds.TryGetValue(sid, out var s)) Fade(s.P, tc.T, c.Num("fade", 0.3), stop: true);
                    break;
            }
        }
        catch (Exception e) { GD.PushWarning($"storybook {File.Id} at {tc.T:0.00}: {c.Do} failed: {e.Message}"); }
    }

    /// <summary>A subtitle, if any of it is left before the black (none: not shown at all).</summary>
    void Say(string text, string? who, double seconds, bool sung, bool italics, double fade)
    {
        if (seconds > 0.05) Bars.Say(text, who, seconds, sung, italics: italics, fade: fade);
    }

    /// <summary>A sound file on its own player (its own small bus when it is panned), through the storybook's muffle.</summary>
    void Sound(StoryCue c, double at)
    {
        var file = c.Str("file");
        if (file == null || !ResourceLoader.Exists(file)) { GD.PushWarning($"storybook: no sound {file}"); return; }
        var stream = GD.Load<AudioStream>(file);
        if (c.Bool("loop"))
            switch (stream)
            {
                case AudioStreamOggVorbis ogg: ogg.Loop = true; break;
                case AudioStreamWav wav: wav.LoopMode = AudioStreamWav.LoopModeEnum.Forward; wav.LoopEnd = (int)(wav.GetLength() * wav.MixRate); break;
                case AudioStreamMP3 mp3: mp3.Loop = true; break;
            }
        string id = c.Str("id") ?? file;
        if (sounds.Remove(id, out var was)) { was.P.QueueFree(); DropBus(was.Bus); }
        string bus = "Master";
        double pan = c.Num("pan");
        if (Math.Abs(pan) > 0.001)
        {
            bus = $"Storybook {id}";
            AudioServer.AddBus();
            int i = AudioServer.BusCount - 1;
            AudioServer.SetBusName(i, bus);
            AudioServer.SetBusSend(i, "Master");
            AudioServer.AddBusEffect(i, new AudioEffectPanner { Pan = (float)Math.Clamp(pan, -1, 1) });
        }
        double gain = c.Num("gain");
        var p = new AudioStreamPlayer { Stream = stream, Bus = bus, VolumeDb = (float)gain };
        AddChild(p);
        p.Play();
        sounds[id] = (p, bus);
        double fade = c.Num("fade");
        if (fade > 0)
        {
            p.VolumeDb = -60;
            tweens.Add((at, at + fade, k => { if (IsInstanceValid(p)) p.VolumeDb = (float)(-60 + (gain + 60) * Math.Sqrt(k)); }));
        }
    }

    void Fade(AudioStreamPlayer p, double at, double over, bool stop)
    {
        float from = p.VolumeDb;
        tweens.Add((at, at + Math.Max(0.01, over), k =>
        {
            if (!IsInstanceValid(p)) return;
            p.VolumeDb = (float)(from + (-60 - from) * k * k);
            if (k >= 1 && stop) p.Stop();
        }));
    }

    static void DropBus(string bus)
    {
        if (bus == "Master") return;
        int i = AudioServer.GetBusIndex(bus);
        if (i > 0) AudioServer.RemoveBus(i);
    }

    /* ------------------------------------------------------ skip and end -- */

    void Skipping(double dt)
    {
        bool held = host.SkipHeld();
        if (held && StoryTimeline.CanSkip(t, seen, File.Skip)) skipHeld += dt;
        else skipHeld = Math.Max(0, skipHeld - dt * 3);
        Bars.Skip((float)(skipHeld / File.Skip.Hold));
        if (skipHeld < File.Skip.Hold) return;
        Skip();
    }

    /// <summary>A skip: black at once, every sound gone over 0.15 s, then it ends as skipped.</summary>
    public void Skip()
    {
        if (Skipped || over) return;
        Skipped = true;
        skipAt = t;
        Bars.Skip(0);
        Bars.Hush();
        Bars.Frame(1, 1);
        foreach (var v in live.Values) v.QueueFree();
        live.Clear();
        screen.Visible = false;
        tweens.Clear();
        if (amp != null)
        {
            double g0 = amp.VolumeDb;
            var a = amp;
            tweens.Add((t, t + 0.15, k => a.VolumeDb = (float)(g0 + (-80 - g0) * k)));
        }
        foreach (var s in sounds.Values) Fade(s.P, t, 0.15, stop: true);
    }

    double skipAt;

    void Finish()
    {
        if (over) return;
        over = true;
        SetProcess(false);
        foreach (var v in live.Values) v.QueueFree();
        live.Clear();
        foreach (var s in sounds.Values) { s.P.Stop(); s.P.QueueFree(); DropBus(s.Bus); }
        sounds.Clear();
        if (host.Sound is { } snd) { snd.CineMood = Mood.Silence; snd.CineIntensity = 0; }
        // It ends on black; the bars stay for whoever takes them (C01, chained), else they go with it.
        Bars.Frame(1, 1);
        Bars.Hush();
        Unmuffle();
        GD.Print($"storybook: {File.Id} {(Skipped ? "skipped" : "done")} at {t:0.00}s (wall {Time.GetTicksMsec() / 1000.0:0.00}s)");
        done(Skipped);
        QueueFree();
    }

    void Unmuffle()
    {
        foreach (var e in new AudioEffect?[] { low, amp })
        {
            if (e == null) continue;
            for (int i = AudioServer.GetBusEffectCount(0) - 1; i >= 0; i--)
                if (AudioServer.GetBusEffect(0, i) == e) AudioServer.RemoveBusEffect(0, i);
        }
        low = null; amp = null;
    }

    /// <summary>--sb-shots: the frame drawn at its moment, saved where the game's pictures go.</summary>
    void PostDraw()
    {
        if (shotDue == null) return;
        var d = ProjectSettings.GlobalizePath("res://.shots");
        DirAccess.MakeDirRecursiveAbsolute(d);
        var f = $"{d}/{shotDue}.png";
        GetViewport().GetTexture().GetImage().SavePng(f);
        GD.Print($"saved {f} at {t:0.00}s");
        shotDue = null;
        if (shots.Count == 0 && Args.Has("storybook")) GetTree().Quit();
    }
}
