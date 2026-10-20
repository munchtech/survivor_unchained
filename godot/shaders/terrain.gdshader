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
uniform float rut_depth = 0.07;
uniform float wet_amt = 1.0;
// 1: show the road mask (R road, G ruts, B wet) as the colour; 2: the paint.
uniform int debug_view = 0;

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
	sp.b *= 1.0 - heal * 0.85;
	vec3 n_geo = normalize(w_nrm);
	vec3 p_dx = dFdx(w_pos), p_dy = dFdy(w_pos);

	// How much of each material the paint asks for: its own ramps (about a
	// metre), nudged by noise, never stepped.
	float wd = clamp((sp.r - 0.5) * edge_k + 0.5 + (nM.b - 0.5) * 0.3 + (nF.g - 0.5) * 0.12, 0.0, 1.0) * step(0.02, sp.r);
	float ws = clamp((sp.g - 0.5) * edge_k + 0.5 + (nM.g - 0.5) * 0.25, 0.0, 1.0) * step(0.02, sp.g);
	float wb = clamp((sp.b - 0.5) * edge_k + 0.5 + (nM.r - 0.5) * 0.4, 0.0, 1.0) * step(0.02, sp.b);
	float wm = clamp((sp.a - 0.5) * edge_k + 0.5 + (nM.g - 0.5) * 0.3, 0.0, 1.0) * step(0.02, sp.a);
	// The road's centre strip: sparse grass between the ruts.
	float cen = smoothstep(0.84, 0.96, pm.r);
	wd *= 1.0 - cen * 0.45;
	float slope = 1.0 - clamp(n_geo.y, 0.0, 1.0);
	float wr = smoothstep(0.3, 0.55, slope + (nM.b - 0.5) * 0.15);
	float leafy = smoothstep(0.38, 0.82, nL.g * 0.7 + nM.a * 0.3 + leaves - 0.5);
	float gw[NL] = float[](1.0 - leafy, leafy, 0.0, 0.0, 0.0, 0.0, 0.0);
	// Each overlay takes its share from everything under it.
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wd;
	gw[2] += wd;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wm;
	gw[3] += wm;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - ws;
	gw[SETTS] += ws;
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

	vec4 A[4], Nn[4], H[4];
	mat3 T[4];
	float hs[4];
	float best = -1.0;
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
		if (s < 2 && k != SETTS) {
			vec4 a1, n1, h1;
			fetch3(k, uv + off_b, ly, dx, dy, a1, n1, h1);
			float b = smoothstep(0.2, 0.8, at_f + (h1.b - h0.b) * 0.5);
			a0 = mix(a0, a1, b); n0 = mix(n0, n1, b); h0 = mix(h0, h1, b);
		}
		A[s] = a0; Nn[s] = n0; H[s] = h0;
		hs[s] = wv[s] + h0.b * h_amp;
		best = max(best, hs[s]);
	}
	// Heights decide at the edges: the taller material shows.
	float bw[4];
	float tot = 0.0;
	for (int s = 0; s < 4; s++) {
		bw[s] = hs[s] < -1.0 ? 0.0 : max(hs[s] - best + h_depth, 0.0);
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
	vec3 straw = albedo * vec3(1.07, 1.03, 0.86);
	vec3 green = albedo * vec3(0.95, 1.03, 0.94);
	albedo = mix(albedo, mix(green, straw, smoothstep(0.3, 0.7, nC.g)), w_meadow * 0.6 * macro_amt);
	// Setts: the world's own tone over the tile, so no two copies match.
	albedo *= 1.0 + (nF.r - 0.5) * 0.22 * w_setts;

	// The road: its made surface packed a little smoother; the ruts darker,
	// wetter, smoother, dipped through the normal.
	float road = smoothstep(0.4, 0.8, pm.r) * w_soft;
	rough -= road * 0.03;
	float rut = pm.g;
	// Packed smooth by the wheels.
	n_w = normalize(mix(n_w, n_geo, rut * w_soft * 0.3));
	if (rut > 0.003) {
		vec2 e = vec2(mask_texel / zone_size, 0.0);
		float gx = textureLod(paint_mask, zuv + e.xy, 0.0).g - textureLod(paint_mask, zuv - e.xy, 0.0).g;
		float gz = textureLod(paint_mask, zuv + e.yx, 0.0).g - textureLod(paint_mask, zuv - e.yx, 0.0).g;
		vec2 dh = -vec2(gx, gz) / (2.0 * mask_texel) * rut_depth;
		n_w = normalize(n_w + vec3(-dh.x, 0.0, -dh.y) * w_soft);
	}

	// Wet: hollows, ruts, gutters. Damp grass darkens less than earth.
	float wet = clamp(pm.b * wet_amt * (1.0 - w_meadow * 0.6) + rut * 0.35 * w_soft, 0.0, 1.0);
	wet *= smoothstep(0.25, 0.55, 1.0 - hgt * 0.6 + (nF.a - 0.5) * 0.4);
	albedo *= mix(1.0, 0.64, wet) * (1.0 - 0.38 * rut * w_soft);
	rough = mix(rough, 0.72, wet * 0.6);
	// Puddles: standing water in the deepest ruts and low corners, on earth, mud and stone.
	float pud = smoothstep(0.6, 0.7, pm.a + (nF.b - 0.5) * 0.5 + (nM.a - 0.5) * 0.3 - hgt * 0.25) * w_soft * wet_amt;
	albedo = mix(albedo, albedo * 0.45, pud);
	rough = mix(rough, 0.05, pud);
	n_w = normalize(mix(n_w, n_geo, pud * 0.9));

	// Blight: dead ground veined with sick light.
	float vein = 1.0 - abs(nM.g * 2.0 - 1.0);
	vein = pow(vein, 10.0) + pow(1.0 - abs(nF.r * 2.0 - 1.0), 16.0) * 0.6;
	// Only true blight glows (the Verge's paint runs to 0.55): a faint wash (Low Ford's graveyard, 0.35 at most) is dead
	// ground, not neon veins (its few noise-tipped patches drew a hard green squiggle by the crypt; judge 2, item 6).
	EMISSION = blight_glow * vein * w_blight * (0.55 + 0.45 * sin(TIME * 1.3 + nL.r * 12.0)) * 1.6 * smoothstep(0.38, 0.46, sp.b);

	ALBEDO = albedo;
	if (debug_view == 1) ALBEDO = pm.rgb;
	if (debug_view == 2) ALBEDO = sp.rgb;
	ROUGHNESS = clamp(rough, 0.04, 1.0);
	AO = mix(1.0, ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	SPECULAR = mix(0.35, 0.5, pud);
	NORMAL = normalize((VIEW_MATRIX * vec4(n_w, 0.0)).xyz);

	// The Flare's drain, web, frost and scars (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; float fl_s = SPECULAR; vec3 fl_n = NORMAL; vec3 fl_e = EMISSION;
		flare_ground((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, fl_a, fl_r, fl_s, fl_n, fl_e, VIEW_MATRIX, INV_VIEW_MATRIX);
		ALBEDO = fl_a; ROUGHNESS = fl_r; SPECULAR = fl_s; NORMAL = fl_n; EMISSION = fl_e;
	}
}
