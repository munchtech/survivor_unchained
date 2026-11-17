// (lane B fx s3, 16 Nov: E rule 4; coordinator #15) Sunder's shockwave: ONE painted ring on the ground in front of her,
// after the grade (FxAfter: the steel bands are the board's colors, which the in-frame AgX caps near C 0.10), hidden
// behind whatever stands on it (the world depth copy). Its brush is painted once a session in polar form
// (BattleFx.Grip.cs SunderRingPaint): R heat (1 the hot inner lip, 0 the dry outer front), G coverage, B the order it
// erodes in (the dry front first, the lip last). The plane is the cut's: local +X along the cut's line, scaled to the
// ring's radius; the texture spans ring_range radians of it across that line and ring_r0..1 of the radius.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform sampler2D ring_tex : filter_linear_mipmap, repeat_disable;
uniform float ring_range = 2.79;
uniform float ring_r0 = 0.6;
uniform float ring_flip = 1.0;
// 1: white-hot (the core band over the body, the mid at its dry front); 0: the steel bands
uniform float ring_hot = 1.0;
// heat at or over it is the mid band (gold), under it the edge (amber); it rises as the ring cools
uniform float ring_cut = 0.45;
// heat at or over it is white while hot
uniform float ring_core = 0.3;
// grain under it has eroded away (0 whole, 1 gone)
uniform float ring_fade = 0.0;

varying vec2 lp;

void vertex() {
	lp = VERTEX.xz;
}

void fragment() {
	float rho = length(lp);
	float u = ring_flip * atan(lp.y, lp.x) / ring_range + 0.5;
	float v = (rho - ring_r0) / (1.0 - ring_r0);
	if (u < 0.0 || u > 1.0 || v < 0.0 || v > 1.0) discard;
	vec3 t = texture(ring_tex, vec2(u, v)).rgb;
	float heat = t.r, grain = t.b;
	float aa = max(fwidth(grain) * 0.75, 0.01);
	float a = t.g * smoothstep(ring_fade - aa, ring_fade + aa, grain);
	if (a < 0.004) discard;
	vec3 c = ring_hot > 0.5 ? mix(fx_mid, fx_core, fx_step(ring_core, heat)) : mix(fx_edge, fx_mid, fx_step(ring_cut, heat));
	ALBEDO = fx_out(c, a);
	ALPHA = a;
}
