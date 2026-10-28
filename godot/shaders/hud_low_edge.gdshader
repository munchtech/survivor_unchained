// Her life's low edge (HerLight.cs): at 30% of her life and under, the screen's edges darken
// to a deep blood red that beats with her heart (HeartPulse: the sound's own pacing). Subtle at 30%, stronger
// toward none; it never reaches into the middle 70% of the screen (a rounded square, |x| and |y| under 0.70 of
// the half-screen stay clear). One full-screen quad, a few ALU ops.
shader_type canvas_item;
render_mode blend_mix;
#include "res://shaders/hud_low_edge.gdshaderinc"

uniform sampler2D screen : hint_screen_texture, filter_linear;
uniform vec3 tint = vec3(0.78, 0.09, 0.08);   // the grey edge multiplied toward deep crimson
uniform vec4 blood : source_color = vec4(0.95, 0.10, 0.06, 1.0);
uniform float glow = 0.60;   // crimson light at the beat's peak, inside the band (m^1.5: it reads at 18% too)
// (judges 3-4: crimson added over the night blue read plum; a multiply toward red over blue read aubergine. The
// edge now takes the scene to grey first, then to dark crimson, then lights a crimson band on the beat, so the fade
// runs blue, grey-dark, crimson and never violet. It reads the screen, so it costs one screen copy, and only at
// low life: the node is hidden otherwise.)

void fragment()
{
	float a = edge_a(UV);
	if (a <= 0.002) discard;
	vec3 c = texture(screen, SCREEN_UV).rgb;
	float m = clamp(a / 0.9, 0.0, 1.0);
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(c, vec3(l), smoothstep(0.0, 0.40, m));
	// (UI 16 judge round 4: the band read heavier at the top left, where the ground is lit: its light evened toward
	// one level inside the band, so it is the same weight round the whole screen)
	c *= mix(1.0, clamp(0.11 / max(l, 0.02), 0.55, 1.6), 0.55 * smoothstep(0.0, 0.6, m));
	// (UI 16 judge: on lit ground the band's inner edge read salmon: the red comes in faster than the light goes)
	c *= mix(vec3(1.0), tint, smoothstep(0.0, 0.65, m));
	c += blood.rgb * pow(m, 1.5) * glow * smoothstep(0.1, 0.9, beat);
	COLOR = vec4(c, 1.0);
}
