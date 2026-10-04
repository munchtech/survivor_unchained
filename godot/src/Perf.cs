using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Text;
using Godot;

namespace SurvivorUnchained;

/// <summary>
/// The frame, measured (docs/PERF_AUDIT.md says how to read it):
///
///   -- --perf NAME [--perf-warm W] [--perf-for S] [--perf-window T] [--perf-vsync]
///
/// waits W seconds (default 8: loading, the first shaders, the horde
/// filling), then records every frame for S seconds (default 30) and quits,
/// writing godot/.shots/perf/NAME.json (the summary) and NAME.csv (every
/// frame). Each frame keeps its wall time; the main thread's own work (from
/// the first process callback to the last) and the parts of it timed on
/// their own (the fight's ticks, the survivor, the crowd, the effects, the
/// HUD, the sound); the renderer's CPU time and the GPU's time (Godot's
/// timestamps); draw calls and objects in the picture and in the shadows;
/// what C# allocated, collections, pipelines compiled, memory. Every T
/// seconds (default 10) a line of the window so far is printed, for long
/// runs (a whole arena). Vsync is off unless --perf-vsync: what is measured
/// is the headroom, not the monitor. Measuring allocates nothing while it
/// records, so what it reports is the game's own.
/// </summary>
public partial class Perf : Node
{
    /// <summary>What the game adds to each window's line (the horde, the sound's voices).</summary>
    public static Func<string> Note = () => "";
    /// <summary>The game's own numbers for each frame (foes, voices...): their
    /// names, and a filler that writes them into the array it is given.</summary>
    public static string[] CounterNames = Array.Empty<string>();
    public static Action<double[]> Counters = _ => { };
    /// <summary>Done every frame before measuring it (--perf-off: what is taken out of the picture).</summary>
    public Action Each = () => { };

    /// <summary>Parts of the frame timed on their own (Begin and End round
    /// them; nothing is done when not measuring).</summary>
    public enum Part { Sim, Player, Crowd, Fx, Hud, Sound, Zone }
    const int Parts = 7;
    static readonly string[] PartNames = { "sim", "player", "crowd", "fx", "hud", "sound", "zone" };
    static readonly double[] partMs = new double[Parts];
    static readonly long[] partFrom = new long[Parts];
    static bool live;
    static readonly double TickMs = 1000.0 / Stopwatch.Frequency;
    /// <summary>The frame's first process callback (Start), on the stopwatch's clock.</summary>
    static long frameFrom;

    public static void Begin(Part p) { if (live) partFrom[(int)p] = Stopwatch.GetTimestamp(); }
    public static void End(Part p) { if (live) partMs[(int)p] += (Stopwatch.GetTimestamp() - partFrom[(int)p]) * TickMs; }

    /// <summary>A part timed to the end of a block (`using var _ = new Perf.Span(...)`).</summary>
    public readonly struct Span : IDisposable
    {
        readonly Part part;
        public Span(Part p) { part = p; Begin(p); }
        public void Dispose() => End(part);
    }

    /// <summary>First in every frame's process callbacks: where the main thread's own work begins.</summary>
    sealed partial class Start : Node
    {
        public override void _Ready() { ProcessPriority = int.MinValue; ProcessMode = ProcessModeEnum.Always; }
        public override void _Process(double delta) => frameFrom = Stopwatch.GetTimestamp();
    }

    struct Frame
    {
        public double T, Ms, Main, Physics, RenderCpu, Setup, Gpu;
        public long Alloc, MainAlloc, Primitives;
        public int Draws, Objects, ShadowDraws, ShadowObjects, CanvasDraws, Pipelines, Gen0, Gen1, Gen2;
    }

    string name = "";
    double warm, span, window, t, nextWindow;
    long last;
    long lastAlloc, lastMainAlloc;
    int lastGen0, lastGen1, lastGen2;
    double lastPipes, coldPipes;
    TimeSpan pauseAtStart;
    bool recording;
    Rid vp;
    readonly List<Frame> frames = new(16384);
    /// <summary>Each frame's parts (Parts to a frame) and counters (CounterNames.Length to a frame).</summary>
    readonly List<double> parts = new(65536), extras = new(65536);
    double[] counters = Array.Empty<double>();
    string[] extraNames = Array.Empty<string>();
    readonly double[] recent = new double[600];
    int windowFrom;
    readonly List<string> hitches = new();
    readonly List<string> windows = new();

    public static bool On => Args.Has("perf");

    public override void _Ready()
    {
        if (!On) { SetProcess(false); return; }
        name = Args.Get("perf") is { } n && n != "1" ? n : "perf";
        warm = Args.Num("perf-warm", 8);
        span = Args.Num("perf-for", 30);
        window = Args.Num("perf-window", 10);
        ProcessMode = ProcessModeEnum.Always;
        // Last in the frame, so its clock brackets everything else.
        ProcessPriority = int.MaxValue;
        // (Process order is by priority across the tree, wherever the node sits.)
        AddChild(new Start());
        if (!Args.Has("perf-vsync"))
        {
            DisplayServer.WindowSetVsyncMode(DisplayServer.VSyncMode.Disabled);
            Engine.MaxFps = 0;
        }
        vp = GetViewport().GetViewportRid();
        RenderingServer.ViewportSetMeasureRenderTime(vp, true);
        last = Stopwatch.GetTimestamp();
        GD.Print($"perf {name}: warm {warm}s, recording {span}s, vsync {(Args.Has("perf-vsync") ? "on" : "off")}, " +
                 $"window {DisplayServer.WindowGetSize()}, screen {DisplayServer.ScreenGetSize()}, {RenderingServer.GetVideoAdapterName()} ({RenderingServer.GetVideoAdapterApiVersion()})");
    }

    static double Pipes() =>
        Performance.GetMonitor(Performance.Monitor.PipelineCompilationsCanvas) + Performance.GetMonitor(Performance.Monitor.PipelineCompilationsMesh) +
        Performance.GetMonitor(Performance.Monitor.PipelineCompilationsSurface) + Performance.GetMonitor(Performance.Monitor.PipelineCompilationsDraw) +
        Performance.GetMonitor(Performance.Monitor.PipelineCompilationsSpecialization);

    public override void _Process(double delta)
    {
        long now = Stopwatch.GetTimestamp();
        double ms = (now - last) * TickMs, main = (now - frameFrom) * TickMs;
        last = now;
        t += delta;
        Each();
        long alloc = GC.GetTotalAllocatedBytes(false), mainAlloc = GC.GetAllocatedBytesForCurrentThread();
        int g0 = GC.CollectionCount(0), g1 = GC.CollectionCount(1), g2 = GC.CollectionCount(2);
        double pipes = Pipes();
        if (!recording)
        {
            // Pipelines compiled while warming: the first shaders' cost (cold with an empty shader cache).
            coldPipes = pipes;
            if (t >= warm)
            {
                recording = live = true;
                pauseAtStart = GC.GetTotalPauseDuration();
                extraNames = CounterNames;
                counters = new double[extraNames.Length];
                nextWindow = t + window;
                GD.Print($"perf {name}: recording from {t:0.0}s ({coldPipes:0} pipelines compiled while warming)");
            }
            Remember(alloc, mainAlloc, g0, g1, g2, pipes);
            Array.Clear(partMs);
            return;
        }
        var f = new Frame
        {
            T = t, Ms = ms, Main = main,
            Physics = Performance.GetMonitor(Performance.Monitor.TimePhysicsProcess) * 1000,
            RenderCpu = RenderingServer.ViewportGetMeasuredRenderTimeCpu(vp),
            Setup = RenderingServer.GetFrameSetupTimeCpu(),
            Gpu = RenderingServer.ViewportGetMeasuredRenderTimeGpu(vp),
            Alloc = alloc - lastAlloc, MainAlloc = mainAlloc - lastMainAlloc,
            Gen0 = g0 - lastGen0, Gen1 = g1 - lastGen1, Gen2 = g2 - lastGen2,
            Pipelines = (int)(pipes - lastPipes),
            Draws = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Visible, RenderingServer.ViewportRenderInfo.DrawCallsInFrame),
            Objects = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Visible, RenderingServer.ViewportRenderInfo.ObjectsInFrame),
            Primitives = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Visible, RenderingServer.ViewportRenderInfo.PrimitivesInFrame),
            ShadowDraws = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Shadow, RenderingServer.ViewportRenderInfo.DrawCallsInFrame),
            ShadowObjects = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Shadow, RenderingServer.ViewportRenderInfo.ObjectsInFrame),
            CanvasDraws = RenderingServer.ViewportGetRenderInfo(vp, RenderingServer.ViewportRenderInfoType.Canvas, RenderingServer.ViewportRenderInfo.DrawCallsInFrame),
        };
        frames.Add(f);
        parts.AddRange(partMs);
        Array.Clear(partMs);
        Counters(counters);
        extras.AddRange(counters);
        Remember(alloc, mainAlloc, g0, g1, g2, pipes);
        // A hitch: a frame well over the run's usual, with what came with it.
        if (frames.Count > 30 && ms > Math.Max(25, 2.5 * Median()))
            hitches.Add($"{t:0.00}s {ms:0.0}ms (main {f.Main:0.0}: {PartsOf(frames.Count - 1)}; render cpu {f.RenderCpu:0.0}, gpu {f.Gpu:0.0}) pipelines {f.Pipelines} gc {f.Gen0}/{f.Gen1}/{f.Gen2} alloc {f.Alloc / 1024}KB {Note()}");
        if (t >= nextWindow)
        {
            nextWindow += window;
            var line = $"[{t,6:0.0}s] {Summary(windowFrom, frames.Count)} | {Note()}";
            windowFrom = frames.Count;
            windows.Add(line);
            GD.Print($"perf {line}");
        }
        if (t >= warm + span) Finish();
    }

    /// <summary>--perf-dump: what is in the scene to draw, by the branch it
    /// hangs from (the survivor, the crowd, the zone's flora and props, the
    /// effects): meshes, surfaces, vertices, blend shapes, instances, lights
    /// and their shadows, decals, particles.</summary>
    void Dump()
    {
        var rows = new SortedDictionary<string, long[]>();
        // meshes, surfaces, vertices (x instances), blend shapes, multimeshes, instances, omni, shadowed, spot, decals, particles, visible-range'd, shadow casters
        void Walk(Node n, string branch, int depth)
        {
            if (n is Node3D n3 && !n3.Visible) return;
            if (n is CanvasItem ci && !ci.Visible) return;
            if (depth <= 4 && n is Node3D && n.GetChildCount() > 0) branch = branch == "" ? n.Name : depth <= 3 ? $"{branch}/{n.Name}" : branch;
            if (!rows.TryGetValue(branch, out var r)) rows[branch] = r = new long[13];
            switch (n)
            {
                case MeshInstance3D mi when mi.Mesh != null:
                    r[0]++; r[1] += mi.Mesh.GetSurfaceCount();
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++) r[2] += mi.Mesh is ArrayMesh am ? am.SurfaceGetArrayLen(s) : 0;
                    r[3] += mi.Mesh is ArrayMesh bm ? bm.GetBlendShapeCount() : 0;
                    if (mi.VisibilityRangeEnd > 0) r[11]++;
                    if (mi.CastShadow != GeometryInstance3D.ShadowCastingSetting.Off) r[12]++;
                    break;
                case MultiMeshInstance3D mm when mm.Multimesh?.Mesh != null:
                    int count = mm.Multimesh.VisibleInstanceCount >= 0 ? mm.Multimesh.VisibleInstanceCount : mm.Multimesh.InstanceCount;
                    r[4]++; r[5] += count;
                    for (int s = 0; s < mm.Multimesh.Mesh.GetSurfaceCount(); s++) r[2] += (long)(mm.Multimesh.Mesh is ArrayMesh am2 ? am2.SurfaceGetArrayLen(s) : 0) * count;
                    r[1] += mm.Multimesh.Mesh.GetSurfaceCount();
                    if (mm.VisibilityRangeEnd > 0) r[11]++;
                    if (mm.CastShadow != GeometryInstance3D.ShadowCastingSetting.Off) r[12]++;
                    break;
                case OmniLight3D o: r[6]++; if (o.ShadowEnabled) r[7]++; break;
                case SpotLight3D sp: r[8]++; if (sp.ShadowEnabled) r[7]++; break;
                case Decal: r[9]++; break;
                case GpuParticles3D gp: r[10] += gp.Amount; break;
            }
            foreach (var c in n.GetChildren()) Walk(c, branch, depth + 1);
        }
        Walk(GetTree().Root, "", 0);
        GD.Print("perf dump: branch | meshes surfaces vertices blendshapes | multimeshes instances | omni shadowed spot | decals particles | ranged casters");
        foreach (var (k, r) in rows)
            if (r.Any(x => x != 0))
                GD.Print($"perf dump: {k} | {r[0]} {r[1]} {r[2]} {r[3]} | {r[4]} {r[5]} | {r[6]} {r[7]} {r[8]} | {r[9]} {r[10]} | {r[11]} {r[12]}");
    }

    string PartsOf(int fi) => string.Join(" ", Enumerable.Range(0, Parts).Select(i => $"{PartNames[i]} {parts[fi * Parts + i]:0.0}"));

    void Remember(long alloc, long mainAlloc, int g0, int g1, int g2, double pipes)
    {
        lastAlloc = alloc; lastMainAlloc = mainAlloc; lastGen0 = g0; lastGen1 = g1; lastGen2 = g2; lastPipes = pipes;
    }

    double median;
    int medianAt;
    /// <summary>The usual frame of the last ten seconds or so (sorted in a kept array: no garbage).</summary>
    double Median()
    {
        if (frames.Count - medianAt > 120 || median == 0)
        {
            medianAt = frames.Count;
            int n = Math.Min(recent.Length, frames.Count);
            for (int i = 0; i < n; i++) recent[i] = frames[frames.Count - 1 - i].Ms;
            Array.Sort(recent, 0, n);
            median = recent[n / 2];
        }
        return median;
    }

    /// <summary>The slowest share of frames, averaged (a "1% low" as frame time).</summary>
    static double Worst(List<double> sorted, double share)
    {
        int n = Math.Max(1, (int)Math.Ceiling(sorted.Count * share));
        return sorted.Skip(sorted.Count - n).Average();
    }

    double PartMean(int from, int to, int i)
    {
        double s = 0;
        for (int fi = from; fi < to; fi++) s += parts[fi * Parts + i];
        return s / Math.Max(1, to - from);
    }

    string Summary(int from, int to)
    {
        if (to <= from) return "no frames";
        var w = frames.GetRange(from, to - from);
        var ms = w.Select(x => x.Ms).OrderBy(x => x).ToList();
        double mean = ms.Average();
        var each = string.Join(" ", Enumerable.Range(0, Parts).Select(i => $"{PartNames[i]} {PartMean(from, to, i):0.00}"));
        return string.Create(CultureInfo.InvariantCulture,
            $"{1000 / mean:0} fps, {mean:0.00}ms (p50 {ms[ms.Count / 2]:0.00}, 1% {Worst(ms, 0.01):0.0}, 0.1% {Worst(ms, 0.001):0.0}, max {ms[^1]:0.0}) " +
            $"main {w.Average(x => x.Main):0.00}ms ({each}) render {w.Average(x => x.RenderCpu + x.Setup):0.00}ms gpu {w.Average(x => x.Gpu):0.00}ms " +
            $"draws {w.Average(x => x.Draws):0}+{w.Average(x => x.ShadowDraws):0}sh+{w.Average(x => x.CanvasDraws):0}ui " +
            $"alloc {w.Average(x => x.Alloc) / 1024:0.0}KB/f (main {w.Average(x => x.MainAlloc) / 1024:0.0}) gc {w.Sum(x => x.Gen0)}/{w.Sum(x => x.Gen1)}/{w.Sum(x => x.Gen2)} pipes {w.Sum(x => x.Pipelines)}");
    }

    void Finish()
    {
        SetProcess(false);
        live = false;
        var dir = ProjectSettings.GlobalizePath("res://.shots/perf");
        DirAccess.MakeDirRecursiveAbsolute(dir);
        var ms = frames.Select(x => x.Ms).OrderBy(x => x).ToList();
        double mean = ms.Average();
        var inv = CultureInfo.InvariantCulture;
        string N(double v) => v.ToString("0.###", inv);
        var j = new StringBuilder();
        j.Append("{\n");
        void P(string key, string v, bool end = false) => j.Append($"  \"{key}\": {v}{(end ? "" : ",")}\n");
        P("name", $"\"{name}\"");
        P("args", $"\"{string.Join(' ', OS.GetCmdlineUserArgs()).Replace("\"", "'")}\"");
        P("adapter", $"\"{RenderingServer.GetVideoAdapterName()}\"");
        P("window", $"\"{DisplayServer.WindowGetSize().X}x{DisplayServer.WindowGetSize().Y}\"");
        P("frames", frames.Count.ToString(inv));
        P("seconds", N(frames.Sum(x => x.Ms) / 1000));
        P("fps_mean", N(1000 / mean));
        P("ms_mean", N(mean));
        P("ms_p50", N(ms[ms.Count / 2]));
        P("ms_p99", N(ms[(int)(ms.Count * 0.99)]));
        P("ms_low1", N(Worst(ms, 0.01)));
        P("ms_low01", N(Worst(ms, 0.001)));
        P("ms_max", N(ms[^1]));
        P("fps_low1", N(1000 / Worst(ms, 0.01)));
        P("fps_low01", N(1000 / Worst(ms, 0.001)));
        P("cpu_main_ms", N(frames.Average(x => x.Main)));
        P("cpu_main_p99_ms", N(frames.Select(x => x.Main).OrderBy(x => x).ElementAt((int)(frames.Count * 0.99))));
        for (int i = 0; i < Parts; i++) P("cpu_" + PartNames[i] + "_ms", N(PartMean(0, frames.Count, i)));
        P("cpu_physics_max_ms", N(frames.Average(x => x.Physics)));
        P("cpu_render_ms", N(frames.Average(x => x.RenderCpu)));
        P("cpu_setup_ms", N(frames.Average(x => x.Setup)));
        P("gpu_ms", N(frames.Average(x => x.Gpu)));
        P("gpu_p99_ms", N(frames.Select(x => x.Gpu).OrderBy(x => x).ElementAt((int)(frames.Count * 0.99))));
        P("draws", N(frames.Average(x => x.Draws)));
        P("draws_shadow", N(frames.Average(x => x.ShadowDraws)));
        P("draws_canvas", N(frames.Average(x => x.CanvasDraws)));
        P("objects", N(frames.Average(x => x.Objects)));
        P("objects_shadow", N(frames.Average(x => x.ShadowObjects)));
        P("primitives", N(frames.Average(x => (double)x.Primitives)));
        P("alloc_kb_frame", N(frames.Average(x => x.Alloc) / 1024.0));
        P("alloc_main_kb_frame", N(frames.Average(x => x.MainAlloc) / 1024.0));
        P("gc", $"[{frames.Sum(x => x.Gen0)}, {frames.Sum(x => x.Gen1)}, {frames.Sum(x => x.Gen2)}]");
        P("gc_pause_ms", N((GC.GetTotalPauseDuration() - pauseAtStart).TotalMilliseconds));
        P("pipelines_warm", N(coldPipes));
        P("pipelines_recorded", frames.Sum(x => x.Pipelines).ToString(inv));
        P("video_mem_mb", N(Performance.GetMonitor(Performance.Monitor.RenderVideoMemUsed) / 1048576));
        P("texture_mem_mb", N(Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576));
        P("buffer_mem_mb", N(Performance.GetMonitor(Performance.Monitor.RenderBufferMemUsed) / 1048576));
        P("static_mem_mb", N(Performance.GetMonitor(Performance.Monitor.MemoryStatic) / 1048576));
        P("managed_heap_mb", N(GC.GetTotalMemory(false) / 1048576.0));
        P("working_set_mb", N(System.Environment.WorkingSet / 1048576.0));
        P("nodes", N(Performance.GetMonitor(Performance.Monitor.ObjectNodeCount)));
        P("orphan_nodes", N(Performance.GetMonitor(Performance.Monitor.ObjectOrphanNodeCount)));
        P("physics_active", N(Performance.GetMonitor(Performance.Monitor.Physics3DActiveObjects)));
        P("physics_pairs", N(Performance.GetMonitor(Performance.Monitor.Physics3DCollisionPairs)));
        int k = extraNames.Length;
        for (int i = 0; i < k; i++)
        {
            double sum = 0, max = 0;
            for (int fi = 0; fi < frames.Count; fi++) { double v = extras[fi * k + i]; sum += v; max = Math.Max(max, v); }
            P(extraNames[i], N(sum / Math.Max(1, frames.Count)));
            P(extraNames[i] + "_max", N(max));
        }
        P("windows", "[\n" + string.Join(",\n", windows.Select(w => $"    \"{w}\"")) + "\n  ]");
        P("hitches", "[\n" + string.Join(",\n", hitches.Take(200).Select(h => $"    \"{h}\"")) + "\n  ]", true);
        j.Append("}\n");
        using (var f = FileAccess.Open($"{dir}/{name}.json", FileAccess.ModeFlags.Write)) f?.StoreString(j.ToString());

        var c = new StringBuilder("t,ms,main,physics_max,render_cpu,setup,gpu,draws,objects,primitives,shadow_draws,shadow_objects,canvas_draws,alloc,main_alloc,gen0,gen1,gen2,pipelines");
        foreach (var p in PartNames) c.Append(',').Append(p);
        foreach (var e in extraNames) c.Append(',').Append(e);
        c.Append('\n');
        for (int fi = 0; fi < frames.Count; fi++)
        {
            var x = frames[fi];
            c.Append(string.Create(inv, $"{x.T:0.000},{x.Ms:0.000},{x.Main:0.000},{x.Physics:0.000},{x.RenderCpu:0.000},{x.Setup:0.000},{x.Gpu:0.000},{x.Draws},{x.Objects},{x.Primitives},{x.ShadowDraws},{x.ShadowObjects},{x.CanvasDraws},{x.Alloc},{x.MainAlloc},{x.Gen0},{x.Gen1},{x.Gen2},{x.Pipelines}"));
            for (int i = 0; i < Parts; i++) c.Append(',').Append(parts[fi * Parts + i].ToString("0.###", inv));
            for (int i = 0; i < k; i++) c.Append(',').Append(extras[fi * k + i].ToString("0.##", inv));
            c.Append('\n');
        }
        using (var f = FileAccess.Open($"{dir}/{name}.csv", FileAccess.ModeFlags.Write)) f?.StoreString(c.ToString());
        GD.Print($"perf {name} done: {Summary(0, frames.Count)}");
        GD.Print($"perf {name}: {hitches.Count} hitches; wrote {dir}/{name}.json");
        foreach (var h in hitches.Take(12)) GD.Print($"perf hitch {h}");
        if (Args.Has("perf-dump")) Dump();
        GetTree().Quit();
    }
}
