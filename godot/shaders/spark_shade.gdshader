// A dark soft bed under a bright core in flight (src/Fx/BattleFx.Skills.cs),
// drawn over the crowd before the core: a light passing over the pale dead
// needs dark round it to be seen. COLOR is the dark and how much of it.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

void vertex() {
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(INV_VIEW_MATRIX[0].xyz * s, 0.0), vec4(INV_VIEW_MATRIX[1].xyz * s, 0.0), vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0), MODEL_MATRIX[3]);
}

void fragment() {
	float r = length(UV * 2.0 - 1.0);
	float a = pow(max(0.0, 1.0 - r), 1.3);
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a * a * smoothstep(0.33, 1.0, clear);
}