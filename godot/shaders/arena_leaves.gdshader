// Fallen leaves lying on an arena's litter (World/Grass.cs, Leaves): a scatter of
// leaves per cell on a jittered grid that wraps round the survivor, each lying
// flat and a little curled, rust, ochre and dead-pale, where the place's paint
// says the litter lies (its mask's R). From thirty metres up a photograph of
// litter averages into gravel; leaves a few pixels long, each its own colour and
// catching the light on its curl, read as leaves.
// COLOR.rg: the leaf's middle in its cell (0..1 over cell_span); COLOR.b: its own
// hash; UV.y: 0 at its edge, 1 on its curl's crown.
shader_type spatial;
render_mode cull_disabled, diffuse_burley, world_vertex_coords;
#define CEL_INK 2
#define CEL_BAND vec4(0.0, 0.15, 0.2, 0.05)
#define CEL_NO_RIM
// (the material library, godot/data/look/materials.json: this shader's default class; matte, rule 6: no highlight)
#define CEL_SPEC vec4(9.0, 1.5, 0.0, 0.85)
#include "res://shaders/cel.gdshaderinc"

#include "res://shaders/flare_world.gdshaderinc"
#include "res://shaders/arena_masses.gdshaderinc"

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform float zone_size = 300.0;
uniform float density = 1.0;
uniform float size = 1.0;
uniform float cell_span = 0.6;
// Linear colours: this year's rust, ochre, dead-pale, and old leaves gone dark.
uniform vec3 rust : source_color = vec3(0.24, 0.07, 0.02);
uniform vec3 ochre : source_color = vec3(0.3, 0.17, 0.04);
uniform vec3 pale : source_color = vec3(0.32, 0.25, 0.14);
uniform vec3 dark : source_color = vec3(0.06, 0.035, 0.02);
uniform vec2 centre = vec2(0.0);
uniform float span = 80.0;
// (H2 R2 round 2) The litter under them, as its ground draws it (ArenaGround.Material, layer 0:
// its repeats a metre, tone, saturation, contrast and mean), and the ground's own terms over it:
// trodden (splat2 B), the ember's scorch toward the ring, the dark past it.
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2DArray g_arh : filter_linear_mipmap, repeat_enable;
uniform sampler2D splat2 : filter_linear_mipmap, repeat_disable;
uniform float l_scale = 0.5;
uniform float l_tone = 1.0;
uniform float l_sat = 1.0;
uniform float l_con = 1.0;
uniform float l_mean = 0.1;
uniform float scorch_reach = 11.0;
uniform float scorch_out = 1000.0;
uniform float past_dark = 0.6;
// R: the ground's height; G: metres inside the ring (negative past it).
uniform sampler2D heights : filter_linear, repeat_disable;
uniform float h_size = 300.0;
uniform float h_res = 300.0;

varying vec3 v_col;
varying float v_t;
varying float v_rough;
varying float v_ao;

float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

vec2 ground_at(vec2 p) {
	vec2 f = clamp((p + h_size * 0.5) / h_size * (h_res - 1.0), vec2(0.0), vec2(h_res - 1.0));
	return textureLod(heights, (f + 0.5) / h_res, 0.0).rg;
}

void vertex() {
	vec3 root = MODEL_MATRIX[3].xyz;
	vec3 off = VERTEX - root;
	vec2 wp = root.xz + span * round((centre - root.xz) / span);
	float edge = 1.0 - smoothstep(span * 0.38, span * 0.5, length(wp - centre));
	// (The cell is turned as it was laid: its leaves' middles with it.)
	vec2 mid = (MODEL_MATRIX * vec4((COLOR.r - 0.5) * cell_span, 0.0, (COLOR.g - 0.5) * cell_span, 0.0)).xz;
	float own = COLOR.b;
	vec2 lp = wp + mid;
	float paint = texture(splat, (lp + zone_size * 0.5) / zone_size).r;
	float drift = texture(noise_tex, lp * 0.09 + 0.3).g;
	// Thick in drifts, thin between them; none where the paint has none.
	float keep = step(own, paint * density * edge * (0.45 + 1.0 * drift));
	float s = size * (0.75 + 0.5 * gh(wp * 3.7 + own * 11.0)) * keep;
	vec3 rel = (off - vec3(mid.x, 0.0, mid.y)) * s;
	vec2 gi = ground_at(lp);
	VERTEX = vec3(lp.x, gi.x + 0.012, lp.y) + rel;
	NORMAL = vec3(0.0, 1.0, 0.0);
	v_col = vec3(0.0); v_rough = 0.9; v_ao = 1.0;
	// (A leaf not laid, most of them, costs nothing more: its colour is twelve fetches, seven times a leaf.)
	if (keep > 0.5) {
		// (H2 R2, bible rules 5 and 6: painted, not photographic.) A drift's colour is the drift's, a few
		// metres across (rust, ochre, a paler fall), and each leaf only a little off it.
		float dm = texture(noise_tex, lp * 0.17 + 0.61).r * 0.7 + texture(noise_tex, lp * 0.05 + 0.23).g * 0.3;
		vec3 dc = mix(mix(rust, ochre, smoothstep(0.3, 0.55, dm)), pale, smoothstep(0.6, 0.8, dm) * 0.6);
		// (Round 2: the leaves are the litter's brush strokes, so they take the litter's own albedo at
		// their spot, as its ground draws it, and only their hue from the drift. Coloured by the drift
		// alone they had none of the blue the moon finds in the litter, and lay on it as near-black chips.)
		vec2 luv = lp * l_scale;
		float pk = texture(noise_tex, lp * 0.09).r * 8.0;
		float ia = floor(pk);
		vec2 oa = sin(vec2(3.0, 7.0) * ia), ob = sin(vec2(3.0, 7.0) * (ia + 1.0));
		float pt = smoothstep(0.25, 0.75, fract(pk));
		// (At a leaf's own size, a few centimetres: the litter's colour there, not its every grain.)
		const float LOD = 5.5;
		vec3 a = mix(textureLod(g_alb, vec3(luv + oa, 0.0), LOD).rgb, textureLod(g_alb, vec3(luv + ob, 0.0), LOD).rgb, pt);
		vec4 arh = textureLod(g_arh, vec3(luv + oa, 0.0), LOD);
		float la = dot(a, vec3(0.2126, 0.7152, 0.0722));
		a *= pow(max(la, 1e-4) / l_mean, l_con - 1.0);
		a = mix(vec3(dot(a, vec3(0.2126, 0.7152, 0.0722))), a, l_sat) * l_tone;
		vec4 nL = texture(noise_tex, lp * 0.011);
		vec4 nM = texture(noise_tex, lp * 0.061 + 0.37);
		vec4 nF = texture(noise_tex, lp * 0.29 + 0.71);
		a *= 0.78 + 0.3 * nL.r;
		a = mix(a, a * vec3(1.04, 1.0, 0.9), smoothstep(0.55, 0.8, nL.b) * 0.4);
		float inside = gi.y;
		a *= arena_mass(inside, texture(noise_tex, lp * 0.0085 + vec2(0.41, 0.17)), nL);
		// The hue nudged a quarter of the way to the drift's, at the litter's value.
		float ly = max(dot(a, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
		vec3 dn = dc / max(dot(dc, vec3(0.2126, 0.7152, 0.0722)), 1e-4) * ly;
		vec3 c = mix(a, dn, 0.25) * (0.8 + 0.24 * gh(wp * 9.1 + own * 3.0));
		// The ground's own terms over the litter (arena_ground.gdshader), so the leaf keeps to it.
		vec2 suv = (lp + zone_size * 0.5) / zone_size;
		float trod = texture(splat2, suv).b * (0.8 + 0.4 * nF.r);
		c *= 1.0 - 0.22 * trod;
		float inn = inside + (nM.r - 0.5) * 2.2 + (nF.g - 0.5) * 0.25;
		float scorch = 1.0 - smoothstep(2.0 * scorch_reach / 11.0, scorch_reach, inn + (nL.g - 0.5) * 7.0 * scorch_reach / 11.0);
		scorch *= smoothstep(-scorch_out - 1.5, -scorch_out, inn);
		float lum0 = dot(c, vec3(0.2126, 0.7152, 0.0722));
		c = mix(c, vec3(lum0) * vec3(1.05, 0.9, 0.74) * 0.72, scorch * 0.8);
		c *= 1.0 - past_dark * (1.0 - smoothstep(0.0, 1.0, smoothstep(-16.0, -3.0, inside)));
		v_col = c;
		v_rough = arh.g;
		v_ao = arh.r;
	}
	v_t = UV.y;
}

void fragment() {
	// The curl's crown catches the light; the leaf's edges lie in its own shade.
	// (A soft curl, 0.88-1.08: with a dark rim each leaf was outlined, and the litter read as chips.)
	// (Round 2: 0.92-1.08, a stroke's soft body lit on its crown, never a chip's outline.)
	ALBEDO = v_col * mix(0.92, 1.08, v_t);
	// Lit as the litter under it is (arena_ground.gdshader: its roughness and occlusion, specular
	// 0.35), so the moon finds as much in a leaf as round it. (Round 1 had them matte, 0.88 and
	// 0.12, against a slate-blue sheen; at the litter's own value and roughness the sheen matches.)
	ROUGHNESS = clamp(max(v_rough, 0.6), 0.04, 1.0);
	SPECULAR = 0.35;
	AO = mix(1.0, v_ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);

	// The Flare's drain and frost on the tips (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_blade((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, v_t, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
	}
	// The cel model's end of fragment (cel.gdshaderinc: geometric normal, ink tag, debug).
	CEL_FRAGMENT;
}
