// An ember arena's ground (View/ArenaGround.cs): the place's own seven
// photoscanned materials (art/arena/PLACE: two for the ground itself, four it
// paints over them, one for steep faces), mixed by the arena's two paints
// (Maps/ArenaGen.cs), their edges frayed by noise and decided by height, each
// sampled twice and turned along a slow noise so no tile repeats on screen.
// Over them: standing water that holds the moon, ground trodden flat, the
// ember's char with its cracks glowing, and the dark past the ring.
//
// For the fight's sake the ground is held in a value range below everything
// that moves on it (g_tone, g_sat), and the ember's glow keeps to the char.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#define NL 7
#define FACE 6

uniform sampler2D noise_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2D splat2 : filter_linear_mipmap, repeat_disable;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_nor : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_arh : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float g_scale[NL];
// Each photograph brought to the value the place asks of it (its mean albedo
// over what it was shot at), and how much of its colour it keeps: all kept
// below the living (View/ArenaGround.cs).
uniform float g_tone[NL];
uniform float g_sat[NL];
uniform float zone_size = 300.0;
// Moonlight through a canopy, in pools (the Hollow).
uniform float dapple = 0.0;
uniform vec3 ember : source_color = vec3(1.0, 0.35, 0.13);
uniform float ember_glow = 1.0;
// Water's colour in the low places (a stream's slurry sheen).
uniform vec3 wet_tint : source_color = vec3(0.55, 0.55, 0.52);
// The night sky as standing water gives it back (no reflection probe sees
// it from the arena's camera; without it, water reads as a hole).
uniform vec3 sheen : source_color = vec3(0.2, 0.27, 0.4);
uniform float sheen_amount = 0.06;

varying vec3 w_pos;
varying vec3 w_nrm;
varying float w_in;

const mat2 G_TURN = mat2(vec2(0.8, -0.6), vec2(0.6, 0.8));

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	// How far inside the ring this vertex is (1 well in, 0 well out).
	w_in = COLOR.r;
}

vec2 g_uv(int i, vec3 p, vec3 n, out mat3 tbn) {
	if (i == FACE) {
		vec2 h = normalize(n.xz + vec2(1e-4, 0.0));
		vec3 t = vec3(-h.y, 0.0, h.x);
		tbn = mat3(t, vec3(0.0, -1.0, 0.0), n);
		return vec2(dot(p.xz, vec2(-h.y, h.x)), p.y) * g_scale[i];
	}
	vec3 t = normalize(vec3(1.0, 0.0, 0.0) - n * n.x);
	tbn = mat3(t, cross(n, t), n);
	return p.xz * g_scale[i];
}

// No tile repeats on screen (Inigo Quilez's "texture repetition", third
// way): a slow noise picks, patch by patch, one of eight offsets into the
// photograph, and two neighbouring picks are blended where the noise
// crosses between them. Offsets only, so the normals need no turning; the
// gradients are the unshifted uv's, so the mip level never jumps at a seam.
struct Pick { vec2 a; vec2 b; float t; vec2 dx; vec2 dy; };

Pick pick(vec2 uv, vec2 w, int i) {
	Pick p;
	float k = texture(noise_tex, w * 0.09 + vec2(float(i) * 0.137, float(i) * 0.291)).r;
	float l = k * 8.0;
	float ia = floor(l);
	p.a = sin(vec2(3.0, 7.0) * ia);
	p.b = sin(vec2(3.0, 7.0) * (ia + 1.0));
	p.t = smoothstep(0.25, 0.75, fract(l));
	p.dx = dFdx(uv);
	p.dy = dFdy(uv);
	return p;
}

vec4 tex2(sampler2DArray s, vec2 uv, int i, Pick p) {
	vec4 a = textureGrad(s, vec3(uv + p.a, float(i)), p.dx, p.dy);
	vec4 b = textureGrad(s, vec3(uv + p.b, float(i)), p.dx, p.dy);
	return mix(a, b, p.t);
}

vec3 nor2(vec2 uv, int i, Pick p) {
	return normalize(tex2(g_nor, uv, i, p).xyz * 2.0 - 1.0);
}

void fragment() {
	vec2 w = w_pos.xz;
	vec4 nL = texture(noise_tex, w * 0.011);
	vec4 nM = texture(noise_tex, w * 0.061 + 0.37);
	vec4 nF = texture(noise_tex, w * 0.29 + 0.71);
	vec2 suv = (w + zone_size * 0.5) / zone_size;
	vec4 sp = texture(splat, suv);
	vec4 s2 = texture(splat2, suv);
	vec3 n_geo = normalize(w_nrm);

	// The ground's two materials, in the patches the paint asks for.
	float b2 = smoothstep(0.3, 0.7, s2.a + (nM.b - 0.5) * 0.5 + (nF.g - 0.5) * 0.15);
	float gw[NL] = float[](1.0 - b2, b2, 0.0, 0.0, 0.0, 0.0, 0.0);
	// The four painted over them, each taking its share from what is under it.
	float wp[4] = float[](
		smoothstep(0.35, 0.65, sp.r + (nM.b - 0.5) * 0.4 + (nF.g - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.g + (nM.g - 0.5) * 0.4 + (nF.b - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.b + (nM.r - 0.5) * 0.4 + (nF.r - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.a + (nM.a - 0.5) * 0.4 + (nF.g - 0.5) * 0.12));
	for (int l = 0; l < 4; l++) {
		for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wp[l];
		gw[2 + l] += wp[l];
	}
	float slope = 1.0 - clamp(n_geo.y, 0.0, 1.0);
	float wr = smoothstep(0.32, 0.52, slope + (nM.b - 0.5) * 0.15);
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wr;
	gw[FACE] += wr;

	// Heights decide at the edges: the taller material shows.
	const float BLEND_DEPTH = 0.22;
	float hs[NL];
	vec4 arhs[NL];
	float best = 0.0;
	for (int k = 0; k < NL; k++) {
		hs[k] = -1.0;
		if (gw[k] < 0.003) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		arhs[k] = tex2(g_arh, uv, k, pick(uv, w, k));
		hs[k] = gw[k] + arhs[k].b * BLEND_DEPTH;
		best = max(best, hs[k]);
	}
	float tot = 0.0;
	for (int k = 0; k < NL; k++) {
		gw[k] = hs[k] < 0.0 ? 0.0 : max(hs[k] - best + BLEND_DEPTH, 0.0);
		tot += gw[k];
	}
	vec3 albedo = vec3(0.0);
	vec3 n_w = vec3(0.0);
	float rough = 0.0, ao = 0.0, hgt = 0.0;
	for (int k = 0; k < NL; k++) {
		float wk = gw[k] / tot;
		if (wk < 0.004) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		Pick p = pick(uv, w, k);
		vec4 arh = arhs[k];
		vec3 a = tex2(g_alb, uv, k, p).rgb;
		a = mix(vec3(dot(a, vec3(0.2126, 0.7152, 0.0722))), a, g_sat[k]);
		albedo += a * g_tone[k] * wk;
		n_w += tbn * nor2(uv, k, p) * wk;
		rough += arh.g * wk;
		ao += arh.r * wk;
		hgt += arh.b * wk;
	}
	vec3 n = normalize(n_w);

	// Slow variation over tens of metres, so a field is never one colour.
	albedo *= 0.78 + 0.3 * nL.r;
	albedo = mix(albedo, albedo * vec3(1.04, 1.0, 0.9), smoothstep(0.55, 0.8, nL.b) * 0.4);

	// Trodden flat: darker, smoother.
	float trod = s2.b * (0.8 + 0.4 * nF.r);
	albedo *= 1.0 - 0.22 * trod;
	rough = mix(rough, rough * 0.85, trod);

	// Standing water: in the low parts of the material first, then over it;
	// dark, near mirror-smooth, flat, holding the moon.
	float wet = clamp(s2.r * 1.25 - hgt * 0.45 + (nM.g - 0.5) * 0.25, 0.0, 1.0);
	float pool = smoothstep(0.45, 0.75, wet);
	albedo *= mix(1.0, 0.55, smoothstep(0.0, 0.5, wet));
	albedo = mix(albedo, albedo * wet_tint * 1.4, pool);
	rough = mix(rough, 0.06, pool);
	rough = mix(rough, rough * 0.55, smoothstep(0.1, 0.45, wet));
	n = normalize(mix(n, n_geo, pool * 0.92));

	// The ember's char: ash-black, cracked, the cracks glowing where it is
	// deepest and breathing slowly.
	float ch = s2.g;
	float charred = smoothstep(0.15, 0.6, ch + (nF.b - 0.5) * 0.3);
	albedo = mix(albedo, vec3(0.022, 0.019, 0.017) * (0.7 + 0.6 * nF.g), charred * 0.92);
	rough = mix(rough, 0.95, charred);
	// Thin cracks: the char split along two scales of noise, glowing only
	// where it is deepest; a hotter place (a pit's mouth, char past 0.85)
	// glows whole. Kept thin so the ring never reads as an amber telegraph.
	float crack = pow(1.0 - abs(nF.r * 2.0 - 1.0), 28.0) + pow(1.0 - abs(texture(noise_tex, w * 0.7 + 0.21).g * 2.0 - 1.0), 36.0) * 0.6;
	float deep = smoothstep(0.5, 0.8, ch);
	float hot = smoothstep(0.87, 1.0, ch);
	float breathe = 0.6 + 0.4 * sin(TIME * 0.9 + nL.r * 9.0) * sin(TIME * 0.37 + nM.b * 5.0);
	vec3 glow = ember * (crack * deep * 1.6 + hot * (0.5 + 0.8 * crack)) * breathe * ember_glow;

	// Moon through the leaves, in pools.
	if (dapple > 0.0) {
		float leaves = texture(noise_tex, w * 0.022 + vec2(TIME * 0.002, TIME * 0.0012)).g * 0.75 + texture(noise_tex, w * 0.09 - vec2(TIME * 0.004, 0.0)).b * 0.25;
		albedo *= mix(1.0, mix(0.45, 1.4, smoothstep(0.4, 0.62, leaves)), dapple);
	}

	// Past the ring the night closes in: the place goes on, darker.
	float past = 1.0 - smoothstep(0.0, 1.0, w_in);
	albedo *= 1.0 - 0.6 * past;

	ALBEDO = albedo;
	ROUGHNESS = clamp(rough, 0.04, 1.0);
	AO = mix(1.0, ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	SPECULAR = mix(0.35, 0.6, pool);
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	// Standing water gives the sky back, broken by the wind on it.
	float ripple = texture(noise_tex, w * 0.35 + vec2(TIME * 0.02, -TIME * 0.013)).g;
	glow += sheen * sheen_amount * pool * (0.55 + 0.9 * ripple) * (1.0 - charred);
	EMISSION = glow;
}
