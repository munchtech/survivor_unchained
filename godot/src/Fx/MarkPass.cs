using System;
using System.Collections.Generic;
using System.Globalization;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>The red line drawn on the finished frame (round 3's judge: an alpha-blended dark bed flattened the ground's
/// texture, read as red cellophane by day, and over water as an opaque plank). One compute pass after the transparent
/// pass (so after the water), on the linear HDR frame before the tonemap: every pixel whose surface is the ground or the
/// water under an elite's or a boss's mark is RE-TINTED, its own light kept as a scalar and given back in scarlet
/// (bed = value x K x scarlet: the ground's texture and the river's ripples stay, the hue locked under moon or sun), the
/// rims and the running fill's front added as light on top. The same function over land and water, so a bank is not
/// seen. Only the ground takes it: a point well above the mark's own ground (a rock's cap, a foe, her) is left alone,
/// and a roof over a lane takes the lane at the ground's place under it. BattleFx feeds the marks each frame (Set).</summary>
public partial class MarkPass : CompositorEffect
{
    public const int MaxMarks = 32, Grid = 32;
    const int MarkFloats = 16;

    /// <summary>The look's numbers (env MARK_TUNE "k=0.8,w=0.5,..." overrides, for measuring).</summary>
    public static readonly Dictionary<string, float> Tune = new()
    {
        ["k"] = 1.0f,      // the bed's value against the ground's (its scalar x k, in linear light)
        ["w"] = 1.0f,      // the scalar: luma (0) to the brightest channel (1)
        ["tg"] = 0.0f, ["tb"] = 0.004f, // the bed's scarlet, linear (1, tg, tb)
        ["hg"] = 0.0f, ["hb"] = 0.015f, // the rims' (#ff0612)
        ["glow"] = 0.0f,   // a breath of light through the bed's heart (the rise toward the rims stays)
        ["g0"] = 0.14f, ["g1"] = 0.4f, // over the mark's ground: full to g0 m, none past g1
        ["front"] = 0.2f, ["tail"] = 0.4f, ["body"] = 0.1f, ["fill"] = 0.35f,
        ["roof"] = 2.6f,
        ["cal"] = 0, ["dk"] = 0.6f, ["dv"] = 0.02f,
    };

    static MarkPass()
    {
        if (System.Environment.GetEnvironmentVariable("MARK_TUNE") is not { Length: > 0 } s) return;
        foreach (var kv in s.Split(','))
            if (kv.Split('=') is [var k, var v] && float.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out var f)) Tune[k.Trim()] = f;
    }

    // (main thread -> render thread: whole arrays swapped, never written once handed over)
    volatile float[]? marks;
    volatile int count;
    volatile float[]? heights;
    float waterY; bool waterOn;
    public double GpuMs = -1;
    public static bool Time = System.Environment.GetEnvironmentVariable("MARK_TIME") == "1";

    RenderingDevice? rd;
    Rid shader, pipe, sampler, ubo, markBuf, hBuf;
    bool failed;

    public MarkPass()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PostTransparent;
        AccessResolvedColor = true;
        AccessResolvedDepth = true;
        NeedsNormalRoughness = true;
        Enabled = false;
    }

    /// <summary>This frame's marks (MarkFloats each) and the zone's still water.</summary>
    public void Set(float[] m, int n, float? water)
    {
        marks = m; count = n; waterOn = water.HasValue; waterY = water ?? 0;
        Enabled = n > 0;
    }

    /// <summary>The marks' ground heights (Grid x Grid per slot) after one changed.</summary>
    public void SetHeights(float[] h) => heights = h;

    void Init()
    {
        rd = RenderingServer.GetRenderingDevice();
        var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Src });
        if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError("MarkPass shader: " + spirv.CompileErrorCompute); failed = true; return; }
        shader = rd.ShaderCreateFromSpirV(spirv, "mark_pass");
        pipe = rd.ComputePipelineCreate(shader);
        sampler = rd.SamplerCreate(new RDSamplerState
        {
            MinFilter = RenderingDevice.SamplerFilter.Nearest, MagFilter = RenderingDevice.SamplerFilter.Nearest,
            RepeatU = RenderingDevice.SamplerRepeatMode.ClampToEdge, RepeatV = RenderingDevice.SamplerRepeatMode.ClampToEdge,
        });
        ubo = rd.UniformBufferCreate(128);
        markBuf = rd.StorageBufferCreate(MaxMarks * MarkFloats * 4);
        hBuf = rd.StorageBufferCreate(MaxMarks * Grid * Grid * 4);
    }

    static void Put(float[] m, int at, Projection p)
    {
        Vector4[] cols = { p.X, p.Y, p.Z, p.W };
        for (int c = 0; c < 4; c++) { m[at + c * 4] = cols[c].X; m[at + c * 4 + 1] = cols[c].Y; m[at + c * 4 + 2] = cols[c].Z; m[at + c * 4 + 3] = cols[c].W; }
    }

    static RDUniform U(RenderingDevice.UniformType t, int binding, params Rid[] ids)
    {
        var u = new RDUniform { UniformType = t, Binding = binding };
        foreach (var id in ids) u.AddId(id);
        return u;
    }

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (failed || effectCallbackType != (int)EffectCallbackTypeEnum.PostTransparent) return;
        var m = marks; int n = Math.Min(count, MaxMarks);
        if (m == null || n <= 0) return;
        if (rd == null) { Init(); if (failed) return; }
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf || renderData.GetRenderSceneData() is not RenderSceneDataRD data) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        if (Time)
        {
            ulong t0 = 0, t1 = 0;
            for (uint i = 0, c = rd!.GetCapturedTimestampsCount(); i < c; i++)
            {
                var nm = rd.GetCapturedTimestampName(i);
                if (nm == "mark0") t0 = rd.GetCapturedTimestampGpuTime(i);
                else if (nm == "mark1") t1 = rd.GetCapturedTimestampGpuTime(i);
            }
            if (t1 > t0 && t0 > 0) GpuMs = (t1 - t0) / 1e6;
            rd.CaptureTimestamp("mark0");
        }
        if (heights is { } h) { heights = null; rd!.BufferUpdate(hBuf, 0, (uint)(h.Length * 4), MemoryMarshal.AsBytes(h.AsSpan()).ToArray()); }
        rd!.BufferUpdate(markBuf, 0, (uint)(n * MarkFloats * 4), MemoryMarshal.AsBytes(m.AsSpan(0, n * MarkFloats)).ToArray());
        var proj = data.GetCamProjection();
        var mats = new float[32];
        var flipY = Projection.Identity; if (proj.Y.Y > 0) flipY.Y = new Vector4(0, -1, 0, 0);
        Put(mats, 0, proj.Inverse() * flipY);
        Put(mats, 16, new Projection(data.GetCamTransform()));
        rd.BufferUpdate(ubo, 0, 128, MemoryMarshal.AsBytes(mats.AsSpan()).ToArray());
        var T = Tune;
        bool hasN = buf.HasTexture("forward_clustered", "normal_roughness");
        var push = new float[]
        {
            size.X, size.Y, n, hasN ? 1 : 0,
            waterOn ? 1 : 0, waterY, T["k"], T["w"],
            T["tg"], T["tb"], T["hg"], T["hb"],
            T["glow"], T["g0"], T["g1"], T["roof"],
            T["front"], T["tail"], T["body"], T["fill"],
            T["cal"], T["dk"], T["dv"], 0,
        };
        var pb = MemoryMarshal.AsBytes(push.AsSpan()).ToArray();
        for (uint v = 0, nv = buf.GetViewCount(); v < nv; v++)
        {
            Rid colour = buf.GetColorLayer(v), depth = buf.GetDepthLayer(v);
            Rid nr = hasN ? buf.GetTextureSlice("forward_clustered", "normal_roughness", v, 0, 1, 1) : depth;
            var set = UniformSetCacheRD.GetCache(shader, 0, new Godot.Collections.Array<RDUniform>
            {
                U(RenderingDevice.UniformType.Image, 0, colour),
                U(RenderingDevice.UniformType.SamplerWithTexture, 1, sampler, depth),
                U(RenderingDevice.UniformType.SamplerWithTexture, 2, sampler, nr),
                U(RenderingDevice.UniformType.UniformBuffer, 3, ubo),
                U(RenderingDevice.UniformType.StorageBuffer, 4, markBuf),
                U(RenderingDevice.UniformType.StorageBuffer, 5, hBuf),
            });
            long l = rd.ComputeListBegin();
            rd.ComputeListBindComputePipeline(l, pipe);
            rd.ComputeListBindUniformSet(l, set, 0);
            rd.ComputeListSetPushConstant(l, pb, (uint)pb.Length);
            rd.ComputeListDispatch(l, (uint)((size.X + 7) / 8), (uint)((size.Y + 7) / 8), 1);
            rd.ComputeListEnd();
        }
        if (Time) rd.CaptureTimestamp("mark1");
    }

    public override void _Notification(int what)
    {
        if (what != NotificationPredelete || rd == null) return;
        foreach (var r in new[] { shader, sampler, ubo, markBuf, hBuf })
            if (r.IsValid) rd.FreeRid(r);
    }

    /// <summary>One mark's floats: centre (x, y, z), shape (0 lane, 1 ring, 2 cone, 3 band); its local X and Z axes in
    /// the plane; its half sizes (x, z), its light's energy now, its bed's strength; its fill (a lane's filled length
    /// from its start, a disc's filled radius; -1 none), a cone's half arc or a band's inner radius, its heights' slot,
    /// whether a roof over it takes it.</summary>
    public static void Pack(float[] a, int i, Vector3 c, int shape, Vector3 ax, Vector3 az, float hx, float hz, float energy, float bed, float fill, float p1, int slot, bool roof)
    {
        int o = i * MarkFloats;
        a[o] = c.X; a[o + 1] = c.Y; a[o + 2] = c.Z; a[o + 3] = shape;
        a[o + 4] = ax.X; a[o + 5] = ax.Z; a[o + 6] = az.X; a[o + 7] = az.Z;
        a[o + 8] = hx; a[o + 9] = hz; a[o + 10] = energy; a[o + 11] = bed;
        a[o + 12] = fill; a[o + 13] = p1; a[o + 14] = slot; a[o + 15] = roof ? 1 : 0;
    }

    const string Src = """
        #version 450
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        layout(push_constant, std430) uniform P {
            vec2 size; float n; float has_n;
            float water_on; float water_y; float k; float w;
            float tg; float tb; float hg; float hb;
            float glow; float g0; float g1; float roof;
            float front; float tail; float body; float fill_e;
            float cal; float dk; float dv; float pad;
        } pc;
        layout(set = 0, binding = 0, rgba16f) uniform image2D colour;
        layout(set = 0, binding = 1) uniform sampler2D depth;
        layout(set = 0, binding = 2) uniform sampler2D nrm;
        layout(set = 0, binding = 3, std140) uniform M { mat4 inv_proj; mat4 cam; } mt;
        layout(set = 0, binding = 4, std430) readonly buffer Marks { vec4 m[]; } mk;
        layout(set = 0, binding = 5, std430) readonly buffer Hts { float h[]; } ht;

        const int G = 32;
        float ground(int slot, vec2 q) {
            // q: the mark's local point over its half sizes, -1..1
            vec2 g = clamp(q * 0.5 + 0.5, 0.0, 1.0) * float(G - 1);
            ivec2 i = min(ivec2(floor(g)), ivec2(G - 2)); vec2 f = g - vec2(i);
            int o = slot * G * G;
            float a = ht.h[o + i.y * G + i.x], b = ht.h[o + i.y * G + i.x + 1];
            float c = ht.h[o + (i.y + 1) * G + i.x], d = ht.h[o + (i.y + 1) * G + i.x + 1];
            return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
        }

        // A rim's light at signed distance d (m, < 0 inside): a narrow hot core, a short soft glow.
        float rim(float d, float core, float soft, float glw, float gk) {
            return max(clamp(1.0 - max(abs(d) - core, 0.0) / soft, 0.0, 1.0), gk * exp(-abs(d) / glw));
        }

        // A fill's light at dm metres behind its front (< 0: ahead of it): a soft leading edge, a short tail, a breath of body.
        float fillf(float dm) {
            float lead = smoothstep(-pc.front, 0.0, dm);
            float t = 1.0 - clamp(dm / pc.tail, 0.0, 1.0);
            return lead * max(dm > 0.0 ? t * t : 1.0, dm > 0.0 ? pc.body : 0.0);
        }

        // One mark at local point l (m): out cover (the bed's re-tint), light (its own, x the energy)
        void shape(int i, vec2 l, out float cover, out float light) {
            vec4 a = mk.m[i * 4], s = mk.m[i * 4 + 2], e = mk.m[i * 4 + 3];
            int kind = int(a.w + 0.5);
            float hx = s.x, hz = s.y, d, inner, edge, ends = 1.0, wh, f = 0.0;
            if (kind == 0) {
                // a lane: rims along its sides at 0.9 of its half width, soft ends (no cap line: a lane, not a box)
                float sc = hx;
                d = abs(l.x) - 0.9 * hx;
                float core = max(0.012 * sc, 0.008), soft = max(0.014 * sc, 0.008), glw = max(0.05 * sc, 0.03);
                edge = rim(d, core, soft, glw, 0.5);
                float sm = smoothstep(-0.35 * hx, 0.0, d);
                inner = d < 0.0 ? pc.glow + 0.45 * sm * sm : 0.0;
                float fe = hz - abs(l.y);
                ends = smoothstep(0.0, 0.45, fe);
                edge *= smoothstep(0.0, 0.3, fe);
                wh = glw * 1.5;
                if (e.x >= 0.0) {
                    float dm = (-hz + e.x) - l.y;
                    f = fillf(dm) * clamp((0.86 * hx - abs(l.x)) / max(0.04 * hx, 0.02), 0.0, 1.0) * smoothstep(0.0, 0.15, l.y + hz);
                }
            } else {
                float R = hx, r = length(l);
                float core = clamp(0.045, 0.004 * R, 0.06 * R), soft = core * 0.6 + 0.003 * R;
                float fin = core * 4.0 + 0.01 * R, fout = core * 1.2 + 0.004 * R;
                float rc = 0.93 * R;
                if (kind == 1) d = r - rc;
                else if (kind == 2) {
                    float ang = abs(atan(l.x, l.y));
                    d = max(r - rc, r * sin(clamp(ang - e.y, -1.5, 1.5)));
                } else d = max(r - rc, e.y - r);
                float rm = clamp(1.0 - max(abs(d) - core, 0.0) / soft, 0.0, 1.0);
                float fall = d < 0.0 ? 0.35 * exp(d / fin) : 0.25 * exp(-d / fout);
                edge = max(rm, fall) * clamp((0.995 * R - r) / (0.01 * R), 0.0, 1.0);
                float sm = smoothstep(-0.33 * R, 0.0, d);
                inner = d < 0.0 ? pc.glow + 0.4 * sm * sm : 0.0;
                wh = fout * 2.0;
                if (e.x >= 0.0 && kind == 1) f = fillf(e.x * 0.97 - r);
            }
            cover = (d < 0.0 ? 1.0 : exp(-d / wh)) * ends;
            light = max(edge, inner * ends) * s.z + f * pc.fill_e * (s.z > 0.0 ? 1.0 : 0.0);
        }

        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (p.x >= int(pc.size.x) || p.y >= int(pc.size.y)) return;
            vec2 uv = (vec2(p) + 0.5) / pc.size;
            float dz = texture(depth, uv).r;
            vec4 v = mt.inv_proj * vec4(uv * 2.0 - 1.0, dz, 1.0);
            v.xyz /= v.w;
            vec3 wp = (mt.cam * vec4(v.xyz, 1.0)).xyz, eye = mt.cam[3].xyz;
            vec3 ray = normalize(wp - eye);
            if (dz <= 1e-7) wp = eye + ray * 1e4;
            // under the still water's line (its bed, a leg in the river): the surface seen there instead
            bool wet = pc.water_on > 0.5 && wp.y < pc.water_y - 0.01 && ray.y < -1e-4;
            if (wet) wp = eye + ray * ((pc.water_y - eye.y) / ray.y);
            float up = 1.0;
            if (pc.has_n > 0.5 && !wet) {
                vec3 nv = texture(nrm, uv).xyz * 2.0 - 1.0;
                up = (mt.cam * vec4(nv, 0.0)).y / max(length(nv), 1e-4);
            }
            float tint = 0.0, kk = pc.k;
            float light = 0.0;
            int n = int(pc.n);
            for (int i = 0; i < n; i++) {
                vec4 a = mk.m[i * 4], ax = mk.m[i * 4 + 1], s = mk.m[i * 4 + 2], e = mk.m[i * 4 + 3];
                vec3 q = wp;
                float gate;
                vec2 d = q.xz - a.xz;
                vec2 l = vec2(dot(d, ax.xy), dot(d, ax.zw));
                bool inbox = abs(l.x) <= s.x && abs(l.y) <= s.y;
                float gh = 0.0;
                if (inbox) {
                    float gy = ground(int(e.z + 0.5), l / s.xy);
                    if (pc.water_on > 0.5) gy = max(gy, pc.water_y);
                    gh = wet ? 0.0 : q.y - gy;
                }
                if (inbox && gh < pc.roof) {
                    // the ground (and grass, a pebble): full to g0 over it; past a few cm only what faces up
                    gate = (1.0 - smoothstep(pc.g0, pc.g1, gh)) * (1.0 - smoothstep(0.15, 0.4, -gh));
                    gate *= mix(1.0, smoothstep(0.3, 0.6, up), smoothstep(0.04, 0.12, gh));
                } else if (e.w > 0.5 && ray.y < -1e-4 && up > 0.5) {
                    // a roof or a canopy over it: the mark where the ground under it would be seen
                    vec3 g = eye + ray * ((a.y - eye.y) / ray.y);
                    if (dot(g - eye, ray) - dot(wp - eye, ray) < pc.roof) continue;
                    d = g.xz - a.xz;
                    l = vec2(dot(d, ax.xy), dot(d, ax.zw));
                    if (abs(l.x) > s.x || abs(l.y) > s.y) continue;
                    gate = smoothstep(0.5, 0.7, up);
                } else continue;
                if (gate <= 0.0) continue;
                float c, li;
                shape(i, l, c, li);
                if (pc.cal > 0.5) {
                    // (calibration: stripes 0.25 m across the lane, tinted and not; k in four steps along it)
                    if (fract(l.x / 0.25) >= 0.5) c = 0.0;
                    kk = 0.6 + 0.4 * floor(clamp((l.y + s.y) / (2.0 * s.y), 0.0, 0.999) * 4.0);
                    li = 0.0;
                }
                tint = max(tint, c * gate * s.w);
                light += li * gate;
            }
            if (tint <= 0.0 && light <= 0.0) return;
            vec4 col = imageLoad(colour, p);
            float lum = dot(col.rgb, vec3(0.2126, 0.7152, 0.0722));
            float val = mix(lum, max(col.r, max(col.g, col.b)), pc.w);
            // (AgX's toe darkens a lone red more than grey: dk lifts the dark ground's bed, full below dv)
            float kd = pc.cal > 0.5 ? kk : kk * (1.0 + pc.dk * (1.0 - smoothstep(0.0, 1.0, log2(max(val, 1e-5) / pc.dv) / 4.0 + 0.0)));
            vec3 bed = val * kd * vec3(1.0, pc.tg, pc.tb);
            col.rgb = mix(col.rgb, bed, clamp(tint, 0.0, 1.0)) + light * vec3(1.0, pc.hg, pc.hb);
            imageStore(colour, p, col);
        }
        """;
}
