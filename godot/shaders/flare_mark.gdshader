shader_type spatial;
// The marks (H7; Fx/Flare/FlareMarksView.cs): light on the ground (LOOK_BIBLE row 8), soft-edged, never a vector line;
// flare_mark.gdshaderinc. One pass, premultiplied: a mark's light adds while its alpha (its light over the cap) lays the
// ground under it back by as much, so overlapping rings converge on the cap and never stack to white; the soft shade just
// outside a ring is alpha alone, tied to the same envelope as its light (a pop or a fade takes it with the light).
// (no depth test: the arena ground stands above HeightAt, and a ring under it was never seen; a ring over a foe's feet reads
// as its under-glow)
render_mode unshaded, blend_premul_alpha, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/flare_mark.gdshaderinc"

void fragment() {
	vec3 m = flare_mark_at(UV);
	float g = max(mk_col.r, max(mk_col.g, mk_col.b));
	vec3 hue = g > 1e-4 ? mk_col.rgb / g : vec3(0.0);
	// The pool leans toward her ember's warmth (light the foe stands in, not a coin under it).
	vec3 pool_hue = mix(hue, warm_hue, warm);
	vec3 light = (hue * m.x + pool_hue * m.y) * g;
	ALBEDO = light;
	float lum = max(light.r, max(light.g, light.b));
	ALPHA = clamp(lum / max(cap, 1e-3) + mk_col.a * m.z, 0.0, 1.0);
}
