// The Lamps board's halos (src/Ui/LampBoard.cs): one additive pass, lit lamps only, at most 90 (§6: 1.8x its size).
// Instance COLOR: the halo's color. INSTANCE_CUSTOM: x radius px, y flicker, z 1 at the Valley (one tight spot).
shader_type canvas_item;
render_mode blend_add, unshaded;

#include "res://shaders/ui_lamps_field.gdshaderinc"
uniform float find_on = 0.0;

varying flat vec4 d0;
varying flat vec4 d1;
varying vec2 lp;

void vertex() {
	d0 = COLOR;
	d1 = INSTANCE_CUSTOM;
	float H = d1.z > 0.5 ? max(d1.x * 1.4, 2.5) * 3.2 : d1.x * 1.8 * 3.2;
	lp = (UV - 0.5) * 2.0 * H;
	COLOR = vec4(1.0);
}

void fragment() {
	float R = d1.x, flick = d1.y;
	float r2 = dot(lp, lp);
	float g;
	if (d1.z > 0.5) {
		float sg = max(R * 1.4, 2.5);
		g = 0.55 * flick * exp(-r2 / (2.0 * sg * sg));
	} else {
		float s1 = 0.9 * R, s2 = 1.8 * R;
		g = 0.55 * flick * exp(-r2 / (2.0 * s1 * s1)) + 0.10 * flick * exp(-r2 / (2.0 * s2 * s2));
	}
	g *= 0.85 * (find_on > 0.5 ? 0.45 : 1.0);
	float m = field_mask(FRAGCOORD.xy);
	COLOR = vec4(d0.rgb * d0.a, clamp(g * m, 0.0, 1.0));
}
