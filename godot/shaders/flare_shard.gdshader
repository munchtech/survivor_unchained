// Burns Twice's ice shards (Fx/Flare/FlareShards.cs): real lit geometry, so the fire beside them lights them
// and the night's sky glints off their faces. Dark cold glass with bright edges, never white; a cold rim
// light; the instance colour tints them (a shattered body's shards keep a little of its paint). INSTANCE_CUSTOM.x
// is the shard's heat (lit from inside by the ember that broke it, cooling), .y its melt (0..1, it thins).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_back;

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
	// Glass: a dark cold body you see into, its edges and fracture planes bright, its one face's glint sharp.
	vec3 ice = vec3(0.025, 0.05, 0.08) * (0.7 + 0.8 * cr);
	ALBEDO = mix(ice, COLOR.rgb * 0.22, COLOR.a * 0.3);
	ROUGHNESS = 0.05 + 0.1 * cr;
	SPECULAR = 0.6;
	METALLIC = 0.0;
	RIM = 0.25;
	RIM_TINT = 0.6;
	float heat = v_c.x;
	float plane = smoothstep(0.72, 0.8, cr) * (1.0 - smoothstep(0.8, 0.9, cr));
	EMISSION = vec3(0.2, 0.48, 0.95) * (pow(rim, 4.0) * 0.6 + plane * 0.18) * (1.0 - 0.6 * v_c.y)
		+ vec3(1.0, 0.36, 0.07) * heat * (0.35 + 0.8 * pow(rim, 2.0)) * 0.6;
}
