// Watch Bell's toll wave (BattleFx.WardenHoly, VFX 10 item 3): a pressure front, not a lit hoop. A low ripple band
// raised off the ground, ~0.5 m (35 px at the play camera) across: a faint body (about 25% at most) fading to nothing
// behind, and at the front one hard thin line (#FFE6A8, 4 px, 2.5x the body's brightness). The ring is broken: a gap
// every ~4 m, 0.45-1.1 m long (15-25% of its length), the breaks fixed to the wave.
// The mesh (BattleFx.WaveMesh): UV.x round it (0..1), UV.y across it (0 behind, 1 the leading edge); every vertex
// is placed here. The instance: its basis scales X and Z by the front's radius (Y by 1).
// COLOR.r its strength (distance fall-off, fade and night in it), COLOR.g the band's width as a share of the
// radius, COLOR.b the crest's height (m), COLOR.a the run, 0..1.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

varying float vu;
varying float va;
varying float rad;

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
	rad = length(MODEL_MATRIX[0].xyz);
}

void fragment() {
	float k = COLOR.r, u = vu;
	float s = dot(MODEL_MATRIX[3].xz, vec2(1.7, 3.1));
	// the gaps: round the front's length, one in each ~4 m, placed and sized by hash, fixed to the wave
	float circ = TAU * rad;
	float cells = max(3.0, floor(circ / 4.2));
	float cx = va * cells, ci = floor(cx);
	float clen = circ / cells;
	float gl = mix(0.45, 1.1, h1(ci * 7.7 + s));
	float gc = mix(0.6, clen - 0.6, h1(ci * 3.3 + s * 1.9 + 5.0));
	float ax = (cx - ci) * clen;
	float gap = 1.0 - (1.0 - smoothstep(gl * 0.5 - 0.12, gl * 0.5 + 0.12, abs(ax - gc)));
	// body: nothing behind, rising to about a quarter toward the front
	float body = pow(smoothstep(0.0, 0.88, u), 2.0) * (1.0 - smoothstep(0.96, 1.0, u));
	// the leading edge: one hard thin line (~4 px = 0.06 m of the ~0.5 m band)
	float edge = smoothstep(0.87, 0.89, u) * (1.0 - smoothstep(0.985, 1.0, u));
	float jit = 0.8 + 0.2 * n1(va * 90.0 + s);
	vec3 bodyc = vec3(1.0, 0.77, 0.35);
	vec3 edgec = vec3(1.0, 0.9, 0.66);
	vec3 c = bodyc * body * 0.17 + edgec * edge * 0.42 * jit;
	ALBEDO = c * gap * k * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
