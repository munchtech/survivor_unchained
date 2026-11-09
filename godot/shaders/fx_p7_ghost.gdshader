// P7's afterimages: her pose in the mid band, with a depth prepass so her own limbs do not double where they overlap.
shader_type spatial;
render_mode unshaded, blend_mix, depth_prepass_alpha, cull_back, shadows_disabled, fog_disabled;
#include "res://shaders/fx_p7.gdshaderinc"
void fragment() {
	vec3 a; float al;
	p7_frag(UV, NORMAL, VIEW, a, al);
	ALBEDO = a; ALPHA = al;
}
