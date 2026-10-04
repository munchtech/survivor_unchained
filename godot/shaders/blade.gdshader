// A blade's swing (src/Fx/Blades.cs): the crescent its edge cuts through
// the air, drawn as it goes. A white-hot line at the reach leads, its
// smear of colour streaked along the swing behind it, deepest a little
// behind the edge and coming to a point at both ends; as it dies the smear
// is eaten away in soft tatters from its tail, never fading as one flat
// sheet and never breaking along straight lines.
// Premultiplied: what it adds is its light, and its alpha darkens what is
// under it, so the same pass lays the dark bed that makes it read over the
// pale dead. No end and no side of it is ever cut straight.
//
// One instance per swing (a MultiMesh): COLOR is its hue (linear, kept
// near 1 so the tone curve leaves it a colour; the edge is the only white)
// and in alpha how deep its smear reaches; INSTANCE_CUSTOM is (head, back,
// span in radians, seed + what is left): the blade's place along the swing
// (0 the start, 1 the end), where its smear ends behind it, the angle it
// sweeps, and a seed whose fraction is how much of it is left.
//
// The mesh is a unit grid (UV.x along the swing, UV.y from the inner
// radius out past the reach); the vertex stage bends it round the swing.
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

// Where the smear may reach in to, and how far out the mesh goes, as shares of the reach.
const float INNER_R = 0.3;
const float OUTER_R = 1.06;
// The cutting edge's radius (soft glow outside it).
const float EDGE_R = 0.96;

varying flat vec4 v_custom;
varying flat vec4 v_hue;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
// Turned between octaves, so no grid shows through as straight lines.
float fbm(vec2 p) {
	float a = vnoise(p) * 0.5;
	p = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * p * 2.03 + 4.1;
	a += vnoise(p) * 0.3;
	p = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * p * 2.01 + 1.7;
	return a + vnoise(p) * 0.2;
}

void vertex() {
	v_custom = INSTANCE_CUSTOM;
	v_hue = COLOR;
	float span = INSTANCE_CUSTOM.z;
	float a = (UV.x - 0.5) * span;
	float r = mix(INNER_R, OUTER_R, UV.y);
	// The swing's plane tilts up through its middle, as an arm's does.
	float lift = 0.16 * sin(UV.x * PI) * r;
	VERTEX = vec3(sin(a) * r, lift, cos(a) * r);
}

void fragment() {
	float head = v_custom.x, back = v_custom.y, span = v_custom.z;
	float seed = floor(v_custom.w), left = fract(v_custom.w);
	float u = UV.x, y = mix(INNER_R, OUTER_R, UV.y);
	float len = max(head - back, 0.02);
	float t = (head - u) / len;
	if (t < -0.05 || t > 1.02) discard;
	float tc = clamp(t, 0.0, 1.0);
	// Along the swing in units of the reach, so the noise is round, not stretched.
	float along = u * span;
	// The crescent: how deep in from the edge the smear reaches here: nothing
	// at the blade, deepest just behind it, thinning to a point at its tail;
	// and at the very start of the swing it comes to a point too.
	float shape = pow(sin(PI * pow(tc, 0.5)), 0.7) * smoothstep(0.0, 0.12, along);
	float depth = v_hue.a * shape;
	float inner = EDGE_R - depth;
	// Across the smear: 0 at its inner edge, 1 at the cutting edge.
	float across = clamp((y - inner) / max(depth, 1e-3), 0.0, 1.0);
	float inBand = smoothstep(inner - 0.03, inner + depth * 0.45, y) * (1.0 - smoothstep(EDGE_R - 0.005, EDGE_R + 0.03, y));
	// Streaks along the swing: lines at random depths, bold and broken, with dark between.
	float lines = vnoise(vec2(along * 1.2 + seed * 3.1, y * 55.0 + seed));
	float fine = vnoise(vec2(along * 3.0 - seed, y * 150.0));
	float streak = 0.05 + 1.6 * pow(lines, 3.0) + 0.25 * fine;
	// The edge itself: a thin hot line at the reach, brightest at the blade,
	// coming to a point with the crescent at both ends.
	float ed = (y - EDGE_R) / 0.013;
	float tipOff = smoothstep(0.0, 0.07, t) * (1.0 - smoothstep(0.75, 1.0, tc)) * smoothstep(0.0, 0.1, along);
	float edge = exp(-ed * ed) * mix(1.0, 0.3, tc) * tipOff;
	float halo = exp(-pow((y - EDGE_R) / 0.045, 2.0)) * 0.3 * (1.0 - tc) * tipOff;
	// The smear, brighter towards the edge and the blade.
	float body = pow(across, 1.8) * streak * inBand * mix(1.0, 0.3, tc);
	// Eaten from the tail as it dies: soft tatters, round in the swing's plane,
	// drawn out a little along it as a fast thing's are.
	float n = fbm(vec2(along * 4.5, y * 7.0) + seed * 1.37);
	float wear = smoothstep(0.4, 1.0, tc) * 0.65 + (1.0 - left) * 1.1 - 0.1;
	float keep = smoothstep(wear - 0.16, wear + 0.16, n);
	// Colour: white-hot at the edge, the hue in the smear, its deeper, darker self behind.
	vec3 hue = v_hue.rgb;
	vec3 deep = hue * hue * 0.35;
	vec3 hot = mix(hue, vec3(1.0), 0.75) * 2.4;
	vec3 smear = mix(deep, hue, smoothstep(0.15, 0.95, across) * mix(1.0, 0.45, tc));
	vec3 light = smear * body * 0.8 + hot * (edge * 1.3 + halo * 0.4);
	light *= keep;
	// The dark bed under it: the smear's shape, a little softer, so the light reads over pale bodies.
	float bed = smoothstep(inner - 0.07, inner + depth * 0.5, y) * (1.0 - smoothstep(EDGE_R, EDGE_R + 0.07, y)) * step(0.001, depth);
	float dark = bed * 0.5 * mix(1.0, 0.2, tc) * smoothstep(0.1, 0.7, keep) * left * left * smoothstep(-0.05, 0.05, t);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = light * left * clear;
	ALPHA = clamp(dark * clear, 0.0, 1.0);
}
