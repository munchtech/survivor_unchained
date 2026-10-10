using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// How her hair's cards, brows and lashes are drawn, to choose the smoothing
/// (--hair-draw, a developer's switch for now). Godot's hashed alpha (today:
/// "hash") keeps one threshold for each point of the surface: TAA blurs it,
/// FSR 2 cannot average it, and her hair crawled under FSR 2 at the Look.
/// Blended, a strand is drawn to its own cover in every frame, soft and still,
/// with nothing left for the smoothing to average: "blend" draws its solid
/// parts in Godot's depth prepass and blends the whole over them; "two" draws
/// its solid parts opaque (so their depth, motion and ambient occlusion are
/// written) and the whole again over them, blended. Lashes (and brow cards),
/// which alpha to coverage cuts under MSAA, are blended to their paint's own
/// alpha in both (shaders/heroine_cards_blend.gdshader).
/// </summary>
public static class HairDraw
{
    public static readonly string Mode = SurvivorUnchained.Args.Get("hair-draw") ?? "hash";

    /// <summary>Blended (either way).</summary>
    public static bool Blended => Mode is "blend" or "two";

    static Shader? blend, core, over, cards;

    /// <summary>Her hair cards' material (not the cap, fine hairs or tie), its
    /// passes unset; null when drawn as today. Blended hair is drawn after the
    /// cap it covers (priority 0) and before the fine hairs over it (2).</summary>
    public static ShaderMaterial? Hair()
    {
        switch (Mode)
        {
            case "blend":
                blend ??= GD.Load<Shader>("res://shaders/heroine_hair_blend.gdshader");
                return new ShaderMaterial { Shader = blend, RenderPriority = 1 };
            case "two":
                core ??= GD.Load<Shader>("res://shaders/heroine_hair_core.gdshader");
                over ??= GD.Load<Shader>("res://shaders/heroine_hair_over.gdshader");
                return new ShaderMaterial { Shader = core, NextPass = new ShaderMaterial { Shader = over, RenderPriority = 1 } };
            default:
                return null;
        }
    }

    /// <summary>Whether a shader is one of these ways of drawing her hair.</summary>
    public static bool IsHair(Shader? s) => s != null && (s == blend || s == core || s == over);

    /// <summary>A material and each pass after it (each takes the same parameters).</summary>
    public static IEnumerable<ShaderMaterial> Passes(ShaderMaterial m)
    {
        for (var p = m; p != null; p = p.NextPass as ShaderMaterial) yield return p;
    }

    /// <summary>Brows or lashes blended to their paint's alpha; null when drawn as today.</summary>
    public static ShaderMaterial? Cards(StandardMaterial3D m)
    {
        if (!Blended) return null;
        cards ??= GD.Load<Shader>("res://shaders/heroine_cards_blend.gdshader");
        var c = new ShaderMaterial { Shader = cards, ResourceName = m.ResourceName };
        c.SetShaderParameter("albedo_tex", m.AlbedoTexture);
        c.SetShaderParameter("albedo_color", m.AlbedoColor);
        c.SetShaderParameter("skin_lit", m.ResourceName == "lashes" ? 1f : 0f);
        return c;
    }
}
