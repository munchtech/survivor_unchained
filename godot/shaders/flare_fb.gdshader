// One of a Flare's own simulated bursts (tools/fxsim: Mantaflow fire and smoke, rendered at the game's pitch and
// cut into a premultiplied atlas), played once on a single camera-facing quad that the Flare's clock drives (so
// hitstop holds it or not, as the Flare decides). The engine is flipbook.gdshader's: frames blended, the colour
// premultiplied (fire adds, smoke lays over), soft where it meets the ground, held off her (hero_clear).
shader_type spatial;
render_mode unshaded, blend_premul_alpha, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform int grid = 7;
uniform int frames = 48;
// Where in the burst, 0..1 over its frames.
uniform float life = 0.0;
// The fire's light (above 1 blooms), and the smoke's weight laid over the world (0 lets it through).
uniform float gain = 1.0;
uniform float smoke = 1.0;
uniform float fade = 1.0;
// The fire's hue: the sim's tone read salmon over the night ground (s5f); less blue makes it burn orange.
uniform vec3 fire_tint = vec3(1.0, 0.92, 0.6);
uniform float soft = 0.8;
// The BOOM's ring (flare_world): its first tenth of a second shows through the fireball's base (judge 3).
global uniform sampler2D flare_marks : filter_nearest, repeat_disable;

void vertex() {
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(INV_VIEW_MATRIX[0].xyz * s, 0.0), vec4(INV_VIEW_MATRIX[1].xyz * s, 0.0),
		vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0), MODEL_MATRIX[3]);
}

vec4 cell(int i, vec2 uv, float lod) {
	vec2 at = vec2(float(i % grid), float(i / grid));
	return textureLod(atlas, (at + uv) / float(grid), lod);
}

void fragment() {
	float f = clamp(life, 0.0, 1.0) * float(frames - 1);
	int i0 = int(floor(f));
	int i1 = min(i0 + 1, frames - 1);
	vec2 texels = UV * vec2(textureSize(atlas, 0)) / float(grid);
	float lod = clamp(log2(max(length(dFdx(texels)), length(dFdy(texels)))), 0.0, 3.0);
	vec4 c = mix(cell(i0, UV, lod), cell(i1, UV, lod), fract(f));
	c.rgb = min(c.rgb, vec3(c.a));
	// Square, soft: the atlas fades its own cells (pack.py); a round fade trimmed the rising smoke.
	vec2 q = abs(UV * 2.0 - 1.0);
	c *= 1.0 - smoothstep(0.9, 0.995, max(q.x, q.y));
	float k = fade;
	if (soft > 0.0) {
		float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
		vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		behind.xyz /= behind.w;
		k *= clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
		vec4 bm = texelFetch(flare_marks, ivec2(31, 0), 0);
		if (bm.z > 0.0 && bm.w < 0.13) {
			vec3 gw = (INV_VIEW_MATRIX * vec4(behind.xyz, 1.0)).xyz;
			float x = clamp((bm.w - 0.01) / 0.7, 0.0, 1.0);
			float ahead = bm.z * (1.0 - pow(1.0 - x, 2.5)) - length(gw.xz - bm.xy);
			float line = exp(-pow((ahead - 0.05) / 0.3, 2.0));
			k *= 1.0 - 0.85 * line * (1.0 - smoothstep(0.07, 0.13, bm.w));
		}
	}
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = c.rgb * fire_tint * gain * k * clear;
	ALPHA = c.a * smoke * k * clear;
}
