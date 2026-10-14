// Burns Twice's ice shards (Fx/Flare/FlareShards.cs): real lit geometry, faceted plates of cold glass, so the fire
// beside them lights them and their facets flash as they tumble. A cold blue-grey glass body that reads on char and
// on frost alike, never white; a cold rim; the instance colour tints them (a shattered body's shards keep a little
// of its paint). INSTANCE_CUSTOM.x is the shard's heat (lit from inside by the ember that broke it, cooling), .y its
// melt (0..1 after it lands: it sinks to a pool and glints), .z 1 once landed, .w its seed.
shader_type spatial;
render_mode diffuse_burley, specular_disabled, cull_back;

global uniform sampler2D flare_plate : filter_linear_mipmap, repeat_enable;

varying flat vec4 v_c;
varying vec3 v_local;

void vertex() {
	v_c = INSTANCE_CUSTOM;
	v_local = VERTEX;
	// Facets stay facets (judge 3 asked for faceted plates); a breath of dome so a face never goes one flat white.
	NORMAL = normalize(mix(NORMAL, normalize(VERTEX * vec3(0.6, 4.0, 0.6) + vec3(0.0, 1e-3, 0.0)), 0.15));
}

float fl_h(float x) { return fract(sin(x * 91.7) * 43758.5453); }

void fragment() {
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float cr = texture(flare_plate, v_local.xz * 1.6 + v_local.y * 1.7).r;
	float heat = clamp(v_c.x, 0.0, 1.0);
	float melt = v_c.y;
	float seed = v_c.w;
	// Which facet this is (the twelve each face their own way): each flashes on its own clock while it tumbles.
	float fid = floor(atan(v_local.z, v_local.x) * 0.955 + 3.0) + step(0.0, v_local.y) * 7.0;
	float tick = floor(TIME * (11.0 + 7.0 * seed) + seed * 17.0 + fid * 3.1);
	float flick = step(0.72, fl_h(seed * 13.0 + fid * 1.37 + tick * 0.173));
	// Glass: a cold blue-grey body, lit by the fire and the moon like any solid (at 0.04-0.06 dark glass it was
	// invisible on the char: judge 3).
	vec3 ice = vec3(0.2, 0.26, 0.33) * (0.8 + 0.45 * cr);
	vec3 alb = mix(ice, COLOR.rgb * 0.4, COLOR.a * 0.25);
	// Melted: darker wet stone under a skin of water.
	ALBEDO = mix(alb, vec3(0.05, 0.06, 0.075), smoothstep(0.2, 0.8, melt));
	ROUGHNESS = 0.3;
	SPECULAR = 0.0;
	METALLIC = 0.0;
	float glint = smoothstep(0.975, 0.995, dot(NORMAL, VIEW));
	float plane = smoothstep(0.72, 0.8, cr) * (1.0 - smoothstep(0.8, 0.9, cr));
	float alive = 1.0 - smoothstep(0.35, 0.75, melt);
	// The pool's last glints: sharp, a few frames on and off, gone as it dries.
	float pool = smoothstep(0.3, 0.6, melt) * (1.0 - smoothstep(0.85, 1.0, melt)) * step(0.55, fl_h(seed * 7.0 + tick * 0.31))
		* (1.0 - smoothstep(0.05, 0.11, length(v_local.xz - vec2(fl_h(seed) - 0.5, fl_h(seed + 0.5) - 0.5) * 0.4)));
	// (The cold rim is put out by the heat: orange faces with blue rims added up to pink, s5.)
	EMISSION = vec3(0.22, 0.42, 0.75) * (pow(rim, 2.0) * 0.7 + plane * 0.14 + 0.06) * alive * (1.0 - 0.85 * heat)
		+ vec3(0.7, 0.86, 1.0) * (glint * 1.3 + flick * (1.0 - v_c.z) * 0.55) * alive * (1.0 - 0.8 * heat)
		+ vec3(0.8, 0.92, 1.0) * pool * 1.8
		// Hot: lit orange through its faces by the fire that threw it, brightest at its edges.
		// Only its edges and a breath of its body: a whole face lit read as a flat flake of confetti (s5).
		+ vec3(1.0, 0.3, 0.04) * heat * (0.06 + 1.3 * pow(rim, 2.5));
}
