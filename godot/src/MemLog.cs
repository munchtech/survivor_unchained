using System;
using System.Linq;
using Godot;

namespace SurvivorUnchained;

/// <summary>(dev, --mem-log N) Every N seconds (default 10) one log line of the game's own memory monitors: Godot's static
/// memory, video and texture memory, buffers, object, resource and node counts, orphan nodes, the .NET heap and the
/// process's working set and private bytes, with the zone. tools/perf/memrun.py samples the process from outside and
/// reads these lines from the same log (the tester lane, 23 Nov: a tester's build reached 6.8 GB). --mem-tex S: at S s
/// (default 60) one census of every live texture (RenderingServer.TextureDebugUsage): totals by folder for the imported ones,
/// by size and format for the ones made at runtime (no path), and the 40 biggest.</summary>
public partial class MemLog : Node
{
    readonly double every;
    double t;
    bool texDone;

    readonly double texAt = Args.Has("mem-tex") ? Args.Num("mem-tex", 60) : -1;

    public MemLog(double every) { this.every = Math.Max(1, every); ProcessMode = ProcessModeEnum.Always; }

    public override void _Process(double delta)
    {
        if (texAt >= 0 && Time.GetTicksMsec() / 1000.0 >= texAt && !texDone) { texDone = true; Textures(GetTree().Root); }
        if ((t += delta) < every) return;
        t = 0;
        Line(GetParent() is Play.Game g ? g.Zone?.Id ?? "-" : "-");
    }

    public static void Line(string where)
    {
        static double M(Performance.Monitor m) => Performance.GetMonitor(m) / 1048576.0;
        static long N(Performance.Monitor m) => (long)Performance.GetMonitor(m);
        using var me = System.Diagnostics.Process.GetCurrentProcess();
        GD.Print($"mem: t {Time.GetTicksMsec() / 1000.0:0} s zone {where} | static {M(Performance.Monitor.MemoryStatic):0} MB, " +
                 $"video {M(Performance.Monitor.RenderVideoMemUsed):0} MB, texture {M(Performance.Monitor.RenderTextureMemUsed):0} MB, " +
                 $"buffers {M(Performance.Monitor.RenderBufferMemUsed):0} MB | objects {N(Performance.Monitor.ObjectCount)}, " +
                 $"resources {N(Performance.Monitor.ObjectResourceCount)}, nodes {N(Performance.Monitor.ObjectNodeCount)}, " +
                 $"orphans {N(Performance.Monitor.ObjectOrphanNodeCount)}, pipelines {Perf.PipesNow():0} | managed {GC.GetTotalMemory(false) / 1048576.0:0} MB | " +
                 $"working set {me.WorkingSet64 / 1048576.0:0} MB, private {me.PrivateMemorySize64 / 1048576.0:0} MB");
    }

    /// <summary>One census of the textures the scene tree reaches (nodes, their materials and meshes, each property that holds
    /// a texture; the engine's own list is not exposed to scripts): imported ones by folder, runtime ones (no path) by the node
    /// that holds them. Bytes are width x height x the format's bytes per pixel, x 4/3 for mipmaps
    /// (an upper bound: mipmaps assumed), x layers.</summary>
    public static void Textures(Node root)
    {
        var seen = new System.Collections.Generic.HashSet<ulong>();
        var tex = new System.Collections.Generic.Dictionary<Rid, (long B, string What, string Where)>();
        var shaders = new System.Collections.Generic.Dictionary<ulong, (Shader S, string Where)>();
        void Visit(GodotObject o, string where, int depth)
        {
            if (depth > 6 || !seen.Add(o.GetInstanceId())) return;
            foreach (var pr in o.GetPropertyList())
            {
                if ((Variant.Type)pr["type"].AsInt32() != Variant.Type.Object) continue;
                var name = pr["name"].AsString();
                if (name is "script" or "owner") continue;
                GodotObject? v;
                try { v = o.Get(name).AsGodotObject(); } catch { continue; }
                if (v == null || v is Node) continue;
                if (v is Texture t) Add(t, $"{where}:{name}");
                else if (v is Shader sh) { if (!shaders.ContainsKey(sh.GetInstanceId())) shaders[sh.GetInstanceId()] = (sh, where); }
                else if (v is Material or Mesh or Resource) Visit(v, $"{where}>{name}", depth + 1);
            }
        }
        void Add(Texture t, string where)
        {
            var rid = t.GetRid();
            if (!rid.IsValid || tex.ContainsKey(rid)) return;
            int w = 0, h = 0, layers = 1;
            Image.Format f = Image.Format.Rgba8;
            if (t is Texture2D t2) { w = t2.GetWidth(); h = t2.GetHeight(); }
            if (t is TextureLayered tl) { w = tl.GetWidth(); h = tl.GetHeight(); layers = tl.GetLayers(); f = tl.GetFormat(); }
            if (t is Texture3D t3) { w = t3.GetWidth(); h = t3.GetHeight(); layers = t3.GetDepth(); f = t3.GetFormat(); }
            try { f = RenderingServer.TextureGetFormat(rid); } catch { }
            double bpp = Bpp(f);
            long b = (long)(w * (double)h * layers * bpp * 1.333);
            string path = t.ResourcePath;
            tex[rid] = (b, $"{w}x{h}{(layers > 1 ? "x" + layers : "")} {f} {t.GetClass()}", path.Length > 0 ? path : where);
        }
        void Walk(Node n)
        {
            Visit(n, n.Name, 0);
            if (n is MeshInstance3D mi && mi.Mesh != null)
                for (int i = 0; i < mi.GetSurfaceOverrideMaterialCount(); i++) if (mi.GetSurfaceOverrideMaterial(i) is { } m) Visit(m, $"{mi.Name}>surf{i}", 1);
            foreach (var k in n.GetChildren(true)) Walk(k);
        }
        Walk(root);
        long total = tex.Values.Sum(v => v.B), runtime = tex.Values.Where(v => !v.Where.StartsWith("res://")).Sum(v => v.B);
        static string Mb(long b) => $"{b / 1048576.0:0.0} MB";
        GD.Print($"mem tex: {tex.Count} textures reached from the tree, {Mb(total)} (mips assumed); made at runtime {Mb(runtime)}; the monitor says {Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576.0:0} MB");
        var byDir = tex.Values.Where(v => v.Where.StartsWith("res://")).GroupBy(v => string.Join("/", v.Where[6..].Split('/')[..^1].Take(3)));
        foreach (var g in byDir.OrderByDescending(g => g.Sum(v => v.B)).Take(30)) GD.Print($"mem tex dir: {Mb(g.Sum(v => v.B))} {g.Count()} {g.Key}");
        var byHolder = tex.Values.Where(v => !v.Where.StartsWith("res://")).GroupBy(v => System.Text.RegularExpressions.Regex.Replace(v.Where, "[0-9]+", "#") + " | " + v.What);
        foreach (var g in byHolder.OrderByDescending(g => g.Sum(v => v.B)).Take(40)) GD.Print($"mem tex runtime: {Mb(g.Sum(v => v.B))} {g.Count()} x {g.Key}");
        foreach (var v in tex.Values.OrderByDescending(v => v.B).Take(25)) GD.Print($"mem tex big: {Mb(v.B)} {v.What} {v.Where}");
        // (each Shader object compiles its own pipelines, even when its code is another's: copies of one code are pipelines twice)
        var byCode = shaders.Values.GroupBy(v => v.S.Code.GetHashCode()).ToList();
        GD.Print($"mem shaders: {shaders.Count} Shader objects reached from the tree, {byCode.Count} distinct codes, {shaders.Values.Count(v => v.S.ResourcePath.Length == 0)} made in code");
        foreach (var g in byCode.Where(g => g.Count() > 1).OrderByDescending(g => g.Count()).Take(30))
            GD.Print($"mem shaders dup: {g.Count()} copies of one code ({g.First().S.ResourcePath}{(g.First().S.ResourcePath.Length == 0 ? "code" : "")}), e.g. {string.Join(", ", g.Take(3).Select(v => System.Text.RegularExpressions.Regex.Replace(v.Where, "[0-9]+", "#")))}");
    }

    static double Bpp(Image.Format f) => f switch
    {
        Image.Format.L8 or Image.Format.R8 => 1, Image.Format.La8 or Image.Format.Rg8 or Image.Format.Rh => 2, Image.Format.Rgb8 => 3,
        Image.Format.Rgba8 or Image.Format.Rf or Image.Format.Rgh or Image.Format.Rgbe9995 or Image.Format.Rgba4444 => 4,
        Image.Format.Rgf or Image.Format.Rgbah => 8, Image.Format.Rgbh => 6, Image.Format.Rgbf => 12, Image.Format.Rgbaf => 16,
        Image.Format.Dxt1 or Image.Format.RgtcR or Image.Format.Etc or Image.Format.Etc2R11 or Image.Format.Etc2Rgb8 or Image.Format.Etc2Rgb8A1 => 0.5,
        _ => f >= Image.Format.Dxt1 && f <= Image.Format.Astc8X8Hdr ? 1 : 4,
    };
}
