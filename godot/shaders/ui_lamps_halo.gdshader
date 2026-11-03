// The Lamps board's halos (src/Ui/LampBoard.cs): one additive pass, lit lamps only, at most 90 (§6: 1.8x its size).
// Instance COLOR: the halo's color. INSTANCE_CUSTOM: x radius px, y seed (its flicker's phase), z 1 at the Valley (one
// tight spot) + 2 guttering (a lamp put out: its halo fades over 0.2 s), w the event's time (LampMotion's clock): lit, the
// catch (the halo grows over 0.3 s from it); guttering, the put out.
shader_type canvas_item;
render_mode blend_add, unshaded;

#include "res://shaders/ui_lamps_field.gdshaderinc"
#include "res://shaders/ui_lamps_motion.gdshaderinc"
uniform float find_on = 0.0;

varying flat vec4 d0;
varying flat vec4 d1;
varying flat vec2 mo;        // x the alpha (open, close, catch, gutter), y the size (the bloom grows it)
varying vec2 lp;

void vertex() {
	d0 = COLOR;
	d1 = INSTANCE_CUSTOM;
	int z = int(d1.z + 0.5);
	bool vy = (z & 1) != 0, gut = (z & 2) != 0;
	float H = vy ? max(d1.x * 1.4, 2.5) * 3.2 : d1.x * 1.8 * 3.2;
	lp = (UV - 0.5) * 2.0 * H;
	// the open: the halos bloom last (0.20-0.35 s), from x0.6
	float o = ease_out(halo_open());
	float a = o * close_out(), sz = mix(0.6, 1.0, o);
	float t = now - d1.w;
	if (gut) a *= 1.0 - clamp(t / DRAIN, 0.0, 1.0);
	else if (t > -1.0 && t < HALO_GROW) { float u = ease_out(t / HALO_GROW); a *= u; sz *= mix(0.5, 1.0, u); }
	else if (t <= 0.0 && t > -1.0) a = 0.0;
	mo = vec2(a, sz);
	COLOR = vec4(1.0);
}

void fragment() {
	float R = d1.x;
	int z = int(d1.z + 0.5);
	float flick = (z & 1) != 0 ? 1.0 + (d1.y - 0.5) * 0.08 : flicker(d1.y);
	vec2 q = lp / max(mo.y, 0.05);
	float r2 = dot(q, q);
	float g;
	if ((z & 1) != 0) {
		float sg = max(R * 1.4, 2.5);
		g = 0.55 * flick * exp(-r2 / (2.0 * sg * sg));
	} else {
		float s1 = 0.9 * R, s2 = 1.8 * R;
		g = 0.55 * flick * exp(-r2 / (2.0 * s1 * s1)) + 0.10 * flick * exp(-r2 / (2.0 * s2 * s2));
	}
	g *= 0.85 * (find_on > 0.5 ? 0.45 : 1.0) * mo.x;
	float m = field_mask(FRAGCOORD.xy);
	COLOR = vec4(d0.rgb * d0.a, clamp(g * m, 0.0, 1.0));
}
