// Her barrier gain (BattleFx.WardenHoly, VFX 10 item 3): a gold shimmer climbing her body, feet to crown over the
// gain's 0.42 s, broken into fine vertical glints, with a faint shell of light round her (its fresnel rim) that
// comes up at once and fades. Weighted to the silhouette so it never washes her front. Never white.
// The mesh: a unit sphere (Godot SphereMesh, radius 0.5) stretched round her. COLOR.r its strength (the gain's
// share of her health, lower by night), COLOR.a its age, 0..1.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

varying float ly;

float h1(float n) { return fract(sin(n * 91.345) * 47453.5453); }
float n1(float x) { float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h1(i), h1(i + 1.0), f); }

void vertex() {
	ly = VERTEX.y + 0.5;
}

void fragment() {
	float k = COLOR.r, p = COLOR.a;
	float fr = 1.0 - abs(dot(normalize(NORMAL), normalize(VIEW)));
	float rim = pow(fr, 2.6);
	float c0 = mix(-0.05, 1.1, pow(p, 0.85));
	float band = exp(-pow((ly - c0) / 0.06, 2.0));
	float trail = ly < c0 ? exp(-(c0 - ly) / 0.14) : 0.0;
	float glints = smoothstep(0.55, 0.95, n1(UV.x * 70.0 + floor(p * 12.0) * 3.1));
	float shell = rim * 0.28 * smoothstep(0.0, 0.12, p) * pow(1.0 - p, 1.3);
	float climb = (band * (0.35 + 0.65 * glints) + trail * 0.25 * glints) * (0.2 + 0.8 * rim) * (1.0 - smoothstep(0.85, 1.0, p));
	vec3 gold = vec3(1.0, 0.58, 0.15);
	vec3 bronze = vec3(0.6, 0.28, 0.07);
	ALBEDO = (gold * climb * 0.95 + bronze * shell) * k;
}
