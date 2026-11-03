// The Lamps' Open wide (docs/design/LAMPS_SCREEN_BRIEF.md §12 A, §16 "A's night grade"; the mock's skins/a.py grade()):
// night falls over the live world. By day a dusk (saturation x0.40, luminance x0.42, a quarter toward a warm gray);
// by night x0.62 and a moonlight multiply (0.85, 0.93, 1.10) so the world outside the pools still reads; a soft
// vignette from the field's middle. Drawn once over the 3D, under the HUD and the screen (src/Ui/LampGrade.cs).
shader_type canvas_item;
render_mode unshaded, blend_disabled;

uniform sampler2D screen : hint_screen_texture, filter_linear, repeat_disable;
uniform float amount = 1.0;        // the open's fade (0.35 s in, 0.2 s out)
uniform float night = 0.0;
uniform vec2 field_c = vec2(960.0, 522.0);
uniform vec2 vp_size = vec2(1920.0, 1080.0);

void fragment() {
	vec3 rgb = textureLod(screen, SCREEN_UV, 0.0).rgb;
	float sat = mix(0.40, 0.50, night), mul = mix(0.42, 0.62, night);
	vec3 tint = mix(vec3(0.078, 0.086, 0.102), vec3(0.043, 0.059, 0.086), night);
	float lum = dot(rgb, vec3(0.2126, 0.7152, 0.0722));
	vec3 g = (vec3(lum) + (rgb - lum) * sat) * mul;
	g = g * 0.75 + tint * 0.25;
	g *= mix(vec3(1.0), vec3(0.85, 0.93, 1.10), night);
	vec2 px = SCREEN_UV * vp_size * (1080.0 / vp_size.y);
	float r = length(px + 0.5 - field_c) / length(vec2(960.0, 540.0));
	g *= 1.0 - 0.25 * smoothstep(0.55, 1.0, r);
	COLOR = vec4(mix(rgb, g, amount), 1.0);
}
