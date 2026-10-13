// Burns Twice's ice shards (Fx/Flare/FlareShards.cs): real lit geometry, so the fire beside them lights them
// and the night's sky glints off their faces. Glassy ford-blue at a middle value, never white; a cold rim
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
}

void fragment() {
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float cr = texture(flare_plate, v_local.xy * 3.0 + v_local.z * 1.7).r;
	vec3 ice = vec3(0.16, 0.27, 0.4) * (0.75 + 0.6 * cr);
	ALBEDO = mix(ice, COLOR.rgb * 0.6, COLOR.a * 0.45);
	ROUGHNESS = 0.08 + 0.25 * cr;
	SPECULAR = 0.75;
	METALLIC = 0.0;
	RIM = 0.4;
	RIM_TINT = 0.2;
	float heat = v_c.x;
	EMISSION = vec3(0.25, 0.52, 0.95) * pow(rim, 3.0) * 0.45 + vec3(1.0, 0.36, 0.07) * heat * (0.35 + 0.8 * pow(rim, 2.0)) * 1.4;
}
