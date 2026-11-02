// Watch Bell's spectral bell (BattleFx.WardenHoly, VFX 10 item 3): bronze-gold, mostly see-through. A fresnel rim
// of bronze round its outline and the inside of its mouth, a dim body, two cast bands (at the sound bow and the
// shoulder), and its lip lit gold when struck, the strike running up the body as it fades. Never white.
// The mesh (BattleFx.BellMesh): UV.y up it (0 the lip, 1 the crown). COLOR.r its strength (lower by night),
// COLOR.g the strike (1 as it tolls, decaying), COLOR.a its alpha.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

void fragment() {
	float k = COLOR.r, strike = COLOR.g, a = COLOR.a, y = UV.y;
	float fr = 1.0 - abs(dot(normalize(NORMAL), normalize(VIEW)));
	float rim = pow(fr, 2.4);
	float bands = exp(-pow((y - 0.2) / 0.014, 2.0)) * 0.7 + exp(-pow((y - 0.8) / 0.012, 2.0)) * 0.5 + exp(-pow((y - 0.86) / 0.01, 2.0)) * 0.35;
	float lip = smoothstep(0.16, 0.0, y);
	// the strike's light climbing from the lip as it rings out
	float climb = exp(-pow((y - (1.0 - strike) * 0.9) / 0.12, 2.0)) * strike;
	vec3 bronze = vec3(0.58, 0.27, 0.07);
	vec3 gold = vec3(1.0, 0.57, 0.15);
	vec3 c = bronze * (0.07 + rim * 0.95 + bands * (0.25 + 0.4 * rim)) + gold * (lip * (0.18 + 0.85 * strike) * (0.45 + 0.55 * rim) + climb * 0.3 * (0.3 + 0.7 * rim));
	ALBEDO = c * k * a;
}
