using System.Collections.Generic;
using System.Text.RegularExpressions;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The kits' materials as the web game weathers them (src/render/env.ts's
/// WEATHER table) and colours its flora (the kind's leaves and moss): each
/// imported StandardMaterial3D becomes shaders/kit.gdshader with the same
/// textures, cached per material and look.
/// </summary>
public static class KitLook
{
    /// Material name pattern: saturation kept, colour multiply.
    static readonly (Regex Re, float Sat, Vector3 Tint)[] Weather =
    {
        (new("RoundTiles"), 0.42f, new(0.74f, 0.7f, 0.68f)),
        (new("Plaster"), 0.6f, new(0.84f, 0.82f, 0.78f)),
        (new("WoodTrim|Wood"), 0.7f, new(0.72f, 0.7f, 0.68f)),
        (new("Brick|Rock|Stone"), 0.7f, new(0.84f, 0.83f, 0.8f)),
        (new("Leaf|Leaves|Grass|Clover|Fern|Plant|Bush"), 0.7f, new(0.8f, 0.84f, 0.76f)),
        (new("Bark"), 0.75f, new(0.8f, 0.78f, 0.76f)),
        (new("."), 0.82f, new(0.88f, 0.87f, 0.85f)),
    };
    static readonly Regex Foliage = new("Leaf|Leaves|Flower|Petal|Grass|Clover|Fern|Plant|Bush", RegexOptions.IgnoreCase);

    /// <param name="Shade">How much light the leaves give back: under an ember
    /// arena's night they stand as dark crowns round the fight, not lit lawns.</param>
    public sealed record Look(float Wind, Color? LeafA, Color? LeafB, float LeafAmount, float Moss, float Shade = 1)
    {
        /// <summary>A piece as it comes: still, its own colours.</summary>
        public static readonly Look Plain = new(0, null, null, 0, 0);
    }

    static Shader? solid, twoSided, solidRim, twoSidedRim;
    static readonly Dictionary<string, ShaderMaterial> cache = new();

    /// <summary>--see-debug (a developer's switch): the kit's pieces tinted green where whole and
    /// red on the window's rim, and what else stands in the window listed (Dump), so a piece in
    /// the window that is neither can be found.</summary>
    public static readonly bool SeeDebug = SurvivorUnchained.Args.Has("see-debug");
    // (whole: each copy its own tint, so pieces can be told apart; rim: opaque, coloured by how much
    // is kept, blue none to red all)
    const string Whole = "ALBEDO = col;",
        WholeDebug = "ALBEDO = col * (0.45 + 0.55 * vec3(fract(v_jit * 7.0), fract(v_jit * 13.0), fract(v_jit * 29.0)));",
        RimDebug = "ALBEDO = FRONT_FACING ? mix(vec3(0.0, 0.25, 1.0), vec3(1.0, 0.1, 0.0), kept) : vec3(0.1, 1.0, 0.2); ALPHA = 1.0;";

    /// <summary>--see-fix back,screen (a developer's switch while the window's pale wedge is
    /// fixed; shaders/kit.gdshader SEE_BACK, SEE_SCREEN): faces seen from behind cut whole
    /// inside the window, with no rim; the feather held to its width on the screen where
    /// how far a piece is opened varies across it. (--see-debug draws the rim's back faces green.)</summary>
    static readonly string SeeFix = SurvivorUnchained.Args.Get("see-fix") ?? "";

    static string Fixed(string code) => code.Replace("shader_type spatial;", "shader_type spatial;"
        + (SeeFix.Contains("back") ? "\n#define SEE_BACK" : "") + (SeeFix.Contains("screen") ? "\n#define SEE_SCREEN" : "")
        + (SeeFix.Contains("underao") ? "\n#define SEE_UNDER" : "") + (SeeFix.Contains("undercut") ? "\n#define SEE_UNDERCUT" : "") + (SeeFix.Contains("norim") ? "\n#define SEE_NORIM" : "")
        + (SeeFix.Contains("narrow") ? "\n#define SEE_NARROW" : ""));

    /// <summary>The see-through window's feathered rim (shaders/kit.gdshader): the same code
    /// with REVEAL defined, blended, drawn as each kit material's next pass.</summary>
    static Shader Rim(Shader of) => new()
    {
        Code = of.Code.Replace("shader_type spatial;", "shader_type spatial;\n#define REVEAL")
            .Replace("render_mode ", "render_mode blend_mix, depth_draw_never, ")
            .Replace(WholeDebug, RimDebug),
    };

    /// <summary>(--see-debug) Every mesh standing between the survivor's chest and the camera,
    /// within the window's reach of that line, with its materials: printed once.</summary>
    public static void Dump(Node root, Vector3 her, Vector3 cam)
    {
        var line = cam - her;
        float len = line.Length();
        var dir = line / len;
        foreach (var n in root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            if (n is not GeometryInstance3D g || !g.IsVisibleInTree()) continue;
            var box = g.GlobalTransform * g.GetAabb();
            var c = box.GetCenter();
            float t = Mathf.Clamp((c - her).Dot(dir), 0, len);
            float off = (her + dir * t).DistanceTo(c) - box.Size.Length() * 0.5f;
            if (off > 2.6f || (c - her).Dot(dir) < -box.Size.Length() * 0.5f) continue;
            var mats = new List<string>();
            if (g is MeshInstance3D mi && mi.Mesh != null)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    mats.Add(Describe(mi.GetActiveMaterial(s)));
            else if (g is MultiMeshInstance3D mm && mm.Multimesh?.Mesh is { } mesh)
                for (int s = 0; s < mesh.GetSurfaceCount(); s++)
                    mats.Add(Describe(g.MaterialOverride ?? mesh.SurfaceGetMaterial(s)) + $" x{mm.Multimesh.InstanceCount}");
            GD.Print($"see-debug: {g.GetPath()} [{g.GetClass()}] at {c} size {box.Size} off-line {off:0.0} m along {t:0.0} m: {string.Join(" | ", mats)}");
        }
    }

    static string Describe(Material? m) => m switch
    {
        null => "none",
        ShaderMaterial sm => $"shader {sm.Shader?.ResourcePath}{(sm.Shader == solid || sm.Shader == twoSided ? " (kit)" : "")} '{sm.ResourceName}'{(sm.NextPass != null ? " +next" : "")}",
        BaseMaterial3D b => $"{b.GetClass()} '{b.ResourceName}' transparency {b.Transparency} cull {b.CullMode}",
        _ => m.GetClass(),
    };

    /// <summary>A kit material as the web game shades it.</summary>
    /// <param name="foot">Darker toward the piece's foot (the village kit
    /// and the game's own models).</param>
    public static Material For(Material src, Look look, bool foot = false)
    {
        if (src is not StandardMaterial3D s) return src;
        var foliage = Foliage.IsMatch(s.ResourceName);
        var key = $"{s.GetInstanceId()}|{look}|{foot}";
        if (cache.TryGetValue(key, out var m)) return m;
        solid ??= SeeDebug || SeeFix != "" ? new Shader { Code = Fixed(GD.Load<Shader>("res://shaders/kit.gdshader").Code).Replace(Whole, SeeDebug ? WholeDebug : Whole) } : GD.Load<Shader>("res://shaders/kit.gdshader");
        twoSided ??= new Shader { Code = solid.Code.Replace("render_mode diffuse_burley", "render_mode cull_disabled, diffuse_burley") };
        m = new ShaderMaterial { Shader = foliage || s.CullMode == BaseMaterial3D.CullModeEnum.Disabled ? twoSided : solid };
        m.SetShaderParameter("albedo_tex", s.AlbedoTexture);
        m.SetShaderParameter("albedo_color", s.AlbedoColor);
        m.SetShaderParameter("use_vcolor", s.VertexColorUseAsAlbedo);
        if (s.NormalEnabled && s.NormalTexture != null) { m.SetShaderParameter("use_normal", true); m.SetShaderParameter("normal_tex", s.NormalTexture); }
        m.SetShaderParameter("roughness", Mathf.Max(s.Roughness, 0.6f));
        bool cut = foliage || s.Transparency is BaseMaterial3D.TransparencyEnum.AlphaScissor or BaseMaterial3D.TransparencyEnum.Alpha;
        m.SetShaderParameter("alpha_scissor", cut ? Mathf.Max(s.AlphaScissorThreshold, 0.5f) : 0f);
        foreach (var (re, sat, tint) in Weather)
            if (re.IsMatch(s.ResourceName)) { m.SetShaderParameter("weather_sat", sat); m.SetShaderParameter("weather_tint", foliage ? tint * look.Shade : tint); break; }
        m.SetShaderParameter("wind", foliage ? look.Wind : look.Wind * 0.3f);
        if (foliage && look.LeafA is Color a && look.LeafB is Color b)
        {
            m.SetShaderParameter("recolor_a", new Vector4(a.R, a.G, a.B, look.LeafAmount));
            m.SetShaderParameter("recolor_b", new Vector3(b.R, b.G, b.B));
        }
        m.SetShaderParameter("moss", foliage ? 0f : look.Moss);
        m.SetShaderParameter("jitter", foliage ? 0.14f : 0.08f);
        m.SetShaderParameter("foot", foot);
        m.SetShaderParameter("leaves", foliage);
        // The window's rim, drawn again over what the piece's own pass left open: every
        // parameter the same, so the rim is the piece itself, fading.
        solidRim ??= Rim(solid);
        twoSidedRim ??= Rim(twoSided);
        var rim = new ShaderMaterial { Shader = m.Shader == solid ? solidRim : twoSidedRim };
        foreach (var u in m.Shader.GetShaderUniformList())
        {
            var name = (string)u.AsGodotDictionary()["name"];
            rim.SetShaderParameter(name, m.GetShaderParameter(name));
        }
        m.NextPass = rim;
        cache[key] = m;
        return m;
    }
}
