// Her held grip's cut (src/Fx/BattleFx.Grip.cs, take 2): the trail her blade leaves and the contact where it meets a
// body, in the steel family's three bands (fx_cel.gdshaderinc: fx_core white-gold, fx_mid gold, fx_edge amber), drawn
// after the grade (FxCel.Apply), flat bands with hard steps, never added light.
// Mode 0, the trail: a ribbon built each frame from the blade's own samples. UV.x = metres along the tip's path from
// the tail (0) to the head (grip_total: the blade now); UV.y = 0 at the guard, 1 at the tip, and a margin past it.
//   the stroke hugs the tip's path: its outer edge clean and hard (the blade's edge), grip_w wide at the head and
//   drawn to a point at the tail; white-gold from the outer edge in (grip_core of the width at the head), gold
//   trailing inside it with a dry-brush inner edge, amber only where the tail runs dry;
//   in from the stroke toward the guard: a thin flat smear of the white in bristle streaks (the blade's ghost), over
//   the head's half of the trail only; and one bright line on the blade itself at the head.
//   Going out (grip_thin 1, 2): the tail cut forward (grip_cut), the smear and the head's line gone, then the white
//   sliver alone. Steps, no fades.
// Mode 1, the contact (a quad facing the camera, +x the blade's travel): a white cut-through with a gold rim, longer
//   ahead of its kernel than behind, whole for two frames and thin for one (grip_thin = frames since the contact),
//   and a few hard tears thrown along the travel that fly on for 4-7 frames (grip_age seconds).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform int grip_mode = 0;
uniform float grip_total = 1.0;
uniform float grip_blade = 1.0;   // the blade's length guard to tip (m)
uniform float grip_w = 0.28;      // the stroke's width at the head (m)
uniform float grip_core = 0.5;    // the white's share of the width at the head (mode 1: the white's share of the kernel)
uniform float grip_smear = 0.34;  // the inner smear's flat coverage
uniform float grip_cut = 0.0;     // the tail cut forward, a share of the length
uniform float grip_thin = 0.0;    // mode 0: 0 whole, 1, 2 going out; mode 1: frames since the contact
uniform float grip_px = 0.012;    // a pixel here (m)
uniform float grip_seed = 0.0;
uniform vec2 grip_size = vec2(1.5, 0.5);
uniform float grip_sparks = 4.0;
uniform float grip_age = 0.0;

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

vec4 grip_trail(vec2 uv) {
	float al0 = uv.x / max(grip_total, 1e-3);
	float al = (al0 - grip_cut) / max(1.0 - grip_cut, 1e-3);
	if (al <= 0.0) return vec4(0.0);
	float alc = min(al, 1.0);
	float vm = (1.0 - uv.y) * grip_blade;   // metres in from the tip's path (negative: past it)
	int thin = int(grip_thin + 0.5);
	// the brush: bristles run along the trail (each about 2.5 px wide, streaks about 0.3 m long)
	vec2 sp = vec2(vm / (2.5 * grip_px), uv.x / 0.3) + vec2(grip_seed * 17.3, grip_seed * 5.1);
	float b = clamp(0.5 + 0.42 * (fx_gnoise(sp) * 0.65 + fx_gnoise(sp * vec2(2.3, 1.7) + vec2(3.7, 9.3)) * 0.35), 0.0, 1.0);
	float wander = fx_gnoise(vec2(uv.x * 1.6 + grip_seed * 3.1, 0.5 + grip_seed));

	// the stroke: to a point at the tail, thinner as it goes out
	float w = grip_w * pow(alc, 0.75) * (thin == 0 ? 1.0 : thin == 1 ? 0.78 : 0.5);
	w = max(w, 1e-4);
	float d = vm / w;   // 0 the outer edge (the tip's path), 1 the stroke's inner edge
	float dv = d + 0.16 * ((b - 0.5) * 1.6 + wander * 0.6) * smoothstep(0.0, 0.3, d);
	float hot = smoothstep(0.1, 0.55, alc);
	float k_core = thin == 2 ? 0.8 : grip_core * hot;
	float core = grip_in(k_core, dv) * step(1e-3, k_core);
	// the dry brush: the inner edge's feather, and the whole stroke toward the tail
	float feather = thin == 2 ? 0.2 : 0.34;
	float edge_in = clamp((dv - (1.0 - feather)) / feather, 0.0, 1.0);
	float dry = max(edge_in, 0.62 * (1.0 - smoothstep(0.0, 0.32, alc)));
	float body = fx_hard(dry, b * 0.98 + 0.01, 0.0) * grip_in(1.0, dv) * fx_hard(0.0, vm, 0.0);
	// amber where the tail runs dry (a ragged change, bristle by bristle), and the last bristles of the inner edge
	float amber = max(grip_in(0.26 + (b - 0.5) * 0.22, alc), fx_hard(0.86, dv, 0.0) * (1.0 - hot * 0.6));
	vec3 c = mix(fx_mid, fx_edge, amber);
	c = mix(c, fx_core, core);
	float a = body;

	// the blade's ghost, in from the stroke toward the guard: flat, streaked, the head's half only
	if (thin == 0 && vm > 0.0) {
		float h = clamp((vm - w) / max(grip_blade - w, 1e-3), 0.0, 1.0);
		float fresh = (alc - 0.42) / 0.58;
		float thr = 0.3 + 0.5 * h + 0.75 * (1.0 - clamp(fresh, 0.0, 1.0));
		float sm = fx_hard(thr, b, 0.0) * step(0.0, fresh) * step(w, vm);
		float sa = grip_smear * (fresh > 0.55 ? 1.0 : 0.6) * sm;
		c = mix(fx_core, c, a / max(a + sa * (1.0 - a), 1e-4));
		a = a + sa * (1.0 - a);
		// the blade itself, lit at the head
		float line = fx_hard(1.0 - 2.2 * grip_px / max(grip_total, 1e-3) * mix(2.4, 1.0, uv.y), al0, 0.0) * step(0.02, uv.y) * grip_in(1.0, uv.y);
		c = mix(c, fx_core, line);
		a = max(a, line);
	}
	// the head ends on the blade
	a *= grip_in(1.0, al0);
	// the glow past the outer edge: the edge band's light on the dark
	float out_d = max(0.0, -vm) / grip_w;
	float g = mix(fx_glow.w, fx_glow.z, alc) * (thin == 2 ? 0.4 : 1.0) * exp(-out_d / max(fx_glow.x, 1e-3)) * (1.0 - smoothstep(fx_glow.y * 0.6, fx_glow.y, out_d))
		* step(vm, 0.0) * grip_in(1.0, al0) * smoothstep(0.0, 0.2, alc);
	return vec4(mix(fx_glow_color, c, step(1e-3, a)), max(a, g * 0.8));
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
		float ang = (h1 - 0.5) * 1.1 + (fi < 0.5 ? 3.14159 : 0.0) * 0.0;
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

void fragment() {
	vec4 c = grip_mode == 0 ? grip_trail(UV) : grip_contact(UV);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
