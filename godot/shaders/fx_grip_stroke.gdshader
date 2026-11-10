// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 4): the STROKE her blade leaves, the contact where it meets a body,
// and the hot edge her blade keeps between a chain's cuts. Steel family (fx_cel.gdshaderinc: fx_core white-gold, fx_mid
// gold, fx_edge amber), drawn after the grade (FxCel.Apply): flat bands, hard steps, never added light.
// Mode 0, the stroke: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from the
// drawn tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   TAKE 6 (P7 lead 7; round 3, lead 8): the three colors are CONTINUOUS BANDS. Each band's end (the white's, the
//   gold's, the paint's own) is ONE line across the stroke's width (grip_knot: the white reaching furthest along the
//   tip's path: nested commas), laid by the brush's 3-4 BRISTLE CLUMPS of unequal width: each ends at its own length,
//   a step off its neighbour's of its OWN depth (uneven, now and then the longer of the two), its sides along the
//   travel, its end ROUNDED where it stands proud of a neighbour, the notch between two sharp (grip_band; never a
//   slanted side: a row of V's is a zigzag at any depth; never even square steps: stairs). Lanes are only the TAIL's:
//   the paint's last grip_tail share, across grip_tips.x of the width from the tip's path, is 3-5 dry streaks of
//   uneven width and length, each run out along one of its sides, one or two skipping (grip_laid): the only points in
//   the stroke; a stroke too short on screen to carry them has none and ends on its band's line, its tail drawn to
//   a point (grip_short: the comma small). Leaving (grip_shed): the whole stroke THINS toward the tip's path, its
//   inner side first, to grip_narrow of its width; the white runs on along the tip's path and the gold lies ALONG
//   THE INNER EDGE (grip_rim, grip_push), the amber at the tail's end (never a white fan, never the gold bunched at
//   the tail). THE CONTACT IS IN THE STROKE (grip_bite, no second object): round the blade's crossing along the
//   ribbon the stroke swells (its inner side in, its tip's side out, by grip_swell of its own width) and the core
//   floods on past the place over the gold, for the 2-3 frames the strength lasts. COLOR.r = how much the ribbon is
//   the blade's own sweep here (0: turned to the camera for an edge-on cut: no lit blade there).
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
uniform float grip_thin = 0.0;    // mode 2: 0 hot, 1, 2 stepping out
uniform float grip_px = 0.012;    // a pixel here (m)
uniform float grip_seed = 0.0;
uniform vec2 grip_size = vec2(1.5, 0.5);
uniform float grip_knot[24];      // the three bands' ends (the core's, the mid's, the paint's own), 4 knots each: across (0 the tip's path, 1 the inner edge), share of the length
uniform float grip_lanes[16];     // the tail's streaks, from the tip's path in: width share, the share of the tail it keeps (1: to the paint's end)
uniform int grip_lane_n = 4;
uniform vec4 grip_lane = vec4(0.12, 0.04, 0.8, 1.3);     // jitter of a streak's width (share of it), of its end (share of the length); the comma's width at the tail (share of the head's), its power
uniform vec4 grip_tips = vec4(0.5, 0.4, 0.5, 0.1);       // the streaks lie across this share of the width from the tip's path; a streak's point (m, at most this share of the tail); a skip's slant (m)
uniform float grip_tail = 0.28;   // the paint's last share laid as streaks
uniform vec4 grip_clump = vec4(3.0, 4.0, 0.6, 1.5);      // a band end's clumps across the width (fewest, most), how uneven their widths (0: even), a step's depth at most this many of the narrower clump's width
uniform vec4 grip_tooth = vec4(0.07, 0.42, 0.12, 0.3);   // a step's depth along the stroke (m: least, most; each step its own between them), a clump end's rounding (m), the chance a clump is the longer of two
uniform float grip_narrow = 0.2;  // leaving: the stroke's width at the shed's end (share of its own)
uniform vec4 grip_gap = vec4(0.5, 0.14, 0.26, 0.62);     // a lane's chance to skip; the skip's metres (least, most); where it starts (share of the finger)
uniform vec4 grip_shed = vec4(-1.0, 0.084, 0.117, 0.03); // s since the contact; the amber out, the gold out, each lane's own offset
uniform vec4 grip_bite = vec4(0.0, 0.0, 0.35, 0.6);      // the contact, in the stroke: its place (m along, as UV.x), its strength now (0: none; by the bodies struck, stepping out), its reach toward the head and toward the tail (m)
uniform vec3 grip_swell = vec3(0.22, 0.12, 0.5);         // the bite at strength 1: the width it adds on the inner side and past the tip's path (shares of the stroke's own width there), how far past its place the core floods (share of the tail reach)
uniform vec2 grip_short = vec2(1.0, 1.0);                // a stroke short on screen: its tail's width (0 a point, 1 the look's taper), its streaks (0 none yet, 1 whole)
uniform vec4 grip_rim = vec4(0.45, 0.35, 0.12, 0.3);     // leaving: the gold's share of the width along the inner edge, the share of the shed by which it is that wide, where it starts behind the head and the length it widens over (shares of the length)
uniform vec2 grip_push = vec2(0.8, 0.5);                 // leaving: how far the white's end runs on toward the gold's, the gold's toward the paint's (shares, at the shed's end)

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

// 0,0 -> k.xy -> k.zw -> 1,1, straight between
float grip_knots(float x, vec4 k) {
	return x < k.x ? x * k.y / max(k.x, 1e-4)
		: x < k.z ? k.y + (x - k.x) * (k.w - k.y) / max(k.z - k.x, 1e-4)
		: k.w + (x - k.z) * (1.0 - k.w) / max(1.0 - k.z, 1e-4);
}

// a band's own line at `a` across (0 the tip's path, 1 the inner edge): straight between its knots, a share of the length
float grip_line(int k, float a) {
	int o = k * 8;
	float tb = grip_knot[o + 1];
	for (int j = 0; j < 3; j++) {
		float a0 = grip_knot[o + j * 2], a1 = grip_knot[o + j * 2 + 2];
		if (a > a0 && a1 > a0) tb = mix(grip_knot[o + j * 2 + 1], grip_knot[o + j * 2 + 3], min((a - a0) / (a1 - a0), 1.0));
	}
	return tb;
}

// One band's end at `a` across the width, a share of the length: the brush's bristle clumps (3-4, unequal widths), each
// ending at its own length: its line's at the clump's middle (never under `least`: the bite's flood), then held to a
// step off the clump before it of its OWN depth (grip_tooth.x to .y m, a hash each: uneven, never stairs), no deeper
// than grip_clump.w of the narrower of the two is wide (wm: the stroke's width in m), and now and then (grip_tooth.w)
// the LONGER of the two. The side between two clumps runs along the travel (never a slant: a V). A clump's end is
// rounded (grip_tooth.z) where it stands proud of its neighbour or of the stroke's inner edge; the notch stays sharp.
float grip_band(int k, float a, float wm, float body, float least) {
	float fk = float(k) * 7.0;
	int n = min(4, int(grip_clump.x) + int(fx_hash(vec2(fk + 21.7, grip_seed)) * (grip_clump.y - grip_clump.x + 0.999)));
	float w[4];
	float ws = 0.0;
	for (int i = 0; i < n; i++) {
		w[i] = 1.0 + grip_clump.z * (2.0 * fx_hash(vec2(fk + float(i) + 23.3, grip_seed)) - 1.0);
		ws += w[i];
	}
	float lo = 0.0, wl = 1.0, tp = 0.0;
	float val = 0.0, vl = 0.0, vr = -1.0, dl = 1e3, dr = 1e3, wa = 1.0;
	int at = -5;
	for (int i = 0; i < n; i++) {
		float fi = fk + float(i), wi = w[i] / ws;
		float ti = max(grip_line(k, lo + 0.5 * wi), least);
		if (i > 0) {
			float cap = min(mix(grip_tooth.x, grip_tooth.y, fx_hash(vec2(fi + 31.9, grip_seed))), grip_clump.w * min(wl, wi) * wm);
			float d = tp - ti;
			float mag = clamp(abs(d) * body, min(grip_tooth.x, cap), cap) / body;
			bool longer = (d < 0.0) != (fx_hash(vec2(fi + 37.3, grip_seed)) < grip_tooth.w);
			ti = max(tp + (longer ? mag : -mag), least);
		}
		if (i == at + 1) vr = ti;
		if (at < 0 && (a < lo + wi || i == n - 1)) {
			at = i;
			val = ti;
			vl = i > 0 ? tp : ti;
			vr = -1.0;   // (the last clump: the stroke's inner edge is its neighbour)
			dl = i > 0 ? a - lo : 1e3;
			dr = lo + wi - a;
			wa = wi;
		}
		lo += wi;
		wl = wi;
		tp = ti;
	}
	float rw = min(grip_tooth.z / max(wm, 1e-4), 0.5 * wa), rt = grip_tooth.z / body;
	float drop = 0.0;
	if (dl < rw && vl < val) {
		float x = 1.0 - max(dl, 0.0) / rw;
		drop = min(rt, val - vl) * (1.0 - sqrt(max(1.0 - x * x, 0.0)));
	}
	if (dr < rw && vr < val) {
		float x = 1.0 - max(dr, 0.0) / rw;
		drop = max(drop, min(rt, val - vr) * (1.0 - sqrt(max(1.0 - x * x, 0.0))));
	}
	return max(val - drop, 0.0);
}

// the share of the tail the i-th streak keeps (jittered per stroke)
float grip_keep(int i) {
	return clamp(grip_lanes[i * 2 + 1] + grip_lane.y / max(grip_tail, 1e-3) * (2.0 * fx_hash(vec2(float(i) + 5.71, grip_seed)) - 1.0), 0.0, 1.0);
}

// The paint whose end is `end` here (fe: a pixel of it) and `e0` on the tip's path. Inside grip_tips.x of the width it
// is whole to the tail's start (e0's last grip_tail share), then the brush's dry streaks: uneven widths, each keeping
// its own share of the tail, run out along ONE of its sides over its last metres (the outermost along the tip's
// path: the comma's point), some skipping (bare ground cut on a slant, the paint back after it; never the outermost).
// Past it (ax: grip_tips.x, wider as the stroke thins): no lanes, the paint ends on its band's own line.
float grip_laid(float end, float fe, float e0, float ax, float a, float t, float fa, float ft, float body) {
	float cov = clamp((end - t) / fe + 0.5, 0.0, 1.0) * clamp(min(a - ax, 1.0 - a) / fa + 0.5, 0.0, 1.0);
	if (a > ax + fa || e0 <= 1e-3) return cov;
	float ts = e0 * (1.0 - grip_tail), slant = grip_tips.w / body;
	float wsum = 0.0;
	for (int i = 0; i < grip_lane_n; i++) wsum += grip_lanes[i * 2] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(float(i) + 0.37, grip_seed)) - 1.0));
	float lo = 0.0;
	for (int i = 0; i < grip_lane_n; i++) {
		float fi = float(i);
		float w = ax * grip_lanes[i * 2] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(fi + 0.37, grip_seed)) - 1.0)) / wsum;
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
	// the bite (the contact, in the stroke): 1 x its strength at the blade's crossing, down to 0 a reach either way
	float bk = 0.0;
	if (grip_bite.y > 0.0) {
		float x = clamp(abs(u - grip_bite.x) / max(u > grip_bite.x ? grip_bite.z : grip_bite.w, 1e-3), 0.0, 1.0);
		bk = grip_bite.y * (1.0 - x * x) * (1.0 - x * x);
	}
	// leaving (grip_shed): the stroke thins toward the tip's path, its inner side first, its bands with it
	float shed = clamp((grip_shed.x - grip_shed.y + grip_shed.w) / max(grip_shed.z - grip_shed.y + 2.0 * grip_shed.w, 1e-4), 0.0, 1.0);
	float thin = mix(1.0, grip_narrow, shed);
	float taper = grip_lane.z * grip_short.x;
	float flat_w = grip_shape.y * thin * (1.0 - (1.0 - taper) * pow(t, grip_lane.w));
	// (the swell: the brush pressed harder; its inner side never past the guard)
	float vm = 1.0 - uv.y + flat_w * grip_swell.y * bk;   // shares of the blade in from the stroke's outer edge (negative: past it)
	float wide = max(min(flat_w * (1.0 + (grip_swell.x + grip_swell.y) * bk), 0.98 + flat_w * grip_swell.y * bk), 1e-4);
	float a = vm / wide;     // 0 the tip's path, 1 the inner edge
	float fa = max(fwidth(a), 1e-5), ft = max(fwidth(sb) / body, 1e-5);
	float wm = grip_shape.y * thin * 0.5 * (1.0 + taper) * grip_blade;   // the stroke's width (m) at its middle
	float ax = grip_short.y > 0.01 ? mix(grip_tips.x, 1.0, 1.0 - thin) : 0.0;   // the streaks take more of a thinner stroke's width (none yet: no lanes)
	// the three bands' ends here, and the paint's own on the tip's path; the bite's core floods on past its place
	float tm = grip_band(1, a, wm, body, 0.0);
	float te = min(grip_band(2, a, wm, body, 0.0), 1.0);
	float flood = grip_bite.y > 0.0 ? (grip_total - grip_bite.x + grip_swell.z * grip_bite.w * min(grip_bite.y, 1.0)) / body : 0.0;
	float tc = min(grip_band(0, a, wm, body, flood), max(te, tm));
	tm = clamp(tm, tc, 1.0);
	te = clamp(te, tm, 1.0);
	float x0 = min(grip_band(2, 0.0, wm, body, 0.0), 1.0);
	// leaving: the white runs on toward the tail, the gold after it
	tc = mix(tc, tm, grip_push.x * shed);
	tm = mix(tm, te, grip_push.y * shed);
	float dc = tc - t, dm = tm - t, de = te - t;
	float fc = max(fwidth(dc), 1e-5), fm = max(fwidth(dm), 1e-5), fe = max(fwidth(de), 1e-5);
	float cov = grip_laid(te, fe, x0, ax, a, t, fa, ft, body);
	// leaving: the gold lies along the inner edge, from a point behind the head, widening to its share of the width
	float rim = grip_rim.x * clamp(shed / max(grip_rim.y, 1e-3), 0.0, 1.0) * clamp((t - grip_rim.z) / max(grip_rim.w, 1e-3), 0.0, 1.0);
	float rimc = rim > 1e-4 ? clamp((a - (1.0 - rim)) / fa + 0.5, 0.0, 1.0) : 0.0;
	// the bands: flat, hard, continuous across the width
	vec3 col = mix(fx_edge, fx_mid, clamp(dm / fm + 0.5, 0.0, 1.0));
	col = mix(col, fx_core, clamp(dc / fc + 0.5, 0.0, 1.0) * (1.0 - rimc));
	// the paint's end on the tip's path (the outermost streak's): where the glow dies
	float e0 = x0 * (1.0 - grip_tail * (1.0 - grip_keep(0)));
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
	vec4 c = grip_mode == 0 ? grip_trail(UV, COLOR.r) : grip_edge(UV, COLOR.r);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
