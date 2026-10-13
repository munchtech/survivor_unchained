// Burns Twice's ice shards (Fx/Flare/FlareShards.cs): real lit geometry, so the fire beside them lights them
// and the night's sky glints off their faces. Dark cold glass with bright edges, never white; a cold rim
// light; the instance colour tints them (a shattered body's shards keep a little of its paint). INSTANCE_CUSTOM.x
// is the shard's heat (lit from inside by the ember that broke it, cooling), .y its melt (0..1, it thins).
shader_type spatial;
render_mode diffuse_burley, specular_disabled, cull_back;

global uniform sampler2D flare_plate : filter_linear_mipmap, repeat_enable;

varying flat vec4 v_c;
varying vec3 v_local;

void vertex() {
	v_c = INSTANCE_CUSTOM;
	v_local = VERTEX;
	// Melting: thinner, from the outside in.
	VERTEX *= 1.0 - 0.55 * INSTANCE_CUSTOM.y;
	// Half-rounded normals: light runs across each face as across cut glass, never one flat white plane
	// (t5: flat facets read as paper flakes up close).
	NORMAL = normalize(mix(NORMAL, normalize(v_local * vec3(1.0, 0.25, 1.0) + vec3(0.0, 1e-3, 0.0)), 0.55));
}

void fragment() {
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float cr = texture(flare_plate, v_local.xy * 3.0 + v_local.z * 1.7).r;
	// Glass: a dark cold body you see into, its edges bright, a glint only when a face turns to the eye.
	// (The moon's specular on mirror-smooth facets lit whole shards white: paper flakes, t5 and t6. So no direct
	// specular: the glint is drawn, a small spot that sweeps across a face as the shard tumbles.)
	// (At 0.025-0.08 the ring's flung shards were black flecks against its line: t10, s2b.)
	vec3 ice = vec3(0.06, 0.12, 0.2) * (0.7 + 0.8 * cr);
	// The ring's thrown shards cool to dark ash-glass where they land (INSTANCE_CUSTOM.z). (At 0.17 grey, lit
	// by the BOOM's light on the char, they lay over the field as pale confetti, s5.)
	float ash = v_c.z;
	ALBEDO = mix(mix(ice * 0.6, COLOR.rgb * 0.15, COLOR.a * 0.3), vec3(0.04, 0.042, 0.048), ash);
	ROUGHNESS = 0.3;
	SPECULAR = 0.0;
	METALLIC = 0.0;
	float heat = v_c.x;
	float melt = v_c.y;
	float glint = smoothstep(0.986, 0.998, dot(NORMAL, VIEW));
	float plane = smoothstep(0.72, 0.8, cr) * (1.0 - smoothstep(0.8, 0.9, cr));
	// (The cold rim is put out by the heat: orange faces with blue rims added up to pink, s5.)
	EMISSION = vec3(0.2, 0.48, 0.95) * (pow(rim, 2.0) * 0.8 + plane * 0.16 + 0.05) * (1.0 - 0.6 * melt) * (1.0 - 0.95 * ash) * (1.0 - 0.85 * clamp(heat, 0.0, 1.0))
		+ vec3(0.75, 0.88, 1.0) * glint * 1.4 * (1.0 - melt) * (1.0 - ash)
		// Hot: lit orange through its faces by the fire that threw it, brightest at its edges.
		// Only its edges and a breath of its body: a whole face lit read as a flat flake of confetti (s5).
		+ vec3(1.0, 0.3, 0.04) * heat * (0.06 + 1.3 * pow(rim, 2.5));
}
