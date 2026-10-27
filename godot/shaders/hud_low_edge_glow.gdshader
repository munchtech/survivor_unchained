// HUD "her life": the low-life edge's crimson light, added over hud_low_edge.gdshader's darkening (its parent quad).
shader_type canvas_item;
render_mode blend_add;
#include "res://shaders/hud_low_edge.gdshaderinc"

uniform vec4 blood : source_color = vec4(0.90, 0.09, 0.05, 1.0);
uniform float glow = 0.30;   // how much crimson light at full

void fragment()
{
	float a = edge_a(UV);
	if (a <= 0.002) discard;
	COLOR = vec4(blood.rgb * a * glow, 1.0);
}
