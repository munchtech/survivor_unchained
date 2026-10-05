// Loot's light (BattleFx.Loot): light standing on what fell, in the colour of its band.
//
// Each light is a quad held upright on the screen at the item's own depth, so it rises straight
// up the screen wherever the item lies. A world-upright tube under a camera pitched 56 degrees
// leans away from the middle of the screen, and a tall one swells as it nears the camera: the
// Legendary's forty metres read as a huge slanted bar. Here a pillar is sized to reach just past
// the top of the screen and no further.
//
// It is light, not a thing: a hot hairline core in a soft glow that falls away to nothing at its
// sides (gaussians, never an edge), a pool of its light on the ground round its foot, and life
// moving up it. Held below the tone curve's knee: past about 1.5 every band folds to cream.
//
// Instances: the basis's x scale is the half-width in metres, y the height, z the kind (its whole
// part) and a parameter (its fraction); colour in rgb, strength in a.
//   1 Rare: a low glow.            2 Epic: thin and taller (it breathes; the caller sets strength).
//   3 Set: two strands twisting.   4 Pillar: Legendary and Storied, past the top of the screen.
//   5 Strike: a Legendary's light falling onto it as it lands (the fraction is how far through).
//   6 Glow: a plain short light (Chart, Quest, the hoard stone).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled, skip_vertex_transform;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;

varying vec3 tint;
varying vec2 at;
varying float half_w;
varying float tall;
varying float kind;
varying float param;
varying float seed;

void vertex() {
	half_w = length(MODEL_MATRIX[0].xyz);
	tall = length(MODEL_MATRIX[1].xyz);
	float k = length(MODEL_MATRIX[2].xyz);
	kind = floor(k + 0.001);
	param = clamp(k - kind, 0.0, 1.0);
	tint = COLOR.rgb * COLOR.a;
	seed = fract(sin(dot(MODEL_MATRIX[3].xz, vec2(12.9898, 78.233))) * 43758.5453);
	vec3 foot = (VIEW_MATRIX * vec4(MODEL_MATRIX[3].xyz, 1.0)).xyz;
	// A pillar reaches the top of the screen at the item's depth, and a little past it.
	if (kind > 3.5 && kind < 5.5)
		tall = max(tall, -foot.z / abs(PROJECTION_MATRIX[1][1]) - foot.y + half_w);
	// Below the foot by the pool's reach (a circle on the ground seen from 56 degrees up).
	float down = half_w * 0.85;
	at = vec2(VERTEX.x * 2.0 * half_w, mix(-down, tall, VERTEX.y + 0.5));
	VERTEX = foot + vec3(at, 0.0);
}

float hash(float n) { return fract(sin(n * 91.7 + seed * 37.3) * 43758.5453); }
float g(float x, float s) { return exp(-(x * x) / (s * s)); }

// Its light on the ground round its foot, as the camera sees a circle there.
float pool(float r) {
	vec2 e = vec2(at.x / r, at.y / (r * 0.83));
	return exp(-dot(e, e) * 2.2);
}

// Motes of light climbing it: a few at a time, each in its own lane.
float motes(float spread, float speed, float gap) {
	float y = at.y - TIME * speed;
	float cell = floor(y / gap);
	float fy = fract(y / gap);
	float mx = (hash(cell) - 0.5) * spread;
	float my = 0.25 + 0.5 * hash(cell + 5.0);
	return g(at.x - mx, 0.03) * g((fy - my) * gap, 0.045) * step(0.45, hash(cell + 9.0));
}

void fragment() {
	float x = at.x, y = at.y;
	float H = max(tall, 0.01);
	float u = clamp(y / H, 0.0, 1.0);
	// Born out of the ground with no line where it meets it.
	float rise = smoothstep(-0.04, 0.12, y);
	float shimmer = 0.86 + 0.14 * sin(y * 1.9 - TIME * 2.6 + seed * 6.28);
	// Coloured light is palest at its heart and deepest where it thins: the line in its band's
	// colour, the glow and the pool round it deeper still (a pale glow by day reads as haze).
	float top = max(max(tint.r, tint.g), max(tint.b, 1e-3));
	vec3 deep = tint * tint / top;
	vec3 light = vec3(0.0);
	float veil = 0.0;

	if (kind < 1.5) {
		// Rare: a low glow, a fine bright line in it, its light pooled at its foot.
		float fade = rise * pow(1.0 - u, 1.5);
		light = (mix(tint, deep, 0.35) * g(x, 0.026) * 1.1 + deep * g(x, 0.13) * 0.5) * fade * shimmer + deep * pool(half_w * 0.6) * 0.34;
		veil = (g(x, 0.05) * 0.45 + g(x, 0.16) * 0.2) * fade + pool(half_w * 0.6) * 0.06;
	} else if (kind < 2.5) {
		// Epic: thinner and taller, a line of light in a narrow glow, a mote climbing it now and then.
		float fade = rise * pow(1.0 - u, 1.25);
		float up = motes(0.1, 1.1, 0.7) * fade;
		light = (tint * (g(x, 0.022) * 1.1 + up * 0.8) + deep * (g(x, 0.1) * 0.42 + g(x, 0.34) * 0.1)) * fade * shimmer
			+ deep * pool(half_w * 0.6) * 0.34;
		veil = (g(x, 0.045) * 0.45 + g(x, 0.14) * 0.2) * fade + pool(half_w * 0.6) * 0.06;
	} else if (kind < 3.5) {
		// Set: two strands twisting about each other, the one in front the brighter (that is what
		// reads as a twist and not as two lines), a faint glow between them.
		float fade = rise * pow(1.0 - u, 1.1);
		float amp = 0.15 * (1.0 - 0.45 * u) * smoothstep(-0.05, 0.35, y);
		float ph = y * 3.3 - TIME * 2.1 + seed * 6.28;
		float s1 = amp * sin(ph);
		float front = cos(ph);
		float w1 = 0.45 + 0.55 * front, w2 = 0.45 - 0.55 * front;
		float lines = g(x - s1, 0.02) * max(w1, 0.08) + g(x + s1, 0.02) * max(w2, 0.08);
		float halo = g(x - s1, 0.07) * max(w1, 0.15) + g(x + s1, 0.07) * max(w2, 0.15);
		light = (mix(tint, deep, 0.3) * lines * 1.2 + deep * (halo * 0.36 + g(x, 0.26) * 0.1)) * fade + deep * pool(half_w * 0.6) * 0.32;
		veil = (g(x - s1, 0.045) + g(x + s1, 0.045)) * fade * 0.26 + pool(half_w * 0.6) * 0.06;
	} else if (kind < 4.5) {
		// The pillar: a hot core, a glow round it and a wide soft halo, rising past the top of the
		// screen, brightest where it stands and thinning as it climbs. Motes ride up it.
		float fade = rise * (1.0 - 0.55 * smoothstep(0.0, 1.0, u));
		float up = motes(0.24, 2.4, 0.8) * (1.0 - u * 0.6);
		// The foot burns brighter: where the light meets the ground.
		float hearth = g(x, 0.22) * g(y, 0.35);
		vec3 amber = mix(tint, deep, 0.5);
		light = (tint * (g(x, 0.045) * 1.2 + up * 0.9) + amber * g(x, 0.16) * 0.5 + deep * g(x, 0.6) * 0.16) * fade * shimmer
			+ amber * hearth * 0.5 + deep * pool(half_w * 0.75) * 0.5;
		veil = (g(x, 0.07) * 0.3 + g(x, 0.3) * 0.1) * fade + pool(half_w * 0.75) * 0.14;
	} else if (kind < 5.5) {
		// The strike: its light falling down the screen onto it, a bright head and a trail, and
		// on landing a flash at its foot.
		float p = param;
		float head = mix(H, 0.0, smoothstep(0.0, 0.45, p));
		float trail = smoothstep(head - 0.1, head + 0.6, y) * exp(-max(y - head, 0.0) / (H * 0.35));
		float fall = 1.0 - smoothstep(0.45, 0.9, p);
		float flash = smoothstep(0.38, 0.5, p) * (1.0 - smoothstep(0.5, 1.0, p));
		light = (tint * g(x, 0.05) * 1.3 + deep * g(x, 0.22) * 0.45) * trail * fall
			+ deep * pool(half_w * 0.7) * flash * 0.65 + tint * g(x, 0.22) * g(y, 0.4) * flash * 0.6;
		veil = g(x, 0.1) * trail * fall * 0.25 + pool(half_w * 0.8) * flash * 0.15;
	} else {
		// A plain short glow.
		float fade = rise * pow(1.0 - u, 1.5);
		light = (tint * g(x, 0.03) * 0.75 + deep * g(x, 0.14) * 0.36) * fade + deep * pool(half_w * 0.55) * 0.26;
		veil = (g(x, 0.06) * 0.2 + g(x, 0.16) * 0.08) * fade + pool(half_w * 0.55) * 0.08;
	}

	// Seen dimmed behind what stands well in front of it, but never cut off by the ground round
	// its foot (that ground is nearer the camera than the item itself).
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float slack = 0.6 + half_w * 0.9;
	float hidden = smoothstep(slack, slack + 0.8, behind.z - VERTEX.z);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	float keep = (1.0 - hidden * 0.75) * clear;
	ALBEDO = light * keep;
	// A touch of the ground behind is taken where it is densest, so by day it reads as coloured
	// light and not as a pale wash added over a bright ground.
	ALPHA = clamp(veil * keep, 0.0, 0.5);
}
