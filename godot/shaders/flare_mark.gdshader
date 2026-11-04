shader_type spatial;
// The marks' light (LOOK_BIBLE row 8: light on the ground, soft-edged, never a vector line): flare_mark.gdshaderinc.
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/flare_mark.gdshaderinc"

void fragment() {
	vec2 m = flare_mark_at(UV);
	ALBEDO = mk_col.rgb * m.x;
}
