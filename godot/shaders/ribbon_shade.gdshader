// The shadow laid under a ribbon of light (src/Fx/Ribbons.cs): wider than
// the ribbon, dark, soft across and gone at its tail. Light over the pale
// dead (the risen are bone-grey) washes out to white; a dark bed round it is
// what lets a trail be seen at all, as an outline does for a figure. UV2.x is
// how dark, COLOR the hue of the dark.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

void fragment() {
	float across = abs(UV.y * 2.0 - 1.0);
	float body = 1.0 - smoothstep(0.0, 1.0, across);
	body *= body;
	ALBEDO = COLOR.rgb;
	// Over the survivor the dark gives way altogether: she is never shadowed by her own light.
	float clear = hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
	ALPHA = clamp(body * COLOR.a * UV2.x * smoothstep(0.33, 1.0, clear), 0.0, 1.0);
}
