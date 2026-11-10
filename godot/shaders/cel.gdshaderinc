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
//       #define CEL_S3             a STANDING form: it takes the moon's top band and rim (rule R5, cel_s3 below) and its
//                          unlit side sits on the one shade; with CEL_OWN_LIGHT, add cel_s3_add(...) to SPECULAR_LIGHT
//                          and take cel_s3_unlit(sh, dir) as the key's least share yourself
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
// before. y: the dapple's edge width (screen pixels; under 1: one pixel, as before). z: over 0, cel_cookie is the FIELD tile
// and this its stems' range in metres (see cel_dapple_at).
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
// (L1 lead 12, R4 round 4) Her fire on the ground is a FIELD, not a disc: one smooth ramp with no edge (the dab-field push
// and the under-leaf break of rounds 2-3 drew a disc with a crust: retired), the moon coming back smoothly under it
// (cel_give z, w), and the canopy's leaf shade lying across it (rigs.json "ember_shade"): cel_pool_shade x the share of her
// fire a leaf's shade takes (the rest is the shade's warm residue; 0: the rig has not opted in, nothing below applies), y and
// z the canopy's opening over her fire (m from her light's foot: no leaf shade at all inside y, the moon's and the fire's
// both; whole from z on), w how much of the moon's give-way a leaf's shade undoes (1: under a leaf the moon is whole, so the
// shade in her pool is the night's one shade (R3) plus the fire's residue, never black, never orange).
global uniform vec4 cel_pool_shade;
// (L1 lead 17, P) Her fire on the FLOOR, rebuilt (three ramp rounds drew an orange disc and pink panes cut by navy leaves:
// red light ADDED to a blue floor is pink, and a leaf that cuts it leaves the night's navy). On a floor (a shader that
// says `#define CEL_FLOOR` before the include) under a rig with a tone table (rigs.json "ember_floor"; Atmosphere.FloorTurn)
// the fire is a TURN OF THE FLOOR'S OWN TONE: cel_floor_turn row 0 rgb what the floor's lit tone is multiplied by at r
// metres from her light's foot, row 1 the same for the tone under a leaf (so gap and shade take the turn each at its own
// value: one family, a step apart), both 1 at the last stop (the floor's own, so there is no edge to meet); a the moon's
// return there (0 at her feet: its key and sky give way). Where the moon is away her light stands in for it at the
// floor's own two tones (cel_floor_band yzw: the light that shows the floor's lit tone, cel_floor_unit rgb: its shade's),
// so the leaf shapes run on to her feet and the turn alone says what color the floor is. cel_floor_band x the table's
// last stop (m; 0: no table, the floor takes the ramp above exactly as before). No tone lives here: the rig's table.
global uniform vec4 cel_floor_band;
global uniform vec4 cel_floor_unit;
global uniform sampler2D cel_floor_turn : filter_linear, repeat_disable;
// (L1 lead 12, S3: rule R5) What STANDS shows the moon's top step. One stepped term (on or off, a hard edge, no gradient)
// that any standing shader takes by `#define CEL_S3` before the include: a TOP band on planes facing the moon (the key's
// way leaned up by cel_s3_shape.y, so backs, shoulders, crown tops and rock tops take it; on from cel_s3_shape.x of that
// n.m) and a narrow RIM on the form's moon-side silhouette edge (cel_s3_shape.z screen pixels wide). It is authored as a
// screen level and hue (rigs.json "moon_top": [level, R, G, B, top, up, rim px, unlit]; cel_s3 rgb the color x level as
// scene light, a 1: on), not as more light on the albedo: where it stands, the key's own diffuse on that albedo is taken
// back, so it lands on the one step whatever the paint. It obeys the one shade (R3: none under a leaf's shade or a cast
// shadow) and gives way to her fire with the moon (cel_gv; a shader may give a share of its own, CEL_S3_SHARE: the crowd,
// none on a face her fire lights). cel_s3_shape.w: the key's share on a standing form's UNLIT side (R3: a form's unlit
// side is the one shade too, never black; the darker of it and a cast shadow, never the product). cel_s3.a 0: the rig has
// not opted in and nothing here draws (every rig but arena_night).
global uniform vec4 cel_s3;
global uniform vec4 cel_s3_shape;

// (fragment() to light(): the geometric normal, and x SPECULAR, y RIM, z RIM_TINT, w ROUGHNESS before the tag)
// (L1 B4r2) cel_gn's length is 1 + the key's share through the canopy here (cel_dap(): 1 open sky): packed, not a varying
// of its own, because a shader at Godot's 32 varyings (KitLook's roofs) would fail to compile on one more.
// (L1 W2: and the moon's share after her light, cel_gv(): length = 1.01 + 0.98 dapple + 2 round(1000 share); fragment() to
// light() is not interpolated, so the packing is exact to about 1e-4)
varying vec3 cel_gn;
varying vec4 cel_mat;
#ifdef CEL_S3
varying vec2 cel_s3v;   // (x the moon-side rim here, 0..1; y the shader's own share of S3, CEL_S3_SHARE)
#ifndef CEL_S3_SHARE
#define CEL_S3_SHARE 1.0
#endif
#define CEL_FRAG_S3 cel_s3v = vec2(cel_s3_edge(NORMAL, VIEW, VIEW_MATRIX), CEL_S3_SHARE)
#else
#define CEL_FRAG_S3
#endif
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
	// (L1 lead 14, D2) The FIELD tile (cel_oneshade.z > 0: CanopyField, rigs.json dapple "mass"): r the cover a texel closes at
	// (shade where it is under the canopy's cover), g and b the way to its leaf's stem (128 + 127 per z metres). The canopy's
	// opening over her fire (cel_pool_shade y to z) is the COVER falling toward her, read at the leaf's stem: a leaf is whole
	// or gone, so the masses pull back leaf by leaf and the opening's edge is their own hard leaf outlines (lead 12's fade
	// below drew a brown gradient where a mass met the fire). The edge's width is capped (the tile steps from leaf to leaf
	// inside a mass: an uncapped fwidth drew those steps as faint lines).
	if (cel_oneshade.z > 0.0) {
		vec3 c_t = textureLod(cel_cookie, c_p / cel_dapple.z, 0.0).rgb;
		if (cel_pool_shade.z > 0.0 && cel_ember.w > 0.0) c_cov *= smoothstep(cel_pool_shade.y, max(cel_pool_shade.z, cel_pool_shade.y + 1e-3), length(c_wp.xz + (c_t.gb * 255.0 - 128.0) * (cel_oneshade.z / 127.0) - cel_ember.xz));
		float c_wf = min(fwidth(c_t.r) * 0.5, 0.02) * c_e + 0.0005;
		return mix(1.0, smoothstep(c_cov - c_wf, c_cov + c_wf, c_t.r), cel_key.w);
	}
	float c_f = texture(cel_cookie, c_p / cel_dapple.z, log2(c_e)).r;
	float c_w = fwidth(c_f) * 0.5 * c_e + 0.01;
	float c_d = mix(1.0, smoothstep(c_cov - c_w, c_cov + c_w, c_f), cel_key.w);
	// (L1 lead 12, R4 round 4: the canopy opens over her fire, cel_pool_shade y to z)
	if (cel_pool_shade.z > 0.0 && cel_ember.w > 0.0) c_d = mix(1.0, c_d, smoothstep(cel_pool_shade.y, max(cel_pool_shade.z, cel_pool_shade.y + 1e-3), length(c_wp.xz - cel_ember.xz)));
	return c_d;
}
// (L1 lead 9, B1) Her pool's ramp at r metres from her light's foot (past its last stop: the last stop's).
vec4 cel_pool_at(float c_r) {
	return texture(cel_pool_ramp, vec2((clamp(c_r / cel_pool_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, 0.5));
}
// (L1 W2) The moon's return at a world point under her light: 0 at its heart, 1 out of its reach (c_dap: the canopy's dapple
// there, cel_dapple_at); cel_give_of: the moon's share from it, 1 - cel_give.x (key) or .y (sky) at the heart.
float cel_back_at(vec3 c_wp, float c_dap) {
#ifdef CEL_NO_GIVE
	return 1.0;
#else
	if (cel_ember.w <= 0.0) return 1.0;
	// (L1 lead 10, NIGHT: under the ramp the moon gives way on the ground from her light's foot, wholly inside cel_give z (m)
	// and none past w, the ramp's warm stops and its tail (rigs.json ember_give). Tied to the ramp's level (lead 9: a = level
	// over the core's, half the moon back at 1 m), a saturated moon came back inside the gold and drew the pool pink.)
	// (L1 lead 12, round 4: the plain distance on the ground again (rounds 2-3 read a painted radius, retired); and under a
	// leaf's shade the moon stays, cel_pool_shade.w: c_dap carries the canopy's opening over her fire already)
	float c_d = cel_pool_band.x > 0.0 ? length(c_wp.xz - cel_ember.xz) : length(c_wp - cel_ember.xyz);
	float c_back = smoothstep(cel_give.z, max(cel_give.w, cel_give.z + 1e-3), c_d);
	// (round 5: by the cube of the leaf's shade. Where the canopy's opening fades a leaf in, the fire dims first and the
	// moon's blue comes in only as the leaf closes: at half a leaf the plain share laid half the blue over half the fire,
	// an olive smudge on the orange body; under a whole leaf nothing changes.)
	if (cel_pool_shade.w > 0.0 && cel_key.w > 0.0) { float c_ls = clamp((1.0 - c_dap) / cel_key.w, 0.0, 1.0); c_back = mix(c_back, 1.0, cel_pool_shade.w * c_ls * c_ls * c_ls); }
	return c_back;
#endif
}
float cel_give_of(float c_back, float c_k) { return 1.0 - c_k * cel_on * (1.0 - c_back); }
// (L1 lead 17, P) The floor's tone table (cel_floor_turn above) at r metres, row 0.25 (lit) or 0.75 (under a leaf); and a
// floor's fragment: the moon's return from the table (in place of cel_back_at), the turn handed back for its albedo.
#ifdef CEL_FLOOR
bool cel_floor_on() { return cel_on > 0.0 && cel_floor_band.x > 0.0 && cel_ember.w > 0.0 && cel_pool.w > 0.0; }
vec4 cel_floor_at(float c_r, float c_row) {
	return texture(cel_floor_turn, vec2((clamp(c_r / cel_floor_band.x, 0.0, 1.0) * 63.0 + 0.5) / 64.0, c_row));
}
float cel_floor_back(vec3 c_wp, float c_dap, inout vec4 c_turn) {
	if (!cel_floor_on()) return cel_back_at(c_wp, c_dap);
	float c_r = length(c_wp.xz - cel_ember.xz);
	float c_leaf = cel_key.w > 0.0 ? clamp((1.0 - c_dap) / cel_key.w, 0.0, 1.0) : 0.0;
	vec4 c_t = cel_floor_at(c_r, 0.25);
	// (lead 20, MASS, MASS3: w the fire's share for cel_floor_paint, 1 - a^8 of the moon's return: whole at her feet and held
	// to the pool's edge (0.98 at a 0.6, 0.83 at 0.8, 0.57 at 0.9), none where the moon is whole)
	c_turn = vec4(mix(c_t.rgb, cel_floor_at(c_r, 0.75).rgb, c_leaf), 1.0 - pow(c_t.a, 8.0));
	// (p_01: her stand-in under a leaf came out a third of the shade's tone, a near-black mass beside the orange. Under a
	// leaf the sky stays whole instead, so the shade there is the floor's own shade times its turn: the table's tone exactly.)
	return mix(c_t.a, 1.0, c_leaf);
}
// (L1 lead 20, MASS, MASS3) The turn is of the floor's REFERENCE tone. A floor's own value masses (a painted material at
// a third of the floor's mean albedo on one side of her, at 1.5 x on the other) took the turn and made one side of her
// pool deeper than the other, with a navy wedge on its edge. Inside her fire the floor's paint gives way BOTH ways: the
// albedo becomes the reference paint (cel_floor_unit rgb: the table's own floor color at the level of rigs.json
// "ember_floor_lift", w that level; 0: off, the floor as before) carrying only the paint's fine grain and drawn marks, by
// the fire's share c_w (cel_floor_back). c_lum: the floor's luminance here WITHOUT its grain (a floor shader names it
// before the include: #define CEL_FLOOR_LUM; else the albedo's own, which flattens the grain).
#ifndef CEL_FLOOR_LUM
#define CEL_FLOOR_LUM cel_lum(ALBEDO)
#endif
vec3 cel_floor_paint(vec3 c_alb, float c_lum, float c_w) {
	if (cel_floor_unit.w <= 0.0 || c_w <= 0.0) return c_alb;
	return mix(c_alb, cel_floor_unit.rgb * clamp(dot(c_alb, vec3(0.2126, 0.7152, 0.0722)) / max(c_lum, 1e-4), 0.25, 4.0), c_w);
}
#define CEL_FRAG_TURN0 vec4 c_ft = vec4(1.0, 1.0, 1.0, 0.0);
#define CEL_FRAG_BACK(c_p, c_d) cel_floor_back(c_p, c_d, c_ft)
#define CEL_FRAG_TURN1 ALBEDO = cel_floor_paint(ALBEDO, CEL_FLOOR_LUM, c_ft.w) * c_ft.rgb
#else
#define CEL_FRAG_TURN0
#define CEL_FRAG_BACK(c_p, c_d) cel_back_at(c_p, c_d)
#define CEL_FRAG_TURN1
#endif
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
#define CEL_FRAGMENT CEL_FRAG_TURN0 { vec3 c_fw = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz; float c_fd = cel_dapple_at(c_fw); float c_fb = CEL_FRAG_BACK(c_fw, c_fd); cel_gn = normalize(NORMAL) * (1.01 + 0.98 * c_fd + 2.0 * round(1000.0 * cel_give_of(c_fb, cel_give.x) * cel_fires_at(c_fw, cel_fire_give.x))); AO *= cel_give_of(c_fb, cel_give.y) * cel_fires_at(c_fw, cel_fire_give.y); } CEL_FRAG_ALB; CEL_FRAG_TURN1; CEL_FRAG_MAT; CEL_FRAG_S3; ROUGHNESS = cel_tag(ROUGHNESS, cel_ink); if (cel_dbg > 0.5) { EMISSION = cel_dbg > 2.5 ? vec3(CEL_SKIN_V) : cel_dbg > 1.5 ? cel_ink_rgb(cel_ink) : vec3(0.0); ALBEDO = vec3(0.0); SPECULAR = 0.0; METALLIC = 0.0; }

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

#ifdef CEL_S3
// (L1 lead 12, S3) The moon-side rim, in fragment() (CEL_FRAGMENT): the silhouette's distance in screen pixels from n.v and
// its screen derivative, whole inside cel_s3_shape.z pixels of the edge, on the side of the form the key is on.
float cel_s3_edge(vec3 c_n, vec3 c_v, mat4 c_vm) {
	if (cel_s3.a <= 0.0 || cel_s3_shape.z <= 0.0) return 0.0;
	vec3 c_nn = normalize(c_n);
	float c_e = max(dot(c_nn, c_v), 0.0);
	float c_px = c_e / max(fwidth(c_e), 1e-4);
	vec3 c_kv = (c_vm * vec4(cel_key.xyz, 0.0)).xyz;
	float c_side = smoothstep(0.05, 0.25, dot(c_nn.xy, normalize(c_kv.xy + vec2(1e-5))));
	return (1.0 - smoothstep(cel_s3_shape.z - 0.5, cel_s3_shape.z + 0.5, c_px)) * (1.0 - smoothstep(0.55, 0.65, c_e)) * c_side;
}
// The key's share on a standing form's unlit side (0: the rig has not opted in).
float cel_s3_unlit(float c_sh, bool c_dir) { return c_dir && cel_s3.a > 0.0 ? min(cel_s3_shape.w, c_sh) : 0.0; }
// The S3 term in light(), for the key (the directional light along cel_key), as SPECULAR_LIGHT: the top band or the rim,
// in open moonlight only, at the rig's level (the key's diffuse on this albedo taken back). c_iv: INV_VIEW_MATRIX.
vec3 cel_s3_add(vec3 c_l, vec3 c_lc, float c_t, float c_att, bool c_dir, vec3 c_albedo, mat4 c_iv) {
	if (!c_dir || cel_s3.a <= 0.0 || cel_on <= 0.0 || dot((c_iv * vec4(c_l, 0.0)).xyz, cel_key.xyz) < 0.98) return vec3(0.0);
	float c_q = cel_gq();
	float c_leaf = 1.0;
	if (cel_key.w > 0.0) c_leaf = clamp((clamp((length(cel_gn) - 1.01 - 2.0 * c_q) / 0.98, 0.0, 1.0) - (1.0 - cel_key.w)) / cel_key.w, 0.0, 1.0);
	float c_raw = cel_oneshade.x > 0.0 ? clamp(1.0 - (1.0 - c_att) / cel_oneshade.x, 0.0, 1.0) : c_att;
	float c_open = smoothstep(0.42, 0.58, c_raw) * smoothstep(0.4, 0.6, c_leaf) * clamp(c_q * 0.001, 0.0, 1.0);
	vec3 c_nw = normalize((c_iv * vec4(normalize(cel_gn), 0.0)).xyz);
	float c_nm = dot(c_nw, normalize(mix(cel_key.xyz, vec3(0.0, 1.0, 0.0), cel_s3_shape.y)));
	float c_m = max(smoothstep(cel_s3_shape.x - 0.02, cel_s3_shape.x + 0.02, c_nm), cel_s3v.x) * cel_s3v.y * c_open;
	if (c_m <= 0.0) return vec3(0.0);
	float c_sh = cel_shadow(c_att, c_dir);
	vec3 c_key = c_lc * max(cel_level(c_t) * c_sh, vec3(cel_s3_unlit(c_sh, c_dir))) / PI;
	return c_m * max(cel_s3.rgb - c_albedo * c_key, vec3(0.0));
}
#endif

#ifdef CEL_HERO
// (L1 lead 19, HER2) THE HERO IN A POOL: a hero-scale figure standing in her own lit pool takes ONE dark warm anchor tone
// on her shade side (the side away from the pool light's foot, and her under planes), a single hard step, so at 40 px
// she is a light figure with one connected dark mass and the eye lands on her first. Rig-driven (rigs.json "hero_pool",
// Atmosphere.SetCel): cel_hero = unit xz toward the light's foot, the side edge (in n.xz away from the foot), on;
// cel_hero_tone = the anchor (linear rgb x level), the under edge (n.y under it). Off without the row or with her lamp
// out (cel_ember.w 0). No varying (her skin is at Godot's 32): the mask is read from the normal in fragment() and light().
// A shader defines CEL_HERO before the include, writes CEL_HERO_FRAGMENT after CEL_FRAGMENT and CEL_HERO_LIGHT last in light().
global uniform vec4 cel_hero;
global uniform vec4 cel_hero_tone;
float cel_hero_mask(vec3 c_wn, float c_w) {
	if (cel_hero.w < 0.5 || cel_ember.w <= 0.0) return 0.0;
	float c_side = smoothstep(cel_hero.z - c_w, cel_hero.z + c_w, -dot(c_wn.xz, cel_hero.xy));
	float c_under = 1.0 - smoothstep(cel_hero_tone.w - c_w, cel_hero_tone.w + c_w, c_wn.y);
	return max(c_side, c_under);
}
// (L1 lead 20, HER4) SHE IS A LIGHT FIGURE: with the row's light (values 15-18) the whole figure is painted in the rig's
// ABSOLUTE tones, no lights on her: the warm LIGHT on every plane but the ones turned away from the foot, a MID step
// (values 20-24: level, r, g, b, its side edge) between, and the anchor only as a narrow accent past its own side edge
// (value 6) and on under planes (value 7). Each material keeps ITS OWN color inside the light and the mid: the hue of
// its albedo by the share cel_hero_own.x (value 25), its value as pow(v, cel_hero_own.y) (value 26: 0 = one level for
// every material, navy as light as skin). The anchor stays one tone (one connected dark mass). A row without the light
// (under 20 values): the lead 19 form (the anchor over the material's own lit side).
global uniform vec4 cel_hero_lit;
global uniform vec4 cel_hero_mid;
global uniform vec4 cel_hero_own;
bool cel_hero_on() { return cel_hero.w > 0.5 && cel_ember.w > 0.0; }
bool cel_hero_abs() { return cel_hero_on() && cel_hero_lit.rgb != vec3(0.0); }
vec3 cel_hero_local(vec3 c_tone, vec3 c_alb) {
	float c_v = clamp(max(c_alb.r, max(c_alb.g, c_alb.b)), 0.02, 1.0);
	vec3 c_own = clamp(c_alb / c_v, 0.0, 1.0);
	return c_tone * mix(vec3(1.0), c_own, cel_hero_own.x) * pow(c_v, cel_hero_own.y);
}
// (L1 lead 21, CHROMA) THE HERO CHROMA RULE: at hero scale (30-40 px) each of her materials keeps ITS OWN hue and its
// level and GAINS chroma, so each hue reads as a color and not as a grey of it. Worked in Oklab on the painted tone (the
// row's level on the material's own color): L and the hue angle held, the saturation s = C / L (the same at every
// level) scaled. cel_hero_chroma (values 29-32) = the gain on the light, the gain on the shade step, the FLOOR (a
// material under it takes none, the whole gain from twice it: steel and near-greys never go neon), the CAP (the gain
// never lifts a material past it; one already past it is left as it is). cel_hero_chroma_px (values 33-34) = the
// figure's size on screen, in px per metre at 1080p, under which the gain is whole and over which it is none (a close
// shot keeps her data colors). A row without them (all zero): no gain, the painted tone untouched.
// (round 2) THE COLOR'S LEVEL: a light tone cannot hold a color on the screen (her hair's lit tone clipped to the floor's
// light orange, whatever the gain), so a colored material is painted no lighter than cel_hero_chroma_px.z (value 35,
// Oklab L of the emission; 0 = off), at the same C / L, by the floor's own weight: skin and steel keep the full light.
global uniform vec4 cel_hero_chroma;
global uniform vec4 cel_hero_chroma_px;
float cel_hero_near(float c_depth, mat4 c_proj) {
	if (cel_hero_chroma.x <= 0.0) return 0.0;
	float c_ppm = abs(c_proj[1][1]) * 540.0 / (c_proj[3][3] == 0.0 ? max(c_depth, 0.01) : 1.0);
	return 1.0 - smoothstep(cel_hero_chroma_px.x, max(cel_hero_chroma_px.y, cel_hero_chroma_px.x + 0.001), c_ppm);
}
vec3 cel_hero_gain(vec3 c_rgb, float c_gain, float c_k) {
	if (c_k <= 0.0 || c_gain <= 0.0) return c_rgb;
	vec3 c_in = max(c_rgb, vec3(0.0));
	vec3 c_lms = pow(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376), vec3(0.0514459929, 0.1073969566, 0.6299787005)) * c_in, vec3(1.0 / 3.0));
	vec3 c_ok = mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662), vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * c_lms;
	float c_s = length(c_ok.yz) / max(c_ok.x, 0.0001);
	float c_cw = c_k * smoothstep(cel_hero_chroma.z, 2.0 * cel_hero_chroma.z, c_s);
	float c_to = c_s * mix(1.0, c_gain, c_cw);
	float c_lt = cel_hero_chroma_px.z > 0.0 ? mix(c_ok.x, min(c_ok.x, cel_hero_chroma_px.z), c_cw) : c_ok.x;
	if (c_gain > 1.0) c_to = min(c_to, max(c_s, cel_hero_chroma.w));
	if (c_s < 0.0001 || (c_to == c_s && c_lt == c_ok.x)) return c_rgb;
	float c_lf = c_lt / max(c_ok.x, 0.0001);
	c_ok.yz *= (c_to / c_s) * c_lf;
	c_ok.x = c_lt;
	c_in *= c_lf * c_lf * c_lf;
	vec3 c_l = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480)) * c_ok;
	vec3 c_out = mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147), vec3(0.2309699292, -0.3413193965, 1.7076147010)) * (c_l * c_l * c_l);
	// the gamut's edge: no channel under zero (the gain stops where the color is pure, at the same hue)
	float c_lo = min(c_out.r, min(c_out.g, c_out.b));
	if (c_lo < 0.0) { float c_was = min(c_in.r, min(c_in.g, c_in.b)); c_out = mix(c_in, c_out, clamp(c_was / max(c_was - c_lo, 0.000001), 0.0, 1.0)); }
	return c_out;
}
// (L1 lead 22, HERPAIR) HER VALUE PAIRS BY MATERIAL CLASS: one shared level cannot put her hair a step under the floor
// and her lit skin over it (they share the floor's hue and close albedo values). Each hero material has a CLASS
// (cel_hero_class, set by CelLib.HeroClassStep from its shader: 0 hair, 1 skin, 2 outfit leather / cloth, 3 outfit
// metal; -1 = none) and the rig a VALUE pair per class (hero_pool values 36-43: lit L, shade L, as Oklab L of the
// emission; cel_hero_class_lit / _shade, x..w = class 0..3; 0 = that class as before). The painted tone (its own hue,
// its C / L after the chroma gain) is landed at the class's L by scaling its linear rgb (Oklab L, a, b all scale by the
// cube root: hue and C / L are kept exactly; no hue term, the rig never sets her color). cel_hero_class_keep (value 44)
// = the share of the material's own L kept, geometric (0 = every texel at the class's L, 1 = as before), so a darker
// leather stays under a lighter steel in the same class. The anchor (the dark share) is untouched.
uniform float cel_hero_class = -1.0;
global uniform vec4 cel_hero_class_lit;
global uniform vec4 cel_hero_class_shade;
global uniform float cel_hero_class_keep;
float cel_hero_ok_l(vec3 c_rgb) {
	vec3 c_lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376), vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c_rgb, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	return dot(vec3(0.2104542553, 0.7936177850, -0.0040720468), c_lms);
}
float cel_hero_class_pick(vec4 c_v) {
	int c_k = int(round(cel_hero_class));
	return c_k == 0 ? c_v.x : c_k == 1 ? c_v.y : c_k == 2 ? c_v.z : c_k == 3 ? c_v.w : 0.0;
}
// (L1 lead 24, TRIM) GOLD OVER GUNMETAL: with the keep at 0 every metal texel lands at one L, so her gold trim sat at
// the plate's value. cel_hero_gold (hero_pool 78-81), class 3 only, per texel from the tone itself: its GOLD share = the
// tone over its light (lit or mid), Oklab (a, b) along the gold axis (h 60) over its L, smoothstep(y, z) (a cool gunmetal tone has none and lands as
// before); a gold texel lands at the class's L times x (both the lit and the shade pair) and never under it (a floor, whole
// at any c_k), its C / L times w (0 or 1 = its own). Value and chroma only: the hue is the tone's own. Zeros: as before.
global uniform vec4 cel_hero_gold;
// (L1 lead 25, PLATE) WARM UNDER HER FIRE: the gunmetal plate read neutral silver-grey under her own pool. cel_hero_warm
// (hero_pool 82-83), class 3 only, the non-gold share of a texel: its Oklab (a, b) turn to her fire's hue (cel_hero_tone, her
// anchor: the row's own warm tone, no new hue) at C / L = x on the lit pair, y on the shade pair (0 = that pair as before),
// whole at any c_k (as the gold floor). Chroma only, L kept; the anchor (her dark blued share) is not landed and stays cool.
global uniform vec4 cel_hero_warm;
vec3 cel_hero_gold_ok(vec3 c_rgb) {   // (Oklab of linear rgb: cel_hero_ok's math, declared here as land comes first)
	vec3 c_lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376), vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c_rgb, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	return mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662), vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * c_lms;
}
vec3 cel_hero_gold_lin(vec3 c_ok) {
	vec3 c_l = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480)) * c_ok;
	return mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147), vec3(0.2309699292, -0.3413193965, 1.7076147010)) * (c_l * c_l * c_l);
}
vec3 cel_hero_land(vec3 c_rgb, float c_lt, float c_k) {
	if (c_lt <= 0.0 || c_k <= 0.0) return c_rgb;
	float c_l = cel_hero_ok_l(c_rgb);
	if (c_l < 0.0001) return c_rgb;
	float c_gs = 0.0;
	bool c_onlit = abs(c_lt - cel_hero_class_lit.w) < 0.00001;   // (PLATE) the lit pair or the shade pair, before gold lifts c_lt
	if (int(round(cel_hero_class)) == 3 && cel_hero_gold.x > 0.0) {
		// (the tone over its light, the lit or the mid by which pair L it lands at: the material's own share, the light's hue out)
		vec3 c_li = abs(c_lt - cel_hero_class_lit.w) < 0.00001 ? cel_hero_lit.rgb : cel_hero_mid.rgb;
		vec3 c_ok = cel_hero_gold_ok(c_rgb / max(c_li, vec3(0.0001)));
		c_gs = smoothstep(cel_hero_gold.y, max(cel_hero_gold.z, cel_hero_gold.y + 0.0001), dot(c_ok.yz, vec2(0.5, 0.8660254)) / max(c_ok.x, 0.0001));
		c_lt *= mix(1.0, cel_hero_gold.x, c_gs);
	}
	float c_to = pow(c_lt, 1.0 - clamp(cel_hero_class_keep, 0.0, 1.0)) * pow(c_l, clamp(cel_hero_class_keep, 0.0, 1.0));
	float c_f = mix(1.0, c_to / c_l, c_k);
	vec3 c_o = c_rgb * (c_f * c_f * c_f);
	// (gold's L is a FLOOR at the lifted class L, whole at any c_k: at the stand camera the landing is partial (c_near ~0.4),
	// so a landing alone left gold at its own L, the plate's lit pair already near it; the floor never darkens a brighter texel)
	if (c_gs > 0.0) {
		float c_lo = cel_hero_ok_l(c_o);
		if (c_lo > 0.0001 && c_lo < c_lt) { float c_fg = mix(1.0, c_lt / c_lo, c_gs); c_o *= c_fg * c_fg * c_fg; }
	}
	if (c_gs > 0.0 && cel_hero_gold.w > 0.0 && cel_hero_gold.w != 1.0) {
		vec3 c_q = cel_hero_gold_ok(c_o);
		c_q.yz *= mix(1.0, cel_hero_gold.w, c_gs);
		vec3 c_g = cel_hero_gold_lin(c_q);
		if (min(c_g.r, min(c_g.g, c_g.b)) >= 0.0) c_o = c_g;
	}
	// (PLATE) the plate's share turns to her fire's hue at the pair's C / L (L kept; a texel out of gamut keeps its own)
	float c_wc = c_onlit ? cel_hero_warm.x : cel_hero_warm.y;
	if (int(round(cel_hero_class)) == 3 && c_wc > 0.0 && c_gs < 1.0) {
		vec3 c_fo = cel_hero_gold_ok(cel_hero_tone.rgb);
		float c_fc = length(c_fo.yz);
		if (c_fc > 0.0001) {
			vec3 c_q = cel_hero_gold_ok(c_o);
			c_q.yz = mix(c_q.yz, c_fo.yz / c_fc * c_wc * c_q.x, 1.0 - c_gs);
			vec3 c_g = cel_hero_gold_lin(c_q);
			if (min(c_g.r, min(c_g.g, c_g.b)) >= 0.0) c_o = c_g;
		}
	}
	return c_o;
}
// (L1 lead 22, R1HAIR) THE HAIR CLASS'S COLOR: class 0 (hair) with cel_hero_class_hair (hero_pool 45-48: the Oklab C
// of the emission at the class's lit L, at its shade L, the strands' breakup, the strands' mean share of the dye) lands
// every texel at the class's L times its own L over the dye's (c_ref, CEL_HERO_REF: the hair's own data color times the
// share), to the power of the breakup (0 = one flat tone), at the step's saturation C / L, in ITS OWN hue (a texel too
// grey to hold one takes the dye's): darker strands are the same red, darker. No hue term: the hue is the hair's data.
// A row without them (zeros): as before. CEL_HERO_REF defaults to ALBEDO (no other material changes).
global uniform vec4 cel_hero_class_hair;
vec3 cel_hero_ok(vec3 c_rgb) {
	vec3 c_lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376), vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c_rgb, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	return mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662), vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * c_lms;
}
vec3 cel_hero_lin(vec3 c_ok) {
	vec3 c_l = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480)) * c_ok;
	return mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147), vec3(0.2309699292, -0.3413193965, 1.7076147010)) * (c_l * c_l * c_l);
}
vec3 cel_hero_hair(vec3 c_tone, vec3 c_reft, float c_ratio, float c_lt, float c_ct) {
	vec3 c_o = cel_hero_ok(c_tone), c_r = cel_hero_ok(c_reft);
	float c_s = length(c_o.yz) / max(c_o.x, 0.0001);
	vec2 c_dir = normalize(mix(c_r.yz / max(length(c_r.yz), 0.000001), c_o.yz / max(length(c_o.yz), 0.000001), smoothstep(0.04, 0.1, c_s)) + vec2(0.000001));
	float c_l = c_lt * clamp(pow(max(c_ratio, 0.0001), cel_hero_class_hair.z), 0.4, 1.6);
	vec3 c_out = cel_hero_lin(vec3(c_l, c_dir * c_l * c_ct / max(c_lt, 0.0001)));
	// (the gamut's edge: no channel under zero, the chroma pulled toward the grey of the same L at the same hue)
	float c_lo = min(c_out.r, min(c_out.g, c_out.b));
	if (c_lo < 0.0) { vec3 c_g = vec3(c_l * c_l * c_l); c_out = mix(c_g, c_out, clamp(c_g.r / max(c_g.r - c_lo, 0.000001), 0.0, 1.0)); }
	return max(c_out, vec3(0.0));
}
// (L1 lead 22, R3FORM) THE TERMINATOR, HER THIRD VALUE STEP: two value planes per material read as a blocky mannequin;
// a form turns in three (lit, a thin dark band where it turns away, the shade beyond). Per class a terminator L
// (cel_hero_term_l, hero_pool 49-52, Oklab L of the emission, class 0..3; 0 = no band on that class) and its chroma lift
// (cel_hero_term_c, 53-56: the band's C / L over the shade step's, same hue; 0 or 1 = the shade's), drawn as a band
// cel_hero_term.x px wide (57; 0 = off) on screen at the mid edge (value 24), a share cel_hero_term.y (58) of it past the
// edge on the shade side (0 = all of it on the lit side: the lit plane gives the band its width). The width is in
// SCREEN px (fwidth of the side term), so a plane that turns slowly takes no broad dark patch and a limb's turn a line
// of the same 1-2 px at any size. The band's tone is the class's shade tone scaled to the band's L (every texel's
// relation, the hair's breakup and C / L kept), then its C / L lifted: no hue term. A row without them: zeros, as before.
global uniform vec4 cel_hero_term_l;
global uniform vec4 cel_hero_term_c;
global uniform vec4 cel_hero_term;
vec3 cel_hero_term_tone(vec3 c_md, float c_ls, float c_lt, float c_lift) {
	float c_l = c_ls > 0.0 ? c_ls : max(cel_hero_ok_l(c_md), 0.0001);
	float c_f = c_lt / c_l;
	vec3 c_in = max(c_md * (c_f * c_f * c_f), vec3(0.0));
	if (c_lift <= 0.0 || abs(c_lift - 1.0) < 0.0001) return c_in;
	vec3 c_o = cel_hero_ok(c_in);
	c_o.yz *= c_lift;
	vec3 c_out = cel_hero_lin(c_o);
	// (the gamut's edge: no channel under zero, the lift stops where the color is pure, at the same hue)
	float c_lo = min(c_out.r, min(c_out.g, c_out.b));
	if (c_lo < 0.0) { float c_was = min(c_in.r, min(c_in.g, c_in.b)); c_out = mix(c_in, c_out, clamp(c_was / max(c_was - c_lo, 0.000001), 0.0, 1.0)); }
	return max(c_out, vec3(0.0));
}
vec3 cel_hero_paint(vec3 c_wn, vec3 c_alb, float c_w, float c_near, vec3 c_ref) {
	// (round 2) FORM FROM ABOVE: the side is read from the plane's LEAN alone (n.xz normalized, down to the least lean
	// cel_hero_own.z, value 27), so at the play camera, where her planes point up, the side away from the foot still
	// takes the mid and the anchor as one connected side.
	float c_s = -dot(c_wn.xz, cel_hero.xy) / max(length(c_wn.xz), max(cel_hero_own.z, 0.001));
	float c_sfw = max(fwidth(c_s), 0.0001);   // (R3FORM: the side term's change per screen px, taken in uniform flow)
	float c_mid = cel_hero_mid.rgb != vec3(0.0) ? smoothstep(cel_hero_mid.w - c_w, cel_hero_mid.w + c_w, c_s) : 0.0;
	// (HERPAIR) the class's landing is whole at the play camera, none in a close shot (the chroma rule's px band), whole without it
	float c_ck = cel_hero_chroma.x > 0.0 ? c_near : 1.0;
	vec3 c_lit = cel_hero_land(cel_hero_gain(cel_hero_local(cel_hero_lit.rgb, c_alb), cel_hero_chroma.x, c_near), cel_hero_class_pick(cel_hero_class_lit), c_ck);
	vec3 c_md = cel_hero_land(cel_hero_gain(cel_hero_local(cel_hero_mid.rgb, c_alb), cel_hero_chroma.y, c_near), cel_hero_class_pick(cel_hero_class_shade), c_ck);
	// (R1HAIR) the hair class at its own colored C / L, its strands' breakup kept
	if (int(round(cel_hero_class)) == 0 && cel_hero_class_hair.x > 0.0 && cel_hero_class_lit.x > 0.0 && c_ck > 0.0) {
		float c_hr = cel_hero_ok_l(c_alb) / max(cel_hero_ok_l(c_ref * max(cel_hero_class_hair.w, 0.001)), 0.0001);
		c_lit = mix(c_lit, cel_hero_hair(cel_hero_local(cel_hero_lit.rgb, c_alb), cel_hero_local(cel_hero_lit.rgb, c_ref), c_hr, cel_hero_class_lit.x, cel_hero_class_hair.x), c_ck);
		c_md = mix(c_md, cel_hero_hair(cel_hero_local(cel_hero_mid.rgb, c_alb), cel_hero_local(cel_hero_mid.rgb, c_ref), c_hr, max(cel_hero_class_shade.x, 0.0001), cel_hero_class_hair.y), c_ck);
	}
	vec3 c_t = mix(c_lit, c_md, c_mid);
	// (R3FORM) the terminator band at the mid edge, cel_hero_term.x screen px wide, in the class's own tone
	float c_tl = cel_hero_class_pick(cel_hero_term_l);
	if (c_tl > 0.0 && cel_hero_term.x > 0.0 && cel_hero_mid.rgb != vec3(0.0) && c_ck > 0.0) {
		float c_bw = cel_hero_term.x * c_sfw, c_e1 = cel_hero_mid.w + clamp(cel_hero_term.y, 0.0, 1.0) * c_bw, c_e0 = c_e1 - c_bw, c_bh = 0.5 * c_sfw;
		float c_band = smoothstep(c_e0 - c_bh, c_e0 + c_bh, c_s) * (1.0 - smoothstep(c_e1 - c_bh, c_e1 + c_bh, c_s));
		c_t = mix(c_t, cel_hero_term_tone(c_md, cel_hero_class_pick(cel_hero_class_shade), c_tl, cel_hero_class_pick(cel_hero_term_c)), c_band * c_ck);
	}
	float c_dark = max(smoothstep(cel_hero.z - c_w, cel_hero.z + c_w, c_s), 1.0 - smoothstep(cel_hero_tone.w - c_w, cel_hero_tone.w + c_w, c_wn.y));
	return mix(c_t, cel_hero_tone.rgb, c_dark);
}
// (L1 lead 23, GLINT) THE HOT SPECULAR: painted in absolute tones she had no highlight, skin and metal read matte. A
// HARD disc round N.H from HER key (the xz toward her light's foot, cel_hero.xy, lifted by the elevation
// cel_hero_glint_skin.w) and the eye, on her LIT planes only (off the mid step and the under planes), per class:
// cel_hero_glint_skin (hero_pool 64-66) and cel_hero_glint_metal (67-70) = the disc's radius and soft edge in degrees,
// its level (the tone's OWN color brought to a max channel of 1, mixed toward white, times the level, never under 1.2x
// the tone: 0 = off); metal's w = the depth of the dark reflected band just outside its disc (the gunmetal read). The
// edge is never under a screen px of the angle (no speckle). Hue: the tone's own; the rig sets value and chroma only.
// Hair (class 0) and cloth (2) take none. Zeros: as before.
global uniform vec4 cel_hero_glint_skin;
global uniform vec4 cel_hero_glint_metal;
float cel_hero_glint_lit(vec3 c_wn) {
	float c_s = -dot(c_wn.xz, cel_hero.xy) / max(length(c_wn.xz), max(cel_hero_own.z, 0.001));
	float c_m = cel_hero_mid.rgb != vec3(0.0) ? smoothstep(cel_hero_mid.w - 0.02, cel_hero_mid.w + 0.02, c_s) : smoothstep(cel_hero.z - 0.02, cel_hero.z + 0.02, c_s);
	return (1.0 - c_m) * smoothstep(cel_hero_tone.w - 0.02, cel_hero_tone.w + 0.02, c_wn.y);
}
vec3 cel_hero_glint(vec3 c_t, vec3 c_wn, vec3 c_wv, int c_cls, float c_lit) {
	vec4 c_g = c_cls == 1 ? cel_hero_glint_skin : c_cls == 3 ? cel_hero_glint_metal : vec4(0.0);
	vec3 c_l = normalize(vec3(cel_hero.x, cel_hero_glint_skin.w, cel_hero.y));
	float c_ang = degrees(acos(clamp(dot(c_wn, normalize(c_l + c_wv)), -1.0, 1.0)));
	float c_fw = max(fwidth(c_ang), 0.001);   // (taken in uniform flow, before any early return)
	if (c_g.z <= 0.0 || c_g.x <= 0.0 || c_lit <= 0.0) return c_t;
	float c_sf = max(c_g.y, c_fw);
	float c_d = (1.0 - smoothstep(c_g.x - c_sf, c_g.x + c_sf, c_ang)) * c_lit;
	float c_mx = max(c_t.r, max(c_t.g, c_t.b));
	// (TUNE l23: metal's hot glint mixes toward HER KEY's color, not white: a specular is the light's color, so cool
	// gunmetal flashes warm under her lamp and gold flashes hotter; her key's hue, never a rig hue)
	float c_km = max(cel_hero_lit.r, max(cel_hero_lit.g, cel_hero_lit.b));
	vec3 c_key = c_cls == 3 && c_km > 0.0001 ? cel_hero_lit.rgb / c_km : vec3(1.0);
	vec3 c_hot = mix(c_t / max(c_mx, 0.0001), c_key, c_cls == 3 ? 0.85 : 0.5) * max(c_g.z, 1.2 * c_mx);
	vec3 c_o = c_t;
	if (c_cls == 3 && c_g.w > 0.0) {
		float c_b = smoothstep(c_g.x + c_sf, c_g.x + 2.0 * c_sf, c_ang) * (1.0 - smoothstep(2.4 * c_g.x, 2.4 * c_g.x + c_sf, c_ang));
		c_o *= 1.0 - clamp(c_g.w, 0.0, 1.0) * c_b * c_lit;
	}
	return mix(c_o, c_hot, c_d);
}
// (L1 lead 22, P1NORM) SMOOTH SHADING NORMALS: the steps turn her FORMS, not her mesh's bumps. HeroNormals.cs bakes, at
// load, per mesh under her, a normal diffused over the welded surface (radius hero_pool 60, m) into CUSTOM0 as xyz in the
// vertex's own frame (tangent, its square binormal, normal; w 1), so it is skinned with the frame. A shader writes
// CEL_HERO_VERTEX last in vertex(): with the rule on, NORMAL becomes the smoothed normal mixed toward the true one, the
// smoothed share cel_hero_sn.x (hero_pool 59; 0 = off) times the material's cel_hero_sn_k. A mesh without it: as before.
global uniform vec4 cel_hero_sn;
uniform float cel_hero_sn_k : hint_range(0.0, 1.0) = 1.0;
#define CEL_HERO_VERTEX { float c_sk = cel_hero_sn.x * cel_hero_sn_k; if (c_sk > 0.0 && CUSTOM0.w > 0.5 && cel_hero_abs()) { vec3 c_t = TANGENT - NORMAL * dot(NORMAL, TANGENT); c_t = dot(c_t, c_t) > 1e-8 ? normalize(c_t) : normalize(cross(NORMAL, abs(NORMAL.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0))); vec3 c_sn = CUSTOM0.x * c_t + CUSTOM0.y * cross(NORMAL, c_t) + CUSTOM0.z * NORMAL; if (dot(c_sn, c_sn) > 1e-6) NORMAL = normalize(mix(NORMAL, normalize(c_sn), clamp(c_sk, 0.0, 1.0))); } }
// (L1 lead 21, HERMASK) THE ID INSTRUMENT (dev; CelLib sets it only with SU_HERO_ID in the environment, else it is
// zero and nothing changes): a material's own flat ID color in place of the painted tone, on exactly the fragments the
// hero paint (and the held piece's) covers, so one frame shows which pixels of her the row paints, material by material.
uniform vec4 cel_hero_id = vec4(0.0);
#ifndef CEL_HERO_REF
#define CEL_HERO_REF ALBEDO
#endif
#define CEL_HERO_FRAGMENT { if (cel_hero_on()) { vec3 c_hn = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz); if (cel_hero_abs()) { EMISSION = cel_hero_paint(c_hn, ALBEDO, 0.02, cel_hero_near(-VERTEX.z, PROJECTION_MATRIX), CEL_HERO_REF); EMISSION = cel_hero_glint(EMISSION, c_hn, normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz), int(round(cel_hero_class)), cel_hero_glint_lit(c_hn)); if (cel_hero_id.a > 0.5) EMISSION = cel_hero_id.rgb; ALBEDO = vec3(0.0); METALLIC = 0.0; SPECULAR = 0.0; } else { float c_hm = cel_hero_mask(c_hn, 0.02); ALBEDO *= 1.0 - c_hm; EMISSION = mix(EMISSION, cel_hero_tone.rgb, c_hm); } } }
#define CEL_HERO_LIGHT { if (cel_hero_abs()) { DIFFUSE_LIGHT = vec3(0.0); SPECULAR_LIGHT = vec3(0.0); } else { SPECULAR_LIGHT *= 1.0 - cel_hero_mask(normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz), 0.02); } }
#ifdef CEL_HERO_ARM
// (L1 lead 19, HER3; lead 20, HER4) A HELD PIECE of the hero (her shield, her blade: CelLib.Hero binds her own copies of
// their standard materials with CEL_HERO + CEL_HERO_ARM) is a LIT FORM in its OWN color at two absolute levels, no
// lights: the rig's warm light on the whole piece, its shade (values 10-13, never under the anchor) only on its away
// side, read from the POSITION (past value 14 metres from the piece's origin, away from the foot) and never from the
// normal: a flat disc facing the camera is lit, a plane is one tone (no speckle of rivets). Both carry the albedo's
// own color (cel_hero_local). cel_hero_arm = the shade (linear rgb x level), the away edge in m; cel_hero_lit.w = the
// least screen width in px (CEL_HERO_ARM_VERTEX pushes each vertex half of it along its normal).
// (round 2) The piece is QUIETER than she is: its light is the figure's times cel_hero_own.w (value 28). Its color is
// its own albedo (wood, steel) at the two levels: the rig sets VALUE steps, never a color (main, 10 Nov).
global uniform vec4 cel_hero_arm;
bool cel_hero_arm_on() { return cel_hero_abs() && cel_hero_arm.rgb != vec3(0.0); }
#define CEL_HERO_ARM_VERTEX { if (cel_hero_arm_on()) { float c_ad = -(MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).z; VERTEX += NORMAL * (0.5 * cel_hero_lit.w * 2.0 * c_ad / (PROJECTION_MATRIX[1][1] * VIEWPORT_SIZE.y * length(MODEL_MATRIX[0].xyz))); } }
#define CEL_HERO_ARM_FRAGMENT { if (cel_hero_arm_on()) { vec3 c_ap = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz - NODE_POSITION_WORLD; float c_am = smoothstep(cel_hero_arm.w - 0.01, cel_hero_arm.w + 0.01, -dot(c_ap.xz, cel_hero.xy)); vec3 c_aa = ALBEDO; float c_ak = cel_hero_near(-VERTEX.z, PROJECTION_MATRIX); EMISSION = mix(cel_hero_gain(cel_hero_local(cel_hero_lit.rgb * (cel_hero_own.w > 0.0 ? cel_hero_own.w : 1.0), c_aa), cel_hero_chroma.x, c_ak), cel_hero_gain(cel_hero_local(cel_hero_arm.rgb, c_aa), cel_hero_chroma.y, c_ak), c_am); EMISSION = cel_hero_glint(EMISSION, normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz), normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz), 3, 1.0 - c_am); if (cel_hero_id.a > 0.5) EMISSION = cel_hero_id.rgb; ALBEDO = vec3(0.0); METALLIC = 0.0; SPECULAR = 0.0; AO = 0.0; } }
#define CEL_HERO_ARM_LIGHT { if (cel_hero_arm_on()) { DIFFUSE_LIGHT = vec3(0.0); SPECULAR_LIGHT = vec3(0.0); } }
#endif
#endif

#ifdef CEL_STAND
// (L1 lead 14, K1/S1; docs/design/NIGHT_KIT.md) THE STANDING BLOCK: what stands on the board painted in hard steps as the
// rig's levels (rigs.json "stand"), never the albedo's luck. The BASE tones (contact at the foot, side away from the moon,
// body) are absolute scene light written in fragment() as EMISSION, with the ambient off (AO 0) and no diffuse from the key
// or her light, so no piece can render black. The key's light() ADDS only the moon's share (the top tone on up-and-moonward
// normals, the rim line on the moon-side silhouette) in open moonlight: under a cast shadow or a leaf's shade a piece shows
// neither. Her light ADDS the fire as two hard bands on the faces toward it, at her ramp's level at the fragment's distance
// on the ground, and the moon gives way on those faces only. Tones step on the SMOOTH geometric normal, one pixel wide.
// #define CEL_STAND_FAM 0 stone (default), 1 leaf, 2 bark. Globals (Atmosphere.SetCel): cel_stand = top edge, side edge
// (the normal's dot with the key leaned up), up lean, foot band m (x 0: the rig has not opted in); cel_stand_fire = fire
// edge 1, fire edge 2 (the normal's dot toward her light), rim px, spare; cel_stand_pal 8 x 3: texels 0-6 contact, side,
// body, top, rim, fire mid, fire top (rgb the tone, a its level), 7 = paint luminance, dab contrast, rim on any moon edge
// (1) or on tops only (0), spare.
global uniform vec4 cel_stand;
global uniform vec4 cel_stand_fire;
global uniform sampler2D cel_stand_pal : filter_nearest, repeat_disable;
#ifndef CEL_STAND_FAM
#define CEL_STAND_FAM 0
#endif
varying vec3 cel_stm;   // (fragment to light: the moon's add here, top or rim over the base)
varying vec3 cel_stf;   // (fragment to light: her fire's add here per unit of her light's energy over PI)
// (L1 l25 WORLD2) a leaf (CEL_STAND_FAM 1) keeps 1 - CEL_STAND_LEAF_CUT of her fire under the canopy's leaf shade
// (cel_pool_shade.x cuts the ground's fire whole there: the dapple's hard edge inside her pool). Probe world2_01: the pool
// fern's back fronds sat in that shade at frond height (cut 0.05, her light reaching, c_m1 = 1) while st_gv had already
// given their moon tones 27% away: dark wine. Her fire is under the canopy; on a standing leaf the shade is a step, not a cut.
#define CEL_STAND_LEAF_CUT 0.45
bool cel_stand_on() { return cel_on > 0.0 && cel_stand.x != 0.0; }
vec4 cel_stand_tone(int c_i) { return texelFetch(cel_stand_pal, ivec2(c_i, CEL_STAND_FAM), 0); }
// A hard step of c_v at c_e, one pixel wide (fragment() only).
float cel_stand_step(float c_v, float c_e) { float c_w = 0.5 * fwidth(c_v) + 1e-5; return smoothstep(c_e - c_w, c_e + c_w, c_v); }
// The moon-side silhouette line, cel_stand_fire.z pixels wide (fragment() only; c_nv the smooth normal in view space).
float cel_stand_edge(vec3 c_nv, vec3 c_v, mat4 c_vm) {
	if (cel_stand_fire.z <= 0.0) return 0.0;
	float c_e = max(dot(c_nv, c_v), 0.0);
	// (l16 R2) the distance to the outline in pixels from n.v SQUARED: on a round form n.v goes as the root of that distance,
	// so n.v over its own derivative read twice the distance (a 3.5 px ask drew under 2 px); its square is linear in it. The
	// gradient's length, not fwidth (that over-reads a diagonal). The outline is taken where n.v is 0.15, not 0: a coarse
	// lump's smooth normal never reaches 0 at its mesh outline, which broke the line into dashes.
	float c_e2 = max(c_e * c_e - 0.0225, 0.0);
	float c_px = c_e2 / max(length(vec2(dFdx(c_e2), dFdy(c_e2))), 1e-5);
	vec3 c_kv = (c_vm * vec4(cel_key.xyz, 0.0)).xyz;
	float c_side = smoothstep(-0.05, 0.15, dot(c_nv.xy, normalize(c_kv.xy + vec2(1e-5))));
	return (1.0 - smoothstep(cel_stand_fire.z - 0.5, cel_stand_fire.z + 0.5, c_px)) * (1.0 - smoothstep(0.55, 0.65, c_e)) * c_side;
}
// fragment(): the base tone at a world point (EMISSION), and the moon's and her fire's adds for light() (c_moon, c_fire:
// the caller writes them to cel_stm, cel_stf; a varying is assigned in fragment() itself). c_org the piece's foot on the ground (xz: her ramp
// and the moon's give-way are read there, one level a piece, so a tone carries no gradient across a face). c_wn the smooth world normal, c_foot the height over the piece's foot (m), c_lum the paint's luminance here
// (the dabs: the tone x (lum / the family's paint luminance) ^ dab contrast), c_rim the silhouette line (cel_stand_edge).
vec3 cel_stand_base(vec3 c_wp, vec2 c_org, vec3 c_wn, float c_foot, float c_lum, float c_rim, out vec3 c_moon, out vec3 c_fire) {
	vec4 c_x = cel_stand_tone(7);
	float c_dab = c_x.y > 0.0 ? clamp(pow(max(c_lum, 1e-4) / max(c_x.x, 1e-4), c_x.y), 0.5, 1.5) : 1.0;
	float c_d = dot(c_wn, normalize(mix(cel_key.xyz, vec3(0.0, 1.0, 0.0), cel_stand.z)));
	// (l16 R2) stone's own foot band (the shape row's spare, cel_stand_fire.w; 0: the shared one) and a wider margin under
	// the top (0.35: a lump's facets shadow themselves before the smooth normal turns from the moon)
#if CEL_STAND_FAM == 0
	float c_fb = cel_stand_fire.w > 0.0 ? cel_stand_fire.w : cel_stand.w;
	const float c_km = 0.35;
#else
	float c_fb = cel_stand.w;
	const float c_km = 0.2;
#endif
	float c_ft = 1.0 - cel_stand_step(c_foot, c_fb);
	// (the top and the rim only on normals the key lights, with a margin: their edge is this step, not the shadow map's terminator)
	float c_kl = cel_stand_step(dot(c_wn, cel_key.xyz), c_km);
	float c_top = cel_stand_step(c_d, cel_stand.x) * (1.0 - c_ft) * c_kl;
	float c_side = 1.0 - cel_stand_step(c_d, cel_stand.y);
	vec3 c_base = mix(mix(cel_stand_tone(2).rgb, cel_stand_tone(1).rgb, c_side), cel_stand_tone(0).rgb, c_ft);
	vec3 c_lit = mix(c_base, cel_stand_tone(3).rgb, c_top);
	c_lit = mix(c_lit, cel_stand_tone(4).rgb, c_rim * (1.0 - c_ft) * mix(c_top, c_kl, clamp(c_x.z, 0.0, 1.0)));
	float c_g = 1.0;
	c_fire = vec3(0.0);
	if (cel_ember.w > 0.0 && cel_pool_band.x > 0.0) {
		float c_fd = dot(c_wn, normalize(cel_ember.xyz - c_wp));
		float c_m1 = cel_stand_step(c_fd, cel_stand_fire.x), c_m2 = cel_stand_step(c_fd, cel_stand_fire.y);
		c_fire = mix(cel_stand_tone(5).rgb, cel_stand_tone(6).rgb, c_m2) * (c_m1 * c_dab * cel_lum(cel_pool_at(length(c_org - cel_ember.xz)).rgb));
		c_g = mix(1.0, cel_give_of(cel_back_at(vec3(c_org.x, c_wp.y, c_org.y), cel_dapple_at(c_wp)), cel_give.x), c_m1);
	}
	c_moon = max(c_lit - c_base, vec3(0.0)) * (c_g * c_dab);
	return c_base * (c_g * c_dab);
}
// light(): true when this light is the standing material's own (a directional: the key adds the moon's share in open
// moonlight, another adds nothing; her light adds the fire, the leaf's shade cut as on the ground); false: the caller
// lights it as any other (the albedo's response).
bool cel_stand_light(vec3 c_l, vec3 c_lc, float c_att, bool c_dir, mat4 c_iv, inout vec3 c_sl) {
	if (!cel_stand_on()) return false;
	float c_q = cel_gq();
	float c_leaf = 1.0;
	if (cel_key.w > 0.0 && length(cel_gn) > 1.005) c_leaf = clamp((clamp((length(cel_gn) - 1.01 - 2.0 * c_q) / 0.98, 0.0, 1.0) - (1.0 - cel_key.w)) / cel_key.w, 0.0, 1.0);
	if (c_dir) {
		if (dot((c_iv * vec4(c_l, 0.0)).xyz, cel_key.xyz) < 0.98) return true;
		float c_raw = cel_oneshade.x > 0.0 ? clamp(1.0 - (1.0 - c_att) / cel_oneshade.x, 0.0, 1.0) : c_att;
		c_sl += cel_stm * (smoothstep(0.42, 0.58, c_raw) * smoothstep(0.4, 0.6, c_leaf));
		return true;
	}
	if (cel_pool.w <= 0.0 || cel_pool_band.x <= 0.0 || cel_ember.w <= 0.0) return false;
	float c_m = max(c_lc.r, max(c_lc.g, max(c_lc.b, 1e-6)));
	if (dot(abs(c_lc / c_m - cel_pool.rgb), vec3(1.0)) > 0.02) return false;
	float c_sh = c_att > 0.0 ? 1.0 : 0.0;
#if CEL_STAND_FAM == 1
	float c_cut = 1.0 - cel_pool_shade.x * CEL_STAND_LEAF_CUT * (1.0 - c_leaf);
	// (L1 l25 WORLD2) --cel-dbg stand, her light's side: g = the fire's whole cut here (shadow x the canopy-shade cut),
	// b = her light reaches (ATTENUATION > 0); the fragment's r is the moon tones' give-way st_gv
	if (cel_dbg < -0.5) { c_sl += vec3(0.0, c_sh * c_cut, c_sh); return true; }
#else
	float c_cut = 1.0 - cel_pool_shade.x * (1.0 - c_leaf);
#endif
	c_sl += cel_stf * (c_m / PI) * c_sh * c_cut;
	return true;
}
#endif

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
// her flare carry through), and the canopy's leaf shade across it (cel_pool_shade). Called by light() before cel_shade. (Retired: lead 8's
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
	// (Under a leaf: the key's dapple, packed in cel_gn: 1 - cel_key.w under a leaf, 1 open; only where fragment() packed
	// it: an unpacked normal's length is 1. It carries the canopy's opening over her fire, cel_dapple_at.)
	float c_leaf = 0.0;
	if (cel_key.w > 0.0 && length(cel_gn) > 1.005) {
		float c_dr = clamp((length(cel_gn) - 1.01 - 2.0 * cel_gq()) / 0.98, 0.0, 1.0);
		c_leaf = 1.0 - clamp((c_dr - (1.0 - cel_key.w)) / cel_key.w, 0.0, 1.0);
	}
#ifdef CEL_FLOOR
	// (L1 lead 17, P: on a floor with a tone table her light stands in for the moon where the moon is away, at the floor's
	// own lit tone or its shade's by the leaf; the turn of that tone is the albedo's, cel_floor_back)
	if (cel_floor_band.x > 0.0) {
		// (lead 20, MASS3: under a leaf she adds nothing, as before; cel_floor_unit rgb is the floor's reference paint now)
		c_lc = c_m * (1.0 - cel_floor_at(length(c_wp.xz - cel_ember.xz), 0.25).a) * cel_floor_band.yzw * (1.0 - c_leaf);
		c_att = 1.0;
		return;
	}
#endif
	vec4 c_rp = cel_pool_at(length(c_wp.xz - cel_ember.xz));
	vec3 c_ramp = c_rp.rgb;
#ifdef CEL_POOL_PLAIN
	c_ramp /= max(cel_pool_band.y, 1e-3);
#endif
	c_lc = c_m * c_ramp;
	c_att = 1.0;
	// (lead 9's under-leaf cut of her light, for a rig not yet rebuilt (night_play: ember_pool[0..1]). The rebuilt pool
	// (arena_night, R4) has none (0, 0): the fire is not cut by the moon's leaves; the moon comes back under it (ember_give)
	// and its two blues, leaf shade and all, show through the outer band.)
	if (cel_pool_band.z > 0.0 && cel_gq() >= 1.0) c_att = 1.0 - mix(cel_pool_band.z, cel_pool_band.w, c_rp.a) * cel_key.w * c_leaf;
	// (L1 lead 12, R4 round 4: the leaf shade cuts the fire, cel_pool_shade.x: the same hard leaf edge as the moon's shade, so
	// the pool's outline is the outline of leaf shade and the light itself has no edge)
	if (cel_pool_shade.x > 0.0) c_att = 1.0 - cel_pool_shade.x * c_leaf;
}

// The cel model for one light, t = the band's n.l (the caller may wrap it).
void cel_shade(vec3 c_n, vec3 c_nb, float c_t, vec3 c_l, vec3 c_v, vec3 c_lc, float c_att, bool c_dir, vec3 c_albedo, float c_metal, float c_rough,
		float c_spec, float c_spec_amount, vec3 c_backlight, float c_rim, float c_rim_tint, inout vec3 c_dl, inout vec3 c_sl) {
	float c_sh = cel_shadow(c_att, c_dir);
	vec3 c_lv = cel_level(c_t);
	float c_lit_sh = cel_lit(c_t) * c_sh;
	if (c_metal < 1.0) {
#ifdef CEL_S3
		// (L1 lead 12, S3: a standing form's unlit side on the one shade, cel_s3_shape.w)
		c_dl += c_lc * max(c_lv * c_sh, vec3(cel_s3_unlit(c_sh, c_dir))) / PI;
#else
		c_dl += c_lc * c_lv * (c_sh / PI);
#endif
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
#ifdef CEL_STAND
	// (L1 lead 14, K1: the standing material's own lights, the key and her fire, as absolute adds; any other light below)
	else if (cel_stand_light(LIGHT, LIGHT_COLOR, ATTENUATION, LIGHT_IS_DIRECTIONAL, INV_VIEW_MATRIX, c_sl)) { SPECULAR_LIGHT += c_sl; }
#endif
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
#ifdef CEL_S3
		c_sb += cel_s3_add(LIGHT, LIGHT_COLOR, c_t, ATTENUATION, LIGHT_IS_DIRECTIONAL, ALBEDO, INV_VIEW_MATRIX);
#endif
		DIFFUSE_LIGHT += mix(c_da, c_db, cel_on);
		SPECULAR_LIGHT += mix(c_sa, c_sb, cel_on);
	}
#ifdef CEL_HERO_ARM
	CEL_HERO_ARM_LIGHT;   // (L1 lead 19, HER3: the hero's held piece is its two absolute tones, no light on it)
#endif
}
#endif
