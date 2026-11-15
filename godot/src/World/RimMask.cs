using System;
using System.Globalization;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (rim round 3, 14 Nov) Where skin's stepped rim may draw: within a few px of her OUTLINE, the near side of a depth drop
/// to something well behind (the sky, the street), never at a contour that turns in front of her own body (the cleavage's
/// inner breast, the armpit, the flank under an arm, the thigh fork: there the surface behind is a few cm away). A compute
/// pass at PreOpaque, after the depth prepass, on this frame's resolved depth, into an R8 mask the size of the frame;
/// heroine_skin samples it at SCREEN_UV (global cel_rim_mask, gated by cel_rim_mask_on) and times its rim by it.
/// Args: --rim-mask off (no mask: the rim as before), --rim-mask-px close,play (6,3 px at 1080p, by the ink's z_close /
/// z_play), --rim-mask-depth a,b (the drop: max(a m, b x z); 0.15, 0.03), --rim-mask-dbg (the mask drawn grey on the frame).
/// </summary>
public partial class RimMask : CompositorEffect, InkRelease.IRids
{
    public static readonly bool On = Args.Get("rim-mask") is not ("off" or "0");
    public static float RClose = 6f, RPlay = 3f, ThA = 0.15f, ThB = 0.03f;
    public static readonly bool Dbg = Args.Has("rim-mask-dbg");
    public static readonly StringName Global = "cel_rim_mask", GlobalOn = "cel_rim_mask_on";

    static RimMask()
    {
        float[]? V(string k, int n)
        {
            if (Args.Get(k) is not string s) return null;
            var p = s.Split(',');
            if (p.Length != n) { GD.PushWarning($"--{k}: want {n} numbers, got '{s}'"); return null; }
            var o = new float[n];
            for (int i = 0; i < n; i++)
                if (!float.TryParse(p[i], NumberStyles.Float, CultureInfo.InvariantCulture, out o[i])) { GD.PushWarning($"--{k}: bad '{s}'"); return null; }
            return o;
        }
        if (V("rim-mask-px", 2) is [var rc, var rp]) { RClose = rc; RPlay = rp; }
        if (V("rim-mask-depth", 2) is [var a, var b]) { ThA = a; ThB = b; }
    }

    const string Code = """
        #version 450
        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;
        #ifdef MS
        layout(set = 0, binding = 0) uniform sampler2DMS depth_tex;
        #else
        layout(set = 0, binding = 0) uniform sampler2D depth_tex;
        #endif
        layout(set = 0, binding = 1, r8) uniform restrict writeonly image2D mask;
        layout(set = 0, binding = 2, std140) uniform M { mat4 inv_proj; } mt;
        layout(push_constant, std430) uniform P {
            vec2 size; float r_close; float r_play;
            float th_a; float th_b; float z_close; float z_play;
        } pc;

        const int T = 16, A = 10, S = T + 2 * A;
        shared float sz[S * S];   // view depth (positive), 1e9 the sky

        void main() {
            ivec2 isz = ivec2(pc.size);
            ivec2 base = ivec2(gl_WorkGroupID.xy) * T - A;
            int li = int(gl_LocalInvocationIndex);
            for (int i = li; i < S * S; i += T * T) {
                ivec2 p = clamp(base + ivec2(i % S, i / S), ivec2(0), isz - 1);
                #ifdef MS
                float d = texelFetch(depth_tex, p, 0).r;   // (sample 0 of the prepass's own MSAA depth)
                #else
                float d = texelFetch(depth_tex, p, 0).r;
                #endif
                vec2 ndc = (vec2(p) + 0.5) / pc.size * 2.0 - 1.0;
                vec4 v = mt.inv_proj * vec4(ndc, d, 1.0);
                sz[i] = d <= 0.0 ? 1e9 : -v.z / v.w;
            }
            barrier();
            ivec2 px = ivec2(gl_GlobalInvocationID.xy);
            if (px.x >= isz.x || px.y >= isz.y) return;
            ivec2 q = ivec2(gl_LocalInvocationID.xy) + A;
            float z = sz[q.y * S + q.x];
            if (z > 1e8) { imageStore(mask, px, vec4(0.0)); return; }
            float r = mix(pc.r_close, pc.r_play, smoothstep(pc.z_close, pc.z_play, z));
            float th = max(pc.th_a, pc.th_b * z);
            int K = min(int(ceil(r + 1.0)), A);
            // The nearest neighbor (in px, within r) lying well behind this pixel: the outline's near side; the mask
            // 1 up to r px in, fading over the last px.
            float best = 1e9;
            for (int y = -K; y <= K; y++) for (int x = -K; x <= K; x++) {
                float d = length(vec2(x, y));
                if (d > r + 1.0 || d >= best) continue;
                if (sz[(q.y + y) * S + q.x + x] - z > th) best = d;
            }
            imageStore(mask, px, vec4(clamp(r + 1.0 - best, 0.0, 1.0)));
        }
        """;

    const string Show = """
        #version 450
        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;
        layout(set = 0, binding = 0, rgba16f) uniform image2D colour;
        layout(set = 0, binding = 1) uniform sampler2D mask;
        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, imageSize(colour)))) return;
            vec4 c = imageLoad(colour, p);
            float m = texelFetch(mask, p, 0).r;
            imageStore(colour, p, vec4(mix(c.rgb * 0.35, vec3(1.0, 0.2, 1.0), m), c.a));
        }
        """;

    RenderingDevice? rd;
    Rid shader, pipe, shaderMs, pipeMs, showShader, showPipe, sampler, ubo;
    // (the mask's RD texture: the PreOpaque instance makes it, the --rim-mask-dbg one draws it)
    static Rid tex;
    static Vector2I texSize;
    bool failed;
    readonly bool show;
    /// <summary>The mask as a texture the materials can sample (the global cel_rim_mask), its RD texture swapped in on a resize.</summary>
    public static readonly Texture2Drd Tex = new();

    /// <summary>The frame's internal size the mask wants (render thread); <see cref="Ready"/> once a mask of it exists.</summary>
    public static Vector2I Want;
    public static bool Ready => tex.IsValid && texSize == Want;
    static bool announced0;

    /// <summary>(render thread, between frames: RenderingServer.CallOnRenderThread from the Ink node) the mask texture at
    /// <see cref="Want"/>, swapped into <see cref="Tex"/>.</summary>
    public static void Make()
    {
        var dev = RenderingServer.GetRenderingDevice();
        var size = Want;
        if (dev == null || size.X <= 0 || size.Y <= 0 || (tex.IsValid && texSize == size)) return;
        var old = tex;
        tex = dev.TextureCreate(new RDTextureFormat
        {
            Format = RenderingDevice.DataFormat.R8Unorm, Width = (uint)size.X, Height = (uint)size.Y,
            UsageBits = RenderingDevice.TextureUsageBits.StorageBit | RenderingDevice.TextureUsageBits.SamplingBit,
        }, new RDTextureView());
        texSize = size;
        Tex.TextureRdRid = tex;
        if (old.IsValid) dev.FreeRid(old);
        if (!announced0) { announced0 = true; GD.Print($"rim mask: {size.X}x{size.Y}, r {RClose}/{RPlay} px, drop max({ThA} m, {ThB} z)"); }
    }

    /// <summary>show false: the mask (PreOpaque); true: the --rim-mask-dbg view of it (PostTransparent).</summary>
    public RimMask(bool show = false)
    {
        this.show = show;
        EffectCallbackType = show ? EffectCallbackTypeEnum.PostTransparent : EffectCallbackTypeEnum.PreOpaque;
        AccessResolvedDepth = !show;
        AccessResolvedColor = show;
    }

    void Init()
    {
        rd = RenderingServer.GetRenderingDevice();
        var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Code });
        if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError($"rim mask shader: {spirv.CompileErrorCompute}"); failed = true; return; }
        shader = rd.ShaderCreateFromSpirV(spirv, "rim_mask");
        pipe = rd.ComputePipelineCreate(shader);
        // (with MSAA the prepass's depth is read itself: the resolved one is only made before the opaque pass when some
        // effect wants it (SSAO), so in the Look (none) it held another frame's picture)
        var ms = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Code.Replace("#version 450", "#version 450\n#define MS") });
        if (!string.IsNullOrEmpty(ms.CompileErrorCompute)) { GD.PushError($"rim mask shader (MS): {ms.CompileErrorCompute}"); failed = true; return; }
        shaderMs = rd.ShaderCreateFromSpirV(ms, "rim_mask_ms");
        pipeMs = rd.ComputePipelineCreate(shaderMs);
        sampler = rd.SamplerCreate(new RDSamplerState
        {
            MinFilter = RenderingDevice.SamplerFilter.Nearest, MagFilter = RenderingDevice.SamplerFilter.Nearest,
            RepeatU = RenderingDevice.SamplerRepeatMode.ClampToEdge, RepeatV = RenderingDevice.SamplerRepeatMode.ClampToEdge,
        });
        ubo = rd.UniformBufferCreate(64);
        InkRelease.Track(this);
    }

    public void FreeRids(RenderingDevice dev)
    {
        foreach (var r in new[] { shader, shaderMs, showShader, sampler, ubo })
            if (r.IsValid) dev.FreeRid(r);
        // (the mask texture stays: the Texture2DRD still wraps it; freed with the device)
        shader = pipe = shaderMs = pipeMs = showShader = showPipe = sampler = ubo = default;
        rd = null;
    }

    static RDUniform U(RenderingDevice.UniformType t, int binding, params Rid[] ids)
    {
        var u = new RDUniform { UniformType = t, Binding = binding };
        foreach (var id in ids) u.AddId(id);
        return u;
    }

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (!InkRelease.Live || failed) return;
        if (rd == null) { Init(); if (failed) return; }
        if (show) { if (effectCallbackType == (int)EffectCallbackTypeEnum.PostTransparent) ShowMask(renderData); return; }
        if (effectCallbackType != (int)EffectCallbackTypeEnum.PreOpaque) return;
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf || renderData.GetRenderSceneData() is not RenderSceneDataRD data) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        // (the texture is made between frames, Make via the Ink node: swapping it mid-frame dropped the materials' sets)
        Want = size;
        if (!tex.IsValid || texSize != size) return;
        var proj = data.GetCamProjection();
        // (as InkPass: reverse Z 0-1, NDC y Vulkan's)
        var flipY = Projection.Identity; if (proj.Y.Y > 0) flipY.Y = new Vector4(0, -1, 0, 0);
        var inv = proj.Inverse() * flipY;
        var m = new float[16];
        Vector4[] cols = { inv.X, inv.Y, inv.Z, inv.W };
        for (int c = 0; c < 4; c++) { m[c * 4] = cols[c].X; m[c * 4 + 1] = cols[c].Y; m[c * 4 + 2] = cols[c].Z; m[c * 4 + 3] = cols[c].W; }
        rd!.BufferUpdate(ubo, 0, 64, MemoryMarshal.AsBytes(m.AsSpan()).ToArray());
        float scale = size.Y / 1080f;
        var push = new float[] { size.X, size.Y, RClose * scale, RPlay * scale, ThA, ThB, InkPass.ZClose, InkPass.ZPlay };
        var pb = MemoryMarshal.AsBytes(push.AsSpan()).ToArray();
        bool msaa = buf.GetMsaa3D() != RenderingServer.ViewportMsaa.Disabled;
        var sh = msaa ? shaderMs : shader;
        var set = UniformSetCacheRD.GetCache(sh, 0, new Godot.Collections.Array<RDUniform>
        {
            U(RenderingDevice.UniformType.SamplerWithTexture, 0, sampler, buf.GetDepthLayer(0, msaa)),
            U(RenderingDevice.UniformType.Image, 1, tex),
            U(RenderingDevice.UniformType.UniformBuffer, 2, ubo),
        });
        long l = rd.ComputeListBegin();
        rd.ComputeListBindComputePipeline(l, msaa ? pipeMs : pipe);
        rd.ComputeListBindUniformSet(l, set, 0);
        rd.ComputeListSetPushConstant(l, pb, (uint)pb.Length);
        rd.ComputeListDispatch(l, (uint)((size.X + 15) / 16), (uint)((size.Y + 15) / 16), 1);
        rd.ComputeListEnd();
    }

    // (--rim-mask-dbg) the mask in magenta over the darkened frame, after the transparent pass.
    void ShowMask(RenderData renderData)
    {
        if (rd == null || !tex.IsValid) return;
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf) return;
        if (!showShader.IsValid)
        {
            var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Show });
            if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError($"rim mask show: {spirv.CompileErrorCompute}"); return; }
            showShader = rd.ShaderCreateFromSpirV(spirv, "rim_mask_show");
            showPipe = rd.ComputePipelineCreate(showShader);
        }
        var size = buf.GetInternalSize();
        var set = UniformSetCacheRD.GetCache(showShader, 0, new Godot.Collections.Array<RDUniform>
        {
            U(RenderingDevice.UniformType.Image, 0, buf.GetColorLayer(0)),
            U(RenderingDevice.UniformType.SamplerWithTexture, 1, sampler, tex),
        });
        long l = rd.ComputeListBegin();
        rd.ComputeListBindComputePipeline(l, showPipe);
        rd.ComputeListBindUniformSet(l, set, 0);
        rd.ComputeListDispatch(l, (uint)((size.X + 15) / 16), (uint)((size.Y + 15) / 16), 1);
        rd.ComputeListEnd();
    }
}
