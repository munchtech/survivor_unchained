using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Storybook;

namespace SurvivorUnchained.View;

/// <summary>
/// The storybook's pictures: textures loaded a plate ahead on a thread and
/// let go after, the shaders (one per blend), and the small soft sprites the
/// particles draw with, made here so they read as painted dabs rather than
/// engine sparkles.
/// </summary>
public static class StoryArt
{
    static readonly Dictionary<string, Shader> layerShaders = new();
    static Shader? mist, compose;

    public static Shader Layer(string blend)
    {
        if (layerShaders.TryGetValue(blend, out var sh)) return sh;
        var src = GD.Load<Shader>("res://shaders/storybook/story_layer.gdshader");
        if (blend == "mix") return layerShaders[blend] = src;
        // The blend is fixed in a shader's render mode, so each one is its own copy.
        string mode = blend switch { "add" => "blend_add", "screen" => "blend_premul_alpha", "multiply" => "blend_mul", _ => "blend_mix" };
        sh = new Shader { Code = src.Code.Replace("render_mode blend_mix;", $"render_mode {mode};") };
        return layerShaders[blend] = sh;
    }

    public static Shader Mist => mist ??= GD.Load<Shader>("res://shaders/storybook/story_mist.gdshader");
    public static Shader Compose => compose ??= GD.Load<Shader>("res://shaders/storybook/story_compose.gdshader");

    /// <summary>Every texture a plate draws with (to load ahead).</summary>
    public static IEnumerable<string> Paths(StoryPlate p)
    {
        foreach (var l in p.Layers)
        {
            if (l.Image != null) yield return l.Image;
            foreach (var f in l.Frames ?? new()) yield return f.Image;
            foreach (var t in l.Touch ?? new())
                foreach (var k in new[] { "mask", "map" })
                    if (t.Str(k) is string m) yield return m;
        }
        foreach (var fx in p.Fx) if (fx.Str("texture") is string tx) yield return tx;
        if (p.In.Map != null) yield return p.In.Map;
    }

    /// <summary>Starts loading a plate's textures on a thread.</summary>
    public static void Preload(StoryPlate p)
    {
        foreach (var path in Paths(p).Distinct())
            if (ResourceLoader.Exists(path) && requested.Add(path)) ResourceLoader.LoadThreadedRequest(path, "", true);
    }

    /// <summary>Threaded loads asked for and not yet taken (the loader holds each until it is taken).</summary>
    static readonly HashSet<string> requested = new();

    /// <summary>A storybook over: every load still held (a plate loaded ahead and never drawn: a skip,
    /// --sb-from) taken and let go.</summary>
    public static void Release()
    {
        foreach (var path in requested)
            if (ResourceLoader.LoadThreadedGetStatus(path) is ResourceLoader.ThreadLoadStatus.InProgress or ResourceLoader.ThreadLoadStatus.Loaded)
                (ResourceLoader.LoadThreadedGet(path) as IDisposable)?.Dispose();
        requested.Clear();
    }

    /// <summary>A texture, taken from its threaded load if one was asked for (it waits for it if
    /// it is not done), else loaded now.</summary>
    public static Texture2D? Tex(string path)
    {
        if (!ResourceLoader.Exists(path)) { GD.PushWarning($"storybook: no {path}"); return null; }
        var st = ResourceLoader.LoadThreadedGetStatus(path);
        if (requested.Remove(path) && st is ResourceLoader.ThreadLoadStatus.InProgress or ResourceLoader.ThreadLoadStatus.Loaded)
            return ResourceLoader.LoadThreadedGet(path) as Texture2D;
        return GD.Load<Texture2D>(path);
    }

    static ImageTexture? white, dot, puff, drop;

    public static ImageTexture White => white ??= ImageTexture.CreateFromImage(Image.CreateEmpty(4, 4, false, Image.Format.Rgba8).Also(i => i.Fill(Colors.White)));

    /// <summary>A soft dab: a round falloff with a slightly uneven edge, like a brush's touch.</summary>
    public static ImageTexture Dot => dot ??= Dab(64, 0.55, 0.12, 7);

    /// <summary>A smoke puff: a broad, clouded blot.</summary>
    public static ImageTexture Puff => puff ??= Dab(128, 0.9, 0.45, 3);

    /// <summary>A drop: a dab drawn long.</summary>
    public static ImageTexture Drop => drop ??= Dab(64, 0.5, 0.08, 11, stretch: 2.6);

    static ImageTexture Dab(int n, double hardness, double cloud, int seed, double stretch = 1)
    {
        var img = Image.CreateEmpty(n, n, true, Image.Format.Rgba8);
        var noise = new FastNoiseLite { Seed = seed, Frequency = 0.09f, FractalOctaves = 3 };
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                // Drawn long down its height for a drop (stretch > 1), and narrower across.
                double u = ((x + 0.5) / n * 2 - 1) * Math.Sqrt(stretch), v = ((y + 0.5) / n * 2 - 1);
                double r = Math.Sqrt(u * u + v * v);
                double nz = noise.GetNoise2D(x, y) * 0.5 + 0.5;
                double edge = r + (nz - 0.5) * cloud;
                double a = Math.Clamp((1 - edge) / (1 - hardness * 0.9), 0, 1);
                a = a * a * (3 - 2 * a);
                a *= 1 - cloud * 0.6 * (1 - nz);
                img.SetPixel(x, y, new Color(1, 1, 1, (float)Math.Clamp(a, 0, 1)));
            }
        img.GenerateMipmaps();
        return ImageTexture.CreateFromImage(img);
    }

    static T Also<T>(this T t, Action<T> f) { f(t); return t; }

    public static Color Col(string? hex, Color or) => hex == null ? or : new Color(hex);
}

/// <summary>
/// One plate drawn into its own picture (a SubViewport the screen's composite
/// mixes): its layers as flat planes placed by the 2.5D lens each frame, their
/// touches, its particles and mist. Exists only while it is drawn.
/// </summary>
public partial class PlateView : SubViewport
{
    public readonly PlateSpan Span;
    readonly StoryFile file;
    readonly Func<double, StoryView> camera;
    public readonly Func<double, StoryGrade> Grade;
    readonly List<LayerView> layers = new();
    readonly List<FxView> fx = new();

    sealed class LayerView
    {
        public StoryLayer L = null!;
        public Node2D Node = null!;
        public readonly List<(CanvasItem Item, ShaderMaterial? Mat, double T)> Frames = new();
        public Func<double, LayerPose> Pose = null!;
        /// <summary>Image px to canvas px, and the layer's size in canvas px.</summary>
        public double Scale;
        public Vector2 Size;
    }

    sealed class FxView
    {
        public StoryFx F = null!;
        public Node2D Node = null!;
        public ShaderMaterial? Mat;
        public List<(GpuParticles2D P, double At)> Bursts = new();
        public int NextBurst;
    }

    public PlateView(StoryFile file, PlateSpan span, Vector2I size, double startT)
    {
        this.file = file;
        Span = span;
        Name = $"Plate_{span.Plate.Id}";
        Size = size;
        Disable3D = true;
        TransparentBg = false;
        RenderTargetUpdateMode = UpdateMode.Always;
        CanvasItemDefaultTextureFilter = DefaultCanvasItemTextureFilter.LinearWithMipmaps;
        camera = StoryMotion.Camera(span.Plate.Camera, file.CanvasW, file.CanvasH);
        Grade = StoryMotion.Grade(span.Plate.Grade);
        // Paper-black behind everything (the project's clear colour is a night blue).
        AddChild(new ColorRect { Color = Colors.Black, Size = size, MouseFilter = Control.MouseFilterEnum.Ignore });
        // Far first; the same depth in the order written.
        int order = 0;
        var items = span.Plate.Layers.Select(l => (Z: l.Z, Order: order++, Layer: (object)l))
            .Concat(span.Plate.Fx.Select(f => (Z: f.Z, Order: order++, Layer: (object)f)))
            .OrderByDescending(x => x.Z).ThenBy(x => x.Order);
        foreach (var it in items)
        {
            if (it.Layer is StoryLayer l) AddLayer(l);
            else AddFx((StoryFx)it.Layer, startT);
        }
    }

    void AddLayer(StoryLayer l)
    {
        var v = new LayerView { L = l, Node = new Node2D { Name = l.Id }, Pose = StoryMotion.Layer(l.Keys, l.Opacity), Scale = l.Scale };
        AddChild(v.Node);
        if (l.Color != null && l.Image == null && (l.Frames?.Count ?? 0) == 0)
        {
            var sz = l.Size is { Length: 2 } s ? new Vector2((float)s[0], (float)s[1]) : new Vector2((float)file.CanvasW, (float)file.CanvasH);
            var card = new Sprite2D { Texture = StoryArt.White, Centered = false, Scale = sz / 4, Modulate = new Color(l.Color) };
            v.Node.AddChild(card);
            v.Frames.Add((card, null, 0));
            v.Scale = 1;
            v.Size = sz;
            if (l.Label != null)
            {
                // Written small in the corner, as a placeholder card is labelled.
                var lab = new Label { Text = l.Label, Position = new Vector2(48, sz.Y - 110), Modulate = new Color(1, 1, 1, 0.55f) };
                lab.AddThemeFontSizeOverride("font_size", 40);
                v.Node.AddChild(lab);
            }
            layers.Add(v);
            return;
        }
        var frames = l.Frames is { Count: > 0 } fr ? fr.Select(f => (f.Image, f.T)).ToList() : new List<(string, double)> { (l.Image!, 0) };
        foreach (var (path, t) in frames)
        {
            var tex = StoryArt.Tex(path);
            if (tex == null) continue;
            var sp = new Sprite2D { Texture = tex, Centered = false, TextureRepeat = l.Repeat ? CanvasItem.TextureRepeatEnum.Enabled : CanvasItem.TextureRepeatEnum.Disabled };
            var mat = new ShaderMaterial { Shader = StoryArt.Layer(l.Blend) };
            mat.SetShaderParameter("blend", Array.IndexOf(new[] { "mix", "add", "screen", "multiply" }, l.Blend));
            mat.SetShaderParameter("px", tex.GetSize());
            Touches(mat, l, tex.GetSize());
            sp.Material = mat;
            // A repeating image is drawn over the layer's whole size (its region), the texture wrapping.
            if (l.Repeat && l.Size is { Length: 2 } rs)
            {
                sp.RegionEnabled = true;
                sp.RegionRect = new Rect2(0, 0, (float)(rs[0] / l.Scale), (float)(rs[1] / l.Scale));
                mat.SetShaderParameter("px", sp.RegionRect.Size);
            }
            v.Node.AddChild(sp);
            v.Frames.Add((sp, mat, t));
            v.Size = (l.Repeat && l.Size is { Length: 2 } rs2 ? new Vector2((float)rs2[0], (float)rs2[1]) : tex.GetSize() * (float)l.Scale);
        }
        layers.Add(v);
    }

    /// <summary>A layer's touches as its shader's switches. Places (ripple centres) are canvas px,
    /// turned into the image's own px here.</summary>
    void Touches(ShaderMaterial m, StoryLayer l, Vector2 px)
    {
        double sc = l.Scale;
        Vector2 ToImg(double[] c) => new((float)((c[0] - l.Pos[0]) / sc), (float)((c[1] - l.Pos[1]) / sc));
        foreach (var t in l.Touch ?? new())
        {
            void Tex(string key, string uniform) { if (t.Str(key) is string p && StoryArt.Tex(p) is { } tx) m.SetShaderParameter(uniform, tx); }
            switch (t.Kind)
            {
                case "flicker":
                    m.SetShaderParameter("flicker_on", true);
                    m.SetShaderParameter("flicker_rate", t.Num("rate", 7));
                    m.SetShaderParameter("flicker_amount", t.Num("amount", 0.25));
                    m.SetShaderParameter("flicker_seed", t.Num("seed", 0));
                    break;
                case "sway":
                    m.SetShaderParameter("sway_on", true);
                    Tex("mask", "sway_mask");
                    m.SetShaderParameter("sway_amp", t.Num("amp", 4) / sc);
                    m.SetShaderParameter("sway_freq", t.Num("freq", 0.35));
                    if (t.Nums("dir") is { Length: 2 } d) m.SetShaderParameter("sway_dir", new Vector2((float)d[0], (float)d[1]));
                    m.SetShaderParameter("sway_scale", t.Num("scale", 220) / sc);
                    break;
                case "water":
                    m.SetShaderParameter("water_on", true);
                    Tex("mask", "water_mask");
                    m.SetShaderParameter("water_amp", t.Num("amp", 1.5) / sc);
                    m.SetShaderParameter("water_freq", t.Num("freq", 1.4));
                    m.SetShaderParameter("water_scale", t.Num("scale", 36) / sc);
                    break;
                case "ripple":
                {
                    m.SetShaderParameter("ripple_on", true);
                    Tex("mask", "ripple_mask");
                    var cs = t.Points("centers").Take(8).Select(ToImg).ToList();
                    var arr = new Vector2[8];
                    for (int i = 0; i < cs.Count; i++) arr[i] = cs[i];
                    m.SetShaderParameter("ripple_c", arr);
                    m.SetShaderParameter("ripple_n", cs.Count);
                    m.SetShaderParameter("ripple_start", t.Num("start", 0));
                    m.SetShaderParameter("ripple_period", t.Num("period", 3));
                    m.SetShaderParameter("ripple_speed", t.Num("speed", 60) / sc);
                    m.SetShaderParameter("ripple_amp", t.Num("amp", 2) / sc);
                    m.SetShaderParameter("ripple_rings", t.Num("rings", 3));
                    m.SetShaderParameter("ripple_gap", t.Num("gap", 22) / sc);
                    m.SetShaderParameter("ripple_reach", t.Num("reach", 260) / sc);
                    m.SetShaderParameter("ripple_squash", t.Num("squash", 1));
                    m.SetShaderParameter("ripple_light", t.Num("light", 0.25));
                    break;
                }
                case "reveal":
                    m.SetShaderParameter("reveal_on", true);
                    Tex("map", "reveal_map");
                    m.SetShaderParameter("reveal_t0", t.Num("t0", 0));
                    m.SetShaderParameter("reveal_t1", t.Num("t1", 1));
                    m.SetShaderParameter("reveal_soft", t.Num("soft", 0.08));
                    m.SetShaderParameter("reveal_invert", t.Bool("invert"));
                    break;
                case "scroll":
                    if (t.Nums("speed") is { Length: 2 } s) m.SetShaderParameter("scroll_speed", new Vector2((float)(-s[0] / sc), (float)(-s[1] / sc)));
                    break;
            }
        }
    }

    void AddFx(StoryFx f, double startT)
    {
        var v = new FxView { F = f, Node = new Node2D { Name = $"fx_{f.Preset ?? f.Kind}" } };
        AddChild(v.Node);
        if (f.Kind == "mist")
        {
            var r = f.Nums("rect") ?? [0, 0, file.CanvasW, file.CanvasH / 3];
            var sp = new Sprite2D { Texture = StoryArt.White, Centered = false, Position = new Vector2((float)r[0], (float)r[1]), Scale = new Vector2((float)r[2], (float)r[3]) / 4 };
            var m = new ShaderMaterial { Shader = StoryArt.Mist };
            m.SetShaderParameter("size", new Vector2((float)r[2], (float)r[3]));
            m.SetShaderParameter("color", StoryArt.Col(f.Str("color"), new Color(0.75f, 0.8f, 0.85f)));
            m.SetShaderParameter("density", f.Num("density", 0.5));
            var spd = f.Nums("speed") ?? [12, 0];
            m.SetShaderParameter("speed", new Vector2((float)spd[0], spd.Length > 1 ? (float)spd[1] : 0));
            m.SetShaderParameter("scale", f.Num("scale", 260));
            m.SetShaderParameter("seed", f.Num("seed", 0));
            sp.Material = m;
            v.Mat = m;
            v.Node.AddChild(sp);
        }
        else
        {
            var at = f.Nums("at") ?? [file.CanvasW / 2, file.CanvasH / 2];
            v.Node.AddChild(StoryParticles.Make(f, false, startT));
            // Bursts before the moment it is first drawn (a run started mid-plate) are not fired late.
            foreach (var bt in (f.Nums("burst") ?? []).Where(b => b >= startT))
            {
                var b = StoryParticles.Make(f, true, startT);
                v.Node.AddChild(b);
                v.Bursts.Add((b, bt));
            }
            foreach (var c in v.Node.GetChildren()) ((Node2D)c).Position = new Vector2((float)at[0], (float)at[1]);
        }
        fx.Add(v);
    }

    /// <summary>The plate at its own time t (seconds from its "at").</summary>
    public void Show(double t)
    {
        var cam = camera(t);
        double W = Size.X, H = Size.Y;
        foreach (var v in layers)
        {
            var (sc, ox, oy, rot) = StoryLens.Layer(cam, v.L.Z, file.CanvasW, file.CanvasH, W, H);
            var proj = new Transform2D((float)rot, new Vector2((float)sc, (float)sc), 0, new Vector2((float)ox, (float)oy));
            var p = v.Pose(t);
            var pos = new Vector2((float)v.L.Pos[0], (float)v.L.Pos[1]);
            var pivot = v.L.Pivot is { Length: 2 } pv ? new Vector2((float)pv[0], (float)pv[1]) : pos + v.Size / 2;
            // Its own move: about its pivot, then offset; the image's pixels scaled to the canvas's.
            var own = Transform2D.Identity.Translated(-pivot).Scaled(new Vector2((float)p.Scale, (float)p.Scale))
                .Rotated(Mathf.DegToRad((float)p.Rot)).Translated(pivot + new Vector2((float)p.Dx, (float)p.Dy));
            var img = new Transform2D(0, new Vector2((float)v.Scale, (float)v.Scale), 0, pos);
            v.Node.Transform = proj * own * img;
            var shown = v.L.Frames is { Count: > 0 } ? StoryMotion.Frames(v.L.Frames, t) : null;
            for (int i = 0; i < v.Frames.Count; i++)
            {
                var (item, mat, _) = v.Frames[i];
                float a = (float)(p.Opacity * (shown != null && i < shown.Length ? shown[i] : 1));
                item.Visible = a > 0.001f;
                var mc = item.Modulate; mc.A = a; item.Modulate = mc;
                mat?.SetShaderParameter("t", t);
            }
        }
        foreach (var v in fx)
        {
            var (sc, ox, oy, rot) = StoryLens.Layer(cam, v.F.Z, file.CanvasW, file.CanvasH, W, H);
            v.Node.Transform = new Transform2D((float)rot, new Vector2((float)sc, (float)sc), 0, new Vector2((float)ox, (float)oy));
            v.Mat?.SetShaderParameter("t", t);
            while (v.NextBurst < v.Bursts.Count && t >= v.Bursts[v.NextBurst].At)
            {
                var b = v.Bursts[v.NextBurst++].P;
                b.Restart();
                b.Emitting = true;
            }
        }
    }
}

/// <summary>The particle presets (docs/storybook/README.md, "Particles"), tuned by the fx's own numbers.</summary>
public static class StoryParticles
{
    sealed record Preset(double Rate, double Life, double[] Speed, double[] Dir, double Spread, double[] Gravity, double[] Size,
        string Start, string End, bool Additive, double Grow, double Turb, string Tex);

    static readonly Dictionary<string, Preset> Presets = new()
    {
        ["smoke"] = new(6, 5, [25, 50], [0, -1], 14, [0, -6], [70, 120], "#5e5852a0", "#3a363200", false, 2.4, 0.5, "puff"),
        ["sparks"] = new(10, 0.9, [110, 240], [0, -1], 38, [0, 360], [5, 9], "#ffd890ff", "#ff5a1a00", true, 0.6, 0.15, "dot"),
        ["motes"] = new(4, 6, [8, 22], [0, -1], 30, [0, -3], [6, 12], "#ffcf7ae6", "#ff9a3000", true, 0.8, 0.6, "dot"),
        ["bubbles"] = new(12, 1.6, [110, 210], [0, -1], 12, [0, -160], [5, 13], "#cfe8e080", "#cfe8e000", false, 1.3, 0.35, "dot"),
        ["drips"] = new(3, 1.2, [0, 8], [0, 1], 4, [0, 900], [5, 8], "#a8c0c8d0", "#a8c0c860", false, 1, 0, "drop"),
        ["ash"] = new(5, 7, [8, 18], [0.2, 1], 40, [0, 10], [4, 8], "#8a8580b0", "#8a858000", false, 1, 0.7, "dot"),
        ["snow"] = new(8, 8, [14, 28], [0.15, 1], 25, [0, 14], [4, 9], "#e8eef4e0", "#e8eef400", false, 1, 0.5, "dot"),
    };

    /// <summary>One emitter: steady, or a one-shot burst (fired by the plate at its times).</summary>
    public static GpuParticles2D Make(StoryFx f, bool burst, double startT)
    {
        var pr = Presets[f.Preset ?? "smoke"];
        double rate = f.Num("rate", pr.Rate), life = f.Num("life", pr.Life);
        var speed = f.Nums("speed") ?? pr.Speed; if (speed.Length == 1) speed = [speed[0], speed[0]];
        var dir = f.Nums("dir") ?? pr.Dir;
        var grav = f.Nums("gravity") ?? pr.Gravity;
        var size = f.Nums("size") ?? pr.Size; if (size.Length == 1) size = [size[0], size[0]];
        var cols = f.Strs("color");
        var c0 = new Color(cols.Count > 0 ? cols[0] : pr.Start);
        var c1 = cols.Count > 1 ? new Color(cols[1]) : cols.Count == 1 ? new Color(c0, 0) : new Color(pr.End);
        var area = f.Nums("area") ?? [40, 10];
        var tex = (f.Str("texture") is string tp ? StoryArt.Tex(tp) : null) ?? pr.Tex switch { "puff" => StoryArt.Puff, "drop" => StoryArt.Drop, _ => StoryArt.Dot };

        int amount = burst ? Math.Max(1, (int)f.Num("count", 24)) : Math.Max(1, (int)Math.Ceiling(rate * life) + 1);
        var m = new ParticleProcessMaterial
        {
            EmissionShape = ParticleProcessMaterial.EmissionShapeEnum.Box,
            EmissionBoxExtents = new Vector3((float)area[0] / 2, (float)(area.Length > 1 ? area[1] : area[0]) / 2, 0),
            Direction = new Vector3((float)dir[0], (float)dir[1], 0),
            Spread = (float)f.Num("spread", pr.Spread),
            InitialVelocityMin = (float)speed[0], InitialVelocityMax = (float)speed[1],
            Gravity = new Vector3((float)grav[0], (float)grav[1], 0),
            ScaleMin = (float)(size[0] / tex.GetWidth()), ScaleMax = (float)(size[1] / tex.GetWidth()),
            AngleMin = 0, AngleMax = 360,
            DampingMin = 0, DampingMax = (float)f.Num("damping", 0),
        };
        // Grows (smoke spreads as it rises) or shrinks over its life.
        double grow = f.Num("grow", pr.Grow);
        var sc = new Curve();
        sc.AddPoint(new Vector2(0, (float)Math.Min(1, 1 / Math.Max(grow, 1e-3))));
        sc.AddPoint(new Vector2(1, (float)Math.Min(1, grow)));
        sc.MaxValue = 1;
        m.ScaleCurve = new CurveTexture { Curve = sc };
        if (grow > 1) { m.ScaleMin *= (float)grow; m.ScaleMax *= (float)grow; }
        // In quickly, out slowly: nothing pops.
        var g = new Gradient();
        g.SetColor(0, new Color(c0, 0));
        g.SetOffset(0, 0);
        g.SetColor(1, c1);
        g.SetOffset(1, 1);
        g.AddPoint(0.12f, c0);
        m.ColorRamp = new GradientTexture1D { Gradient = g };
        double turb = f.Num("wobble", pr.Turb);
        if (turb > 0)
        {
            m.TurbulenceEnabled = true;
            m.TurbulenceNoiseStrength = (float)(turb * 4);
            m.TurbulenceNoiseScale = 9;
            m.TurbulenceNoiseSpeedRandom = 0.2f;
            m.TurbulenceInfluenceMin = (float)(0.02 * turb);
            m.TurbulenceInfluenceMax = (float)(0.08 * turb);
        }
        var p = new GpuParticles2D
        {
            Amount = amount,
            Lifetime = life,
            ProcessMaterial = m,
            Texture = tex,
            LocalCoords = true,
            OneShot = burst,
            Explosiveness = burst ? 0.92f : 0,
            Randomness = 0.3f,
            Emitting = !burst,
            // The same particles every time it plays: frames and captures repeat.
            UseFixedSeed = true,
            Seed = (uint)(f.Num("seed", 1) + (burst ? 1000 : 0)),
            // A steady emitter is already going when the plate appears.
            Preprocess = burst ? 0 : life,
            VisibilityRect = new Rect2(-4000, -4000, 8000, 8000),
            TextureFilter = CanvasItem.TextureFilterEnum.LinearWithMipmaps,
        };
        if (f.Bool("additive", pr.Additive)) p.Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
        return p;
    }
}
