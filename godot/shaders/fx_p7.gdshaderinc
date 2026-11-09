// P7 (the skills lead, 9 Nov): Heroic Leap, Shield Charge and the dash's shove in the FX language
// (docs/design/FX_LANGUAGE.md; shaders/fx_cel.gdshaderinc). One heat field per shape, cut into the school's bands by
// fx_cel(); drawn after the grade (FxAfter) so a band's hex is its displayed color. Shapes (p7_mode):
//   (solver A rebuild, 9 Nov: every light shape below is p7_stroke(across, along, life) and a coverage cap, nothing else)
//   0 ring   the leap's mark on the ground: a stroke p7_width (share of the radius, sized from the camera) wide whose outer
//            edge is the hit radius (the quad is 2R wide); six gaps (p7_prog, stepped) its arcs taper into; p7_fade life.
//   1 star   a hit: a solid heart and p7_spikes tapered spikes of varied length, ~12 streaks running out; one sample at the
//            peak, then a life step a sample (p7_t, seconds). Flat on the ground, or facing the camera (p7_bill).
//   2 ribbon a strip mesh (UV.x its age along it: 0 tail .. 1 head; UV.y across): the stroke as it is; p7_fade its life.
//   3 ghost  an afterimage (her pose, a mesh): a ~2 px rim of light at her silhouette over a clear core, stepping thinner
//            and out over p7_life seconds.
//   4 glint  the press: two crossed strokes and a hot heart (camera-facing), 3 frames.
//   5 shove  a ring running out to the radius (p7_prog), p7_width its half-width, thinning to nothing as it reaches it.
//  12 crescent the charge's arc of light on the shield's face (camera-facing), its middle toward p7_dir2 (screen).
//   6 storm  Bladestorm's crescents on a flat quad at knee height (2R wide): p7_count blades, blade 0's head at p7_spin
//            (radians, atan(z, x)), turning the way p7_dir says; each core leading, a gold body, an amber trail tapering to
//            a point over p7_trail radians (times p7_prog, the wind-in), curling a little inward; erodes by p7_fade.
//   7 scar   a Sunder line on the ground (UV.x 0 her end .. 1 the far end): pending, a thin jagged heart at p7_lvl
//            (mid); split (p7_prog >= 0), the crack opening behind a core front racing out to p7_prog, at p7_lvl.
//   8 shell  Iron Vow's brace: a bold edge-band stroke round her (camera-facing; p7_width its half-width, a share of
//            the quad), four arcs with ragged gaps that close a step with each store level (p7_prog 0..1), turning;
//            p7_lvl is its heat (edge band only: under the mid's cut).
//   9 store  the vow's store on her shield (camera-facing): a core disc ringed in gold with a four-point flare, both
//            stepping up with p7_prog (0..1); a stored blow brightens it a sample and pulls its sparks inward for 3
//            samples (p7_t since the last).
//  11 pulse  a stored blow's pulse up her body (her pose, a mesh, like the ghost): a flat mid band climbing from her feet
//            (p7_y0, world) to her crown (p7_y0 + p7_h) over 3 samples (p7_t), faint (p7_alpha), its trailing lip edge.
//  10 streak a struck foe's tangential sparks (camera-facing): tears flung along p7_dir2 (screen, y down), 3 samples.
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

vec4 p7_ring(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	// the light on the ground: p7_width is its half-width as a share of the radius (the caller sizes it from the
	// camera); its outer edge stays at 1, the hit radius, while the brush wanders a little in width
	float hw = p7_width * (1.0 + 0.18 * fx_gnoise(vec2(a * 2.2, p7_seed * 3.0)));
	float across = (r - (1.0 - hw)) / hw;
	// six gaps (p7_prog 0..1, stepped by the caller); each lit arc tapers to a point into its gaps
	float along = 1.0;
	if (p7_prog < 0.999) {
		float s = fract(a / P7_TAU * 6.0 + p7_seed);
		float g = mix(0.2, 0.0, p7_prog);
		float u = (s - g) / max(1.0 - 2.0 * g, 1e-3);
		along = (u < 0.0 || u > 1.0) ? -1.0 : clamp(min(u, 1.0 - u) / 0.22, 0.0, 1.0);
	}
	if (along < 0.0) return vec4(0.0);
	vec4 o = p7_stroke(across, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

uniform float p7_spikes = 7.0;  // star: its spikes (6-8 on the ground, 4-6 at a body)
// The star: one bold shape, a solid white-gold heart and p7_spikes tapered spikes of varied length (their roots the
// heads), then ~12 thin streaks running out between them; one sample at its peak (life 0), then a step a sample: the
// core gives out, then the gold, then it is gone, the spikes shortening a little each step.
vec4 p7_star(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float k = p7_steps(p7_t, P7_SAMPLE);
	float life = clamp(k * 0.34 + p7_fade, 0.0, 1.0);
	float shrink = 1.0 - 0.18 * k;
	// each step it thins as well as cools (never a full-width amber slab broken into blocks)
	float thin = 1.0 - 0.3 * min(k, 2.0);
	// the heart: a disc whose across is compressed so most of it is the core band
	float rc = 0.2 * (1.0 - 0.35 * k);
	vec4 o = p7_stroke(pow(r / rc, 2.2), 1.0, life);
	float n = clamp(p7_spikes, 3.0, 8.0);
	for (float i = 0.0; i < 8.0; i += 1.0) {
		if (i >= n) break;
		float h = fx_hash(vec2(i, p7_seed));
		float th = (i + (h - 0.5) * 0.55) / n * P7_TAU + p7_seed;
		// varied: one or two long, the rest a half to two thirds of it
		float hl = fx_hash(vec2(p7_seed, i * 1.7));
		float len = (i < 0.5 ? 0.92 : mix(0.38, 0.8, hl * hl)) * shrink;
		vec2 q = p7_ray(p, th, len, 0.1 * thin);
		if (q.y >= 0.0) o = p7_over(o, p7_stroke(q.x, q.y, life));
	}
	// the streaks: thin and short, running out from 0.25 to the spikes' reach over 3 samples, gone with the star
	float run = clamp(p7_t / (3.0 * P7_SAMPLE), 0.0, 1.0);
	for (float j = 0.0; j < 12.0; j += 1.0) {
		float h = fx_hash(vec2(j * 3.1, p7_seed + 1.0));
		float th = (j + 0.5 + (h - 0.5) * 0.8) / 12.0 * P7_TAU + p7_seed;
		float len = mix(0.1, 0.2, h);
		float head = mix(0.3, mix(0.7, 0.92, fract(h * 7.0)), 1.0 - (1.0 - run) * (1.0 - run));
		vec2 d = vec2(cos(th), sin(th));
		float u = dot(p, d), v = dot(p, vec2(-d.y, d.x));
		if (u > head - len && u < head) o = p7_over(o, p7_stroke(v / 0.02, (u - (head - len)) / len, min(1.0, max(life * 1.5, run * 0.34))));
	}
	return o;
}

vec4 p7_ribbon(vec2 uv) {
	// a strip (UV.x its age along it: 0 the tail .. 1 the head; UV.y 0..1 across): the stroke tapers it to nothing at the
	// tail; its very head (the last 6%, where it meets her) feathers in coverage so it never ends in a square cap
	vec4 o = p7_stroke(uv.y * 2.0 - 1.0, uv.x, p7_fade);
	o.a *= 1.0 - smoothstep(0.94, 1.0, uv.x);
	// and its tail ends where it would thin to a hairline (no 1 px line running long)
	o.a *= smoothstep(0.12, 0.24, uv.x);
	return o;
}

// An afterimage: her pose as a rim of light only (~2 px in from her silhouette, measured in pixels of the facing
// term's own slope), the core transparent; the rim steps thinner and out over p7_life seconds.
uniform float p7_life = 0.15;
vec4 p7_ghost(vec2 uv, vec3 n, vec3 v) {
	float e = abs(dot(normalize(n), normalize(v)));
	float px = e / max(fwidth(e), 1e-4);
	float k = floor(p7_t / (p7_life / 3.0));
	float w = 1.3 * (1.0 - 0.25 * k);
	vec4 o = p7_stroke((px - w) / w, 1.0, 0.0);
	o.a *= p7_alpha * (1.0 - k / 3.0);
	return o;
}

vec4 p7_glint(vec2 p) {
	// two crossed strokes (their heads at the centre) and a small hot heart
	vec4 o = p7_stroke(length(p) / 0.16, 1.0, p7_fade);
	o = p7_over(o, p7_stroke(p.y / 0.07, 1.0 - abs(p.x), p7_fade));
	o = p7_over(o, p7_stroke(p.x / 0.07, 1.0 - abs(p.y), p7_fade));
	return o;
}

// A ring running out (Hard Landing's shove; a ring off the shield): its front at p7_prog of the radius, p7_width its
// half-width (share of the radius); bold while it is near (the head of its life along) and thinning to nothing as it
// reaches the radius; p7_fade its life (stepped by the caller), p7_alpha its coverage.
vec4 p7_shove(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float front = mix(0.18, 1.0, p7_prog);
	float hw = p7_width * (1.0 + 0.22 * fx_gnoise(vec2(a * 2.5, p7_seed)));
	float across = (r - (front - hw)) / hw;
	float along = 1.0 - 0.94 * p7_prog;
	vec4 o = p7_stroke(across, along, p7_fade);
	o.a *= p7_alpha;
	return o;
}

// (12) the charge's crescent on the shield's face (camera-facing): an arc of light whose middle (the head) faces the
// way she drives (p7_dir2, on screen, y down), its ends tapering back round the shield.
vec4 p7_crescent(vec2 p) {
	float r = length(p);
	vec2 f = normalize(p7_dir2);
	float ph = acos(clamp(dot(p / max(r, 1e-4), f), -1.0, 1.0));
	float along = 1.0 - ph / 1.45;
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
	else if (p7_mode == 1) c = p7_star(p);
	else if (p7_mode == 2) c = p7_ribbon(uv);
	else if (p7_mode == 3) c = p7_ghost(uv, n, v);
	else if (p7_mode == 4) c = p7_glint(p);
	else if (p7_mode == 5) c = p7_shove(p);
	else if (p7_mode == 6) c = p7_storm(p);
	else if (p7_mode == 7) c = p7_scar(uv);
	else if (p7_mode == 8) c = p7_shell(n, v);
	else if (p7_mode == 9) c = p7_store(p);
	else if (p7_mode == 11) c = p7_pulse(n, v);
	else if (p7_mode == 16) c = p7_bring(p);
	else if (p7_mode == 17) c = p7_bstar(p);
	else if (p7_mode == 12) c = p7_crescent(p);
	else c = p7_streak(p);
	// (the ghost keeps its clear core: it writes depth there, so her own limbs behind it do not show their rims)
	if (c.a < 0.004 && p7_mode != 3) discard;
	albedo = fx_out(c.rgb, c.a);
	alpha = c.a;
}
