// P7 (the skills lead, 9 Nov): Heroic Leap, Shield Charge and the dash's shove in the FX language
// (docs/design/FX_LANGUAGE.md; shaders/fx_cel.gdshaderinc). One heat field per shape, cut into the school's bands by
// fx_cel(); drawn after the grade (FxAfter) so a band's hex is its displayed color. Shapes (p7_mode):
//   0 ring   the landing mark on the ground: a painted stroke whose outer edge is the hit radius (the quad is 2R wide),
//            mid band, gaps that close as p7_prog runs 0..1, at most half opacity (p7_alpha).
//   1 star   a hit: 4 long and 4 short spikes, core then mid, radial painted sparks; one sample at the peak, then it
//            steps down (p7_t, seconds), holes opening. Flat on the ground, or facing the camera (p7_bill).
//   2 ribbon a body's trail (a strip mesh: UV.x 0 tail .. 1 head, UV.y across): the core leads, the edge trails to a point.
//   3 ghost  an afterimage (her pose, a mesh): flat mid with an edge-band line at the silhouette, stepping out.
//   4 glint  the press: a four-point star in the core color for 2-3 frames (camera-facing).
//   5 shove  Hard Landing's wave: a thin arc ring running out to the radius (p7_prog), its outer lip hot.
//   6 storm  Bladestorm's crescents on a flat quad at knee height (2R wide): p7_count blades, blade 0's head at p7_spin
//            (radians, atan(z, x)), turning the way p7_dir says; each core leading, a gold body, an amber trail tapering to
//            a point over p7_trail radians (times p7_prog, the wind-in), curling a little inward; erodes by p7_fade.
//   7 scar   a Sunder line on the ground (UV.x 0 her end .. 1 the far end): pending, a thin jagged heart at p7_lvl
//            (mid); split (p7_prog >= 0), the crack opening behind a core front racing out to p7_prog, at p7_lvl.
//   8 shell  Iron Vow's brace: a tight edge-band stroke round her (camera-facing), four arcs with gaps, turning;
//            p7_lvl lifts it a band on a stored blow.
//   9 store  the vow's store on her shield (camera-facing): a core disc stepping up with p7_prog (0..1), and the stored
//            blow's sparks pulled inward for 3 samples after it (p7_t since the last).
//  10 streak a struck foe's tangential sparks (camera-facing): tears flung along p7_dir2 (screen, y down), 3 samples.
#include "res://shaders/fx_cel.gdshaderinc"

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

void vertex() {
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

vec4 p7_ring(vec2 p) {
	float r = length(p), a = atan(p.y, p.x) + p7_seed * 6.0;
	// a brushed stroke: its width wanders a little with the angle (a painted line, not a compass circle); the outer
	// edge stays at 1 (the hit radius) so what is marked is what is hit
	float w = p7_width * (1.0 + 0.28 * fx_gnoise(vec2(a * 2.2, p7_seed * 3.0)));
	float c = 1.0 - w * 0.5;
	float h = 1.0 - abs(r - c) / (w * 0.5);
	// six gaps, ragged at their ends, closing as she falls (gone by the landing)
	float n = 6.0;
	float seg = fract(a / P7_TAU * n + 0.13 * p7_prog);
	float g = mix(0.42, 0.0, smoothstep(0.0, 1.0, p7_prog)) * (1.0 + 0.35 * fx_gnoise(vec2(r * 18.0, a * 3.0 + p7_seed)));
	float gap = g * 0.5 - abs(seg - 0.5);
	h -= max(0.0, gap) * 9.0;
	float m = (fx_t.y + fx_t.z) * 0.5;
	float heat = h > 0.0 ? min(h / 0.55, 1.0) * m : h * 0.12;
	heat -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(p * 9.0 + p7_seed);
	vec4 o = fx_cel(heat, 0.5);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_star(vec2 p) {
	float r = length(p), a = atan(p.y, p.x) + p7_seed;
	float c4 = cos(a * 4.0);
	float lng = pow(max(0.0, c4), 30.0), sht = pow(max(0.0, -c4), 40.0);
	float L = 0.16 + 0.84 * lng + 0.42 * sht;
	float k = p7_steps(p7_t, P7_SAMPLE);
	float heat = (1.0 - r / L) * 1.15;
	// one sample at its peak; then it steps down, the spikes shortening and holes opening (core, then mid, then edge)
	heat -= k * 0.26 + k * 0.22 * fx_noise(p * 7.0 + p7_seed * 5.0);
	heat -= p7_fade;
	vec4 o = fx_cel(heat, 1.0);
	// painted sparks flung out along the spokes (tears on the flow, never dots), gone by the third sample
	vec2 q = vec2(r - p7_t * 2.6, a * 0.55);
	float sp = fx_sparks(q, vec2(1.0, 0.0), 0.11, 0.42, 0.13, 3.2, p7_seed * 11.0);
	sp *= smoothstep(0.22, 0.4, r) * (1.0 - smoothstep(0.85, 1.0, r)) * step(p7_t, 3.0 * P7_SAMPLE);
	float body = fx_step(fx_t.x, heat);
	vec3 col = mix(o.rgb, fx_spark_color, sp * (1.0 - body));
	return vec4(col, max(o.a, sp));
}

vec4 p7_ribbon(vec2 uv) {
	float along = uv.x, y = abs(uv.y * 2.0 - 1.0);
	float heat = (1.0 - y) * mix(0.18, 1.05, pow(along, 1.4)) - (1.0 - along) * 0.12;
	heat -= fx_noise(vec2(along * 14.0, p7_seed)) * 0.18 * (1.0 - along);
	heat -= p7_fade * 0.8 + p7_fade * 0.5 * fx_noise(uv * vec2(20.0, 3.0) + p7_seed);
	return fx_cel(heat, along);
}

vec4 p7_ghost(vec2 uv, vec3 n, vec3 v) {
	float k = p7_steps(p7_t, P7_SAMPLE);
	// an edge-band line at the silhouette (the figure's own outline as light), a flat mid body
	float rim = 1.0 - clamp(abs(dot(normalize(n), normalize(v))), 0.0, 1.0);
	float heat = rim > 0.62 ? (fx_t.x + fx_t.y) * 0.5 : (fx_t.y + fx_t.z) * 0.45;
	float holes = fx_noise(uv * 38.0 + p7_seed * 7.0);
	heat -= step(holes, k * 0.24) * 2.0;
	vec4 o = fx_cel(heat, 0.5);
	o.a *= p7_alpha * (1.0 - k * 0.22);
	return o;
}

vec4 p7_glint(vec2 p) {
	float arms = max(1.0 - abs(p.y) * 14.0 - abs(p.x) * 1.05, 1.0 - abs(p.x) * 14.0 - abs(p.y) * 1.05);
	float heat = max(arms * 1.3, 1.0 - length(p) * 4.5) - p7_fade;
	return fx_cel(heat, 1.0);
}

vec4 p7_shove(vec2 p) {
	float r = length(p), a = atan(p.y, p.x) + p7_seed * 4.0;
	float front = mix(0.25, 1.0, p7_prog);
	float w = p7_width * (1.0 + 0.3 * fx_gnoise(vec2(a * 2.5, p7_seed)));
	// hot at its running lip, trailing inward to the edge band
	float d = (front - r) / w;
	float heat = d < 0.0 ? 1.0 + d * 6.0 : (1.0 - d) * mix(0.4, 1.0, 1.0 - d);
	heat = d > 1.0 ? -0.3 : heat;
	heat -= p7_fade * 0.9 + p7_fade * 0.5 * fx_noise(p * 8.0 + p7_seed);
	vec4 o = fx_cel(heat, 0.6);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_storm(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float n = clamp(p7_count, 1.0, 6.0), trail = max(0.05, p7_trail * p7_prog);
	float heat = -1.0, along = 0.0;
	for (int k = 0; k < 6; k++) {
		if (float(k) >= n) break;
		float h = p7_spin + float(k) * P7_TAU / n;
		// behind the head along its way: 0 at the head, 1 at the trail's end; a short round nose ahead of it
		float d = mod((h - a) * p7_dir, P7_TAU);
		float u = d > P7_TAU - 0.16 ? (d - P7_TAU) / trail : d / trail;
		if (u > 1.0) continue;
		float rc = mix(0.88, 0.72, clamp(u, 0.0, 1.0));
		float w0 = 0.075;
		float w = u < 0.0 ? w0 * sqrt(max(0.0, 1.0 - pow(u / (0.13 / trail), 2.0))) : w0 * pow(1.0 - u, 0.85);
		w *= 1.0 + 0.22 * (fx_gnoise(vec2(u * 6.0 + float(k) * 3.1, p7_seed)) - 0.5);
		float prof = 1.0 - abs(r - rc) / max(w, 1e-4);
		float hk = (prof > 0.0 ? min(prof / 0.45, 1.0) : prof * 0.35) * mix(1.12, 0.22, pow(clamp(u, 0.0, 1.0), 0.75));
		// painted bites in the tail, holes as it erodes
		hk -= 0.16 * fx_noise(vec2(u * 11.0, r * 24.0) + p7_seed + float(k)) * clamp(u, 0.0, 1.0);
		hk -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(p * 10.0 + p7_seed);
		if (hk > heat) { heat = hk; along = 1.0 - clamp(u, 0.0, 1.0); }
	}
	return fx_cel(heat, along);
}

vec4 p7_scar(vec2 uv) {
	float x = uv.x, y = uv.y * 2.0 - 1.0;
	float cy = 0.34 * (fx_gnoise(vec2(x * 7.0, p7_seed)) - 0.5) + 0.12 * (fx_noise(vec2(x * 23.0, p7_seed + 4.0)) - 0.5);
	float ends = smoothstep(0.0, 0.04, x) * (1.0 - smoothstep(0.93, 1.0, x));
	float pw = 0.07 * (0.75 + 0.5 * fx_noise(vec2(x * 31.0, p7_seed + 9.0)));
	float lvl = 0.6, w = pw;
	if (p7_prog >= 0.0 && x <= p7_prog) {
		// split: the crack opens behind the front; the front itself is the hottest
		float behind = p7_prog - x;
		w = mix(pw * 2.2, 0.24, clamp(behind * 5.0, 0.0, 1.0));
		lvl = p7_lvl + max(0.0, 0.5 - behind * 6.0) * step(p7_prog, 0.999);
	} else if (p7_prog < 0.0) lvl = p7_lvl;
	float prof = 1.0 - abs(y - cy) / w;
	float heat = (prof > 0.0 ? min(prof / 0.5, 1.0) : prof * 0.3) * lvl * ends;
	heat -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(uv * vec2(40.0, 4.0) + p7_seed);
	return fx_cel(heat, 0.5 + 0.5 * x);
}

vec4 p7_shell(vec2 p) {
	float r = length(p), a = atan(p.y, p.x) + p7_t * 0.9 + p7_seed;
	float w = 0.035 * (1.0 + 0.3 * fx_gnoise(vec2(a * 3.0, p7_seed)));
	float prof = 1.0 - abs(r - 0.9) / w;
	// four arcs, ragged gaps between
	float seg = fract(a / P7_TAU * 4.0);
	float gap = 0.09 * (1.0 + 0.4 * fx_noise(vec2(a * 5.0, r * 30.0))) - min(seg, 1.0 - seg);
	prof -= max(0.0, gap) * 12.0;
	float heat = (prof > 0.0 ? min(prof / 0.5, 1.0) : prof * 0.25) * p7_lvl;
	heat -= p7_fade * 0.9 + p7_fade * 0.6 * fx_noise(p * 9.0 + p7_seed);
	vec4 o = fx_cel(heat, 0.4);
	o.a *= p7_alpha;
	return o;
}

vec4 p7_store(vec2 p) {
	float r = length(p), a = atan(p.y, p.x);
	float lv = p7_prog;
	float rad = 0.18 + 0.3 * lv;
	float heat = lv > 0.001 ? (1.0 - r / rad) * (0.7 + 0.6 * lv) : -1.0;
	vec4 o = fx_cel(heat, 1.0);
	// the stored blow: tears pulled inward to the shield's heart, 3 samples
	if (p7_t < 3.0 * P7_SAMPLE) {
		vec2 q = vec2(r + p7_t * 4.5, a * 0.6);
		float sp = fx_sparks(q, vec2(-1.0, 0.0), 0.12, 0.5, 0.18, 3.5, p7_seed * 13.0 + floor(p7_t * 0.0));
		sp *= smoothstep(0.12, 0.3, r) * (1.0 - smoothstep(0.8, 1.0, r));
		float body = fx_step(fx_t.x, heat);
		o = vec4(mix(o.rgb, fx_spark_color, sp * (1.0 - body)), max(o.a, sp));
	}
	o.a *= 1.0 - p7_fade;
	return o;
}

vec4 p7_streak(vec2 p) {
	vec2 f = normalize(p7_dir2);
	vec2 q = p - f * p7_t * 5.0;
	float sp = fx_sparks(q, f, 0.16, 0.55, 0.32, 4.0, p7_seed * 7.0);
	// a cone along the flight, gone by the third sample
	float cone = smoothstep(0.35, 0.7, dot(normalize(p + 1e-4), f)) * (1.0 - smoothstep(0.75, 1.0, length(p)));
	sp *= cone * step(p7_t, 3.0 * P7_SAMPLE);
	float hot = 1.0 - smoothstep(0.0, 2.0 * P7_SAMPLE, p7_t);
	return vec4(mix(fx_spark_color, fx_core, hot), sp);
}

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
	else if (p7_mode == 8) c = p7_shell(p);
	else if (p7_mode == 9) c = p7_store(p);
	else c = p7_streak(p);
	if (c.a < 0.004) discard;
	albedo = fx_out(c.rgb, c.a);
	alpha = c.a;
}
