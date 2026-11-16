#include "res://shaders/world_clock.gdshaderinc"
#include "res://shaders/flare_world.gdshaderinc"
// The cel model (L1 B1a): the crowd's ink class is 1 (silhouette only); Godot's RIM reproduced and, under cel, stepped;
// the cel rim is the crowd's own edge (crowd_edge below), so the global one is off here.
#define CEL_INK 1
#define CEL_BUILTIN_RIM
#define CEL_NO_RIM
// (L1 B2: the crowd fur class's own rim, godot/data/look/materials.json "edge": x its width in 1 - n.v, y its step;
// LOOK_BIBLE rule 7: one preset for every pack. Its color and strength are the rigs': crowd_rim, crowd_lamp2.w.)
#define CEL_CROWD_EDGE vec2(0.25, 0.04)
// (L1 W2: the class's albedo control goes on the crowd's paint below, so its own night light (the emission) takes it too)
#define CEL_OWN_ALB
// (L1 l9 PACK2: the moon stays on the pack inside her pool, as target 09's cool bodies by her: only the ground gives way)
#define CEL_NO_GIVE
// (L1 lead 12, S3: the crowd STANDS: the moon's top band and rim from the rig (cel.gdshaderinc cel_s3), none on a face her
// fire lights (vat_s3k, set in fragment()); only a rig with "moon_top" draws any of it)
#define CEL_S3
#define CEL_S3_SHARE vat_s3k
// (L1 lead 9: the fur class has no highlight, crowd_fur cel.spec z 0, bible rule 6; the fallback equals the class)
#define CEL_SPEC vec4(9.0, 1.5, 0.0, 0.85)
// (demo-look item 4 pass 2: the den's TOP band, a second light step on the key's planes: fragment() gives its gain x its hard
// mask (vat_den_k, rgb), light() adds it as the key's own diffuse on the albedo, so the fur's value pattern stays and the
// key's cast shadow takes it away like the rest of the key)
varying vec3 vat_den_k;
#define CEL_KEY_ADD (LIGHT_IS_DIRECTIONAL && dot((INV_VIEW_MATRIX * vec4(LIGHT, 0.0)).xyz, cel_key.xyz) > 0.98 ? LIGHT_COLOR * vat_den_k * (cel_shadow(ATTENUATION, true) / PI) : vec3(0.0))
#include "res://shaders/cel.gdshaderinc"
uniform vec2 cel_edge = CEL_CROWD_EDGE;
// (L1 l9 PACK2, rule 7: the moon's rim on the pack in the class's own hue, materials.json crowd_fur "edge_color" FROM target 09's
// backs (#2abbec, cyan-blue, never white or pale silver): rgb that hue at luminance 1, a its share over the rig's rim hue; the
// rig keeps the rim's level (crowd_rim))
uniform vec4 cel_edge_hue = vec4(1.0, 1.0, 1.0, 0.0);
// (H7: a marked foe's rim takes the Flare's school hue while the marks are up: FlareFx.Family; a 0 none)
global uniform vec4 flare_mark_rim;
// H7 r2: a marked foe's light from its pool below (FlareMarksView; flare_family.json marks.lift), x its rim strength.
global uniform float flare_mark_lift;
// The crowd's vertex animation, shared by vat.gdshader (solid bodies, one
// side) and vat_cut.gdshader (fur and hair cards: two sides, cut by alpha).
// See vat.gdshader for what it does.

uniform sampler2D vat_pos : filter_nearest, repeat_disable;
uniform sampler2D vat_nor : filter_nearest, repeat_disable;
uniform int vat_width = 1;
uniform int vat_rows = 1;
// Where this surface's vertices start among all the bake's.
uniform int vat_offset = 0;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform bool use_tex = false;
uniform vec4 albedo : source_color = vec4(1.0);
uniform float roughness = 0.8;
uniform float metallic = 0.0;
uniform vec3 glow_color = vec3(0.0);
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;
uniform float alpha_cut = 0.45;
// Play's moon rim on the crowd (Atmosphere.Set, E1): the key's colour times its strength (rgb), and which way the
// key lies (key_dir, world, toward the light). Godot's RIM is lit by the key, so in the wood's shade a mob had none.
global uniform vec4 crowd_rim;
global uniform vec4 key_dir;
// Rendering 4: the crowd's own light by night, in its own paint (no light added, no shadow). Her pool lit the floor round
// her and its bodies stayed near-black (from the play camera most of a body is its back and shoulders, turned from her
// lamp), so the ring of them leaning at her read as a black starburst. crowd_ember: her lamp's point over her (world xyz)
// and its strength (PlayerView sets it each frame; 0 by day or with --crowd-fill off); crowd_fill: the sky's fill under
// the crowns (rgb, from the preset's hemisphere sky), and the lamp's reach (a).
// Round 2 (its judge: blue-grey plaster miniatures, as light at 10 m as at 2, the dead the lightest rays, pasted on in
// the canopy's shade): the paint is lifted, not floored, and goes into ALBEDO, so the moon's own shadowed light and the
// ambient light the bodies as they light the dirt (they sink in the canopy's shade with it); her lamp is a directional
// warm light, strong within a few metres and gone past its reach; a small unshadowed fill keeps the shade's bodies from
// black; the cool sky only on heads and shoulders. crowd_lamp: her pool's colour (rgb, linear) and the radius her lamp
// is whole within (a); crowd_night: the paint's lift (x: a luminance the darkest paint is raised to), the cut on flat
// and up-facing low surfaces (y), her lamp's wrap (z), the mode (w: 0 off (day), 1 on, 3 a debug mask of distance
// bands for measuring); crowd_top: the cool on heads and shoulders (rgb) and the moon's wrap (a, BACKLIGHT).
global uniform vec4 crowd_ember;
global uniform vec4 crowd_fill;
global uniform vec4 crowd_lamp;
global uniform vec4 crowd_night;
global uniform vec4 crowd_top;
global uniform float crowd_dbg_s;
// Rendering 5 (the r2 judge's numbers): crowd_lamp2 = her lamp's curve on the crowd (x: the inverse-square coefficient k,
// y: the radius it is whole within, z: where it is gone (0: the older smoothstep curve and cuts, for A/B), w: the warm
// rim's strength toward her); crowd_lamp3 = (x: the radius the crowd is held under her, y: the lamp's share there, z: the
// dead's own lift after their tint (a luminance), w: unused).
global uniform vec4 crowd_lamp2;
global uniform vec4 crowd_lamp3;
// H1 round 2C (the round-1 judge: fodder away from her light vanished in the boss's dark): a floor on a foe's outline
// past her lamp's reach, while a boss is up (PlayerView): rgb the hostile hue (linear), a its strength (0: off).
global uniform vec4 crowd_floor;
// Her lamp's reach on the crowd by distance h from her (metres, on the ground): 1 whole, 0 gone.
float crowd_lamp_f(float h) {
	if (crowd_lamp2.z <= 0.0) return 1.0 - smoothstep(crowd_lamp.a, crowd_fill.a, h);
	// (r5: 1 within y, then 1 / (1 + k d^2) - half by 3.5 m, a tenth by 6 m - and gone at z)
	float d = max(h - crowd_lamp2.y, 0.0);
	return (1.0 / (1.0 + crowd_lamp2.x * d * d)) * (1.0 - smoothstep(crowd_lamp2.z - 1.0, crowd_lamp2.z, h));
}
// (and how much of the sky's unshadowed ambient the crowd keeps by night: crowd_amb, AO)
global uniform float crowd_amb;
// H2 R4 (the foes at night, LOOK_BIBLE rules 3 and 7): dark forms with a cold moon edge and her ember's warm side.
// x: where the moon's (and her lamp's) rim starts as a tight edge, smoothstep(x, 1, 1 - NdotV) (0: the older pow 3,
// which from the play camera covered most of a body and made the pack pale smears); y: the crowd's specular by night;
// z: Godot's per-light RIM by night (a scale of rim_amount); w: on (arena nights, Atmosphere.Set).
global uniform vec4 crowd_r4;
// (L1 lead 12, what stands in the night's light; rigs.json "foe_fire" and "foe_moon" on arena_night; zero: the rig has not
// opted in (or --crowd-r4 off / --crowd-fill off) and the crowd is lit as before.) crowd_fire: her fire on a foe is the
// GROUND's ramp (cel_pool_ramp at the foe's ground distance from her light's foot), in two hard bands on faces turned
// toward her: x the bright band's level (a multiplier of the ramp x her lamp, crowd_ember.w), y the second band's share of
// it, z and w the bands' edges in n.l toward her (level: backs and tops take none). The moon gives way on those faces only.
// crowd_moon: x the luminance every foe's paint is pulled to by night (so a moonlit foe reads lighter than its ground,
// about S2 + 0.1) and y how far (0 none, 1 whole); z the fire's residue in a foe's own shadow (crowd_blob_cast.gdshader).
// On a fire face the moon gives way by the ground's own rule (cel_give: wholly inside z metres, none past w). The R4 soft edges (the moon's both-sides rim, the warm rim toward her, Godot's RIM) are off under it: the moon's
// rim is S3's.
global uniform vec4 crowd_fire;
global uniform vec4 crowd_moon;
// (demo-look lane E, item 4: the den's pack, rigs.json "foe_den"; Atmosphere.SetCel. Zero on every other rig: none of it.)
// crowd_den: the body, the paint pulled in Oklab to L x by y, at chroma z and hue w (degrees), so the pack is one dark warm
// grey-brown a step under its ground whatever its fur paint (LOOK_BIBLE "The demo frame: the den", the pack row).
// crowd_den_edge: x the line's width in px at the silhouette, y the body's tone there (a deeper tone, never black), z the
// rim's width in px inside the line, w the rim's share on the key's side for a foe out of her reach.
// crowd_den_rim: rgb the warm rim (linear, its level in), w her reach in metres: inside it the rim is on the side toward her.
global uniform vec4 crowd_den;
global uniform vec4 crowd_den_edge;
global uniform vec4 crowd_den_rim;
// (pass 2) crowd_den_top: x the top band's cut in n.m (m: the key leaned up by y), z its gain on the key's diffuse, w the boss's
// pull (its own paint kept the rest). crowd_den_elite: rgb the elite's band tint (its accent), w its full rim's level.
// crowd_den_boss: rgb the boss's band tint (her cold back), w the boss's body L. The class rides in COLOR.a's 128s (Vat.Push).
global uniform vec4 crowd_den_top;
global uniform vec4 crowd_den_elite;
global uniform vec4 crowd_den_boss;
// (L1 lead 18, W2: the foes' VALUE PLAN by night, target 09. Lead 12's rule "a moonlit foe reads lighter than its ground" is
// withdrawn: the pack was a flat bright-blue cutout (S3's top band lay over a whole back from the play camera) and the
// frame's top contrast, where SHE should be. Now, under crowd_fire (cf_on): OUT IN THE DARK a foe's body sits at the floor's
// shade value (the paint's night luminance, crowd_moon.x), a narrow TOP step on its back (CF_TOP: n toward the leaned-up
// moon, far tighter than S3's edge) and a thin cyan RIM on its moon-side silhouette (S3's edge, cel_s3_shape.z px) say
// "wolf". INSIDE HER GLOW (whole where the ground ramp's level is above CF_KNEE, about 3.6 m, none under CF_REACH, about 5 m)
// the body turns grey-violet (a breath of the fire on every face, CF_AMB; the top step's violet, CF_TOP_IN), the cyan rim
// goes, and the faces turned to her (n toward her, leaned up by CF_UP, past crowd_fire.w) take ONE warm step: CF_WARM's
// hue at a fixed tone (crowd_fire.x x crowd_fire.y: a cel tone, not the ramp's falloff, which left a foe
// 3 m out a faint brown), with a thin gold edge (CF_GOLD at crowd_fire.x) on her-side silhouettes of faces
// past crowd_fire.z. All steps are hard, their edges one screen derivative wide. S3 itself is off on a foe (vat_s3k 0).)
#define CF_KNEE 0.135
#define CF_REACH 0.04
// (L1 lead 21, W3, the tuning round. Main's word: a MID blue-violet body one clear step OVER the floor's shade in the dark
// (crowd_moon.x up), an orange rim on the fire side, no coral or pink patch, nothing cool lighter than her. The pink was two
// things: the warm step ADDED over the blue body (now the body gives way under the warm step and the gold edge: each is its
// own tone, whole), and a HALF-warm step over the 1.4 m where the glow fades (now the step comes on whole over CF_WARM_ON of
// the glow, a narrow band; the gold line alone fades with the glow). The warm planes are slivers toward the light's foot
// (CF_UP down, crowd_fire.w up), the gold line CF_GOLD_PX wide carries the fire side. Inside the glow the moon on the body
// gives way to CF_BODY_IN of itself (the body stays under the lit floor's value). The cyan rim is the px edge alone (one
// clean line; S3's own edge was the patches) and is gone by CF_RIM_GONE of the glow.)
#define CF_UP 0.2
#define CF_AMB 0.006
#define CF_TOP 0.85
#define CF_TOP_OUT vec3(0.02, 0.026, 0.038)   // (l25: a cool value step, was (0.0074, 0.018, 0.051) blue)
#define CF_TOP_IN vec3(0.055, 0.018, 0.036)
#define CF_RIM vec3(0.06, 0.36, 0.54)
// (the warm step's tone, whole: target 09's L 0.49 h 32-36 orange-brown at level crowd_fire.x x crowd_fire.y = 0.35)
#define CF_WARM vec3(1.0, 0.125, 0.04)
// (the gold edge's tone, whole: target 09's L 0.72 h 62 at level crowd_fire.x; never greener: h 78 is lemon)
#define CF_GOLD vec3(1.0, 0.35, 0.04)
#define CF_RIM_PX 2.0
#define CF_GOLD_PX 2.5
#define CF_BODY_IN 0.5
// (a violet lift on every face of the body, so its unlit side also stands over the floor and the moon's blue is calmed)
#define CF_LIFT vec3(0.013, 0.011, 0.011)   // (L1 l25 WORLD: neutral-warm, was violet (0.014, 0.009, 0.02): the lavender streaks)
#define CF_WARM_ON vec2(0.15, 0.45)   // (l25: the warm side further out, was (0.3, 0.6))
#define CF_RIM_GONE 0.35
// (a silhouette edge c_px screen pixels wide from n.v and its screen derivative, on grazing faces only)
float vat_edge_px(vec3 c_n, vec3 c_v, float c_px) {
	float c_nv = clamp(dot(c_n, c_v), 0.0, 1.0);
	return (1.0 - smoothstep(c_px - 0.5, c_px + 0.5, c_nv / max(fwidth(c_nv), 1e-4))) * (1.0 - smoothstep(0.55, 0.65, c_nv));
}
// (whole by 1 - NdotV 0.92: a soft 2-4 px edge on a body at the play camera, not a hairline)
#define CROWD_EDGE_END 0.92
// (the fur and hair cards take crowd_lamp3.w of the edge: both-sided cards at grazing angles lit it as white sparkle)
// (L1 B2: under the cel model (cel_on) the edge is the crowd fur class's rim, cel_edge: whole from 1 - width over its
// step, the same for every pack and every night. It replaces B1a's, which sat where R4's soft ramp was half-way
// (crowd_r4.x, an atmosphere tuning: 0.71 at R4's 0.5) or at 0.79 off R4. At cel_on 0 the edge is R4's exactly.)
float crowd_edge(float rim) {
	float c_e = smoothstep(1.0 - cel_edge.x - 0.5 * cel_edge.y, 1.0 - cel_edge.x + 0.5 * cel_edge.y, rim);
	if (!(crowd_night.w > 0.5 && crowd_r4.w > 0.5 && crowd_r4.x > 0.0)) return mix(pow(rim, 3.0), c_e, cel_on);
	float e = mix(smoothstep(crowd_r4.x, CROWD_EDGE_END, rim), c_e, cel_on);
#ifdef VAT_CUT
	return e * crowd_lamp3.w;
#else
	return e;
#endif
}
// (demo-look item 4) The den's body: the paint in Oklab, its L pulled to crowd_den.x by crowd_den.y, its hue and chroma set.
// (r2 foes, solver 2: cel blocks, all set in Oklab; the paint's own L and hue go by the pull. The pack (class 0) and an elite
// (1): the flank crowd_den.x at chroma crowd_den.z, hue crowd_den.w; the TOP, the world normal's height past crowd_den_top.x
// (the back and crown the play camera looks down on), crowd_den_top.y over it; the belly DEN_BELLY under it. An elite adds
// its affix accent (crowd_den_elite's hue at DEN_ACCENT's L and C) on its ruff's top. The boss (2): its body crowd_den_boss.w
// in the same blocks, warm (the pack's hue); a narrow cold BACK on the torso (the model's own normal past DEN_BOSS_BACK.w,
// DEN_TORSO), the one cold figure in the den, and the blood-red MANE over the neck and shoulders, tufted (DEN_MANE*). Regions
// in the model's space: +Z its head, +Y up, feet at 0, a wolf about 0.95 high (Vat.BakeBeast). Was: the back under the
// flank (r2 solver 1) and a back cold by the world normal past 0.75, which from the play camera was most of the boss. The
// mane's and accent's paint L sits under its screen target: on the top, in the key, they read about 0.1 paler.)
#define DEN_BELLY vec2(-0.2, -0.04)
// (solver 3: the boss's body paint, its own chroma and hue: at the pack's 0.028/32 she read purple-grey on screen, 0.25-0.35 /
// 0.016 / h 313-340, under the lair's cool light; her back and mane paint likewise sit past their screen targets, which
// they reach in the lair: back 0.37/0.025/292, mane 0.43/0.089/30)
#define DEN_BOSS_BODY vec2(0.040, 50.0)
#define DEN_BOSS_BACK vec4(0.43, 0.021, 289.0, 0.93)
#define DEN_TORSO vec2(-0.32, 0.2)
#define DEN_MANE vec3(0.54, 0.11, 34.0)
#define DEN_MANE_Z vec2(0.2, 0.46)
#define DEN_MANE_LOW 0.42
#define DEN_MANE_AXIS 0.62
#define DEN_MANE_TUFT vec2(9.0, 0.05)
#define DEN_ACCENT vec3(0.36, 0.12, 0.80)
// (lead 3 foes: the MID band, the fur's three bands: flank, mid past DEN_MID_CUT of the world normal's y, top past
// crowd_den_top.x; the mid's L step over the flank is crowd_den_rim.w (rigs foe_den [8]), the top's crowd_den_top.y)
#define DEN_MID_CUT 0.3
#define DEN_FLASH_L 0.36
// (lead 3 foes: a den foe's hit is a step in its own paint, never a lift toward white: L up by at most DEN_HIT.x and never
// past DEN_FLASH_L (a block already paler keeps its L), its chroma to at least DEN_HIT.y at hue DEN_HIT.z, warm)
#define DEN_HIT vec3(0.08, 0.075, 40.0)
// (lead 3 foes r2: the boss's hit is half the pack's, its body only: L up DEN_HIT_BOSS.x over its own block (its body sits at
// the cap, so no cap), chroma to at least DEN_HIT_BOSS.y at DEN_HIT's hue; its back and mane keep theirs. At the pack's step
// a struck boss, struck all fight long, read orange-red)
#define DEN_HIT_BOSS vec2(0.04, 0.05)
float vat_den_cut(float c_v, float c_at) {
	float c_w = fwidth(c_v) * 0.5 + 1e-4;
	return smoothstep(c_at - c_w, c_at + c_w, c_v);
}
// (the mane's or ruff's mask: the neck and shoulders over DEN_MANE_LOW, its fore and hind edges in tufts round the neck)
float vat_den_mane(vec3 c_p) {
	float c_ang = atan(c_p.x, c_p.y - DEN_MANE_AXIS);
	float c_tuft = DEN_MANE_TUFT.y * abs(fract(c_ang * DEN_MANE_TUFT.x / 6.2831853) * 2.0 - 1.0);
	return vat_den_cut(c_p.z, DEN_MANE_Z.x + c_tuft) * (1.0 - vat_den_cut(c_p.z, DEN_MANE_Z.y - c_tuft)) * vat_den_cut(c_p.y, DEN_MANE_LOW);
}
vec2 vat_den_ab(float c_c, float c_hd) { return c_c * vec2(cos(radians(c_hd)), sin(radians(c_hd))); }
vec3 vat_den_body(vec3 c_c, float c_cls, float c_ny, vec3 c_p, vec3 c_n, float c_hit) {
	vec3 c_lms = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
		vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(c_c, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	float c_l0 = dot(vec3(0.2104542553, 0.7936177850, -0.0040720468), c_lms);
	vec2 c_ab0 = vec2(dot(vec3(1.9779984951, -2.4285922050, 0.4505937099), c_lms), dot(vec3(0.0259040371, 0.7827717662, -0.8086757660), c_lms));
	bool c_boss = c_cls > 1.5;
	float c_pull = c_boss ? crowd_den_top.w : crowd_den.y;
	float c_top = vat_den_cut(c_ny, crowd_den_top.x), c_belly = 1.0 - vat_den_cut(c_ny, DEN_BELLY.x);
	float c_mid = vat_den_cut(c_ny, DEN_MID_CUT) * (1.0 - c_top);
	float c_l = (c_boss ? crowd_den_boss.w : crowd_den.x) + (crowd_den_top.y * c_top + crowd_den_rim.w * c_mid) * (c_boss ? 0.5 : 1.0)
		+ DEN_BELLY.y * c_belly;
	// (lead 3: the boss body's hue from the rig's boss tint, crowd_den_boss.rgb (foe_den [21-23]), its chroma DEN_BOSS_BODY.x)
	vec3 c_bt = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
		vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(crowd_den_boss.rgb, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
	vec2 c_btab = vec2(dot(vec3(1.9779984951, -2.4285922050, 0.4505937099), c_bt), dot(vec3(0.0259040371, 0.7827717662, -0.8086757660), c_bt));
	vec2 c_ab = c_boss ? DEN_BOSS_BODY.x * normalize(c_btab + vec2(1e-5, 0.0)) : vat_den_ab(crowd_den.z, crowd_den.w);
	float c_hb = c_hit;   // (the hit's share: the boss's body only)
	if (c_boss) {
		float c_back = vat_den_cut(c_n.y, DEN_BOSS_BACK.w) * vat_den_cut(c_p.z, DEN_TORSO.x) * (1.0 - vat_den_cut(c_p.z, DEN_TORSO.y));
		c_l = mix(c_l, DEN_BOSS_BACK.x, c_back);
		c_ab = mix(c_ab, vat_den_ab(DEN_BOSS_BACK.y, DEN_BOSS_BACK.z), c_back);
		float c_mane = vat_den_mane(c_p);
		c_l = mix(c_l, DEN_MANE.x, c_mane);
		c_ab = mix(c_ab, vat_den_ab(DEN_MANE.y, DEN_MANE.z), c_mane);
		c_hb = c_hit * (1.0 - c_back) * (1.0 - c_mane);
	}
	else if (c_cls > 0.5) {
		// (its accent's hue from the rig's elite tint, crowd_den_elite.rgb, linear)
		vec3 c_e = pow(max(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
			vec3(0.0514459929, 0.1073969566, 0.6299787005)) * max(crowd_den_elite.rgb, vec3(0.0)), vec3(0.0)), vec3(1.0 / 3.0));
		vec2 c_eab = vec2(dot(vec3(1.9779984951, -2.4285922050, 0.4505937099), c_e), dot(vec3(0.0259040371, 0.7827717662, -0.8086757660), c_e));
		float c_acc = vat_den_mane(c_p) * vat_den_cut(c_n.y, DEN_ACCENT.z);
		c_l = mix(c_l, DEN_ACCENT.x, c_acc);
		c_ab = mix(c_ab, DEN_ACCENT.y * normalize(c_eab + vec2(1e-5, 0.0)), c_acc);
	}
	c_l += c_boss ? c_hb * DEN_HIT_BOSS.x : c_hit * clamp(DEN_FLASH_L - c_l, 0.0, DEN_HIT.x);
	c_ab = mix(c_ab, vat_den_ab(max(length(c_ab), c_boss ? DEN_HIT_BOSS.y : DEN_HIT.y), DEN_HIT.z), c_hb);
	c_l = mix(c_l0, c_l, c_pull);
	c_ab = mix(c_ab0, c_ab, c_pull);
	vec3 c_m = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775), vec3(0.2158037573, -0.0638541728, -1.2914855480))
		* vec3(c_l, c_ab);
	c_m = c_m * c_m * c_m;
	return clamp(mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147),
		vec3(0.2309699292, -0.3413193965, 1.7076147010)) * c_m, vec3(0.0), vec3(1.0));
}
// (the rim's side: whole past DEN_RIM_CUT of its screen direction's dot with the silhouette's outward normal)
#define DEN_RIM_CUT 0.0
// (r2 foes: the den body's flat share, moved from the lit albedo into its own light, so no smooth tube shading; the flash's
// cap, DEN_FLASH_L, is up with DEN_HIT)
#define DEN_FLAT 0.8
// Moving foes keep about a frame of FSR 2's history, so each frame must be smooth on its own
// (the wolf's fur sparkled): a moving body's paint is read up to this many mips softer, and shine and rim fade
// where the normal turns faster than a pixel can show. (Fading cards edge-on thinned the fur's
// outline and gained nothing at 1.5 mips: dropped.)
// (fading them, not widening the lobe: a rougher lobe spread the sparkle over more pixels).
uniform float tex_bias = 0.0;
uniform float shine_aa = 0.0;

// The cloth's dye, as the person shader has it (shaders/person.gdshader).
uniform bool use_dye = false;
uniform vec3 dye_color = vec3(1.0);
uniform vec3 dye_h = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_s = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_v = vec3(0.0, 1.0, 0.05);
uniform float dye_lum = 0.25;

float dye_band(float x, vec3 r) { return smoothstep(r.x - r.z, r.x, x) * (1.0 - smoothstep(r.y, r.y + r.z, x)); }

vec3 dye_hsv(vec3 c) {
	vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
	vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
	vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
	float d = q.x - min(q.w, q.y);
	return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}

varying flat vec4 fx;
varying flat float fx_crit;
// The hit kit's struck look (BattleFx.HitKit): fx_aa 1 on such a body (fx.x is then its flash blend, 0-0.5, for 2
// frames), fx_rim the gold rim's strength (1 to 0 over 8 frames; held lower by night).
varying flat float fx_rim;
varying flat float fx_aa;
varying vec3 vat_local;
// (demo-look r2 foes: the body's own normal, model space (+Z its head, +Y up), for the den's regions: the boss's back and mane)
varying vec3 vat_nloc;
// (the body's own place in the world, for the Long Cut's burn from the line outward)
varying flat vec3 vat_org;
// How fast the body moves (0 still, 1 fast): FSR 2 keeps little history on it.
varying flat float vat_pace;

// Value noise on the body's own shape (its bake space), so a status's patches stay on the body as
// it moves rather than swimming over it.
float vat_hash(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
float vat_noise(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(vat_hash(i), vat_hash(i + vec3(1.0, 0.0, 0.0)), f.x), mix(vat_hash(i + vec3(0.0, 1.0, 0.0)), vat_hash(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
		mix(mix(vat_hash(i + vec3(0.0, 0.0, 1.0)), vat_hash(i + vec3(1.0, 0.0, 1.0)), f.x), mix(vat_hash(i + vec3(0.0, 1.0, 1.0)), vat_hash(i + vec3(1.0, 1.0, 1.0)), f.x), f.y), f.z);
}

ivec2 vat_coord(int frame, int vid) {
	int row = vid / vat_width;
	return ivec2(vid - row * vat_width, frame * vat_rows + row);
}

void vertex() {
	int vid = vat_offset + VERTEX_ID;
	int f0 = int(INSTANCE_CUSTOM.x + 0.5);
	vat_pace = clamp(fract(INSTANCE_CUSTOM.x) / 0.45, 0.0, 1.0);
	int f1 = int(INSTANCE_CUSTOM.y + 0.5);
	float k = INSTANCE_CUSTOM.z;
	vec3 p0 = texelFetch(vat_pos, vat_coord(f0, vid), 0).xyz;
	vec3 p1 = texelFetch(vat_pos, vat_coord(f1, vid), 0).xyz;
	vec3 n0 = texelFetch(vat_nor, vat_coord(f0, vid), 0).xyz * 2.0 - 1.0;
	vec3 n1 = texelFetch(vat_nor, vat_coord(f1, vid), 0).xyz * 2.0 - 1.0;
	VERTEX = mix(p0, p1, k);
	NORMAL = normalize(mix(n0, n1, k));
	vat_local = VERTEX;
	vat_nloc = NORMAL;
	vat_org = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	int w = int(INSTANCE_CUSTOM.w + 0.5);
	fx = vec4(float(w & 63) / 63.0, float((w >> 8) & 255) / 255.0, float((w >> 16) & 15) / 15.0, float((w >> 20) & 15) / 15.0);
	fx_crit = float((w >> 7) & 1);
	fx_aa = float((w >> 6) & 1);
	fx_rim = fx_aa * clamp((INSTANCE_CUSTOM.y - float(f1)) / 0.45, 0.0, 1.0);
}

#define CROWD_BOUNCE 0.2
#define CROWD_DUST 0.5
void fragment() {
	// Dissolve: the dead go back to the dark in ragged flakes.
	float dn = fract(sin(dot(floor(vat_local * 18.0), vec3(12.9898, 78.233, 37.719))) * 43758.5453);
	// (The Long Cut's burn-up: burnt away like paper from the head down along a ragged edge, not in square flakes,
	// which at 1:1 read as a glitch: FlareFx.LongCut.)
	// It burns from the side facing what struck it (the nearest point of the seam, or her for the sweep) outward.
	if (flare_lc.x > 0.0) {
		// (3-4x finer than r2's 6 and 17: its coarse holes over a dark body read as a beige leopard-spot dissolve)
		// (one octave at 14 a metre, 2.3x r2: at 21 and 47 a cell was a pixel at the play camera and the last of each body
		// went to gold glitter)
		// (vfx9 r4a: coarse, so a body goes in 2-4 big ragged pieces, not glitter: one octave at 2.4 a metre, offset per
		// body, with a 7-a-metre one at an eighth for a torn edge (a quarter laced the edges); the front runs from the line's side and the feet up)
		float bn = vat_noise(vat_local * 2.4 + vat_org * 0.37) * 0.88 + vat_noise(vat_local * 7.0 + 3.1) * 0.12;
		vec2 src = flare_at.xz;
		if (flare_seam.w > 0.0) {
			vec2 sd = vec2(cos(flare_seam.z), sin(flare_seam.z));
			src = flare_seam.xy + sd * clamp(dot(vat_org.xz - flare_seam.xy, sd), 0.0, flare_seam.w);
		}
		vec2 away = vat_org.xz - src;
		away = dot(away, away) > 1e-4 ? normalize(away) : vec2(1.0, 0.0);
		float side = dot((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xz - vat_org.xz, away);
		// (r3: the noise only rags a coherent front from the line's side; at 0.45 its fine holes peppered every body gold)
		dn = clamp((bn - 0.25) / 0.5, 0.0, 1.0) * 0.4 + clamp(0.5 + side / 1.1, 0.0, 1.0) * 0.34 + clamp(vat_local.y / 1.9, 0.0, 1.0) * 0.26;
	}

	// (r4a: the burn edge's width in screen terms, about 2 px: with the coarse noise dn barely changes across a body,
	// so a fixed 0.08 of dn was a band 10-20 cm wide and the seam's pack went to a gold mass at night)
	float dn_ew = clamp(fwidth(dn) * 2.2, 0.008, 0.08);
	if (fx.y > 0.0 && dn < fx.y) discard;
	vec3 c = albedo.rgb;
	vec4 tex = use_tex ? texture(albedo_tex, UV, tex_bias * vat_pace) : vec4(1.0);
	c *= tex.rgb;
#ifdef VAT_CUT
	// Fur and hair cards: cut where the paint is clear.
	ALPHA = tex.a * albedo.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cut;
#endif
	if (use_dye) {
		vec3 hsv = dye_hsv(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)));
		float m = dye_band(hsv.x, dye_h) * dye_band(hsv.y, dye_s) * dye_band(hsv.z, dye_v);
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		c = mix(c, min(dye_color * (lum / dye_lum), vec3(1.0)), m);
	}
	// (a negative red: the copy wears a coat of river mud (CrowdView.TintOf): dark brown patches, heaviest on the legs
	// and the hem, on the body's own shape)
	// (Rendering 4 r2: by night the arena crowd's paint lifted toward crowd_night.x, its hue kept, before its tint, so the
	// dead's darkening (CrowdView.DrawCorpses) still reads; skin and pale paint barely move)
	float cn_l0 = dot(c, vec3(0.2126, 0.7152, 0.0722));
#ifdef VAT_CUT
	// (r5: hair and fur cards are not lifted: they stay the dark of their paint)
	if (crowd_night.w > 0.5 && crowd_lamp2.z <= 0.0) {
#else
	if (crowd_night.w > 0.5) {
#endif
		float cn_l = cn_l0;
		float cn_t = crowd_night.x + cn_l * (1.0 - crowd_night.x);
		c = cn_l > 0.004 ? c * (cn_t / cn_l) : vec3(cn_t);
		// (what the lift adds leans to the dirt's hue (crowd_fill's), so a grey shroud under the blue moon reads as dusty
		// cloth on the dirt, not blue-grey plaster)
		vec3 cn_dirt = crowd_fill.rgb / max(dot(crowd_fill.rgb, vec3(0.2126, 0.7152, 0.0722)), 1e-4);
		c = mix(c, cn_dirt * cn_t, CROWD_DUST * clamp(1.0 - cn_l / max(cn_t, 1e-4), 0.0, 1.0));
	}
	// (L1 W2, B2: the crowd fur class's albedo control, materials.json "albedo", after the night lift and before the copy's own
	// tint, so the dead's darkening and the mud still read; LOOK_BIBLE rule 7: mid-dark bodies, never pale silver)
	c = cel_alb_apply(c);
	// (demo-look item 4: in the den the pack's body is the rig's, crowd_den, before the copy's tint so the dead still darken)
	bool den_on = crowd_den.y > 0.0 && cel_on > 0.0;
	float dn_cls = floor(COLOR.a / 128.0);   // (pass 2: 0 the pack, 1 an elite, 2 the boss; Vat.Push)
	vat_den_k = vec3(0.0);
	float dn_ny = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz).y;
	// (r2 foes, solver 2: alive by the tint's mean, a boss's from 0.3: the Pack-Mother's tint (wolf_alpha's x her frost blue,
	// mean 0.53) under 0.6 left her no den body at all, no line, no rim, lit only, so her underside went black; and a living den
	// foe's tint is not applied (it turned her navy all over); the dead still darken by it)
	float dn_live = den_on ? step(dn_cls > 1.5 ? 0.3 : 0.6, dot(abs(COLOR.rgb), vec3(0.333))) : 0.0;
	// (lead 3: a den foe's hit is its paint's own step (vat_den_body, DEN_HIT): the hit kit's blend (0-0.5) or a struck's)
	float dn_hit = den_on ? clamp(max(2.0 * fx.x * fx_aa * (1.0 - fx_aa * fx_crit), pow(max(fx.x - 0.12, 0.0) / 0.88, 1.5) * (1.0 - fx_aa)), 0.0, 1.0) * dn_live : 0.0;
	if (den_on) c = vat_den_body(c, dn_cls, dn_ny, vat_local, normalize(vat_nloc), dn_hit);
	vec3 dn_c0 = c;   // (r2 foes: the den body before any flash, for the flash's cap below)
	// (L1 lead 12, B3: every foe's paint pulled to one night luminance, its hue kept: crowd_moon)
	bool cf_on = crowd_fire.x > 0.0 && crowd_night.w > 0.5 && cel_pool_band.x > 0.0;
	float vat_s3k = 1.0;
	if (cf_on && crowd_moon.y > 0.0) c *= pow(crowd_moon.x / max(dot(c, vec3(0.2126, 0.7152, 0.0722)), 1e-4), crowd_moon.y);
	// (L1 l9 B2: --crowd-dbg-mode 8, the grey card: the paint's luminance only, every light as it is, to find a hue's root)
	if (crowd_night.w > 7.5 && crowd_night.w < 8.5) c = vec3(dot(c, vec3(0.2126, 0.7152, 0.0722)));
	// (lead 3: the den's dead darken by their tint's value only, in their own warm paint: its cool cast (CrowdView's 0.88/0.92/1
	// per channel) and the rig's cool fill on a fully lit body read blue-lavender in shade; they keep the flat share below too)
	c *= dn_live > 0.5 ? vec3(1.0) : den_on ? vec3(dot(abs(COLOR.rgb), vec3(0.2126, 0.7152, 0.0722))) : abs(COLOR.rgb);
	if (COLOR.r < 0.0 && dn_live < 0.5) {
		float low = 1.0 - smoothstep(0.25, 1.15, vat_local.y);
		float mud = smoothstep(0.5, 0.64, vat_noise(vat_local * 6.5) * 0.8 + low * 0.4) * (0.35 + 0.65 * low);
		c = mix(c, c * vec3(0.36, 0.3, 0.23), mud);
	}
	if (crowd_night.w > 0.5 && crowd_lamp2.z > 0.0 && dot(abs(COLOR.rgb), vec3(0.333)) < 0.6) {
		// (r5: the dead are lifted again after their darkening, to a floor of their own, so they never sink under their ground)
		float cd_l = dot(c, vec3(0.2126, 0.7152, 0.0722));
		float cd_t = crowd_lamp3.z + cd_l * (1.0 - crowd_lamp3.z);
		c = cd_l > 0.002 ? c * (cd_t / cd_l) : vec3(cd_t);
	}
	float rim = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	vec3 sky = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	float up = clamp(dot(NORMAL, sky), 0.0, 1.0);
	// A status reads on the body in patches and at its edge, never as a wash over the whole of it.
	// Washes turned a crowd of pale risen white in Hoarfrost and cream in Cinderfall: AgX folds a
	// bright hue to white past about 1, and the glow blooms what is over 1.1. So the ice is darker
	// and bluer than a pale body, not paler, and every status light stays under 1.
	float rough = roughness;
	vec3 e = glow_color;
	// Burns Twice's glaze takes the rime's place in its reach (flare_world.gdshaderinc): the fight freezes the
	// whole reach at once, but a body glazes only as the frost's front reaches it (t10: all rimed by frost +0.1 s).
	// (the Long Cut sends its death's class in the frozen slot: 1/15 an ash death, off the drawn seam; never ice)
	float lc_ash = flare_lc.x > 0.0 && fx.z > 0.0 ? 1.0 : 0.0;
	float fz = flare_lc.x > 0.0 ? 0.0 : fx.z > 0.0 && flare_live() && flare_frosting((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz) ? 0.0 : fx.z;
	if (fz > 0.001) {
		// Frozen (chill to half): rime grows in patches on what faces up, a cold blue at a
		// middle value that a pale body shows against; the ice is glossy, with a thin cold rim
		// and a few glints.
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		float rime = smoothstep(0.42, 0.62, vat_noise(vat_local * 5.0) * 0.75 + up * 0.45) * smoothstep(0.0, 0.5, fz);
		vec3 ice = vec3(0.16, 0.36, 0.62) * (0.7 + 0.6 * clamp(lum, 0.0, 0.6));
		c = mix(c, vec3(lum) * vec3(0.9, 0.97, 1.08), fz * 0.3);
		c = mix(c, ice, rime * 0.85);
		rough = mix(rough, 0.22, rime);
		float glint = step(0.992, vat_hash(floor(vat_local * 16.0) + floor(WORLD_TIME * 3.0)));
		e += vec3(0.28, 0.62, 1.0) * fz * pow(rim, 4.0) * 0.85 + vec3(0.55, 0.8, 1.0) * rime * glint * 0.8;
	}
	if (fx.w > 0.0) {
		// Burning: thin tongues of fire licking up the body from its edges over char, soot where
		// they have been; the flame is deep orange over near-black, so it stays orange (over a pale
		// body's own light it read as peach). The rest of the body is its own colour.
		float lick = vat_noise(vec3(vat_local.x * 4.5, vat_local.y * 1.6 - WORLD_TIME * 3.4, vat_local.z * 4.5));
		float tongue = smoothstep(0.52, 0.8, lick * 0.75 + rim * 0.5) * fx.w;
		float soot = smoothstep(0.28, 0.56, lick * 0.75 + rim * 0.35) * fx.w;
		if (flare_lc.x > 0.0) {
			// The Long Cut's burn-up is char, not fire: the body goes dark, and its dawn-gold lives only in a ragged
			// band just ahead of the burn line (the dissolve's edge, below). Tongues by the rim lit most of a body
			// from the play camera ("rim" is nearly all of it from up here): the struck pack read as cream plaster
			// ghosts with black heads (vfx9 fix2). (night: the struck bodies' glow at 0.6, the luminance cap)
			// r3: the char is the body's own paint at a quarter, floored (a flat near-black tint read as a missing
			// texture: vfx9 r2), lit through its own normals, matte, and seamed with dawn-gold cracks at HDR 4
			// (0.6x at night, the luminance cap). fx.w is the char's amount.
			float lc_night = mix(1.0, 0.6, flare_hue.a);
			// (r4a: was mix(1, 0.6, flare_lc.w), but flare_lc.w is the sweep band's gain, 7 by day: -1.8, so by day every gold
			// term on the struck was negative light and they went flat black, "no gold reads in sunlight")
			if (lc_ash > 0.0) {
				// vfx9 r4a: the sweep's dead, off the seam: greyed to about half their own value, a little drained, lit and
				// shaded as ever (never a flat silhouette), and a dark charred lip where they fall away; no gold.
				float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
				c = mix(c, mix(c, vec3(lum) * vec3(1.04, 0.98, 0.9), 0.4) * 0.52, fx.w);
				rough = mix(rough, 0.86, fx.w);
				if (fx.y > 0.0) c *= 1.0 - 0.45 * smoothstep(fx.y + dn_ew * 1.5, fx.y, dn);
			} else {
			vec3 c0 = c;
			// (r4a: half its paint, warm-browned: at a quarter or 0.42 the seam's dead were flat black cut-outs by day)
			c = mix(c, max(c * 0.5 * vec3(1.0, 0.88, 0.76), vec3(0.06, 0.05, 0.043)), fx.w);
			rough = mix(rough, 0.88, fx.w);
			// (r4a: the seam's light from below, in the body's own paint: warmest at the feet and on what faces down)
			float down = clamp(-dot(NORMAL, sky), 0.0, 1.0);
			e += vec3(1.0, 0.55, 0.2) * max(c0, vec3(0.12)) * (1.0 - smoothstep(0.0, 1.3, vat_local.y)) * (0.45 + 0.55 * down) * fx.w * 1.1 * lc_night;
			float cn = vat_noise(vat_local * vec3(7.0, 4.5, 7.0)) * 0.7 + vat_noise(vat_local * 15.0) * 0.3;
			// (thin and broken: r3a's 0.035-wide net over every body read as a pale lattice)
			float crack = (1.0 - smoothstep(0.0, 0.016, abs(cn - 0.5))) * smoothstep(0.4, 0.62, vat_noise(vat_local * 3.0 + 7.0));
			// (r4a: the cracks only up from the feet, where the seam's light is: over whole bodies they were a carpet)
			crack *= 1.0 - smoothstep(0.25, 1.0, vat_local.y);
			// (final cuts: no gold cracks on the seam's dead; the char and the light from below stay)
			float lc_unused = crack;
			}
		} else {
			c *= (1.0 - soot * 0.72) * (1.0 - tongue * 0.9);
			e += vec3(1.0, 0.3, 0.03) * tongue + vec3(1.0, 0.42, 0.08) * pow(rim, 3.0) * fx.w * 0.5;
		}
	}
	// Struck past the crowd's rim-only flare (a champion's, a few at once): the body's paint is lifted, lit
	// by the scene's own light, so the flash keeps its shading and is as bright as the place allows. An
	// added light lit it as if by day: at night the Barrow Knight went a flat cream cut-out, struck after
	// struck, and read as a model glitch (Experience 9's judge, 27 October).
	// (half the old falloff's power: at s^3 a champion's blow was gone before a frame at 1:1 caught it)
	float struck = pow(max(fx.x - 0.12, 0.0) / 0.88, 1.5) * (1.0 - fx_aa);
	// A critical's is bigger and warmer, for the two or three frames its flash is high: 1.6x the lift and the rim's pop,
	// and a warm breath that reaches the darks (a grey hood lifted x2.6 of its own paint stayed grey; round 3's judge).
	float crit_k = 1.0 + 0.6 * fx_crit;
	// (its own hue only, and warm: a lift toward white, even shaded, read as an untextured clay body; at x2.3
	// a grey hood under firelight still went white)
	// (The Long Cut's struck get no lift: their flash is a gold rim only, the first frames of the burn-up; a lifted
	// pale body was the start of the cream ghosts: vfx9 fix2.)
	float lc_k = flare_lc.x > 0.0 ? 1.0 : 0.0;
	c = min(c * (1.0 + 1.6 * crit_k * struck * (1.0 - lc_k) * vec3(1.0, 0.85, 0.7)) + vec3(0.16, 0.08, 0.04) * fx_crit * struck * (1.0 - lc_k), vec3(0.85 + 0.05 * fx_crit));
	// The hit kit's flash: a warm white over the body's paint at up to half, lit by the scene (so no glowing cut-out
	// by night), for its first 2 frames only.
	// (F1 r5: the hit kit's flag with a critical's (never both otherwise) is the ember look, CrowdView: no blend there)
	float fx_ember = fx_aa * fx_crit;
	c = mix(c, vec3(1.0, 0.86, 0.62), fx.x * fx_aa * (1.0 - fx_ember));
	// (r2 foes: in the den a hit lifts the body at most DEN_FLASH x in linear, about +0.06 L: a pale hit wolf read L 0.61-0.75)
	// (solver 2: and never past Oklab L DEN_FLASH_L (luminance its cube) unless its own block is paler, the boss's mane)
	// (lead 3: in the den a living foe's hit is in its paint already, dn_c0 (DEN_HIT): no lift, no blend toward white)
	if (den_on && dn_live > 0.5) c = dn_c0;
	ALBEDO = c;
	vec3 dnx = dFdx(NORMAL), dny = dFdy(NORMAL);
	float busy = shine_aa * smoothstep(0.02, 0.3, 0.5 * (dot(dnx, dnx) + dot(dny, dny)));
	// Never fully rough: Godot's RIM falls off as pow(1 - NdotV, (1 - ROUGHNESS) * 16), so at roughness 1 (an imported
	// texture's default: the lamplings' and the skeletons' bodies) the "rim" is 1 everywhere and RIM lays every light's
	// colour over the whole body, mostly white (rim_tint 0.35). Grimtunnel's dark mauve hide read as glowing cyan in C03's
	// ford lamps. At 0.9 it is a rim again ((1 - NdotV)^1.6) and the sheen barely moves.
	ROUGHNESS = min(rough, 0.9);
	SPECULAR = 0.5 * (1.0 - busy);
	METALLIC = metallic;
	RIM = den_on ? 0.0 : rim_amount * (1.0 - busy);
	RIM_TINT = rim_tint;
	// Struck: a warm flare that lives at the rim, so the body keeps its shape
	// from thirty metres up, with only an instant's glow across the whole of it
	// (a full white-hot body bloomed the pale risen into blobs).
	float hot = fx.x * fx.x;
	// (At 0.75 across the whole body a pale body lost its paint and read as a ghost.)
	// The rim-only flare (the crowd's, up to 0.12) as it was. Past it, the lifted paint above and a hot
	// edge, never a flat wash: from the play camera most of a body is "rim", so rim^2 x 1.1 plus 0.38
	// over all of it was a flat unlit cream body.
	float low = min(fx.x, 0.12) * (1.0 - fx_aa), high = max(fx.x - 0.12, 0.0) / 0.88;
	// (the rim's breath gives way as the struck lift comes: at night it alone was a pale wash)
	// (none on the Long Cut's struck: under the sweep at night the whole pack's breath was a field of pale ghosts)
	float dn_fx = den_on && dn_live > 0.5 ? 0.0 : 1.0;   // (lead 3: no struck light on a living den foe: its hit is DEN_HIT)
	e += vec3(1.0, 0.86, 0.72) * low * (1.0 - high) * (0.1 + rim * rim * 1.1) * (1.0 - lc_k) * dn_fx;
	// (and a breath of warm light in its own paint: no rim term, which covers the whole body from up here,
	// and no more, or the night's dark body goes pale)
	e += vec3(1.0, 0.62, 0.38) * c * struck * 0.25 * crit_k * dn_fx;
	// (and a pop at its edge, in its own paint: scaled by c, or from up here the rim covers the whole body
	// and it is the old cream cut-out again)
	e += c * 0.6 * crit_k * struck * pow(rim, 3.0 - fx_crit) * (1.0 - lc_k) * dn_fx;
	e += vec3(1.0, 0.55, 0.16) * struck * pow(rim, 4.0) * 0.9 * lc_k * mix(1.0, 0.6, flare_hue.a);
	// The hit kit's struck rim (BattleFx.HitKit: her auto-attacks' struck, 2 frames): gold-white at the body's
	// edge, not scaled by its paint (a black wolf at night has none to lift), tight so the body keeps its shape.
	// (tight: at rim^2 x3.4 from the play camera every struck body went a white ghost, r4)
	// (r3: gold #FFB84A, fresnel power 3 cut to its outermost edge (from up here most of a body is "rim"; at 0.55 it washed them) so it is ~2-3 px on a 70 px body; strength 1 to 0 over
	// 8 frames, held to ~0.55 by night (BattleFx.StruckRimOn); never the cream ghost)
	e += mix(vec3(1.0, 0.479, 0.069), flare_mark_rim.rgb, flare_mark_rim.a) * fx_rim * pow(rim, 3.0) * smoothstep(0.8, 0.97, rim) * 1.8;
	// (F1 r5) The ember look: a launched mass-kill body (strength 1, its flight's first frames) and a struck survivor
	// after the pool (0.45): ember light through the whole body and a hot band at its edge, in light, not paint (a pale
	// blend over a blue wolf by night read as an ice ghost), so the kill out-shouts the frame and keeps its shape.
	// (own look: 0.22 through the body went a peach-cream ghost under bloom: the body stays dark, the edge carries it)
	e += vec3(1.0, 0.38, 0.06) * fx_ember * fx_rim * (0.07 * fx_rim + 1.6 * smoothstep(0.4, 0.9, rim));
	// (H7 r2, judge r1 fix 5: the foe stands in its mark's pool, so the pool lights it from below: its lower body and the
	// faces turned from the sky, in the school's light, x its own paint (light, not paint: a dark body stays dark))
	e += flare_mark_rim.rgb * flare_mark_rim.a * flare_mark_lift * fx_rim * c * exp(-max(vat_local.y, 0.0) / 0.8) * (0.35 + 0.65 * (1.0 - up));
	// (M5 r3) COLOR.a: the glow in its fraction; a champion's affix rim in its whole part (1 + its hue in 64ths of the
	// wheel, CrowdView/Vat.Push). The rim: a colored edge glow of the affix's hue, emitted (so night and shade keep it),
	// tight at the silhouette with a faint wider breath, never a neon outline. Functional; L1 owns the final look.
	float champ_code = floor(COLOR.a) - 128.0 * floor(COLOR.a / 128.0);
	e += c * fract(COLOR.a);   // (the glow is the fraction alone: the den class rides in the 128s, pass 2)
	if (champ_code > 0.5) {
		float ch_h = (champ_code - 1.0) / 64.0;
		vec3 ch_c = clamp(abs(mod(ch_h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
		ch_c = mix(vec3(1.0), ch_c, 0.72);
		// (r3 shot: at 0.62 a thin skeleton was all edge from up here and glowed whole; a broad boar's back took a hairline)
		float ch_k = smoothstep(0.72, 0.97, rim) * 1.3 + smoothstep(0.4, 0.85, rim) * 0.1;
		e += ch_c * ch_k * (1.0 - fx.y);
	}
	// The moon's rim, in shade as in its light: strongest on the side toward the key, a breath on the far side.
	if (crowd_rim.a > 0.0 && !cf_on && !den_on) {   // (demo-look item 4 pass 2: the den's pack has its own stepped rim)
		vec3 kv = normalize((VIEW_MATRIX * vec4(key_dir.xyz, 0.0)).xyz);
		float side = 0.3 + 0.7 * clamp(dot(NORMAL, kv) * 0.5 + 0.5, 0.0, 1.0);
		vec3 cr_c = mix(crowd_rim.rgb, cel_edge_hue.rgb * dot(crowd_rim.rgb, vec3(0.2126, 0.7152, 0.0722)), cel_edge_hue.a * cel_on);
		e += cr_c * crowd_rim.a * crowd_edge(rim) * side * (1.0 - busy);
	}
	// Her lamp and the sky's fill on the crowd by night (crowd_ember, crowd_fill, crowd_lamp, crowd_night, crowd_top above).
	// Her lamp: from over her, barely wrapped, so a body in her pool has a warm side toward her and a dark side away,
	// whole within crowd_lamp.a and gone at the reach. A small fill in the dirt's hue, unshadowed (the moon's shadowed
	// light is ALBEDO's); the cool sky only on heads and shoulders. Flat and up-facing low surfaces (the lying, the
	// lunging backs) take less, so they sit under the standing ring.
	float cn_flat = 0.0;
	if (crowd_night.w > 0.5) {
		vec3 cw_p = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec3 cw_n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
		vec3 cw_l = crowd_ember.xyz - cw_p;
		float cw_d = length(cw_l);
		float cw_h = length(cw_p.xz - crowd_ember.xz);
		// (and a breath of her pool's bounce off the dirt on the far side, so a back turned to her is dark, not black)
		float cw_wrap = CROWD_BOUNCE + (1.0 - CROWD_BOUNCE) * clamp((dot(cw_n, cw_l / max(cw_d, 1e-3)) + crowd_night.z) / (1.0 + crowd_night.z), 0.0, 1.0);
		float cw_f = crowd_lamp_f(cw_h);
		cn_flat = smoothstep(0.55, 0.9, cw_n.y) * (1.0 - smoothstep(0.9, 1.4, vat_local.y));
		float cn_k = 1.0 - crowd_night.y * cn_flat;
		float cn_head = smoothstep(1.2, 1.6, vat_local.y) * clamp(cw_n.y, 0.0, 1.0);
		if (cf_on) {
			// (L1 lead 12, B2: her fire on the foe from the ground's ramp at its ground distance from her light's foot, two hard
			// bands by n.l toward her (level with the ground: a back or a top takes none), the dead by their darkening; leaf
			// shade does not cut it (a foe stands up out of the ground's shade); the moon, its fill and S3 give way on those
			// faces only, as the ground's moon does by distance (cel_give))
			// (L1 lead 18, W2: the value plan above)
			vec4 cf_rp = cel_pool_at(cw_h);
			float cf_mx = max(cf_rp.r, max(cf_rp.g, cf_rp.b));
			vec3 cf_hue = cf_rp.rgb / max(cf_mx, 1e-4);
			float cf_g = clamp((cf_mx - CF_REACH) / (CF_KNEE - CF_REACH), 0.0, 1.0) * step(0.001, crowd_ember.w);
			float cf_alive = clamp(dot(abs(COLOR.rgb), vec3(0.333)), 0.0, 1.0);
			vec2 cf_to = crowd_ember.xz - cw_p.xz;
			vec2 cf_dir = cf_to / max(length(cf_to), 1e-3);
			float cf_t = dot(cw_n, normalize(vec3(cf_dir.x, CF_UP, cf_dir.y)));
			float cf_w = fwidth(cf_t) * 0.75 + 0.01;
			float cf_b1 = smoothstep(crowd_fire.z - cf_w, crowd_fire.z + cf_w, cf_t), cf_b2 = smoothstep(crowd_fire.w - cf_w, crowd_fire.w + cf_w, cf_t);
			float cf_warm = cf_b2 * smoothstep(CF_WARM_ON.x, CF_WARM_ON.y, cf_g);
			float cf_edge = cf_b1 * cf_g * vat_edge_px(NORMAL, VIEW, CF_GOLD_PX) * (1.0 - busy);
			float cf_give = cf_b2 * cel_give.x * (1.0 - smoothstep(cel_give.z, max(cel_give.w, cel_give.z + 1e-3), cw_h));
			// (W3: the body gives way whole under the warm step and the gold edge, and to CF_BODY_IN of itself inside the glow)
			float cf_keep = (1.0 - max(cf_give, max(cf_warm, cf_edge) * cf_alive)) * mix(1.0, CF_BODY_IN, cf_g);
			// (the moon's own steps on a foe: the top step and the rim, in place of S3's)
			float cf_tm = dot(cw_n, normalize(mix(cel_key.xyz, vec3(0.0, 1.0, 0.0), cel_s3_shape.y)));
			float cf_tw = fwidth(cf_tm) * 0.75 + 0.01;
			float cf_top = smoothstep(CF_TOP - cf_tw, CF_TOP + cf_tw, cf_tm) * (1.0 - max(cf_warm, cf_edge));
			float cf_ms = smoothstep(-0.1, 0.3, dot(NORMAL, normalize((VIEW_MATRIX * vec4(cel_key.xyz, 0.0)).xyz)));
			float cf_rim = vat_edge_px(NORMAL, VIEW, CF_RIM_PX) * cf_ms * (1.0 - smoothstep(0.0, CF_RIM_GONE, cf_g)) * (1.0 - busy);
			e += mix(mix(CF_TOP_OUT, CF_TOP_IN, cf_g) * cf_top, CF_RIM, cf_rim) * cf_alive;
			e += cf_hue * (CF_AMB * cf_g * cf_alive);
			e += mix(CF_WARM * (crowd_fire.y * cf_warm), CF_GOLD, cf_edge) * (crowd_ember.w * crowd_fire.x * cf_alive);
			e += (c * (crowd_fill.rgb + crowd_top.rgb * cn_head) + CF_LIFT * cf_alive) * cf_keep;
			cn_k = cf_keep;
			vat_s3k = 0.0;
		} else if (crowd_lamp2.z > 0.0) {
			// (r5: the flat and the dead lose only the lamp, not the moon or the fill; the crowd close to her takes a share of it
			// so she reads over the ring; a warm rim on the side toward her)
			float cw_near = mix(crowd_lamp3.y, 1.0, smoothstep(crowd_lamp3.x, crowd_lamp3.x + 1.0, cw_h));
			e += c * (crowd_lamp.rgb * crowd_ember.w * cw_wrap * cw_f * cw_near * cn_k + crowd_fill.rgb + crowd_top.rgb * cn_head);
			vec3 cw_v = normalize((VIEW_MATRIX * vec4(cw_l, 0.0)).xyz);
			float cw_side = clamp(dot(NORMAL, cw_v) * 0.5 + 0.5, 0.0, 1.0);
			e += crowd_lamp.rgb / max(dot(crowd_lamp.rgb, vec3(0.2126, 0.7152, 0.0722)), 1e-4) * crowd_lamp2.w * crowd_edge(rim) * cw_side * cw_side * cw_f * cw_near * (1.0 - busy) * step(0.001, crowd_ember.w);
			cn_k = 1.0;
		} else {
			e += c * (crowd_lamp.rgb * crowd_ember.w * cw_wrap * cw_f + crowd_fill.rgb + crowd_top.rgb * cn_head) * cn_k;
		}
		// (the floor: a faint rim in the hostile hue, at the outermost edge only (from up here most of a body is "rim": a wider
		// one washed the pack pale pink), where her lamp is gone; none on the dead)
		if (crowd_floor.a > 0.0 && dot(abs(COLOR.rgb), vec3(0.333)) >= 0.6)
			e += crowd_floor.rgb * crowd_floor.a * pow(rim, 3.0) * smoothstep(0.78, 0.97, rim) * (1.0 - cw_f) * (1.0 - busy) * (1.0 - cn_flat * 0.6);
		ALBEDO *= cn_k;
		if (crowd_r4.w > 0.5) { SPECULAR = crowd_r4.y * (1.0 - busy); RIM = cf_on ? 0.0 : rim_amount * crowd_r4.z * (1.0 - busy); }
		// (the moon wrapped round the body in its own shadowed light (Godot's backlight: the far side takes what the near
		// side would), so under the canopy's dark the bodies sink with the dirt and in its pools they take it as the dirt does)
		BACKLIGHT = vec3(crowd_top.a);
		// (less of the unshadowed ambient, which lit them alike in the canopy's dark and in its pools)
		AO = crowd_amb;
		if (crowd_night.w > 2.5 && crowd_night.w < 7.5) {
			// (the debug masks, for tools/render/crowd_lamp_measure.py; ALBEDO and every light off, an emission of 0.4 on one
			// channel. Mode 3: red within 5 m of her, green 8-12 m, blue between; yellow the flat; magenta the dead. Mode 4:
			// red within 1.5 m of her, green 1.5-2.5 m, blue 3-4 m. Mode 5: red 5.5-6.5 m, green 6.5-7.5 m, blue past 7.5 m.
			// Mode 6 (the paint): red cloth, green skin, blue hair and fur. Mode 7: her lamp's factor as a grey (scaled by
			// crowd_dbg_s), to read the falloff curve off the picture.)
			bool dead = dot(abs(COLOR.rgb), vec3(0.333)) < 0.6;
			ALBEDO = vec3(0.0);
			int dm = int(crowd_night.w + 0.5);
			if (dm == 4) e = cw_h < 1.5 ? vec3(0.4, 0.0, 0.0) : (cw_h >= 1.5 && cw_h < 2.5) ? vec3(0.0, 0.4, 0.0) : (cw_h >= 3.0 && cw_h < 4.0) ? vec3(0.0, 0.0, 0.4) : vec3(0.0);
			else if (dm == 5) e = (cw_h >= 5.5 && cw_h < 6.5) ? vec3(0.4, 0.0, 0.0) : (cw_h >= 6.5 && cw_h < 7.5) ? vec3(0.0, 0.4, 0.0) : cw_h >= 7.5 ? vec3(0.0, 0.0, 0.4) : vec3(0.0);
			else if (dm == 6) {
#ifdef VAT_CUT
				e = vec3(0.0, 0.0, 0.4);
#else
				e = cn_l0 < 0.08 ? vec3(0.4, 0.0, 0.0) : vec3(0.0, 0.4, 0.0);
#endif
			}
			else if (dm == 7) e = vec3(crowd_lamp_f(cw_h) * crowd_dbg_s);
			else
			e = dead ? vec3(0.4, 0.0, 0.4) : cn_flat > 0.5 ? vec3(0.4, 0.4, 0.0) : cw_h < 5.0 ? vec3(0.4, 0.0, 0.0) : (cw_h > 8.0 && cw_h < 12.0) ? vec3(0.0, 0.4, 0.0) : cw_h <= 8.0 ? vec3(0.0, 0.0, 0.4) : vec3(0.0);
		}
	}
	// Ember at the dissolve's edge.
	// (the Long Cut's: a thin dawn-gold line, kept a colour: at 2x of a pale gold it tonemapped to white)
	// (r3: a 0.03 band at HDR 3.5, still a gold, never cream: its hue stays deep)
	// (r4a: about 2 px wide on the seam's deaths (dn_ew), so it survives sunlight; none on the ash deaths)
	// (r3c: out by fx.y 0.62, so the last ~30% of a body (dn spans ~0.14-0.86) goes as dark ash, not gold lace or dust)
	if (fx.y > 0.0) e += (flare_lc.x > 0.0 ? vec3(1.0, 0.46, 0.1) * mix(1.0, 0.6, flare_hue.a) : vec3(1.0, 0.45, 0.12)) * (flare_lc.x > 0.0 ? smoothstep(fx.y + dn_ew, fx.y, dn) * 3.5 * (1.0 - smoothstep(0.46, 0.62, fx.y)) * 0.0 /* final cuts: no gold burn edge */ : smoothstep(fx.y + 0.12, fx.y, dn) * 3.0);

	// (demo-look item 4) The den's pack: a line at the silhouette, the body's own tone deepened (crowd_den_edge.y, never
	// black), and inside it a hard warm rim on the side toward her within her reach (crowd_den_rim.w), toward the key past
	// it at crowd_den_edge.w of the level; none on the dead. Her lamp does not light the pack here (PlayerView.CrowdOmni).
	if (den_on) {
		float dn_alive = dn_live;
		float dn_line = vat_edge_px(NORMAL, VIEW, crowd_den_edge.x);
		// (r2 foes, solver 2: the rim one unbroken stroke on the lit edge. Its side is the screen's: the silhouette's outward
		// normal (view NORMAL.xy) toward the key's screen direction leaned to screen-up by crowd_den_edge.w, past DEN_RIM_CUT, so it
		// runs the whole back; no busy fade (it cut the stroke into dashes on a 60 px wolf) and no turn toward her. An elite or the
		// boss takes a FULL rim, all round, at crowd_den_elite.w at least.)
		float dn_band = vat_edge_px(NORMAL, VIEW, crowd_den_edge.x + crowd_den_edge.z) * (1.0 - dn_line);
		vec3 dn_kv = (VIEW_MATRIX * vec4(key_dir.xyz, 0.0)).xyz;
		vec2 dn_ks = normalize(mix(normalize(dn_kv.xy + vec2(0.0, 1e-4)), vec2(0.0, 1.0), crowd_den_edge.w) + vec2(0.0, 1e-4));
		float dn_side = vat_den_cut(dot(normalize(NORMAL.xy + vec2(0.0, 1e-4)), dn_ks), DEN_RIM_CUT);
		float dn_full = step(0.5, dn_cls);
		e += crowd_den_rim.rgb * (dn_band * dn_alive * mix(dn_side, max(crowd_den_elite.w, dn_side), dn_full));
		// (lead 3: the dead keep the flat share too, so the rig's cool fill does not light them blue-lavender in shade)
		e += ALBEDO * DEN_FLAT;
		ALBEDO *= (1.0 - DEN_FLAT) * mix(1.0, crowd_den_edge.y, dn_line);
		e *= mix(1.0, crowd_den_edge.y, dn_line);
		// (measuring, crowd_den_top.z: 1 each class flat in its own light (pack green, elite blue, boss magenta), the masks for
		// tools; 2 the model's space (hue by z in 0.1 m bands from -0.6, a dark line every 0.1 m of y); 0 in play)
		if (crowd_den_top.z > 0.5) {
			ALBEDO = vec3(0.0);
			vec3 dn_pz = clamp(abs(mod(clamp(floor((vat_local.z + 0.6) / 0.1) / 12.0, 0.0, 1.0) * 5.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
			e = crowd_den_top.z < 1.5 ? (dn_cls > 1.5 ? vec3(3.0, 0.0, 3.0) : dn_cls > 0.5 ? vec3(0.0, 0.0, 3.0) : vec3(0.0, 3.0, 0.0))
				: dn_pz * (fract(vat_local.y / 0.1) < 0.12 ? 0.15 : 1.0);
		}
	}
	EMISSION = e;

	// The Flare's drain and glaze (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_body((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, NORMAL, INV_VIEW_MATRIX, rim, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
		// The BOOM's line reaching a statue: the fire through its cracks before it bursts.
		EMISSION += vec3(1.0, 0.32, 0.05) * flare_crack((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz) * (0.45 + 0.9 * rim);
		// The fireball on the statues (judge 5b fix 3): their faces toward it mixed to its colour (amber added on cyan
		// came out grey), the far faces left cyan, so each statue is two-tone.
		if (flare_fire.w > 0.0) {
			float fw = clamp(flare_fire_w((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz)), 0.0, 1.0);
			vec3 fc = flare_fire_col();
			// Only the ice takes the fire's colour (judge 7 (1): a charred body painted fc * 0.55 by it read as a beige
			// mannequin until the fire went); the char keeps its black and catches the fire at its rim only.
			float ice = clamp(fx.z * 2.0, 0.0, 1.0);
			ALBEDO = mix(ALBEDO, fc * 0.55, fw * 0.8 * ice);
			EMISSION = mix(EMISSION, fc * fire_rim, fw * ice) + fc * fire_rim * fw * (1.0 - ice) * pow(rim, 3.0) * 0.35;
		}
	}
	// (L1 l9 B2, measuring: --crowd-dbg-mode 9 the emission alone (no lit paint), 10 the lit paint alone (no emission))
	if (crowd_night.w > 8.5 && crowd_night.w < 9.5) ALBEDO = vec3(0.0);
	if (crowd_night.w > 9.5 && crowd_night.w < 10.5) EMISSION = vec3(0.0);
	// The cel model's end of fragment (cel.gdshaderinc: geometric normal, ink tag, debug).
	CEL_FRAGMENT;
}
