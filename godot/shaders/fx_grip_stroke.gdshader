// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 4): the STROKE her blade leaves, the contact where it meets a body,
// and the hot edge her blade keeps between a chain's cuts. Steel family (fx_cel.gdshaderinc: fx_core white-gold, fx_mid
// gold, fx_edge amber), drawn after the grade (FxCel.Apply): flat bands, hard steps, never added light.
// Mode 0, the stroke: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from the
// drawn tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   TAKE 6 (P7 lead 7): the three colors are CONTINUOUS BANDS. Each band's end (the white's, the gold's, the paint's
//   own) is ONE line across the stroke's width (grip_knot: straight between its knots, the white reaching furthest
//   along the tip's path: nested commas), jogged by the brush's 2-3 uneven clumps: a tooth each, never deeper than it
//   is wide, its sides cut on a slant, per stroke by grip_seed (grip_band). Lanes are only the TAIL's: the paint's last
//   grip_tail share, across grip_tips.x of the width from the tip's path, is 3-5 dry streaks of uneven width and
//   length, each run out along one of its sides, one or two skipping (grip_laid); their colors are the bands' that
//   reach there. Leaving (grip_shed): the amber goes clump by clump from the tip's path in, then the gold the same
//   way; the white comma is last. (Takes 3-5 ended each band per lane at the lane's own length: a row of needles in
//   different colors, a bolt.) COLOR.r = how much the ribbon is the blade's own sweep here (0: turned to the camera
//   for an edge-on cut: no lit blade there).
// Mode 1, the contact (lead 7: a quad lying IN the stroke, +x the tip's travel at the crossing, +y the stroke's own
//   across there, its center the point on the blade): one gold chisel with a white fat end, smaller than the stroke's
//   head, and 1-2 chips thrown on along the travel (grip_age seconds); whole for grip_steps.x frames, two smaller
//   steps, then gone.
// Mode 2, the hot edge (a quad on the blade facing the camera; UV.x 0 guard to 1 tip, UV.y pixels across; COLOR.r 1:
//   the tip's glint, UV -1..1): a core line grip_size.x px wide, stepping out gold, then amber (grip_thin 1, 2).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform int grip_mode = 0;
uniform float grip_total = 1.0;
uniform float grip_thread = 0.0;  // the link's thread at the tail (m of grip_total)
uniform float grip_u0 = 0.0;      // the path's metres at the drawn tail (the bristles' place)
uniform float grip_blade = 1.0;   // the blade's length guard to tip (m)
uniform vec3 grip_shape = vec3(0.03, 0.6, 1.5);     // the tail's width, the head's (shares of the blade), the power it runs out by
uniform vec3 grip_bands = vec3(0.48, 0.68, 0.74);   // across (shares of the width in from the tip's path): the core's end, the mid's, where the amber runs dry
uniform vec3 grip_reach = vec3(0.62, 0.9, 2.0);     // how far back from the head the core and the mid reach (shares of the length), the power they close by
uniform vec3 grip_dry = vec3(0.4, 0.05, 0.92);      // the tail's dry metres, the brush's along at the tail's end, and in the body
uniform vec2 grip_lit = vec2(0.04, 1.0);            // the lit blade at the head: its thickness (m), how far down the blade (0 none, 1 to the guard)
uniform vec2 grip_grain = vec2(3.0, 0.45);               // a bristle (px across), a streak (m along)
uniform float grip_glow = 0.28;   // the glow's unit (m): fx_glow's width and reach are shares of it
uniform float grip_point = 0.12;  // the tail's last metres, drawn to a point
uniform float grip_core = 1.0;    // mode 1: the white's share of the kernel
uniform float grip_thin = 0.0;    // mode 1: frames since the contact; mode 2: 0 hot, 1, 2 stepping out
uniform float grip_px = 0.012;    // a pixel here (m)
uniform float grip_seed = 0.0;
uniform vec2 grip_size = vec2(1.5, 0.5);
uniform vec4 grip_slit = vec4(0.6, 0.35, 0.1, 0.12);   // mode 1: the cut-through's reach ahead and behind its kernel, its half-width, the kernel (m at size 1)
uniform float grip_sparks = 4.0;
uniform float grip_age = 0.0;
uniform float grip_knot[24];      // the three bands' ends (the core's, the mid's, the paint's own), 4 knots each: across (0 the tip's path, 1 the inner edge), share of the length
uniform float grip_lanes[16];     // the tail's streaks, from the tip's path in: width share, the share of the tail it keeps (1: to the paint's end)
uniform int grip_lane_n = 4;
uniform vec4 grip_lane = vec4(0.12, 0.04, 0.8, 1.3);     // jitter of a streak's width (share of it), of its end (share of the length); the comma's width at the tail (share of the head's), its power
uniform vec4 grip_tips = vec4(0.5, 0.4, 0.5, 0.1);       // the streaks lie across this share of the width from the tip's path; a streak's point (m, at most this share of the tail); a skip's slant (m)
uniform float grip_tail = 0.28;   // the paint's last share laid as streaks
uniform vec4 grip_clump = vec4(2.0, 3.0, 0.4, 1.0);      // a band end's clumps across the width (fewest, most), how uneven their widths (0: even), a tooth's depth at most this many of its clump's width
uniform vec4 grip_tooth = vec4(0.18, 0.3, 0.2, 0.6);     // a tooth's depth along the stroke (m: least, most), its side's slant (share of the narrower clump: least, most)
uniform float grip_fly = 5.0;     // mode 1: a chip's speed along the travel (m/s)
uniform vec4 grip_gap = vec4(0.5, 0.14, 0.26, 0.62);     // a lane's chance to skip; the skip's metres (least, most); where it starts (share of the finger)
uniform vec4 grip_shed = vec4(-1.0, 0.084, 0.117, 0.03); // s since the contact; the amber out, the gold out, each lane's own offset
uniform vec4 grip_kite = vec4(0.36, 0.1, 0.065, 0.4);    // mode 1: m ahead of the point, behind, half-width, the white's share of its length
uniform vec4 grip_shards = vec4(0.1, 0.18, 0.04, 0.06);  // mode 1: a chip's length (least, most), its width at the fat end
uniform vec4 grip_steps = vec4(3.0, 0.7, 0.42, 10.0);    // mode 1: frames whole, the two steps' sizes, a chip's lean off the travel (degrees at most)

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

// 0,0 -> k.xy -> k.zw -> 1,1, straight between
float grip_knots(float x, vec4 k) {
	return x < k.x ? x * k.y / max(k.x, 1e-4)
		: x < k.z ? k.y + (x - k.x) * (k.w - k.y) / max(k.z - k.x, 1e-4)
		: k.w + (x - k.z) * (1.0 - k.w) / max(1.0 - k.z, 1e-4);
}

// One band's end across the width (a: 0 the tip's path, 1 the inner edge), a share of the length: ONE line, straight
// between its knots, jogged by the brush's clumps (2-3, uneven widths): a tooth each, alternately long and short of the
// line, no deeper than its clump is wide (wm: the stroke's width in m), its sides cut on a slant. `gone` = the across
// up to which this band's clumps have left: from the tip's path in, each at its own time round `at` s (grip_shed).
float grip_band(int k, float a, float wm, float body, float at, out float gone) {
	int o = k * 8;
	float tb = grip_knot[o + 1];
	for (int j = 0; j < 3; j++) {
		float a0 = grip_knot[o + j * 2], a1 = grip_knot[o + j * 2 + 2];
		if (a > a0 && a1 > a0) tb = mix(grip_knot[o + j * 2 + 1], grip_knot[o + j * 2 + 3], min((a - a0) / (a1 - a0), 1.0));
	}
	float fk = float(k) * 7.0;
	int n = min(4, int(grip_clump.x) + int(fx_hash(vec2(fk + 21.7, grip_seed)) * (grip_clump.y - grip_clump.x + 0.999)));
	float w[4];
	float ws = 0.0;
	for (int i = 0; i < n; i++) {
		w[i] = 1.0 + grip_clump.z * (2.0 * fx_hash(vec2(fk + float(i) + 23.3, grip_seed)) - 1.0);
		ws += w[i];
	}
	float sgn = fx_hash(vec2(fk + 29.1, grip_seed)) < 0.5 ? -0.5 : 0.5;
	float off = 0.0, lo = 0.0, wl = 1.0;
	bool left = true;
	gone = 0.0;
	for (int i = 0; i < n; i++) {
		float fi = fk + float(i), wi = w[i] / ws;
		float di = sgn * min(mix(grip_tooth.x, grip_tooth.y, fx_hash(vec2(fi + 31.9, grip_seed))), grip_clump.w * wi * wm);
		sgn = -sgn;
		float s = mix(grip_tooth.z, grip_tooth.w, fx_hash(vec2(fi + 37.3, grip_seed))) * min(wl, wi);
		off = i == 0 ? di : mix(off, di, clamp((a - lo) / max(s, 1e-4) + 0.5, 0.0, 1.0));
		left = left && grip_shed.x >= at + grip_shed.w * (2.0 * (float(i) + fx_hash(vec2(fi + 41.7, grip_seed))) / float(n) - 1.0);
		lo += wi;
		wl = wi;
		if (left) gone = i == n - 1 ? 2.0 : lo;
	}
	return max(tb + off / body, 0.0);
}

// the share of the tail the i-th streak keeps (jittered per stroke)
float grip_keep(int i) {
	return clamp(grip_lanes[i * 2 + 1] + grip_lane.y / max(grip_tail, 1e-3) * (2.0 * fx_hash(vec2(float(i) + 5.71, grip_seed)) - 1.0), 0.0, 1.0);
}

// The paint whose end is `end` here (fe: a pixel of it) and `e0` on the tip's path. Inside grip_tips.x of the width it
// is whole to the tail's start (e0's last grip_tail share), then the brush's dry streaks: uneven widths, each keeping
// its own share of the tail, run out along ONE of its sides over its last metres (the outermost along the tip's
// path: the comma's point), some skipping (bare ground cut on a slant, the paint back after it; never the outermost).
// Past grip_tips.x: no lanes, the paint ends on its band's own line.
float grip_laid(float end, float fe, float e0, float a, float t, float fa, float ft, float body) {
	float cov = clamp((end - t) / fe + 0.5, 0.0, 1.0) * clamp(min(a - grip_tips.x, 1.0 - a) / fa + 0.5, 0.0, 1.0);
	if (a > grip_tips.x + fa || e0 <= 1e-3) return cov;
	float ts = e0 * (1.0 - grip_tail), slant = grip_tips.w / body;
	float wsum = 0.0;
	for (int i = 0; i < grip_lane_n; i++) wsum += grip_lanes[i * 2] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(float(i) + 0.37, grip_seed)) - 1.0));
	float lo = 0.0;
	for (int i = 0; i < grip_lane_n; i++) {
		float fi = float(i);
		float w = grip_tips.x * grip_lanes[i * 2] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(fi + 0.37, grip_seed)) - 1.0)) / wsum;
		float l = (a - lo) / w;   // 0..1 across this streak
		lo += w;
		float e = mix(ts, e0, grip_keep(i));
		float hp = fx_hash(vec2(fi + 7.3, grip_seed));
		float p = i == 0 ? 0.0 : hp < 0.5 ? 0.36 * hp : 1.0 - 0.36 * (1.0 - hp);
		float pl = min(min(grip_tips.y / body, grip_tips.z * (e0 - ts)), e - ts);
		float f = clamp((e - t) / max(pl, 1e-4), 0.0, 1.0);
		float l0 = p * (1.0 - f), l1 = p + (1.0 - p) * f, pxl = w / fa;
		float c = clamp(min(l - l0, l1 - l) * pxl + 0.5, 0.0, 1.0) * clamp((l1 - l0) * pxl, 0.0, 1.0) * clamp((e - t) / ft + 0.5, 0.0, 1.0);
		float g0 = mix(ts, e, grip_gap.w * fx_hash(vec2(fi + 11.1, grip_seed)));
		float g1 = g0 + mix(grip_gap.y, grip_gap.z, fx_hash(vec2(fi + 13.9, grip_seed))) / body;
		if (i > 0 && fx_hash(vec2(fi + 9.7, grip_seed)) < grip_gap.x && g1 < e - 1.5 * slant) {
			float tg = t - slant * (l - 0.5);
			c *= 1.0 - clamp(min(tg - g0, g1 - tg) / ft + 0.5, 0.0, 1.0);
		}
		cov += c;
	}
	return min(cov, 1.0);
}

vec4 grip_trail(vec2 uv, float real) {
	float u = uv.x;
	float sb = grip_total - u;   // metres behind the blade (negative: past it)
	float body = max(grip_total - grip_thread, 1e-3);
	float t = clamp(sb / body, 0.0, 1.0);   // 0 the head (the blade now), 1 the stroke's tail
	float vm = 1.0 - uv.y;   // shares of the blade in from the tip's path (negative: past it)
	float wide = max(grip_shape.y * (1.0 - (1.0 - grip_lane.z) * pow(t, grip_lane.w)), 1e-4);
	float a = vm / wide;     // 0 the tip's path, 1 the inner edge
	float fa = max(fwidth(a), 1e-5), ft = max(fwidth(sb) / body, 1e-5);
	float wm = grip_shape.y * grip_lane.z * grip_blade;   // the stroke's width (m) at its narrowest
	// the three bands' ends here and on the tip's path, and how far in the gold and the amber have left
	float gw, gd, gn;
	float tc = grip_band(0, a, wm, body, grip_shed.z, gw);
	float tm = clamp(grip_band(1, a, wm, body, grip_shed.y, gd), tc, 1.0);
	float te = clamp(grip_band(2, a, wm, body, 1e9, gn), tm, 1.0);
	float c0 = grip_band(0, 0.0, wm, body, 1e9, gn);
	float m0 = clamp(grip_band(1, 0.0, wm, body, 1e9, gn), c0, 1.0);
	float x0 = clamp(grip_band(2, 0.0, wm, body, 1e9, gn), m0, 1.0);
	gw = min(gw, gd);   // the gold leaves only where the amber has
	float dc = tc - t, dm = tm - t, de = te - t;
	float fc = max(fwidth(dc), 1e-5), fm = max(fwidth(dm), 1e-5), fe = max(fwidth(de), 1e-5);
	float amber = clamp((a - gd) / fa + 0.5, 0.0, 1.0), gold = clamp((a - gw) / fa + 0.5, 0.0, 1.0);
	// the paint: ends on the amber's line, on the gold's where the amber has left, on the white's where both have
	float cov = mix(mix(grip_laid(tc, fc, c0, a, t, fa, ft, body), grip_laid(tm, fm, m0, a, t, fa, ft, body), gold),
		grip_laid(te, fe, x0, a, t, fa, ft, body), amber);
	// the bands: flat, hard, continuous across the width
	vec3 col = mix(fx_edge, fx_mid, mix(1.0, clamp(dm / fm + 0.5, 0.0, 1.0), amber));
	col = mix(col, fx_core, mix(1.0, clamp(dc / fc + 0.5, 0.0, 1.0), gold));
	// the paint's end on the tip's path (the outermost streak's): where the glow dies
	float e0 = (gd > 0.0 ? (gw > 0.0 ? c0 : m0) : x0) * (1.0 - grip_tail * (1.0 - grip_keep(0)));
	// a link's thread (the first grip_thread metres; hidden while grip.link.on is 0): the tail's width, to a point
	if (grip_thread > 1e-4 && u < grip_thread) {
		cov = grip_in(grip_shape.x * sqrt(clamp(u / max(grip_point, 1e-3), 0.0, 1.0)), vm) * step(0.0, vm);
		col = fx_edge;
	}
	// past the tip's path: the house glow off the clean edge, as far as the tip's own lane is painted (never in a gap)
	float alb = grip_dry.z * smoothstep(0.0, 1.0, (e0 - t) * body / max(grip_dry.x, 1e-3));
	vec4 g = fx_cel(fx_t.x - max(-vm, 0.0) * grip_blade / grip_glow - 1e-3, alb);
	g.a *= smoothstep(0.0, 0.25, alb) * step(vm, 0.0);
	vec4 c4 = vec4(mix(g.rgb, col, cov), max(cov, g.a * (1.0 - cov)));
	c4.a *= grip_in(0.0, -sb) * step(0.0, u);
	// the lit blade: white on the blade's own line from the tip's path through the head and on down toward the guard
	float lit_end = grip_shape.y + (1.0 - grip_shape.y) * grip_lit.y;
	float kl = clamp((vm - grip_shape.y) / max(lit_end - grip_shape.y, 1e-4), 0.0, 1.0);
	float lit = real * grip_in(0.5 * grip_lit.x * (1.0 - 0.8 * kl), abs(sb)) * step(0.0, vm) * step(vm, lit_end) * step(1e-3, grip_lit.y);
	return vec4(mix(c4.rgb, fx_core, lit), max(c4.a, lit));
}

// a wedge: its flat fat end at `at`, to a point `len` on along `dir`
float grip_wedge(vec2 p, vec2 at, vec2 dir, float len, float hw) {
	vec2 dd = p - at;
	float x = dot(dd, dir), y = abs(dot(dd, vec2(-dir.y, dir.x)));
	return max((y - hw * (1.0 - x / len)) * len / length(vec2(len, hw)), -x);
}

// a triangle's three half-planes (either winding): under 0 inside
float grip_tri(vec2 p, vec2 a, vec2 b, vec2 c) {
	vec2 e0 = b - a, e1 = c - b, e2 = a - c;
	float w = sign(e0.x * (c.y - a.y) - e0.y * (c.x - a.x));
	return max(max(dot(p - a, vec2(e0.y, -e0.x)) / length(e0), dot(p - b, vec2(e1.y, -e1.x)) / length(e1)), dot(p - c, vec2(e2.y, -e2.x)) / length(e2)) * w;
}

// (lead 7) The contact: where the edge bit, in the stroke's own hand. ONE chisel of paint lying in the stroke along
// the tip's travel: gold, its fat slanted end on the blade white (the stroke's head and body, small), run to an
// off-center point ahead; and one or two short hard chips of the same gold thrown on along the travel (grip_fly).
// No rim, no fan, nothing symmetric: the kite with its barbs read as a crown standing on the cut.
vec4 grip_contact(vec2 uv) {
	vec2 q = (uv - 0.5) * 2.0 * grip_size;
	float f = floor(grip_thin + 0.5) - grip_steps.x;   // under 0: whole; 0 and 1: the two steps out
	float k = f < 0.0 ? 1.0 : f < 1.0 ? grip_steps.y : f < 2.0 ? grip_steps.z : 0.0;
	if (k <= 0.0) return vec4(0.0);
	float s = grip_size.x / 1.5 * k;   // the contact's size (1 = Sunder's on one body)
	float hw = grip_kite.z * s, ahead = grip_kite.x * s, behind = grip_kite.y * s;
	q.y *= fract(grip_seed) < 0.5 ? 1.0 : -1.0;
	// (wound so the half-planes' normals point out: a, b, c counter-clockwise in q)
	float sdm = grip_tri(q, vec2(-behind, -hw), vec2(ahead, 0.4 * hw), vec2(-0.3 * behind, hw));
	float sdc = 1e3;
	for (int i = 0; i < 2; i++) {
		float fi = float(i);
		if (fi >= grip_sparks - max(f + 1.0, 0.0) || f >= 1.0) break;
		float h1 = fx_hash(vec2(fi * 1.7 + 0.3, grip_seed)), h2 = fx_hash(vec2(fi * 2.3 + 7.1, grip_seed)), h3 = fx_hash(vec2(fi * 3.1 + 3.3, grip_seed));
		float side = mod(fi + floor(grip_seed), 2.0) < 0.5 ? 1.0 : -1.0;
		float ang = side * radians(h2 * grip_steps.w);
		vec2 at = vec2(ahead * mix(0.8, 1.25, h1) + grip_fly * grip_age * mix(0.6, 1.0, h3), side * hw * mix(0.5, 1.7, h1) + 0.4 * hw);
		sdc = min(sdc, grip_wedge(q, at, vec2(cos(ang), sin(ang)), mix(grip_shards.x, grip_shards.y, h3) * s, 0.5 * mix(grip_shards.z, grip_shards.w, h2) * s));
	}
	float cm = clamp(0.5 - sdm / grip_px, 0.0, 1.0), cc = clamp(0.5 - sdc / grip_px, 0.0, 1.0);
	float xk = -behind + (ahead + behind) * grip_kite.w * grip_core;
	float white = clamp(-0.5 - sdm / grip_px, 0.0, 1.0) * clamp(0.5 - (q.x + 0.6 * q.y - xk) / (1.17 * grip_px), 0.0, 1.0);
	vec3 col = mix(f < 0.0 ? fx_mid : fx_edge, mix(fx_mid, fx_core, white), cm);
	return vec4(col, max(cm, cc));
}

vec4 grip_edge(vec2 uv, float glint) {
	int st = int(grip_thin + 0.5);
	vec3 c = st == 0 ? fx_core : st == 1 ? fx_mid : fx_edge;
	if (glint > 0.5) {
		// the tip's glint: a small four-point star, long along the blade; only while the edge is hot
		vec2 q = abs(uv);
		float sd = pow(q.x, 0.62) + pow(q.y, 0.62) - 1.0;
		return vec4(c, st == 0 ? grip_in(0.0, sd) : 0.0);
	}
	// the line: a little finer toward the guard, thinner by the step
	float hw = 0.5 * grip_size.x * mix(0.7, 1.0, clamp(uv.x, 0.0, 1.0)) * (st == 0 ? 1.0 : st == 1 ? 0.7 : 0.45);
	float cov = grip_in(hw, abs(uv.y)) * step(0.0, uv.x) * step(uv.x, 1.0);
	return vec4(c, cov);
}

void fragment() {
	vec4 c = grip_mode == 0 ? grip_trail(UV, COLOR.r) : grip_mode == 1 ? grip_contact(UV) : grip_edge(UV, COLOR.r);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
