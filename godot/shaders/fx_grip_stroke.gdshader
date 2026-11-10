// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 4): the STROKE her blade leaves, the contact where it meets a body,
// and the hot edge her blade keeps between a chain's cuts. Steel family (fx_cel.gdshaderinc: fx_core white-gold, fx_mid
// gold, fx_edge amber), drawn after the grade (FxCel.Apply): flat bands, hard steps, never added light.
// Mode 0, the stroke: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from the
// drawn tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   TAKE 5 (P7 lead 6): the stroke is laid by a brush of grip_lane_n bristle CLUMPS, lanes across its width (data: each
//   lane's width, where its core ends, its mid ends, its finger ends, as shares of the length; jittered per stroke by
//   grip_seed). The bands are laid here, lane by lane (only the house colors and the outer glow are fx_cel's): each
//   band's end is a step per lane with a short pointed tongue, each lane runs to its own point (the tail is fingers),
//   some lanes skip (a bare gap) and come back. Leaving: each lane drops its amber, then its gold, at its own time
//   (grip_shed); the white is last. COLOR.r = how much the ribbon is the blade's own sweep here (0: turned to the camera
//   for an edge-on cut: no lit blade there).
// Mode 1, the contact (a quad facing the camera, +x the blade's travel, its center the point on the blade): ONE hard
//   kite, cream with a gold rim, fat on the blade, long along the travel, with up to 3 short fat barbs starting on it;
//   whole for grip_steps.x frames, then two smaller steps, then gone.
//   and a few hard tears thrown along the travel that fly on for 4-7 frames (grip_age seconds).
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
uniform float grip_lanes[32];     // per lane (from the tip's path in): width share, core's end, mid's end, finger's end
uniform int grip_lane_n = 6;
uniform vec4 grip_lane = vec4(0.12, 0.04, 0.8, 1.3);     // jitter of a width (share of it), of an end (share of the length); the comma's width at the tail (share of the head's), its power
uniform vec4 grip_tips = vec4(0.1, 0.4, 0.5, 0.0);       // a band's tongue (m); a finger's point (m, at most this share of the finger)
uniform vec4 grip_gap = vec4(0.5, 0.14, 0.26, 0.62);     // a lane's chance to skip; the skip's metres (least, most); where it starts (share of the finger)
uniform vec4 grip_shed = vec4(-1.0, 0.084, 0.117, 0.03); // s since the contact; the amber out, the gold out, each lane's own offset
uniform vec4 grip_kite = vec4(0.8, 0.2, 0.1, 2.0);       // mode 1: m ahead of the point, behind, half-width, the rim (px)
uniform vec4 grip_shards = vec4(0.28, 0.4, 0.09, 0.11);  // mode 1: a barb's length (least, most), its width at the fat end
uniform vec4 grip_steps = vec4(3.0, 0.7, 0.42, 25.0);    // mode 1: frames whole, the two steps' sizes, the fan (degrees)

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

// 0,0 -> k.xy -> k.zw -> 1,1, straight between
float grip_knots(float x, vec4 k) {
	return x < k.x ? x * k.y / max(k.x, 1e-4)
		: x < k.z ? k.y + (x - k.x) * (k.w - k.y) / max(k.z - k.x, 1e-4)
		: k.w + (x - k.z) * (1.0 - k.w) / max(1.0 - k.z, 1e-4);
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
	float tongue = grip_tips.x / body;
	float wsum = 0.0;
	for (int i = 0; i < grip_lane_n; i++) wsum += grip_lanes[i * 4] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(float(i) + 0.37, grip_seed)) - 1.0));
	vec3 col = vec3(0.0);
	float cov = 0.0, lo = 0.0, e0 = 0.0;
	for (int i = 0; i < grip_lane_n; i++) {
		float fi = float(i);
		float w = grip_lanes[i * 4] * (1.0 + grip_lane.x * (2.0 * fx_hash(vec2(fi + 0.37, grip_seed)) - 1.0)) / wsum;
		float l = (a - lo) / w;   // 0..1 across this lane
		lo += w;
		float j1 = 2.0 * fx_hash(vec2(fi + 1.91, grip_seed)) - 1.0, j2 = 2.0 * fx_hash(vec2(fi + 3.13, grip_seed)) - 1.0, j3 = 2.0 * fx_hash(vec2(fi + 5.71, grip_seed)) - 1.0;
		float tc = grip_lanes[i * 4 + 1], tm = grip_lanes[i * 4 + 2];
		tc = tc > 0.0 ? max(tc + grip_lane.y * j1, 0.03) : 0.0;
		tm = tm > 0.0 ? max(tm + grip_lane.y * j2, tc) : tc;
		float te = clamp(grip_lanes[i * 4 + 3] + grip_lane.y * j3, tm, 1.0);
		// leaving: this lane's amber drops, then its gold, at its own time
		float end = grip_shed.x >= grip_shed.z + grip_shed.w * j2 ? tc : grip_shed.x >= grip_shed.y + grip_shed.w * j1 ? tm : te;
		if (i == 0) e0 = end;
		if (end <= 1e-3) continue;
		// the finger: the lane whole, then over its last metres to a point of its own
		float p = mix(0.25, 0.75, fx_hash(vec2(fi + 7.3, grip_seed))), pm = max(p, 1.0 - p);
		float f = clamp((end - t) / max(min(grip_tips.y / body, grip_tips.z * end), 1e-4), 0.0, 1.0);
		float l0 = p * (1.0 - f), l1 = p + (1.0 - p) * f, pxl = w / fa;
		float c = clamp(min(l - l0, l1 - l) * pxl + 0.5, 0.0, 1.0) * clamp((l1 - l0) * pxl, 0.0, 1.0) * clamp((end - t) / ft + 0.5, 0.0, 1.0);
		// the skip: bare ground across the lane, cut on a slant, the paint back after it
		float g0 = te * mix(grip_gap.w, 0.8, fx_hash(vec2(fi + 11.1, grip_seed)));
		float g1 = g0 + mix(grip_gap.y, grip_gap.z, fx_hash(vec2(fi + 13.9, grip_seed))) / body;
		if (fx_hash(vec2(fi + 9.7, grip_seed)) < grip_gap.x && g1 < te - 1.5 * tongue) {
			float tg = t - tongue * (l - 0.5);
			c *= 1.0 - clamp(min(tg - g0, g1 - tg) / ft + 0.5, 0.0, 1.0);
		}
		// the bands: each ends in this lane at its own distance, in a short tongue on the lane's point
		float tb = t + tongue * abs(l - p) / pm;
		float gb = length(vec2(ft, tongue * fa / (w * pm)));
		vec3 k = mix(fx_edge, fx_mid, clamp((tm - tb) / gb + 0.5, 0.0, 1.0));
		k = mix(k, fx_core, clamp((tc - tb) / gb + 0.5, 0.0, 1.0));
		col += k * c;
		cov += c;
	}
	col /= max(cov, 1e-4);
	cov = min(cov, 1.0);
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

// a fat wedge: its flat fat end at `at`, to a point `len` on along `dir`
float grip_wedge(vec2 p, vec2 at, vec2 dir, float len, float hw) {
	vec2 dd = p - at;
	float x = dot(dd, dir), y = abs(dot(dd, vec2(-dir.y, dir.x)));
	return max((y - hw * (1.0 - x / len)) * len / length(vec2(len, hw)), -x);
}

vec4 grip_contact(vec2 uv) {
	vec2 q = (uv - 0.5) * 2.0 * grip_size;
	float f = floor(grip_thin + 0.5) - grip_steps.x;   // under 0: whole; 0 and 1: the two steps out
	float k = f < 0.0 ? 1.0 : f < 1.0 ? grip_steps.y : f < 2.0 ? grip_steps.z : 0.0;
	if (k <= 0.0) return vec4(0.0);
	float s = grip_size.x / 1.5 * k;   // the contact's size (1 = Sunder's on one body)
	float hw = grip_kite.z * s, ahead = grip_kite.x * s;
	float len = q.x > 0.0 ? ahead : grip_kite.y * s;
	float sd = (abs(q.y) - hw * (1.0 - abs(q.x) / len)) * len / length(vec2(len, hw));
	for (int i = 0; i < 3; i++) {
		float fi = float(i);
		if (fi >= grip_sparks - max(f + 1.0, 0.0) || f >= 1.0) break;
		float h1 = fx_hash(vec2(fi * 1.7 + 0.3, grip_seed)), h2 = fx_hash(vec2(fi * 2.3 + 7.1, grip_seed)), h3 = fx_hash(vec2(fi * 3.1 + 3.3, grip_seed));
		float side = mod(fi + floor(grip_seed), 2.0) < 0.5 ? 1.0 : -1.0;
		float xb = mix(0.06, 0.42, h1) * ahead;
		float ang = side * radians(mix(0.4, 1.0, h2) * grip_steps.w);
		sd = min(sd, grip_wedge(q, vec2(xb, side * 0.8 * hw * (1.0 - xb / ahead)), vec2(cos(ang), sin(ang)), mix(grip_shards.x, grip_shards.y, h3) * s, 0.5 * mix(grip_shards.z, grip_shards.w, h2) * s));
	}
	float cov = clamp(0.5 - sd / grip_px, 0.0, 1.0);
	float white = clamp(0.5 - sd / grip_px - grip_kite.w * (2.0 - grip_core), 0.0, 1.0);
	return vec4(mix(fx_mid, fx_core, white), cov);
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
