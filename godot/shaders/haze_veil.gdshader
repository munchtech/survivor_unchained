// (E8 later r2) The air between the gate and what the open gate shows (C04 A8): a sheet just past the gatehouse's back,
// the sky's horizon colour (Atmosphere sets it) laid over the house, the lamp and the road beyond at a fixed share, so
// they sit back from the jambs (the house wall measured the jamb's value, 51,54,71 to 50,52,66: no air between).
// Hidden everywhere else by the gatehouse round it. One draw, no shadow.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;
uniform vec3 haze_col : source_color = vec3(0.37, 0.33, 0.41);
uniform float amount = 0.22;
void fragment() {
	ALBEDO = haze_col;
	ALPHA = amount;
}
