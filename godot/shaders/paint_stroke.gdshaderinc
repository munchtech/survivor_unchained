// (lane J lead 8, 19 Nov: art-paint-strokes) The world's painted stroke layer: one brush for every world surface.
// Judge r6: "every surface one flat fill = toon shader + outline". The reference paints small tapered strokes inside each
// flat field that follow the form. Ours are painted in Sunder's crescent language (FX_LANGUAGE §4 travel: a crescent with
// its head leading and a tail that tapers to a point, two-tone, the darker band on the inner, concave edge), and each
// mark turns its field's hue by +-ps_tone.x degrees at (nearly) the field's own value, so the value fields stay flat and
// the strokes read as colour, not noise. Day: an orange field gets crimson and gold marks; night: a blue field teal and violet.
// Data (logic/Look/Palettes.cs "stroke", rigs.json palettes, blended by the clock; Atmosphere.SetPalette):
//   ps_brush = (cell m, length m, width m, bend: the crescent's sagitta as a share of its length)
//   ps_tone  = (hue turn deg, value lift of a mark, inner edge value drop, chroma scale)
//   ps_cover0 = cover share per class (leaf, grass, ground, path), ps_cover1 = (stone, bark, hit amount, hit emission)
// A surface calls ps_paint(albedo, p2, flow2, cover, seed): p2 its 2D surface coords in metres (world-anchored, never
// screen), flow2 the unit direction the marks run in those coords (along the form). Cost: 2 layers x 2x2 cells, ALU only.
// Keep length * 1.3 <= 1.15 * cell (a longer mark is cut square by the 2x2 search).
// Off (all zero data, or --pal off): ps_paint returns the albedo untouched.
#ifndef PAINT_STROKE_INC
#define PAINT_STROKE_INC
#define PS_BARE 0.36   // (lead 9) the share of patches left bare

global uniform vec4 ps_brush;
global uniform vec4 ps_tone;
global uniform vec4 ps_cover0;
global uniform vec4 ps_cover1;
global uniform vec4 ps_hitc;
global uniform vec4 ps_hite;

float ps_h(vec2 p) { p = fract(p * vec2(0.1031, 0.1030)); p += dot(p, p.yx + 33.33); return fract((p.x + p.y) * p.x); }

vec3 ps_lab(vec3 c) {
	c = max(c, vec3(0.0));
	vec3 lms = vec3(0.4122214708 * c.r + 0.5363325363 * c.g + 0.0514459929 * c.b,
			0.2119034982 * c.r + 0.6806995451 * c.g + 0.1073969566 * c.b,
			0.0883024619 * c.r + 0.2817188376 * c.g + 0.6299787005 * c.b);
	lms = pow(lms, vec3(1.0 / 3.0));
	return vec3(0.2104542553 * lms.x + 0.7936177850 * lms.y - 0.0040720468 * lms.z,
			1.9779984951 * lms.x - 2.4285922050 * lms.y + 0.4505937099 * lms.z,
			0.0259040371 * lms.x + 0.7827717662 * lms.y - 0.8086757660 * lms.z);
}
vec3 ps_rgb(vec3 l) {
	vec3 q = vec3(l.x + 0.3963377774 * l.y + 0.2158037573 * l.z,
			l.x - 0.1055613458 * l.y - 0.0638541728 * l.z,
			l.x - 0.0894841775 * l.y - 1.2914855480 * l.z);
	q = q * q * q;
	return max(vec3(4.0767416621 * q.x - 3.3077115913 * q.y + 0.2309699292 * q.z,
			-1.2684380046 * q.x + 2.6097574011 * q.y - 0.3413193965 * q.z,
			-0.0041960863 * q.x - 0.7034186147 * q.y + 1.7076147010 * q.z), vec3(0.0));
}
// The field's colour turned by deg at value + dl, chroma times cs (Oklab; the value is Oklab L).
vec3 ps_turn(vec3 c, float deg, float dl, float cs) {
	vec3 l = ps_lab(c);
	float a = radians(deg), ca = cos(a), sa = sin(a);
	l.yz = vec2(l.y * ca - l.z * sa, l.y * sa + l.z * ca) * cs;
	// (the chroma floor ps_hitc.w: a near-grey field, a stone, still takes a coloured mark, in its own faint hue)
	float c0 = length(l.yz);
	if (c0 < ps_hitc.w) l.yz = (c0 > 1e-4 ? l.yz / c0 : vec2(ca, sa)) * ps_hitc.w;
	l.x = max(l.x + dl, 0.0);
	return ps_rgb(l);
}

// One crescent in its own frame: q.x along the flow (metres, 0 = the mark's centre), q.y across. Head leads (+x), round;
// the tail tapers to a point (-x). Returns (coverage, inner: the concave edge's darker band), antialiased over one pixel.
vec2 ps_mark(vec2 q, float len, float wid, float bend) {
	float t = q.x / len + 0.5;   // 0 tail .. 1 head
	if (t < -0.05 || t > 1.05) return vec2(0.0);
	float tc = clamp(t, 0.0, 1.0);
	float hw = 0.5 * wid * pow(tc, 0.85) * sqrt(clamp((1.0 - tc) / 0.22, 0.0, 1.0));
	float vc = bend * len * (1.0 - 4.0 * (tc - 0.5) * (tc - 0.5));
	float d = q.y - vc;
	float sd = abs(d) - hw;
	float fw = max(fwidth(sd), 1e-5);
	float cov = 1.0 - smoothstep(-fw, fw, sd);
	// the concave side is toward -y (the bend lifts the middle to +y): its outer third, a hard pixel edge
	float inn = (1.0 - smoothstep(-fw, fw, d + hw * 0.3)) * cov;
	return vec2(cov, inn);
}

// The strokes at p2 (metres) running along flow2: (coverage, inner, sign +-1 of the mark on top, the mark's hash).
vec4 ps_field(vec2 p2, vec2 flow2, float cover, float seed) {
	vec4 r = vec4(0.0);
	if (cover <= 0.0 || ps_brush.x <= 0.0) return r;
	float cell = ps_brush.x;
	vec2 fx = flow2, fy = vec2(-flow2.y, flow2.x);
	for (int layer = 0; layer < 2; layer++) {
		vec2 pl = p2 / cell + (layer == 1 ? vec2(0.5, 0.5) : vec2(0.0)) + seed * 17.0;
		vec2 base = floor(pl - 0.5);
		for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++) {
			vec2 c = base + vec2(float(i), float(j));
			vec2 ch = c + float(layer) * 41.3;
			float h0 = ps_h(ch);
			// (lead 9) patches of about 3.5 cells, their edges broken per cell: a share ps_brush... bare (no marks), the rest each its
			// own density, so the field is laid by a hand in passes, not stamped (cover varies tile to tile; 30-40% bare)
			vec2 pj = floor((c + vec2(ps_h(ch + 5.3), ps_h(ch + 9.1)) * 2.5) / 3.5);
			float hp = ps_h(pj * 1.7 + seed * 23.0);
			float cv = hp < PS_BARE ? 0.0 : cover * mix(0.55, 1.35, (hp - PS_BARE) / (1.0 - PS_BARE));
			if (h0 > cv) continue;
			float h1 = ps_h(ch + 7.7), h2 = ps_h(ch + 3.1), h3 = ps_h(ch + 11.9);
			// (the mark's centre within a quarter cell of its cell's: with len <= 1.15 cell no mark is cut by the 2x2 search)
			vec2 dq = (pl - (c + 0.5 + (vec2(h1, h2) - 0.5) * 0.5)) * cell;
			// along the flow, a few degrees off, so the field reads hand-laid, not combed
			float wob = (h3 - 0.5) * 0.35;
			vec2 ax = normalize(fx + fy * wob), ay = vec2(-ax.y, ax.x);
			float len = ps_brush.y * (0.36 + 0.97 * h2 * h2 * (3.0 - 2.0 * h2));   // (lead 9: p10:p90 ~2.7, was 1.6)
			vec2 m = ps_mark(vec2(dot(dq, ax), dot(dq, ay)), len, ps_brush.z * mix(0.8, 1.2, h1), ps_brush.w * (h3 < 0.5 ? 1.0 : -1.0));
			if (m.x > r.x) r = vec4(m.x, m.y, h1 < 0.5 ? -1.0 : 1.0, h0);
		}
	}
	return r;
}

// The painted field: albedo with its marks laid in. cover: this surface's share of cells holding a mark (its class's
// ps_cover). The + marks turn +deg and lift, the - marks turn -deg and sink, each by ps_tone.y; the inner band drops ps_tone.z.
// (lead 9, judge r7 strokes fix 1: the turn measured in the FRAME; set in albedo, light, grade and tonemap pulled it to +-8..20)
// code: +1 / -1 where a mark covers this pixel (> half), for ps_tag: InkPass turns the lit pixel's hue by the palette's
// "frame" [deg +, deg -, chroma floor, chroma scale] (ps_tone.x, the albedo turn, is 0 when the frame turns).
vec3 ps_paint_c(vec3 albedo, vec2 p2, vec2 flow2, float cover, float seed, inout float code) {
	vec4 f = ps_field(p2, flow2, cover, seed);
	if (f.x <= 0.0) return albedo;
	if (f.x > 0.5) code = f.z;
	vec3 mk = ps_turn(albedo, ps_tone.x * f.z, ps_tone.y * f.z - ps_tone.z * f.y, ps_tone.w);
	return mix(albedo, mk, f.x);
}
vec3 ps_paint(vec3 albedo, vec2 p2, vec2 flow2, float cover, float seed) { float c = 0.0; return ps_paint_c(albedo, p2, flow2, cover, seed, c); }
// The mark's code into ROUGHNESS (after cel_tag: n = r5 x 4 + ink class): a + mark r5 0, a - mark r5 1, no highlight (so the
// low roughness lights as before); every other pixel r5 >= 4 (rougher than 0.13: the world is matte). Off with the strokes.
void ps_tag(inout float rough, inout float spec, float code) {
	if (ps_brush.x <= 0.0) return;
	float n = round(rough * 127.0);
	float cls = mod(n, 4.0), r5 = floor(n / 4.0);
	r5 = code > 0.5 ? 0.0 : code < -0.5 ? 1.0 : max(r5, 4.0);
	rough = (r5 * 4.0 + cls) / 127.0;
	if (abs(code) > 0.5) spec = 0.0;
}

// A surface's 2D frame from its world normal: the marks across a facet (stone sides) run level, round the form; up a
// trunk (bark: along = 1) they run along the axis. Returns (p2.xy, flow2.xy) for ps_paint; tops take the dir given.
vec4 ps_frame(vec3 wp, vec3 n, float along, vec2 top_dir) {
	n = normalize(n);
	if (abs(n.y) > 0.75) return vec4(wp.xz, normalize(top_dir));
	vec3 t = normalize(cross(vec3(0.0, 1.0, 0.0), n));   // level, across the facet
	vec3 b = cross(n, t);                                   // up the facet
	vec2 p2 = vec2(dot(wp, t), dot(wp, b));
	return vec4(p2, along > 0.5 ? vec2(0.0, 1.0) : vec2(1.0, 0.0));
}
// (lead 8, the owner 19 Nov: "Hit paint") Her hits leave a stroke of colour on the ground for a moment: the same crescent,
// laid across her swing at the contact, with two small satellite marks flung along it. HitPaint.cs keeps the 8 newest as
// ps_hp<k>a = (x, z, swing angle rad, size m; size 0 = empty) and ps_hp<k>b = (erode 0 fresh .. 1 gone, stepped in 4;
// seed; crit 0/1; 0). It dies by stepping (FX_LANGUAGE §4): holes open and the mark thins, never an alpha fade.
// Colour from the palette (blended by the clock): ps_hitc = (body rgb linear, the strokes' chroma floor "cmin"), ps_hite = (inner edge rgb, 0).
// Terrain only: every figure, decal and tell draws over it.
global uniform vec4 ps_hp0a; global uniform vec4 ps_hp0b;
global uniform vec4 ps_hp1a; global uniform vec4 ps_hp1b;
global uniform vec4 ps_hp2a; global uniform vec4 ps_hp2b;
global uniform vec4 ps_hp3a; global uniform vec4 ps_hp3b;
global uniform vec4 ps_hp4a; global uniform vec4 ps_hp4b;
global uniform vec4 ps_hp5a; global uniform vec4 ps_hp5b;
global uniform vec4 ps_hp6a; global uniform vec4 ps_hp6b;
global uniform vec4 ps_hp7a; global uniform vec4 ps_hp7b;

// (lead 9, the owner 19 Nov: "more like splashes of blood. paint splatter that looks cool from physics of the attack ...
// somewhere in the middle of sparks and splatter but from impact") One splat at the contact and droplets thrown along the blow:
// a = (x, z, throw angle rad, size m), b = (step 0 fresh .. 1 gone, seed, power 1 a plain hit .. 2.5 a crit into a crowd, 0).
// More power throws more droplets, farther. Each droplet a short streak along its throw, the two colours split among them;
// it dies in hard steps: the far droplets drop first and the rest shrink (never holes, never alpha).
vec2 ps_stamp(vec2 xz, vec4 a, vec4 b, vec2 r) {
	if (a.w <= 0.0 || b.x >= 1.0) return r;
	vec2 d = xz - a.xy;
	float pw = max(b.z, 1.0), reach = a.w * (0.55 + 0.8 * pw);
	if (dot(d, d) > reach * reach) return r;
	vec2 ax = vec2(cos(a.z), sin(a.z)), ay = vec2(-ax.y, ax.x);
	vec2 q = vec2(dot(d, ax), dot(d, ay));
	float sh = 1.0 - 0.3 * floor(b.x * 3.0);   // 1, .7, .4: shrinks in hard steps
	// the splat at the contact: a fat streak leaning into the throw
	vec2 m = ps_mark(q - vec2(0.12 * a.w, 0.0), 0.42 * a.w * sh, 0.2 * a.w * sh, 0.08);
	m.y = 0.0;
	int n = 3 + int(round(2.5 * pw));
	for (int k = 0; k < 9; k++) {
		if (k >= n) break;
		float hk = ps_h(vec2(b.y * 97.0, float(k) * 7.31)), hj = ps_h(vec2(float(k) * 3.7, b.y * 61.0));
		if (hk > 1.0 - b.x * 1.1) continue;   // the far ones go first (hk: the throw's reach below)
		float u = a.w * (0.3 + 0.75 * pw * hk);
		float v = (hj - 0.5) * 0.55 * u;   // a cone along the throw
		float sz = a.w * mix(0.22, 0.14, hk) * sh;
		vec2 dq = q - vec2(u, v);
		float an = atan(v, u);
		vec2 dx = vec2(cos(an), sin(an));
		vec2 dk = ps_mark(vec2(dot(dq, dx), dot(dq, vec2(-dx.y, dx.x))), sz, sz * 0.5, 0.0);
		dk.y = hj < 0.4 ? dk.x : 0.0;   // some droplets the edge colour, the rest the body's
		if (dk.x > m.x) m = dk;
	}
	return m.x > r.x ? m : r;
}
// (coverage, inner) of the hit paint at world xz.
// (lead 9, perf) ps_hpb = (x, z, R, n live): one circle round every live stamp; a pixel outside it (most) skips all 8.
global uniform vec4 ps_hpb;
vec2 ps_hits(vec2 xz) {
	if (ps_cover1.z <= 0.0 || ps_hpb.w < 0.5) return vec2(0.0);
	vec2 bd = xz - ps_hpb.xy;
	if (dot(bd, bd) > ps_hpb.z * ps_hpb.z) return vec2(0.0);
	vec2 r = vec2(0.0);
	r = ps_stamp(xz, ps_hp0a, ps_hp0b, r); r = ps_stamp(xz, ps_hp1a, ps_hp1b, r);
	r = ps_stamp(xz, ps_hp2a, ps_hp2b, r); r = ps_stamp(xz, ps_hp3a, ps_hp3b, r);
	r = ps_stamp(xz, ps_hp4a, ps_hp4b, r); r = ps_stamp(xz, ps_hp5a, ps_hp5b, r);
	r = ps_stamp(xz, ps_hp6a, ps_hp6b, r); r = ps_stamp(xz, ps_hp7a, ps_hp7b, r);
	return r * ps_cover1.z;
}
// The ground with the hit paint laid on: returns (albedo, emission rgb add) packed as albedo; emission via ps_hit_emit.
vec3 ps_hit_paint(vec3 albedo, vec2 h) {
	return mix(albedo, mix(ps_hitc.rgb, ps_hite.rgb, h.y), h.x);
}
vec3 ps_hit_emit(vec2 h) { return mix(ps_hitc.rgb, ps_hite.rgb, h.y) * h.x * ps_cover1.w; }
// (lane J lead 8: painted light, glows light the world in hard steps) The night glows' spill: ps_gl0..15 = (x, y, z, r) the
// nearest clusters (r > 0 the cyan light, r < 0 the alt violet, 0 none), ps_glc0 = (cyan rgb linear, step 1 strength),
// ps_glc1 = (violet rgb, step 2 strength), ps_glk = (step radii as multiples of |r|, innermost first, step 3 strength).
// Steps are cumulative and hard (one pixel of antialias), the edges broken by a world wobble so they read painted.
// Returns an EMISSION add: the light's colour times the surface's own albedo (plus a floor), so it tints, not paints over.
// n_world = vec3(0): no facing term (the ground); else a hard 0/1 rim of the faces turned to the source.
global uniform vec4 ps_glc0;
global uniform vec4 ps_glc1;
global uniform vec4 ps_glk;
global uniform vec4 ps_gl0;
global uniform vec4 ps_gl1;
global uniform vec4 ps_gl2;
global uniform vec4 ps_gl3;
global uniform vec4 ps_gl4;
global uniform vec4 ps_gl5;
global uniform vec4 ps_gl6;
global uniform vec4 ps_gl7;
global uniform vec4 ps_gl8;
global uniform vec4 ps_gl9;
global uniform vec4 ps_gl10;
global uniform vec4 ps_gl11;
global uniform vec4 ps_gl12;
global uniform vec4 ps_gl13;
global uniform vec4 ps_gl14;
global uniform vec4 ps_gl15;

vec3 ps_gl_one(vec4 g, vec3 wp, vec3 n, vec3 alb, float wob) {
	float ar = abs(g.w);
	vec3 dv = wp - g.xyz;
	float rr = ps_glk.z * ar * 1.12;
	float d2 = dot(dv, dv);
	if (g.w == 0.0 || d2 > rr * rr) return vec3(0.0);
	float d = sqrt(d2) / ar * wob;
	float px = fwidth(d) + 1e-4;
	float s1 = 1.0 - smoothstep(ps_glk.x - px, ps_glk.x + px, d);
	float s2 = 1.0 - smoothstep(ps_glk.y - px, ps_glk.y + px, d);
	float s3 = 1.0 - smoothstep(ps_glk.z - px, ps_glk.z + px, d);
	bool cy = g.w > 0.0;
	vec3 lc = cy ? ps_glc0.rgb : ps_glc1.rgb;
	float face = 1.0;
	if (dot(n, n) > 0.01) face = mix(0.35, 1.0, step(0.05, dot(n, -dv) / max(sqrt(d2), 1e-4)));
	vec3 inner = lc * (alb * 0.4 + 0.1) * (ps_glc0.w * s1 + ps_glc1.w * s2);
	vec3 outer = lc * (alb * 0.5 + 0.03) * ps_glk.w * s3;
	return (inner + outer) * face;
}
// (lead 9, perf) ps_glb = (x, z, R, n sources): one circle (xz) round every source's outer step; a pixel outside it skips
// the loop; the sources past the 8th are read only when n > 8 (a uniform branch). n = 0 (day, --glowlight off): nothing.
global uniform vec4 ps_glb;
vec3 ps_glow_light(vec3 wp, vec3 n_world, vec3 albedo) {
	if (ps_glb.w < 0.5) return vec3(0.0);
	vec2 bd = wp.xz - ps_glb.xy;
	if (dot(bd, bd) > ps_glb.z * ps_glb.z) return vec3(0.0);
	float wob = 1.0 + 0.1 * sin(wp.x * 1.9 + wp.z * 1.3) * sin(wp.z * 2.7 - wp.x * 0.9 + 1.0) + 0.05 * sin(wp.x * 5.1 - wp.z * 4.3);
	vec3 e = vec3(0.0);
	e += ps_gl_one(ps_gl0, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl1, wp, n_world, albedo, wob);
	e += ps_gl_one(ps_gl2, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl3, wp, n_world, albedo, wob);
	e += ps_gl_one(ps_gl4, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl5, wp, n_world, albedo, wob);
	e += ps_gl_one(ps_gl6, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl7, wp, n_world, albedo, wob);
	if (ps_glb.w > 8.5) {
		e += ps_gl_one(ps_gl8, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl9, wp, n_world, albedo, wob);
		e += ps_gl_one(ps_gl10, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl11, wp, n_world, albedo, wob);
		e += ps_gl_one(ps_gl12, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl13, wp, n_world, albedo, wob);
		e += ps_gl_one(ps_gl14, wp, n_world, albedo, wob); e += ps_gl_one(ps_gl15, wp, n_world, albedo, wob);
	}
	return e;
}
#endif
