// Her barrier gain (BattleFx.WardenHoly, VFX 10 item 3): a band ~9 px thick (0.13 m) of ~20 near-white gold glints
// (3-5 px each) climbing her feet to crown over the gain's 0.42 s, then a 2 px gold fresnel rim on her silhouette
// (80% at the gain, 45% while the barrier holds). Weighted to the silhouette so it never washes her front.
// The mesh: a unit sphere (Godot SphereMesh, radius 0.5) stretched round her (2.02 m tall). COLOR.r the strength
// (the gain's share of her health, lower by night), COLOR.g the rim's strength, COLOR.a the climb's age, 0..1.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_back, shadows_disabled, fog_disabled;

varying float ly;

float h1(float n) { return fract(sin(n * 91.345) * 47453.5453); }

void vertex() {
	ly = VERTEX.y + 0.5;
}

void fragment() {
	float k = COLOR.r, rimk = COLOR.g, p = COLOR.a;
	float fr = 1.0 - abs(dot(normalize(NORMAL), normalize(VIEW)));
	float rim = smoothstep(0.6, 0.72, fr);
	// the glints: 20 columns round her, each a dot at its own height inside the band that climbs
	float cols = 20.0;
	float cx = UV.x * cols, ci = floor(cx);
	float c0 = mix(0.02, 1.0, p);
	float oy = (h1(ci * 5.1 + 1.0) - 0.5) * 0.065;
	float dx = (fract(cx) - 0.5) * (3.3 / cols);
	float dy = (ly - (c0 + oy)) * 2.02;
	float dot_ = 1.0 - smoothstep(0.022, 0.05, length(vec2(dx, dy)));
	float vis = smoothstep(0.0, 0.08, p) * (1.0 - smoothstep(0.9, 1.0, p));
	vec3 glint = vec3(1.0, 0.92, 0.7) * 2.4;
	vec3 gold = vec3(1.0, 0.7, 0.28) * 1.6;
	ALBEDO = (glint * dot_ * (0.4 + 0.6 * rim) * vis * k + gold * rim * rimk);
}
