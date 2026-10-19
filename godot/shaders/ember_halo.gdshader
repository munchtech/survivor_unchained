// The warm breath round an ember lying on the ground (src/Fx/BattleFx.cs Pickups): a soft round
// glow facing the camera, added light, so a stone a few pixels across reads at the play camera.
// (it reaches nothing at 0.48 of the quad's width from its middle: no corner, no edge.)
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
	float a = exp(-r * r * 5.0) * (1.0 - smoothstep(0.8, 0.96, r));
	// (the fall rides ALPHA, not only the colour: the engine's fog is mixed into the colour before the
	// blend, so a quad whose colour alone fell to nothing still added the fog's grey as a square
	// (render_mode fog_disabled notwithstanding); the add is colour times alpha, so nothing is left)
	ALBEDO = COLOR.rgb * COLOR.a;
	ALPHA = a;
}
