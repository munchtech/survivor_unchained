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
        public float R = 3, Str = 0.75f, Tex = 0.12f, Len = 15, Wid = 4, Sharp = 8, Hard = 8, Ang = 35, Feather = 1.5f, Dbg, HdrA = 4, HdrB = 12;
        public bool Time, Vfx = true;

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
                if (k == "hdr" && v.Split('/') is [var ha, var hb])
                {
                    if (float.TryParse(ha, System.Globalization.NumberStyles.Float, inv, out float a) && float.TryParse(hb, System.Globalization.NumberStyles.Float, inv, out float b2) && b2 > a) { t.HdrA = a; t.HdrB = b2; }
                    else GD.PushWarning($"--brush: bad hdr '{v}' (hdr=A/B, A < B)");
                    continue;
                }
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
                    case "hdr": t.HdrA = f; break;
                    case "hdrb": t.HdrB = Mathf.Max(f, t.HdrA + 0.01f); break;
                    case "time": t.Time = f != 0; break;
                    case "vfx": t.Vfx = f != 0; break;
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
        if (effect.Spec.Vfx) { GetTree().NodeAdded += Added; Scan(GetTree().Root); }
        if (effect.Spec.Time) RenderingServer.ViewportSetMeasureRenderTime(mask.GetViewportRid(), true);
    }

    public override void _ExitTree()
    {
        RenderingServer.FramePreDraw -= Sync;
        if (effect.Spec.Vfx) GetTree().NodeAdded -= Added;
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
        // Fire, sparks and spells stay pure: new ones checked a frame after they arrive (their
        // materials set), and the whole tree again now and then for materials swapped later.
        while (added.Count > 0) { var id = added.Dequeue(); if (InstanceFromId(id) is GeometryInstance3D g) Vfx(g); }
        if (effect.Spec.Vfx && ++scanT % 120 == 0) Scan(GetTree().Root);
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

    readonly System.Collections.Generic.Queue<ulong> added = new();
    ulong scanT;

    void Added(Node n) { if (n is GeometryInstance3D) added.Enqueue(n.GetInstanceId()); }

    static void Scan(Node n)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is GeometryInstance3D g) Vfx(g);
            Scan(c);
        }
    }

    /// <summary>VFX on the mask layer too, so they come out unfiltered: particles, and meshes drawn
    /// additive or unshaded-and-transparent (flames, embers, sparks, flare, spells, lamp glass), except
    /// the wide translucent sheets (mist, the distant crowd, canopy shade) that would unmask what's behind.</summary>
    static void Vfx(GeometryInstance3D g)
    {
        if ((g.Layers & MaskLayer) != 0) return;
        bool on = g is GpuParticles3D or CpuParticles3D || Bright(g.MaterialOverride) || Bright(g.MaterialOverlay);
        if (!on && g is MeshInstance3D mi && mi.Mesh is { } mesh)
            for (int i = 0, n = mesh.GetSurfaceCount(); i < n && !on; i++)
                on = Bright(mi.GetSurfaceOverrideMaterial(i)) || Bright(mesh.SurfaceGetMaterial(i));
        if (!on && g is MultiMeshInstance3D mm && mm.Multimesh?.Mesh is { } m2)
            for (int i = 0, n = m2.GetSurfaceCount(); i < n && !on; i++) on = Bright(m2.SurfaceGetMaterial(i));
        if (on) g.Layers |= MaskLayer;
    }

    static readonly string[] Sheets = { "canopy", "crowd_blob", "mist_sheet", "river_mist", "unlit" };

    static bool Bright(Material? m)
    {
        switch (m)
        {
            case BaseMaterial3D b:
                return b.BlendMode == BaseMaterial3D.BlendModeEnum.Add
                    || (b.ShadingMode == BaseMaterial3D.ShadingModeEnum.Unshaded && b.Transparency != BaseMaterial3D.TransparencyEnum.Disabled);
            case ShaderMaterial sm when sm.Shader is { } sh:
                foreach (var x in Sheets) if (sh.ResourcePath.Contains(x)) return false;
                var code = sh.Code;
                int r = code.IndexOf("render_mode", System.StringComparison.Ordinal);
                if (r < 0) return false;
                int e = code.IndexOf(';', r);
                var modes = e > r ? code[r..e] : "";
                return (modes.Contains("unshaded") || modes.Contains("blend_add")) && !modes.Contains("blend_mul");
        }
        return false;
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
