// The ground: the web game's terrain shader (src/render/terrain.ts), in
// Godot. Seven photoscanned materials (art/ground, one array layer each:
// meadow, forest floor, dirt, mud, setts, rock, burnt earth); the zone's
// paint says how much of each, edges frayed by noise, and then their heights
// decide, so setts stand out of the mud between them. Each is sampled twice,
// as laid and turned, meeting along a slow noise, so no tile repeats across
// the screen; rock on steep faces is laid on the face.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#define NL 7
#define ROCK 5

uniform sampler2D noise_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_nor : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_arh : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float g_scale[NL];
uniform float zone_size = 290.0;
uniform float leaves = 0.3;
uniform vec3 blight_glow : source_color = vec3(0.55, 1.0, 0.35);
// How far the blight has drawn back (the Verge once the poison stops): the
// paint's blight at 1 - heal * 0.85, as the web game paints it.
uniform float heal = 0.0;

varying vec3 w_pos;
varying vec3 w_nrm;

// Each photograph brought into the same light: the setts were shot clean
// and pale in the sun; this country's are not.
// The trodden earth's photograph is pale gravel, which under the moon turned
// to lilac stone: taken down and warmed toward the soil round it.
const float G_TONE[NL] = float[](1.0, 1.0, 0.62, 1.0, 0.72, 0.95, 1.0);
const mat2 G_TURN = mat2(vec2(0.8, -0.6), vec2(0.6, 0.8));

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec2 g_uv(int i, vec3 p, vec3 n, out mat3 tbn) {
	if (i == ROCK) {
		// On the face: across it horizontally, and up it.
		vec2 h = normalize(n.xz + vec2(1e-4, 0.0));
		vec3 t = vec3(-h.y, 0.0, h.x);
		tbn = mat3(t, vec3(0.0, -1.0, 0.0), n);
		return vec2(dot(p.xz, vec2(-h.y, h.x)), p.y) * g_scale[i];
	}
	// Laid flat: u along +x, the image's top toward -z.
	vec3 t = normalize(vec3(1.0, 0.0, 0.0) - n * n.x);
	tbn = mat3(t, cross(n, t), n);
	return p.xz * g_scale[i];
}

vec2 turned(vec2 uv) { return G_TURN * uv * 0.87 + vec2(0.37, 0.71); }

vec4 g_tex_alb(vec2 uv, int i, float tile) {
	vec4 a = texture(g_alb, vec3(uv, float(i)));
	if (tile <= 0.0) return a;
	return mix(a, texture(g_alb, vec3(turned(uv), float(i))), tile);
}

vec4 g_tex_arh(vec2 uv, int i, float tile) {
	vec4 a = texture(g_arh, vec3(uv, float(i)));
	if (tile <= 0.0) return a;
	return mix(a, texture(g_arh, vec3(turned(uv), float(i))), tile);
}

vec3 g_nor_ts(vec2 uv, int i, float tile) {
	vec3 a = texture(g_nor, vec3(uv, float(i))).xyz * 2.0 - 1.0;
	if (tile <= 0.0) return a;
	vec3 b = texture(g_nor, vec3(turned(uv), float(i))).xyz * 2.0 - 1.0;
	b.xy = transpose(G_TURN) * b.xy;
	return normalize(mix(a, b, tile));
}

void fragment() {
	vec2 w = w_pos.xz;
	vec4 nL = texture(noise_tex, w * 0.011);
	vec4 nM = texture(noise_tex, w * 0.061 + 0.37);
	vec4 nF = texture(noise_tex, w * 0.29 + 0.71);
	vec4 sp = texture(splat, (w + zone_size * 0.5) / zone_size);
	sp.b *= 1.0 - heal * 0.85;
	vec3 n_geo = normalize(w_nrm);
	float tile = smoothstep(0.46, 0.54, nL.b * 0.6 + nM.r * 0.4);

	// How much of each material the paint asks for, edges frayed by noise.
	float wd = smoothstep(0.35, 0.65, sp.r + (nM.b - 0.5) * 0.45 + (nF.g - 0.5) * 0.12);
	float ws = smoothstep(0.35, 0.65, sp.g + (nM.g - 0.5) * 0.35 + (nF.b - 0.5) * 0.15);
	float wb = smoothstep(0.3, 0.7, sp.b + (nM.r - 0.5) * 0.5);
	float wm = smoothstep(0.35, 0.65, sp.a + (nM.g - 0.5) * 0.4);
	float slope = 1.0 - clamp(n_geo.y, 0.0, 1.0);
	float wr = smoothstep(0.32, 0.5, slope + (nM.b - 0.5) * 0.15);
	float leafy = smoothstep(0.42, 0.78, nL.g * 0.7 + nM.a * 0.3 + leaves - 0.5);
	float gw[NL] = float[](1.0 - leafy, leafy, 0.0, 0.0, 0.0, 0.0, 0.0);
	// Each overlay takes its share from everything under it.
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wd;
	gw[2] += wd;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wm;
	gw[3] += wm;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - ws;
	gw[4] += ws;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wb;
	gw[6] += wb;
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wr;
	gw[ROCK] += wr;

	// Heights decide at the edges: the taller material shows.
	const float BLEND_DEPTH = 0.22;
	float hs[NL];
	float best = 0.0;
	for (int k = 0; k < NL; k++) {
		hs[k] = -1.0;
		if (gw[k] < 0.003) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		hs[k] = gw[k] + g_tex_arh(uv, k, tile).b * BLEND_DEPTH;
		best = max(best, hs[k]);
	}
	float tot = 0.0;
	for (int k = 0; k < NL; k++) {
		gw[k] = hs[k] < 0.0 ? 0.0 : max(hs[k] - best + BLEND_DEPTH, 0.0);
		tot += gw[k];
	}

	vec3 albedo = vec3(0.0);
	vec3 n_w = vec3(0.0);
	float rough = 0.0, ao = 0.0;
	for (int k = 0; k < NL; k++) {
		float wk = gw[k] / tot;
		if (wk < 0.004) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		vec4 arh = g_tex_arh(uv, k, tile);
		vec3 a = g_tex_alb(uv, k, tile).rgb * G_TONE[k];
		if (k == 2) a *= vec3(1.08, 0.98, 0.8);
		albedo += a * wk;
		n_w += tbn * g_nor_ts(uv, k, tile) * wk;
		rough += arh.g * wk;
		ao += arh.r * wk;
	}
	rough *= 1.0 - gw[3] / tot * 0.45;

	// The photographs are of lighter country than this; slow variation over
	// tens of metres, so a field is not one colour.
	albedo *= 0.8 + 0.2 * nL.r;
	albedo = mix(albedo, albedo * vec3(1.05, 1.0, 0.86), smoothstep(0.55, 0.8, nL.b) * 0.35);

	// Blight: dead ground veined with sick light.
	float vein = 1.0 - abs(nM.g * 2.0 - 1.0);
	vein = pow(vein, 10.0) + pow(1.0 - abs(nF.r * 2.0 - 1.0), 16.0) * 0.6;
	EMISSION = blight_glow * vein * (gw[6] / tot) * (0.55 + 0.45 * sin(TIME * 1.3 + nL.r * 12.0)) * 1.6;

	ALBEDO = albedo;
	ROUGHNESS = clamp(rough, 0.3, 1.0);
	AO = mix(1.0, ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	SPECULAR = 0.35;
	NORMAL = normalize((VIEW_MATRIX * vec4(normalize(n_w), 0.0)).xyz);
}
