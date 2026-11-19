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
        layout(set = 0, binding = 3, std140) uniform M { mat4 inv_proj; vec4 rig; vec4 fog; vec4 fog2; vec4 opt; vec4 wt; vec4 wo; vec4 wc; vec4 wr; vec4 wm; vec4 pt; } mt;
        layout(set = 0, binding = 4) uniform sampler2D pre_tex; // the frame before the transparent pass (InkSnap; opt.x 1)
        layout(push_constant, std430) uniform P {
            vec2 size; float r_close; float r_play;
            float th_a; float th_b; float crease_cos; float has_nr;
            float fade_near; float fade_far; float dbg; float lum_cut;
            float z_close; float z_play; float crease_w; float sil_thin;
        } pc;

        // (lane J lead 9) Oklab, for the stroke marks' hue turn in the frame (linear rgb in)
        vec3 OK(vec3 c) {
            c = max(c, vec3(0.0));
            vec3 l = vec3(0.4122214708 * c.r + 0.5363325363 * c.g + 0.0514459929 * c.b, 0.2119034982 * c.r + 0.6806995451 * c.g + 0.1073969566 * c.b,
                0.0883024619 * c.r + 0.2817188376 * c.g + 0.6299787005 * c.b);
            l = pow(l, vec3(1.0 / 3.0));
            return vec3(0.2104542553 * l.x + 0.7936177850 * l.y - 0.0040720468 * l.z, 1.9779984951 * l.x - 2.4285922050 * l.y + 0.4505937099 * l.z,
                0.0259040371 * l.x + 0.7827717662 * l.y - 0.8086757660 * l.z);
        }
        vec3 RGB(vec3 l) {
            vec3 q = vec3(l.x + 0.3963377774 * l.y + 0.2158037573 * l.z, l.x - 0.1055613458 * l.y - 0.0638541728 * l.z, l.x - 0.0894841775 * l.y - 1.2914855480 * l.z);
            q = q * q * q;
            return max(vec3(4.0767416621 * q.x - 3.3077115913 * q.y + 0.2309699292 * q.z, -1.2684380046 * q.x + 2.6097574011 * q.y - 0.3413193965 * q.z,
                -0.0041960863 * q.x - 0.7034186147 * q.y + 1.7076147010 * q.z), vec3(0.0));
        }
        // The lit pixel's hue turned by deg (its value kept), its chroma times cs, at least cmin; k: the share (fog takes it back)
        vec3 TURN(vec3 c, float deg, float cmin, float cs, float k) {
            vec3 l = OK(c);
            float c0 = length(l.yz);
            float a = radians(deg * k), ca = cos(a), sa = sin(a);
            vec2 ab = vec2(l.y * ca - l.z * sa, l.y * sa + l.z * ca);
            float c1 = mix(c0, max(c0 * cs, cmin), k);
            ab = (c0 > 1e-4 ? ab / c0 : vec2(cos(radians(deg)), sin(radians(deg)))) * c1;
            return RGB(vec3(l.x, ab));
        }

        const int T = 16, A = 6, S = T + 2 * A, NA = 3, NS = T + 2 * NA;
        shared vec4 sp[S * S];   // view position; w: the ink class (0-3; the raw code in dbg 3), -1 the sky
        shared vec4 sn[NS * NS]; // the reconstructed normal (toward the camera)

        vec4 P_(ivec2 q) { return sp[q.y * S + q.x]; }
        vec3 N_(ivec2 q) { return sn[q.y * NS + q.x].xyz; }

        const ivec2 DIRS[8] = ivec2[8](ivec2(1, 0), ivec2(-1, 0), ivec2(0, 1), ivec2(0, -1), ivec2(1, 1), ivec2(-1, 1), ivec2(1, -1), ivec2(-1, -1));
        const int OPP[8] = int[8](1, 0, 3, 2, 7, 6, 5, 4);
        // (lane J lead 6) a view position straight from the depth (past the tile's apron), w -1 the sky
        vec4 VP(ivec2 p) {
            p = clamp(p, ivec2(0), ivec2(pc.size) - 1);
            float d = texelFetch(depth_tex, p, 0).r;
            vec2 ndc = (vec2(p) + 0.5) / pc.size * 2.0 - 1.0;
            vec4 v = mt.inv_proj * vec4(ndc, d, 1.0);
            return vec4(v.xyz / v.w, d <= 0.0 ? -1.0 : 0.0);
        }

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
                    cls = (pc.dbg > 2.5 && pc.dbg < 3.5) ? float(n) + (b > 127u ? 128.0 : 0.0) : float(n & 3u) + (b <= 127u && mt.wo.x > 0.0 ? 4.0 : 0.0); // (+4: a static pixel, the world's ink)
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
            bool wd = cls > 3.5;   // (lane J lead 5) the world's ink: a static pixel, while the palette names one
            if (wd) cls -= 4.0;
            if (pc.dbg > 1.5 && pc.dbg < 2.5) {
                vec3 k = cls < 0.5 ? vec3(1.0) : cls < 1.5 ? vec3(1.0, 1.0, 0.0) : cls < 2.5 ? vec3(0.0, 0.2, 1.0) : vec3(1.0, 0.0, 0.0);
                imageStore(colour, px, vec4(k, col.a));
                return;
            }
            float line = 0.0;
            float z = -c.z, dist = length(c.xyz);
            float wcl = cls < 0.5 ? mt.wc.x : cls < 1.5 ? mt.wc.y : cls < 2.5 ? mt.wc.z : mt.wc.w;
            float wcr = cls < 0.5 ? mt.wr.x : cls < 1.5 ? mt.wr.y : cls < 2.5 ? mt.wr.z : mt.wr.w;
            bool sil = wd ? wcl > 0.0 : (cls < 1.5 || cls > 2.5);
            bool cre = wd ? wcr > 0.0 : (cls < 0.5 || cls > 2.5);
            if (sil || cre) {
                vec3 N = N_(qn);
                float r = wd ? mt.wo.x * wcl : mix(pc.r_close, pc.r_play, smoothstep(pc.z_close, pc.z_play, z));
                float th = max(pc.th_a, pc.th_b * z) * (wd ? mt.wm.y : 1.0);
                float thin = wd ? mt.wo.z : pc.sil_thin;
                int K = sil ? min(int(ceil(r + 1.0)), A) : 0;
                // (lane J lead 6, judge r4 cel fix 2: a thin prop went solid black, both its contours meeting) the world's
                // contour no wider than a share (wm.z) of the form's own width across, measured to its far edge (up to wm.w px)
                bool fit = wd && mt.wm.z > 0.0;
                // The silhouette: a neighbor behind this pixel's tangent plane (the line thicker the deeper the drop).
                for (int j = 0; j < 8; j++) {
                    float len = j < 4 ? 1.0 : 1.41421356;
                    float rj = r; bool probed = false;
                    for (int k = 1; k <= K; k++) {
                        float d = float(k) * len;
                        if (d > r + 1.0) break;
                        vec4 s = P_(q + DIRS[j] * k);
                        float gap = s.w < 0.0 ? 1e9 : dot(c.xyz - s.xyz, N);
                        float w = smoothstep(th, th * 1.5, gap);
                        if (w <= 0.0) continue;
                        float f = mix(thin, 1.0, smoothstep(th * 2.0, th * 12.0, gap));
                        if (fit && !probed) { probed = true;   // the far edge the other way: the form's width across this line
                            int o = OPP[j], Lm = int(mt.wm.w);
                            float wf = 1e9;
                            for (int m = 1; m <= Lm; m++) {
                                vec4 t = VP(px + DIRS[o] * m);
                                float g2 = t.w < 0.0 ? 1e9 : dot(c.xyz - t.xyz, N);
                                if (g2 > th) { wf = (float(m) + float(k) - 1.0) * len; break; }
                            }
                            rj = min(r, mt.wm.z * wf);
                        }
                        line = max(line, w * clamp(rj * f + 1.0 - d, 0.0, 1.0));
                    }
                }
                // The crease (classes 0 and 3): the surface folding by more than the crease angle.
                if (cre) {
                    float rc = wd ? mt.wo.x * mt.wo.y * wcr : r * pc.crease_w;
                    float ccos = wd ? mt.wm.x : pc.crease_cos;
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
                            float w = 1.0 - smoothstep(ccos - 0.08, ccos + 0.08, cs);
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
            float lc = wd ? mt.wo.w : pc.lum_cut;
            a *= 1.0 - smoothstep(lc * 0.75, lc * 1.25, lum);
            if (pc.dbg > 3.5 && pc.dbg < 4.5) { imageStore(colour, px, vec4(vec3(a), col.a)); return; } // "lines": before the effects' mask
            vec3 ink = mix(vec3(1.0), wd ? mt.wt.rgb * mt.wt.w : mt.rig.rgb * mt.rig.w, a);
            vec3 outc = col.rgb * ink;
            // Under the effects (rule 8): the darkening is the opaque frame's (pre x (1 - ink)), taken off the final
            // frame, never more than today's multiply. Opaque pixels (post = pre) are as before; an additive effect is
            // exact (pre x ink + fx); her blended hair over its own solid core (post ~ pre) keeps its line.
            if (mt.opt.x > 0.5) outc = max(col.rgb - texelFetch(pre_tex, px, 0).rgb * (1.0 - ink), outc);
            if (pc.dbg > 0.5 && pc.dbg < 4.5) { // "edges": the line as drawn (the darkening's share of a full line)
                float full = dot(col.rgb * (1.0 - ink), vec3(0.2126, 0.7152, 0.0722));
                float got = dot(col.rgb - outc, vec3(0.2126, 0.7152, 0.0722));
                imageStore(colour, px, vec4(vec3(full > 1e-6 ? a * clamp(got / full, 0.0, 1.0) : a), col.a)); return;
            }
            // (lane J lead 9, judge r7 strokes fix 1) The world's stroke marks (paint_stroke.gdshaderinc ps_tag: a static pixel's
            // roughness code r5 0 = a + mark, 1 = a - mark) take their hue turn HERE, on the lit frame, so the turn the eye sees is
            // the palette's ("frame" [deg +, deg -, cmin, cs]), not what light, grade and tonemap leave of an albedo turn.
            // Under the effects as the ink is: the turn is the opaque frame's (pre), added to the final.
            bool mk = false;
            if (mt.pt.w > 0.0 && pc.has_nr > 0.5) {
                uint mb = uint(round(texelFetch(nr_tex, px, 0).a * 255.0));
                if (mb <= 127u && (mb >> 2u) <= 1u) {
                    vec3 src = mt.opt.x > 0.5 ? texelFetch(pre_tex, px, 0).rgb : col.rgb;
                    if (a > 0.0) src *= ink;
                    float kf = (1.0 - clamp(fogk, 0.0, 1.0)) * (1.0 - smoothstep(pc.fade_near, pc.fade_far, dist));
                    vec3 d = TURN(src, (mb >> 2u) == 0u ? mt.pt.x : mt.pt.y, mt.pt.z, mt.pt.w, kf) - src;
                    if (pc.dbg > 4.5 && pc.dbg < 5.5) { imageStore(colour, px, vec4((mb >> 2u) == 0u ? vec3(1.0, 0.0, 1.0) : vec3(0.0, 1.0, 1.0), col.a)); return; }
                    outc = (a > 0.0 ? outc : col.rgb) + d;
                    mk = true;
                }
            }
            if (pc.dbg > 4.5 && pc.dbg < 5.5) { imageStore(colour, px, vec4(col.rgb * 0.25, col.a)); return; }   // (dbg 5 "marks": magenta +, cyan -)
            if (a <= 0.0 && !mk) return;
            col.rgb = max(outc, vec3(0.0));
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
