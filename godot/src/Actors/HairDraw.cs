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

    /// <summary>--hair-erase KEEP: each blended pass of her hair, cap, fine
    /// hairs, lashes and brows is followed by an eraser (shaders/heroine_hair_erase
    /// and heroine_cards_erase: the colour multiplied by white, the alpha by KEEP),
    /// drawn after all of them. Godot hands FSR 2 the colour's alpha as its
    /// reactive mask, so blended hair showed as the near-raw jittered frame and
    /// moved frame to frame at the Look; erased (0), FSR 2 accumulates it as it
    /// does her skin. Negative (the default): no eraser.</summary>
    public static readonly float EraseKeep = SurvivorUnchained.Args.Num("hair-erase", -1f);

    /// <summary>--hair-core-cut C: with "two", the cover a strand needs to be drawn
    /// solid (its depth and motion written); 0.9 by default.</summary>
    public static readonly float CoreCut = SurvivorUnchained.Args.Num("hair-core-cut", 0.9f);

    /// <summary>--hair-erase-from F: with "two", the cards' eraser works fully where
    /// the strands cover F or more (the core's cut: only what wrote her hair's own
    /// motion is accumulated), easing out over the 0.25 below it (so the mask can't
    /// flip with the jitter at the core's edge); the thin fringe stays reactive. 0 by default.</summary>
    public static readonly float EraseFrom = SurvivorUnchained.Args.Num("hair-erase-from", 0f);

    /// <summary>--hair-bias B: a bias on the strands' and lashes' mip level
    /// (0.5 cancels the smoothing's -0.5 on strands thinner than a pixel). 0 by default.</summary>
    public static readonly float Bias = SurvivorUnchained.Args.Num("hair-bias", 0f);

    static Shader? blend, core, over, cards, hairErase, cardsErase;

    /// <summary>The material with the hair eraser added as its last pass (when
    /// --hair-erase is given): it takes the hair's parameters, so it swings with it.</summary>
    public static ShaderMaterial WithErase(ShaderMaterial m)
    {
        bool cards = m.Shader != null && m.Shader == core;
        if (EraseKeep >= 0f)
        {
            hairErase ??= GD.Load<Shader>("res://shaders/heroine_hair_erase.gdshader");
            var e = new ShaderMaterial { Shader = hairErase, RenderPriority = 3 };
            e.SetShaderParameter("keep", EraseKeep);
            e.SetShaderParameter("erase_from", cards ? EraseFrom : 0f);
            Last(m).NextPass = e;
        }
        foreach (var p in Passes(m))
        {
            p.SetShaderParameter("strand_bias", Bias);
            if (cards) p.SetShaderParameter("core_cut", CoreCut);
        }
        return m;
    }

    static ShaderMaterial Last(ShaderMaterial m)
    {
        var p = m;
        while (p.NextPass is ShaderMaterial n) p = n;
        return p;
    }

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

    /// <summary>A pass erasing FSR 2's reactive mask under what was drawn before it on
    /// the same surface (lashes, brow cards, her brows and face paint); null without
    /// --hair-erase or blended hair.</summary>
    public static ShaderMaterial? Eraser()
    {
        if (EraseKeep < 0f || !Blended) return null;
        cardsErase ??= GD.Load<Shader>("res://shaders/heroine_cards_erase.gdshader");
        var e = new ShaderMaterial { Shader = cardsErase, RenderPriority = 3 };
        e.SetShaderParameter("keep", EraseKeep);
        return e;
    }

    /// <summary>Brows or lashes blended to their paint's alpha; null when drawn as today.</summary>
    public static ShaderMaterial? Cards(StandardMaterial3D m)
    {
        if (!Blended) return null;
        cards ??= GD.Load<Shader>("res://shaders/heroine_cards_blend.gdshader");
        var c = new ShaderMaterial { Shader = cards, ResourceName = m.ResourceName };
        c.SetShaderParameter("albedo_tex", m.AlbedoTexture);
        c.SetShaderParameter("albedo_color", m.AlbedoColor);
        c.SetShaderParameter("lash_bias", Bias);
        if (EraseKeep >= 0f)
        {
            c.NextPass = Eraser();
        }
        return c;
    }
}
