// cel.gdshaderinc: the painted-cel shading model (L1 B1a, look-l1; docs: the bible v2 "painted cel").
//
// What it gives a lit surface, per light: a two-band ramp with a hard terminator, an optional warm half-tone band
// just past it, a soft Lambert gradient kept inside the lit band (forms stay round), a hardened cast shadow from the
// key (directional lights), the key's colored fill in the shadow band, a small hard-edged highlight in the light's
// color, and a stepped rim. Omni and spot lights keep their smooth distance falloff; only their n.l is banded.
// At cel_on 0 the default light() is Godot 4.5.1's built-in Burley diffuse + Schlick-GGX specular (+ RIM and
// BACKLIGHT), so every adopting shader lights as it did (the A side).
//
// ADOPTING IT (the pattern for a shader):
//  1. After `shader_type`/`render_mode` (and after any #define the C# side inserts), optionally define:
//       #define CEL_INK 1          the ink class this shader's materials default to (0 if not defined)
//       #define CEL_BAND vec4(0.0, 0.15, 0.2, 0.05)   a softer default ramp (the ground: no stripes)
//       #define CEL_NO_RIM         no stepped rim (ground, grass and cards, whose normals are not a silhouette)
//       #define CEL_BUILTIN_RIM    the shader writes Godot's RIM / RIM_TINT (the crowd, folk): light() reproduces it
//       #define CEL_OWN_LIGHT      the shader writes its own light() (see 4); the include then defines none
//     then:  #include "res://shaders/cel.gdshaderinc"
//  2. Make `CEL_FRAGMENT;` the LAST statement of fragment(). It records the geometric normal (NORMAL before
//     NORMAL_MAP; light() bands on mix(it, the mapped normal, cel_nmap) so detail doesn't crawl the terminator),
//     SPECULAR and RIM for light(), writes the ink tag into ROUGHNESS, and the debug views' overrides.
//  3. Nothing else: the default light() mixes today's light and the cel model by cel_on.
//  4. A shader with its own light() (CEL_OWN_LIGHT): first `if (cel_dbg_light(nb, t, ATTENUATION, LIGHT_IS_DIRECTIONAL,
//     dbg)) { SPECULAR_LIGHT += dbg; } else { ... }`, keep today's code as the A side, and build the B side from the
//     helpers below, e.g.
//       vec3 nb = cel_nb(NORMAL); float t = <your wrapped n.l on nb>; float sh = cel_shadow(ATTENUATION, LIGHT_IS_DIRECTIONAL);
//       vec3 lv = cel_level(t); vec3 b = LIGHT_COLOR * lv * sh / PI + cel_fill_add(LIGHT_COLOR, cel_lit(t) * sh, LIGHT_IS_DIRECTIONAL);
//       DIFFUSE_LIGHT += mix(a_side, b, cel_on);
//     (kit.gdshader's OWN_FOLIAGE and grass_own.gdshader are the worked examples.)
//
// PER-MATERIAL UNIFORMS (the material library sets them):
//   cel_band  x terminator in n.l, y its half-width (0.06 ~ 7 degrees full), z the half-tone's width past the
//             terminator (0: two bands), w the half-tone edge's half-width
//   cel_mid   the half-tone's level as a multiplier of the light (rgb; skin red-orange), a = how much
//   cel_form  how much Lambert gradient stays in the lit band (0 flat, 1 Lambert)
//   cel_spec  x highlight radius (degrees around N.H), y edge softness (degrees), z strength, w light color vs white;
//             the strength fades out with roughness (smoothstep 0.55-0.85) and with SPECULAR (0.5 = whole)
//   cel_nmap  the normal-map strength the band sees (the highlight keeps the full mapped normal)
//   cel_ink   the ink class (0 full: silhouette + creases, 1 silhouette only, 2 none, 3 full = unconverted)
// GLOBALS (project.godot [shader_globals]; Atmosphere.cs sets them from the preset):
//   cel_on 0..1 (0 = today exactly), cel_rig (x cast-shadow hardness: 0 PCF, 1 smoothstep(0.42, 0.58) on the key's
//   shadow; y the key's fill in the shadow band 0..0.25, tinted cel_fill, at the key's luminance; z rim strength;
//   w rim width in 1-n.v), cel_fill rgb, cel_rim rgb (linear), cel_tune (multipliers: band half-width, half-tone
//   width, spec radius, form; 1 = as authored), cel_dbg (0 off, 1 band: the key's band level as gray, 2 ink: the
//   class unlit, 0 white 1 yellow 2 blue 3 red).
//
// THE INK TAG (B5 reads it), verified against Godot 4.5.1-stable scene_forward_clustered.glsl (MODE_RENDER_NORMAL_ROUGHNESS):
//   the engine writes normal_roughness.a = roughness * 127/255, then 1 - that for instances flagged DYNAMIC
//   (moving / skinned: INSTANCE_FLAGS_DYNAMIC), into an R8G8B8A8_UNORM target; MSAA resolves pick one sample
//   (effects/resolve.glsl), never an average. The roughness limiter runs between fragment() and that write, so it
//   is off (project.godot). cel_tag sets ROUGHNESS = n / 127 with n = clamp(round(r * 31), 0, 31) * 4 + class, so:
//     byte b = round(a * 255);  n = b <= 127 ? b : 255 - b;  class = n & 3;  roughness ~ (n >> 2) / 31.
//   In a shader (alpha a as sampled from hint_normal_roughness_texture):
//     int b = int(round(a * 255.0)); int n = b > 127 ? 255 - b : b; int ink = n & 3;
//   An unconverted material at roughness 1.0 gives n 127: class 3 (full). Lighting sees the tagged roughness
//   (a step of 1/31 plus up to 3/127): under 0.04 rougher at most.

#ifndef CEL_INK
#define CEL_INK 0
#endif
#ifndef CEL_BAND
#define CEL_BAND vec4(0.0, 0.06, 0.2, 0.05)
#endif

group_uniforms cel;
uniform vec4 cel_band = CEL_BAND;
uniform vec4 cel_mid : source_color = vec4(0.55, 0.55, 0.6, 1.0);
uniform float cel_form : hint_range(0.0, 1.0) = 0.3;
uniform vec4 cel_spec = vec4(9.0, 1.5, 1.0, 0.85);
uniform float cel_nmap : hint_range(0.0, 1.0) = 0.35;
uniform int cel_ink : hint_range(0, 3) = CEL_INK;
group_uniforms;

global uniform float cel_on;
global uniform vec4 cel_rig;
global uniform vec3 cel_fill;
global uniform vec3 cel_rim;
global uniform vec4 cel_tune;
global uniform float cel_dbg;

// (fragment() to light(): the geometric normal, and x SPECULAR, y RIM, z RIM_TINT)
varying vec3 cel_gn;
varying vec4 cel_mat;

float cel_tag(float c_r, int c_ink) {
	return (clamp(round(c_r * 31.0), 0.0, 31.0) * 4.0 + float(clamp(c_ink, 0, 3))) / 127.0;
}
vec3 cel_ink_rgb(int c_ink) {
	return c_ink == 0 ? vec3(1.0) : c_ink == 1 ? vec3(1.0, 0.85, 0.0) : c_ink == 2 ? vec3(0.0, 0.25, 1.0) : vec3(1.0, 0.0, 0.0);
}

#ifdef CEL_BUILTIN_RIM
#define CEL_FRAG_MAT cel_mat = vec4(SPECULAR, RIM, RIM_TINT, 0.0)
#else
#define CEL_FRAG_MAT cel_mat = vec4(SPECULAR, 0.0, 0.0, 0.0)
#endif
// The last statement of fragment(): see the header.
#define CEL_FRAGMENT cel_gn = NORMAL; CEL_FRAG_MAT; ROUGHNESS = cel_tag(ROUGHNESS, cel_ink); if (cel_dbg > 0.5) { EMISSION = cel_dbg > 1.5 ? cel_ink_rgb(cel_ink) : vec3(0.0); ALBEDO = vec3(0.0); SPECULAR = 0.0; METALLIC = 0.0; }

float cel_lum(vec3 c_c) { return dot(c_c, vec3(0.2126, 0.7152, 0.0722)); }
float cel_schlick(float c_u) { float c_m = 1.0 - c_u; float c_m2 = c_m * c_m; return c_m2 * c_m2 * c_m; }

// The band's normal: the geometric one with cel_nmap of the normal map's detail.
vec3 cel_nb(vec3 c_n) { return normalize(mix(cel_gn, c_n, cel_nmap)); }
// The key's cast shadow hardened (directional lights); omni and spot as they are.
float cel_shadow(float c_att, bool c_dir) { return c_dir ? mix(c_att, smoothstep(0.42, 0.58, c_att), cel_rig.x) : c_att; }
// The lit band's coverage (the hard terminator) at n.l t.
float cel_lit(float c_t) {
	float c_hw = max(cel_band.y * cel_tune.x, 1e-4);
	return smoothstep(cel_band.x - c_hw, cel_band.x + c_hw, c_t);
}
// The ramp: lit band x half-tone x form, a multiplier of the light (rgb for the half-tone's tint).
vec3 cel_level(float c_t) {
	float c_z = cel_band.z * cel_tune.y;
	float c_full = c_z > 0.0 ? smoothstep(cel_band.x + c_z - cel_band.w, cel_band.x + c_z + max(cel_band.w, 1e-4), c_t) : 1.0;
	return mix(vec3(1.0), cel_mid.rgb, cel_mid.a * (1.0 - c_full)) * cel_lit(c_t) * mix(1.0, clamp(c_t, 0.0, 1.0), clamp(cel_form * cel_tune.w, 0.0, 1.0));
}
// The key's fill where its light doesn't reach (lit_sh: the lit band times the shadow), as DIFFUSE_LIGHT.
vec3 cel_fill_add(vec3 c_lc, float c_lit_sh, bool c_dir) {
	return c_dir ? cel_fill * (cel_lum(c_lc) * cel_rig.y * (1.0 - c_lit_sh) / PI) : vec3(0.0);
}
// The highlight: a disc of cel_spec.x degrees round N.H, in the light's color, as SPECULAR_LIGHT.
vec3 cel_spec_add(vec3 c_n, vec3 c_l, vec3 c_v, vec3 c_lc, float c_lit_sh, float c_rough, float c_metal, vec3 c_albedo, float c_spec, float c_spec_amount) {
	float c_k = cel_spec.z * (1.0 - smoothstep(0.55, 0.85, c_rough)) * clamp(c_spec * 2.0, 0.0, 1.0) * c_spec_amount * c_lit_sh;
	if (c_k <= 0.0) return vec3(0.0);
	float c_ang = degrees(acos(clamp(dot(c_n, normalize(c_v + c_l)), -1.0, 1.0)));
	float c_r = cel_spec.x * cel_tune.z;
	float c_s = 1.0 - smoothstep(c_r - cel_spec.y, c_r + max(cel_spec.y, 1e-3), c_ang);
	vec3 c_col = mix(vec3(cel_lum(c_lc)), c_lc, cel_spec.w) * mix(vec3(1.0), c_albedo, c_metal);
	return c_col * (c_s * c_k / PI);
}
// The stepped rim on the key's side of a form, as SPECULAR_LIGHT (half its albedo's tint).
vec3 cel_rim_add(vec3 c_nb, vec3 c_v, vec3 c_lc, float c_t, float c_sh, bool c_dir, vec3 c_albedo) {
#ifdef CEL_NO_RIM
	return vec3(0.0);
#else
	if (!c_dir || cel_rig.z <= 0.0) return vec3(0.0);
	float c_e = 1.0 - max(dot(c_nb, c_v), 0.0);
	float c_edge = 1.0 - cel_rig.w;
	float c_r = smoothstep(c_edge - 0.02, c_edge + 0.02, c_e) * smoothstep(-0.35, -0.15, c_t) * c_sh;
	return cel_rim * mix(vec3(1.0), c_albedo, 0.5) * (cel_lum(c_lc) * cel_rig.z * c_r / PI);
#endif
}

// Godot 4.5.1's built-in light for one light (scene_forward_lights_inc.glsl light_compute, not LIGHT_CODE_USED):
// Burley diffuse, Schlick-GGX specular, f0 = mix(0.16 specular^2, albedo, metallic), the BACKLIGHT transmission
// and RIM. (Not reproduced: the directional light's angular size A (~0 here) and the specular's energy
// compensation (~1 for rough dielectrics), neither available to light().)
void cel_today(vec3 c_n, vec3 c_l, vec3 c_v, vec3 c_lc, float c_att, bool c_dir, vec3 c_albedo, float c_metal, float c_rough, float c_spec,
		float c_spec_amount, vec3 c_backlight, float c_rim, float c_rim_tint, inout vec3 c_dl, inout vec3 c_sl) {
	float c_nl = min(dot(c_n, c_l), 1.0);
	float c_cnv = max(dot(c_n, c_v), 1e-4);
	if (c_rim > 0.0) {
		float c_rl = pow(max(1e-4, 1.0 - c_cnv), max(0.0, (1.0 - c_rough) * 16.0));
		c_dl += c_rl * c_rim * mix(vec3(1.0), c_albedo, c_rim_tint) * c_lc;
	}
	if (c_dir || c_att > 1.175494351e-38) {
		float c_cnl = max(c_nl, 0.0);
		vec3 c_h = normalize(c_v + c_l);
		float c_clh = clamp(dot(c_l, c_h), 0.0, 1.0);
		if (c_metal < 1.0) {
			float c_fd90m1 = 2.0 * c_clh * c_clh * c_rough - 0.5;
			float c_d = (1.0 / PI) * (1.0 + c_fd90m1 * cel_schlick(c_cnv)) * (1.0 + c_fd90m1 * cel_schlick(c_cnl)) * c_cnl;
			c_dl += c_lc * c_d * c_att;
			c_dl += c_lc * (vec3(1.0 / PI) - c_d) * c_backlight * c_att;
		}
		if (c_rough > 0.0) {
			float c_cnh = clamp(dot(c_n, c_h), 0.0, 1.0);
			float c_a = c_rough * c_rough;
			float c_aa = c_cnh * c_a;
			float c_k = c_a / (1.0 - c_cnh * c_cnh + c_aa * c_aa);
			float c_dd = c_k * c_k * (1.0 / PI);
			float c_g = 0.5 / mix(2.0 * c_cnl * c_cnv, c_cnl + c_cnv, c_a);
			vec3 c_f0 = mix(vec3(0.16 * c_spec * c_spec), c_albedo, c_metal);
			float c_f90 = clamp(dot(c_f0, vec3(50.0 * 0.33)), c_metal, 1.0);
			vec3 c_f = c_f0 + (c_f90 - c_f0) * cel_schlick(c_clh);
			c_sl += c_cnl * c_dd * c_f * c_g * c_lc * c_att * c_spec_amount;
		}
	}
}

// The cel model for one light, t = the band's n.l (the caller may wrap it).
void cel_shade(vec3 c_n, vec3 c_nb, float c_t, vec3 c_l, vec3 c_v, vec3 c_lc, float c_att, bool c_dir, vec3 c_albedo, float c_metal, float c_rough,
		float c_spec, float c_spec_amount, vec3 c_backlight, float c_rim, float c_rim_tint, inout vec3 c_dl, inout vec3 c_sl) {
	float c_sh = cel_shadow(c_att, c_dir);
	vec3 c_lv = cel_level(c_t);
	float c_lit_sh = cel_lit(c_t) * c_sh;
	if (c_metal < 1.0) {
		c_dl += c_lc * c_lv * (c_sh / PI);
		c_dl += c_lc * (vec3(1.0) - c_lv) * c_backlight * (c_sh / PI);
	}
	c_dl += cel_fill_add(c_lc, c_lit_sh, c_dir);
	if (c_rim > 0.0) {
		// (Godot's RIM, stepped: whole past its half-way)
		float c_rl = pow(max(1e-4, 1.0 - max(dot(c_nb, c_v), 1e-4)), max(0.0, (1.0 - c_rough) * 16.0));
		c_dl += smoothstep(0.45, 0.55, c_rl) * c_rim * c_lc * mix(vec3(1.0), c_albedo, c_rim_tint);
	}
	c_sl += cel_spec_add(c_n, c_l, c_v, c_lc, c_lit_sh, c_rough, c_metal, c_albedo, c_spec, c_spec_amount);
	c_sl += cel_rim_add(c_nb, c_v, c_lc, c_t, c_sh, c_dir, c_albedo);
}

// The debug views in light(): true when one is on (the caller then writes nothing else).
// band: the key's band level x its hardened shadow as gray (SPECULAR_LIGHT; fragment() zeroed the albedo).
bool cel_dbg_light(vec3 c_nb, float c_t, float c_att, bool c_dir, inout vec3 c_sl) {
	if (cel_dbg < 0.5) return false;
	if (cel_dbg < 1.5 && c_dir) c_sl += vec3(dot(cel_level(c_t), vec3(1.0 / 3.0)) * cel_shadow(c_att, c_dir));
	return true;
}

#ifndef CEL_OWN_LIGHT
void light() {
	vec3 c_nb = cel_nb(NORMAL);
	float c_t = dot(c_nb, LIGHT);
	vec3 c_sl = vec3(0.0);
	if (cel_dbg_light(c_nb, c_t, ATTENUATION, LIGHT_IS_DIRECTIONAL, c_sl)) { SPECULAR_LIGHT += c_sl; }
	else {
		vec3 c_da = vec3(0.0), c_sa = vec3(0.0), c_db = vec3(0.0), c_sb = vec3(0.0);
		if (cel_on < 1.0) cel_today(NORMAL, LIGHT, VIEW, LIGHT_COLOR, ATTENUATION, LIGHT_IS_DIRECTIONAL, ALBEDO, METALLIC, ROUGHNESS,
				cel_mat.x, SPECULAR_AMOUNT, BACKLIGHT, cel_mat.y, cel_mat.z, c_da, c_sa);
		if (cel_on > 0.0) cel_shade(NORMAL, c_nb, c_t, LIGHT, VIEW, LIGHT_COLOR, ATTENUATION, LIGHT_IS_DIRECTIONAL, ALBEDO, METALLIC, ROUGHNESS,
				cel_mat.x, SPECULAR_AMOUNT, BACKLIGHT, cel_mat.y, cel_mat.z, c_db, c_sb);
		DIFFUSE_LIGHT += mix(c_da, c_db, cel_on);
		SPECULAR_LIGHT += mix(c_sa, c_sb, cel_on);
	}
}
#endif
