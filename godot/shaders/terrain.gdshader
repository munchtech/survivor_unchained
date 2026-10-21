// The ground. Seven materials of our own (tools/assets/env_ground.py, one
// array layer each: meadow, forest floor, trodden earth, mud, setts, rock,
// burnt earth); the zone's paint says how much of each, over ramps about a
// metre wide, and then their heights decide, so the higher material pushes
// through (stones through earth, grass clumps over a road's edge). Only the
// four strongest are sampled; the two strongest are anti-tiled (Quilez:
// a random offset per noise cell, blended on height). The setts are their
// own 8 m tile at 2K, one of three variants per tile (their outer stones
// shared), never blended. Over it all: a macro colour and value every
// 30-60 m, the road (GroundPaint.cs: its made surface, ruts dipped through
// the normal), and wet hollows, ruts, gutters and puddles.
// Also draws the endgame's generated maps (Maps/MapGen: no road mask).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://shaders/flare_world.gdshaderinc"

#define NL 7
#define ROCK 5
#define SETTS 4

uniform sampler2D noise_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
// GroundPaint.cs: R road surface (0.8; its centre strip to 1), G ruts, B wet, A puddles.
uniform sampler2D paint_mask : filter_linear_mipmap, repeat_disable;
uniform float mask_texel = 0.127;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_nor : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_arh : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray s_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray s_nor : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray s_arh : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float g_scale[NL];
uniform float zone_size = 290.0;
uniform float leaves = 0.3;
uniform vec3 blight_glow : source_color = vec3(0.55, 1.0, 0.35);
// How far the blight has drawn back (the Verge once the poison stops): the
// paint's blight at 1 - heal * 0.85, as the web game paints it.
uniform float heal = 0.0;
// The blend: heights' weight against the paint's, and how deep the overlap.
uniform float h_amp = 1.0;
uniform float h_depth = 0.08;
// The paint's ramps: steeper than 1 narrows the edge.
uniform float edge_k = 1.6;
uniform float macro_amt = 1.0;
uniform float rut_depth = 0.035;
uniform float wet_amt = 1.0;
// 1: show the road mask (R road, G ruts, B wet) as the colour; 2: the paint; 3: the frost's exposure (R sky, G sun);
// 4: the frost (red where it lies, blue where not: measure_b.py's mask).
// 19-24 (E3 E, measure_e.py): open setts facing +x, +z; dirt over 0.1, over 0.9; the puddles' wet rim; open setts.
uniform int debug_view = 0;
// Hoar frost (look bible 1f, "The trick" 5): GroundPaint's exposure (R the open sky, G the sun at the thaw's key),
// the preset's amount and thaw (Atmosphere: x amount, y thaw), the rime's value, and how far down the heights it reaches.
uniform sampler2D expo_tex : filter_linear, repeat_disable, hint_default_white;
global uniform vec4 ground_frost;
// E6: the river (Water.cs): the water's height (x; w 1 when the zone has one), and its bed and bank (water.json "look"
// "bed": x pebbles 0-1, y silt 0-1, z m above the water the bank is wet, w how dark it is), the silt's colour.
global uniform vec4 water_level;
global uniform vec4 water_bed;
global uniform vec4 water_silt;
// The rime: the ground under it lifted by frost_tone, greyed and cooled, never past frost_cap (frost is never
// the brightest thing at night: look bible 1c).
uniform float frost_tone = 1.7;
uniform float frost_cap = 0.1;
uniform float frost_reach = 0.5;
// The fires' warmth: no frost within z metres of (x, y); radius 0 is unused.
uniform vec4 warm_at[4];
// The meadow's three scales (look bible 1f): the land's lie and patches over 10-40 m, clumps and bare
// ground over 1-5 m (0: as A left it).
uniform float meadow_amt = 1.0;
// Judge 1's fix round (E3 C). GroundPaint's Near: R the distance to a wall's base, G to anything standing, B the setts'
// wear lane, A the distance into the setts from their edge (each /2 m).
uniform sampler2D near_tex : filter_linear, repeat_disable, hint_default_black;
// The ruts: the albedo at a full rut's core (GroundPaint gives G 0.42-1, so plus or minus 40%); the crown between them lighter.
uniform float rut_dark = 0.45;
uniform float crown_lift = 0.12;
// The setts: grime near what stands (0.6-1 m), the gutter's width at a wall's base, the wear lane's lift, the share of
// edge stones dropped, the weeds in the joints by the walls.
uniform float grime = 0.08;
uniform float gutter_w = 0.4;
// The setts' shoulders lit less (judge 1, E3 fix 6: the bevel rims read as mosaic; halve their highlight).
uniform float setts_bump = 0.32;
uniform float night_dew = 0.35;
uniform float pud_dark = 0.45;
uniform float night_spec = 0.12;
uniform float lane_lift = 0.32;
uniform float edge_drop = 0.6;
uniform float weeds = 1.0;
// The meadow's value over 4-10 m (plus or minus this).
uniform float meadow_val = 0.13;
// Frost as speckle on the tops (1: crisp; 0: B's soft ramp), and the dawn's stricter threshold (tops only).
uniform float frost_crisp = 1.0;
uniform float frost_dawn = 0.12;
// The rime on bare earth and stone (the road read as snow by moonlight at 0.5: judge 1, E3 fix 10).
uniform float frost_soft = 0.3;
// Judge 2's round (E3 E). The road's verge: the heights' overlap widened where the dirt meets the grass by a road, so the
// edge ramps over 0.2 m or more (no crisp noise threshold).
uniform float verge_soft = 0.8;
// The ruts darker in the sun (GroundPaint's sun on the ground): at a low sun the road's own relief darkened it, not the ruts.
uniform float rut_sun = 0.35;
// Puddles: the wet rim's darkness, and the sky's reflection broken (no ReflectionProbe): the open sky (canopy, eaves),
// the sun on the ground (darker in the shade), noise; mirror_amt scales it all, mirror_rut the ruts' own (0: a dark wet patch).
uniform float pud_rim = 0.45;
uniform float mirror_amt = 1.0;
uniform float mirror_rut = 1.0;
// The meadow by night: frost and value from the tufts' density (grass.gdshader's clumps and bare patches), bare soil dark.
uniform float night_tuft = 1.0;
// ... and its value over 4-10 m by night, set after the rime (the frost's cap levelled the day's meadow_val into felt).
uniform float night_val = 0.7;
// Judge 3's setts restage (E3 F): the street's mud by what stands (the joints fill and the stones' edges are buried, by
// the tile's own height; out to setts_reach metres from the well, the stalls, the posts, less far from a wall), stones
// sunk and missing at their foot, moss in the shaded joints. 0 turns each off.
uniform float setts_mud = 1.0;
uniform float setts_reach = 1.5;
uniform float setts_moss = 1.0;
// E3 G: the mud collar at the foot of what stands (metres), and the mud's value.
uniform float setts_collar = 0.45;
uniform float mud_tone = 1.0;
uniform float mud_sat = 1.5;
// ... and its specular (the sky's sheen greyed the dark mud).
uniform float mud_spec = 0.1;
// Style r2 (--setts-paint): the street's mud painted, an opaque matte darker browner earth (a calm sheet, no grain), flat,
// moss along its edges. 0 is the mud as it was.
uniform float mud_paint = 0.0;

varying vec3 w_pos;
varying vec3 w_nrm;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

// (Derivatives from the world position's, taken before any branch.)
vec2 g_uv(int i, vec3 p, vec3 n, vec3 px, vec3 py, out mat3 tbn, out vec2 dx, out vec2 dy) {
	if (i == ROCK) {
		// On the face: across it horizontally, and up it.
		vec2 h = normalize(n.xz + vec2(1e-4, 0.0));
		vec3 t = vec3(-h.y, 0.0, h.x);
		tbn = mat3(t, vec3(0.0, -1.0, 0.0), n);
		vec2 a = vec2(-h.y, h.x);
		dx = vec2(dot(px.xz, a), px.y) * g_scale[i];
		dy = vec2(dot(py.xz, a), py.y) * g_scale[i];
		return vec2(dot(p.xz, a), p.y) * g_scale[i];
	}
	// Laid flat: u along +x, the image's top toward -z.
	vec3 t = normalize(vec3(1.0, 0.0, 0.0) - n * n.x);
	tbn = mat3(t, cross(n, t), n);
	dx = px.xz * g_scale[i];
	dy = py.xz * g_scale[i];
	return p.xz * g_scale[i];
}

float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

// One material's three maps at uv (layer `ly`; the setts from their own arrays).
void fetch3(int k, vec2 uv, float ly, vec2 dx, vec2 dy, out vec4 a, out vec4 n, out vec4 h) {
	if (k == SETTS) {
		a = textureGrad(s_alb, vec3(uv, ly), dx, dy);
		n = textureGrad(s_nor, vec3(uv, ly), dx, dy);
		h = textureGrad(s_arh, vec3(uv, ly), dx, dy);
	} else {
		a = textureGrad(g_alb, vec3(uv, ly), dx, dy);
		n = textureGrad(g_nor, vec3(uv, ly), dx, dy);
		h = textureGrad(g_arh, vec3(uv, ly), dx, dy);
	}
}

void fragment() {
	vec2 w = w_pos.xz;
	vec4 nL = texture(noise_tex, w * 0.011);           // ~90 m
	vec4 nC = texture(noise_tex, w * 0.0213 + 0.13);   // ~47 m: the macro
	vec4 nM = texture(noise_tex, w * 0.061 + 0.37);    // ~16 m
	vec4 nF = texture(noise_tex, w * 0.29 + 0.71);     // ~3.4 m
	vec2 zuv = (w + zone_size * 0.5) / zone_size;
	vec4 sp = texture(splat, zuv);
	vec4 pm = texture(paint_mask, zuv);
	vec4 ex4 = texture(expo_tex, zuv);
	vec4 nr = texture(near_tex, zuv);
	sp.b *= 1.0 - heal * 0.85;
	vec3 n_geo = normalize(w_nrm);
	vec3 p_dx = dFdx(w_pos), p_dy = dFdy(w_pos);

	// How much of each material the paint asks for: its own ramps (about a
	// metre), nudged by noise, never stepped.
	// (Fingers of dirt into the grass at a clearing's edge: 2-3 every 5 m, 0.5-1 m long; judge 1, E3 fix 4.)
	float fing = smoothstep(0.5, 0.8, texture(noise_tex, w * 0.105 + 0.21).g) * (1.0 - smoothstep(0.3, 0.7, pm.r));
	float wd = clamp((sp.r - 0.5) * edge_k + 0.5 + (nM.b - 0.5) * 0.3 + (nF.g - 0.5) * 0.12 + fing * 0.45 * smoothstep(0.03, 0.25, sp.r), 0.0, 1.0) * step(0.02, sp.r);
	float ws = clamp((sp.g - 0.5) * edge_k + 0.5 + (nM.g - 0.5) * 0.25, 0.0, 1.0) * step(0.02, sp.g);
	// The setts' ragged edge (judge 1, E3 fix 5): within a metre of their edge (wobbling, so no straight run), whole
	// stones dropped or sunk, dirt filling where they went, and the paint's own edge pushed in and out.
	float sd_in = nr.a * 2.0 + (nM.g - 0.5) * 0.7 + (nF.r - 0.5) * 0.5;
	float s_band = (1.0 - smoothstep(0.3, 1.15, sd_in)) * step(0.02, sp.g);   // (0.5-1 m: judge 1, E3 fix 5)
	ws = clamp(ws + (nF.g - 0.5) * 0.6 * s_band, 0.0, 1.0);
	wd = max(wd, s_band * ws * 0.9);
	float wb = clamp((sp.b - 0.5) * edge_k + 0.5 + (nM.r - 0.5) * 0.4, 0.0, 1.0) * step(0.02, sp.b);
	float wm = clamp((sp.a - 0.5) * edge_k + 0.5 + (nM.g - 0.5) * 0.3, 0.0, 1.0) * step(0.02, sp.a);
	// The meadow's bare patches (1-3 m, in loose drifts): trodden earth through the grass, as the grass leaves them.
	// (noise_tex's channels are value noise of base period 4, 8, 16 and 64 a tile: nM's R about 4 m across, G 2 m, B 1 m.)
	float bare = smoothstep(0.62, 0.76, nM.b * 0.45 + nC.b * 0.55) * smoothstep(0.45, 0.68, nL.b) * meadow_amt;
	wd = max(wd, bare * (1.0 - step(0.02, sp.g)));
	// (Their rims blended over a wider overlap, so a patch is not stamped: judge 1, E3 fix 8, 0.3 m or more of feather.)
	float hdp = h_depth + 0.22 * clamp(bare * (1.0 - bare) * 4.0, 0.0, 1.0);
	// The road's centre strip: sparse grass between the ruts.
	float cen = smoothstep(0.84, 0.96, pm.r);
	wd *= 1.0 - cen * 0.45;
	// (Where trodden earth meets grass the heights decide less, so the edge ramps instead of cutting on the maps' grain.)
	float wedge = clamp(max(wd * (1.0 - wd), wm * (1.0 - wm)) * 4.0, 0.0, 1.0) * (1.0 - step(0.02, sp.g));
	hdp += verge_soft * wedge;
	float slope = 1.0 - clamp(n_geo.y, 0.0, 1.0);
	float wr = smoothstep(0.3, 0.55, slope + (nM.b - 0.5) * 0.15);
	float leafy = smoothstep(0.38, 0.82, nL.g * 0.7 + nM.a * 0.3 + leaves - 0.5);
	// Needles and leaves under every crown (GroundPaint's sky: 2-4 m round a trunk), ragged at their rim.
	leafy = max(leafy, smoothstep(0.82, 0.42, ex4.r + (nF.b - 0.5) * 0.25));
	float gw[NL] = float[](1.0 - leafy, leafy, 0.0, 0.0, 0.0, 0.0, 0.0);
	// Each overlay takes its share from everything under it.
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wd;
	gw[2] += wd;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wm;
	gw[3] += wm;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - ws;
	gw[SETTS] += ws;
	// The gutter: a band of mud 0.3-0.5 m wide at a wall's foot, over the setts too, broken here and there.
	float gut = (1.0 - smoothstep(gutter_w - 0.07, gutter_w + 0.07, nr.r * 2.0 + (nF.g - 0.5) * 0.14)) * smoothstep(0.12, 0.22, nM.r * 0.6 + nF.b * 0.4) * step(nr.r, 0.99);
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - gut;
	gw[3] += gut;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wb;
	gw[6] += wb;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wr;
	gw[ROCK] += wr;

	// The four strongest, strongest first.
	int id[4] = int[](0, 0, 0, 0);
	float wv[4] = float[](-1.0, -1.0, -1.0, -1.0);
	for (int k = 0; k < NL; k++) {
		float v = gw[k];
		int kk = k;
		for (int s = 0; s < 4; s++) {
			if (v > wv[s]) { float tv = wv[s]; wv[s] = v; v = tv; int tk = id[s]; id[s] = kk; kk = tk; }
		}
	}

	// Anti-tiling: a cell of slow noise picks each copy's offset.
	float at_k = texture(noise_tex, w * 0.043 + 0.51).r * 8.0;
	float at_i = floor(at_k), at_f = fract(at_k);
	vec2 off_a = sin(vec2(3.0, 7.0) * at_i), off_b = sin(vec2(3.0, 7.0) * (at_i + 1.0));
	// The setts: one of three variants per 8 m tile.
	vec2 st_uv = w * g_scale[SETTS];
	float st_ly = floor(hash12(floor(st_uv) + 17.0) * 2.999);

	float st_sid = 0.5;
	vec4 A[4], Nn[4], H[4];
	mat3 T[4];
	float hs[4];
	float best = -1.0;
	float dbg_drop = 0.0;
	// The strongest material's own place on its map, for the frost's local tops.
	vec3 uv0 = vec3(0.0); vec2 dx0 = vec2(0.0), dy0 = vec2(0.0); int k0 = 0;
	for (int s = 0; s < 4; s++) {
		hs[s] = -9.0;
		A[s] = vec4(0.0); Nn[s] = vec4(0.5, 0.5, 1.0, 1.0); H[s] = vec4(1.0, 1.0, 0.0, 1.0);
		T[s] = mat3(1.0);
		if (wv[s] < 0.004) continue;
		int k = id[s];
		mat3 tbn;
		vec2 dx, dy;
		vec2 uv = g_uv(k, w_pos, n_geo, p_dx, p_dy, tbn, dx, dy);
		T[s] = tbn;
		float ly = float(k);
		if (k == SETTS) { uv = st_uv; ly = st_ly; }
		vec4 a0, n0, h0;
		fetch3(k, k == SETTS ? uv : uv + off_a, ly, dx, dy, a0, n0, h0);
		float drop = 0.0;
		if (k == SETTS) {
			// (The setts' normal carries each stone's own random in B: env_ground.py.)
			float sid = n0.b;
			st_sid = sid;
			vec2 nxy = (n0.rg * 2.0 - 1.0) * setts_bump;
			n0.rg = nxy * 0.5 + 0.5;
			n0.b = sqrt(max(1.0 - dot(nxy, nxy), 0.0)) * 0.5 + 0.5;
			drop = step(sid, 0.1 + edge_drop * s_band) * s_band;
		}
		if (s < 2 && k != SETTS) {
			vec4 a1, n1, h1;
			fetch3(k, uv + off_b, ly, dx, dy, a1, n1, h1);
			float b = smoothstep(0.2, 0.8, at_f + (h1.b - h0.b) * 0.5);
			a0 = mix(a0, a1, b); n0 = mix(n0, n1, b); h0 = mix(h0, h1, b);
		}
		A[s] = a0; Nn[s] = n0; H[s] = h0;
		if (s == 0) { uv0 = vec3(k == SETTS ? uv : uv + off_a, ly); dx0 = dx; dy0 = dy; k0 = k; }
		hs[s] = wv[s] + h0.b * h_amp * (1.0 - wedge * step(0.01, verge_soft)) - drop * 1.2;
		dbg_drop = max(dbg_drop, drop);
		best = max(best, hs[s]);
	}
	// Heights decide at the edges: the taller material shows.
	float bw[4];
	float tot = 0.0;
	for (int s = 0; s < 4; s++) {
		bw[s] = hs[s] < -1.0 ? 0.0 : max(hs[s] - best + hdp, 0.0);
		tot += bw[s];
	}
	vec3 albedo = vec3(0.0);
	vec3 n_w = vec3(0.0);
	float rough = 0.0, ao = 0.0, hgt = 0.0;
	float w_mud = 0.0, w_soft = 0.0, w_meadow = 0.0, w_blight = 0.0, w_setts = 0.0;
	for (int s = 0; s < 4; s++) {
		float wk = bw[s] / tot;
		if (wk <= 0.0) continue;
		int k = id[s];
		albedo += A[s].rgb * wk;
		vec3 tn = Nn[s].xyz * 2.0 - 1.0;
		n_w += T[s] * tn * wk;
		rough += H[s].g * wk;
		ao += H[s].r * wk;
		hgt += H[s].b * wk;
		if (k == 3) w_mud += wk;
		if (k == 2 || k == 3 || k == SETTS) w_soft += wk;
		if (k == 0 || k == 1) w_meadow += wk;
		if (k == 6) w_blight += wk;
		if (k == SETTS) w_setts += wk;
	}
	n_w = normalize(n_w);

	// Macro: colour and value drift every 30-60 m, so a field is not one colour.
	float mv = mix(1.0, 0.8 + 0.3 * nC.r + 0.08 * (nL.r - 0.5), macro_amt);
	albedo *= mv;
	// The meadow over 10-40 m: damp lows greener and darker, rises and open patches gone to straw, worn
	// stretches browner; then clumps over a metre or two, darker hearts and lighter crowns.
	float low = ex4.b * 2.0 - 1.0;
	float lush = clamp(smoothstep(0.08, 0.6, low + (nM.r - 0.5) * 0.3), 0.0, 1.0);
	float dry = smoothstep(0.46, 0.72, nL.g * 0.5 + nC.r * 0.3 + nM.r * 0.2 + max(-low, 0.0) * 0.45) * (1.0 - lush);
	float brown = smoothstep(0.55, 0.78, nL.b * 0.5 + nC.g * 0.5) * (1.0 - lush) * (1.0 - dry * 0.6);
	float clump = nM.r * 0.45 + nM.g * 0.35 + nF.r * 0.2;
	// The tufts' density over 2-5 m, as grass.gdshader thins them (bare patches, clumps): 0 bare soil, 1 the thickest.
	float tuft = (1.0 - bare) * smoothstep(0.32, 0.68, clump);
	float night0 = ground_frost.x * (1.0 - clamp(ground_frost.y * 4.0, 0.0, 1.0));
	float nt = night0 * night_tuft * w_meadow;
	vec3 mm = albedo;
	mm = mix(mm, mm * vec3(1.36, 1.14, 0.66) * 1.22, dry);
	mm = mix(mm, mm * vec3(1.1, 0.93, 0.78) * 0.9, brown * 0.8);
	mm = mix(mm, mm * vec3(0.76, 1.0, 0.78) * 0.68, lush);
	mm *= (0.64 + 0.72 * clump) * mix(vec3(1.12, 1.0, 0.76), vec3(0.88, 1.04, 0.9), smoothstep(0.3, 0.7, clump));
	vec3 straw = albedo * vec3(1.07, 1.03, 0.86);
	vec3 green = albedo * vec3(0.95, 1.03, 0.94);
	vec3 old = mix(green, straw, smoothstep(0.3, 0.7, nC.g));
	// Its value over 4-10 m (judge 1, E3 fix 8: the shaded meadow read as felt).
	mm *= 1.0 + meadow_val * 2.0 * ((nC.g - 0.5) * 1.2 + (nL.b - 0.5) * 0.8);
	albedo = mix(albedo, mix(old, mm, meadow_amt), w_meadow * mix(0.6, 1.0, meadow_amt) * macro_amt);
	// By night the bare soil between the tufts dark, the thick clumps lighter (judge 2, E3 fix 4: the moonlit meadow read as felt).
	albedo *= mix(1.0, mix(0.8, 1.06, tuft), nt);
	// Setts: the world's own tone over the tile, so no two copies match.
	albedo *= 1.0 + (nF.r - 0.5) * 0.22 * w_setts;
	// Grime within 0.6-1 m of what stands (a trace now: the mud below carries it); a wear lane down the ways; weeds and
	// moss in the joints by the walls.
	float near_any = 1.0 - smoothstep(0.6, 1.0, nr.g * 2.0 + (nF.b - 0.5) * 0.3);
	albedo *= 1.0 - grime * near_any * w_setts;
	albedo *= 1.0 + lane_lift * nr.b * w_setts * (1.0 - near_any);
	// The street's mud (judge 3, E3 F: grime as mud, not darker stone). The tile's height: joints about 0.1, a stone's
	// edge 0.3, its top 0.6-0.95. Near what stands the mud's level rises, ragged, so the joints widen and fill and the
	// stones' edges (their low side first, by their tilt) are buried; some stones sunk (lower, darker, more buried), a
	// few at the very foot gone (mud where they were). Not so far from a wall as from the well or a stall.
	vec4 rg4 = texture(noise_tex, w * 1.7 + 0.43);
	float rgm = rg4.r;
	float hgt0 = hgt;
	float wallish = step(nr.r - nr.g, 0.08);
	float dn = nr.g * 2.0 + (nF.b - 0.5) * 0.4 + (nM.a - 0.5) * 0.3 + (rg4.g - 0.5) * 0.6;
	float mud_g = (1.0 - smoothstep(0.0, setts_reach * mix(1.0, 0.65, wallish), dn)) * w_setts * setts_mud;
	// (E3 G: the collar at the foot of all that stands, 0.3-0.6 m, broken by the 0.6 m noise: stones there buried to their
	// tops, sunk or gone. The tile's height is read a mip or two down at the play camera, so the joints' 0.1 reads
	// nearer 0.25 and the levels allow for it, with the edge widened by the height's own footprint.)
	float col_d = nr.g * 2.0 + (rg4.g - 0.5) * 0.45 + (rg4.b - 0.5) * 0.25;
	float collar = (1.0 - smoothstep(setts_collar * 0.6, setts_collar * 1.2, col_d)) * w_setts * setts_mud * mix(1.0, 0.5, wallish);
	float lost = max(step(st_sid, 0.1 + 0.2 * mud_g * mud_g) * step(0.3, mud_g), step(st_sid, 0.35) * step(0.5, collar));
	float sunk = max(step(st_sid, 0.1 + 0.4 * mud_g) * step(0.1, mud_g), step(st_sid, 0.6) * step(0.3, collar)) * (1.0 - lost);
	float lvl = 0.2 + mud_g * mud_g * (0.2 + (rgm - 0.5) * 0.24) + mud_g * 0.06 + sunk * 0.18 + collar * (0.5 + (rg4.a - 0.5) * 0.3);
	float hfw = fwidth(hgt) * 0.5;
	float mud_c = max(1.0 - smoothstep(lvl - 0.04 - hfw, lvl + 0.03 + hfw, hgt), lost) * step(0.001, mud_g + collar);
	// (E3 G: mud, not dark stone: about 30% under the stones' value, hue about 30 degrees and well over the stones'
	// saturation (the town's grade greys the setts' own warmth by a third); wetter and darker in the joints and at the
	// collar, a paler dried crust where it rides over a stone. sRGB about 0.26, 0.185, 0.11.)
	float mdep = clamp((lvl - hgt) * 5.0, 0.0, 1.0);
	vec3 mud_col = mix(vec3(0.048, 0.034, 0.011), vec3(0.047, 0.029, 0.011), mud_paint) * mud_tone * mix(1.08, 0.78, max(mdep, collar * 0.6)) * (0.85 + 0.3 * rgm) * mv;
	// (A grain of its own at 5-20 cm: a flat sheet read as a decal. Not the tile's, whose stones showed through.)
	vec2 mgr = texture(noise_tex, w * 5.3 + 0.17).rg;
	mud_col *= mix(0.78 + 0.3 * mgr.r + 0.14 * mgr.g, 0.93 + 0.1 * mgr.r, mud_paint);
	mud_col = max(mix(vec3(dot(mud_col, vec3(0.2126, 0.7152, 0.0722))), mud_col, mud_sat), 0.0);
	albedo *= 1.0 - 0.14 * sunk * w_setts;
	// Worn tops by the well and the stalls: a little lighter.
	albedo *= 1.0 + 0.07 * mud_g * (1.0 - sunk) * smoothstep(0.55, 0.8, hgt);
	// A film of mud over the tops that poke through the collar.
	albedo = mix(albedo, albedo * vec3(0.92, 0.85, 0.74), collar * (1.0 - mud_c) * 0.6);
	albedo = mix(albedo, mud_col, mud_c);
	rough = mix(rough, mix(mix(0.85, 0.65, mdep * collar), 0.97, mud_paint), mud_c);
	n_w = normalize(mix(n_w, n_geo, mud_c * mix(0.85, 1.0, mud_paint)));
	hgt = mix(hgt, min(hgt, lvl * 0.8), mud_c);
	float dbg_mud_c = step(0.5, mud_c) * w_setts;
	float mud_s = mud_c * w_setts;
	float dbg_collar = step(0.5, collar);
	float joint = w_setts * (1.0 - smoothstep(0.14, 0.26, hgt));
	// Moss in the shaded joints, in patches, out of the wear lane.
	float moss_k = joint * (1.0 - ex4.g) * smoothstep(0.45, 0.7, rgm * 0.6 + nF.a * 0.4) * (1.0 - nr.b) * setts_moss * (1.0 - mud_c);
	albedo = mix(albedo, vec3(0.022, 0.031, 0.010) * mv, moss_k * 0.75);
	// (Painted: moss along the mud's edge, in its joints and its rim, in patches.)
	if (mud_paint > 0.0) {
		float mg = mud_g + collar * 0.7;
		float rim = smoothstep(0.04, 0.3, mg) * (1.0 - smoothstep(0.35, 0.8, mg));
		float mk = rim * smoothstep(0.4, 0.62, rg4.b * 0.7 + nF.a * 0.3) * (1.0 - smoothstep(0.16, 0.34, hgt)) * (1.0 - nr.b * 0.7);
		albedo = mix(albedo, vec3(0.030, 0.042, 0.012) * mv * (0.8 + 0.4 * mgr.g), mk * 0.8 * mud_paint * setts_moss);
	}
	// (Out to 0.9 m: the gutter takes the wall's first 0.3-0.5 m, so the weeds live in the joints at its lip.)
	float wsel = smoothstep(0.5, 0.62, texture(noise_tex, w * 0.9 + 0.2).g) * (1.0 - smoothstep(0.75, 1.0, nr.r * 2.0));
	albedo = mix(albedo, vec3(0.085, 0.11, 0.045) * (0.8 + 0.4 * nF.a), joint * wsel * weeds);

	// The road: its made surface packed a little smoother; the ruts darker,
	// wetter, smoother, dipped through the normal.
	float road = smoothstep(0.4, 0.8, pm.r) * w_soft;
	rough -= road * 0.03;
	float rut = pm.g;
	// Packed a little smoother by the wheels (judge 1: much smoother lit them brighter than the road at a low sun).
	n_w = normalize(mix(n_w, n_geo, rut * w_soft * 0.1));
	if (rut > 0.003) {
		vec2 e = vec2(mask_texel / zone_size, 0.0);
		float gx = textureLod(paint_mask, zuv + e.xy, 0.0).g - textureLod(paint_mask, zuv - e.xy, 0.0).g;
		float gz = textureLod(paint_mask, zuv + e.yx, 0.0).g - textureLod(paint_mask, zuv - e.yx, 0.0).g;
		// (Shallower in the sun: at a low sun the wall facing it lit the rut lighter than the road; judge 2, E3 fix 5.)
		vec2 dh = -vec2(gx, gz) / (2.0 * mask_texel) * rut_depth * (1.0 - 0.7 * ex4.g);
		n_w = normalize(n_w + vec3(-dh.x, 0.0, -dh.y) * w_soft);
	}

	// Wet: hollows, ruts, gutters. Damp grass darkens less than earth.
	float wet = clamp(pm.b * wet_amt * (1.0 - w_meadow * 0.6), 0.0, 1.0);
	wet *= smoothstep(0.25, 0.55, 1.0 - hgt * 0.6 + (nF.a - 0.5) * 0.4);
	// The ruts (judge 1, E3 fix 1): two damp tracks, a core 0.3 m wide and a feathered shoulder, their depth and
	// darkness wandering; the crown between them a little lighter. (The dip in the normal kept slight: at a low
	// sun one wall lit and one dark read as a thin line, not a track.)
	float rut_w = rut * w_soft;
	albedo *= mix(1.0, rut_dark, rut_w);
	albedo *= 1.0 - rut_sun * rut_w * ex4.g;
	albedo *= 1.0 + crown_lift * smoothstep(0.82, 0.95, pm.r) * w_soft;
	albedo *= mix(1.0, 0.64, wet);
	rough = mix(rough, 0.72, wet * 0.6);
	// (Not smoother: at the dawn's low sun a smoother rut took a sheen and read lighter than the road.)
	rough = mix(rough, 0.8, rut_w * 0.5);
	// Puddles: standing water in the deepest ruts and low corners, on earth, mud and stone.
	// (The noise only ragged a pool's rim: wider, it broke the gutters' damp into a rash of 0.2 m specks.)
	// (Judge 2, E3 fix 1: ragged at 0.1-0.4 m, no ellipse or capsule; the setts' stone tops poke through in town.)
	// (Fetched only near water: a fetch everywhere cost 0.2 ms at 1440p.)
	float pmb = 0.0, rag = 0.5;
	if (w_soft * wet_amt > 0.01) pmb = textureLod(paint_mask, zuv, 1.5).a;
	if (pmb > 0.04 || pm.a > 0.04) rag = textureGrad(noise_tex, w * 1.3 + 0.9, p_dx.xz * 1.3, p_dy.xz * 1.3).r;
	float pf = pm.a + (nF.b - 0.5) * 0.24 + (nM.a - 0.5) * 0.12 + (rag - 0.5) * 0.3 - hgt * mix(0.25, 0.7, w_setts);
	float pud = smoothstep(0.62, 0.68, pf) * w_soft * wet_amt;
	// A wet rim 0.1-0.2 m wide, a quarter darker than the dry ground.
	float prim = smoothstep(mix(0.14, 0.24, w_setts), mix(0.34, 0.42, w_setts), pmb + (nF.b - 0.5) * 0.15) * (1.0 - pud) * w_soft * wet_amt;
	albedo *= 1.0 - pud_rim * prim;
	rough = mix(rough, 0.6, prim * 0.5);
	// (Standing water: dark, and smooth enough to hold the sky; judge 1, E3 fix 7.)
	albedo = mix(albedo, albedo * pud_dark, pud);
	// The sky in it broken (judge 2): none under a crown or the eaves, less in the shade, broken by ripples and scum.
	float brk = smoothstep(0.25, 0.75, nF.g * 0.6 + nF.b * 0.4);
	float mirror = mirror_amt * mix(mirror_rut, 1.0, max(w_setts, 1.0 - step(0.05, rut))) * smoothstep(0.35, 0.9, ex4.r) * mix(0.45, 1.0, ex4.g) * mix(0.15, 1.0, brk);
	rough = mix(rough, mix(0.32, 0.03, brk * step(0.01, mirror)), pud);
	n_w = normalize(mix(n_w, normalize(n_geo + vec3(nF.a - 0.5, 0.0, rag - 0.5) * 0.15), pud));

	// Dew by night (judge 1, E3 fix 10 and 3: the moonlit road read as snow): bare earth and stone darker while the
	// frost is out and no thaw has begun; the dawn keeps its own numbers.
	float night = ground_frost.x * (1.0 - clamp(ground_frost.y * 4.0, 0.0, 1.0));
	albedo *= 1.0 - night_dew * night * w_soft;

	// Hoar frost: on the exposed tops (the heights' high parts, the road's verges and centre strip), less in the
	// ruts, none in the wet or on standing water, none under a crown or the eaves; at dawn only in the shade.
	float frost_k = 0.0;
	if (ground_frost.x > 0.001) {
		vec2 ex = ex4.rg;
		float cover = ground_frost.x * ex.r * (1.0 - ground_frost.y * ex.g * 0.92) * smoothstep(0.6, 0.85, n_geo.y);
		float verge = (1.0 - smoothstep(0.3, 0.7, pm.r)) * smoothstep(0.05, 0.4, sp.r);
		// The tops: what stands above its own few centimetres around (the height a few mips up), so the rime
		// lies on each clump, stone and crumb, never in blotches the size of the map's own swells.
		float hb = (k0 == SETTS ? textureGrad(s_arh, uv0, dx0 * 5.0, dy0 * 5.0) : textureGrad(g_arh, uv0, dx0 * 5.0, dy0 * 5.0)).b;
		// Bare earth holds the day's warmth longer than grass does; a fire's keeps it off.
		cover *= mix(0.45, 1.0, w_meadow);
		for (int i = 0; i < 4; i++) if (warm_at[i].z > 0.0) cover *= smoothstep(warm_at[i].z, warm_at[i].z + 2.5, length(w - warm_at[i].xy));
		// (The ruts take the frost as the road beside them does: judge 1 kept the frost out of the ruts' contrast.)
		float top = 0.5 + (hgt - hb) * 2.2 + cen * 0.12;
		// On a road the rime follows its shape (judge 2, E3 fix 3): the crown and the ruts' shoulders, not the map's noise.
		float rd = smoothstep(0.3, 0.7, pm.r);
		// Its verges: no lift at the made edge (the pale verge strips), the rime there no crisper than the road's.
		float vb = smoothstep(0.02, 0.3, pm.r) + verge * 0.6;
		float ridge = smoothstep(0.04, 0.25, rut) * (1.0 - smoothstep(0.3, 0.65, rut));
		top = mix(top, 0.5 + cen * 0.25 + ridge * 0.35 - rut * 0.45 + (hgt - hb) * 0.5, rd);
		// By night the frost on the tufts, not the bare soil between.
		top += (tuft - 0.5) * 0.5 * nt;
		// At dawn only the tops: the threshold raised with the thaw (judge 1, E3 fix 2: no pale blotches in the shade).
		float thr = mix(1.0, 1.0 - frost_reach, cover) + ground_frost.y * frost_dawn;
		float fw = mix(mix(0.11, 0.025, frost_crisp), 0.14, clamp(vb, 0.0, 1.0));
		float fr = smoothstep(thr - fw, thr + fw, top) * smoothstep(0.02, 0.2, cover);
		fr *= (1.0 - smoothstep(0.12, 0.4, wet)) * (1.0 - pud);
		float fstr = min(mix(0.8, frost_soft, w_soft), mix(0.8, 0.3, clamp(vb, 0.0, 1.0)));
		// (By night on the meadow: thick on the tufts, thin on the bare soil between.)
		frost_k = fr * fstr * mix(1.0, mix(0.3, 1.0, tuft), nt);
		float fl = min(dot(albedo, vec3(0.2126, 0.7152, 0.0722)) * frost_tone, frost_cap * mix(1.0, mix(0.7, 1.1, tuft), nt));
		// Neutral rime (judge 1: blue rime under a lilac dawn read as mould), keeping a trace of the ground's own hue.
		vec3 own = albedo / max(dot(albedo, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
		albedo = mix(albedo, mix(vec3(1.0), own, 0.25) * fl, frost_k);
		rough = mix(rough, 0.88, fr);
		albedo *= 1.0 + night_val * ((nC.g - 0.5) * 1.2 + (nM.r - 0.5) * 0.8) * nt;
		n_w = normalize(mix(n_w, n_geo, fr * 0.3));
	}

	// Blight: dead ground veined with sick light.
	float vein = 1.0 - abs(nM.g * 2.0 - 1.0);
	vein = pow(vein, 10.0) + pow(1.0 - abs(nF.r * 2.0 - 1.0), 16.0) * 0.6;
	// Only true blight glows (the Verge's paint runs to 0.55): a faint wash (Low Ford's graveyard, 0.35 at most) is dead
	// ground, not neon veins (its few noise-tipped patches drew a hard green squiggle by the crypt; judge 2, item 6).
	EMISSION = blight_glow * vein * w_blight * (0.55 + 0.45 * sin(TIME * 1.3 + nL.r * 12.0)) * 1.6 * smoothstep(0.38, 0.46, sp.b);

	// E6: the river's bed (silt and river stones, under the water) and its wet bank (dark and slick a hand above it),
	// both wobbling so the waterline never runs straight.
	if (water_level.w > 0.5 && water_bed.y + water_bed.z > 0.0) {
		float bk_above = w_pos.y - water_level.x + (nF.b - 0.5) * 0.08 + (nM.r - 0.5) * 0.06;
		float bk_sunk = 1.0 - smoothstep(-0.1, 0.0, bk_above);
		if (bk_sunk > 0.0) {
			// River stones: a cell each about 0.3 m, some left out, their edges shaded into the silt.
			vec2 q = w * 3.4;
			vec2 qi = floor(q), qf = fract(q);
			float f1 = 8.0, f2 = 8.0, hid = 0.0;
			for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
				vec2 o = vec2(float(i), float(j));
				vec2 c = o + vec2(hash12(qi + o), hash12(qi + o + 17.3)) * 0.8 + 0.1 - qf;
				float d = dot(c, c);
				if (d < f1) { f2 = f1; f1 = d; hid = hash12(qi + o + 41.7); } else if (d < f2) f2 = d;
			}
			float bk_rim = sqrt(f2) - sqrt(f1);
			float bk_peb = smoothstep(0.06, 0.2, bk_rim) * step(hid, water_bed.x * (0.6 + 0.8 * nM.g));
			float bk_lum = dot(albedo, vec3(0.2126, 0.7152, 0.0722));
			vec3 bk_silt = water_silt.rgb * (0.82 + 0.36 * nF.g);
			vec3 bk_bedc = mix(albedo, bk_silt * mix(1.0, bk_lum / 0.12, 0.25), water_bed.y);
			vec3 bk_stone = mix(bk_silt * 1.15, vec3(dot(bk_silt, vec3(0.333)) * 1.2), 0.5) * (0.85 + 0.3 * fract(hid * 7.31));
			bk_bedc = mix(bk_bedc * mix(0.86, 1.0, smoothstep(0.0, 0.14, bk_rim)), bk_stone, bk_peb * 0.7);
			albedo = mix(albedo, bk_bedc, bk_sunk);
			rough = mix(rough, 0.55, bk_sunk);
		}
		// (the bed under the water as wet as the bank's foot: no lighter strip where the water takes it)
		float bk_wet = (1.0 - smoothstep(0.0, water_bed.z, bk_above)) * step(0.001, water_bed.z);
		albedo *= 1.0 - bk_wet * water_bed.w * (1.0 - 0.4 * bk_sunk);
		rough = mix(rough, 0.28, bk_wet);
	}

	ALBEDO = albedo;
	if (debug_view == 1) ALBEDO = pm.rgb;
	if (debug_view == 2) ALBEDO = sp.rgb;
	if (debug_view == 4) ALBEDO = vec3(frost_k, 0.0, 1.0 - frost_k);
	if (debug_view == 3) ALBEDO = vec3(texture(expo_tex, zuv).rg, 0.0);
	// 10-18 (measure_d.py's masks), one a frame, unlit and stepped at 0.5 (white on black: no tonemap can mix them):
	// 10 the gutter, 11 open setts (no grime, gutter, lane or puddle), 12 the grime's reach on setts, 13 puddles,
	// 14 setts within 0.9 m of a wall (0.5 m past the gutter) whose joints are weeded, 15 setts within 0.9 m of a wall, 16 the wear lane (clear of the grime),
	// 17 a street-side wall's foot (to gutter_w), 18 the setts' edge band.
	float near05 = step(nr.r * 2.0, 0.9) * w_setts;
	bool dbg_on = debug_view >= 10;
	if (dbg_on) {
		float m = 0.0;
		if (debug_view == 10) m = gut;
		if (debug_view == 11) m = w_setts * (1.0 - step(0.5, near_any)) * (1.0 - step(0.5, gut)) * (1.0 - step(0.5, nr.b)) * (1.0 - step(0.5, pud));
		if (debug_view == 12) m = near_any * step(0.5, w_setts);
		if (debug_view == 13) m = pud;
		if (debug_view == 14) m = step(0.5, wsel) * near05;
		if (debug_view == 15) m = near05;
		if (debug_view == 16) m = step(0.5, nr.b) * w_setts * (1.0 - step(0.5, near_any));
		if (debug_view == 17) m = step(nr.r * 2.0, gutter_w) * step(0.5, sp.g);
		if (debug_view == 18) m = s_band;
		float opn = w_setts * (1.0 - step(0.5, near_any)) * (1.0 - step(0.5, gut)) * (1.0 - step(0.5, nr.b)) * (1.0 - step(0.5, pud)) * step(joint, 0.3);
		if (debug_view == 19) m = opn * step(0.0, n_w.x);
		if (debug_view == 20) m = opn * step(0.0, n_w.z);
		if (debug_view == 21) m = step(0.1, w_soft);
		if (debug_view == 22) m = step(0.9, w_soft);
		if (debug_view == 23) m = step(0.5, prim);
		if (debug_view == 24) m = opn;
		// 25 the setts' stones (tile height over a stone's edge, before the mud), for their sizes in the frame.
		if (debug_view == 25) m = step(0.5, w_setts) * step(0.34, hgt0);
		// 26 the setts' mud (E3 G).
		if (debug_view == 26) m = dbg_mud_c;
		if (debug_view == 27) m = dbg_collar;
		ALBEDO = vec3(0.0);
		EMISSION = vec3(step(0.5, m) * 50.0);
	}
	ROUGHNESS = clamp(mix(rough, 1.0, night * (1.0 - pud) * 0.6), 0.04, 1.0);
	AO = mix(1.0, ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	// By night the ground's sheen at the close camera's grazing angle read as snow on the road and pale smears at the
	// tufts' feet (judge 1, E3 fix 10): the moonlit ground kept matte, the puddles still holding the sky.
	SPECULAR = dbg_on ? 0.0 : mix(mix(mix(0.35, mud_spec, mud_s), night_spec, night), mirror, pud);
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);

	// The Flare's drain, web, frost and scars (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; float fl_s = SPECULAR; vec3 fl_n = NORMAL; vec3 fl_e = EMISSION;
		flare_ground((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, fl_a, fl_r, fl_s, fl_n, fl_e, VIEW_MATRIX, INV_VIEW_MATRIX);
		ALBEDO = fl_a; ROUGHNESS = fl_r; SPECULAR = fl_s; NORMAL = fl_n; EMISSION = fl_e;
	}
}
