// The den's painted set (den round 10, DungeonDress.Set.cs; the paintings by tools/look/den_set.py): each module is the
// painting laid in the camera's plane and cast along the play camera's view onto its proxy (the bank's surface and the
// floor for the banks, a half-ellipsoid on the floor for a boulder), so every painted pixel sits at the depth of the
// ground it shows: she stands in front of the far bank, behind the near bank's crest, on the roots spilled on the floor.
// The painting is already lit and shaded (its lit tops, cool gaps and ink): the room's light only scales it (no cel bands,
// no n.l from the key; a soft turn for the shafts' spots and the fungus' omnis), as the round 6 boulders.
// COLOR.r: the module's fade (1 shown; toward 0 only its brightest masses, so a module laid over its neighbour shows its
// roots crossing the other's and never a seam); COLOR.g: 0 where the cast landed on walkable floor beyond the bank.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, specular_disabled;

uniform sampler2D paint_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float gain = 1.0;                       // the painting's albedo scale (calibrated on the den's frames)
uniform vec3 tint = vec3(1.0);
uniform float sat = 1.0;
uniform float cold_take = 0.5;                  // how much of a cold light's brightness it takes (never its colour)
uniform float local_turn = 0.5;                 // how much a spot or omni follows the proxy's normal (0 flat)
uniform float key_shadow = 0.0;                 // 1: the key's shadow falls on it (her shadow on a spill); 0: pre-lit only

void fragment() {
	vec4 c = texture(paint_tex, UV);
	float lb = dot(textureLod(paint_tex, UV, 3.0).rgb, vec3(0.299, 0.587, 0.114));
	float s = smoothstep(0.1, 0.4, sqrt(max(lb, 0.0)));
	float show = step(1.0, s + COLOR.r + 0.001);
	vec3 col = c.rgb * tint;
	col = mix(vec3(dot(col, vec3(0.299, 0.587, 0.114))), col, sat);
	ALBEDO = col * gain;
	ALPHA = c.a * show * step(0.5, COLOR.g);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// the ink tag (cel.gdshaderinc's cel_tag): roughness 1, class 2 (no post ink: the painting carries its own)
	ROUGHNESS = 126.0 / 127.0;
}

void light() {
	float w = LIGHT_IS_DIRECTIONAL ? 1.0 : mix(1.0, max(dot(NORMAL, LIGHT), 0.0), local_turn);
	vec3 lc = LIGHT_COLOR;
	float ll = dot(lc, vec3(0.299, 0.587, 0.114));
	lc = LIGHT_IS_DIRECTIONAL || lc.r >= lc.g ? lc : vec3(ll) * cold_take;
	float att = LIGHT_IS_DIRECTIONAL ? mix(1.0, ATTENUATION, key_shadow) : ATTENUATION;
	DIFFUSE_LIGHT += lc * att * w / PI;
}
