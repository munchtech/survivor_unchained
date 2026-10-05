// A ring of fire running out over the ground from a point (her rise, Cold, Then Not), drawn
// on one flat square as a field in rings and spokes rather than as sprites: a front of flame
// whose tongues stream outward the way it goes, deep red at their tips to orange-yellow at
// their roots, a dark bed under them so they read over the pale dead, and behind the front
// a band of ground left charred, embers winking in it as it cools. Seen from above, fire
// spreading over the ground is a ragged edge; flame sprites stood upright read as a field of
// torches, and laid flat as scattered streaks.
//
// front: how far out the front has run (0..1 of the square's half-width); width: its depth;
// fade: the whole of it going out; cool: how far the char behind it has cooled (0..1).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform float front = 0.5;
uniform float width = 0.1;
uniform float fade = 1.0;
uniform float cool = 0.0;
uniform float seed = 0.0;
// Held below the tone curve's knee: hotter, the band read as a cream doughnut.
uniform vec3 hot = vec3(1.05, 0.5, 0.08);
uniform vec3 mid = vec3(0.8, 0.17, 0.015);
uniform vec3 deep = vec3(0.22, 0.015, 0.0);

vec2 grad(vec2 i) {
	float a = fract(sin(dot(i, vec2(127.1, 311.7))) * 43758.5453) * 6.2831853;
	return vec2(cos(a), sin(a));
}
// Gradient noise (smooth, no lattice squares), wrapping every `period` cells along x, so it
// runs round a circle with no seam. About -0.7..0.7.
float gnoise(vec2 p, float period) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	float x0 = mod(i.x, period), x1 = mod(i.x + 1.0, period);
	float a = dot(grad(vec2(x0, i.y)), f);
	float b = dot(grad(vec2(x1, i.y)), f - vec2(1.0, 0.0));
	float c = dot(grad(vec2(x0, i.y + 1.0)), f - vec2(0.0, 1.0));
	float d = dot(grad(vec2(x1, i.y + 1.0)), f - vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
// Four octaves, 0..1.
float fbm(vec2 p, float period) {
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) { s += a * gnoise(p, period); p *= 2.0; period *= 2.0; a *= 0.5; }
	return clamp(s * 1.1 + 0.5, 0.0, 1.0);
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = length(p);
	float around = atan(p.y, p.x) / 6.2831853 + 0.5;
	// Round the ring and out along its spokes: many cells round, few out, so the field
	// streaks outward like flame; flowing outward with time.
	float n = fbm(vec2(around * 40.0, d * 7.0 - TIME * 2.2 + seed), 40.0);
	float n2 = fbm(vec2(around * 110.0 + 13.0, d * 11.0 - TIME * 4.5 + seed * 1.3), 110.0);
	// Out past the front: the tongues, each as long as the noise lets it reach, the long ones
	// few, with dark gaps between.
	float out_ = (d - front) / width;
	float nn = smoothstep(0.3, 0.78, n);
	float reach = 0.15 + 3.6 * nn * nn * nn + 1.1 * n2 * n2;
	float tongue = clamp(1.0 - out_ / reach, 0.0, 1.0) * step(0.0, out_);
	// In behind it: the body of the fire, burning down unevenly behind the front.
	float in_ = (front - d) / width;
	float body = step(0.0, in_) * (1.0 - smoothstep(0.05, 0.45 + 1.3 * n, in_));
	float flame = max(tongue * tongue * (0.5 + 0.5 * tongue), body * (0.55 + 0.45 * n2));
	flame *= smoothstep(0.0, 0.06, front);
	// Ragged: broken where the fine noise is low, so it is never a clean band.
	flame *= smoothstep(0.22, 0.55, n2 * 0.75 + n * 0.4);
	// A flicker running through it.
	flame *= 0.85 + 0.15 * sin(TIME * 23.0 + n2 * 17.0);
	vec3 col = mix(deep, mid, smoothstep(0.05, 0.45, flame));
	col = mix(col, hot, smoothstep(0.55, 0.95, flame));
	// Behind the fire, a band of ground charred, embers glowing in it as it cools: the middle,
	// where it began, is left (as the smoulder mark it leaves is a ring).
	float burnt = smoothstep(0.0, 2.0, in_) * (1.0 - smoothstep(4.0, 7.0, in_)) * (1.0 - smoothstep(0.92, 1.0, d));
	float ember = smoothstep(0.72, 0.86, fbm(vec2(around * 160.0, d * 60.0 + seed), 160.0)) * burnt * (1.0 - cool);
	float soot = burnt * (0.5 - 0.2 * n) * (1.0 - cool * 0.7);
	// Round, whatever the square: nothing past the ring's reach.
	float round_ = 1.0 - smoothstep(0.96, 1.0, d);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = (col * flame + vec3(0.9, 0.25, 0.04) * ember) * round_ * fade * clear;
	// The dark under the flame (so it reads over the pale dead) and the char behind it.
	ALPHA = clamp(flame * 0.6 + soot, 0.0, 1.0) * round_ * fade * clear;
}
