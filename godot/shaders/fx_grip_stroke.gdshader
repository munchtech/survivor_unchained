// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 3): the SAIL her blade leaves, the contact where it meets a body,
// and the hot edge her blade keeps between a chain's cuts. Steel family (fx_cel.gdshaderinc: fx_core white-gold, fx_mid
// gold, fx_edge amber), drawn after the grade (FxCel.Apply): flat bands, hard steps, never added light.
// Mode 0, the sail: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from the
// drawn tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   The outer edge is the tip's path, clean and hard, the house glow past it. The inner edge: at the head the blade's
//   whole lit share (grip_shape.y), then out to the tip's path fast (power grip_shape.z), so the head third is a sail and
//   the rest a whip-thin tail (grip_shape.x of the blade) drawn to a point; the first grip_thread metres are a link's
//   thread (the tail's width throughout). The paint is the house brush, fx_stroke_at, given a ONE-SIDED across (0 the
//   tip's path, 1 the inner edge) through the knots grip_across, so its core (white-gold) is the widest band, its mid
//   (gold) a rim on the trailing side and its feathered edge (amber) the last dry bristles; its along through the knots
//   grip_along (the tail's end dry, the rest hot). The bristles are laid in the path's own metres and the screen's
//   pixels (grain_at), so they stay where they were painted as the trail grows and runs up.
//   Leaving is the view's: the tail runs up to the blade (a shorter ribbon each frame) and the knots step the amber,
//   then the gold, out: the white is last.
// Mode 1, the contact (a quad facing the camera, +x the blade's travel): a white cut-through with a gold rim, longer
//   ahead of its kernel than behind, whole for two frames and thin for one (grip_thin = frames since the contact),
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
uniform vec3 grip_shape = vec3(0.03, 1.0, 2.7);          // the tail's width, the head's (shares of the blade), the power
uniform vec4 grip_across = vec4(0.62, 0.22, 0.8, 0.62);  // across knots: (share of the width, the brush's across) x 2
uniform vec4 grip_along = vec4(0.14, 0.4, 0.34, 0.86);   // along knots: (share of the length, the brush's along) x 2
uniform vec2 grip_grain = vec2(3.0, 0.45);               // a bristle (px across), a streak (m along)
uniform float grip_glow = 0.28;   // the glow's unit (m): fx_glow's width and reach are shares of it
uniform float grip_point = 0.12;  // the tail's last metres, drawn to a point
uniform float grip_core = 1.0;    // mode 1: the white's share of the kernel
uniform float grip_thin = 0.0;    // mode 1: frames since the contact; mode 2: 0 hot, 1, 2 stepping out
uniform float grip_px = 0.012;    // a pixel here (m)
uniform float grip_seed = 0.0;
uniform vec2 grip_size = vec2(1.5, 0.5);
uniform float grip_sparks = 4.0;
uniform float grip_age = 0.0;

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

// 0,0 -> k.xy -> k.zw -> 1,1, straight between
float grip_knots(float x, vec4 k) {
	return x < k.x ? x * k.y / max(k.x, 1e-4)
		: x < k.z ? k.y + (x - k.x) * (k.w - k.y) / max(k.z - k.x, 1e-4)
		: k.w + (x - k.z) * (1.0 - k.w) / max(1.0 - k.z, 1e-4);
}

vec4 grip_trail(vec2 uv) {
	float u = uv.x;
	float al0 = clamp(u / max(grip_total, 1e-3), 0.0, 1.0);
	float als = clamp((u - grip_thread) / max(grip_total - grip_thread, 1e-3), 0.0, 1.0);
	float share = grip_shape.x + (grip_shape.y - grip_shape.x) * pow(als, grip_shape.z);
	share *= sqrt(clamp(u / max(grip_point, 1e-3), 0.0, 1.0));
	share = max(share, 1e-4);
	float vm = 1.0 - uv.y;   // shares of the blade in from the tip's path (negative: past it)
	float a = vm / share;    // 0 the tip's path, 1 the inner edge
	float alb = grip_knots(al0, grip_along);
	// past the inner edge: the brush's own glow, in the glow's metres
	float d = grip_knots(clamp(a, 0.0, 1.0), grip_across) + max(a - 1.0, 0.0) * share * grip_blade / grip_glow;
	vec2 at = vec2(vm * grip_blade / (grip_grain.x * grip_px), (u + grip_u0) / grip_grain.y);
	vec4 s = fx_stroke_at(d, alb, 0.0, at - vec2(d * fx_bristle.x * 0.5, alb * fx_bristle.y));
	// past the tip's path: the house glow off a clean edge
	vec4 g = fx_cel(fx_t.x - max(-vm, 0.0) * grip_blade / grip_glow - 1e-3, alb);
	g.a *= smoothstep(0.0, 0.25, alb);
	vec4 c = mix(g, s, fx_hard(0.0, vm, 0.0));
	// the head ends on the blade, the tail at its point
	c.a *= grip_in(grip_total, u) * step(0.0, u);
	return c;
}

float grip_tear(vec2 p, vec2 at, vec2 dir, float len, float asp) {
	vec2 dd = p - at;
	vec2 r = vec2(dot(dd, dir), dot(dd, vec2(-dir.y, dir.x)));
	float k = clamp(-r.x / len, 0.0, 1.0);
	float hw = len / asp * 0.5;
	float sd = r.x > 0.0 ? length(r) - hw : abs(r.y) - hw * (1.0 - k);
	return max(sd, -r.x - len);
}

vec4 grip_contact(vec2 uv) {
	vec2 q = (uv - 0.5) * 2.0 * grip_size;
	float s = grip_size.x / 1.5;   // the contact's size (1 = Sunder's on one body)
	float f = floor(grip_thin + 0.5);
	float xk = -0.2 * s;
	float ahead = q.x - xk;
	float sd = 1.0;
	if (f < 2.5) {
		float reach = (ahead > 0.0 ? 1.05 : 0.6) * s * (f < 0.5 ? 0.8 : 1.0);
		float k = clamp(abs(ahead) / reach, 0.0, 1.0);
		float nw = 0.05 * s * pow(1.0 - k, 1.5) * (f < 1.5 ? 1.0 : 0.5);
		sd = abs(q.y) - nw + step(1.0, k);
		if (f < 1.5) sd = min(sd, (length(vec2(ahead / 1.9, q.y)) - 0.085 * s));
	}
	float rim = 1.6 * grip_px;
	float aa = max(fwidth(sd), 1e-4);
	float cov = 1.0 - smoothstep(-aa, aa, sd);
	float white = 1.0 - smoothstep(-aa, aa, sd + rim * (2.0 - grip_core));
	vec3 c = mix(fx_mid, fx_core, white);
	// the tears: thrown along the travel, a fan of them, each shorter by the frame
	float sp = 0.0;
	for (int i = 0; i < 6; i++) {
		float fi = float(i);
		if (fi >= grip_sparks) break;
		float h1 = fx_hash(vec2(fi * 1.7 + 0.3, grip_seed)), h2 = fx_hash(vec2(fi * 2.3 + 7.1, grip_seed)), h3 = fx_hash(vec2(fi * 3.1 + 3.3, grip_seed));
		float life = 4.0 + floor(h3 * 3.99);
		if (f >= life) continue;
		float ang = (h1 - 0.5) * 1.1;
		vec2 dir = vec2(cos(ang), sin(ang));
		float dist = (0.12 + (5.5 + 6.0 * h2) * (1.0 - exp(-10.0 * grip_age)) / 10.0) * s;
		float len = mix(0.2, 0.07, f / life) * s;
		float t = grip_tear(q, vec2(xk, 0.0) + dir * dist, dir, len, 6.5);
		float ta = max(fwidth(t), 1e-4);
		sp = max(sp, 1.0 - smoothstep(-ta, ta, t));
	}
	c = mix(c, fx_core, sp * (1.0 - cov));
	return vec4(c, max(cov, sp));
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
	vec4 c = grip_mode == 0 ? grip_trail(UV) : grip_mode == 1 ? grip_contact(UV) : grip_edge(UV, COLOR.r);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
