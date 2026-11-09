using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (L1 W2 C5) Effects drawn after the grade (the B6 verdict: "the engine loses the prototype's saturation, 27% against
/// MB5's 55%: draw it after the grade"). The frame's exposure, AgX and color grade (Atmosphere's LUT, its mute and vibrance
/// terms) act on the whole 3D frame, so a spell drawn inside it lands wherever the night's grade puts it, and a calibrated
/// gain (fx_language.json "emit") holds only for the rig it was charted on. Drawn here, a band's color IS its displayed
/// color (the board's hex, MB5), on every rig: a second camera that follows the play camera renders only the render layer
/// <see cref="RenderLayer"/> into a transparent viewport with no tonemap, no grade, no fog and no lights (the camera's cull mask
/// also culls the lights, so it draws no shadows), and that viewport is laid over the 3D frame under the HUD (canvas layer
/// -1). Effects on it are unshaded and drawn without depth (the cel bolt's were already), so nothing is lost by the
/// separate pass. The shader writes its color premultiplied in display space (fx_after: the 3D pass blends in linear, so
/// it hands over linear(srgb(c) x a) / a, which the pass blends to srgb(c) x a), and the layer composites premultiplied.
/// --fx-after off: drawn in the frame as before (B6's emit). Never at --cel off (FxCel.On).
/// --fx-after-occlude off: no depth twins for figures (OccludeFigure), so a spell draws over her as before.
/// </summary>
public partial class FxAfter : CanvasLayer
{
    /// <summary>Render layer 20: drawn only by the after-grade camera (the play cameras' cull masks lose it).</summary>
    public const uint RenderLayer = 1u << 19;
    public static readonly bool On = FxCel.On && SurvivorUnchained.Args.Get("fx-after") != "off";
    static FxAfter? one;

    SubViewport vp = null!;
    Camera3D cam = null!;

    /// <summary>Puts an effect on the after-grade layer (and makes the layer once).</summary>
    public static void Adopt(GeometryInstance3D g)
    {
        g.Layers = RenderLayer;
        if (one != null && IsInstanceValid(one)) return;
        one = new FxAfter { Name = "FxAfter" };
        if (Engine.GetMainLoop() is SceneTree t) t.Root.CallDeferred(Node.MethodName.AddChild, one);
        foreach (var f in figures.ToArray()) if (IsInstanceValid(f)) TwinFigure(f);
    }

    public static readonly bool FigureOn = SurvivorUnchained.Args.Get("fx-after-occlude") != "off";
    const string HoleName = "FxAfterHole";
    static readonly System.Collections.Generic.List<Node3D> figures = new();
    static readonly System.Collections.Generic.List<(MeshInstance3D src, MeshInstance3D twin)> pairs = new();
    static bool hooked;
    static ShaderMaterial? skipMat;

    /// <summary>(L1 W6) A figure's depth twins, skinned meshes included: registers <paramref name="root"/> and, once the
    /// after-grade layer exists (none is made for it), gives each of its meshes (and any laid later) a child twin that
    /// writes depth only, sharing mesh, skin and skeleton so it deforms with the figure; see-through surfaces (hair cards,
    /// lashes, cutout cloth) are skipped so a card never punches its quad out of a spell. --fx-after-occlude off: nothing.</summary>
    public static void OccludeFigure(Node3D root)
    {
        if (!On || !FigureOn) return;
        figures.RemoveAll(f => !IsInstanceValid(f));
        if (!figures.Contains(root)) figures.Add(root);
        if (!hooked && Engine.GetMainLoop() is SceneTree t)
        {
            hooked = true;
            t.NodeAdded += OnNodeAdded;
        }
        if (one != null && IsInstanceValid(one)) TwinFigure(root);
    }

    static void OnNodeAdded(Node n)
    {
        if (n is not MeshInstance3D mi || one == null || !IsInstanceValid(one) || mi.Name == HoleName) return;
        foreach (var f in figures)
            if (IsInstanceValid(f) && f.IsAncestorOf(mi)) { Callable.From(() => TwinMesh(mi)).CallDeferred(); return; }
    }

    static int TwinFigure(Node3D root)
    {
        int n = 0;
        foreach (var node in root.FindChildren("*", "MeshInstance3D", true, false))
            if (node is MeshInstance3D mi && TwinMesh(mi)) n++;
        GD.Print($"fxafter: twins {n} under {root.Name}");
        return n;
    }

    static bool SeeThrough(MeshInstance3D mi, int i)
    {
        var m = mi.GetActiveMaterial(i);
        if (m is BaseMaterial3D b) return b.Transparency != BaseMaterial3D.TransparencyEnum.Disabled;
        if (m is ShaderMaterial sm) return sm.Shader != null && sm.Shader.Code.Contains("ALPHA");
        return false;
    }

    static bool TwinMesh(MeshInstance3D mi)
    {
        if (!IsInstanceValid(mi) || mi.Mesh == null || mi.Name == HoleName || (mi.Layers & RenderLayer) != 0) return false;
        foreach (var c in mi.GetChildren()) if (c.Name == HoleName) return false;
        hole ??= MakeHole();
        skipMat ??= new ShaderMaterial { Shader = new Shader { Code = "shader_type spatial; void fragment() { discard; }" } };
        var twin = new MeshInstance3D { Mesh = mi.Mesh, Layers = RenderLayer, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Name = HoleName };
        mi.AddChild(twin);
        if (mi.Skin != null) twin.Skin = mi.Skin;
        if (!mi.Skeleton.IsEmpty)
        {
            // (the twin is mi's child, so a relative path starts one step further up; absolute ones stay)
            var sp = mi.Skeleton.IsAbsolute() ? mi.Skeleton : new NodePath("../" + mi.Skeleton);
            if (twin.GetNodeOrNull(sp) is Skeleton3D) twin.Skeleton = sp;
        }
        for (int i = 0; i < mi.Mesh.GetSurfaceCount(); i++)
            twin.SetSurfaceOverrideMaterial(i, SeeThrough(mi, i) ? skipMat : hole);
        pairs.Add((mi, twin));
        return true;
    }

    static ShaderMaterial MakeHole() => new()
    {
        Shader = new Shader { Code = "shader_type spatial; render_mode unshaded, blend_mix, depth_draw_always, cull_back, shadows_disabled, fog_disabled; void fragment() { ALBEDO = vec3(0.0); ALPHA = 0.0; }" },
        RenderPriority = (int)Material.RenderPriorityMin,
    };

    static void FollowFigures()
    {
        for (int k = pairs.Count - 1; k >= 0; k--)
        {
            var (src, twin) = pairs[k];
            if (!IsInstanceValid(src) || !IsInstanceValid(twin)) { pairs.RemoveAt(k); continue; }
            if (twin.Mesh != src.Mesh) twin.Mesh = src.Mesh;
            if (src.Mesh == null) continue;
            int bs = src.GetBlendShapeCount();
            for (int b = 0; b < bs; b++) twin.SetBlendShapeValue(b, src.GetBlendShapeValue(b));
        }
    }

    static ShaderMaterial? hole;

    /// <summary>(W2 C5b) What stands in front of an after-grade effect, as depth only: every mesh under <paramref name="root"/>
    /// (but <paramref name="skip"/>) gets a twin on the after-grade layer that writes depth and no color, drawn before the
    /// effects (render priority -128), so a camp fire's flame drawn after the grade still sits behind its own front logs and
    /// stones and fades into them (fx_cel_flame's soft edge reads this layer's depth). Static meshes only (the twin shares
    /// the mesh and follows its parent).</summary>
    public static void Occlude(Node root, Node? skip = null)
    {
        hole ??= MakeHole();
        foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D mi || mi.Mesh == null || (mi.Layers & RenderLayer) != 0) continue;
            if (skip != null && (n == skip || skip.IsAncestorOf(n))) continue;
            mi.AddChild(new MeshInstance3D { Mesh = mi.Mesh, Layers = RenderLayer, MaterialOverride = hole, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Name = "FxAfterHole" });
        }
    }

    public override void _Ready()
    {
        Layer = -1;
        ProcessPriority = 10000;
        vp = new SubViewport
        {
            TransparentBg = true, RenderTargetUpdateMode = SubViewport.UpdateMode.Always, HandleInputLocally = false,
            GuiDisableInput = true, PositionalShadowAtlasSize = 0, Msaa3D = Viewport.Msaa.Disabled,
        };
        cam = new Camera3D
        {
            CullMask = RenderLayer, Current = true,
            Environment = new Godot.Environment
            {
                BackgroundMode = Godot.Environment.BGMode.ClearColor, TonemapMode = Godot.Environment.ToneMapper.Linear,
                AmbientLightSource = Godot.Environment.AmbientSource.Disabled, ReflectedLightSource = Godot.Environment.ReflectionSource.Disabled,
            },
        };
        vp.AddChild(cam);
        AddChild(vp);
        var rect = new TextureRect
        {
            Texture = vp.GetTexture(), MouseFilter = Control.MouseFilterEnum.Ignore,
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.PremultAlpha },
        };
        rect.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        AddChild(rect);
    }

    public override void _Process(double delta)
    {
        var root = GetTree().Root;
        if (root.GetCamera3D() is not { } main) { vp.RenderTargetUpdateMode = SubViewport.UpdateMode.Disabled; return; }
        vp.RenderTargetUpdateMode = SubViewport.UpdateMode.Always;
        FollowFigures();
        if (vp.Size != root.Size) vp.Size = root.Size;
        main.CullMask &= ~RenderLayer;
        cam.GlobalTransform = main.GlobalTransform;
        cam.Projection = main.Projection;
        cam.Fov = main.Fov; cam.Size = main.Size; cam.FrustumOffset = main.FrustumOffset;
        cam.Near = main.Near; cam.Far = main.Far; cam.KeepAspect = main.KeepAspect;
        cam.HOffset = main.HOffset; cam.VOffset = main.VOffset;
    }
}
