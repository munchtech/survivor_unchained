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
uniform float soot_max = 0.85;
// How much the dip takes from the fire (1/dip - 1) after the birth: the hottest of it (straight luma undip_lo..hi) gets it back.
uniform float undip = 0.0;
uniform float undip_lo = 0.5;
uniform float undip_hi = 0.8;
// The soot eroding from its thin edge first (0 none .. 1 all), with a noise so it tears rather than shrinks.
uniform float erode = 0.0;
// The heat (judge 6 A1: f72-f85 read as uniform mid-orange clay): after the birth the fire is gradient-mapped by its
// heat, the atlas's straight luma x its density (thin fire runs cooler), cooling with age: a white-yellow core
// (heat gm_lo..gm_hi, pushed gm_hot over the tonemapper's white, gone by sim frame gm_end), an orange body, and
// edges falling to dark red and into the smoke (gm_edge: the heat under which it darkens).
uniform float gm = 1.0;
uniform float gm_lo = 0.20;
uniform float gm_hi = 0.33;
uniform float gm_hot = 7.0;
uniform float gm_end = 15.0;
uniform float gm_edge = 0.10;
// The body's light (under the tonemapper's knee, so it stays orange: brighter it went cream).
uniform float gm_body = 0.6;
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
	vec4 c0 = c;
	if (f < birth_end) {
		// straight colour (the atlas is premultiplied): its top channel finds the heart, its luma the body
		vec3 sc = c.rgb / max(c.a, 1e-3);
		float l = dot(sc, vec3(0.2126, 0.7152, 0.0722));
		float heart = smoothstep(hot_lo, hot_hi, l) * (1.0 - smoothstep(4.0, 7.0, f));
		float s = mix(1.0, mix(sat, 1.0, smoothstep(birth_end - 4.0, birth_end, f)), smoothstep(0.04, 0.15, l));
		sc = max(mix(vec3(l), sc, mix(s, 1.0, heart)), vec3(0.0));
		c.rgb = sc * c.a * (1.0 + hot * heart);
	}
	if (gm > 0.0) {
		vec3 sc = c0.rgb / max(c0.a, 1e-3);
		float l = dot(sc, vec3(0.2126, 0.7152, 0.0722));
		float heat = l * mix(0.55, 1.0, smoothstep(0.15, 0.7, c0.a)) * mix(1.0, 0.75, smoothstep(6.0, 22.0, f));
		// (the atlas's hottest runs low over sim frames 4-8, p99 0.27-0.3 against 0.45 either side: the core held through it)
		heat *= 1.0 + 0.3 * smoothstep(3.0, 4.5, f) * (1.0 - smoothstep(6.5, 8.5, f));
		float core = smoothstep(gm_lo, gm_hi, heat) * (1.0 - smoothstep(gm_end - 6.0, gm_end, f));
		float t = clamp(heat / gm_lo, 0.0, 1.0);
		// dark red at the edges, orange through the body, white-yellow at the core
		vec3 hue = mix(vec3(1.0, 0.04, 0.0), vec3(1.0, 0.24, 0.0), smoothstep(0.45, 0.9, t));
		hue = mix(hue, vec3(1.0, 0.86, 0.62), core);
		float lum = max(l, 0.02) * mix(0.25 * gm_body, gm_body, smoothstep(gm_edge / gm_lo, 0.9, t)) * (1.0 + gm_hot / gm_body * core);
		vec3 g = hue * (lum / dot(hue, vec3(0.2126, 0.7152, 0.0722)));
		c.rgb = mix(c.rgb, g * c.a, gm * smoothstep(1.5, 3.0, f));
	}
	// Nothing outside the fire before f124 (judge 5a 1d: an olive haze hugged the young ball): its thin veil clipped,
	// the clip let go over f120-f134 (judge 5b 2a: released in one step it filmed the folds), the veil's light x density^2.
	float vk = 1.0 - smoothstep(3.4, 11.0, f);
	c *= mix(1.0, smoothstep(0.1 * vk, 0.2 * vk + 1e-3, c.a), vk);
	c.rgb *= mix(1.0, smoothstep(0.0, 0.35, c.a), smoothstep(3.4, 5.0, f) * (1.0 - smoothstep(14.0, 18.0, f)));
	// The fire is opaque (judge 5b 1c: statues and frost showed through its lobes): its bright body covers what's behind.
	{
		float lf = dot(c.rgb / max(c.a, 1e-3), vec3(0.2126, 0.7152, 0.0722));
		float a = max(c.a, smoothstep(0.12, 0.3, lf) * smoothstep(0.08, 0.3, c.a));
		c.a = a;
	}
	{
		// the soot: a pixel's darkness (straight luma under ~0.2) is how much of it is soot
		float l = dot(c.rgb / max(c.a, 1e-3), vec3(0.2126, 0.7152, 0.0722));
		float soot = 1.0 - smoothstep(0.02, 0.2, l);
		// lit in proportion to its own value (judge 5a 3: folds to bellies ~1:3), and from one side
		float own = smoothstep(0.0, 0.08, l);
		float side = 0.5 + 0.5 * soot_up * (1.0 - 2.0 * UV.y);
		c.rgb = max(c.rgb, soot_lit * mix(0.22, 1.0, own * own) * mix(0.6, 1.2, side) * c.a * soot);
		float a = mix(c.a, min(c.a, soot_max), soot);
		// eroding from its thin edge first, torn by a noise drifting up
		float n = textureLod(flare_noise, UV * 2.5 + vec2(0.0, life * 0.4), 0.0).r;
		a *= mix(1.0, smoothstep(erode, erode + 0.25, a + 0.3 * (n - 0.5)), soot);
		c.rgb *= a / max(c.a, 1e-3);
		c.a = a;
	}
	if (undip > 0.0) {
		float lh = dot(c.rgb / max(c.a, 1e-3), vec3(0.2126, 0.7152, 0.0722));
		c.rgb *= 1.0 + undip * smoothstep(undip_lo, undip_hi, lh);
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
