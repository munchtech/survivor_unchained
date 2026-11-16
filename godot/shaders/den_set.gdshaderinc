// The den's painted set's body (den_set.gdshader cuts at alpha 0.5; den_set_soft.gdshader blends: the hole paintings).

uniform sampler2D paint_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float gain = 1.0;                       // the painting's albedo scale (calibrated on the den's frames)
uniform vec3 tint = vec3(1.0);
uniform float sat = 1.0;
uniform float cold_take = 0.5;                  // how much of a cold light's brightness it takes (never its colour)
uniform float local_turn = 0.5;                 // how much a spot or omni follows the proxy's normal (0 flat)
uniform float key_shadow = 0.0;                 // 1: the key's shadow falls on it (her shadow on a spill); 0: pre-lit only
// (round 10b) The painting's own shade goes cool grey-violet, its lit masses keep their warmth: the targets' darks between
// the roots are blue-grey (90% of their pixels under 20 of 255 have B >= R), their lit root tops warm. By the painting's own
// luminance (linear): under shade_lo all shade_tint, over shade_hi all the painting's colour.
uniform vec3 shade_tint = vec3(0.84, 0.92, 1.2);
uniform float shade_lo = 0.01;
uniform float shade_hi = 0.08;
uniform float shade_k = 1.0;
// (r10c) The darks between the roots never go black: the targets' sit at L 12-20 of 255, cool; the painting's own darks
// lit at least dark_floor (an emission in shade_tint, fading out over the painting's darkest 5%), whatever light reaches them.
uniform float dark_floor = 0.0;
// (r10c) and the painting shows at least amb_floor of its own painted value where little light reaches (the frame's edges
// fell to 1/20 of it: flat black between roots the target paints at L 20-40)
uniform float amb_floor = 0.0;
uniform float glow_k = 0.7;
// (r12 judge: den_room.png's mushrooms light the ground beneath them teal) the painted caps' halo: their cyan in a coarse
// mip, a little below them in the painting (the ground they stand on), as a soft teal emission on the painting round them
uniform float mush_glow = 0.0;
uniform float mush_lod = 4.5;
uniform float mush_drop = 0.012;
uniform vec3 mush_col : source_color = vec3(0.3, 0.85, 0.78);
uniform float fg_dark = 0.65;
uniform float rim_in = 1.15;    // (r11, the hole paintings) the surround shown to this many lip radii, gone by rim_out
uniform float rim_out = 1.45;
// (r12) the lair's holes glow green from below (den_boss.png: lime veins down in the pits' dark): veins by a cell
// noise's edges over the painting's own darks inside the lip; COLOR.a < 0.75 marks a lair hole (PlaceSetHole)
uniform float pit_glow = 0.0;
uniform vec3 pit_col : source_color = vec3(0.5, 0.9, 0.28);
// (r12) the lair's gloom (dungeon_floor.gdshader's boss_gloom, the same rule): its pools of light in the middle, the
// ground and its dressing falling dark and cool toward the walls (den_boss.png: its 12-35 band 13 %, cool 18.8 %)
uniform vec3 boss_c = vec3(0.0);
uniform float boss_gloom = 0.0;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float lair_gloom(vec3 p) {
	if (boss_c.z <= 0.0 || boss_gloom <= 0.0) return 0.0;
	float d = distance(p.xz, boss_c.xy);
	return boss_gloom * smoothstep(boss_c.z * 0.3, boss_c.z * 0.75, d) * (1.0 - smoothstep(boss_c.z * 1.2, boss_c.z * 1.5, d));
}
vec3 gloom_col(vec3 c, float g) { return mix(c, vec3(dot(c, vec3(0.3, 0.55, 0.15))) * vec3(0.8, 0.95, 1.25), 0.7 * g) * (1.0 - 0.55 * g); }
vec2 pg_h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float pg_edge(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) {
		vec2 g = vec2(float(x), float(y)), o = pg_h2(i + g);
		float d = length(g + o - f);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
	}
	return d2 - d1;
}

void fragment() {
	vec4 c = texture(paint_tex, UV);
	float lb = dot(textureLod(paint_tex, UV, 3.0).rgb, vec3(0.299, 0.587, 0.114));
	float s = smoothstep(0.1, 0.4, sqrt(max(lb, 0.0)));
	float show = step(1.0, s + COLOR.r + 0.001);
	vec3 col = c.rgb * tint;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(l), col, sat);
	col = mix(col, vec3(l) * shade_tint, shade_k * (1.0 - smoothstep(shade_lo, shade_hi, l)));
	col = gloom_col(col, lair_gloom(wpos));
	ALBEDO = col * gain * mix(1.0, fg_dark, smoothstep(0.82, 1.0, SCREEN_UV.y));   // (r11 judge: the nearest banks fall off, as den_room.png's bottom row)
	EMISSION = col * gain * amb_floor + shade_tint * dark_floor * (1.0 - smoothstep(0.0, 0.05, l));
	// (r10d) the painted glow caps (pale cyan: G and B well over R) give their own light, whatever reaches them
	EMISSION += c.rgb * glow_k * smoothstep(0.05, 0.2, min(c.g, c.b) - c.r);
	if (mush_glow > 0.0) {
		vec3 hb = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod).rgb;
		vec3 hc = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod + 1.0).rgb;
		// cyan AND bright in the mip: the painting's cool dark hollows (B over R, dim) take none
		float hm = max(smoothstep(-0.02, 0.05, min(hb.g, hb.b) - hb.r * 0.9) * smoothstep(0.1, 0.2, dot(hb, vec3(0.299, 0.587, 0.114))),
			0.6 * smoothstep(-0.03, 0.04, min(hc.g, hc.b) - hc.r * 0.9) * smoothstep(0.07, 0.15, dot(hc, vec3(0.299, 0.587, 0.114))));
		EMISSION += mush_col * mush_glow * hm * (1.0 - smoothstep(0.05, 0.2, min(c.g, c.b) - c.r));
	}
	ALPHA = c.a * show * step(0.5, COLOR.g);
#ifdef SET_SOFT
	// (r11) a hole painting's own earth surround fades out past its rim (COLOR.b: half the distance in lip radii)
	ALPHA *= 1.0 - smoothstep(rim_in, rim_out, 2.0 * COLOR.b);
	if (pit_glow > 0.0 && COLOR.a < 0.75) {
		vec2 q = UV * 13.0;
		float e = pg_edge(q + 0.35 * vec2(pg_edge(q * 0.5 + 3.1), pg_edge(q * 0.5 - 7.3)));
		// fissures, not a net: the cell edges lit only where a slow mask says so, the brightest where two meet
		float m = smoothstep(0.25, 0.65, pg_edge(q * 0.33 + 5.3) * 1.6);
		// (r12) a lit core in a wide smoky halo (den_boss.png's veins glow, they are not wire)
		float v = (0.55 * exp(-e * 14.0) + 0.35 * exp(-e * 4.0)) * (0.2 + 0.8 * m) + 0.2 * exp(-pg_edge(q * 2.3 + 1.7) * 12.0) * m;
		float inner = 1.0 - smoothstep(0.55, 0.95, 2.0 * COLOR.b);
		float dark = 1.0 - smoothstep(0.015, 0.09, l);
		float pulse = 0.85 + 0.15 * sin(TIME * 1.3 + q.x * 0.2);
		EMISSION += pit_col * pit_glow * v * inner * dark * pulse;
		EMISSION += pit_col * pit_glow * 0.07 * inner * dark * (0.3 + m);
	}
#endif
#ifndef SET_SOFT
	ALPHA_SCISSOR_THRESHOLD = 0.5;
#endif
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
