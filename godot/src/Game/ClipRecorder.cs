using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// The rolling last 30 seconds for a bug report: every 1/15 s the final picture is scaled to 960x540 on the GPU (a
/// SubViewport showing the root viewport's texture), read back without stalling (RenderingDevice async readback; the
/// image fallback under Compatibility or headless), and JPEG-encoded on a worker thread into a ring held in memory.
/// Frame times (every frame) and this node's own main-thread cost are kept for the report's stats.
/// </summary>
public partial class ClipRecorder : Node
{
    public static ClipRecorder? Instance { get; private set; }
    public const int Width = 960, Height = 540;
    public const double Fps = 15;
    public const double Seconds = 30;
    const int RingMax = (int)(Seconds * Fps);

    /// <summary>On while the setting is on (and --no-bug-clip is not given). Off in the demo flavor unless --bug-clip is given
    /// (the owner, 19 Nov: "TURN IT OFF FOR DEMO BUILD": its 2 MB readback 15 times a second cost a large-object GC about every 10 s).
    /// Off in the den test build too, a tester's build of the demo's den (24 Nov, the RAM lane: its garbage was the managed heap's
    /// 0.5 -> 1.25 GB sawtooth in the den and the town, about 0.7 GB of the den's RAM peak over its 3 GB budget).</summary>
    public bool Enabled => !Args.Has("no-bug-clip") && Settings.Current.BugClip
        && (!(SurvivorUnchained.Core.Demo.On || SurvivorUnchained.Core.DenTest.On) || Args.Has("bug-clip"));

    bool Frozen;
    SubViewport? sub;
    bool tried, useRd;
    Rid rdTex;
    RenderingDevice.DataFormat fmt;
    double acc;
    int pending;      // readbacks asked for and not yet delivered
    int inFlight;     // frames handed to the worker and not yet in the ring
    int epoch;        // bumped by Resume so a late frame of an old ring is dropped
    int grabs;

    readonly BlockingCollection<(byte[] Raw, int Epoch)> work = new(4);
    Thread? worker;
    readonly LinkedList<byte[]> ring = new();
    readonly object ringLock = new();
    long jpegBytes; int jpegCount;

    // frame times and own cost, trimmed to the last 30 s
    readonly Queue<double> frames = new();
    double framesSum;
    readonly Queue<double> cost = new();
    double costSum;
    readonly object statLock = new();
    readonly Stopwatch sw = new();
    double lastPerf;
    double clock;
    bool sampleSaved;

    public override void _Ready()
    {
        Instance = this;
        Name = "ClipRecorder";
        ProcessMode = ProcessModeEnum.Always;
    }

    public override void _ExitTree()
    {
        work.CompleteAdding();
        // (quit-crash) the encoder makes Godot Images: it ends its last frames here, not inside the engine's teardown
        worker?.Join(1000);
        if (Instance == this) Instance = null;
    }

    void Setup()
    {
        tried = true;
        sub = new SubViewport { Size = new Vector2I(Width, Height), TransparentBg = false, Disable3D = true, RenderTargetUpdateMode = SubViewport.UpdateMode.Always };
        var tr = new TextureRect
        {
            Texture = GetTree().Root.GetTexture(), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize,
            StretchMode = TextureRect.StretchModeEnum.Scale, Size = new Vector2(Width, Height), MouseFilter = Control.MouseFilterEnum.Ignore,
        };
        sub.AddChild(tr);
        AddChild(sub);
        var rd = RenderingServer.GetRenderingDevice();
        useRd = rd != null && DisplayServer.GetName() != "headless";
        if (!useRd) GD.Print("clip: no RenderingDevice (Compatibility or headless): the Image readback fallback is in use");
        worker = new Thread(Encode) { IsBackground = true, Name = "ClipEncoder" };
        worker.Start();
    }

    void Encode()
    {
        foreach (var (raw, ep) in work.GetConsumingEnumerable())
        {
            try
            {
                var img = Image.CreateFromData(Width, Height, false, Image.Format.Rgba8, raw);
                img.Convert(Image.Format.Rgb8);
                var jpg = img.SaveJpgToBuffer(0.7f);
                lock (ringLock)
                {
                    if (ep == epoch)
                    {
                        ring.AddLast(jpg);
                        while (ring.Count > RingMax) ring.RemoveFirst();
                        jpegBytes += jpg.Length; jpegCount++;
                    }
                }
            }
            catch (Exception e) { GD.PushWarning("clip: encode failed: " + e.Message); }
            finally { Interlocked.Decrement(ref inFlight); }
        }
    }

    void Hand(byte[] raw)
    {
        if (Frozen || raw == null || raw.Length < Width * Height * 4) return;
        if (Interlocked.Increment(ref inFlight) > 4 || !work.TryAdd((raw, epoch))) Interlocked.Decrement(ref inFlight);
    }

    void OnReadback(byte[] data)
    {
        long t = Stopwatch.GetTimestamp();
        pending--;
        if (!Frozen) Hand(data);
        AddCost((Stopwatch.GetTimestamp() - t) * 1000.0 / Stopwatch.Frequency, false);
    }

    double thisFrameCost;
    void AddCost(double ms, bool close)
    {
        thisFrameCost += ms;
        if (!close) return;
        lock (statLock)
        {
            cost.Enqueue(thisFrameCost); costSum += thisFrameCost;
            while (cost.Count > Math.Max(1, frames.Count)) costSum -= cost.Dequeue();
        }
        thisFrameCost = 0;
    }

    public override void _Process(double delta)
    {
        bool perf = Args.Has("clip-perf");
        long t0 = Stopwatch.GetTimestamp();
        clock += delta;
        lock (statLock)
        {
            frames.Enqueue(delta * 1000); framesSum += delta * 1000;
            while (frames.Count > 1 && framesSum > Seconds * 1000) framesSum -= frames.Dequeue();
        }
        if (Enabled && !Frozen)
        {
            if (!tried) Setup();
            acc += delta;
            if (acc >= 1.0 / Fps - 0.002)
            {
                acc = Math.Min(acc - 1.0 / Fps, 1.0 / Fps);
                Grab();
            }
        }
        AddCost((Stopwatch.GetTimestamp() - t0) * 1000.0 / Stopwatch.Frequency, true);
        if (perf && clock - lastPerf >= 10) { lastPerf = clock; Report(); }
        if (perf && !sampleSaved && clock > 14) SaveSample();
    }

    void Grab()
    {
        if (sub == null || pending >= 3) return;
        var tex = sub.GetTexture();
        if (useRd)
        {
            var rd = RenderingServer.GetRenderingDevice();
            if (rdTex == default)
            {
                rdTex = RenderingServer.TextureGetRdTexture(tex.GetRid());
                if (rdTex == default) { useRd = false; return; }
                fmt = rd.TextureGetFormat(rdTex).Format;
                GD.Print("clip: async readback path, texture format " + fmt);
            }
            pending++;
            grabs++;
            if (rd.TextureGetDataAsync(rdTex, 0, Callable.From<byte[]>(OnReadback)) != Error.Ok) pending--;
        }
        else
        {
            var img = tex.GetImage();
            if (img == null) return;
            if (img.GetFormat() != Image.Format.Rgba8) img.Convert(Image.Format.Rgba8);
            grabs++;
            Hand(img.GetData());
        }
    }

    public (List<byte[]> Jpegs, double Fps) Freeze()
    {
        Frozen = true;
        var sw2 = Stopwatch.StartNew();
        while (Volatile.Read(ref inFlight) > 0 && sw2.ElapsedMilliseconds < 300) Thread.Sleep(5);
        lock (ringLock) return (new List<byte[]>(ring), Fps);
    }

    public void Resume()
    {
        lock (ringLock) { ring.Clear(); epoch++; }
        acc = 0;
        Frozen = false;
    }

    /// <summary>Restart recording without clearing the ring.</summary>
    public void Thaw() { acc = 0; Frozen = false; }

    public IReadOnlyList<double> FrameMs()
    {
        lock (statLock) return frames.ToArray();
    }

    public (double AvgMs, double MaxMs, int Grabs) CaptureCost()
    {
        lock (statLock)
        {
            if (cost.Count == 0) return (0, 0, grabs);
            double sum = 0, max = 0;
            foreach (var c in cost) { sum += c; if (c > max) max = c; }
            return (sum / cost.Count, max, grabs);
        }
    }

    void Report()
    {
        var f = FrameMs();
        var s = new List<double>(f); s.Sort();
        double avg = 0; foreach (var x in s) avg += x;
        if (s.Count > 0) avg /= s.Count;
        double p99 = s.Count > 0 ? s[Math.Min(s.Count - 1, (int)(s.Count * 0.99))] : 0, max = s.Count > 0 ? s[^1] : 0;
        var c = CaptureCost();
        int n; double kb;
        lock (ringLock) { n = ring.Count; kb = jpegCount > 0 ? jpegBytes / (double)jpegCount / 1024 : 0; }
        GD.Print($"clip: frame ms avg {avg:F2} p99 {p99:F2} max {max:F2}; capture ms avg {c.AvgMs:F3} max {c.MaxMs:F3}; grabs {c.Grabs}; ring {n} frames; jpeg avg {kb:F0} KB (enabled {Enabled})");
    }

    void SaveSample()
    {
        if (!Enabled) { sampleSaved = true; return; }
        byte[]? mid = null;
        lock (ringLock) { if (ring.Count > 0) { int i = 0, k = ring.Count / 2; foreach (var j in ring) { if (i++ == k) { mid = j; break; } } } }
        if (mid == null) return;
        sampleSaved = true;
        var dir = ProjectSettings.GlobalizePath("res://.shots/clip_perf");
        System.IO.Directory.CreateDirectory(dir);
        System.IO.File.WriteAllBytes(dir + "/sample.jpg", mid);
        GD.Print("clip: sample saved " + dir + "/sample.jpg");
    }
}
