// Watch Bell's spectral bell (BattleFx.WardenHoly, VFX 10 item 3): a thin gold fresnel rim (2-3 px at the play camera,
// #FFD98A at 90%) round its outline, a body 10-20% lit and pale (not amber jelly), its two raised bands (shoulder and
// lip) picked out a little, and the strike running up it from the lip as it fades.
// The mesh (BattleFx.BellMesh): UV.y up it (0 the lip, 1 the crown). COLOR.r its strength (lower by night),
// COLOR.g the strike (1 as it tolls, decaying), COLOR.a its alpha.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

void fragment() {
	float k = COLOR.r, strike = COLOR.g, a = COLOR.a, y = UV.y;
	float fr = 1.0 - abs(dot(normalize(NORMAL), normalize(VIEW)));
	float rim = smoothstep(0.6, 0.72, fr);
	float bands = exp(-pow((y - 0.84) / 0.03, 2.0)) * 0.6 + exp(-pow((y - 0.085) / 0.03, 2.0)) * 0.6;
	float climb = exp(-pow((y - (1.0 - strike) * 0.9) / 0.12, 2.0)) * strike;
	vec3 rimc = vec3(1.0, 0.85, 0.54) * 0.9;
	vec3 body = vec3(0.9, 0.74, 0.5);
	vec3 c = rimc * rim * (1.0 + 0.5 * strike) + body * (0.13 + bands * 0.07 + climb * 0.1 + (1.0 - smoothstep(0.0, 0.16, y)) * strike * 0.08);
	ALBEDO = c * k * a;
}
