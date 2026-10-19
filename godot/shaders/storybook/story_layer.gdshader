// A storybook layer and its living touches (docs/storybook/README.md, "Touches").
// One shader for every touch, each switched by its own flag; the blend line
// below is swapped by the player for add, screen and multiply layers.
shader_type canvas_item;
render_mode blend_mix;

#include "res://shaders/storybook/story_noise.gdshaderinc"

// 0 mix, 1 add, 2 screen (premultiplied, by the colour's own lightness), 3 multiply.
uniform int blend = 0;
// The plate's clock (seconds) and the image's size in its own pixels.
uniform float t = 0.0;
uniform vec2 px = vec2(1024.0);

uniform bool flicker_on = false;
uniform float flicker_rate = 7.0;
uniform float flicker_amount = 0.25;
uniform float flicker_seed = 0.0;

uniform bool sway_on = false;
uniform sampler2D sway_mask : hint_default_white, filter_linear;
uniform float sway_amp = 4.0;
uniform float sway_freq = 0.35;
uniform vec2 sway_dir = vec2(1.0, 0.0);
uniform float sway_scale = 220.0;

uniform bool water_on = false;
uniform sampler2D water_mask : hint_default_white, filter_linear;
uniform float water_amp = 1.5;
uniform float water_freq = 1.4;
uniform float water_scale = 36.0;

uniform bool ripple_on = false;
uniform sampler2D ripple_mask : hint_default_white, filter_linear;
uniform vec2 ripple_c[8];
uniform int ripple_n = 0;
uniform float ripple_start = 0.0;
uniform float ripple_period = 3.0;
uniform float ripple_speed = 60.0;
uniform float ripple_amp = 2.0;
uniform float ripple_rings = 3.0;
uniform float ripple_gap = 22.0;
uniform float ripple_reach = 260.0;
uniform float ripple_squash = 1.0;
uniform float ripple_light = 0.25;

uniform bool reveal_on = false;
uniform sampler2D reveal_map : hint_default_white, filter_linear;
uniform float reveal_t0 = 0.0;
uniform float reveal_t1 = 1.0;
uniform float reveal_soft = 0.08;
uniform bool reveal_invert = false;

uniform vec2 scroll_speed = vec2(0.0);

void fragment() {
	vec2 p = UV * px;
	vec2 d = vec2(0.0);
	if (sway_on) {
		float m = texture(sway_mask, UV).r;
		vec2 dir = length(sway_dir) > 0.0 ? normalize(sway_dir) : vec2(1.0, 0.0);
		vec3 q = vec3(p / sway_scale, t * sway_freq);
		float a = sb_fbm3(q) * 2.0 - 1.0;
		float b = sb_fbm3(q + vec3(31.7, 7.3, 0.0)) * 2.0 - 1.0;
		// Mostly along its direction, a little across it, so cloth and flame curl.
		d += (dir * a + vec2(-dir.y, dir.x) * b * 0.3) * sway_amp * m;
	}
	if (water_on) {
		float m = texture(water_mask, UV).r;
		vec3 q = vec3(p / water_scale, t * water_freq);
		d += vec2(sb_noise3(q) - 0.5, sb_noise3(q + vec3(5.2, 1.3, 2.8)) - 0.5) * 2.0 * water_amp * m;
	}
	float light = 0.0;
	if (ripple_on && t >= ripple_start) {
		float m = texture(ripple_mask, UV).r;
		float tau = mod(t - ripple_start, ripple_period);
		float life = 1.0 - tau / ripple_period;
		for (int i = 0; i < 8; i++) {
			if (i >= ripple_n) break;
			vec2 v = p - ripple_c[i];
			v.y /= max(0.05, ripple_squash);
			float r = length(v);
			float front = ripple_speed * tau;
			float wave = 0.0;
			for (int j = 0; j < 6; j++) {
				if (float(j) >= ripple_rings) break;
				float x = r - (front - float(j) * ripple_gap);
				wave += exp(-x * x / (ripple_gap * ripple_gap * 0.08)) * (j == 0 ? 1.0 : 0.75);
			}
			float fade = pow(clamp(1.0 - r / ripple_reach, 0.0, 1.0), 2.0) * life * step(0.0, front - r + ripple_gap);
			wave *= fade * m;
			vec2 dir = r > 0.001 ? v / r : vec2(0.0);
			dir.y *= ripple_squash;
			d += dir * wave * ripple_amp;
			light += wave * ripple_light;
		}
	}
	vec2 uv = (p + d + scroll_speed * t) / px;
	vec4 c = texture(TEXTURE, uv);
	c.rgb *= 1.0 + light;
	if (flicker_on) {
		// Layered noise, never a sine: a slow swell, a quicker waver and a fine tremble.
		float x = t * flicker_rate + flicker_seed * 13.7;
		float n = 0.55 * sb_noise1(x * 0.35) + 0.3 * sb_noise1(x * 1.1 + 7.0) + 0.15 * sb_noise1(x * 3.3 + 19.0);
		c.rgb *= 1.0 + flicker_amount * (n * 2.0 - 1.0);
	}
	if (reveal_on) {
		float k = clamp((t - reveal_t0) / max(1e-4, reveal_t1 - reveal_t0), 0.0, 1.0) * (1.0 + reveal_soft);
		float a = 1.0 - smoothstep(k - reveal_soft, k, texture(reveal_map, UV).r);
		c.a *= reveal_invert ? 1.0 - a : a;
	}
	c *= COLOR;
	if (blend == 2) {
		// Screen, approximately: lighten by the colour's own lightness.
		float l = max(c.r, max(c.g, c.b));
		c = vec4(c.rgb * c.a, l * c.a);
	} else if (blend == 3) {
		c = vec4(mix(vec3(1.0), c.rgb, c.a), 1.0);
	}
	COLOR = c;
}
