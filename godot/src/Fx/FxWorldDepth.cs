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

    /// <summary>(L1 lead 8 FX2) The effects run only while the after-grade layer lives (FxAfter sets it in _Ready, clears it as it leaves).</summary>
    public static volatile bool Live;

    /// <summary>An effect holding render-device RIDs: <see cref="Release"/> frees them (render thread) and the effect remakes them lazily.</summary>
    internal interface IRids { void FreeRids(RenderingDevice rd); }
    static readonly System.Collections.Generic.List<IRids> owners = new();
    internal static void Track(IRids o) { lock (owners) if (!owners.Contains(o)) owners.Add(o); }

    /// <summary>(L1 lead 8 FX2) Frees every effect's RIDs, the depth texture and the sampler, on the render thread, now. FxAfter
    /// calls it as it leaves the tree: at quit that is SceneTree.finalize, before the scripts and the rendering server go.
    /// The effects' own predelete never came in time: the static copy effect and the compositors' C# wrappers outlive the
    /// tree, and are only let go at the .NET shutdown, by which time a predelete either never reaches the script or the
    /// device is gone; the cached uniform sets (UniformSetCacheRD) then outlive the cache, and the device's leak sweep
    /// calls back into the freed cache: the signal 11 at quit.</summary>
    public static void Release()
    {
        Live = false;
        RenderingServer.CallOnRenderThread(Callable.From(ReleaseNow));
    }

    static void ReleaseNow()
    {
        var rd = RenderingServer.GetRenderingDevice();
        if (rd == null) return;
        IRids[] all;
        lock (owners) { all = owners.ToArray(); owners.Clear(); }
        foreach (var o in all) o.FreeRids(rd);
        bool tex = Tex.IsValid;
        Free(rd);
        GD.Print($"fx world depth: released {all.Length} effect(s), depth texture {(tex ? "freed" : "none")}");
    }

    /// <summary>Frees the static depth texture and the sampler.</summary>
    static void Free(RenderingDevice rd)
    {
        if (Tex.IsValid) rd.FreeRid(Tex);
        Tex = default; TexSize = default;
        if (samplerNearest.IsValid) rd.FreeRid(samplerNearest);
        samplerNearest = default;
    }

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
