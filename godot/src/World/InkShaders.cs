namespace SurvivorUnchained.View;

/// <summary>The ink line's compute shader (InkPass): one pass on the linear HDR frame after the transparent pass (its darkening the
/// frame's before that pass, InkSnap's copy, so effects carry none: rule 8),
/// before TAA, the tonemap and the grade. A 16 x 16 tile loads its view-space positions (and the ink class) with a
/// 6 px apron into shared memory and reconstructs normals from depth; then each pixel takes its silhouette (a
/// neighbor within the line's radius lying behind this pixel's tangent plane: drawn on the near side only) and its
/// crease (the reconstructed normals turning by more than the crease angle, classes 0 and 3 only) as coverage by
/// distance, so the line's edge is fractional (TAA's jitter resolves the rest).</summary>
public static class InkShaders
{
    public const string Line = """
        #version 450
        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;
        layout(set = 0, binding = 0, rgba16f) uniform image2D colour;
        layout(set = 0, binding = 1) uniform sampler2D depth_tex;
        layout(set = 0, binding = 2) uniform sampler2D nr_tex;
        layout(set = 0, binding = 3, std140) uniform M { mat4 inv_proj; vec4 rig; vec4 fog; vec4 fog2; vec4 opt; } mt;
        layout(set = 0, binding = 4) uniform sampler2D pre_tex; // the frame before the transparent pass (InkSnap; opt.x 1)
        layout(push_constant, std430) uniform P {
            vec2 size; float r_close; float r_play;
            float th_a; float th_b; float crease_cos; float has_nr;
            float fade_near; float fade_far; float dbg; float lum_cut;
            float z_close; float z_play; float crease_w; float sil_thin;
        } pc;

        const int T = 16, A = 6, S = T + 2 * A, NA = 3, NS = T + 2 * NA;
        shared vec4 sp[S * S];   // view position; w: the ink class (0-3; the raw code in dbg 3), -1 the sky
        shared vec4 sn[NS * NS]; // the reconstructed normal (toward the camera)

        vec4 P_(ivec2 q) { return sp[q.y * S + q.x]; }
        vec3 N_(ivec2 q) { return sn[q.y * NS + q.x].xyz; }

        const ivec2 DIRS[8] = ivec2[8](ivec2(1, 0), ivec2(-1, 0), ivec2(0, 1), ivec2(0, -1), ivec2(1, 1), ivec2(-1, 1), ivec2(1, -1), ivec2(-1, -1));

        void main() {
            ivec2 isz = ivec2(pc.size);
            ivec2 base = ivec2(gl_WorkGroupID.xy) * T - A;
            int li = int(gl_LocalInvocationIndex);
            for (int i = li; i < S * S; i += T * T) {
                ivec2 p = clamp(base + ivec2(i % S, i / S), ivec2(0), isz - 1);
                float d = texelFetch(depth_tex, p, 0).r;
                vec2 ndc = (vec2(p) + 0.5) / pc.size * 2.0 - 1.0;
                vec4 v = mt.inv_proj * vec4(ndc, d, 1.0);
                v.xyz /= v.w;
                float cls = 0.0;
                if (pc.has_nr > 0.5) {
                    // Godot 4.5.1 (scene_forward_clustered.glsl): alpha = roughness x 127/255, 1 - that on a dynamic instance.
                    uint b = uint(round(texelFetch(nr_tex, p, 0).a * 255.0));
                    uint n = b <= 127u ? b : 255u - b;
                    cls = (pc.dbg > 2.5 && pc.dbg < 3.5) ? float(n) + (b > 127u ? 128.0 : 0.0) : float(n & 3u);
                }
                sp[i] = vec4(v.xyz, d <= 0.0 ? -1.0 : cls);
            }
            barrier();
            for (int i = li; i < NS * NS; i += T * T) {
                ivec2 q = ivec2(i % NS, i / NS) + (A - NA);
                vec3 c = P_(q).xyz, l = P_(q - ivec2(1, 0)).xyz, r = P_(q + ivec2(1, 0)).xyz;
                vec3 u = P_(q - ivec2(0, 1)).xyz, w = P_(q + ivec2(0, 1)).xyz;
                vec3 dx = abs(c.z - l.z) < abs(r.z - c.z) ? c - l : r - c;
                vec3 dy = abs(c.z - u.z) < abs(w.z - c.z) ? c - u : w - c;
                vec3 n = cross(dx, dy);
                float ln = length(n);
                n = ln > 1e-12 ? n / ln : vec3(0.0, 0.0, 1.0);
                if (dot(n, c) > 0.0) n = -n;
                sn[i] = vec4(n, 0.0);
            }
            barrier();
            ivec2 px = ivec2(gl_GlobalInvocationID.xy);
            if (px.x >= isz.x || px.y >= isz.y) return;
            ivec2 lp = ivec2(gl_LocalInvocationID.xy), q = lp + A, qn = lp + NA;
            vec4 c = P_(q);
            vec4 col = imageLoad(colour, px);
            if (c.w < 0.0) { if (pc.dbg > 0.5) imageStore(colour, px, vec4(0.0, 0.0, 0.0, col.a)); return; }
            if (pc.dbg > 2.5 && pc.dbg < 3.5) { // the raw code: n/127 grey, red where the instance is dynamic
                float n = mod(c.w, 128.0);
                imageStore(colour, px, vec4(c.w >= 128.0 ? 1.0 : n / 127.0, n / 127.0, c.w >= 128.0 ? 0.0 : n / 127.0, col.a));
                return;
            }
            // The class: the nearest-depth pixel's of the 3 x 3 (an MSAA edge's resolved code may be the far sample's).
            float cls = c.w, best = -1e30;
            for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
                vec4 s = P_(q + ivec2(x, y));
                if (s.w >= 0.0 && s.z > best) { best = s.z; cls = s.w; }
            }
            if (pc.dbg > 1.5 && pc.dbg < 2.5) {
                vec3 k = cls < 0.5 ? vec3(1.0) : cls < 1.5 ? vec3(1.0, 1.0, 0.0) : cls < 2.5 ? vec3(0.0, 0.2, 1.0) : vec3(1.0, 0.0, 0.0);
                imageStore(colour, px, vec4(k, col.a));
                return;
            }
            float line = 0.0;
            float z = -c.z, dist = length(c.xyz);
            if (cls < 1.5 || cls > 2.5) {
                vec3 N = N_(qn);
                float r = mix(pc.r_close, pc.r_play, smoothstep(pc.z_close, pc.z_play, z));
                float th = max(pc.th_a, pc.th_b * z);
                int K = min(int(ceil(r + 1.0)), A);
                // The silhouette: a neighbor behind this pixel's tangent plane (the line thicker the deeper the drop).
                for (int j = 0; j < 8; j++) {
                    float len = j < 4 ? 1.0 : 1.41421356;
                    for (int k = 1; k <= K; k++) {
                        float d = float(k) * len;
                        if (d > r + 1.0) break;
                        vec4 s = P_(q + DIRS[j] * k);
                        float gap = s.w < 0.0 ? 1e9 : dot(c.xyz - s.xyz, N);
                        float w = smoothstep(th, th * 1.5, gap);
                        if (w <= 0.0) continue;
                        float f = mix(pc.sil_thin, 1.0, smoothstep(th * 2.0, th * 12.0, gap));
                        line = max(line, w * clamp(r * f + 1.0 - d, 0.0, 1.0));
                    }
                }
                // The crease (classes 0 and 3): the surface folding by more than the crease angle.
                if (cls < 0.5 || cls > 2.5) {
                    float rc = r * pc.crease_w;
                    int Kc = min(int(ceil(rc + 1.0)), NA);
                    for (int j = 0; j < 8; j++) {
                        float len = j < 4 ? 1.0 : 1.41421356;
                        for (int k = 1; k <= Kc; k++) {
                            float d = float(k) * len;
                            if (d > rc + 1.0) break;
                            ivec2 o = DIRS[j] * k;
                            vec4 s = P_(q + o);
                            if (s.w < 0.0 || abs(dot(c.xyz - s.xyz, N)) > th) continue;
                            float cs = dot(N, N_(qn + o));
                            float w = 1.0 - smoothstep(pc.crease_cos - 0.08, pc.crease_cos + 0.08, cs);
                            line = max(line, w * clamp(rc + 1.0 - d, 0.0, 1.0));
                        }
                    }
                }
            }
            // Weaker with distance and the fog (the far background stays painted), and off the emissive.
            float a = line * (1.0 - smoothstep(pc.fade_near, pc.fade_far, dist));
            float fogk = 0.0;
            if (mt.fog.x > 1.5) fogk = pow(smoothstep(mt.fog.z, mt.fog.w, dist), mt.fog2.x) * mt.fog.y;
            else if (mt.fog.x > 0.5) fogk = 1.0 - exp(-dist * mt.fog.y);
            a *= (1.0 - clamp(fogk, 0.0, 1.0)) * exp(-min(dist, mt.fog2.z) * mt.fog2.y);
            float lum = dot(col.rgb, vec3(0.2126, 0.7152, 0.0722));
            a *= 1.0 - smoothstep(pc.lum_cut * 0.75, pc.lum_cut * 1.25, lum);
            if (pc.dbg > 3.5) { imageStore(colour, px, vec4(vec3(a), col.a)); return; } // "lines": before the effects' mask
            vec3 ink = mix(vec3(1.0), mt.rig.rgb * mt.rig.w, a);
            vec3 outc = col.rgb * ink;
            // Under the effects (rule 8): the darkening is the opaque frame's (pre x (1 - ink)), taken off the final
            // frame, never more than today's multiply. Opaque pixels (post = pre) are as before; an additive effect is
            // exact (pre x ink + fx); her blended hair over its own solid core (post ~ pre) keeps its line.
            if (mt.opt.x > 0.5) outc = max(col.rgb - texelFetch(pre_tex, px, 0).rgb * (1.0 - ink), outc);
            if (pc.dbg > 0.5) { // "edges": the line as drawn (the darkening's share of a full line)
                float full = dot(col.rgb * (1.0 - ink), vec3(0.2126, 0.7152, 0.0722));
                float got = dot(col.rgb - outc, vec3(0.2126, 0.7152, 0.0722));
                imageStore(colour, px, vec4(vec3(full > 1e-6 ? a * clamp(got / full, 0.0, 1.0) : a), col.a)); return;
            }
            if (a <= 0.0) return;
            col.rgb = outc;
            imageStore(colour, px, col);
        }
        """;

    /// <summary>(--ink-test) the normal_roughness alpha bytes into a buffer, one uint per pixel, for a readback.</summary>
    public const string Probe = """
        #version 450
        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;
        layout(set = 0, binding = 0) uniform sampler2D nr_tex;
        layout(set = 0, binding = 1, std430) restrict writeonly buffer B { uint px[]; } ob;
        layout(push_constant, std430) uniform P { vec2 size; vec2 pad; } pc;
        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (p.x >= int(pc.size.x) || p.y >= int(pc.size.y)) return;
            ob.px[p.y * int(pc.size.x) + p.x] = uint(round(texelFetch(nr_tex, p, 0).a * 255.0));
        }
        """;
}
