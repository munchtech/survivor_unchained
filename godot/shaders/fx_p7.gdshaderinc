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
#include "res://shaders/fx_cel.gdshaderinc"

uniform int p7_mode = 0;
uniform float p7_t = 0.0;      // seconds since it began
uniform float p7_prog = 0.0;   // ring closure / shove reach 0..1
uniform float p7_fade = 0.0;   // 0 whole .. 1 gone (stepped by the caller)
uniform float p7_alpha = 1.0;  // the coverage cap (the ring's half opacity)
uniform float p7_seed = 0.0;
uniform float p7_bill = 0.0;   // 1: the quad faces the camera
uniform float p7_width = 0.08; // ring / shove stroke width (share of the radius)

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

void p7_frag(vec2 uv, vec3 n, vec3 v, out vec3 albedo, out float alpha) {
	vec2 p = uv * 2.0 - 1.0;
	vec4 c;
	if (p7_mode == 0) c = p7_ring(p);
	else if (p7_mode == 1) c = p7_star(p);
	else if (p7_mode == 2) c = p7_ribbon(uv);
	else if (p7_mode == 3) c = p7_ghost(uv, n, v);
	else if (p7_mode == 4) c = p7_glint(p);
	else c = p7_shove(p);
	if (c.a < 0.004) discard;
	albedo = fx_out(c.rgb, c.a);
	alpha = c.a;
}
