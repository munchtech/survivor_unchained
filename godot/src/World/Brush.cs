using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// --brush k=v,...: the painterly post-filter (style trial, off by default). Surfaces read as painted: an
/// anisotropic Kuwahara that flattens texture into patches following the forms, and a faint stroke texture
/// along the flow, world-anchored so it doesn't slide when the camera follows her. Her own pixels are never
/// filtered: her meshes carry MaskLayer too, and a mask viewport sharing the world draws only that layer,
/// unshaded, with the main camera's view each frame; its alpha is her coverage.
/// Keys: r (Kuwahara radius, px at 1080p), str (blend 0-1), tex (stroke texture), len (stroke length px),
/// wid (stroke width px), sharp (sector sharpness q), hard (sector hardness), ang (stroke angle where the
/// image has no flow, degrees), feather (her mask's dilation px), dbg (1 mask, 2 world, 3 strokes, 4 Kuwahara),
/// time (1: print the filter's GPU time).
/// </summary>
public partial class Brush : Node
{
    /// <summary>The filter's settings, or null without the flag (then nothing is made).</summary>
    public static readonly Spec? On = Spec.Parse(SurvivorUnchained.Args.Get("brush") is string b ? (b == "1" ? "" : b) : null);
    /// <summary>The layer her meshes carry as well while the filter is on (20; the mask viewport's only layer).</summary>
    public const uint MaskLayer = 1u << 19;
    public const string HerGroup = "player_view";

    public sealed class Spec
    {
        public float R = 3, Str = 0.75f, Tex = 0.2f, Len = 10, Wid = 3, Sharp = 8, Hard = 8, Ang = 35, Feather = 1.5f, Dbg;
        public bool Time;

        public static Spec? Parse(string? spec)
        {
            if (spec == null) return null;
            var t = new Spec();
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            foreach (var part in spec.Split(',', System.StringSplitOptions.RemoveEmptyEntries | System.StringSplitOptions.TrimEntries))
            {
                int eq = part.IndexOf('=');
                if (eq < 0) { GD.PushWarning($"--brush: no value in '{part}'"); continue; }
                string k = part[..eq].Trim().ToLowerInvariant(), v = part[(eq + 1)..].Trim();
                if (!float.TryParse(v, System.Globalization.NumberStyles.Float, inv, out float f)) { GD.PushWarning($"--brush: bad number '{part}'"); continue; }
                switch (k)
                {
                    case "r": t.R = Mathf.Clamp(f, 1, 8); break;
                    case "str": t.Str = Mathf.Clamp(f, 0, 1); break;
                    case "tex": t.Tex = f; break;
                    case "len": t.Len = Mathf.Clamp(f, 1, 32); break;
                    case "wid": t.Wid = Mathf.Max(f, 0.5f); break;
                    case "sharp": t.Sharp = Mathf.Clamp(f, 1, 16); break;
                    case "hard": t.Hard = Mathf.Max(f, 0.01f); break;
                    case "ang": t.Ang = f; break;
                    case "feather": t.Feather = Mathf.Clamp(f, 0, 4); break;
                    case "dbg": t.Dbg = f; break;
                    case "time": t.Time = f != 0; break;
                    default: GD.PushWarning($"--brush: unknown key '{k}'"); break;
                }
            }
            return t;
        }
    }

    readonly BrushEffect effect;
    readonly Compositor compositor;
    SubViewport? mask;
    Camera3D? maskCam;
    Camera3D? on;
    ulong frames;
    double gpuSum, maskSum; int gpuN;

    public Brush(Spec spec)
    {
        Name = "Brush";
        effect = new BrushEffect { Spec = spec };
        compositor = new Compositor { CompositorEffects = new Godot.Collections.Array<CompositorEffect> { effect } };
    }

    public override void _Ready()
    {
        mask = new SubViewport
        {
            Name = "BrushMask", TransparentBg = true, Msaa3D = Viewport.Msaa.Disabled, UseTaa = false,
            ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled, Scaling3DMode = Viewport.Scaling3DModeEnum.Bilinear, Scaling3DScale = 1,
            PositionalShadowAtlasSize = 0, UseOcclusionCulling = false, DebugDraw = Viewport.DebugDrawEnum.Unshaded,
            RenderTargetUpdateMode = SubViewport.UpdateMode.Always, Size = (Vector2I)GetViewport().GetVisibleRect().Size,
        };
        maskCam = new Camera3D
        {
            CullMask = MaskLayer, Current = true,
            Environment = new Godot.Environment { BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = new Color(0, 0, 0, 0), BackgroundEnergyMultiplier = 0, AmbientLightSource = Godot.Environment.AmbientSource.Disabled, TonemapMode = Godot.Environment.ToneMapper.Linear },
            Attributes = new CameraAttributesPractical { DofBlurFarEnabled = false, DofBlurNearEnabled = false, AutoExposureEnabled = false },
        };
        mask.AddChild(maskCam);
        AddChild(mask);
        RenderingServer.FramePreDraw += Sync;
        if (effect.Spec.Time) RenderingServer.ViewportSetMeasureRenderTime(mask.GetViewportRid(), true);
    }

    public override void _ExitTree()
    {
        RenderingServer.FramePreDraw -= Sync;
        if (on != null && IsInstanceValid(on) && on.Compositor == compositor) on.Compositor = null;
    }

    /// <summary>Before the viewports draw: her meshes tagged, the mask camera on the main camera's view,
    /// the filter on whichever camera is current.</summary>
    void Sync()
    {
        if (mask == null || maskCam == null) return;
        var cam = GetViewport().GetCamera3D();
        if (cam != on)
        {
            if (on != null && IsInstanceValid(on) && on.Compositor == compositor) on.Compositor = null;
            on = cam;
            if (cam != null) cam.Compositor = compositor;
        }
        if (cam == null) return;
        foreach (var n in GetTree().GetNodesInGroup(HerGroup)) Tag(n);
        maskCam.GlobalTransform = cam.GlobalTransform;
        maskCam.Projection = cam.Projection;
        maskCam.KeepAspect = cam.KeepAspect;
        maskCam.Fov = cam.Fov; maskCam.Size = cam.Size; maskCam.FrustumOffset = cam.FrustumOffset;
        maskCam.Near = cam.Near; maskCam.Far = cam.Far;
        maskCam.HOffset = cam.HOffset; maskCam.VOffset = cam.VOffset;
        var want = effect.TargetSize.X > 0 ? effect.TargetSize : (Vector2I)GetViewport().GetVisibleRect().Size;
        if (mask.Size != want) mask.Size = want;
        var rid = RenderingServer.TextureGetRdTexture(mask.GetTexture().GetRid());
        effect.Mask = rid.IsValid ? rid : null;
        if (effect.Spec.Time && ++frames > 60)
        {
            if (effect.GpuMs >= 0) { gpuSum += effect.GpuMs; maskSum += RenderingServer.ViewportGetMeasuredRenderTimeGpu(mask.GetViewportRid()); gpuN++; }
            if (gpuN == 120)
            {
                GD.Print($"BRUSH gpu filter {gpuSum / gpuN:0.000} ms, mask view {maskSum / gpuN:0.000} ms (mean of {gpuN} frames, {effect.TargetSize})");
                gpuSum = maskSum = 0; gpuN = 0;
            }
        }
    }

    static void Tag(Node n)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is MeshInstance3D g && (g.Layers & MaskLayer) == 0) g.Layers |= MaskLayer;
            Tag(c);
        }
    }
}
