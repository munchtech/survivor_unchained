// Loot's light (BattleFx.Loot): a column standing on what fell, in the colour of its band. Drawn
// on an open cylinder one unit tall about its origin, scaled to the beam (instances: colour in
// rgb, strength in a). Light, not a tube: a thin hot line down its middle in a soft glow that
// falls away to nothing at its sides, threads of light running up it and a shimmer climbing it,
// born out of the ground with no line where it meets it, thinning away up its length. Held below
// the tone curve's knee (a beam at full strength blooms pastel and every band looks alike).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_back, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float climb = 0.9;

varying vec3 tint;
varying float up;
varying float tall;
varying float seed;

void vertex() {
	tint = COLOR.rgb * COLOR.a;
	up = clamp(VERTEX.y + 0.5, 0.0, 1.0);
	tall = length(MODEL_MATRIX[1].xyz);
	seed = fract(sin(dot(MODEL_MATRIX[3].xz, vec2(12.9898, 78.233))) * 43758.5453);
}

float hash(float n) { return fract(sin(n * 91.7 + seed * 37.3) * 43758.5453); }

void fragment() {
	// Across the column as the eye sees it: 1 down its middle, 0 at its sides.
	float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float line = pow(facing, 14.0);
	float glow = pow(facing, 3.0);
	float metres = up * tall;
	// Threads running up it: a few streaks round it, each its own speed.
	float around = UV.x * 7.0;
	float lane = floor(around);
	float lx = fract(around);
	float thread = smoothstep(0.45, 0.0, abs(lx - 0.5)) * hash(lane + 11.0);
	float run = fract(metres * 0.3 - TIME * climb * (0.6 + 0.8 * hash(lane + 3.0)) + hash(lane + 7.0));
	thread *= smoothstep(0.0, 0.2, run) * smoothstep(1.0, 0.5, run);
	// A shimmer climbing the whole of it.
	float shimmer = 0.82 + 0.18 * sin(metres * 2.3 - TIME * 3.1 + seed * 6.28);
	// Born out of the ground (over its first fifth, or half a metre on a tall one); thinning away
	// up its length.
	float foot = smoothstep(0.0, min(0.5 / max(tall, 0.5), 0.22), up);
	float fade = foot * pow(1.0 - up, 1.3);
	// Seen behind what stands in front of it, but never cut off by the ground it stands in.
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float hidden = smoothstep(0.0, 0.6, behind.z - VERTEX.z);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = tint * (line * 1.4 + glow * 0.45 + thread * glow * 0.6) * shimmer * fade * (1.0 - hidden * 0.7) * clear;
}
