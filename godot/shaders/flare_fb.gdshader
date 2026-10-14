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
uniform vec3 fire_tint = vec3(1.0); // (burns_boom5's own colour: no tint)
uniform float soft = 0.8;
// The birth (atlas cells 0..birth_end): the atlas tops out at 1.0, so its white-yellow heart (linear luma
// hot_lo..hot_hi: the top fifth of b5dx's ball in cells 0-2, a tenth in 3) is pushed past the tonemapper's white
// (hot: how far over, fading out over cells 4-7) and its body pre-saturated against AgX's desaturation of bright
// colour (sat, back to 1 by birth_end). Judge 4 fix 1; solver 5's limits. (s9: lo 0.82 gave 11-16% of the ball.)
uniform float hot = 3.0;
uniform float hot_lo = 0.74;
uniform float hot_hi = 0.90;
uniform float sat = 1.8;
// (b5e burns to ~f24: its fire keeps the birth's saturation through its whole life, the soot never gets it.)
uniform float birth_end = 24.0;
// The soot, lit (judge 4 fix 3: black soot read as a hole): its dark pixels lifted to at least soot_lit (night amber
// lit from below by the fire, day grey-brown with sunlit tops: soot_up +1 lit from above, -1 from below), and laid
// over the world at most soot_max.
uniform vec3 soot_lit = vec3(0.08, 0.035, 0.012);
uniform float soot_up = -1.0;
uniform float soot_max = 0.7;
// The soot eroding from its thin edge first (0 none .. 1 all), with a noise so it tears rather than shrinks.
uniform float erode = 0.0;
global uniform sampler2D flare_noise : filter_linear_mipmap, repeat_enable;

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
	if (f < birth_end) {
		// straight colour (the atlas is premultiplied): its top channel finds the heart, its luma the body
		vec3 sc = c.rgb / max(c.a, 1e-3);
		float l = dot(sc, vec3(0.2126, 0.7152, 0.0722));
		float heart = smoothstep(hot_lo, hot_hi, l) * (1.0 - smoothstep(4.0, 7.0, f));
		float s = mix(1.0, mix(sat, 1.0, smoothstep(birth_end - 4.0, birth_end, f)), smoothstep(0.04, 0.15, l));
		sc = max(mix(vec3(l), sc, mix(s, 1.0, heart)), vec3(0.0));
		c.rgb = sc * c.a * (1.0 + hot * heart);
	}
	// Nothing outside the fire before f124 (judge 5a 1d: an olive haze hugged the young ball): its thin veil clipped.
	c *= mix(1.0, smoothstep(0.1, 0.2, c.a), 1.0 - smoothstep(4.5, 6.0, f));
	{
		// the soot: a pixel's darkness (straight luma under ~0.2) is how much of it is soot
		float l = dot(c.rgb / max(c.a, 1e-3), vec3(0.2126, 0.7152, 0.0722));
		float soot = 1.0 - smoothstep(0.02, 0.2, l);
		// lit in proportion to its own value (judge 5a 3: folds to bellies ~1:3), and from one side
		float own = smoothstep(0.0, 0.08, l);
		float side = 0.5 + 0.5 * soot_up * (1.0 - 2.0 * UV.y);
		c.rgb = max(c.rgb, soot_lit * mix(0.3, 1.0, own) * mix(0.6, 1.2, side) * c.a * soot);
		float a = mix(c.a, min(c.a, soot_max), soot);
		// eroding from its thin edge first, torn by a noise drifting up
		float n = textureLod(flare_noise, UV * 2.5 + vec2(0.0, life * 0.4), 0.0).r;
		a *= mix(1.0, smoothstep(erode, erode + 0.25, a + 0.3 * (n - 0.5)), soot);
		c.rgb *= a / max(c.a, 1e-3);
		c.a = a;
	}
	// Square, soft: the atlas fades its own cells (pack.py); a round fade trimmed the rising smoke.
	vec2 q = abs(UV * 2.0 - 1.0);
	c *= 1.0 - smoothstep(0.9, 0.995, max(q.x, q.y));
	float k = fade;
	if (soft > 0.0) {
		float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
		vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
		behind.xyz /= behind.w;
		k *= clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	}
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = c.rgb * fire_tint * gain * k * clear;
	ALPHA = c.a * smoke * k * clear;
}
