// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 4): the STROKE her blade leaves, the contact where it meets a body,
// and the hot edge her blade keeps between a chain's cuts. Steel family (fx_cel.gdshaderinc: fx_core white-gold, fx_mid
// gold, fx_edge amber), drawn after the grade (FxCel.Apply): flat bands, hard steps, never added light.
// Mode 0, the stroke: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from the
// drawn tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   ONE fast brushed sweep, a heavy-headed comma. Its outer (leading) edge is the tip's path, clean and hard, the house
//   glow past it. Its inner edge starts part way up the blade (grip_shape.y of it) and runs out to the tip's path along
//   the length (power grip_shape.z), down to a brush tail that is cut where it gets narrower than grip_shape.x (never a
//   hairline); a link's thread (the first grip_thread metres) keeps that width, drawn to a point over grip_point. At the head the blade
//   itself is lit white from the comma down to the guard (grip_lit), so the stroke is joined to her hand.
//   The paint is the house brush, fx_stroke_at, given a ONE-SIDED across (0 the tip's path, 1 the inner edge) so that
//   its three bands are three NESTED commas: the core (white-gold) the widest at the head and the shortest (it closes
//   to a point on the leading edge grip_reach.x of the way back), the mid (gold) inside it reaching grip_reach.y, the
//   edge (amber) the rest: the tail. The amber's inner part is the brush run dry (from grip_bands.z of the width): its
//   bristles are laid in the path's own metres and the screen's pixels (grain_at), streaks along the sweep that end
//   where the comma narrows past them, and they stay where they were painted as the stroke grows and runs up. The
//   tail's last grip_dry.x metres are dry across their whole width.
//   Leaving is the view's: the tail runs up to the blade (a shorter comma each frame) and the bands step the amber,
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
	float sb = grip_total - u;   // metres behind the blade (negative: past it)
	// 0 at the head (the blade now), 1 at the stroke's tail (a link's thread runs on behind it at the tail's width)
	float t = clamp(sb / max(grip_total - grip_thread, 1e-3), 0.0, 1.0);
	// the comma: the blade's share painted in from the tip's path. Under the narrowest painted width (grip_shape.x) the
	// tail is CUT: its end is inside the brush, never a hairline. (A link's thread keeps that width, drawn to a point.)
	float thread = step(u, grip_thread) * step(1e-4, grip_thread);
	float share = grip_shape.y * pow(1.0 - t, grip_shape.z);
	float painted = max(fx_hard(grip_shape.x, share, 0.0), thread);
	share = max(mix(share, grip_shape.x * sqrt(clamp(u / max(grip_point, 1e-3), 0.0, 1.0)), thread), 1e-4);
	// where the painted tail ends (m from the ribbon's own end): the dry metres are counted from there
	float u_end = grip_thread > 1e-4 ? 0.0 : grip_total * pow(clamp(grip_shape.x / max(grip_shape.y, 1e-4), 0.0, 1.0), 1.0 / grip_shape.z);
	float vm = 1.0 - uv.y;   // shares of the blade in from the tip's path (negative: past it)
	float a = vm / share;    // 0 the tip's path, 1 the inner edge
	// the brush's along: hot through the body, dry over the tail's last metres
	float alb = mix(grip_dry.y, grip_dry.z, smoothstep(0.0, 1.0, (u - u_end) / max(grip_dry.x, 1e-3)));
	// the house brush's own numbers at this heat (fx_stroke_at: its core ends 0.24 x hot in from its centerline, its mid
	// at 0.48..0.66, its feather starts at 1 - fx_stroke_shape.y): the across below lands the bands' ends on them
	float hot = smoothstep(0.15, 1.0, alb);
	float kc = 0.24 * hot, km = mix(0.48, 0.66, hot), kf = 1.0 - fx_stroke_shape.y;
	// the bands, three nested commas: the core and the mid each close to a point on the leading edge
	float ac = grip_bands.x * (1.0 - pow(clamp(t / max(grip_reach.x, 1e-3), 0.0, 1.0), grip_reach.z));
	float am = max(grip_bands.y * (1.0 - pow(clamp(t / max(grip_reach.y, 1e-3), 0.0, 1.0), grip_reach.z)), ac);
	float af = max(grip_bands.z, am);
	float ax = clamp(a, 0.0, 1.0);
	float d = ax < ac ? kc * ax / max(ac, 1e-4)
		: ax < am ? kc + (km - kc) * (ax - ac) / max(am - ac, 1e-4)
		: ax < af ? km + (kf - km) * (ax - am) / max(af - am, 1e-4)
		: kf + (1.0 - kf) * (ax - af) / max(1.0 - af, 1e-4);
	// (behind the core's point the leading edge is the mid's: the boundaries' waver must not fleck it white)
	d = max(d, (kc + 1.3 * fx_bristle.w) * (1.0 - smoothstep(0.0, 0.06, ac)));
	// past the inner edge: the brush's own glow, in the glow's metres
	d += max(a - 1.0, 0.0) * share * grip_blade / grip_glow;
	vec2 at = vec2(vm * grip_blade / (grip_grain.x * grip_px), (u + grip_u0) / grip_grain.y);
	vec4 s = fx_stroke_at(d, alb, 0.0, at - vec2(d * fx_bristle.x * 0.5, alb * fx_bristle.y));
	// past the tip's path: the house glow off a clean edge
	vec4 g = fx_cel(fx_t.x - max(-vm, 0.0) * grip_blade / grip_glow - 1e-3, alb);
	g.a *= smoothstep(0.0, 0.25, alb);
	vec4 c = mix(g, s, fx_hard(0.0, vm, 0.0));
	// the head ends on the blade, the tail at its point
	c.a *= grip_in(0.0, -sb) * step(0.0, u) * painted;
	// the lit blade: white on the blade's own line from the tip's path through the comma's head and on down toward the
	// guard, drawn to a point there
	float lit_end = grip_shape.y + (1.0 - grip_shape.y) * grip_lit.y;
	float k = clamp((vm - grip_shape.y) / max(lit_end - grip_shape.y, 1e-4), 0.0, 1.0);
	float lit = grip_in(0.5 * grip_lit.x * (1.0 - 0.8 * k), abs(sb)) * step(0.0, vm) * step(vm, lit_end) * step(1e-3, grip_lit.y);
	return vec4(mix(c.rgb, fx_core, lit), max(c.a, lit));
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
