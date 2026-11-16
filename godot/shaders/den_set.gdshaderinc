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
uniform float fungus_sat = 1.0;   // (den r14) the painted caps' saturation (DungeonDress.SetMat: --den-fungus-sat)
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
uniform float blood_rust = 0.0;   // (den r15 C) share of the blood pulled to a rust hue (O5 only)
uniform vec3 blood_dir = vec3(1.5, 0.9, 0.45);
uniform float pit_sat = 0.7;   // (den r15 C) pit glow core saturation (judge r14: C90 .18 against .089)
uniform float pit_halo = 0.14;   // (den r15 C) the soft halo (was .07)
uniform float pit_dark = 0.35;   // (den r13 rooms) share of each pit left dark: a slow noise mask on the veins
// (r12) the lair's gloom (dungeon_floor.gdshader's boss_gloom, the same rule): its pools of light in the middle, the
// ground and its dressing falling dark and cool toward the walls (den_boss.png: its 12-35 band 13 %, cool 18.8 %)
uniform vec3 boss_c = vec3(0.0);
uniform float boss_gloom = 0.0;
uniform float hi_roll = 1.0;   // (den r14 corr) the near banks' highlights' scale (1 off)
uniform float bank_gloom = 0.0;   // (den r13 corr) the corridor banks' depth gloom (--den-set-gloom)
uniform float dbg_mod = 0.0;   // (den r15 E, diagnosis: --den-set-dbgmod) each bank module a false colour (COLOR.a), rows behind striped
// (den r15 E, judge r14 item 4) a bank card's cut (COLOR.g's 0.5 contour) wanders at a fine scale and follows the painting's
// masses: the threshold moved by a world value noise (cut_noise: its share of the ramp) and by the painting's local brightness
// (cut_lum: lit roots kept further out, dark gaps cut first), so a border ends in root shapes, not a ruled line. 0, 0: off
uniform float cut_noise = 0.0;
uniform float cut_lum = 0.0;
uniform float cut_scale = 2.2;   // the noise's cycles per metre (two octaves)
uniform vec2 gloom_m = vec2(2.5, 6.5);   // metres into the bank: from, full
// (den r14 objects, item 3) the lit open-floor boulders (sheet O1r): the painting's facets blurred out (rock_lod), a lit warm top
// (COLOR.b: the card's v, 0 at the top) mottled by cell noise and mossed, as den_room.png's round stones. 0: off (banks, other sheets)
uniform float rock_k = 0.0;
uniform float rock_lod = 2.2;
uniform vec3 rock_lit = vec3(0.23, 0.155, 0.085);
uniform vec3 rock_moss = vec3(0.1, 0.13, 0.04);
uniform float rock_moss_k = 0.6;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float lair_gloom(vec3 p) {
	if (boss_c.z <= 0.0 || boss_gloom <= 0.0) return 0.0;
	float d = distance(p.xz, boss_c.xy);
	return boss_gloom * smoothstep(boss_c.z * 0.3, boss_c.z * 0.75, d) * (1.0 - smoothstep(boss_c.z * 1.2, boss_c.z * 1.5, d));
}
vec3 gloom_col(vec3 c, float g) { return mix(c, vec3(dot(c, vec3(0.3, 0.55, 0.15))) * vec3(0.8, 0.95, 1.25), 0.7 * g) * (1.0 - 0.55 * g); }
vec2 pg_h2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return fract(sin(p) * 43758.5453); }
float pg_vn(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(pg_h2(i).x, pg_h2(i + vec2(1.0, 0.0)).x, f.x), mix(pg_h2(i + vec2(0.0, 1.0)).x, pg_h2(i + vec2(1.0, 1.0)).x, f.x), f.y);
}
// (den r14 objects, item 12) branching cracks: the ridge of a domain-warped noise (thin lit line, soft halo), not cell edges
float pg_ridge(vec2 p) {
	vec2 w = vec2(pg_vn(p * 0.7 + 3.1), pg_vn(p * 0.7 - 5.7));
	return 1.0 - abs(2.0 * pg_vn(p + 2.5 * w) - 1.0);
}
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
	if (rock_k > 0.0) {
		vec4 cb = textureLod(paint_tex, UV, rock_lod);
		float lbm = dot(cb.rgb, vec3(0.299, 0.587, 0.114));
		vec2 q = UV * 70.0;
		float m1 = pg_edge(q), m2 = pg_edge(q * 3.1 + 7.0);
		float mot = clamp(0.55 + 0.9 * (0.6 * pg_vn(q * 0.18 + 1.0) + 0.4 * pg_vn(q * 0.55 + 4.0)), 0.55, 1.4);
		float top = smoothstep(0.8, 0.12, COLOR.b);
		float ab = textureLod(paint_tex, UV, 3.0).a;
		float rim = smoothstep(0.35, 0.95, ab);
		// form: lit across the top, falling to a dark belly and a darker rim; cracks as thin dark cell edges
		float form = mix(0.42, 1.2, top) * mix(0.55, 1.0, rim);
		float crack = 1.0 - 0.12 * pg_ridge(q * 0.3 + 2.0) * pg_ridge(q * 0.3 + 2.0);
		vec3 stone = rock_lit * mot * form * crack * clamp(0.75 + lbm * 3.0, 0.8, 1.3);
		float ms = top * rim * smoothstep(0.45, 0.7, 0.7 * pg_vn(q * 0.2 + 9.0) + 0.3 * pg_vn(q * 0.7) + 0.2 * top) * rock_moss_k;
		stone = mix(stone, rock_moss * mot * (0.6 + 0.6 * form), ms);
		vec3 rb = mix(cb.rgb * 0.9, stone, rock_k);
		c = vec4(rb, c.a);
	}
	float lb = dot(textureLod(paint_tex, UV, 3.0).rgb, vec3(0.299, 0.587, 0.114));
	float s = smoothstep(0.1, 0.4, sqrt(max(lb, 0.0)));
	float show = step(1.0, s + COLOR.r + 0.001);
	vec3 col = c.rgb * tint;
	float l = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(l), col, sat);
	col = mix(col, vec3(l) * blood_dir, blood_rust);
	// (den r14 lead, lane E note) the painted fungus' cyan held in its band (C .053-.080 under E's grade, .10-.11 before)
	float cyan = smoothstep(0.05, 0.2, min(c.g, c.b) - c.r);
	col = mix(col, mix(vec3(l), col, fungus_sat), cyan);
	col = mix(col, vec3(l) * shade_tint, shade_k * (1.0 - smoothstep(shade_lo, shade_hi, l)));
	col = gloom_col(col, lair_gloom(wpos));
	// (den r14 corr, item 9) the camera-side banks' lit tops rolled off and warmed (hi_roll 1: off; DungeonDress.SetMat)
	col = mix(col, col * hi_roll * vec3(1.0, 0.93, 0.84), smoothstep(0.05, 0.22, l) * step(hi_roll, 0.999));
#ifndef SET_SOFT
	// (den r13 corr) a corridor bank's roots go dark warm umber as they lie deeper in the bank (COLOR.b: metres in / 10,
	// 0 outside the corridors and on objects): the deep rows' borders and the mound behind them meet in the gloom
	float bg = bank_gloom * smoothstep(gloom_m.x, gloom_m.y, COLOR.b * 10.0);
	col = mix(col, vec3(dot(col, vec3(0.299, 0.587, 0.114))) * vec3(1.0, 0.84, 0.7) * 0.3, bg);
#endif
	ALBEDO =col * gain * mix(1.0, fg_dark, smoothstep(0.82, 1.0, SCREEN_UV.y));   // (r11 judge: the nearest banks fall off, as den_room.png's bottom row)
	EMISSION = col * gain * amb_floor + shade_tint * dark_floor * (1.0 - smoothstep(0.0, 0.05, l));
	// (r10d) the painted glow caps (pale cyan: G and B well over R) give their own light, whatever reaches them
	EMISSION += mix(vec3(dot(c.rgb, vec3(0.299, 0.587, 0.114))), c.rgb, fungus_sat) * glow_k * cyan;
	if (mush_glow > 0.0) {
		vec3 hb = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod).rgb;
		vec3 hc = textureLod(paint_tex, UV - vec2(0.0, mush_drop), mush_lod + 1.0).rgb;
		// cyan AND bright in the mip: the painting's cool dark hollows (B over R, dim) take none
		float hm = max(smoothstep(-0.02, 0.05, min(hb.g, hb.b) - hb.r * 0.9) * smoothstep(0.1, 0.2, dot(hb, vec3(0.299, 0.587, 0.114))),
			0.6 * smoothstep(-0.03, 0.04, min(hc.g, hc.b) - hc.r * 0.9) * smoothstep(0.07, 0.15, dot(hc, vec3(0.299, 0.587, 0.114))));
		EMISSION += mush_col * mush_glow * hm * (1.0 - smoothstep(0.05, 0.2, min(c.g, c.b) - c.r));
	}
	float cut_t = 0.5;
#ifndef SET_SOFT
	if (cut_noise > 0.0 || cut_lum > 0.0) {
		vec2 cq = wpos.xz * cut_scale;
		float fn = 0.62 * pg_vn(cq + 17.3) + 0.38 * pg_vn(cq * 2.7 - 4.1);
		cut_t = clamp(0.5 + cut_noise * (fn - 0.5) * 2.0 + cut_lum * (0.5 - s), 0.03, 0.97);
		// the fades (a run's ends, the image's own cut: COLOR.r) gone before the card's geometric end: at COLOR.r 0 the bright
		// masses still showed, cut by the card's last column (s23 corridor x 1490-1500, a module's end ruled for 260 px)
		show = step(1.0, 0.8 * s + 1.25 * COLOR.r + 0.5 * cut_noise * (fn - 0.5));
	}
#endif
	ALPHA = c.a * show * step(cut_t, COLOR.g);
#ifndef SET_SOFT
	if (dbg_mod > 0.0) {
		vec3 hc = clamp(abs(fract(fract(COLOR.a * 2.0) + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
		float stripe = COLOR.a >= 0.5 ? step(0.5, fract((FRAGCOORD.x + FRAGCOORD.y) / 14.0)) : 1.0;
		vec3 dc = hc * (0.2 + 0.8 * clamp(dot(c.rgb, vec3(0.299, 0.587, 0.114)) * 2.5, 0.0, 1.0)) * mix(0.3, 1.0, stripe) * mix(0.5, 1.0, step(0.999, COLOR.r));
		ALBEDO = dc * 0.1;
		EMISSION = dc * dbg_mod;
	}
#endif
#ifdef SET_SOFT
	// (r11) a hole painting's own earth surround fades out past its rim (COLOR.b: half the distance in lip radii)
	ALPHA *= 1.0 - smoothstep(rim_in, rim_out, 2.0 * COLOR.b);
	if (pit_glow > 0.0 && COLOR.a < 0.75) {
		vec2 q = UV * 13.0;
		float m = smoothstep(0.25, 0.65, pg_edge(q * 0.33 + 5.3) * 1.6);
		float r1 = pg_ridge(q * 0.9), r2 = pg_ridge(q * 2.1 + 4.0);
		// (den r14 objects, item 12) a hairline core, a soft halo, a second finer set of branches on the slow mask
		float v = 1.0 * smoothstep(0.93, 0.99, r1) + 0.5 * pow(r1, 8.0) + (0.75 * smoothstep(0.945, 0.99, r2) + 0.22 * pow(r2, 8.0)) * (0.4 + 0.6 * m);
		float inner = 1.0 - smoothstep(0.55, 1.1, 2.0 * COLOR.b);
		// (den r13 rooms) clusters: veins only where the slow cell mask clears its threshold (about pit_dark of the area stays dark)
		float pm = smoothstep(0.0, 0.06, pg_edge(q * 0.16 + 11.3) - pit_dark * 0.55);
		inner *= pm;
		float dark = 1.0 - smoothstep(0.015, 0.09, l);
		float pulse = 0.85 + 0.15 * sin(TIME * 1.3 + q.x * 0.2);
		vec3 pc = mix(vec3(dot(pit_col, vec3(0.299, 0.587, 0.114))), pit_col, pit_sat);
		EMISSION += pc * pit_glow * v * inner * dark * pulse;
		EMISSION += pc * pit_glow * pit_halo * inner * dark * (0.3 + m);
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
