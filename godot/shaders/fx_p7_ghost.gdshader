// P7s afterimages: her pose as a rim of light over a clear core that still writes depth, so her own limbs behind do not show.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_always, cull_back, shadows_disabled, fog_disabled;
#include "res://shaders/fx_p7.gdshaderinc"
void fragment() {
	vec3 a; float al;
	p7_frag(UV, NORMAL, VIEW, a, al);
	ALBEDO = a; ALPHA = al;
}
