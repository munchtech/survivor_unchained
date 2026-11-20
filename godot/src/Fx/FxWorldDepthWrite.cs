using System;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>The write, on the after-grade camera (after its opaque pass: the twins are in its depth).</summary>
public partial class FxWorldDepthWrite : CompositorEffect, FxWorldDepth.IRids
{
    RenderingDevice? rd;
    Rid shader, pipe, fb, fbDepth;
    long fbFormat = -1;
    bool failed;
    readonly float[] pc = new float[8];
    readonly byte[] pb = new byte[32];
    Godot.Collections.Array<RDUniform>? setArr;
    Rid setSampler, setTex;

    public FxWorldDepthWrite()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PostOpaque;
    }

    void FxWorldDepth.IRids.FreeRids(RenderingDevice rd)
    {
        if (fb.IsValid && rd.FramebufferIsValid(fb)) rd.FreeRid(fb);
        if (shader.IsValid) rd.FreeRid(shader); // (its pipelines and cached uniform sets go with it)
        fb = default; shader = default; pipe = default; fbDepth = default; fbFormat = -1; setArr = null;
        this.rd = null;
    }

    const string Vs = """
        #version 450
        layout(location = 0) out vec2 uv;
        void main() {
            vec2 p = vec2(float((gl_VertexIndex << 1) & 2), float(gl_VertexIndex & 2));
            uv = p;
            gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
        }
        """;
    // pr: the projection's depth terms (Z.z, W.z, Z.w, W.w: clip z and w from view z); b: the bias (share, meters)
    const string Fs = """
        #version 450
        layout(location = 0) in vec2 uv;
        layout(set = 0, binding = 0) uniform sampler2D world;
        layout(push_constant, std430) uniform P { vec4 pr; vec4 b; } pc;
        void main() {
            float d = texture(world, uv).r;
            if (d <= 1e-7) discard;
            float vz = (pc.pr.y - d * pc.pr.w) / (d * pc.pr.z - pc.pr.x);
            vz -= abs(vz) * pc.b.x + pc.b.y;
            float cz = pc.pr.x * vz + pc.pr.y, cw = pc.pr.z * vz + pc.pr.w;
            gl_FragDepth = clamp(cz / cw, 0.0, 1.0);
        }
        """;

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (failed || !FxWorldDepth.Live || !FxWorldDepth.Tex.IsValid || effectCallbackType != (int)EffectCallbackTypeEnum.PostOpaque) return;
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf || renderData.GetRenderSceneData() is not RenderSceneDataRD data) return;
        rd ??= RenderingServer.GetRenderingDevice();
        if (!shader.IsValid)
        {
            var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceVertex = Vs, SourceFragment = Fs });
            if (!string.IsNullOrEmpty(spirv.CompileErrorVertex) || !string.IsNullOrEmpty(spirv.CompileErrorFragment))
            { GD.PushError("FxWorldDepth write: " + spirv.CompileErrorVertex + spirv.CompileErrorFragment); failed = true; return; }
            shader = rd.ShaderCreateFromSpirV(spirv, "fx_world_depth_write");
            FxWorldDepth.Track(this);
        }
        var depth = buf.GetDepthLayer(0);
        if (!fb.IsValid || fbDepth != depth || !rd.FramebufferIsValid(fb))
        {
            if (fb.IsValid && rd.FramebufferIsValid(fb)) rd.FreeRid(fb);
            fbDepth = depth;
            fb = rd.FramebufferCreate(new Godot.Collections.Array<Rid> { depth });
            long fmt = rd.FramebufferGetFormat(fb);
            if (fmt != fbFormat || !pipe.IsValid)
            {
                fbFormat = fmt;
                if (pipe.IsValid && rd.RenderPipelineIsValid(pipe)) rd.FreeRid(pipe);
                pipe = rd.RenderPipelineCreate(shader, fmt, RenderingDevice.InvalidFormatId, RenderingDevice.RenderPrimitive.Triangles,
                    new RDPipelineRasterizationState(), new RDPipelineMultisampleState(),
                    new RDPipelineDepthStencilState
                    {
                        EnableDepthTest = true, EnableDepthWrite = true,
                        // (reversed z: nearer is greater; the nearer of the twins and the world stays)
                        DepthCompareOperator = RenderingDevice.CompareOperator.GreaterOrEqual,
                    },
                    new RDPipelineColorBlendState(), 0, 0, new Godot.Collections.Array<RDPipelineSpecializationConstant>());
            }
        }
        var p = data.GetCamProjection();
        pc[0] = p.Z.Z; pc[1] = p.W.Z; pc[2] = p.Z.W; pc[3] = p.W.W; pc[4] = FxWorldDepth.BiasRel; pc[5] = FxWorldDepth.BiasAbs; pc[6] = 0; pc[7] = 0;
        MemoryMarshal.AsBytes(pc.AsSpan()).CopyTo(pb);
        // (the uniform array made once, rebuilt only when the sampler or the texture RID changes)
        Rid nearest = FxWorldDepth.Nearest(rd), tex = FxWorldDepth.Tex;
        if (setArr == null || setSampler != nearest || setTex != tex)
        {
            setSampler = nearest; setTex = tex;
            setArr = new Godot.Collections.Array<RDUniform>
            {
                FxWorldDepth.U(RenderingDevice.UniformType.SamplerWithTexture, 0, nearest, tex),
            };
        }
        var set = UniformSetCacheRD.GetCache(shader, 0, setArr);
        long dl = rd.DrawListBegin(fb, RenderingDevice.DrawFlags.DefaultAll);
        rd.DrawListBindRenderPipeline(dl, pipe);
        rd.DrawListBindUniformSet(dl, set, 0);
        rd.DrawListSetPushConstant(dl, pb, (uint)pb.Length);
        rd.DrawListDraw(dl, false, 1, 3);
        rd.DrawListEnd();
    }
}
