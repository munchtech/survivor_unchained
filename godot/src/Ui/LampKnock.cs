using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The Lamps' Open wide knockout (docs/design/LAMPS_SCREEN_BRIEF.md §16 "Edges, A"): no lamp, road, halo or label
/// crosses the HUD's foot or her. Two half-size masks the board's shaders sample once (shaders/ui_lamps_field.gdshaderinc,
/// knock_hud and knock_her, 1 = the board shows):
/// the foot's, from the HUD's own art alpha (her figure, the keeper, the plate) and its live discs (the seats, the coin,
/// the Flare's glass, the flask, the dash) at the bottom HUD's scale (HudBottom), grown 32 px soft (48 px at the girl's
/// face), built once per scale on the CPU; and hers, live (HerMask).
/// </summary>
public static class LampKnock
{
    /// <summary>The masks are half the screen's size.</summary>
    public const int Down = 2, W = 1920 / Down, H = 1080 / Down;
    public const float Grow = 32, GrowFace = 48;

    static ImageTexture? hud;
    static float builtScale = -1;
    static readonly List<Box> boxes = new();
    static Vector2 face;
    static double buildMs;

    /// <summary>The foot's knockout (R8, 1 = clear).</summary>
    public static Texture2D Hud { get { Build(); return hud!; } }
    /// <summary>Where the foot's knockout is not clear, as boxes on the screen (16 px rows): the card and the labels keep out.</summary>
    public static IReadOnlyList<Box> Boxes { get { Build(); return boxes; } }
    /// <summary>The girl's face on the screen (the knockout is 48 px there).</summary>
    public static Vector2 Face { get { Build(); return face; } }
    public static double BuildMs => buildMs;
    static float[] alpha = [];
    /// <summary>The higher of the two statues' heads (the foot's art top, left and right of the bar's middle).</summary>
    public static float HeadsTop { get; private set; }

    /// <summary>The statues' inner edges across a band of rows (screen px): the girl's rightmost art left of the bar's
    /// middle, the keeper's leftmost right of it.</summary>
    public static (float Left, float Right) InnerEdges(float y0, float y1)
    {
        Build();
        float mid = HudBottom.MapX(960), l = 0, r = 1920;
        int a = Math.Max(0, (int)(y0 / Down)), b = Math.Min(H, (int)Math.Ceiling(y1 / Down));
        int pl = (int)(HudBottom.MapX(DgPanel.Rect.Position.X) / Down), pr = (int)(HudBottom.MapX(DgPanel.Rect.End.X) / Down);
        for (int y = a; y < b; y++)
            for (int x = 0; x < W; x++)
                if (alpha[y * W + x] > 0.02f && (x < pl || x >= pr))
                {
                    float px = x * Down;
                    if (px < mid) l = Math.Max(l, px + Down); else r = Math.Min(r, px);
                }
        return (l, r);
    }

    /// <summary>What the build reads from the HUD's art and geo (gathered on the main thread; the arithmetic runs on a
    /// worker: phase 5 built it on the first open, 122-158 ms in the open's frame).</summary>
    sealed record Inputs(float Scale, List<(ArtImg? Art, Rect2 R)> Arts, List<(Vector2 C, float R)> Discs, ArtImg? Girl, Rect2 GirlR);
    sealed record Built(byte[] Bytes, List<Box> Boxes, Vector2 Face, float[] Alpha, float HeadsTop, double Ms);

    static System.Threading.Tasks.Task<Built>? pending;
    static float pendingScale = -1;

    /// <summary>Build it ahead (the HUD calls this when it loads): the art is read here, the rest on a worker; the first
    /// open then only makes the texture (Build waits for the worker if it is still running).</summary>
    public static void Prewarm()
    {
        if ((hud != null && Math.Abs(builtScale - HudBottom.Scale) < 1e-4f) || (pending != null && Math.Abs(pendingScale - HudBottom.Scale) < 1e-4f)) return;
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        var inp = Gather();
        pendingScale = inp.Scale;
        pending = System.Threading.Tasks.Task.Run(() => Compute(inp));
        GD.Print($"LAMPWIDE knock: prewarm started at HUD scale {inp.Scale:F2} (art read in {(System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:F1} ms on the main thread)");
    }

    static void Build()
    {
        if (hud != null && Math.Abs(builtScale - HudBottom.Scale) < 1e-4f) return;
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        bool warm = pending != null && Math.Abs(pendingScale - HudBottom.Scale) < 1e-4f;
        var b = warm ? pending!.Result : Compute(Gather());
        pending = null;
        builtScale = HudBottom.Scale;
        var img = Image.CreateFromData(W, H, false, Image.Format.L8, b.Bytes);
        hud = ImageTexture.CreateFromImage(img);
        boxes.Clear();
        boxes.AddRange(b.Boxes);
        face = b.Face;
        alpha = b.Alpha;
        HeadsTop = b.HeadsTop;
        buildMs = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        GD.Print($"LAMPWIDE knock: {(warm ? "prewarmed" : "built")} ({b.Ms:F1} ms of work{(warm ? " on a worker" : "")}), {buildMs:F1} ms on the open's frame, at HUD scale {builtScale:F2}, {boxes.Count} boxes, face {face.X:F0},{face.Y:F0}");
    }

    static Inputs Gather()
    {
        float s = HudBottom.Scale;
        // the art: her figure (her quad at her group's scale), the keeper and his lip, the plate
        float gs = DgPanel.GroupScale;
        var girlTl = DgPanel.GirlAnchor + (LifeLamp.At - DgPanel.GirlAnchor) * gs + DgPanel.GirlOffset;
        var girl = HudBottom.Map(new Rect2(girlTl, LifeLamp.Canvas * gs));
        var girlImg = Art("lamp_life/drowned/lamp_cold.png");
        var kr = HudBottom.Map(DgPanel.KeeperRect);
        var (plate, at) = DgPanel.Plate();
        var arts = new List<(ArtImg?, Rect2)>
        {
            (girlImg, girl), (Art("dg_keeper/keeper.png"), kr), (Art("dg_keeper/keeper_lip.png"), kr),
            (Art(plate), HudBottom.Map(new Rect2(DgPanel.Rect.Position + at.Position, at.Size))),
        };
        // the live parts over the art (each a disc, a pixel over its rim)
        var discs = new List<(Vector2, float)>();
        void Disc(Vector2 c, float r) => discs.Add((HudBottom.Map(c), (r + 1) * s));
        for (int i = 0; i < Content.Weapons.MaxWeapons; i++) Disc(DgPanel.Seat(i), DgPanel.SeatR);
        Disc(DgPanel.Coin, DgPanel.ArchR);
        Disc(DgPanel.GlassAt, DgPanel.GlassOuterR);
        // (the flask and the dash by their geo scales: the dash's ring is 26 px at 0.84; UI 29 seats the flask in a ring as
        // the dash's, at its own scale; the count's badge at its own radius)
        Disc(DgPanel.FlaskAt, 31 * DgPanel.FlaskScale);
        Disc(DgPanel.CountAt, DgPanel.CountR + 1);
        Disc(DgPanel.DashAt, 31 * DgPanel.DashScale);
        Disc(new Vector2(DgPanel.Globe.X, DgPanel.Globe.Y), DgPanel.Globe.Z);
        return new Inputs(s, arts, discs, girlImg, girl);
    }

    /// <summary>The arithmetic (no engine calls: a worker runs it).</summary>
    static Built Compute(Inputs inp)
    {
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        float s = inp.Scale;
        var a = new float[W * H];
        foreach (var (art, r) in inp.Arts) Stamp(a, art, r);
        foreach (var (c, r) in inp.Discs) DiscAt(a, c, r);
        // the girl's face: the middle of her art's top band (her head), on the screen
        var fc = FaceOf(inp.Girl, inp.GirlR);
        float headsTop = 1080;
        for (int i = 0; i < a.Length && headsTop >= 1080; i++) if (a[i] > 0.5f) headsTop = (i / W) * Down;
        // the distance from the foot (screen px), then the soft knockout: 0 on the art, 1 at 32 px (48 at her face)
        var d = Distance(a);
        var bytes = new byte[W * H];
        float fr = 70 * s;
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                var p = new Vector2((x + 0.5f) * Down, (y + 0.5f) * Down);
                float f = MathF.Exp(-(p - fc).LengthSquared() / (fr * fr));
                float k = Grow + (GrowFace - Grow) * Math.Clamp(f * 1.6f, 0, 1);
                float t = Math.Clamp(d[y * W + x] / k, 0, 1);
                bytes[y * W + x] = (byte)Math.Round(t * t * (3 - 2 * t) * 255);
            }
        // the boxes: per 16 px row, each run of cells not clear
        var bx = new List<Box>();
        const int Row = 16 / Down;
        for (int y0 = 0; y0 < H; y0 += Row)
        {
            int run = -1;
            for (int x = 0; x <= W; x++)
            {
                bool set = false;
                if (x < W) for (int y = y0; y < Math.Min(H, y0 + Row) && !set; y++) set = bytes[y * W + x] < 250;
                if (set && run < 0) run = x;
                else if (!set && run >= 0) { bx.Add(new Box(run * Down, y0 * Down, x * Down, Math.Min(H, y0 + Row) * Down)); run = -1; }
            }
        }
        double ms = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        return new Built(bytes, bx, fc, a, headsTop, ms);
    }

    sealed record ArtImg(byte[] Data, int W, int H);

    static ArtImg? Art(string rel)
    {
        var t = UiArt.Tex(rel, false);
        var im = t?.GetImage();
        if (im == null || im.IsEmpty()) { GD.PushError($"LampKnock: {rel} did not load: the knockout leaves it out"); return null; }
        if (im.IsCompressed()) im.Decompress();
        if (im.GetFormat() != Image.Format.Rgba8) im.Convert(Image.Format.Rgba8);
        return new ArtImg(im.GetData(), im.GetWidth(), im.GetHeight());
    }

    /// <summary>The art's alpha over its screen rect, into the half-size grid (max with what is there).</summary>
    static void Stamp(float[] a, ArtImg? art, Rect2 r)
    {
        if (art == null) return;
        int x0 = Math.Max(0, (int)(r.Position.X / Down)), x1 = Math.Min(W, (int)Math.Ceiling(r.End.X / Down));
        int y0 = Math.Max(0, (int)(r.Position.Y / Down)), y1 = Math.Min(H, (int)Math.Ceiling(r.End.Y / Down));
        for (int y = y0; y < y1; y++)
            for (int x = x0; x < x1; x++)
            {
                // (the cell's four corners and middle: a hair's thin strand still counts)
                float m = 0;
                for (int k = 0; k < 5; k++)
                {
                    float ox = k == 4 ? 0.5f : (k & 1) * 0.9f + 0.05f, oy = k == 4 ? 0.5f : (k >> 1) * 0.9f + 0.05f;
                    float u = ((x + ox) * Down - r.Position.X) / r.Size.X, v = ((y + oy) * Down - r.Position.Y) / r.Size.Y;
                    if (u < 0 || v < 0 || u >= 1 || v >= 1) continue;
                    int ix = Math.Min(art.W - 1, (int)(u * art.W)), iy = Math.Min(art.H - 1, (int)(v * art.H));
                    m = Math.Max(m, art.Data[(iy * art.W + ix) * 4 + 3] / 255f);
                }
                if (m > a[y * W + x]) a[y * W + x] = m;
            }
    }

    static void DiscAt(float[] a, Vector2 c, float r)
    {
        int x0 = Math.Max(0, (int)((c.X - r) / Down) - 1), x1 = Math.Min(W, (int)((c.X + r) / Down) + 2);
        int y0 = Math.Max(0, (int)((c.Y - r) / Down) - 1), y1 = Math.Min(H, (int)((c.Y + r) / Down) + 2);
        for (int y = y0; y < y1; y++)
            for (int x = x0; x < x1; x++)
                if (new Vector2((x + 0.5f) * Down, (y + 0.5f) * Down).DistanceTo(c) <= r) a[y * W + x] = 1;
    }

    static Vector2 FaceOf(ArtImg? art, Rect2 r)
    {
        if (art == null) return r.Position + r.Size * new Vector2(0.4f, 0.1f);
        int top = -1;
        for (int y = 0; y < art.H && top < 0; y++)
            for (int x = 0; x < art.W; x++)
                if (art.Data[(y * art.W + x) * 4 + 3] > 128) { top = y; break; }
        if (top < 0) return r.GetCenter();
        int band = Math.Max(1, art.H / 8);
        double sx = 0, n = 0;
        for (int y = top; y < Math.Min(art.H, top + band); y++)
            for (int x = 0; x < art.W; x++)
                if (art.Data[(y * art.W + x) * 4 + 3] > 128) { sx += x; n++; }
        float fx = n > 0 ? (float)(sx / n) : art.W / 2f, fy = top + band * 0.6f;
        return r.Position + new Vector2(fx / art.W * r.Size.X, fy / art.H * r.Size.Y);
    }

    /// <summary>Each cell's distance (screen px) to the nearest cell of the foot (alpha above 0.02): a 5x5 chamfer
    /// (1, √2, √5), two passes.</summary>
    static float[] Distance(float[] a)
    {
        const float Inf = 1e9f, A = 1, B = 1.41421f, C = 2.23607f;
        var d = new float[W * H];
        for (int i = 0; i < d.Length; i++) d[i] = a[i] > 0.02f ? 0 : Inf;
        (int dx, int dy, float w)[] fwd = [(-1, 0, A), (-1, -1, B), (0, -1, A), (1, -1, B), (-2, -1, C), (-1, -2, C), (1, -2, C), (2, -1, C)];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                float v = d[y * W + x];
                if (v == 0) continue;
                foreach (var (dx, dy, w) in fwd)
                {
                    int xx = x + dx, yy = y + dy;
                    if (xx < 0 || yy < 0 || xx >= W) continue;
                    v = Math.Min(v, d[yy * W + xx] + w);
                }
                d[y * W + x] = v;
            }
        for (int y = H - 1; y >= 0; y--)
            for (int x = W - 1; x >= 0; x--)
            {
                float v = d[y * W + x];
                if (v == 0) continue;
                foreach (var (dx, dy, w) in fwd)
                {
                    int xx = x - dx, yy = y - dy;
                    if (xx >= W || yy >= H || xx < 0) continue;
                    v = Math.Min(v, d[yy * W + xx] + w);
                }
                d[y * W + x] = v;
            }
        for (int i = 0; i < d.Length; i++) d[i] *= Down;
        return d;
    }
}

/// <summary>
/// Her silhouette, live (§16 "Edges, A": she stands on her road; the mock cut her from a still): her meshes carry
/// Brush.MaskLayer while the view is open, and a camera on the main camera's view each frame draws only that layer,
/// unshaded, into a half-size viewport (her alpha); a second half-size pass grows it 10 px with a soft edge and gives
/// the board 1 - that (R). Lights that must miss her miss MaskLayer too (PlayerView, GameFront, GameCloseUp).
/// --lamps-her off: no mask (the cost check). Measured: the two viewports' GPU time (--lamps-measure).
/// </summary>
public partial class HerMask : Node
{
    public const float Feather = 10;
    SubViewport? view, soft;
    Camera3D? cam;
    readonly List<MeshInstance3D> tagged = new();
    double scanT;
    public static bool Off => SurvivorUnchained.Args.Get("lamps-her") == "off";

    /// <summary>The mask for the board (white while it isn't ready).</summary>
    public Texture2D? Texture => soft?.GetTexture();

    public override void _Ready()
    {
        var size = new Vector2I(LampKnock.W, LampKnock.H);
        view = new SubViewport
        {
            Name = "LampsHer", TransparentBg = true, Msaa3D = Viewport.Msaa.Disabled, UseTaa = false,
            ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled, PositionalShadowAtlasSize = 0, UseOcclusionCulling = false,
            DebugDraw = Viewport.DebugDrawEnum.Unshaded, RenderTargetUpdateMode = SubViewport.UpdateMode.Always, Size = size,
        };
        cam = new Camera3D
        {
            CullMask = Brush.MaskLayer, Current = true,
            Environment = new Godot.Environment { BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = new Color(0, 0, 0, 0), AmbientLightSource = Godot.Environment.AmbientSource.Disabled, TonemapMode = Godot.Environment.ToneMapper.Linear },
            Attributes = new CameraAttributesPractical { DofBlurFarEnabled = false, DofBlurNearEnabled = false, AutoExposureEnabled = false },
        };
        view.AddChild(cam);
        AddChild(view);
        soft = new SubViewport
        {
            Name = "LampsHerSoft", TransparentBg = false, Disable3D = true, RenderTargetUpdateMode = SubViewport.UpdateMode.Always, Size = size,
        };
        var mat = new ShaderMaterial { Shader = SoftShader };
        mat.SetShaderParameter("her", view.GetTexture());
        mat.SetShaderParameter("texel", new Vector2(1f / size.X, 1f / size.Y));
        mat.SetShaderParameter("px", (float)LampKnock.Down);
        soft.AddChild(new ColorRect { Size = size, Color = Colors.White, Material = mat });
        AddChild(soft);
        RenderingServer.FramePreDraw += Sync;
        if (SurvivorUnchained.Args.Has("lamps-measure"))
        {
            RenderingServer.ViewportSetMeasureRenderTime(view.GetViewportRid(), true);
            RenderingServer.ViewportSetMeasureRenderTime(soft.GetViewportRid(), true);
        }
    }

    /// <summary>The two passes' GPU and CPU time this frame (ms).</summary>
    public (double Gpu, double Cpu) Cost()
    {
        if (view == null || soft == null) return (0, 0);
        return (RenderingServer.ViewportGetMeasuredRenderTimeGpu(view.GetViewportRid()) + RenderingServer.ViewportGetMeasuredRenderTimeGpu(soft.GetViewportRid()),
                RenderingServer.ViewportGetMeasuredRenderTimeCpu(view.GetViewportRid()) + RenderingServer.ViewportGetMeasuredRenderTimeCpu(soft.GetViewportRid()));
    }

    /// <summary>The mask is drawn every Every-th frame (the play camera holds in A and she barely moves: the 10 px
    /// feather covers a few frames' sway); --lamps-her full: every frame (the cost check).</summary>
    public static int Every => SurvivorUnchained.Args.Get("lamps-her") == "full" ? 1 : 4;
    int tick;
    int mf = -1, mn;
    double mg, mc;
    public override void _Process(double delta)
    {
        if (!SurvivorUnchained.Args.Has("lamps-measure") || mf == -2) return;
        // (--lamps-measure: frames 180-299, the two passes' own viewport times on the frames they draw)
        mf++;
        if (mf < 180) return;
        if (drewLast) { var (g, c) = Cost(); mg += g; mc += c; mn++; }
        if (mf == 299)
        {
            GD.Print($"LAMPWIDE her mask: per draw GPU {mg / Math.Max(1, mn):F3} ms, render CPU {mc / Math.Max(1, mn):F3} ms; drawn every {Every} frames: " +
                     $"{mg / 120:F3} ms GPU, {mc / 120:F3} ms CPU a frame (two {LampKnock.W}x{LampKnock.H} passes, {mn} draws in 120 frames)");
            mf = -2;
        }
    }
    bool drewLast;

    public override void _ExitTree()
    {
        RenderingServer.FramePreDraw -= Sync;
        // (the brush's mask keeps her on its layer while it is on)
        if (Brush.On == null)
            foreach (var m in tagged) if (IsInstanceValid(m)) m.Layers &= ~Brush.MaskLayer;
        tagged.Clear();
    }

    void Sync()
    {
        if (cam == null || !IsInsideTree()) return;
        var main = GetViewport().GetCamera3D();
        if (main == null) return;
        drewLast = tick % Every == 1 % Every;   // (the frame after a draw is asked reads its time)
        bool draw = tick++ % Every == 0;
        if (Every > 1 && view != null && soft != null)
        {
            if (!draw) return;
            view.RenderTargetUpdateMode = SubViewport.UpdateMode.Once;
            soft.RenderTargetUpdateMode = SubViewport.UpdateMode.Once;
        }
        // her meshes on the mask's layer (again now and then: a weapon drawn, an outfit changed)
        if (scanT-- <= 0)
        {
            scanT = 30;
            foreach (var n in GetTree().GetNodesInGroup(Brush.HerGroup)) Tag(n);
        }
        cam.GlobalTransform = main.GlobalTransform;
        cam.Projection = main.Projection;
        cam.KeepAspect = main.KeepAspect;
        cam.Fov = main.Fov; cam.Size = main.Size; cam.FrustumOffset = main.FrustumOffset;
        cam.Near = main.Near; cam.Far = main.Far;
        cam.HOffset = main.HOffset; cam.VOffset = main.VOffset;
    }

    void Tag(Node n)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is MeshInstance3D g && (g.Layers & Brush.MaskLayer) == 0) { g.Layers |= Brush.MaskLayer; tagged.Add(g); }
            Tag(c);
        }
    }

    /// <summary>Her alpha grown 10 px with a soft edge: 1 - max over three rings (2.5, 5, 7.5 px; 8 taps each) of her
    /// alpha weighted by 1 - smoothstep(0, 10, ring), and her alpha where the board would be.</summary>
    static Shader? softShader;
    static Shader SoftShader => softShader ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            render_mode unshaded, blend_disabled;
            uniform sampler2D her : filter_linear, repeat_disable;
            uniform vec2 texel;
            uniform float px = 2.0;
            void fragment() {
                float m = texture(her, UV).a;
                for (int r = 1; r <= 3; r++) {
                    float d = 2.5 * float(r);
                    float w = 1.0 - smoothstep(0.0, 10.0, d);
                    float rr = d / px;
                    for (int k = 0; k < 8; k++) {
                        float an = 0.785398 * float(k) + 0.3927 * float(r & 1);
                        m = max(m, texture(her, UV + vec2(cos(an), sin(an)) * rr * texel).a * w);
                    }
                }
                COLOR = vec4(vec3(1.0 - m), 1.0);
            }
            """,
    };
}
