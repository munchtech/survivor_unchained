namespace SurvivorUnchained.View;

/// <summary>The compute passes of the painterly post-filter (Brush, BrushEffect): the structure tensor and
/// its flow at half resolution, an anisotropic Kuwahara (Kyprianidis et al. 2009/2011, polynomial sector
/// weights) at full, and the stroke texture: a line integral of world-anchored noise along the flow.
/// Statistics and means are taken on a tonemapped proxy (c / (1 + c)) so bright pools don't dominate.</summary>
static class BrushShaders
{
    const string Head = """
        #version 450
        layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;
        layout(push_constant, std430) uniform P {
            vec2 size; vec2 hsize;
            float radius; float q; float hard; float strength;
            float tex; float len; float wid; float ang;
            float pxk; float ortho; float feather; float dbg;
        } pc;
        vec3 proxy(vec3 c) { c = max(c, vec3(0.0)); return c / (1.0 + c); }
        """;

    /// <summary>Half resolution: Sobel gradients of the proxy (bilinear taps on the full image, a 2x2
    /// prefilter for free) into the tensor (E, F, G).</summary>
    public const string Tensor = Head + """
        layout(set = 0, binding = 0) uniform sampler2D colour;
        layout(set = 0, binding = 1, rgba16f) uniform writeonly image2D tens;
        vec3 at(vec2 uv, float x, float y) { return proxy(texture(colour, uv + vec2(x, y) / pc.hsize).rgb); }
        void main() {
            ivec2 g = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(g, ivec2(pc.hsize)))) return;
            vec2 uv = (vec2(g) + 0.5) / pc.hsize;
            vec3 a = at(uv, -1, -1), b = at(uv, 0, -1), c = at(uv, 1, -1);
            vec3 d = at(uv, -1, 0), f = at(uv, 1, 0);
            vec3 h = at(uv, -1, 1), i = at(uv, 0, 1), j = at(uv, 1, 1);
            vec3 gx = (c + 2.0 * f + j) - (a + 2.0 * d + h);
            vec3 gy = (h + 2.0 * i + j) - (a + 2.0 * b + c);
            imageStore(tens, g, vec4(dot(gx, gx), dot(gx, gy), dot(gy, gy), 1.0));
        }
        """;

    /// <summary>Half resolution: the tensor smoothed (Gaussian, sigma 1.5 half pixels), then its
    /// tangent (the flow along edges), anisotropy A, and the stroke flow's confidence.</summary>
    public const string Flow = Head + """
        layout(set = 0, binding = 0) uniform sampler2D tens;
        layout(set = 0, binding = 1, rgba16f) uniform writeonly image2D flow;
        void main() {
            ivec2 g = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(g, ivec2(pc.hsize)))) return;
            vec3 s = vec3(0.0); float ws = 0.0;
            for (int y = -3; y <= 3; y++) for (int x = -3; x <= 3; x++) {
                float w = exp(-float(x * x + y * y) / 4.5);
                s += texelFetch(tens, clamp(g + ivec2(x, y), ivec2(0), ivec2(pc.hsize) - 1), 0).xyz * w; ws += w;
            }
            s /= ws;
            float E = s.x, F = s.y, G = s.z;
            float D = sqrt((E - G) * (E - G) + 4.0 * F * F);
            float l1 = 0.5 * (E + G + D), l2 = 0.5 * (E + G - D);
            vec2 v1 = vec2(-F, E - l2), v2 = vec2(G - l2, -F);
            vec2 t = dot(v1, v1) > dot(v2, v2) ? v1 : v2;
            t = dot(t, t) > 1e-20 ? normalize(t) : vec2(0.0, 1.0);
            float A = (l1 + l2) > 1e-9 ? (l1 - l2) / (l1 + l2) : 0.0;
            float conf = clamp(A * 1.5, 0.0, 1.0) * smoothstep(4e-4, 4e-3, l1);
            imageStore(flow, g, vec4(t, A, conf));
        }
        """;

    /// <summary>Full resolution: the anisotropic Kuwahara on the proxy, eight sectors with polynomial
    /// weights, taps in symmetric pairs. Writes the proxy result and her (dilated) coverage in alpha;
    /// her own pixels are skipped.</summary>
    public const string Kuwahara = Head + """
        layout(set = 0, binding = 0) uniform sampler2D colour;
        layout(set = 0, binding = 1) uniform sampler2D flow;
        layout(set = 0, binding = 2) uniform sampler2D mask;
        layout(set = 0, binding = 3, rgba16f) uniform writeonly image2D kout;
        // Her coverage: the mask's alpha, or any colour at all (her hair's erasers multiply the alpha
        // away under her hair and brows, for FSR 2's reactive mask; the background is exact black).
        float cov(vec2 uv) { vec4 c = texture(mask, uv); return max(c.a * 4.0, max(c.r, max(c.g, c.b)) * 128.0); }
        float her(vec2 uv) {
            vec2 d = pc.feather / pc.size, e = d * 0.7071;
            float m = cov(uv);
            m = max(m, max(max(cov(uv + vec2(d.x, 0)), cov(uv - vec2(d.x, 0))), max(cov(uv + vec2(0, d.y)), cov(uv - vec2(0, d.y)))));
            m = max(m, max(max(cov(uv + e), cov(uv - e)), max(cov(uv + vec2(e.x, -e.y)), cov(uv + vec2(-e.x, e.y)))));
            return clamp(m, 0.0, 1.0);
        }
        void main() {
            ivec2 g = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(g, ivec2(pc.size)))) return;
            vec2 uv = (vec2(g) + 0.5) / pc.size;
            float h = her(uv);
            if (h >= 0.999) { imageStore(kout, g, vec4(0.0, 0.0, 0.0, 1.0)); return; }
            vec4 t = texture(flow, uv);
            float r = pc.radius;
            float a = r * clamp(1.0 + t.z, 0.1, 2.0), b = r * clamp(1.0 / (1.0 + t.z), 0.1, 2.0);
            float cp = t.x, sp = t.y;
            mat2 SR = mat2(0.5 / a, 0.0, 0.0, 0.5 / b) * mat2(cp, -sp, sp, cp);
            int mx = int(sqrt(a * a * cp * cp + b * b * sp * sp));
            int my = int(sqrt(a * a * sp * sp + b * b * cp * cp));
            float zeta = 1.0 / max(r, 1.0);
            const float zc = 0.58;
            float eta = (zeta + cos(zc)) / (sin(zc) * sin(zc));
            vec4 m[8]; vec3 s[8];
            vec3 c = proxy(texture(colour, uv).rgb);
            for (int k = 0; k < 8; k++) { m[k] = vec4(c * 0.125, 0.125); s[k] = c * c * 0.125; }
            vec2 px = 1.0 / pc.size;
            for (int y = 0; y <= my; y++) {
                for (int x = -mx; x <= mx; x++) {
                    if (y == 0 && x <= 0) continue;
                    vec2 v = SR * vec2(x, y);
                    if (dot(v, v) > 0.25) continue;
                    vec3 c0 = proxy(texture(colour, uv + vec2(x, y) * px).rgb);
                    vec3 c1 = proxy(texture(colour, uv - vec2(x, y) * px).rgb);
                    float w[8]; float sum = 0.0, z, vxx, vyy;
                    vxx = zeta - eta * v.x * v.x; vyy = zeta - eta * v.y * v.y;
                    z = max(0.0, v.y + vxx); w[0] = z * z; sum += w[0];
                    z = max(0.0, -v.x + vyy); w[2] = z * z; sum += w[2];
                    z = max(0.0, -v.y + vxx); w[4] = z * z; sum += w[4];
                    z = max(0.0, v.x + vyy); w[6] = z * z; sum += w[6];
                    vec2 u = 0.70710678 * vec2(v.x - v.y, v.x + v.y);
                    vxx = zeta - eta * u.x * u.x; vyy = zeta - eta * u.y * u.y;
                    z = max(0.0, u.y + vxx); w[1] = z * z; sum += w[1];
                    z = max(0.0, -u.x + vyy); w[3] = z * z; sum += w[3];
                    z = max(0.0, -u.y + vxx); w[5] = z * z; sum += w[5];
                    z = max(0.0, u.x + vyy); w[7] = z * z; sum += w[7];
                    float gk = exp(-3.125 * dot(v, v)) / max(sum, 1e-12);
                    vec3 cc0 = c0 * c0, cc1 = c1 * c1;
                    for (int k = 0; k < 8; k++) {
                        float wk = w[k] * gk;
                        m[k] += vec4(c0 * wk, wk); s[k] += cc0 * wk;
                        m[(k + 4) & 7] += vec4(c1 * wk, wk); s[(k + 4) & 7] += cc1 * wk;
                    }
                }
            }
            vec4 o = vec4(0.0);
            for (int k = 0; k < 8; k++) {
                vec3 mu = m[k].rgb / m[k].w;
                vec3 sg = abs(s[k] / m[k].w - mu * mu);
                float sig = min(pc.hard * 1000.0 * (sg.r + sg.g + sg.b), 1e4);
                float wk = 1.0 / (1.0 + pow(sig, 0.5 * pc.q));
                o += vec4(mu * wk, wk);
            }
            imageStore(kout, g, vec4(o.rgb / max(o.w, 1e-30), h));
        }
        """;

    /// <summary>Full resolution: the stroke texture (noise seeded from the world position rebuilt from
    /// depth, at two world octaves blended so it keeps one screen scale, integrated along the flow),
    /// and the blend back over the frame outside her.</summary>
    public const string Final = Head + """
        layout(set = 0, binding = 0, rgba16f) uniform image2D colour;
        layout(set = 0, binding = 1) uniform sampler2D kuw;
        layout(set = 0, binding = 2) uniform sampler2D flow;
        layout(set = 0, binding = 3) uniform sampler2D depth;
        layout(set = 0, binding = 4, std140) uniform M { mat4 inv_proj; mat4 cam; } mt;
        uvec3 pcg(uvec3 v) {
            v = v * 1664525u + 1013904223u;
            v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
            v ^= v >> 16u;
            v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
            return v;
        }
        float hash(ivec3 p) { return float(pcg(uvec3(p)).x) * (1.0 / 4294967295.0); }
        float vnoise(vec3 x) {
            ivec3 i = ivec3(floor(x)); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
            float a = mix(hash(i), hash(i + ivec3(1, 0, 0)), f.x);
            float b = mix(hash(i + ivec3(0, 1, 0)), hash(i + ivec3(1, 1, 0)), f.x);
            float c = mix(hash(i + ivec3(0, 0, 1)), hash(i + ivec3(1, 0, 1)), f.x);
            float d = mix(hash(i + ivec3(0, 1, 1)), hash(i + ivec3(1, 1, 1)), f.x);
            return mix(mix(a, b, f.y), mix(c, d, f.y), f.z);
        }
        bool world(vec2 uv, out vec3 wp, out float fp) {
            float dz = texture(depth, uv).r;
            vec4 v = mt.inv_proj * vec4(uv * 2.0 - 1.0, dz, 1.0);
            v.xyz /= v.w;
            wp = (mt.cam * vec4(v.xyz, 1.0)).xyz;
            fp = (pc.ortho > 0.5 ? 1.0 : -v.z) * pc.pxk;
            return dz > 1e-7 || pc.ortho > 0.5;
        }
        float noise_at(vec2 uv) {
            vec3 wp; float fp;
            if (!world(uv, wp, fp)) return 0.5;
            float l = log2(max(pc.wid * fp, 1e-5)), l0 = floor(l), f = l - l0, s0 = exp2(l0);
            float n = mix(vnoise(wp / s0), vnoise(wp / (2.0 * s0) + 19.19), f);
            return 0.5 + (n - 0.5) / sqrt(f * f + (1.0 - f) * (1.0 - f));
        }
        vec2 dir_at(vec2 uv, vec2 fixd) {
            vec4 t = texture(flow, uv);
            vec2 d = t.xy; if (dot(d, fixd) < 0.0) d = -d;
            d = mix(fixd, d, t.w);
            return dot(d, d) > 1e-12 ? normalize(d) : fixd;
        }
        float strokes(vec2 uv) {
            vec2 fixd = vec2(cos(pc.ang), -sin(pc.ang));
            int n = max(int(pc.len * 0.5 + 0.5), 1);
            float sig = max(pc.len * 0.25, 0.5);
            float acc = noise_at(uv), ws = 1.0;
            vec2 d0 = dir_at(uv, fixd);
            for (int sg = -1; sg <= 1; sg += 2) {
                vec2 p = uv, v = d0 * float(sg);
                for (int k = 1; k <= n; k++) {
                    p += v / pc.size;
                    float wk = exp(-float(k * k) / (2.0 * sig * sig));
                    acc += noise_at(p) * wk; ws += wk;
                    vec2 nv = dir_at(p, fixd); if (dot(nv, v) < 0.0) nv = -nv; v = nv;
                }
            }
            return (acc / ws - 0.5) * 5.0;
        }
        void main() {
            ivec2 g = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(g, ivec2(pc.size)))) return;
            vec4 kk = texelFetch(kuw, g, 0);
            int dbg = int(pc.dbg + 0.5);
            if (kk.a >= 0.999 && dbg != 1) return;
            vec2 uv = (vec2(g) + 0.5) / pc.size;
            vec4 c = imageLoad(colour, g);
            float st = (pc.tex > 0.0 || dbg == 3) ? strokes(uv) : 0.0;
            vec3 pp = clamp(kk.rgb * (1.0 + pc.tex * st), vec3(0.0), vec3(0.998));
            vec3 painted = pp / (1.0 - pp);
            vec3 o = mix(c.rgb, painted, pc.strength * (1.0 - kk.a));
            if (dbg == 1) o = mix(c.rgb, vec3(1.0, 0.0, 0.0), kk.a);
            else if (dbg == 2) { vec3 wp; float fp; world(uv, wp, fp); o = fract(wp); }
            else if (dbg == 3) o = vec3(0.18 * (1.0 + 0.5 * st));
            else if (dbg == 4) o = mix(c.rgb, kk.rgb / (1.0 - min(kk.rgb, vec3(0.998))), 1.0 - kk.a);
            imageStore(colour, g, vec4(o, c.a));
        }
        """;
}
