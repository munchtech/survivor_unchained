// P7's shapes that sit on her or a body (the press glint on her blade, a hit's star): over everything after the grade.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_p7.gdshaderinc"
void fragment() {
	vec3 a; float al;
	p7_frag(UV, NORMAL, VIEW, a, al);
	ALBEDO = a; ALPHA = al;
}
