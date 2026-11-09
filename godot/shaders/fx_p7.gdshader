// P7's shapes after the grade, hidden behind her where she stands in front (FxAfter.OccludeFigure's twins write depth).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_p7.gdshaderinc"
void fragment() {
	vec3 a; float al;
	p7_frag(UV, NORMAL, VIEW, a, al);
	ALBEDO = a; ALPHA = al;
}
