// A drifting band of mist (fx "mist"): fractal noise moving with the wind,
// thinned toward the band's edges so it has no frame.
shader_type canvas_item;
render_mode blend_mix;

#include "res://shaders/storybook/story_noise.gdshaderinc"

uniform float t = 0.0;
uniform vec2 size = vec2(1000.0, 300.0);
uniform vec4 color : source_color = vec4(0.75, 0.8, 0.85, 1.0);
uniform float density = 0.5;
uniform vec2 speed = vec2(12.0, 0.0);
uniform float scale = 260.0;
uniform float seed = 0.0;

void fragment() {
	vec2 p = UV * size;
	vec2 q = (p - speed * t) / scale + seed * 3.1;
	// Two layers at different speeds, so it rolls rather than slides.
	float n = sb_fbm2(q) * 0.65 + sb_fbm2(q * 1.9 - speed.yx * t / scale * 0.6 + 11.0) * 0.35;
	float shape = smoothstep(0.35, 0.8, n);
	float edge = smoothstep(0.0, 0.3, UV.y) * smoothstep(1.0, 0.55, UV.y) * smoothstep(0.0, 0.12, UV.x) * smoothstep(1.0, 0.88, UV.x);
	COLOR = vec4(color.rgb, color.a * shape * density * edge);
}
