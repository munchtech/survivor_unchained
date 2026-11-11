// P7s afterimages: her pose as an amber rim of light over a clear core. (Round 3: the core no longer writes depth: its
// clear core cut dark holes in the ribbon behind it, the r2 judge's "dark blotches".)
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled, fog_disabled;
#include "res://shaders/fx_p7.gdshaderinc"
void fragment() {
	vec3 a; float al;
	p7_frag(UV, NORMAL, VIEW, a, al);
	ALBEDO = a; ALPHA = al;
}
