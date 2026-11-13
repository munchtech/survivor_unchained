// A gem's glint (bd-ui W16): a four-point star that always faces the camera, laid over the stone.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled;

uniform float strength = 1.6;

void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float h = exp(-abs(p.y) * 34.0) * (1.0 - abs(p.x));
	float v = exp(-abs(p.x) * 34.0) * (1.0 - abs(p.y));
	float core = exp(-dot(p, p) * 90.0);
	float s = clamp(max(h, v) + core, 0.0, 1.0);
	ALBEDO = vec3(1.0, 0.97, 0.92);
	ALPHA = clamp(s * strength, 0.0, 1.0);
}
