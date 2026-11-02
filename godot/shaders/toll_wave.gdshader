// Watch Bell's toll wave (BattleFx.WardenHoly, VFX 10 item 3): a pressure front, not a lit hoop. A low ripple band
// raised off the ground (0.15-0.25 m), a long low rise behind to a crest just short of the front and a steep face
// down to the ground; bronze-gold, brightest at its leading edge with one thin hot line on the crest, nothing lit
// behind it; broken round its length (never an even ring).
// The mesh (BattleFx.WaveMesh): UV.x round it (0..1), UV.y across it (0 behind, 1 the leading edge); every vertex
// is placed here. The instance: its basis scales X and Z by the front's radius (Y by 1).
// COLOR.r its strength (distance fall-off, fade and night in it), COLOR.g the band's width as a share of the
// radius, COLOR.b the crest's height (m), COLOR.a the run, 0..1.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

varying float vu;
varying float va;

float h1(float n) { return fract(sin(n * 91.345) * 47453.5453); }
float n1(float x) { float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

void vertex() {
	float a = UV.x * TAU, u = UV.y;
	float r = 1.0 - (1.0 - u) * COLOR.g;
	float s = dot(MODEL_MATRIX[3].xz, vec2(1.7, 3.1));
	float wob = 0.6 + 0.4 * n1(UV.x * 23.0 + s);
	float crest = smoothstep(0.0, 0.9, u) * (1.0 - smoothstep(0.9, 1.0, u));
	VERTEX = vec3(cos(a) * r, COLOR.b * crest * wob, sin(a) * r);
	vu = u;
	va = UV.x;
}

void fragment() {
	float k = COLOR.r, p = COLOR.a, u = vu;
	float s = dot(MODEL_MATRIX[3].xz, vec2(1.7, 3.1));
	// lit only toward the front: dark behind it
	float lead = pow(smoothstep(0.5, 0.93, u), 2.2) * (1.0 - 0.7 * smoothstep(0.93, 1.0, u));
	float hot = exp(-pow((u - 0.925) / 0.022, 2.0));
	// broken round its length, the breaks drifting as it runs
	float br = (0.35 + 0.65 * n1(va * 41.0 + s * 1.3 + p * 5.0)) * (0.5 + 0.5 * n1(va * 11.0 - s));
	vec3 bronze = vec3(0.6, 0.26, 0.055);
	vec3 gold = vec3(1.0, 0.56, 0.13);
	vec3 c = bronze * lead * 0.95 + gold * hot * 0.85 * (0.4 + 0.6 * br);
	ALBEDO = c * br * k * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
