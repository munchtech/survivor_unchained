using System;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>The copy, on the play camera (after its transparent pass: the depth is final).</summary>
public partial class FxWorldDepthCopy : CompositorEffect
{
    RenderingDevice? rd;
    Rid shader, pipe;
    bool failed;

    public FxWorldDepthCopy()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PostTransparent;
        AccessResolvedDepth = true;
    }

    const string Src = """
        #version 450
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        layout(set = 0, binding = 0) uniform sampler2D depth;
        layout(set = 0, binding = 1, r32f) uniform writeonly image2D outd;
        layout(push_constant, std430) uniform P { vec4 size; } pc;
        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (p.x >= int(pc.size.x) || p.y >= int(pc.size.y)) return;
            imageStore(outd, p, vec4(texelFetch(depth, p, 0).r, 0.0, 0.0, 0.0));
        }
        """;

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (failed || effectCallbackType != (int)EffectCallbackTypeEnum.PostTransparent) return;
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        if (rd == null)
        {
            rd = RenderingServer.GetRenderingDevice();
            var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Src });
            if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError("FxWorldDepth copy: " + spirv.CompileErrorCompute); failed = true; return; }
            shader = rd.ShaderCreateFromSpirV(spirv, "fx_world_depth_copy");
            pipe = rd.ComputePipelineCreate(shader);
        }
        if (!FxWorldDepth.Tex.IsValid || size != FxWorldDepth.TexSize)
        {
            if (FxWorldDepth.Tex.IsValid) rd.FreeRid(FxWorldDepth.Tex);
            FxWorldDepth.TexSize = size;
            FxWorldDepth.Tex = rd.TextureCreate(new RDTextureFormat
            {
                Width = (uint)size.X, Height = (uint)size.Y, Format = RenderingDevice.DataFormat.R32Sfloat,
                UsageBits = RenderingDevice.TextureUsageBits.StorageBit | RenderingDevice.TextureUsageBits.SamplingBit,
            }, new RDTextureView());
        }
        var set = UniformSetCacheRD.GetCache(shader, 0, new Godot.Collections.Array<RDUniform>
        {
            FxWorldDepth.U(RenderingDevice.UniformType.SamplerWithTexture, 0, FxWorldDepth.Nearest(rd), buf.GetDepthLayer(0)),
            FxWorldDepth.U(RenderingDevice.UniformType.Image, 1, FxWorldDepth.Tex),
        });
        var pc = new float[] { size.X, size.Y, 0, 0 };
        var pb = MemoryMarshal.AsBytes(pc.AsSpan()).ToArray();
        long l = rd.ComputeListBegin();
        rd.ComputeListBindComputePipeline(l, pipe);
        rd.ComputeListBindUniformSet(l, set, 0);
        rd.ComputeListSetPushConstant(l, pb, (uint)pb.Length);
        rd.ComputeListDispatch(l, (uint)((size.X + 7) / 8), (uint)((size.Y + 7) / 8), 1);
        rd.ComputeListEnd();
    }
}
