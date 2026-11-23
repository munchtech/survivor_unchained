using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Godot;

namespace SurvivorUnchained.Fx;

/// <summary>
/// (P2 task 5, session 3) The general effect warm-up: everything that is first drawn in play (an effect, a drop, a foe's
/// effect, a pop of the HUD with a material of its own) drawn once behind the load instead, so its pipelines compile there.
///
/// The list is not kept by hand. It is the census's (--fx-census): a run of the game that watches every drawable that comes
/// into view during play, after the place stood up, and keeps one stand-in for each kind it saw. A kind is what a pipeline
/// depends on: the node's class, each surface's vertex format and primitive, each material's shader (a ShaderMaterial's
/// shader file or code; a built-in material's switches and which of its texture slots are filled), and the instance's own
/// switches (shadows, transparency, a sprite's or label's flags, a particle system's process material and draw passes).
/// A stand-in is the same engine class with the same switches, a mesh of the same format cut to one primitive, and every
/// texture swapped for a 4x4 one of the same kind: no art, no script, small. The census writes them to <see cref="Library"/>.
///
/// At each place's load (Game.EnterPlay) <see cref="Begin"/> puts every stand-in not yet warmed this session a few
/// millimetres in front of the camera, shrunk to nothing, for the frames it takes the pipeline counters to settle, then
/// frees the nodes and keeps their materials (a built-in material's shader lives only while a material of its kind does).
/// Then Perf's first-draw check is armed: a frame in play that still compiles a pipeline is told by name, and the run's
/// end says PASS or FAIL (Perf.FirstDrawsVerdict). A new effect is covered by the next census run: nothing to list.
/// --no-fx-warm: not run (to measure against).
/// </summary>
public static partial class FxWarm
{
    /// <summary>The census's stand-ins (res:// so the export packs it).</summary>
    public const string Library = "res://data/fx_warm/warm.scn";
    const string SigMeta = "fxwarm_sig";

    static readonly HashSet<string> warmed = new();
    static readonly List<Resource> held = new();
    /// <summary>The last warm-up's line (also printed as "load: fx warm-up ..."); empty until one ran.</summary>
    public static string Report { get; private set; } = "";

    /// <summary>Starts the warm-up under `host` (a node of the place: the stand-ins follow the active camera). Returns at
    /// once; the warm-up runs over the next frames and arms Perf's first-draw check when done.</summary>
    public static void Begin(Node host, string why)
    {
        if (Args.Has("no-fx-warm") || Args.Has("fx-census")) { Perf.ArmFirstDraws($"{why}: no warm-up (--{(Args.Has("fx-census") ? "fx-census" : "no-fx-warm")})"); return; }
        if (!ResourceLoader.Exists(Library)) { GD.Print($"load: fx warm-up: no library at {Library}"); Perf.ArmFirstDraws($"{why}: no library"); return; }
        host.AddChild(new Run(why));
    }

    // (frame pacing, session 4) The early start: the library's load runs on a loader thread while the map builds; Run takes it.
    static bool preBegun, preRequested;
    static long preT0;

    /// <summary>Primes the renderer and requests the library on a loader thread (idempotent; not with --no-fx-warm, --fx-census or --no-fx-pre).</summary>
    public static void Pre(Node host)
    {
        if (Args.Has("no-fx-warm") || Args.Has("fx-census") || Args.Has("no-fx-pre")) return;
        if (preBegun || !ResourceLoader.Exists(Library)) return;
        preBegun = true;
        if (!Args.Has("no-fx-pre-draw"))
        {
            // (a frame before the library exists: the renderer switches its shader groups on at the first scene render, and every shader alive then is rebuilt for the new group on the main thread)
            var vp = host.GetViewport();
            Camera3D? tmp = null;
            if (vp.GetCamera3D() == null) { tmp = new Camera3D { Name = "FxWarmPrimer" }; host.AddChild(tmp); tmp.MakeCurrent(); }
            long d0 = System.Diagnostics.Stopwatch.GetTimestamp();
            RenderingServer.ForceDraw(false);
            double ms = System.Diagnostics.Stopwatch.GetElapsedTime(d0).TotalMilliseconds;
            if (tmp != null) { host.RemoveChild(tmp); tmp.QueueFree(); }
            GD.Print($"load: fx pre-warm: primer frame {ms:0} ms (temp camera: {tmp != null})");
        }
        var err = ResourceLoader.LoadThreadedRequest(Library, "", true);
        preT0 = System.Diagnostics.Stopwatch.GetTimestamp();
        preRequested = err == Error.Ok;
        GD.Print($"load: fx pre-warm: library requested on a loader thread ({err})");
    }

    /// <summary>True while a place's warm-up is drawing (the travel's black waits for it: Game.WhenSmooth).</summary>
    public static bool Busy => running > 0;
    static int running;

    sealed partial class Run : Node3D
    {
        readonly string why;
        long t0;
        int frames, drawn, still, entries, skipped;
        double lastPipes = -1, pipes0;
        double[] kinds0 = new double[5];
        double worstMs;
        long lastTick;
        CanvasLayer? canvas;
        Camera3D? cam;
        Node3D? mirror;

        public Run(string why) { this.why = why; Name = "FxWarm"; }

        public override void _EnterTree() => running++;
        public override void _ExitTree() => running--;

        public override void _Ready()
        {
            t0 = System.Diagnostics.Stopwatch.GetTimestamp();
            pipes0 = Perf.PipesNow();
            kinds0 = Perf.PipesKinds();
            canvas = new CanvasLayer { Layer = -64, Name = "FxWarm2D" };
            PackedScene? lib;
            if (preRequested)
            {
                var st = ResourceLoader.LoadThreadedGetStatus(Library);
                long w0 = System.Diagnostics.Stopwatch.GetTimestamp();
                lib = ResourceLoader.LoadThreadedGet(Library) as PackedScene;
                GD.Print($"load: fx pre-warm: library taken {System.Diagnostics.Stopwatch.GetElapsedTime(preT0).TotalSeconds:0.00} s after the request, status then {st}, waited {System.Diagnostics.Stopwatch.GetElapsedTime(w0).TotalMilliseconds:0} ms");
                preRequested = false;
            }
            else lib = GD.Load<PackedScene>(Library);
            var root = lib?.Instantiate();
            if (root == null) { Done("library did not load"); return; }
            AddChild(canvas);
            foreach (var k in root.GetChildren().ToList())
            {
                string sig = k.HasMeta(SigMeta) ? k.GetMeta(SigMeta).AsString() : k.Name;
                if (!warmed.Add(sig)) { skipped++; continue; }
                root.RemoveChild(k);
                k.Owner = null;
                Hold(k);
                if (k is CanvasItem ci)
                {
                    canvas.AddChild(ci);
                    if (ci is Control c) { c.Position = Vector2.Zero; c.Size = new Vector2(8, 8); }
                    else if (ci is Node2D n2) n2.Position = Vector2.One;
                    ci.Modulate = new Color(1, 1, 1, 0.01f);
                }
                else AddChild(k);
                if (k is Node3D n3) n3.Transform = Transform3D.Identity;
                if (k is GpuParticles3D gp) { gp.Emitting = true; gp.Amount = 1; }
                // (a mirrored copy too: a negative-scale instance draws with the other cull mode, its own pipeline)
                if (k is Node3D && !Args.Has("fx-warm-flat"))
                {
                    if (mirror == null) AddChild(mirror = new Node3D { Name = "Mirrored", Scale = new Vector3(-1, 1, 1) });
                    mirror.AddChild((Node)k.Duplicate());
                }
                entries++;
            }
            root.QueueFree();
            // (nothing new to draw: the place's own first frames still settle before the check arms)
            if (entries == 0) { end = "everything already warmed"; return; }
            Follow();
        }

        // Its stand-ins a hair in front of the lens, shrunk to nothing: inside the view (so they are drawn), seen by no one.
        void Follow()
        {
            cam ??= GetViewport().GetCamera3D();
            if (cam == null) return;
            var t = cam.GlobalTransform;
            GlobalTransform = new Transform3D(t.Basis.Scaled(Vector3.One * 0.0005f), t.Origin - t.Basis.Z * (cam.Near * 4 + 0.05f));
        }

        // Counted in frames, not seconds (the editor's first frames are seconds long: a 3 s cap ended check1's after 2 frames):
        // the stand-ins in view for at least 4 frames and until the counters stand still 3 (cap 600); then, the stand-ins
        // gone, the place's own first frames until 10 stand still (cap 600), and only then the check is armed.
        string end = "";
        double warmSecs;
        int settle;
        public override void _Process(double delta)
        {
            frames++;
            long tick = System.Diagnostics.Stopwatch.GetTimestamp();
            if (lastTick != 0) worstMs = Math.Max(worstMs, System.Diagnostics.Stopwatch.GetElapsedTime(lastTick, tick).TotalMilliseconds);
            lastTick = tick;
            double p = Perf.PipesNow();
            still = p == lastPipes ? still + 1 : 0;
            lastPipes = p;
            if (end.Length == 0)
            {
                Follow();
                if (cam != null) drawn++;
                if (drawn >= 4 && still >= 3 || frames >= 600)
                {
                    end = frames >= 600 ? "the 600-frame cap" : "the pipelines settled";
                    warmSecs = System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalSeconds;
                    foreach (var k in GetChildren()) k.QueueFree();
                    still = 0;
                }
                return;
            }
            if (++settle >= 600 || still >= 10) Done(settle >= 600 ? "the place still compiling (600-frame cap)" : "the place settled");
        }

        void Done(string placeEnd)
        {
            double secs = System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalSeconds;
            if (end.Length == 0) { end = placeEnd; warmSecs = secs; }
            var k1 = Perf.PipesKinds();
            Report = $"{entries} stand-ins drawn ({skipped} warmed before), {Perf.PipesNow() - pipes0:0} pipelines compiled, {drawn} frames in view, " +
                     $"{warmSecs:0.00} s, ended by {end} (in view from {Time.GetTicksMsec() / 1000.0 - secs:0.0} s, done {Time.GetTicksMsec() / 1000.0:0.0} s after the engine started); then {settle} frames, {secs - warmSecs:0.00} s, till {placeEnd} (canvas/mesh/surface/draw/specialization {(int)(k1[0] - kinds0[0])}/{(int)(k1[1] - kinds0[1])}/{(int)(k1[2] - kinds0[2])}/{(int)(k1[3] - kinds0[3])}/{(int)(k1[4] - kinds0[4])}; worst frame {worstMs:0} ms)";
            GD.Print($"load: fx warm-up ({why}): {Report}");
            SetProcess(false);
            QueueFree();
            Perf.ArmFirstDraws($"{why}: after the warm-up");
        }
    }

    // A built-in material's shader is freed with the last material of its kind: the stand-ins' materials are held.
    static void Hold(Node n)
    {
        void Mat(Material? m) { while (m != null) { held.Add(m); m = m.NextPass; } }
        switch (n)
        {
            case GeometryInstance3D g:
                Mat(g.MaterialOverride); Mat(g.MaterialOverlay);
                if (g is MeshInstance3D mi && mi.Mesh != null)
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++) { Mat(mi.GetSurfaceOverrideMaterial(s)); Mat(mi.Mesh.SurfaceGetMaterial(s)); }
                if (g is GpuParticles3D gp) { Mat(gp.ProcessMaterial); for (int d = 0; d < gp.DrawPasses; d++) if (gp.GetDrawPassMesh(d) is { } dm) for (int s = 0; s < dm.GetSurfaceCount(); s++) Mat(dm.SurfaceGetMaterial(s)); }
                break;
            case CanvasItem c: Mat(c.Material); break;
        }
    }

    // ---------------------------------------------------------------- the census

    /// <summary>--fx-census: the watcher, put under the game's root at the start of play. Every 0.25 s it walks the tree for
    /// drawables in view (the place's own kinds too: drawn at load, they can be drawn again into another framebuffer); every kind
    /// seen after that is added to the library (merged with what the library already holds), written every 20 s and at exit.</summary>
    public static Node? CensusNode() => Args.Has("fx-census") && !censusMade && (censusMade = true) ? new Census() : null;
    static bool censusMade;

    sealed partial class Census : Node
    {
        readonly Dictionary<string, Node> lib = new();
        int walks, added, refused;
        double next, nextSave = 20, t;
        bool dirty;

        // (what the 0.25 s walk misses: a node that lives or shows for less, e.g. fx_p7_top, never seen by census1) every
        // drawable added to the tree, or shown, is looked at in the next frame or two, once it is made up.
        readonly List<Node> fresh = new(), later = new();
        readonly HashSet<ulong> hooked = new();
        void Fresh(Node n)
        {
            if (n is not (GeometryInstance3D or CanvasItem)) return;
            fresh.Add(n);
            if (!hooked.Add(n.GetInstanceId())) return;
            if (n is Node3D n3) n3.VisibilityChanged += () => { if (IsInstanceValid(n3) && n3.IsVisibleInTree()) fresh.Add(n3); };
            else if (n is CanvasItem c) c.VisibilityChanged += () => { if (IsInstanceValid(c) && c.IsVisibleInTree()) fresh.Add(c); };
        }
        void Look(Node n)
        {
            if (!IsInstanceValid(n) || !n.IsInsideTree() || n is Node3D { } a && !a.IsVisibleInTree() || n is CanvasItem { } b && !b.IsVisibleInTree()) return;
            for (var p = n; p != null; p = p.GetParent()) if (p is FxWarm.Run) return;
            if (Drawable(n)) Consider(n, false);
        }

        public override void _Ready()
        {
            Name = "FxCensus";
            ProcessMode = ProcessModeEnum.Always;
            GetTree().NodeAdded += Fresh;
            if (ResourceLoader.Exists(Library) && GD.Load<PackedScene>(Library)?.Instantiate() is { } old)
            {
                foreach (var k in old.GetChildren().ToList())
                    if (k.HasMeta(SigMeta)) { old.RemoveChild(k); lib[k.GetMeta(SigMeta).AsString()] = k; }
                old.QueueFree();
            }
            GD.Print($"fx census: watching; the library holds {lib.Count} kinds");
        }

        public override void _Process(double delta)
        {
            t += delta;
            if (walks > 0)
            {
                var now = fresh.ToArray();
                fresh.Clear();
                foreach (var n in later) Look(n);
                later.Clear();
                later.AddRange(now);
                foreach (var n in now) Look(n);
            }
            if (t < next) return;
            next = t + 0.25;
            bool first = walks++ == 0;
            Walk(GetTree().Root, first);
            if (dirty && t >= nextSave) { nextSave = t + 20; Save(); }
        }

        public override void _Notification(int what)
        {
            if (what == NotificationWMCloseRequest || what == NotificationExitTree) { if (dirty) Save(); }
        }

        void Walk(Node n, bool first)
        {
            if (n is FxWarm.Run || n == this) return;
            if (n is CanvasItem ci0 && !ci0.Visible) return;
            if (n is Node3D n30 && !n30.Visible) return;
            if (Drawable(n)) Consider(n, first);
            foreach (var k in n.GetChildren()) Walk(k, first);
        }

        void Consider(Node n, bool first)
        {
            string? sig = Signature(n);
            if (sig == null) return;
            // (what was in view at the first walk is kept too: a kind drawn at load can be drawn again in play into another
            // framebuffer, e.g. the page backdrop, check2 498.96 s, 86 ms; warming a kind already drawn costs nothing)
            if (lib.ContainsKey(sig)) return;
            Node? stand = null;
            try { stand = StandIn(n); } catch (Exception e) { GD.PrintErr($"fx census: {n.GetPath()}: {e.Message}"); }
            if (stand == null) { refused++; return; }
            stand.SetMeta(SigMeta, sig);
            stand.Name = $"k{lib.Count:0000}";
            lib[sig] = stand;
            added++;
            dirty = true;
            GD.Print($"fx census: +{n.GetClass()} {n.GetPath()} :: {sig}");
        }

        void Save()
        {
            dirty = false;
            var root = new Node { Name = "FxWarmLibrary" };
            foreach (var (_, k) in lib)
            {
                if (k.GetParent() != null) k.GetParent().RemoveChild(k);
                root.AddChild(k);
                k.Owner = root;
            }
            var ps = new PackedScene();
            var err = ps.Pack(root);
            DirAccess.MakeDirRecursiveAbsolute(ProjectSettings.GlobalizePath(Library.GetBaseDir()));
            var err2 = err == Error.Ok ? ResourceSaver.Save(ps, Library, ResourceSaver.SaverFlags.Compress) : err;
            foreach (var k in root.GetChildren().ToList()) root.RemoveChild(k);
            root.Free();
            GD.Print($"fx census: library written: {lib.Count} kinds ({added} new this run, {refused} refused), {err2}");
        }
    }

    /// <summary>(the first-draw check's words for a node drawn new) "lib": its kind is in the library, so the warm-up drew a
    /// stand-in for it and missed anyway (a fidelity miss); "NEW": the census never saw its kind (a coverage miss);
    /// ",mirrored": a negative-scale instance; ",L20": on FxAfter's layer (drawn by its own camera and viewport).</summary>
    public static string Tag(Node n)
    {
        string? sig = null;
        try { sig = Signature(n); } catch (Exception) { }
        if (sig == null) return "no kind";
        if (librarySigs == null)
        {
            librarySigs = new HashSet<string>();
            if (ResourceLoader.Exists(Library) && GD.Load<PackedScene>(Library)?.Instantiate() is { } r)
            {
                foreach (var k in r.GetChildren()) if (k.HasMeta(SigMeta)) librarySigs.Add(k.GetMeta(SigMeta).AsString());
                r.Free();
            }
        }
        return (librarySigs.Contains(sig) ? "lib" : "NEW") + (n is Node3D a && a.GlobalTransform.Basis.Determinant() < 0 ? ",mirrored" : "") +
               (n is VisualInstance3D v && (v.Layers & SurvivorUnchained.View.FxAfter.RenderLayer) != 0 ? ",L20" : "");
    }
    static HashSet<string>? librarySigs;

    static bool Drawable(Node n) => n switch
    {
        MeshInstance3D mi => mi.Mesh != null,
        MultiMeshInstance3D mm => mm.Multimesh?.Mesh != null && mm.Multimesh.VisibleInstanceCount != 0,
        GpuParticles3D gp => gp.DrawPasses > 0,
        SpriteBase3D or Label3D => true,
        CanvasItem c => c.Material != null,
        _ => false,
    };

    // ---------------------------------------------------------------- what a pipeline depends on

    /// <summary>The kind of a drawable, as a pipeline sees it (null: not one we stand in for, e.g. a skinned mesh).</summary>
    public static string? Signature(Node n)
    {
        var sb = new StringBuilder(n.GetClass());
        switch (n)
        {
            case GeometryInstance3D g:
                sb.Append("|sh").Append((int)g.CastShadow).Append(g.Transparency > 0 ? "|tr" : "");
                // (FxAfter's layer is drawn by its own camera into its own viewport, another framebuffer: another pipeline)
                if ((g.Layers & SurvivorUnchained.View.FxAfter.RenderLayer) != 0) sb.Append("|L20");
                sb.Append("|o:").Append(MatKey(g.MaterialOverride)).Append("|ov:").Append(MatKey(g.MaterialOverlay));
                switch (g)
                {
                    case MeshInstance3D mi:
                        // (a skinned one, her Henge ghost: deformed by compute before it is drawn; its stand-in is the unskinned mesh)
                        if (mi.Skin != null || !mi.Skeleton.IsEmpty) sb.Append("|sk");
                        if (!MeshKey(mi.Mesh!, s => g.MaterialOverride ?? mi.GetActiveMaterial(s), sb)) return null;
                        break;
                    case MultiMeshInstance3D mm:
                        var m = mm.Multimesh!;
                        sb.Append($"|mm{(int)m.TransformFormat}{(m.UseColors ? "c" : "")}{(m.UseCustomData ? "d" : "")}");
                        if (!MeshKey(m.Mesh!, s => g.MaterialOverride ?? m.Mesh!.SurfaceGetMaterial(s), sb)) return null;
                        break;
                    case GpuParticles3D gp:
                        sb.Append("|p:").Append(MatKey(gp.ProcessMaterial)).Append($"|tf{(int)gp.TransformAlign}{(gp.TrailEnabled ? "t" : "")}");
                        for (int d = 0; d < gp.DrawPasses; d++)
                            if (gp.GetDrawPassMesh(d) is { } dm && !MeshKey(dm, s => g.MaterialOverride ?? dm.SurfaceGetMaterial(s), sb)) return null;
                        break;
                    case SpriteBase3D sp:
                        sb.Append($"|b{(int)sp.Billboard}{(sp.Transparent ? "t" : "")}{(sp.Shaded ? "s" : "")}{(sp.DoubleSided ? "d" : "")}{(sp.NoDepthTest ? "n" : "")}{(sp.FixedSize ? "f" : "")}" +
                                  $"a{(int)sp.AlphaCut}f{(int)sp.TextureFilter}aa{(int)sp.AlphaAntialiasingMode}");
                        break;
                    case Label3D l:
                        sb.Append($"|b{(int)l.Billboard}{(l.Shaded ? "s" : "")}{(l.DoubleSided ? "d" : "")}{(l.NoDepthTest ? "n" : "")}{(l.FixedSize ? "f" : "")}" +
                                  $"a{(int)l.AlphaCut}f{(int)l.TextureFilter}aa{(int)l.AlphaAntialiasingMode}{(l.OutlineSize > 0 ? "o" : "")}");
                        break;
                    default: return null;
                }
                return sb.ToString();
            case CanvasItem c:
                sb.Append("|m:").Append(MatKey(c.Material)).Append(c.UseParentMaterial ? "|up" : "");
                return sb.ToString();
        }
        return null;
    }

    static bool MeshKey(Mesh mesh, Func<int, Material?> mat, StringBuilder sb)
    {
        var rid = mesh.GetRid();
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
        {
            var d = RenderingServer.MeshGetSurface(rid, s);
            ulong format = d.TryGetValue("format", out var f) ? f.AsUInt64() : 0;
            long prim = d.TryGetValue("primitive", out var p) ? p.AsInt64() : -1;
            sb.Append($"|s{format:x}p{prim}:").Append(MatKey(mat(s)));
        }
        return true;
    }

    static string MatKey(Material? m)
    {
        if (m == null) return "-";
        var sb = new StringBuilder();
        switch (m)
        {
            case ShaderMaterial sm:
                var sh = sm.Shader;
                sb.Append("S:").Append(sh == null ? "none" : sh.ResourcePath.Length > 0 && !sh.ResourcePath.Contains("::") ? sh.ResourcePath : $"code{Hash(sh.Code)}");
                break;
            default:
                // A built-in material (StandardMaterial3D, ORMMaterial3D, ParticleProcessMaterial, CanvasItemMaterial...): its
                // shader is made from its switches (bools and enums) and which texture slots are filled.
                sb.Append(m.GetClass()).Append(':');
                foreach (var pr in m.GetPropertyList())
                {
                    int usage = pr["usage"].AsInt32();
                    if ((usage & (int)PropertyUsageFlags.Storage) == 0) continue;
                    var type = (Variant.Type)pr["type"].AsInt32();
                    string name = pr["name"].AsString();
                    if (name is "render_priority" or "resource_local_to_scene" or "resource_name" or "resource_path") continue;
                    if (type is Variant.Type.Bool) sb.Append(m.Get(name).AsBool() ? '1' : '0');
                    else if (type is Variant.Type.Int) sb.Append(m.Get(name).AsInt64()).Append(',');
                    else if (type is Variant.Type.Object && name != "next_pass" && name != "script") sb.Append(m.Get(name).Obj is Texture ? 'T' : '_');
                }
                break;
        }
        if (m.NextPass != null) sb.Append(">").Append(MatKey(m.NextPass));
        return sb.ToString();
    }

    static string Hash(string s)
    {
        ulong h = 1469598103934665603UL;
        foreach (char c in s) { h ^= c; h *= 1099511628211UL; }
        return h.ToString("x16");
    }

    // ---------------------------------------------------------------- the stand-in

    /// <summary>The same engine class with the same stored switches, no script and no children; every mesh cut to one
    /// primitive of the same format; every texture a 4x4 one of the same kind; every material a copy so made.</summary>
    static Node? StandIn(Node n)
    {
        var copy = ClassDB.Instantiate(n.GetClass()).AsGodotObject() as Node;
        if (copy == null) return null;
        var memo = new Dictionary<ulong, GodotObject>();
        foreach (var pr in n.GetPropertyList())
        {
            int usage = pr["usage"].AsInt32();
            if ((usage & (int)PropertyUsageFlags.Storage) == 0) continue;
            string name = pr["name"].AsString();
            if (name is "script" or "owner" or "scene_file_path" or "unique_name_in_owner" or "transform" or "position" or "rotation" or "scale" or "quaternion" or "basis"
                or "rotation_edit_mode" or "rotation_order" or "top_level" or "visible" or "process_mode" or "skeleton" or "skin" or "multiplayer" or "anchors_preset"
                or "size" or "layout_mode" or "offset_left" or "offset_top" or "offset_right" or "offset_bottom" or "anchor_left" or "anchor_top" or "anchor_right" or "anchor_bottom"
                or "visibility_parent" or "custom_aabb" or "editor_description" || name.StartsWith("metadata/")) continue;
            var v = n.Get(name);
            if (v.VariantType == Variant.Type.Object) { var o = v.AsGodotObject(); if (o is Resource r) copy.Set(name, Scrub(r, memo)); else if (o == null) copy.Set(name, v); }
            else if (v.VariantType == Variant.Type.Array && v.AsGodotArray() is { } arr && arr.Any(e => e.Obj is Resource))
                copy.Set(name, new Godot.Collections.Array(arr.Select(e => e.Obj is Resource rr ? (Variant)Scrub(rr, memo) : e)));
            else copy.Set(name, v);
        }
        if (copy is MeshInstance3D cmi && n is MeshInstance3D omi && omi.Mesh != null)
            for (int s = 0; s < omi.Mesh.GetSurfaceCount(); s++)
                if (omi.GetSurfaceOverrideMaterial(s) is { } so) cmi.SetSurfaceOverrideMaterial(s, (Material)Scrub(so, memo));
        return copy;
    }

    static Resource Scrub(Resource r, Dictionary<ulong, GodotObject> memo)
    {
        if (memo.TryGetValue(r.GetInstanceId(), out var done)) return (Resource)done;
        Resource result = r switch
        {
            Texture t => Placeholder(t),
            Material m => ScrubMat(m, memo),
            PrimitiveMesh pm => pm,
            Mesh mesh => TinyMesh(mesh, memo),
            MultiMesh mm => new MultiMesh { TransformFormat = mm.TransformFormat, UseColors = mm.UseColors, UseCustomData = mm.UseCustomData, Mesh = mm.Mesh == null ? null : (Mesh)Scrub(mm.Mesh, memo), InstanceCount = 1 },
            SpriteFrames => new SpriteFrames(),
            _ => r,
        };
        memo[r.GetInstanceId()] = result;
        return result;
    }

    static Material ScrubMat(Material m, Dictionary<ulong, GodotObject> memo)
    {
        var c = (Material)m.Duplicate(false);
        c.ResourcePath = "";
        if (c is ShaderMaterial sm && sm.Shader != null)
        {
            foreach (var u in sm.Shader.GetShaderUniformList())
            {
                string name = u.AsGodotDictionary()["name"].AsString();
                if (sm.GetShaderParameter(name).Obj is Texture t) sm.SetShaderParameter(name, Placeholder(t));
            }
        }
        else
        {
            foreach (var pr in c.GetPropertyList())
            {
                string name = pr["name"].AsString();
                if ((Variant.Type)pr["type"].AsInt32() == Variant.Type.Object && name != "next_pass" && c.Get(name).Obj is Texture t) c.Set(name, Placeholder(t));
            }
        }
        if (m.NextPass != null) c.NextPass = (Material)Scrub(m.NextPass, memo);
        return c;
    }

    static Texture2D? tex2d;
    static Texture Placeholder(Texture t)
    {
        static Image Img() => Image.CreateEmpty(4, 4, false, Image.Format.Rgba8);
        switch (t)
        {
            case Texture2D: return tex2d ??= ImageTexture.CreateFromImage(Img());
            case Cubemap or CubemapArray:
            {
                var imgs = new Godot.Collections.Array<Image>();
                for (int i = 0; i < 6; i++) imgs.Add(Img());
                var c = t is Cubemap ? (ImageTextureLayered)new Cubemap() : new CubemapArray();
                c.CreateFromImages(imgs);
                return c;
            }
            case Texture2DArray:
            {
                var a = new Texture2DArray();
                a.CreateFromImages(new Godot.Collections.Array<Image> { Img() });
                return a;
            }
            case Texture3D:
            {
                var d = new ImageTexture3D();
                d.Create(Image.Format.Rgba8, 4, 4, 1, false, new Godot.Collections.Array<Image> { Img() });
                return d;
            }
            default: return tex2d ??= ImageTexture.CreateFromImage(Img());
        }
    }

    // Each surface cut to its first primitive, every array kept (so the vertex format is the same), its material scrubbed.
    static Mesh TinyMesh(Mesh mesh, Dictionary<ulong, GodotObject> memo)
    {
        var o = new ArrayMesh();
        var rid = mesh.GetRid();
        for (int s = 0; s < mesh.GetSurfaceCount(); s++)
        {
            var d = RenderingServer.MeshGetSurface(rid, s);
            ulong format = d.TryGetValue("format", out var f) ? f.AsUInt64() : 0;
            var prim = (Mesh.PrimitiveType)(d.TryGetValue("primitive", out var p) ? p.AsInt32() : 3);
            var arrays = mesh.SurfaceGetArrays(s);
            int nv = arrays[(int)Mesh.ArrayType.Vertex].VariantType == Variant.Type.Nil ? 0 :
                arrays[(int)Mesh.ArrayType.Vertex].Obj is Vector3[] v3 ? v3.Length : arrays[(int)Mesh.ArrayType.Vertex].AsVector2Array().Length;
            if (nv == 0) continue;
            int keep = Math.Min(nv, prim switch { Mesh.PrimitiveType.Points => 1, Mesh.PrimitiveType.Lines or Mesh.PrimitiveType.LineStrip => 2, _ => 3 });
            var cut = new Godot.Collections.Array();
            for (int a = 0; a < (int)Mesh.ArrayType.Max; a++)
            {
                var v = arrays[a];
                if (a == (int)Mesh.ArrayType.Bones || a == (int)Mesh.ArrayType.Weights) { cut.Add(default(Variant)); continue; }
                if (a == (int)Mesh.ArrayType.Index) { cut.Add(v.VariantType == Variant.Type.Nil ? v : Enumerable.Range(0, keep).ToArray()); continue; }
                cut.Add(Cut(v, nv, keep));
            }
            // (the format's flags beyond the arrays themselves: custom channel formats, 2D vertices, compression)
            ulong flags = format & 0x3FFFE000UL & ~(ulong)Mesh.ArrayFormat.FlagUse8BoneWeights;
            o.AddSurfaceFromArrays(prim, cut, null, null, (Mesh.ArrayFormat)flags);
            var m = mesh.SurfaceGetMaterial(s);
            if (m != null) o.SurfaceSetMaterial(o.GetSurfaceCount() - 1, (Material)Scrub(m, memo));
        }
        return o;
    }

    static Variant Cut(Variant v, int nv, int keep)
    {
        int Per(int len) => Math.Max(1, len / nv);
        switch (v.VariantType)
        {
            case Variant.Type.PackedVector3Array: return v.AsVector3Array()[..keep];
            case Variant.Type.PackedVector2Array: return v.AsVector2Array()[..keep];
            case Variant.Type.PackedColorArray: return v.AsColorArray()[..keep];
            case Variant.Type.PackedFloat32Array: { var a = v.AsFloat32Array(); return a[..(Per(a.Length) * keep)]; }
            case Variant.Type.PackedInt32Array: { var a = v.AsInt32Array(); return a[..(Per(a.Length) * keep)]; }
            case Variant.Type.PackedByteArray: { var a = v.AsByteArray(); return a[..(Per(a.Length) * keep)]; }
            default: return v;
        }
    }
}
