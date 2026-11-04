shader_type spatial;
// The marks' soft shade just outside each ring, so a ring holds over a pale day ground (flare_mark.gdshaderinc).
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/flare_mark.gdshaderinc"

void fragment() {
	vec2 m = flare_mark_at(UV);
	ALBEDO = vec3(0.0);
	ALPHA = clamp(mk_col.a * m.y, 0.0, 1.0);
}
