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
//       #define CEL_MID / CEL_FORM / CEL_SPEC / CEL_NMAP   the material defaults of cel_mid, cel_form, cel_spec, cel_nmap
//       #define CEL_EXACT_ROUGH    the default light() lights by the roughness fragment() wrote, not the tagged one
//                          (cel_mat.w; the tag's step is up to 0.04 rougher): today's look exact at cel_on 0
//       #define CEL_CLEARCOAT      the shader writes CLEARCOAT: the default light()'s A side adds Godot's clearcoat
//                          (cel_today_cc; a user light() gets none from the engine); the B side has none (L1 B1b)
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
//   cel_rim_k the stepped rim's share (0: none; kit foliage, whose card normals are no silhouette)
//   cel_ink   the ink class (0 full: silhouette + creases, 1 silhouette only, 2 none, 3 full = unconverted)
// GLOBALS (project.godot [shader_globals]; Atmosphere.cs sets them from the preset):
//   cel_on 0..1 (0 = today exactly), cel_rig (x cast-shadow hardness: 0 PCF, 1 smoothstep(0.42, 0.58) on the key's
//   shadow; y the key's fill in the shadow band 0..0.25, tinted cel_fill, at the key's luminance; z rim strength;
//   w rim width in 1-n.v), cel_fill rgb, cel_rim rgb (linear), cel_tune (multipliers: band half-width, half-tone
//   width, spec radius, form; 1 = as authored), cel_dbg (0 off, 1 band: the key's band level as gray, 2 ink: the
//   class unlit, 0 white 1 yellow 2 blue 3 red; 3 skin: white where the shader defines CEL_SKIN, else black, the
//   skin mask for measuring; --cel-dbg skin).
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

#ifdef CEL_SKIN
#define CEL_SKIN_V 1.0
#else
#define CEL_SKIN_V 0.0
#endif
#ifndef CEL_TRANS_WRAP
#define CEL_TRANS_WRAP 0.25
#endif
#ifndef CEL_TRANS_CAP
#define CEL_TRANS_CAP 0.15
#endif
#ifndef CEL_SOFT_TURN
#define CEL_SOFT_TURN 0.5
#endif
#ifndef CEL_INK
#define CEL_INK 0
#endif
#ifndef CEL_BAND
#define CEL_BAND vec4(0.0, 0.06, 0.2, 0.05)
#endif
#ifndef CEL_MID
#define CEL_MID vec4(0.55, 0.55, 0.6, 1.0)
#endif
#ifndef CEL_FORM
#define CEL_FORM 0.3
#endif
#ifndef CEL_SPEC
#define CEL_SPEC vec4(9.0, 1.5, 1.0, 0.85)
#endif
#ifndef CEL_NMAP
#define CEL_NMAP 0.35
#endif

group_uniforms cel;
uniform vec4 cel_band = CEL_BAND;
uniform vec4 cel_mid : source_color = CEL_MID;
uniform float cel_form : hint_range(0.0, 1.0) = CEL_FORM;
uniform vec4 cel_spec = CEL_SPEC;
uniform float cel_nmap : hint_range(0.0, 1.0) = CEL_NMAP;
uniform int cel_ink : hint_range(0, 3) = CEL_INK;
uniform float cel_rim_k : hint_range(0.0, 1.0) = 1.0;   // (the stepped rim's share: 0 none, card normals; L1 B1c)
// (L1 W2, B2) the class's albedo control (materials.json "albedo"; never a repaint): x a target Oklab L and y how far the
// albedo's L is pulled to it (0 none), z a cap on its L, w its chroma's scale. (0, 0, 1, 1): the albedo as painted.
uniform vec4 cel_alb = vec4(0.0, 0.0, 1.0, 1.0);
// (L1 l9 PACK2, B2) and its hue (materials.json albedo_ctl "hue": [h, C, pull]): xy the target's Oklab a, b (C at h), z how far
// the albedo's a, b (after w's scale) are pulled to it (0 none): the pack's fur cold neutral FROM target 09, whatever its paint.
uniform vec4 cel_alb_hue = vec4(0.0);
group_uniforms;

global uniform float cel_on;
global uniform vec4 cel_rig;
global uniform vec3 cel_fill;
global uniform vec3 cel_sky;   // (L1 l9 DAY, rule 6: the sky's hue at luminance 1, for the metal's broad band; the fill's tinted it magenta at 08)
global uniform vec3 cel_rim;
global uniform vec4 cel_tune;
global uniform float cel_dbg;
// (L1 B4) The moon through the canopy (bible rule 9): cel_key xyz the world key's way toward the light, w the dapple's
// strength (0: none); cel_dapple x how much of the sky the crowns close where the canopy is whole, y the crowns' world
// height, z the leaf cookie's tile (m), w the cover's floor (S2b-N3: the canopy closes at least this much of the sky
// everywhere, so an arena's clearing too reads as big moonlit patches on deep shade, target 09); cel_canopy the canopy's mask over the zone (from the trees' placement,
// CanopyCookie), cel_canopy_r its world origin (xy) and 1/size (zw); cel_cookie the leaf shapes (a rank per leaf cluster).
global uniform vec4 cel_key;
global uniform vec4 cel_dapple;
global uniform vec4 cel_canopy_r;
// (L1 lead 11, R3 one shade) cel_oneshade x: the key's cast shadow as a LEVEL, the key's shadow opacity (rigs.json key.shadow on
// a rig with "shadow_level": true): the raw shadow is hardened first, then the opacity applied, so a cast shadow keeps
// exactly 1 - x of the key, and where the canopy's dapple falls too the darker one stands (min), never the product; the
// dapple's strength is the same number (Rigs.Lit), so both land on one shade. 0: the rig has not opted in (the day rigs,
// the other nights, a camera rig): the attenuation hardened after the opacity (a switch round 0.5), times the dapple, as
// before. y: the dapple's edge width (screen pixels; under 1: one pixel, as before).
global uniform vec4 cel_oneshade;
global uniform sampler2D cel_cookie : filter_linear_mipmap, repeat_enable;
global uniform sampler2D cel_canopy : filter_linear, repeat_disable;
// (L1 W2) Her light over the moon (bible rules 1, 3, 4: her pool is the night's warm lit mass, so within its reach the moon
// gives way to it): cel_ember xyz her light's world point, w its reach (m, the omni's range; 0: none); cel_give x how much of
// the moon's key, its fill and its rim give way at the pool's heart, y how much of the sky's light (the ambient, through AO),
// z and w where the giving starts to fade and where it is gone (metres from her light, smooth between; S2b-N2: was shares
// of the reach, which gave the arena's pool twice the Low Ford's). Set by the rig
// (rigs.json "ember_give"; Atmosphere.SetCel) and her light (PlayerView, each frame). A shader may define CEL_NO_GIVE.
global uniform vec4 cel_ember;
global uniform vec4 cel_give;
// (L1 lead 9, NIGHT2) The zone's fires and lamps over the moon (bible rule 3; T01, T05, T06: each throws its own warm pool and
// the moon gives way inside it, as to her light): cel_fire0-2 the nearest lit warm lights' world points, w their range (m;
// 0: none; ZoneView.CelFires, each frame); cel_fire_give x the share of the moon's key, fill and rim given up at a source's
// foot, y the sky's, z and w where the giving starts to fade and where it is gone (shares of the range, on the ground).
// Set by the rig (rigs.json "fire_give"; Atmosphere.SetCel). A shader with CEL_NO_GIVE skips it with her light's.
global uniform vec4 cel_fire_give;
global uniform vec4 cel_fire0;
global uniform vec4 cel_fire1;
global uniform vec4 cel_fire2;
// (L1 lead 9, B1) Her pool as light, a ramp in metres from her light's foot (judge 1, verdict section 3, FROM targets 09 and
// 12: no plateau, no step, no ring; L falling from 0.5 m on, chroma peaking at the gold core and dying outward through
// orange and dusk into the moon's ground): an omni light of her color whose level and color at a distance r on the ground
// (horizontal, from the point under the light) come from the rig's table (rigs.json "ember_pool": stops of r, level,
// color; Atmosphere builds cel_pool_ramp from it), the same in every place. cel_pool her light's color (linear, largest
// channel 1; how the cel model knows her light among the others) and w its fall (OmniAttenuation; 0: off); cel_pool_band
// x the ramp's last stop (m; 0: no ramp, her light as Godot falls it), y the core's level (her gear takes the ramp's shape
// at that level, CEL_POOL_PLAIN), z and w how much of the canopy's dapple stays in her pool at its edge and at its core (light adds to the ground, so the moon's
// leaf shapes run on through the pool, its lit patches hotter and its shade darker: target 09). cel_pool_ramp rgb the
// light's level x color over her light's energy at r, a the moon's give-way there (0..1; cel_give x and y scale it).
global uniform vec4 cel_pool;
global uniform vec4 cel_pool_band;
global uniform sampler2D cel_pool_ramp : filter_linear, repeat_disable;

// (fragment() to light(): the geometric normal, and x SPECULAR, y RIM, z RIM_TINT, w ROUGHNESS before the tag)
// (L1 B4r2) cel_gn's length is 1 + the key's share through the canopy here (cel_dap(): 1 open sky): packed, not a varying
// of its own, because a shader at Godot's 32 varyings (KitLook's roofs) would fail to compile on one more.
// (L1 W2: and the moon's share after her light, cel_gv(): length = 1.01 + 0.98 dapple + 2 round(1000 share); fragment() to
// light() is not interpolated, so the packing is exact to about 1e-4)
varying vec3 cel_gn;
varying vec4 cel_mat;
#ifdef CEL_CLEARCOAT
varying vec2 cel_cc;   // (CLEARCOAT, CLEARCOAT_ROUGHNESS)
#endif

// (L1 W2) The class's albedo control on a linear albedo (cel_alb), in Oklab; at cel_on 0 the albedo as it is.
vec3 cel_alb_apply(vec3 c_c) {
	if (cel_on <= 0.0 || (cel_alb.y <= 0.0 && cel_alb.z >= 1.0 && cel_alb.w == 1.0 && cel_alb_hue.z <= 0.0)) return c_c;
	vec3 c_lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
		vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c_c, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	vec3 c_o = mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662),
		vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * c_lms;
	float c_l = min(mix(c_o.x, cel_alb.x, cel_alb.y), cel_alb.z);
	vec2 c_ab = mix(c_o.yz * cel_alb.w, cel_alb_hue.xy, cel_alb_hue.z);
	vec3 c_m = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480))
		* vec3(c_l, c_ab);
	c_m = c_m * c_m * c_m;
	vec3 c_r = mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147),
		vec3(0.2309699292, -0.3413193965, 1.7076147010)) * c_m;
	return mix(c_c, clamp(c_r, vec3(0.0), vec3(1.0)), cel_on);
}
#ifdef CEL_OWN_ALB
#define CEL_FRAG_ALB
#else
#define CEL_FRAG_ALB ALBEDO = cel_alb_apply(ALBEDO)
#endif

float cel_tag(float c_r, int c_ink) {
	return (clamp(round(c_r * 31.0), 0.0, 31.0) * 4.0 + float(clamp(c_ink, 0, 3))) / 127.0;
}
vec3 cel_ink_rgb(int c_ink) {
	return c_ink == 0 ? vec3(1.0) : c_ink == 1 ? vec3(1.0, 0.85, 0.0) : c_ink == 2 ? vec3(0.0, 0.25, 1.0) : vec3(1.0, 0.0, 0.0);
}

#ifdef CEL_BUILTIN_RIM
#define CEL_FRAG_RIM cel_mat = vec4(SPECULAR, RIM, RIM_TINT, ROUGHNESS)
#else
#define CEL_FRAG_RIM cel_mat = vec4(SPECULAR, 0.0, 0.0, ROUGHNESS)
#endif
#ifdef CEL_CLEARCOAT
#define CEL_FRAG_MAT CEL_FRAG_RIM; cel_cc = vec2(CLEARCOAT, CLEARCOAT_ROUGHNESS)
#else
#define CEL_FRAG_MAT CEL_FRAG_RIM
#endif
// The last statement of fragment(): see the header.
// (L1 B4) The key's light through the canopy at a world point: the point carried up the key's way to the crowns' height,
// the canopy's cover there, and the leaf cookie's cluster ranks under it: shade where a cluster's rank is under the cover,
// two values (rule 9), the edge one pixel wide.
float cel_dapple_at(vec3 c_wp) {
	if (cel_key.w <= 0.0) return 1.0;
	vec2 c_p = c_wp.xz + cel_key.xz * (max(cel_dapple.y - c_wp.y, 0.0) / max(cel_key.y, 0.2));
	float c_cov = max(texture(cel_canopy, (c_p - cel_canopy_r.xy) * cel_canopy_r.zw).r, cel_dapple.w) * cel_dapple.x;
	if (c_cov <= 0.004) return 1.0;
	float c_e = max(cel_oneshade.y, 1.0);
	float c_f = texture(cel_cookie, c_p / cel_dapple.z, log2(c_e)).r;
	float c_w = fwidth(c_f) * 0.5 * c_e + 0.01;
	return mix(1.0, smoothstep(c_cov - c_w, c_cov + c_w, c_f), cel_key.w);
}
// (L1 lead 9, B1) Her pool's ramp at r metres from her light's foot (past its last stop: the last stop's).
vec4 cel_pool_at(float c_r) {
	return texture(cel_pool_ramp, vec2((clamp(c_r / cel_pool_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.5));
}
// (L1 W2) The moon's share at a world point under her light: 1 out of its reach, 1 - cel_give.x (key) or .y (sky) at its heart.
float cel_give_at(vec3 c_wp, float c_k) {
#ifdef CEL_NO_GIVE
	return 1.0;
#else
	if (cel_ember.w <= 0.0 || c_k <= 0.0) return 1.0;
	// (L1 lead 10, NIGHT: under the ramp the moon gives way on the ground from her light's foot, wholly inside cel_give z (m)
	// and none past w, the ramp's warm stops and its tail (rigs.json ember_give). Tied to the ramp's level (lead 9: a = level
	// over the core's, half the moon back at 1 m), a saturated moon came back inside the gold and drew the pool pink.)
	if (cel_pool_band.x > 0.0) return 1.0 - c_k * cel_on * (1.0 - smoothstep(cel_give.z, max(cel_give.w, cel_give.z + 1e-3), length(c_wp.xz - cel_ember.xz)));
	float c_d = length(c_wp - cel_ember.xyz);
	return 1.0 - c_k * cel_on * (1.0 - smoothstep(cel_give.z, max(cel_give.w, cel_give.z + 1e-3), c_d));
#endif
}
// (L1 lead 9, NIGHT2) The moon's share at a world point under the zone's fires and lamps (the least of the nearest three).
float cel_fire_one(vec2 c_p, vec4 c_f, float c_k) {
	if (c_f.w <= 0.0) return 1.0;
	float c_d = length(c_p - c_f.xz) / c_f.w;
	return 1.0 - c_k * (1.0 - smoothstep(cel_fire_give.z, max(cel_fire_give.w, cel_fire_give.z + 1e-3), c_d));
}
float cel_fires_at(vec3 c_wp, float c_k) {
#ifdef CEL_NO_GIVE
	return 1.0;
#else
	if (c_k <= 0.0 || cel_on <= 0.0) return 1.0;
	return min(cel_fire_one(c_wp.xz, cel_fire0, c_k * cel_on), min(cel_fire_one(c_wp.xz, cel_fire1, c_k * cel_on), cel_fire_one(c_wp.xz, cel_fire2, c_k * cel_on)));
#endif
}
float cel_pack(vec3 c_wp) { return 1.01 + 0.98 * cel_dapple_at(c_wp) + 2.0 * round(1000.0 * cel_give_at(c_wp, cel_give.x) * cel_fires_at(c_wp, cel_fire_give.x)); }
#define CEL_FRAGMENT cel_gn = normalize(NORMAL) * cel_pack((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz); AO *= cel_give_at((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, cel_give.y) * cel_fires_at((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, cel_fire_give.y); CEL_FRAG_ALB; CEL_FRAG_MAT; ROUGHNESS = cel_tag(ROUGHNESS, cel_ink); if (cel_dbg > 0.5) { EMISSION = cel_dbg > 2.5 ? vec3(CEL_SKIN_V) : cel_dbg > 1.5 ? cel_ink_rgb(cel_ink) : vec3(0.0); ALBEDO = vec3(0.0); SPECULAR = 0.0; METALLIC = 0.0; }

float cel_lum(vec3 c_c) { return dot(c_c, vec3(0.2126, 0.7152, 0.0722)); }
float cel_schlick(float c_u) { float c_m = 1.0 - c_u; float c_m2 = c_m * c_m; return c_m2 * c_m2 * c_m; }

// The band's normal: the geometric one with cel_nmap of the normal map's detail.
vec3 cel_nb(vec3 c_n) { return normalize(mix(normalize(cel_gn), c_n, cel_nmap)); }
float cel_gq() { return floor((length(cel_gn) - 1.0) * 0.5); }
// (the canopy's dapple times the moon's share after her light: the key's light here)
float cel_dap() { float c_q = cel_gq(); return clamp((length(cel_gn) - 1.01 - 2.0 * c_q) / 0.98, 0.0, 1.0) * (c_q * 0.001); }
// (the moon's share after her light alone: the key's fill)
float cel_gv() { return clamp(cel_gq() * 0.001, 0.0, 1.0); }
// The key's cast shadow hardened (directional lights); omni and spot as they are.
// (L1 B4: and the canopy's dapple, cel_dap, on the directional key)
// (L1 lead 11, R3: under cel_oneshade.x the shadow is a level and the dapple the same shade: see cel_oneshade)
float cel_shadow(float c_att, bool c_dir) {
	if (!c_dir) return c_att;
	if (cel_oneshade.x <= 0.0) return mix(c_att, smoothstep(0.42, 0.58, c_att), cel_rig.x) * cel_dap();
	float c_q = cel_gq();
	float c_raw = clamp(1.0 - (1.0 - c_att) / cel_oneshade.x, 0.0, 1.0);
	float c_cast = 1.0 - cel_oneshade.x * (1.0 - mix(c_raw, smoothstep(0.42, 0.58, c_raw), cel_rig.x));
	return min(c_cast, clamp((length(cel_gn) - 1.01 - 2.0 * c_q) / 0.98, 0.0, 1.0)) * (c_q * 0.001);
}
// The lit band's coverage (the hard terminator) at n.l t.
float cel_lit(float c_t) {
	float c_hw = max(cel_band.y * cel_tune.x, 1e-4);
	return smoothstep(cel_band.x - c_hw, cel_band.x + c_hw, c_t);
}
// The ramp: lit band x half-tone x form, a multiplier of the light (rgb for the half-tone's tint).
// (cel_level_mid: the same with the half-tone's tint given (rgb its level, a how much): hair's own hue; L1 B1b)
vec3 cel_level_mid(float c_t, vec4 c_mid) {
	float c_z = cel_band.z * cel_tune.y;
	float c_full = c_z > 0.0 ? smoothstep(cel_band.x + c_z - cel_band.w, cel_band.x + c_z + max(cel_band.w, 1e-4), c_t) : 1.0;
	return mix(vec3(1.0), c_mid.rgb, c_mid.a * (1.0 - c_full)) * cel_lit(c_t) * mix(1.0, clamp(c_t, 0.0, 1.0), clamp(cel_form * cel_tune.w, 0.0, 1.0));
}
vec3 cel_level(float c_t) { return cel_level_mid(c_t, cel_mid); }
// The light through a form (BACKLIGHT) under the cel model: a thin edge on the shade side of the terminator (CEL_TRANS_WRAP
// of n.l past it) and the thin parts (c_thin 0..1), never across the shade band, which keeps the fill's cool tint; capped at
// CEL_TRANS_CAP of the light. As a multiplier of the light (L1 B1c: rules 2 and 5, MB1's cool colored shade; before it the
// shade band took (1 - level) x BACKLIGHT whole, lifting her front to near the lit level with the key behind her).
// (cel_trans_w: where it shows, 0..1, for a shader that multiplies by BACKLIGHT itself, then by cel_trans_k's cap)
float cel_trans_w(float c_t, float c_thin) {
	float c_hw = max(cel_band.y * cel_tune.x, 1e-4);
	float c_edge = smoothstep(cel_band.x - c_hw - CEL_TRANS_WRAP, cel_band.x - c_hw, c_t);
	return max(c_edge, clamp(c_thin, 0.0, 1.0)) * (1.0 - cel_lit(c_t));
}
float cel_trans_k(vec3 c_backlight) { return min(1.0, CEL_TRANS_CAP / max(max(c_backlight.r, max(c_backlight.g, c_backlight.b)), 1e-4)); }
vec3 cel_trans(vec3 c_backlight, float c_t, float c_thin) { return c_backlight * (cel_trans_k(c_backlight) * cel_trans_w(c_t, c_thin)); }
// An omni or spot light on a form it should model, not flatten (skin): Lambert's gradient, no flat band, the half-tone's
// tint over its first CEL_SOFT_TURN of n.l; never brighter than Lambert (L1 B1c: rules 5 and 11; the campfire's banded
// n.l lit her whole front at one level).
vec3 cel_level_soft(float c_t) {
	return mix(vec3(1.0), cel_mid.rgb, cel_mid.a * (1.0 - smoothstep(0.0, CEL_SOFT_TURN, c_t))) * clamp(c_t, 0.0, 1.0);
}
// The key's fill where its light doesn't reach (lit_sh: the lit band times the shadow), as DIFFUSE_LIGHT.
vec3 cel_fill_add(vec3 c_lc, float c_lit_sh, bool c_dir) {
	return c_dir ? cel_fill * (cel_lum(c_lc) * cel_rig.y * cel_gv() * (1.0 - c_lit_sh) / PI) : vec3(0.0);
}
// The highlight: a disc of cel_spec.x degrees round N.H, in the light's color, as SPECULAR_LIGHT.
// (cel_spec_disc: the same disc by its own cel_spec-style numbers, in the color given (before a metal's tint): a second
// band (metal's broad one in the sky's hue), or a highlight per material kind; L1 B1b)
vec3 cel_spec_disc(vec4 c_sp, vec3 c_hc, vec3 c_n, vec3 c_l, vec3 c_v, float c_lit_sh, float c_rough, float c_metal, vec3 c_albedo, float c_spec, float c_spec_amount) {
	float c_k = c_sp.z * (1.0 - smoothstep(0.55, 0.85, c_rough)) * clamp(c_spec * 2.0, 0.0, 1.0) * c_spec_amount * c_lit_sh;
	if (c_k <= 0.0) return vec3(0.0);
	float c_ang = degrees(acos(clamp(dot(c_n, normalize(c_v + c_l)), -1.0, 1.0)));
	float c_r = c_sp.x * cel_tune.z;
	float c_s = 1.0 - smoothstep(c_r - c_sp.y, c_r + max(c_sp.y, 1e-3), c_ang);
	return c_hc * mix(vec3(1.0), c_albedo, c_metal) * (c_s * c_k / PI);
}
vec3 cel_spec_add(vec3 c_n, vec3 c_l, vec3 c_v, vec3 c_lc, float c_lit_sh, float c_rough, float c_metal, vec3 c_albedo, float c_spec, float c_spec_amount) {
	return cel_spec_disc(cel_spec, mix(vec3(cel_lum(c_lc)), c_lc, cel_spec.w), c_n, c_l, c_v, c_lit_sh, c_rough, c_metal, c_albedo, c_spec, c_spec_amount);
}
// The stepped rim on the key's side of a form, as SPECULAR_LIGHT (half its albedo's tint).
vec3 cel_rim_add(vec3 c_nb, vec3 c_v, vec3 c_lc, float c_t, float c_sh, bool c_dir, vec3 c_albedo) {
#ifdef CEL_NO_RIM
	return vec3(0.0);
#else
	if (!c_dir || cel_rig.z * cel_rim_k <= 0.0) return vec3(0.0);
	float c_e = 1.0 - max(dot(c_nb, c_v), 0.0);
	float c_edge = 1.0 - cel_rig.w;
	float c_r = smoothstep(c_edge - 0.02, c_edge + 0.02, c_e) * smoothstep(-0.35, -0.15, c_t) * c_sh;
	return cel_rim * mix(vec3(1.0), c_albedo, 0.5) * (cel_lum(c_lc) * cel_rig.z * cel_rim_k * c_r / PI);
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

#ifdef CEL_CLEARCOAT
// Godot 4.5.1's clearcoat for one light (light_compute's LIGHT_CLEARCOAT_USED: on the geometric normal, its N.L the
// mapped normal's), as SPECULAR_LIGHT; a shader with a light() gets none from the engine.
vec3 cel_today_cc(vec3 c_n, vec3 c_l, vec3 c_v, vec3 c_lc, float c_att, bool c_dir, float c_spec_amount) {
	if (cel_cc.x <= 0.0 || !(c_dir || c_att > 1.175494351e-38)) return vec3(0.0);
	vec3 c_g = normalize(cel_gn);
	vec3 c_h = normalize(c_v + c_l);
	float c_lh = clamp(dot(c_l, c_h), 0.0, 1.0);
	float c_gh = clamp(dot(c_g, c_h), 0.0, 1.0);
	float c_r = mix(0.001, 0.1, cel_cc.y);
	float c_a = c_gh * c_r;
	float c_k = c_r / (1.0 - c_gh * c_gh + c_a * c_a);
	float c_d = c_k * c_k * (1.0 / PI);
	float c_gg = 0.25 / (c_lh * c_lh + 1e-4);
	float c_f = mix(0.04, 1.0, cel_schlick(c_lh));
	return vec3(cel_cc.x * c_gg * c_f * c_d * max(min(dot(c_n, c_l), 1.0), 0.0)) * c_lc * c_att * c_spec_amount;
}
#endif

// (L1 lead 9, B1) Her light painted as light (cel_pool above): an omni light of her color, its distance from the light read
// back from its attenuation (Godot's omni fall: (1 - u^4)^2 (u r)^-decay, u = d / r; her light casts no shadow, so
// ATTENUATION is the fall alone), the point found along the light's way (c_lw: world, toward the light), then the ramp's
// level and color at that point's distance on the ground from the light's foot, over her light's energy (her flicker and
// her flare carry through), and the canopy's leaf shapes kept in it. Called by light() before cel_shade. (Retired: lead 8's
// three steps, their value-noise patches and the gold and red tints, cel_pool_tint/lv/out and rigs.json "ember_edge".)
void cel_pool_paint(inout vec3 c_lc, inout float c_att, vec3 c_lw) {
	if (cel_on <= 0.0 || cel_pool.w <= 0.0 || cel_pool_band.x <= 0.0 || cel_ember.w <= 0.0 || c_att <= 0.0) return;
	float c_m = max(c_lc.r, max(c_lc.g, max(c_lc.b, 1e-6)));
	if (dot(abs(c_lc / c_m - cel_pool.rgb), vec3(1.0)) > 0.02) return;
	float c_r = cel_ember.w, c_dec = cel_pool.w;
	float c_lo = 0.0, c_hi = 1.0;
	for (int i = 0; i < 16; i++) {
		float c_u = 0.5 * (c_lo + c_hi);
		float c_q = c_u * c_u; c_q *= c_q; c_q = max(1.0 - c_q, 0.0);
		float c_f = c_q * c_q * pow(max(c_u * c_r, 1e-4), -c_dec);
		if (c_f > c_att) c_lo = c_u; else c_hi = c_u;
	}
	vec3 c_wp = cel_ember.xyz - normalize(c_lw) * (0.5 * (c_lo + c_hi) * c_r);
	// (L1 lead 11, R4: a broken end. Under a leaf (the key's dapple, packed in cel_gn: 1 - cel_key.w under a leaf, 1 open; only
	// where fragment() packed it and the moon is back) the ramp is read further out, so her pool reaches cel_oneshade.z of its
	// radius less far there: its end is scalloped by the leaf shapes, not a compass circle, and its heart is untouched.)
	float c_leaf = 0.0;
	if (cel_key.w > 0.0 && cel_gq() >= 1.0) {
		float c_dr = clamp((length(cel_gn) - 1.01 - 2.0 * cel_gq()) / 0.98, 0.0, 1.0);
		// (times the moon's share here: the leaf shapes come in with the moon, from nothing where it has given way)
		c_leaf = (1.0 - clamp((c_dr - (1.0 - cel_key.w)) / cel_key.w, 0.0, 1.0)) * clamp(cel_gv(), 0.0, 1.0);
	}
	vec4 c_rp = cel_pool_at(length(c_wp.xz - cel_ember.xz) / max(1.0 - cel_oneshade.z * c_leaf, 0.2));
	vec3 c_ramp = c_rp.rgb;
#ifdef CEL_POOL_PLAIN
	c_ramp /= max(cel_pool_band.y, 1e-3);
#endif
	c_lc = c_m * c_ramp;
	c_att = 1.0;
	// (lead 9's under-leaf cut of her light, for a rig not yet rebuilt (night_play: ember_pool[0..1]). The rebuilt pool
	// (arena_night, R4) has none (0, 0): the fire is not cut by the moon's leaves; the moon comes back under it (ember_give)
	// and its two blues, leaf shade and all, show through the outer band.)
	if (cel_pool_band.z > 0.0) c_att = 1.0 - mix(cel_pool_band.z, cel_pool_band.w, c_rp.a) * cel_key.w * c_leaf;
}

// The cel model for one light, t = the band's n.l (the caller may wrap it).
void cel_shade(vec3 c_n, vec3 c_nb, float c_t, vec3 c_l, vec3 c_v, vec3 c_lc, float c_att, bool c_dir, vec3 c_albedo, float c_metal, float c_rough,
		float c_spec, float c_spec_amount, vec3 c_backlight, float c_rim, float c_rim_tint, inout vec3 c_dl, inout vec3 c_sl) {
	float c_sh = cel_shadow(c_att, c_dir);
	vec3 c_lv = cel_level(c_t);
	float c_lit_sh = cel_lit(c_t) * c_sh;
	if (c_metal < 1.0) {
		c_dl += c_lc * c_lv * (c_sh / PI);
		c_dl += c_lc * cel_trans(c_backlight, c_t, 0.0) * (c_sh / PI);
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
#ifdef CEL_EXACT_ROUGH
	float c_rough = cel_mat.w;
#else
	float c_rough = ROUGHNESS;
#endif
	vec3 c_nb = cel_nb(NORMAL);
	float c_t = dot(c_nb, LIGHT);
	vec3 c_sl = vec3(0.0);
	if (cel_dbg_light(c_nb, c_t, ATTENUATION, LIGHT_IS_DIRECTIONAL, c_sl)) { SPECULAR_LIGHT += c_sl; }
	else {
		vec3 c_da = vec3(0.0), c_sa = vec3(0.0), c_db = vec3(0.0), c_sb = vec3(0.0);
		if (cel_on < 1.0) {
			cel_today(NORMAL, LIGHT, VIEW, LIGHT_COLOR, ATTENUATION, LIGHT_IS_DIRECTIONAL, ALBEDO, METALLIC, c_rough,
				cel_mat.x, SPECULAR_AMOUNT, BACKLIGHT, cel_mat.y, cel_mat.z, c_da, c_sa);
#ifdef CEL_CLEARCOAT
			c_sa += cel_today_cc(NORMAL, LIGHT, VIEW, LIGHT_COLOR, ATTENUATION, LIGHT_IS_DIRECTIONAL, SPECULAR_AMOUNT);
#endif
		}
		vec3 c_plc = LIGHT_COLOR; float c_patt = ATTENUATION;
		if (!LIGHT_IS_DIRECTIONAL) cel_pool_paint(c_plc, c_patt, (INV_VIEW_MATRIX * vec4(LIGHT, 0.0)).xyz);
		if (cel_on > 0.0) cel_shade(NORMAL, c_nb, c_t, LIGHT, VIEW, c_plc, c_patt, LIGHT_IS_DIRECTIONAL, ALBEDO, METALLIC, c_rough,
				cel_mat.x, SPECULAR_AMOUNT, BACKLIGHT, cel_mat.y, cel_mat.z, c_db, c_sb);
		DIFFUSE_LIGHT += mix(c_da, c_db, cel_on);
		SPECULAR_LIGHT += mix(c_sa, c_sb, cel_on);
	}
}
#endif
