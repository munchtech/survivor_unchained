// Smoke and dust: a soft round sprite facing the camera, blended over what
// is behind it (spark.gdshader's twin).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

varying vec4 tint;

void vertex() {
	tint = COLOR;
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * s, INV_VIEW_MATRIX[1] * s, INV_VIEW_MATRIX[2] * s, MODEL_MATRIX[3]);
}

void fragment() {
	float d = length(UV * 2.0 - 1.0);
	ALBEDO = tint.rgb;
	ALPHA = tint.a * smoothstep(1.0, 0.25, d);
}
