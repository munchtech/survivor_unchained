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
    }

    static ShaderMaterial? hole;

    /// <summary>(W2 C5b) What stands in front of an after-grade effect, as depth only: every mesh under <paramref name="root"/>
    /// (but <paramref name="skip"/>) gets a twin on the after-grade layer that writes depth and no color, drawn before the
    /// effects (render priority -128), so a camp fire's flame drawn after the grade still sits behind its own front logs and
    /// stones and fades into them (fx_cel_flame's soft edge reads this layer's depth). Static meshes only (the twin shares
    /// the mesh and follows its parent).</summary>
    public static void Occlude(Node root, Node? skip = null)
    {
        hole ??= new ShaderMaterial
        {
            Shader = new Shader { Code = "shader_type spatial; render_mode unshaded, blend_mix, depth_draw_always, cull_back, shadows_disabled, fog_disabled; void fragment() { ALBEDO = vec3(0.0); ALPHA = 0.0; }" },
            RenderPriority = (int)Material.RenderPriorityMin,
        };
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
        if (vp.Size != root.Size) vp.Size = root.Size;
        main.CullMask &= ~RenderLayer;
        cam.GlobalTransform = main.GlobalTransform;
        cam.Projection = main.Projection;
        cam.Fov = main.Fov; cam.Size = main.Size; cam.FrustumOffset = main.FrustumOffset;
        cam.Near = main.Near; cam.Far = main.Far; cam.KeepAspect = main.KeepAspect;
        cam.HOffset = main.HOffset; cam.VOffset = main.VOffset;
    }
}
