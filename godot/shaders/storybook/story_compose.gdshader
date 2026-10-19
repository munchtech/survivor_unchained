// The storybook's screen: the plate under and the plate coming in over it,
// each graded and faded on its own, mixed by the transition, then the light
// finish over everything (grain and vignette). docs/storybook/README.md.
shader_type canvas_item;
render_mode blend_disabled;

#include "res://shaders/storybook/story_noise.gdshaderinc"

uniform sampler2D under_tex : filter_linear;
uniform sampler2D over_tex : filter_linear;
uniform bool has_under = false;
uniform bool has_over = false;
// Under's and over's grade: exposure, saturation; tint; how far each has faded to its fade colour.
uniform vec2 under_es = vec2(1.0);
uniform vec3 under_tint = vec3(1.0);
uniform vec4 under_fade = vec4(0.0);
uniform vec2 over_es = vec2(1.0);
uniform vec3 over_tint = vec3(1.0);
uniform vec4 over_fade = vec4(0.0);

// The transition: 0 cut, 1 fade (a dip through its colour), 2 dissolve, 3 ink, 4 light, 5 waterline.
uniform int kind = 0;
uniform float k = 0.0;
uniform vec2 origin = vec2(0.5);
uniform sampler2D ink_map : filter_linear, hint_default_black;
uniform bool has_map = false;
uniform vec3 edge = vec3(0.043, 0.039, 0.035);
uniform float soft = 0.08;
uniform vec3 dip = vec3(0.0);
uniform float wave = 0.025;

uniform float t = 0.0;
uniform float aspect = 1.7778;
uniform vec2 screen = vec2(1920.0, 1080.0);
uniform float grain = 0.05;
uniform float vignette = 0.3;

vec3 graded(vec3 c, vec2 es, vec3 tint, vec4 fade) {
	c *= es.x * tint;
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(vec3(l), c, es.y);
	return mix(c, fade.rgb, fade.a);
}

// The order in which ink reaches each point: a fractal bloom from the origin,
// or the lead's own map (dark first). About 0..1.
float order(vec2 uv) {
	if (has_map) return texture(ink_map, uv).r;
	vec2 v = (uv - origin) * vec2(aspect, 1.0);
	vec2 far = max(origin, 1.0 - origin) * vec2(aspect, 1.0);
	float r = length(v) / length(far);
	// Domain-warped, so the front blooms in lobes like ink taken up by wet paper.
	vec2 w = vec2(sb_fbm2(uv * 3.0 + 4.1), sb_fbm2(uv * 3.0 - 7.3)) - 0.5;
	float n = sb_fbm2(uv * vec2(aspect, 1.0) * 2.2 + w * 1.6);
	float fine = sb_noise2(uv * screen / 6.0) - 0.5;
	return r * 0.78 + (n - 0.5) * 0.5 + fine * 0.02 + 0.08;
}

void fragment() {
	vec2 uv = UV;
	vec3 a = has_under ? graded(texture(under_tex, uv).rgb, under_es, under_tint, under_fade) : vec3(0.0);
	vec3 c = a;
	if (has_over) {
		float e = k * k * (3.0 - 2.0 * k);
		if (kind == 0) {
			c = graded(texture(over_tex, uv).rgb, over_es, over_tint, over_fade);
		} else if (kind == 1) {
			vec3 b = graded(texture(over_tex, uv).rgb, over_es, over_tint, over_fade);
			c = k < 0.5 ? mix(a, dip, smoothstep(0.0, 1.0, k * 2.0)) : mix(dip, b, smoothstep(0.0, 1.0, k * 2.0 - 1.0));
		} else if (kind == 2) {
			vec3 b = graded(texture(over_tex, uv).rgb, over_es, over_tint, over_fade);
			c = mix(a, b, e);
		} else if (kind == 3 || kind == 4) {
			float o = order(uv);
			float th = mix(-soft * 2.0, 1.35 + soft, e);
			float m = 1.0 - smoothstep(th - soft, th, o);
			// Just behind the front the incoming paint is still wet: a little drawn
			// along the bloom, as ink bleeds.
			vec2 pull = (uv - origin) * (1.0 - m) * 0.004;
			vec3 b = graded(texture(over_tex, uv - pull).rgb, over_es, over_tint, over_fade);
			c = mix(a, b, m);
			float rim = exp(-pow((o - (th - soft * 0.6)) / (soft * 0.55 + 0.004), 2.0)) * (1.0 - pow(k, 6.0));
			if (kind == 3) {
				// A dark wet-ink rim, uneven like a brush's edge.
				float ragged = 0.7 + 0.3 * sb_noise2(uv * screen / 14.0);
				c = mix(c, edge, rim * 0.82 * ragged);
			} else {
				// The front is warm light, and it glows a little ahead of itself.
				float ahead = exp(-max(0.0, o - th) / (soft * 2.5 + 0.01)) * (1.0 - m);
				c += edge * (rim * 1.3 + ahead * 0.35) * (1.0 - pow(k, 6.0));
			}
		} else if (kind == 5) {
			// A wavy surface line sweeps up: under it the next plate, a little bent;
			// at it a thin bright skin and a dark band below.
			float line = mix(1.08, -0.1, e) + wave * (sin(uv.x * 11.0 + t * 2.3) * 0.6 + (sb_noise2(vec2(uv.x * 6.0, t * 0.8)) - 0.5) * 1.6);
			float below = smoothstep(line - 0.004, line + 0.004, uv.y);
			vec2 bend = vec2(sin(uv.y * 40.0 + t * 3.0), 0.0) * 0.004 * below;
			vec3 b = graded(texture(over_tex, uv + bend).rgb, over_es, over_tint, over_fade);
			c = mix(a, b, below);
			float dy = uv.y - line;
			c += vec3(0.75, 0.85, 0.9) * exp(-dy * dy / 0.000012) * 0.55;
			c *= 1.0 - exp(-max(0.0, dy) / 0.03) * 0.35 * below;
		}
	}
	// The finish: a vignette, and grain held for a film frame (24 a second).
	vec2 v = (uv - 0.5) * vec2(aspect / 1.7778, 1.0);
	c *= mix(1.0, smoothstep(0.95, 0.25, length(v * vec2(1.0, 1.1))), vignette);
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	float g = sb_hash2(floor(uv * screen) + floor(t * 24.0) * 17.31) - 0.5;
	c += g * grain * (0.35 + 0.65 * sqrt(clamp(l, 0.0, 1.0)));
	COLOR = vec4(max(c, vec3(0.0)), 1.0);
}
