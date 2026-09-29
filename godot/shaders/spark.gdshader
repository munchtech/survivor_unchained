// A spark, a mote, a puff: a soft round sprite facing the camera, its size
// the instance's scale and its colour the instance's (above 1 to bloom).
// The additive kind for light (sparks, cores, trails); the mixed kind for
// smoke and dust (spark_smoke.gdshader includes this with blend_mix).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

varying vec4 tint;

void vertex() {
	tint = COLOR;
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * s, INV_VIEW_MATRIX[1] * s, INV_VIEW_MATRIX[2] * s, MODEL_MATRIX[3]);
}

void fragment() {
	float d = length(UV * 2.0 - 1.0);
	float a = pow(max(0.0, 1.0 - d), 1.6);
	ALBEDO = tint.rgb * a * tint.a;
}
