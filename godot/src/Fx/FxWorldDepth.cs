using System;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (L1 lead 7, B) The world's depth behind the after-grade light. FxAfter draws its effects with a second camera into its
/// own viewport, so a tree's canopy, a foe or a prop in front of a spell never hid it (only her depth twins did). Two passes:
/// <see cref="FxWorldDepthCopy"/> on the play camera copies its finished depth into <see cref="Tex"/> (R32F, the frame's internal size);
/// <see cref="FxWorldDepthWrite"/> on the after-grade camera, after its opaque pass (the twins), draws that depth into its own depth
/// buffer, pushed back by a small bias (TAA's jitter, a ring lying on the ground), keeping the nearer of the two. Every
/// depth-tested after-grade effect then sits behind the world as it does in the frame. The after-grade viewport renders
/// before the play frame, so the depth is the frame before's: her twins stay (they are this frame's, and she is what the
/// close-up sees). --fx-after-world off: none of it (the A|B).
/// </summary>
public static class FxWorldDepth
{
    public static readonly bool On = SurvivorUnchained.Args.Get("fx-after-world") != "off";
    /// <summary>The bias: a share of the distance plus meters (the world is pushed this far back before it hides light).</summary>
    public const float BiasRel = 0.01f, BiasAbs = 0.06f;
    /// <summary>The play frame's depth (render thread); invalid until the first frame is copied.</summary>
    public static Rid Tex;
    internal static Vector2I TexSize;

    static Rid samplerNearest;
    internal static Rid Nearest(RenderingDevice rd)
    {
        if (!samplerNearest.IsValid)
            samplerNearest = rd.SamplerCreate(new RDSamplerState
            {
                MinFilter = RenderingDevice.SamplerFilter.Nearest, MagFilter = RenderingDevice.SamplerFilter.Nearest,
                RepeatU = RenderingDevice.SamplerRepeatMode.ClampToEdge, RepeatV = RenderingDevice.SamplerRepeatMode.ClampToEdge,
            });
        return samplerNearest;
    }

    internal static RDUniform U(RenderingDevice.UniformType t, int binding, params Rid[] ids)
    {
        var u = new RDUniform { UniformType = t, Binding = binding };
        foreach (var id in ids) u.AddId(id);
        return u;
    }
}
