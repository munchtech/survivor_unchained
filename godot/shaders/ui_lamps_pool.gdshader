// The Lamps' Open wide (§12 A; the mock's skins/a.py pools()): each lit lamp gives the world back its own colors round
// it. One instance per lit lamp (src/Ui/LampGrade.cs), reading the world as it was before the grade (the same
// back-buffer copy the grade read) and laid over the grade with a Gaussian's weight (1 at the lamp, sigma 34 px; 14 at
// the Valley), plus a 5% warm lift. The field's knockout and edges hold it as they hold the board.
// INSTANCE_CUSTOM: x sigma px.
shader_type canvas_item;
render_mode unshaded, blend_premul_alpha;

#include "res://shaders/ui_lamps_field.gdshaderinc"

uniform sampler2D screen : hint_screen_texture, filter_linear, repeat_disable;
uniform float amount = 1.0;

varying vec2 lp;
varying flat float sg;

void vertex() {
	sg = INSTANCE_CUSTOM.x;
	lp = (UV - 0.5) * 2.0 * 3.0 * sg;
	COLOR = vec4(1.0);
}

void fragment() {
	float w = exp(-dot(lp, lp) / (2.0 * sg * sg)) * amount * field_mask(FRAGCOORD.xy);
	vec3 world = textureLod(screen, SCREEN_UV, 0.0).rgb + vec3(1.0, 0.69, 0.29) * 0.05;
	COLOR = vec4(world * w, w);
}
