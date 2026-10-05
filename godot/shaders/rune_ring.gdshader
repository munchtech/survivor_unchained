// Hallowed Ground's ring of runes (BattleFx.Skills: RuneRing), held flat in the air at her waist
// at the ground's edge, turning slowly: a band of staves and twigs in gold light between two thin
// rings, a light running round it. Ground marks hide under a packed crowd (that is why the gold
// circle on the ground read as any circle); what must be seen is held in the air.
//
// The runes are drawn here, not painted: each a stave with two or three twigs chosen by its place,
// strokes as distances, so they are crisp at any size and ours. On a PlaneMesh 2 across; the node's
// scale is the ground's radius. lit: its strength (0..1); count: runes round it.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform vec3 tint = vec3(1.0, 0.72, 0.3);
uniform float lit = 1.0;
uniform float count = 32.0;
uniform float seed = 0.0;

float h1(float n) { return fract(sin(n * 127.1 + seed * 13.7) * 43758.5453); }

float seg(vec2 p, vec2 a, vec2 b) {
	vec2 pa = p - a, ba = b - a;
	float t = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return length(pa - ba * t);
}

// One rune in a cell (x across -0.5..0.5, y up the band -0.5..0.5): its distance to the strokes.
float rune(vec2 p, float id) {
	float d = seg(p, vec2(0.0, -0.36), vec2(0.0, 0.36));
	// A second stave on some.
	if (h1(id + 1.0) > 0.78) { d = min(d, seg(p, vec2(0.2, -0.36), vec2(0.2, 0.36))); p.x += 0.1; }
	// Twigs: up to three of eight, each by a bit of the rune's hash.
	float bits = floor(h1(id) * 256.0);
	vec2 twig[8] = vec2[8](vec2(0.24, 0.12), vec2(-0.24, 0.12), vec2(0.24, -0.12), vec2(-0.24, -0.12),
		vec2(0.24, 0.36), vec2(-0.24, 0.36), vec2(0.24, -0.36), vec2(-0.24, -0.36));
	vec2 from[8] = vec2[8](vec2(0.0, 0.36), vec2(0.0, 0.36), vec2(0.0, 0.1), vec2(0.0, 0.1),
		vec2(0.0, 0.0), vec2(0.0, 0.0), vec2(0.0, -0.1), vec2(0.0, -0.1));
	int n = 0;
	for (int i = 0; i < 8; i++) {
		if (n >= 3) break;
		if (mod(floor(bits / pow(2.0, float(i))), 2.0) > 0.5) { d = min(d, seg(p, from[i], twig[i])); n++; }
	}
	if (n == 0) d = min(d, seg(p, vec2(0.0, 0.2), vec2(0.24, 0.0)));
	return d;
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float r = length(p);
	if (r > 1.0) discard;
	float a = atan(p.y, p.x) / TAU + 0.5;
	// The band of runes between two thin rings.
	float r0 = 0.84, r1 = 0.97;
	float band = (r - r0) / (r1 - r0);
	float cell = floor(a * count);
	float cx = fract(a * count) - 0.5;
	// Square-ish strokes: the cell's width against the band's height.
	float aspect = (TAU * (r0 + r1) * 0.5 / count) / (r1 - r0);
	vec2 q = vec2(cx * aspect, band - 0.5);
	float d = (band > -0.1 && band < 1.1) ? rune(q / vec2(0.9, 0.95), cell) : 1.0;
	float strokes = smoothstep(0.07, 0.025, d);
	float halo = exp(-d * d / 0.03) * 0.35;
	float rings = smoothstep(0.01, 0.0, abs(r - r0 + 0.02)) + smoothstep(0.008, 0.0, abs(r - r1 - 0.015));
	rings += exp(-pow((r - r0 + 0.02) / 0.02, 2.0)) * 0.2 + exp(-pow((r - r1 - 0.015) / 0.02, 2.0)) * 0.2;
	// A light running round it, the runes it passes brightest.
	float run = fract(a - TIME * 0.12);
	float chase = 0.5 + 0.5 * smoothstep(0.75, 1.0, run) + 0.25 * smoothstep(0.0, 0.08, run) * (1.0 - smoothstep(0.08, 0.3, run));
	float flick = 0.85 + 0.15 * sin(TIME * 3.0 + cell * 1.7);
	float k = (strokes * 1.0 + halo) * chase * flick + rings * 0.55;
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = tint * k * lit * clear;
}
