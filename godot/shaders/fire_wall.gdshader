// The wall of flame riding the rise's fire front (Cold, Then Not), drawn on one open cylinder
// round her: tongues of flame standing up off the ground all the way round, each its own
// height, licking and flickering upward, hot yellow at their roots through orange to deep red
// at their ragged tips, with dark between them. (Filmed flame tiled round it read as a soft
// tan band; flame laid flat on the ground as a band of orange.) The ground under it
// (fire_ring.gdshader) is its bed and its char.
//
// UV.x runs round the ring; the height is the mesh's own (a CylinderMesh's side spans only half
// its UV's height, the caps the rest). cells: noise cells round the ring (an integer, so it wraps
// with no seam); burn: how strongly it burns (0..1).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float cells = 60.0;
uniform float burn = 1.0;
uniform float seed = 0.0;
uniform float soft = 0.3;
// Held below the tone curve's knee: hotter, flame reads as cream.
uniform vec3 hot = vec3(1.25, 0.78, 0.22);
uniform vec3 mid = vec3(1.0, 0.36, 0.05);
uniform vec3 deep = vec3(0.42, 0.05, 0.01);

vec2 grad(vec2 i) {
	float a = fract(sin(dot(i, vec2(127.1, 311.7)) + seed) * 43758.5453) * 6.2831853;
	return vec2(cos(a), sin(a));
}
// Gradient noise wrapping every `period` cells along x. About -0.7..0.7.
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
float fbm(vec2 p, float period) {
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 4; i++) { s += a * gnoise(p, period); p *= 2.0; period *= 2.0; a *= 0.5; }
	return clamp(s * 1.1 + 0.5, 0.0, 1.0);
}

varying float height;

void vertex() {
	height = VERTEX.y + 0.5;
}

void fragment() {
	float up = clamp(height, 0.0, 1.0);
	float x = UV.x * cells;
	// The air rising through it licks every tongue sideways as it climbs.
	float lick = fbm(vec2(x * 1.7, up * 2.4 - TIME * 2.2), cells * 1.7) - 0.5;
	float xs = x + lick * 0.7 * up;
	// Ridged noise: each tongue rises to a point, its own height, the tall ones few.
	float n = fbm(vec2(xs * 1.1, TIME * 0.9), cells * 1.1);
	float ridge = 1.0 - abs(2.0 * n - 1.0);
	float high = 0.12 + 0.88 * pow(ridge, 2.2) * (0.88 + 0.12 * sin(TIME * 15.0 + xs * 2.3));
	// Torn as it climbs: the turbulence opens dark gaps toward the tips.
	float tear = fbm(vec2(xs * 2.6, up * 4.0 - TIME * 3.6), cells * 2.6);
	float body = 1.0 - up / max(0.05, high);
	float f = clamp(body * 1.25 - (1.0 - tear) * 0.55 * sqrt(up), 0.0, 1.0);
	// Its roots burn steady along the ground.
	f = max(f, (1.0 - smoothstep(0.0, 0.1, up)) * (0.7 + 0.3 * tear));
	vec3 col = mix(deep, mid, smoothstep(0.12, 0.55, f));
	col = mix(col, hot, smoothstep(0.62, 0.95, f));
	float a = smoothstep(0.0, 0.35, f);
	// Where it stands in the ground it fades into it, so its foot is never a line.
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0) * burn;
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	// Mostly light, a little dark laid under it, as real flame does over what is behind it.
	ALBEDO = col * a * fade * clear;
	ALPHA = a * 0.35 * fade * clear;
}
