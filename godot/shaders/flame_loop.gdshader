// A flame filmed and cut into an atlas (art/fx/fb/fire_loop), played round
// and round on a card that faces the camera but stays upright. The clip
// does not loop of itself, so two plays half a cycle apart are blended, each
// fading in and out with its own cycle: no frame where it jumps back to the
// start. A card's own `phase` keeps several in one fire out of step.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform int grid = 8;
uniform int frames = 64;
uniform float fps = 24.0;
uniform float phase = 0.0;
uniform float glow = 1.6;
uniform vec3 tint : source_color = vec3(1.0, 0.92, 0.85);
uniform float soft = 0.25;

void vertex() {
	// Upright, turned toward the camera about the vertical only.
	vec3 to_cam = INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz;
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam));
	vec3 s = vec3(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[1].xyz), 1.0);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(right * s.x, 0.0), vec4(0.0, s.y, 0.0, 0.0), vec4(cross(right, vec3(0.0, 1.0, 0.0)), 0.0), MODEL_MATRIX[3]);
}

vec4 cell(float f, vec2 uv) {
	int i = int(mod(floor(f), float(frames)));
	vec2 at = vec2(float(i % grid), float(i / grid));
	return texture(atlas, (at + uv) / float(grid));
}

vec4 play(float f, vec2 uv) {
	return mix(cell(f, uv), cell(f + 1.0, uv), fract(f));
}

void fragment() {
	float n = float(frames);
	float f = mod(TIME * fps + phase * n, n);
	float g = mod(f + n * 0.5, n);
	// Each play strongest in the middle of its cycle, gone at its ends.
	float wa = 1.0 - abs(f / n * 2.0 - 1.0);
	float wb = 1.0 - wa;
	vec4 c = play(f, UV) * wa + play(g, UV) * wb;
	c.rgb = min(c.rgb, vec3(c.a));
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	ALBEDO = c.rgb * tint * glow * fade;
}
