// The warm breath round an ember lying on the ground (src/Fx/BattleFx.cs Pickups): a soft round
// glow facing the camera, added light, so a stone a few pixels across reads at the play camera.
// COLOR is its warmth and strength (the pulse rides COLOR.a and the size, set per stone).
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

void vertex() {
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(INV_VIEW_MATRIX[0].xyz * s, 0.0), vec4(INV_VIEW_MATRIX[1].xyz * s, 0.0), vec4(INV_VIEW_MATRIX[2].xyz * s, 0.0), MODEL_MATRIX[3]);
}

void fragment() {
	float r = length(UV * 2.0 - 1.0);
	// (a gaussian-ish fall: a warm heart, no hard rim)
	float a = exp(-r * r * 5.0) * (1.0 - smoothstep(0.85, 1.0, r));
	ALBEDO = COLOR.rgb * COLOR.a * a;
}
