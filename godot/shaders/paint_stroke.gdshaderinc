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
			if (h0 > cover) continue;
			float h1 = ps_h(ch + 7.7), h2 = ps_h(ch + 3.1), h3 = ps_h(ch + 11.9);
			// (the mark's centre within a quarter cell of its cell's: with len <= 1.15 cell no mark is cut by the 2x2 search)
			vec2 dq = (pl - (c + 0.5 + (vec2(h1, h2) - 0.5) * 0.5)) * cell;
			// along the flow, a few degrees off, so the field reads hand-laid, not combed
			float wob = (h3 - 0.5) * 0.35;
			vec2 ax = normalize(fx + fy * wob), ay = vec2(-ax.y, ax.x);
			float len = ps_brush.y * mix(0.7, 1.3, h2);
			vec2 m = ps_mark(vec2(dot(dq, ax), dot(dq, ay)), len, ps_brush.z * mix(0.8, 1.2, h1), ps_brush.w * (h3 < 0.5 ? 1.0 : -1.0));
			if (m.x > r.x) r = vec4(m.x, m.y, h1 < 0.5 ? -1.0 : 1.0, h0);
		}
	}
	return r;
}

// The painted field: albedo with its marks laid in. cover: this surface's share of cells holding a mark (its class's
// ps_cover). The + marks turn +deg and lift, the - marks turn -deg and sink, each by ps_tone.y; the inner band drops ps_tone.z.
vec3 ps_paint(vec3 albedo, vec2 p2, vec2 flow2, float cover, float seed) {
	vec4 f = ps_field(p2, flow2, cover, seed);
	if (f.x <= 0.0) return albedo;
	vec3 mk = ps_turn(albedo, ps_tone.x * f.z, ps_tone.y * f.z - ps_tone.z * f.y, ps_tone.w);
	return mix(albedo, mk, f.x);
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

vec2 ps_stamp(vec2 xz, vec4 a, vec4 b, vec2 r) {
	if (a.w <= 0.0 || b.x >= 1.0) return r;
	vec2 d = xz - a.xy;
	if (dot(d, d) > a.w * a.w * 0.6) return r;
	vec2 ax = vec2(cos(a.z), sin(a.z)), ay = vec2(-ax.y, ax.x);
	float thin = 1.0 - 0.45 * b.x;
	vec2 m = ps_mark(vec2(dot(d, ax), dot(d, ay)), a.w, a.w * 0.2 * thin * (1.0 + 0.25 * b.z), 0.18);
	// two satellites flung along the swing, ahead of the head and off its convex side
	vec2 d1 = d - ax * a.w * 0.52 - ay * a.w * 0.16, d2 = d - ax * a.w * 0.18 - ay * a.w * 0.3;
	vec2 m1 = ps_mark(vec2(dot(d1, ax), dot(d1, ay)), a.w * 0.3, a.w * 0.07 * thin, 0.12);
	vec2 m2 = ps_mark(vec2(dot(d2, ax), dot(d2, ay)), a.w * 0.22, a.w * 0.06 * thin, -0.1);
	m = max(m, max(m1 * step(0.25, fract(b.y * 7.3)), m2 * step(fract(b.y * 3.9), 0.75)));
	// holes open as it erodes: a 6 cm world cell drops out when its hash is under the erosion
	float hole = step(b.x * 0.9, ps_h(floor(xz / 0.06) + b.y * 31.0));
	m *= hole;
	return m.x > r.x ? m : r;
}
// (coverage, inner) of the hit paint at world xz.
vec2 ps_hits(vec2 xz) {
	if (ps_cover1.z <= 0.0) return vec2(0.0);
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
#endif
