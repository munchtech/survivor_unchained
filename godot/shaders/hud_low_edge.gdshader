// HUD variant "her life" (--hud-life her, HerLight.cs): at 30% of her life and under, the screen's edges darken
// to a deep blood red that beats with her heart (HeartPulse: the sound's own pacing). Subtle at 30%, stronger
// toward none; it never reaches into the middle 70% of the screen (a rounded square, |x| and |y| under 0.70 of
// the half-screen stay clear). One full-screen quad, a few ALU ops.
shader_type canvas_item;
render_mode blend_mul;
#include "res://shaders/hud_low_edge.gdshaderinc"

uniform vec3 tint = vec3(0.92, 0.16, 0.12);   // what the edge multiplies the scene by at full: blue and green crushed
// (UI 15 judge 2: crimson ADDED over the blue night grade read mauve where it faded; the multiply darkens toward
// deep crimson first, then hud_low_edge_glow.gdshader (a child quad) adds a little crimson light on top)

void fragment()
{
	float a = edge_a(UV);
	if (a <= 0.002) discard;
	COLOR = vec4(mix(vec3(1.0), tint, a), 1.0);
}
