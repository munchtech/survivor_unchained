// P7 (the skills lead): Heroic Leap, Shield Charge, the dash, Bladestorm and Iron Vow in the FX language
// (docs/design/FX_LANGUAGE.md; shaders/fx_cel.gdshaderinc), drawn after the grade (FxAfter) so a band's hex is its
// displayed color. Round 3 (9 Nov, against judge r2): every light shape is p7_stroke (L1's fx_stroke) or p7_wave (the
// travelling wavefront built on it, fx_p7_stroke.gdshaderinc) plus a coverage cap (p7_alpha); the sizes come from the
// view in shares of the quad, worked out from the px in data/look/fx_language.json "p7". Shapes (p7_mode):
//   0 target  the leap's mark: a wavefront standing at the hit radius (front 1), p7_arcs arcs growing to p7_cover of the
//             ring (their ends tapering to points), p7_lead / p7_trw its edge and trailing band; life p7_fade.
//   1 star    a hit (17 the same): p7_count tapered spikes of varied length round a small heart (p7_heart), their roots
//             p7_root half-wide (so the middle never merges into a slab), p7_streaks thin streaks running out between them
//             over 3 samples (p7_t); life p7_fade (stepped by the view). Flat on the ground, or facing the camera (p7_bill).
//   2 ribbon  a strip mesh (UV.x its along: 0 tail .. 1 head; UV.y across), tapering to a point at the tail.
//   3 ghost   an afterimage (her pose): a ~2 px amber rim at her silhouette, the core clear (and depth left alone).
//   4 glint   the press: one three-band glint (a hot heart and a lens streak through it, camera-facing); life p7_fade.
//   5 wave    a wavefront running out (16 the same): front p7_prog, p7_lead / p7_trw, p7_fall how far it has run.
//  12 crescent the charge's press: an arc of light on the shield's face, its middle toward p7_dir2 (screen).
//   6-11      part B (fx_p7_b.gdshaderinc): smear, seam, dome rim, store glow, nick, pulse.
#include "res://shaders/fx_cel.gdshaderinc"
#include "res://shaders/fx_p7_stroke.gdshaderinc"

uniform int p7_mode = 0;
uniform float p7_t = 0.0;      // seconds since it began
uniform float p7_prog = 0.0;   // ring closure / shove reach 0..1
uniform float p7_fade = 0.0;   // 0 whole .. 1 gone (stepped by the caller)
uniform float p7_alpha = 1.0;  // the coverage cap (the ring's half opacity)
uniform float p7_seed = 0.0;
uniform float p7_bill = 0.0;   // 1: the quad faces the camera
uniform float p7_width = 0.08; // ring / shove stroke width (share of the radius)
uniform float p7_spin = 0.0;   // storm: blade 0's head angle
uniform float p7_dir = -1.0;   // storm: which way the heads move (the sign of the angle's change)
uniform float p7_count = 4.0;  // storm: blades
uniform float p7_trail = 1.75; // storm: the trail's arc (radians)
uniform float p7_lvl = 0.6;    // scar / shell: the heat at its heart
uniform vec2 p7_dir2 = vec2(1.0, 0.0); // streak: the flight, on screen
uniform float p7_y0 = 0.0;    // pulse: her feet (world y)
uniform float p7_h = 1.8;     // pulse: her height
uniform float p7_lead = 0.05;  // wave: the leading edge's width (share of the quad's half-size)
uniform float p7_trw = 0.06;   // wave: the trailing band's depth
uniform float p7_fall = 0.0;   // wave: how far it has run to its reach (width and coverage -> 0 at 1)
uniform float p7_cover = 1.0;  // target: the share of the ring its arcs cover
uniform float p7_arcs = 3.0;   // target: its arcs
uniform float p7_root = 0.06;  // star: a spike's root half-width
uniform float p7_heart = 0.05; // star: the heart's radius
uniform float p7_streaks = 7.0; // star: the thin streaks between the spikes
varying float p7_wy;

void vertex() {
	// the pulse lies on her own surface: pushed out a little along it so her depth twin does not fight it
	if (p7_mode == 11) VERTEX += NORMAL * 0.014;
	p7_wy = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
	if (p7_bill > 0.5) {
		float s = length(MODEL_MATRIX[0].xyz);
		mat4 bb = mat4(INV_VIEW_MATRIX[0] * s, INV_VIEW_MATRIX[1] * s, INV_VIEW_MATRIX[2] * s, MODEL_MATRIX[3]);
		MODELVIEW_MATRIX = VIEW_MATRIX * bb;
	}
}

const float P7_TAU = 6.2831853;
const float P7_SAMPLE = 0.0833333;

// a stepped erosion: 0 for the first `hold` seconds, then one more step every sample
float p7_steps(float t, float hold) { return t < hold ? 0.0 : floor((t - hold) / P7_SAMPLE) + 1.0; }

// (solver A, 9 Nov: the r1 rebuild) every light shape below computes (across, along, life) for its pixel and takes its
// bands and its life from p7_stroke(); on top only the coverage cap (p7_alpha). Composite of several strokes: the one
// with the most coverage wins (one painted layer, never added light).
vec4 p7_over(vec4 o, vec4 c) { return c.a > o.a ? c : o; }

// A stroke along a ray from the centre at angle th, `len` long (its root the head, its tip the tail), its root half-width
// hw: (across, along) for point p (r, a its polar form). Returns vec2(across, along); along < 0 means off it.
vec2 p7_ray(vec2 p, float th, float len, float hw) {
	vec2 d = vec2(cos(th), sin(th));
	float u = dot(p, d), v = dot(p, vec2(-d.y, d.x));
	if (u < 0.0 || u > len) return vec2(9.0, -1.0);
	return vec2(v / hw, 1.0 - u / len);
}

// (0) the leap's target: the wavefront standing at the hit radius (its outer edge the radius: marked = hit); p7_arcs
// arcs, each centred in its sector, growing to p7_cover of it, their ends tapering to points; whole at cover 1.
vec4 p7_ring(vec2 p) {
	float tip = 1.0;
	if (p7_cover < 0.999) {
		float s = fract(atan(p.y, p.x) / P7_TAU * p7_arcs + p7_seed);
		float h = 0.5 * p7_cover, dc = abs(s - 0.5);
		if (dc > h) return vec4(0.0);
		tip = clamp((h - dc) / max(0.3 * h, 0.01), 0.0, 1.0);
	}
	vec4 o = p7_wave(p, 1.0, p7_lead, p7_trw, 0.0, p7_fade, tip);
	o.a *= p7_alpha;
	return o;
}

// (1, 17) the star: one bold shape. p7_count tapered spikes (one long, the rest a half to 0.85 of it), their roots p7_root
// half-wide at a small heart; p7_streaks thin streaks running out between them over 3 samples; life p7_fade.
vec4 p7_star(vec2 p) {
	float life = p7_fade;
	vec4 o = p7_stroke(length(p) / max(p7_heart, 1e-3) * 0.8, 0.9, life);
	float n = clamp(p7_count, 3.0, 8.0);
	for (float i = 0.0; i < 8.0; i += 1.0) {
		if (i >= n) break;
		float h = fx_hash(vec2(i, p7_seed));
		float th = (i + (h - 0.5) * 0.5) / n * P7_TAU + p7_seed;
		float hl = fx_hash(vec2(p7_seed, i * 1.7));
		float len = i < 0.5 ? 1.0 : mix(0.5, 0.85, hl);
		vec2 q = p7_ray(p, th, len, p7_root);
		if (q.y >= 0.0) o = p7_over(o, p7_stroke(q.x, min(q.y, 0.9), life));
	}
	float run = clamp(p7_t / (3.0 * P7_SAMPLE), 0.0, 1.0);
	float m = clamp(p7_streaks, 0.0, 8.0);
	for (float j = 0.0; j < 8.0; j += 1.0) {
		if (j >= m) break;
		float h = fx_hash(vec2(j * 3.1, p7_seed + 1.0));
		float th = (j + 0.5 + (h - 0.5) * 0.6) / max(m, 1.0) * P7_TAU + p7_seed;
		float len = mix(0.12, 0.2, h);
		float head = mix(0.35, mix(0.75, 0.95, fract(h * 7.0)), 1.0 - (1.0 - run) * (1.0 - run));
		vec2 d = vec2(cos(th), sin(th));
		float u = dot(p, d), v = dot(p, vec2(-d.y, d.x));
		if (u > head - len && u < head) o = p7_over(o, p7_stroke(v / (p7_root * 0.3), min(0.9, (u - (head - len)) / len), max(life, 0.34)));
	}
	return o;
}

vec4 p7_ribbon(vec2 uv) {
	// a strip (UV.x its along: 0 the tail .. 1 the head; UV.y 0..1 across): the stroke tapers it to a point at the tail
	// (the view's fx_stroke_shape.z 0) and rounds its head; nothing is cut square
	vec4 o = p7_stroke(uv.y * 2.0 - 1.0, min(uv.x, 0.995), p7_fade);
	o.a *= smoothstep(0.0, 0.6, uv.x); // its coverage 1 -> 0 toward the tail
	return o;
}

// An afterimage: her pose as an amber rim only (~2 px in from her silhouette, measured in pixels of the facing term's
// own slope), the core clear; the rim steps thinner and out over p7_life seconds.
uniform float p7_life = 0.15;
vec4 p7_ghost(vec2 uv, vec3 n, vec3 v) {
	float e = abs(dot(normalize(n), normalize(v)));
	float px = e / max(fwidth(e), 1e-4);
	float k = floor(p7_t / (p7_life / 3.0));
	float w = 1.5 * (1.0 - 0.2 * k);
	vec4 o = p7_stroke((px - w) / w, 0.9, 0.67);
	o.a *= p7_alpha * (1.0 - k / 3.0);
	return o;
}

// (4) the press: one three-band glint, a hot round heart and a lens streak through it (both ends tapered to points)
vec4 p7_glint(vec2 p) {
	vec2 q = vec2(p.x * 0.97 + p.y * 0.26, p.y * 0.97 - p.x * 0.26);
	vec4 o = p7_stroke(length(p) / 0.4, 0.9, p7_fade);
	return p7_over(o, p7_stroke(q.y / 0.2, 0.9 * (1.0 - abs(q.x)), p7_fade));
}

// (5, 16) a wavefront running out to the quad's edge (the reach): front p7_prog
vec4 p7_shove(vec2 p) {
	vec4 o = p7_wave(p, p7_prog, p7_lead, p7_trw, p7_fall, p7_fade, 1.0);
	o.a *= p7_alpha;
	return o;
}

// (12) the charge's press: an arc of light on the shield's face (camera-facing), its middle (the head) toward where she
// drives (p7_dir2, on screen, y down), its ends tapering back round the shield.
vec4 p7_crescent(vec2 p) {
	float r = length(p);
	vec2 f = normalize(p7_dir2);
	float ph = acos(clamp(dot(p / max(r, 1e-4), f), -1.0, 1.0));
	float along = 0.9 * (1.0 - ph / 1.45);
	if (along <= 0.0) return vec4(0.0);
	vec4 o = p7_stroke((r - 0.72) / 0.2, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

#include "res://shaders/fx_p7_b.gdshaderinc"

void p7_frag(vec2 uv, vec3 n, vec3 v, out vec3 albedo, out float alpha) {
	vec2 p = uv * 2.0 - 1.0;
	vec4 c;
	if (p7_mode == 0) c = p7_ring(p);
	else if (p7_mode == 1 || p7_mode == 17) c = p7_star(p);
	else if (p7_mode == 2) c = p7_ribbon(uv);
	else if (p7_mode == 3) c = p7_ghost(uv, n, v);
	else if (p7_mode == 4) c = p7_glint(p);
	else if (p7_mode == 5 || p7_mode == 16) c = p7_shove(p);
	else if (p7_mode == 6) c = p7_storm(p);
	else if (p7_mode == 7) c = p7_scar(uv);
	else if (p7_mode == 8) c = p7_shell(uv, n, v);
	else if (p7_mode == 9) c = p7_store(p);
	else if (p7_mode == 11) c = p7_pulse(n, v);
	else if (p7_mode == 12) c = p7_crescent(p);
	else c = p7_nick(p);
	if (c.a < 0.004) discard;
	albedo = fx_out(c.rgb, c.a);
	alpha = c.a;
}
