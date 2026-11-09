// (L1 lead 7) A lookdev stroke: fx_stroke on a quad (UV.x along, tail 0 to head 1; UV.y across), drawn after the grade.
// Spawned by --fx-debug-stroke (FxAfter.DebugStroke) over the first danger mark, for the marks-over and world-depth A|Bs.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"
uniform float stroke_life = 0.1;
void fragment() {
	vec4 c = fx_stroke(UV.y * 2.0 - 1.0, UV.x, stroke_life);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}
