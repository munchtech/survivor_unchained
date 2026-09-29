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

    public sealed record Look(float Wind, Color? LeafA, Color? LeafB, float LeafAmount, float Moss)
    {
        /// <summary>A piece as it comes: still, its own colours.</summary>
        public static readonly Look Plain = new(0, null, null, 0, 0);
    }

    static Shader? solid, twoSided;
    static readonly Dictionary<string, ShaderMaterial> cache = new();

    /// <summary>A kit material as the web game shades it.</summary>
    /// <param name="foot">Darker toward the piece's foot (the village kit
    /// and the game's own models).</param>
    public static Material For(Material src, Look look, bool foot = false)
    {
        if (src is not StandardMaterial3D s) return src;
        var foliage = Foliage.IsMatch(s.ResourceName);
        var key = $"{s.GetInstanceId()}|{look}|{foot}";
        if (cache.TryGetValue(key, out var m)) return m;
        solid ??= GD.Load<Shader>("res://shaders/kit.gdshader");
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
            if (re.IsMatch(s.ResourceName)) { m.SetShaderParameter("weather_sat", sat); m.SetShaderParameter("weather_tint", tint); break; }
        m.SetShaderParameter("wind", foliage ? look.Wind : look.Wind * 0.3f);
        if (foliage && look.LeafA is Color a && look.LeafB is Color b)
        {
            m.SetShaderParameter("recolor_a", new Vector4(a.R, a.G, a.B, look.LeafAmount));
            m.SetShaderParameter("recolor_b", new Vector3(b.R, b.G, b.B));
        }
        m.SetShaderParameter("moss", foliage ? 0f : look.Moss);
        m.SetShaderParameter("jitter", foliage ? 0.14f : 0.08f);
        m.SetShaderParameter("foot", foot);
        cache[key] = m;
        return m;
    }
}
