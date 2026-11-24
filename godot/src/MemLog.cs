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

    // --mem-probe S (dev): at S s (default 40) a one-way sequence that takes a feature out of the live picture, makes the main view
    // rebuild its buffers (Scaling3DScale nudged), waits a few frames and logs the video memory monitors, so each step's
    // difference is what that feature's buffers cost. Never for play.
    readonly double probeAt = Args.Has("mem-probe") ? Args.Num("mem-probe", 40) : -1;
    int probeStep = -1, probeWait;
    (double Tex, double Buf, double Vid) probePrev;

    public MemLog(double every) { this.every = Math.Max(1, every); ProcessMode = ProcessModeEnum.Always; }

    public override void _Process(double delta)
    {
        if (texAt >= 0 && Time.GetTicksMsec() / 1000.0 >= texAt && !texDone) { texDone = true; Viewports(GetTree().Root); Textures(GetTree().Root); }
        if (probeAt >= 0 && Time.GetTicksMsec() / 1000.0 >= probeAt) Probe();
        FreshTick(delta);
        StripTick();
        if ((t += delta) < every) return;
        t = 0;
        Line(GetParent() is Play.Game g ? g.Zone?.Id ?? "-" : "-");
    }

    // --mem-fresh (dev, the tester lane's den loop, 24 Nov): 8 s into each new place, the textures the tree reaches that the
    // last place's census did not (made again, so uploaded again: each upload passes through a staging buffer of the
    // engine's that grows to its biggest upload and is never given back), and the pipelines compiled since, by kind.
    static readonly bool fresh = Args.Has("mem-fresh");
    static System.Collections.Generic.HashSet<Rid>? lastTex;
    static readonly double[] freshPipes = new double[5];
    object? freshZone;
    double freshT = -1;

    void FreshTick(double delta)
    {
        if (!fresh) return;
        if (GetParent() is Play.Game gz && gz.Zone != null && gz.Zone != freshZone) { freshZone = gz.Zone; freshT = 8; }
        if (freshT > 0 && (freshT -= delta) <= 0) Fresh(GetTree().Root);
    }

    static void Fresh(Node root)
    {
        var (tex, shaders) = Reach(root);
        // (and the resource cache's textures the tree does not reach: a flipbook, a warm-up's, a static's; 24 Nov, session 3)
        int reached = tex.Count;
        CachedOnly(tex.Keys.ToHashSet(), tex);
        GD.Print($"mem fresh cache: {tex.Count - reached} cache-only textures ({tex.Values.Where(v => v.Where.StartsWith("cache ")).Sum(v => v.B) >> 20} MB)");
        var k = Perf.PipesKinds();
        string pipes = string.Join("/", k.Select((v, i) => (int)(v - freshPipes[i])));
        k.CopyTo(freshPipes, 0);
        var made = lastTex == null ? new() : tex.Where(e => !lastTex.Contains(e.Key)).Select(e => e.Value).ToList();
        GD.Print($"mem fresh: {tex.Count} textures reached ({tex.Values.Sum(v => v.B) >> 20} MB), {made.Count} made since the last place ({made.Sum(v => v.B) >> 20} MB), " +
                 $"{made.Count(v => v.B > 64 << 20)} over 64 MB, {made.Count(v => v.B > 32 << 20)} over 32 MB; {shaders.Count} Shader objects; pipelines since c/m/s/d/sp {pipes}");
        foreach (var v in made.OrderByDescending(v => v.B).Take(8)) GD.Print($"mem fresh big: {v.B / 1048576.0:0.0} MB {v.What} {v.Where}");
        lastTex = tex.Keys.ToHashSet();
        // (the Shader objects made again since the last place: each compiles its pipelines again; by file, or by its code's first line)
        var newSh = lastShaders == null ? new() : shaders.Where(e => !lastShaders.Contains(e.Key)).Select(e => e.Value).ToList();
        GD.Print($"mem fresh shaders: {newSh.Count} of {shaders.Count} Shader objects made since the last place");
        foreach (var g in newSh.GroupBy(v => v.S.ResourcePath.Length > 0 && !v.S.ResourcePath.Contains("::") ? v.S.ResourcePath : "code " + (v.S.Code.Length > 0 ? (uint)v.S.Code.GetHashCode() : 0) + " " + v.Where.Split('>')[0]).OrderByDescending(g => g.Count()).Take(30))
            GD.Print($"mem fresh shader: {g.Count()} x {g.Key}");
        lastShaders = shaders.Keys.ToHashSet();
    }
    static System.Collections.Generic.HashSet<ulong>? lastShaders;

    static (double Tex, double Buf, double Vid) Mon() => (Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576.0,
        Performance.GetMonitor(Performance.Monitor.RenderBufferMemUsed) / 1048576.0, Performance.GetMonitor(Performance.Monitor.RenderVideoMemUsed) / 1048576.0);

    void Probe()
    {
        if (probeWait > 0) { probeWait--; return; }
        var root = GetTree().Root;
        var env = root.FindChildren("*", "WorldEnvironment", true, false).OfType<WorldEnvironment>().FirstOrDefault()?.Environment;
        string name = "";
        if (probeStep >= 0)
        {
            var m = Mon();
            GD.Print($"mem probe: after [{probeNames[Math.Min(probeStep, probeNames.Length - 1)]}] texture {m.Tex:0} MB ({m.Tex - probePrev.Tex:+0;-0;0}), buffers {m.Buf:0} ({m.Buf - probePrev.Buf:+0;-0;0}), video {m.Vid:0} ({m.Vid - probePrev.Vid:+0;-0;0})");
            probePrev = m;
        }
        else probePrev = Mon();
        probeStep++;
        probeWait = 20;
        if (probeStep >= probeNames.Length) { probeStep = 1000; probeWait = int.MaxValue; return; }
        name = probeNames[probeStep];
        switch (probeStep)
        {
            case 0: root.Scaling3DScale = 0.999f; break;                       // control: the rebuild with everything on
            case 1: if (env != null) env.SsaoEnabled = false; root.Scaling3DScale = 1f; break;
            case 2: if (env != null) env.GlowEnabled = false; root.Scaling3DScale = 0.999f; break;
            case 3: if (env != null) env.VolumetricFogEnabled = false; root.Scaling3DScale = 1f; break;
            case 4: if (env != null) env.FogEnabled = false; root.Scaling3DScale = 0.999f; break;
            case 5: root.ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled; root.Scaling3DScale = 1f; break;
            case 6: root.PositionalShadowAtlasSize = 0; root.Scaling3DScale = 0.999f; break;
            case 7: RenderingServer.DirectionalShadowAtlasSetSize(256, true); root.Scaling3DScale = 1f; break;
            case 8: root.Scaling3DScale = 0.5f; break;
        }
        GD.Print($"mem probe: step {probeStep} {name}");
    }

    static readonly string[] probeNames = { "control: rebuild, all on", "ssao off", "glow off", "volumetric fog off", "fog off", "smaa off",
        "positional shadow atlas 0", "directional shadow atlas 256", "internal scale 0.5 (all pixels cost x0.25)" };

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

    /// <summary>(--mem-tex) Every Viewport in the tree (the root, each SubViewport, the other windows): its size, the window it
    /// sits in, what it renders (3D or 2D), the scaling, MSAA, HDR 2D, the update mode and an estimated GPU cost. The estimate is
    /// a model, not a measurement: a 2D target is size x 4 B (8 with HDR 2D); a 3D target adds the internal buffers at
    /// size x scale: colour RGBA16F 8 B + depth 4 B (+ 8 B x samples for MSAA, + about 12 B for FSR 2's velocity, history and
    /// reactive masks) and the positional shadow atlas (size^2 x 2 B). Compare with the monitors, and toggle to measure.</summary>
    public static void Viewports(Window root)
    {
        var win = root;
        var scr = DisplayServer.WindowGetCurrentScreen();
        GD.Print($"mem vp: window {win.Size.X}x{win.Size.Y} mode {win.Mode} | DisplayServer window {DisplayServer.WindowGetSize()} screen {scr} {DisplayServer.ScreenGetSize(scr)} " +
                 $"scale {DisplayServer.ScreenGetScale(scr):0.00} dpi {DisplayServer.ScreenGetDpi(scr)} | content scale mode {win.ContentScaleMode} aspect {win.ContentScaleAspect} size {win.ContentScaleSize} factor {win.ContentScaleFactor:0.00} | " +
                 $"root visible rect {root.GetVisibleRect().Size} | project base {ProjectSettings.GetSetting("display/window/size/viewport_width")}x{ProjectSettings.GetSetting("display/window/size/viewport_height")} | args {string.Join(' ', OS.GetCmdlineArgs())}");
        double total = 0;
        void Walk(Node n)
        {
            if (n is Viewport v)
            {
                var sub = v as SubViewport;
                Vector2I size = sub != null ? sub.Size : (v is Window w ? w.Size : v.GetWindow().Size);
                float sc = v.Scaling3DMode == Viewport.Scaling3DModeEnum.Fsr2 || v.Scaling3DMode == Viewport.Scaling3DModeEnum.Bilinear || v.Scaling3DMode == Viewport.Scaling3DModeEnum.Fsr ? v.Scaling3DScale : 1f;
                bool d3 = !v.Disable3D;
                double px = (double)size.X * size.Y;
                double bytes = px * (v.UseHdr2D ? 8 : 4);
                if (d3)
                {
                    double ip = px * sc * sc;
                    int smp = v.Msaa3D switch { Viewport.Msaa.Msaa2X => 2, Viewport.Msaa.Msaa4X => 4, Viewport.Msaa.Msaa8X => 8, _ => 1 };
                    bytes += ip * (8 + 4) * smp + (v.Scaling3DMode == Viewport.Scaling3DModeEnum.Fsr2 ? ip * 12 : 0);
                    bytes += (double)v.PositionalShadowAtlasSize * v.PositionalShadowAtlasSize * 2;
                }
                total += bytes;
                string mode = sub != null ? sub.RenderTargetUpdateMode.ToString() : "window";
                GD.Print($"mem vp: {root.GetPathTo(v)} {v.GetClass()} {size.X}x{size.Y} {(d3 ? "3D" : "2D")} scale {sc:0.00} {v.Scaling3DMode} msaa {v.Msaa3D} aa {v.ScreenSpaceAA}{(v.UseTaa ? " taa" : "")} hdr2d {v.UseHdr2D} transparent {v.TransparentBg} " +
                         $"shadowAtlas {v.PositionalShadowAtlasSize} update {mode} own3d {v.OwnWorld3D} | est {bytes / 1048576.0:0.0} MB");
            }
            foreach (var k in n.GetChildren(true)) Walk(k);
        }
        Walk(root);
        GD.Print($"mem vp: estimated total {total / 1048576.0:0} MB (a model: see the doc comment)");
    }

    /// <summary>One census of the textures the scene tree reaches (nodes, their materials and meshes, each property that holds
    /// a texture; the engine's own list is not exposed to scripts): imported ones by folder, runtime ones (no path) by the node
    /// that holds them. Bytes are width x height x the format's bytes per pixel, x 4/3 for mipmaps
    /// (an upper bound: mipmaps assumed), x layers.</summary>
    /// <summary>What the tree reaches: its textures (by RID: size, kind, path or holder) and its Shader objects.</summary>
    static (System.Collections.Generic.Dictionary<Rid, (long B, string What, string Where)> Tex, System.Collections.Generic.Dictionary<ulong, (Shader S, string Where)> Shaders) Reach(Node root)
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
        return (tex, shaders);
    }

    public static void Textures(Node root)
    {
        var (tex, shaders) = Reach(root);
        CachedOnly(tex.Keys.ToHashSet());
        long total = tex.Values.Sum(v => v.B), runtime = tex.Values.Where(v => !v.Where.StartsWith("res://")).Sum(v => v.B);
        static string Mb(long b) => $"{b / 1048576.0:0.0} MB";
        GD.Print($"mem tex: {tex.Count} textures reached from the tree, {Mb(total)} (mips assumed); made at runtime {Mb(runtime)}; the monitor says {Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576.0:0} MB");
        var byDir = tex.Values.Where(v => v.Where.StartsWith("res://")).GroupBy(v => string.Join("/", v.Where[6..].Split('/')[..^1].Take(3)));
        foreach (var g in byDir.OrderByDescending(g => g.Sum(v => v.B)).Take(30)) GD.Print($"mem tex dir: {Mb(g.Sum(v => v.B))} {g.Count()} {g.Key}");
        // The textures held uncompressed on the card (RGBA8 / RGB8 padded to RGBA8 here; BC7 would be a quarter of it): the folders
        // an import-side compress (or a smaller cap) would act on, with the size a 4:1 compress would leave.
        var raw = tex.Values.Where(v => v.What.Contains(" Rgba8 ") || v.What.Contains(" Rgb8 ")).ToList();
        GD.Print($"mem tex uncompressed: {raw.Count} textures, {Mb(raw.Sum(v => v.B))} held as RGBA8/RGB8 (a 4:1 block compress leaves {Mb(raw.Sum(v => v.B) / 4)}); of these {Mb(raw.Where(v => v.B > 4 << 20).Sum(v => v.B))} in {raw.Count(v => v.B > 4 << 20)} over 4 MB");
        foreach (var g in raw.GroupBy(v => v.Where.StartsWith("res://") ? string.Join("/", v.Where[6..].Split('/')[..^1].Take(3)) : "(runtime)").OrderByDescending(g => g.Sum(v => v.B)).Take(15))
            GD.Print($"mem tex uncompressed dir: {Mb(g.Sum(v => v.B))} {g.Count()} {g.Key}");
        var byHolder = tex.Values.Where(v => !v.Where.StartsWith("res://")).GroupBy(v => System.Text.RegularExpressions.Regex.Replace(v.Where, "[0-9]+", "#") + " | " + v.What);
        foreach (var g in byHolder.OrderByDescending(g => g.Sum(v => v.B)).Take(40)) GD.Print($"mem tex runtime: {Mb(g.Sum(v => v.B))} {g.Count()} x {g.Key}");
        foreach (var v in tex.Values.OrderByDescending(v => v.B).Take(25)) GD.Print($"mem tex big: {Mb(v.B)} {v.What} {v.Where}");
        // (each Shader object compiles its own pipelines, even when its code is another's: copies of one code are pipelines twice)
        var byCode = shaders.Values.GroupBy(v => v.S.Code.GetHashCode()).ToList();
        GD.Print($"mem shaders: {shaders.Count} Shader objects reached from the tree, {byCode.Count} distinct codes, {shaders.Values.Count(v => v.S.ResourcePath.Length == 0)} made in code");
        foreach (var g in byCode.Where(g => g.Count() > 1).OrderByDescending(g => g.Count()).Take(30))
            GD.Print($"mem shaders dup: {g.Count()} copies of one code ({g.First().S.ResourcePath}{(g.First().S.ResourcePath.Length == 0 ? "code" : "")}), e.g. {string.Join(", ", g.Take(3).Select(v => System.Text.RegularExpressions.Regex.Replace(v.Where, "[0-9]+", "#")))}");
    }

    /// <summary>(--mem-tex) The textures the resource cache holds that the tree does not reach (held by a static, a warm-up's
    /// material, a dictionary): every texture file under res:// asked of ResourceLoader.HasCached, then Load (a cache hit costs
    /// nothing). Listed by folder (not added to the tree census's total).</summary>
    static void CachedOnly(System.Collections.Generic.HashSet<Rid> known) => CachedOnly(known, null);

    static void CachedOnly(System.Collections.Generic.HashSet<Rid> known, System.Collections.Generic.Dictionary<Rid, (long B, string What, string Where)>? into)
    {
        var found = new System.Collections.Generic.List<(long B, string What, string Path)>();
        int files = 0;
        void Scan(string dir, int depth)
        {
            if (depth > 9) return;
            using var d = DirAccess.Open(dir);
            if (d == null) return;
            foreach (var sub in d.GetDirectories()) { if (sub.StartsWith(".") || sub == "addons") continue; Scan((dir.EndsWith("/") ? dir : dir + "/") + sub, depth + 1); }
            // (an exported build lists NAME.png.import / NAME.tres.remap, not NAME.png: the name is taken back off them,
            // each file once; Godot's loader maps the bare path to the imported one. Session 4: the scan read 0 on exports)
            var names = new System.Collections.Generic.HashSet<string>();
            foreach (var raw in d.GetFiles())
                names.Add(raw.EndsWith(".import") ? raw[..^7] : raw.EndsWith(".remap") ? raw[..^6] : raw);
            foreach (var f in names)
            {
                string e = f.GetExtension().ToLowerInvariant();
                if (e is not ("png" or "jpg" or "jpeg" or "webp" or "exr" or "hdr" or "tga" or "bmp" or "ktx" or "dds" or "svg" or "res" or "tres" or "ctex")) continue;
                files++;
                string path = (dir.EndsWith("/") ? dir : dir + "/") + f;
                if (!ResourceLoader.HasCached(path)) continue;
                if (ResourceLoader.Load(path, "", ResourceLoader.CacheMode.Reuse) is not Texture t || !t.GetRid().IsValid) continue;
                if (!known.Add(t.GetRid())) continue;
                int w = 0, h = 0, layers = 1; var fm = Image.Format.Rgba8;
                if (t is Texture2D t2) { w = t2.GetWidth(); h = t2.GetHeight(); }
                if (t is TextureLayered tl) { w = tl.GetWidth(); h = tl.GetHeight(); layers = tl.GetLayers(); fm = tl.GetFormat(); }
                if (t is Texture3D t3) { w = t3.GetWidth(); h = t3.GetHeight(); layers = t3.GetDepth(); fm = t3.GetFormat(); }
                try { fm = RenderingServer.TextureGetFormat(t.GetRid()); } catch { }
                long b = (long)(w * (double)h * layers * Bpp(fm) * 1.333);
                found.Add((b, $"{w}x{h}{(layers > 1 ? "x" + layers : "")} {fm} {t.GetClass()}", path));
                into?.TryAdd(t.GetRid(), (b, $"{w}x{h}{(layers > 1 ? "x" + layers : "")} {fm} {t.GetClass()}", "cache " + path));
            }
        }
        Scan("res://", 0);
        if (into != null) return;
        static string Mb(long b) => $"{b / 1048576.0:0.0} MB";
        GD.Print($"mem tex flipbooks: {View.Flipbooks.UsedReport()}");
        GD.Print($"mem tex cache-only: {found.Count} textures in the resource cache that the tree does not reach, {Mb(found.Sum(v => v.B))} (scanned {files} files)");
        foreach (var g in found.GroupBy(v => string.Join("/", v.Path[6..].Split('/')[..^1].Take(4))).OrderByDescending(g => g.Sum(v => v.B)).Take(25))
            GD.Print($"mem tex cache-only dir: {Mb(g.Sum(v => v.B))} {g.Count()} {g.Key}");
        foreach (var v in found.OrderByDescending(v => v.B).Take(15)) GD.Print($"mem tex cache-only big: {Mb(v.B)} {v.What} {v.Path}");
    }

    static double Bpp(Image.Format f) => f switch
    {
        Image.Format.L8 or Image.Format.R8 => 1, Image.Format.La8 or Image.Format.Rg8 or Image.Format.Rh => 2,
        Image.Format.Rgb8 or Image.Format.Rgba8 or Image.Format.Rf or Image.Format.Rgh or Image.Format.Rgbe9995 or Image.Format.Rgba4444 => 4,
        Image.Format.Rgf or Image.Format.Rgbah => 8, Image.Format.Rgbh => 8, Image.Format.Rgbf => 12, Image.Format.Rgbaf => 16,
        Image.Format.Dxt1 or Image.Format.RgtcR or Image.Format.Etc or Image.Format.Etc2R11 or Image.Format.Etc2Rgb8 or Image.Format.Etc2Rgb8A1 => 0.5,
        _ => f >= Image.Format.Dxt1 && f <= Image.Format.Astc8X8Hdr ? 1 : 4,
    };
}
