using System;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>The painterly post-filter's compute passes (BrushShaders) on the current camera's Compositor,
/// after the transparent pass: on the linear HDR frame before the tonemap and the grade LUT. Made and fed
/// by Brush (--brush); never exists without the flag.</summary>
public partial class BrushEffect : CompositorEffect
{
    public Brush.Spec Spec = new();
    /// <summary>Her coverage (Brush's mask viewport, an RD texture), set from the main thread each frame.</summary>
    public volatile object? Mask;
    /// <summary>The 3D target size the last frame rendered at (the mask viewport follows it).</summary>
    public Vector2I TargetSize;
    public double GpuMs = -1;

    RenderingDevice? rd;
    Rid tensor, flow, kuwahara, final, pTensor, pFlow, pKuwahara, pFinal, sampler, ubo;
    bool failed;
    static readonly StringName Ctx = "brush", TTens = "tens", TFlow = "flow", TKuw = "kuw";

    public BrushEffect()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PostTransparent;
        AccessResolvedColor = true;
        AccessResolvedDepth = true;
    }

    Rid Make(string src, string name, out Rid pipe)
    {
        var spirv = rd!.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = src });
        if (!string.IsNullOrEmpty(spirv.CompileErrorCompute))
        {
            GD.PushError($"--brush: {name} shader: {spirv.CompileErrorCompute}");
            failed = true; pipe = default; return default;
        }
        var sh = rd.ShaderCreateFromSpirV(spirv, "brush_" + name);
        pipe = rd.ComputePipelineCreate(sh);
        return sh;
    }

    void Init()
    {
        rd = RenderingServer.GetRenderingDevice();
        tensor = Make(BrushShaders.Tensor, "tensor", out pTensor);
        flow = Make(BrushShaders.Flow, "flow", out pFlow);
        kuwahara = Make(BrushShaders.Kuwahara, "kuwahara", out pKuwahara);
        final = Make(BrushShaders.Final, "final", out pFinal);
        sampler = rd.SamplerCreate(new RDSamplerState
        {
            MinFilter = RenderingDevice.SamplerFilter.Linear, MagFilter = RenderingDevice.SamplerFilter.Linear,
            RepeatU = RenderingDevice.SamplerRepeatMode.ClampToEdge, RepeatV = RenderingDevice.SamplerRepeatMode.ClampToEdge,
        });
        ubo = rd.UniformBufferCreate(128);
    }

    static RDUniform Tex(int binding, Rid sampler, Rid tex)
    {
        var u = new RDUniform { UniformType = RenderingDevice.UniformType.SamplerWithTexture, Binding = binding };
        u.AddId(sampler); u.AddId(tex); return u;
    }

    static RDUniform Img(int binding, Rid tex)
    {
        var u = new RDUniform { UniformType = RenderingDevice.UniformType.Image, Binding = binding };
        u.AddId(tex); return u;
    }

    Rid Set(Rid shader, params RDUniform[] us) => UniformSetCacheRD.GetCache(shader, 0, new Godot.Collections.Array<RDUniform>(us));

    void Pass(Rid pipe, Rid set, byte[] push, Vector2I size)
    {
        long l = rd!.ComputeListBegin();
        rd.ComputeListBindComputePipeline(l, pipe);
        rd.ComputeListBindUniformSet(l, set, 0);
        rd.ComputeListSetPushConstant(l, push, (uint)push.Length);
        rd.ComputeListDispatch(l, (uint)((size.X + 7) / 8), (uint)((size.Y + 7) / 8), 1);
        rd.ComputeListEnd();
    }

    static void Put(float[] m, int at, Projection p)
    {
        Vector4[] cols = { p.X, p.Y, p.Z, p.W };
        for (int c = 0; c < 4; c++) { m[at + c * 4] = cols[c].X; m[at + c * 4 + 1] = cols[c].Y; m[at + c * 4 + 2] = cols[c].Z; m[at + c * 4 + 3] = cols[c].W; }
    }

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (failed || effectCallbackType != (int)EffectCallbackTypeEnum.PostTransparent) return;
        if (Mask is not Rid mask || !mask.IsValid) return;
        if (rd == null) { Init(); if (failed) return; }
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf || renderData.GetRenderSceneData() is not RenderSceneDataRD data) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        TargetSize = buf.GetTargetSize();
        var half = new Vector2I((size.X + 1) / 2, (size.Y + 1) / 2);
        const uint use = (uint)(RenderingDevice.TextureUsageBits.StorageBit | RenderingDevice.TextureUsageBits.SamplingBit);
        var fmt = RenderingDevice.DataFormat.R16G16B16A16Sfloat;
        if (!buf.HasTexture(Ctx, TTens) || buf.GetTextureSliceSize(Ctx, TTens, 0) != half)
        {
            if (buf.HasTexture(Ctx, TTens)) buf.ClearContext(Ctx);
            buf.CreateTexture(Ctx, TTens, fmt, use, RenderingDevice.TextureSamples.Samples1, half, 1, 1, true, false);
            buf.CreateTexture(Ctx, TFlow, fmt, use, RenderingDevice.TextureSamples.Samples1, half, 1, 1, true, false);
            buf.CreateTexture(Ctx, TKuw, fmt, use, RenderingDevice.TextureSamples.Samples1, size, 1, 1, true, false);
        }
        Rid tTens = buf.GetTexture(Ctx, TTens), tFlow = buf.GetTexture(Ctx, TFlow), tKuw = buf.GetTexture(Ctx, TKuw);

        // Read last frames' timings (the GPU timestamps come back a few frames late).
        if (Spec.Time)
        {
            ulong t0 = 0, t1 = 0;
            for (uint i = 0, n = rd!.GetCapturedTimestampsCount(); i < n; i++)
            {
                var nm = rd.GetCapturedTimestampName(i);
                if (nm == "brush0") t0 = rd.GetCapturedTimestampGpuTime(i);
                else if (nm == "brush1") t1 = rd.GetCapturedTimestampGpuTime(i);
            }
            if (t1 > t0 && t0 > 0) GpuMs = (t1 - t0) / 1e6; // (nanoseconds)
            rd.CaptureTimestamp("brush0");
        }

        var proj = data.GetCamProjection();
        float scale = size.Y / 1080f;
        bool ortho = Mathf.IsEqualApprox(proj.W.W, 1f);
        var mats = new float[32];
        // The projection comes depth-corrected (reverse Z, 0-1: the depth buffer's own value is NDC z); the
        // shader takes NDC y = 2v - 1 (Vulkan's, down), so an unflipped projection gets y turned over here.
        var flipY = Projection.Identity; if (proj.Y.Y > 0) flipY.Y = new Vector4(0, -1, 0, 0);
        Put(mats, 0, proj.Inverse() * flipY);
        var x = data.GetCamTransform();
        Put(mats, 16, new Projection(x));
        rd!.BufferUpdate(ubo, 0, 128, MemoryMarshal.AsBytes(mats.AsSpan()).ToArray());
        var s = Spec;
        var push = new float[]
        {
            size.X, size.Y, half.X, half.Y,
            s.R * scale, s.Sharp, s.Hard, s.Str,
            s.Tex, s.Len * scale, s.Wid, Mathf.DegToRad(s.Ang),
            2f / (Mathf.Abs(proj.Y.Y) * size.Y), ortho ? 1 : 0, s.Feather * scale, s.Dbg,
        };
        var pb = MemoryMarshal.AsBytes(push.AsSpan()).ToArray();

        for (uint v = 0, nv = buf.GetViewCount(); v < nv; v++)
        {
            Rid colour = buf.GetColorLayer(v), depth = buf.GetDepthLayer(v);
            Pass(pTensor, Set(tensor, Tex(0, sampler, colour), Img(1, tTens)), pb, half);
            Pass(pFlow, Set(flow, Tex(0, sampler, tTens), Img(1, tFlow)), pb, half);
            Pass(pKuwahara, Set(kuwahara, Tex(0, sampler, colour), Tex(1, sampler, tFlow), Tex(2, sampler, mask), Img(3, tKuw)), pb, size);
            var u = new RDUniform { UniformType = RenderingDevice.UniformType.UniformBuffer, Binding = 4 };
            u.AddId(ubo);
            Pass(pFinal, Set(final, Img(0, colour), Tex(1, sampler, tKuw), Tex(2, sampler, tFlow), Tex(3, sampler, depth), u), pb, size);
        }
        if (Spec.Time) rd.CaptureTimestamp("brush1");
    }

    public override void _Notification(int what)
    {
        if (what != NotificationPredelete || rd == null) return;
        foreach (var r in new[] { tensor, flow, kuwahara, final, sampler, ubo })
            if (r.IsValid) rd.FreeRid(r);
    }
}
