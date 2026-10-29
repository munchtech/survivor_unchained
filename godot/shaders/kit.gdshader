// The kits' pieces as the web game shades them (src/render/env.ts's weather,
// src/render/flora.ts's kit look): the bright, clean kit paint pulled toward
// this country's grey and dark, foliage recoloured to its kind (autumn, the
// blight), moss on what faces up, each copy a little different, and wind in
// what grows. For MultiMesh copies, each copy's origin is its own.
//
// What stands between the camera and the survivor opens round her in a soft
// round window (see_through below). The piece itself is cut there, and its
// feathered rim is drawn again, translucent, by this material's next pass
// (KitLook: the same code with REVEAL defined, blended).
// Our own town walls and roofs (OWN_WALL, OWN_ROOF) have no window: the house in the way fades
// whole instead (the house fade, below; E9c).
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://shaders/flare_world.gdshaderinc"

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 albedo_color : source_color = vec4(1.0);
uniform bool use_vcolor = false;
uniform bool use_normal = false;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float roughness = 0.9;
uniform float alpha_scissor = 0.0;
uniform float wind = 0.0;
uniform float weather_sat = 0.82;
uniform vec3 weather_tint = vec3(0.88, 0.87, 0.85);
uniform vec4 recolor_a = vec4(0.0);  // rgb, amount
uniform vec3 recolor_b = vec3(0.0);
uniform float moss = 0.0;
uniform float jitter = 0.08;
// The village kit's walls darken toward their foot (splash, damp, dirt).
uniform bool foot = false;

// Where the survivor is (her chest, xyz; w = 1 in a fight: WorldScene sets it
// each frame), and where the game's camera is (xyz; w = 1 in play: Game sets
// it each frame). The window is made only in the camera's own view: in a
// light's (its shadows) the piece is whole, so a tree opened for her still
// casts all of its shadow.
global uniform vec4 survivor;
global uniform vec4 view_from;

#if defined(OWN_FOLIAGE) || defined(OWN_ROCK)
// The key light's kind for our own trees and stones (Atmosphere sets it): x how much it is the moon (0 by day,
// 1 at night), y how much a low warm sun (dawn, dusk); z, w the key's red and blue against its
// green (linear), so the needles' back light and their lit tips can be held to a hue.
global uniform vec4 flora_light;
// (a packed species, env_trees.py / env_rocks.py: its pieces in one mesh, each vertex's COLOR.a its piece, (index + 0.5) / 8; each
// copy draws only its own, its MultiMesh's custom data r, the rest collapsed to one point: one draw for all its pieces)
uniform bool packed = false;
#endif

#ifdef OWN_ROCK
// Our own stone (tools/assets/env_rocks.py; look bible 07: one stone for the rocks, the river's stones and, later, the
// footings): one painted sheet drawn triplanar in world space (its alpha the moss's breakup), the pieces' baked vertex
// colour (r edge wear, g cavity, b broad occlusion), moss on what faces up and toward moss_side, pale lichen spots,
// grime from the foot, and under the water's height a dark wet band (flora_species.json "stone": every value here).
uniform sampler2D stone_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D stone_nor : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
// (where the zone's water stands: x its height, w 1 if it has any; ZoneView sets it)
global uniform vec4 water_level;
uniform float tile = 1.9;
uniform vec3 stone_tint = vec3(1.0);
uniform float macro = 0.22;
uniform float bump = 0.55;
uniform float edge_light = 0.32;
uniform float cavity_dark = 0.45;
uniform float occl_dark = 0.4;
uniform float moss_amount = 0.5;
uniform vec4 moss_color : source_color = vec4(0.27, 0.31, 0.17, 1.0);
uniform vec2 moss_side = vec2(0.0, -1.0);
uniform float moss_side_amount = 0.25;
// (how far up a face must turn for moss, lo to hi, and how much worn rims shed it: a boulder's rounded crown is all rim)
uniform vec2 moss_face = vec2(0.45, 0.85);
uniform float moss_edge = 0.3;
uniform float lichen_amount = 0.25;
uniform vec4 lichen_color : source_color = vec4(0.56, 0.58, 0.47, 1.0);
uniform float grime_h = 0.45;
uniform float grime_dark = 0.3;
uniform float wet_above = 0.09;
uniform float wet_dark = 0.55;
uniform float wet_rough = 0.32;
uniform float stone_rough = 0.88;
// (the colour its shade keeps, a little of its own albedo given back: never grey-black; more under the moon)
uniform vec3 shade = vec3(0.92, 0.98, 1.1);
uniform float shade_floor = 0.025;
uniform float night_fill = 0.1;
// (E5b, judge r1: under the moon the stone darkened and warmed by this, so the moon's blue makes it blue-grey, not ice-cyan)
uniform vec3 night_tint = vec3(1.0);
// (a stepping stone's wet band: if wet_share > 0, up wet_share of its side above the water, its top the piece's wet_top m
// up, scaled with it; else wet_above m over the water, every stone alike)
uniform float wet_share = 0.0;
uniform float wet_top = 0.75;
// (C03 env fix: a stepping stone's top damp at night (any blue in the key: a cinematic's near-white moon too), the river's spray: its albedo down by up to top_damp, patchy (drier
// spots), its roughness toward wet_rough by half that share, so a moon or lamp catches it in a spot, not a pale even cap)
uniform float top_damp = 0.0;
// (C03 env r2: how far the damp top's roughness goes toward wet_rough, a share of the damp (0.5 as r1): a glossy damp crown
// mirrored the bright sky at a low camera's grazing angle as a pale, flat "ice floe" (c03 s8); the stepping stones 0)
uniform float damp_gloss = 0.5;
// (C03 env r4: the damp top's light for one shot (GameCinema "stones"), the top's albedo times it above the wet band, as far
// as it faces up (1 as built): c03 s8's near stone crown stood 2.4x the water beside it, the frame's palest broad thing after her)
uniform float top_level = 1.0;
// (E5c, judge r2) each copy's own value, +-inst_val (its hash), and a share cool_share of them tinted cool_tint (the stepping
// stones' variety); each stone of a cluster its own colour, its UV (env_rocks.py's pebbles: u its class, slate / ochre /
// umber, v its value), stone_mix of the class's tint and +-stone_val; a thin algae line at the water's edge (algae: how
// much, algae_w m high); and amb_occl the ambient light it takes (AO: in shade it darkens as the ground round it does)
uniform float inst_val = 0.07;
uniform float cool_share = 0.0;
uniform vec3 cool_tint = vec3(1.0);
uniform float stone_mix = 0.0;
uniform float stone_val = 0.0;
uniform vec3 stone_a = vec3(1.0);
uniform vec3 stone_b = vec3(1.0);
uniform vec3 stone_c = vec3(1.0);
uniform float algae = 0.0;
uniform vec4 algae_color : source_color = vec4(0.22, 0.2, 0.11, 1.0);
uniform float algae_w = 0.025;
uniform float amb_occl = 1.0;
// (lf5c) leaf litter caught on its ledges and level faces (what faces up, in its hollows and inner corners: the baked
// cavity and occlusion), in scattered spots, litter_color; 0 none
uniform float litter = 0.0;
uniform vec4 litter_color : source_color = vec4(0.36, 0.22, 0.11, 1.0);
// (a pebble under a crown darkens as the ground's litter does there: GroundPaint's exposure (R the open sky), sky_dark of it; Dressing sets it)
uniform sampler2D expo_tex : filter_linear, repeat_disable, hint_default_white;
uniform float zone_size = 260.0;
uniform float sky_dark = 0.0;
varying float v_top;
varying vec3 v_wpos;
varying vec3 v_wnrm;
varying float v_foot;
#endif

#ifdef OWN_FOLIAGE
// (a species' own: its leaves' flutter in the wind, the spruce's 1; the warmest hue its sunlit
// tips may take under a low sun, sRGB degrees)
uniform float flutter = 1.0;
// (C03 env r4, judge r3: a ridge of spruces read as one top copied: each copy's stem bent its own way, its top leaning by up
// to 'lean' deg (its hash), a curve up the whole stem (h^2, a wind-set tree) and its foot where it stood; lean_h the
// piece's height (local m) the lean is reached at; 0 straight)
uniform float lean = 0.0;
uniform float lean_h = 8.8;
// ...each copy's height stretched by its hash within stretch_lo-hi (the far LODs alike: the ridge's spires at one height,
// judge r3), and its crown above leader_from (local m) squashed or drawn out within leader_lo-hi (a stubby top, a long
// spire: no ridge of one top shape); 1 as built
uniform float stretch_lo = 1.0;
uniform float stretch_hi = 1.0;
uniform float leader_from = 6.0;
uniform float leader_lo = 1.0;
uniform float leader_hi = 1.0;
uniform float hue_floor = 100.0;
// (lf1b) each tree its own green: hue within +-jit_hue deg, value jit_lo-jit_hi; a share (old_share) browner and greyer by
// old_amt (an old or drought-touched spruce), so a stand is not one teal mass; core_night: how far an inner spray darkens
// under the moon (0.8 as before; the spruce's tiers need more); lamp_gain, lamp_green: a lamp's light on the needles (not
// the moon's or the sun's) scaled, its green cut, so needles by her light go a warm olive, not lime (light(), below)
uniform float jit_hue = 7.0;
uniform float jit_lo = 0.87;
uniform float jit_hi = 1.08;
uniform float old_share = 0.0;
uniform float old_amt = 0.0;
uniform float core_night = 0.8;
uniform float lamp_gain = 1.0;
uniform float lamp_green = 0.0;
// (lf1b) under the moon a spray's open outer half lifted by up to this (the lit top of each tier, its tips)
uniform float tip_lift = 0.0;
// (lf3b, judge lf2 #2: the lit tips by night the frame's brightest green, neon emerald) under the moon the same tips
// pulled toward their own grey by tip_night_sat and down by tip_night_dim (0: as before; by day and at dawn, nothing)
uniform float tip_night_sat = 0.0;
uniform float tip_night_dim = 0.0;
// (how much of the vertex occlusion darkens a species' crown core: the spruce's 1; the alder's less,
// its crown seen from above read as a hole by day, judge E4c)
uniform float core = 1.0;
uniform float night_fill = 0.1;
uniform float near_dim = 0.2;
// (under the moon a species' leaves turned this many degrees toward blue-green and held to this value: judge E4h, the
// alder and the hazel the greenest masses by night)
uniform float night_hue = 0.0;
uniform float night_value = 1.0;
// (and its light through the needles cut by this much by day: judge E4 r3, the nearest roaddawn spruce still the frame's mintiest)
uniform float near_back = 0.25;
// (E3 au1-5) The canopy fade, in place of the round window for our trees: a tree whose crown, seen from the play
// camera, covers her or the ground within canopy_fade.x m of her (on the screen, at her distance; the ground's
// depth foreshortened by the camera's pitch) fades WHOLE, its leaves and its bark above crown_keep, to a ghost
// (canopy_fade.z the share cut), eased over canopy_fade.y m, by the house fade's moving threshold (coverage.gdshaderinc),
// so the temporal smoothing makes it an even ghost, never a hole or a stipple. Decided per copy in vertex() from its
// origin, its scale and its species' crown (local m: crown_lo its base, crown_hi its top, 0 never faded, crown_r its
// radius; flora_species.json's "shader"), the same for every vertex of it (a flat varying). Only in the play camera's
// own view: in a light's the tree is whole, so its shadow stays. canopy_fade.w 0: off (--canopy off).
uniform float crown_lo = 0.0;
uniform float crown_hi = 0.0;
uniform float crown_r = 2.0;
uniform float crown_keep = 1.5;
global uniform vec4 canopy_fade;
// (lf5p) the kept stump's cut top (its trunk's inside seen from above), and our broadleaves' night grey (flora_night.x)
uniform float stump_top = 0.0;
uniform vec3 stump_wood : source_color = vec3(0.42, 0.33, 0.22);
global uniform vec4 flora_night;
varying flat float v_fade;
#ifdef OWN_BROADLEAF
// (the alder: its leaves take this much of the key's shadow, the proxy's and its neighbours', so a
// crown in its own shade by day still reads lit through, judge E4c; lamps' shadows whole)
uniform float self_shadow = 0.5;
uniform float wrap = 1.0;
// (and the sky's blue in its shade by day less than the needles', so its shade stays olive)
uniform float sky_amb = 0.45;
// (its sun-facing half lifted by this much by day, the shade side as it was: judge E4 r3, the town alder darker and cooler than the square)
uniform float sun_lift = 0.1;
#endif

float hue_of(vec3 c) {
	float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)), d = mx - mn;
	if (d < 1e-5) return 120.0;
	float h = mx == c.r ? mod((c.g - c.b) / d, 6.0) : mx == c.g ? (c.b - c.r) / d + 2.0 : (c.r - c.g) / d + 4.0;
	return h * 60.0;
}

vec3 hue_turn(vec3 c, float a) {
	vec3 k = vec3(0.57735);
	float ca = cos(a);
	return c * ca + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - ca);
}
#endif

// (foliage: its leaves' undersides are not a roof's; KitLook)
uniform bool leaves = false;

// (E9c) The house fade, in place of the round window for our walls and roofs: the part of a house (OwnWalls'
// fade unit: a house, or a 12 m length of a long one) that stands between her and the play camera is cut away
// by a threshold moved every frame (coverage.gdshaderinc), so the temporal smoothing sums the frames' cuts into
// an even fade, never a stipple and never a hole. HouseFade (OwnWalls.cs) eases each unit's fade over 0.3 s and
// names up to 8 of them here: ids (unit + 1, 0 none) and how far each is faded (0 whole, 1 gone). Only in the
// camera's own view: in a light's the house is whole, so its shadow stays on the street.
#include "res://shaders/coverage.gdshaderinc"
global uniform vec4 house_fade_ids;
global uniform vec4 house_fade_ids2;
global uniform vec4 house_fade;
global uniform vec4 house_fade2;
varying flat float v_unit;
// (E9c3) a kit piece inside one of our houses (OwnWalls.FadeUnits: its copy's custom data g 1, the cauldron 2): it comes
// in with its house's cutaway (below the cut, by its own scatter, so where the wall's ghost is kept it is not) and goes
// above it with the walls; where it is (world), and its own frame's place and normal (the cauldron's mouth)
varying flat float v_inmode;
varying vec3 v_kw;
varying vec3 v_kl;
varying vec3 v_kn;
// (E9c2) The cutaway: each unit's walls fade only above its cut (house_cut: a world height, 0.9 m over its floor),
// the footing below stands, capped (its walls' back faces, seen down into the cut, drawn as a stone wall top);
// its roofs fade whole. What hangs on its walls (a kit lantern: its MultiMesh's custom data r, the unit + 1) fades
// whole with it.
global uniform vec4 house_cut;
global uniform vec4 house_cut2;
float house_fade_of(float u) {
	vec4 a = step(abs(house_fade_ids - u), vec4(0.5)) * house_fade;
	vec4 b = step(abs(house_fade_ids2 - u), vec4(0.5)) * house_fade2;
	return u < 0.5 ? 0.0 : max(max(max(a.x, a.y), max(a.z, a.w)), max(max(b.x, b.y), max(b.z, b.w)));
}
// (the unit's cut height; -1e4 for none)
float house_cut_of(float u) {
	vec4 a = step(abs(house_fade_ids - u), vec4(0.5));
	vec4 b = step(abs(house_fade_ids2 - u), vec4(0.5));
	return dot(a, house_cut) + dot(b, house_cut2) + (1.0 - min(1.0, dot(a, vec4(1.0)) + dot(b, vec4(1.0)))) * -1e4;
}


#if defined(OWN_WALL) || defined(OWN_ROOF)
// Our own town walls (tools/assets/env_house.py, OwnWalls, KitLook.Wall): the trim sheet's aux (r its tint class:
// 1 plaster, .5 timber; g roughness; b a grime noise tiling with its region); each copy's custom data r its house's
// tint ((i + .5) / 8), g its height above its house's ground, b its own hash, a its treatment; the vertex colour
// r occlusion, g the stain under a sill, b 1 on timber that takes the house's timber tint.
uniform sampler2D aux_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 plaster_tints[6];  // (godot/data/house_look.json: arrays take no defaults)
uniform vec3 timber_tints[3];
uniform float grime_h = 1.4;      // the grime's height above the house's ground (m)
uniform float grime_dark = 0.4;   // how much darker at the ground
uniform float splash_h = 0.45;    // the splash band (rain off the street)
uniform float splash_dark = 0.2;
uniform float house_rise = 0.12;  // the house's ground storey this much darker than its 6 m line
uniform float stain_dark = 0.45;  // the streaks under a sill
uniform float val_noise = 0.1;    // broad value patches over the walls (world space)
uniform float house_val = 0.06;   // each house a little lighter or darker
uniform float occl = 0.5;         // the vertex occlusion's reach
uniform sampler2D ground_h : filter_linear, repeat_disable;  // (E9b3) the terrain's height under the town (OwnWalls.Build)
uniform vec4 ground_rect = vec4(0.0);  // its world x, z origin and size; z 0: no map (the house's own ground instead)
uniform float plaster_mottle = 0.1;  // value mottling on plaster at 1-2 m
uniform float lost_plaster = 1.0;    // patches where the plaster has fallen off (the lath behind)
uniform float big_lost = 0.4;        // (E9b6) the share of 2.5 m cells with a 40-80 cm patch fallen off
// (E9d) the town's lit windows: how lit the town is (Atmosphere.TownLit: 0 by day, 1 at dawn and by night), the share of
// wall pieces whose glass glows, its colour and strength (linear, over the dark glass)
global uniform float town_lit;
uniform float window_share = 0.38;
// (E9d, judge E9b r3) weathering: dressed stone's ground grime and worn arrises, sunlit plaster's stains, a clay roof's eave
// run-off, its broad blotches toward grey-brown and its lichen, a chimney's stone cap
uniform float ashlar_grime_h = 1.1;     // the dressed stone's grime to this height (m)
uniform float ashlar_grime = 0.2;       // this much darker at the ground
uniform float ashlar_edge = 0.1;        // its arrises this much darker (worn, dirt in them)
uniform float plaster_stain = 0.15;     // plaster stained to (1 - this) in streaked patches
uniform float eave_run = 0.25;          // the eave's run-off: (1 - this) over its lowest 0.6-0.9 m
uniform float roof_blotch = 0.1;        // 2-4 m blotches this much toward grey-brown, lighter or darker
uniform float roof_blotch_clay = 0.24;  // (r2) the same on clay, and a finer darker layer
uniform float lichen = 0.6;             // lichen flecks in patches (clay), mostly on the lower third
uniform vec3 window_hot = vec3(1.0, 0.6, 0.24);    // (r2) the pane's hot spot
uniform vec3 window_edge = vec3(0.85, 0.3, 0.06);  // its edges, a deeper amber
uniform float window_k = 1.9;
uniform float window_edge_k = 0.55;
uniform float window_bake = 1.2;   // the bakery's windows this much brighter again
global uniform vec4 town_bakery;   // the bakery's front (world) and the radius its windows are in (0: none)
uniform float grime_debug = 0.0;     // (E9b4) 1: flat colours by height above the ground (red < 0.4 m, green < 1.2, blue < 3), to check the ground map reaches the wall
varying vec4 v_wall;
varying flat float v_stone;
varying float v_hgt;
varying vec3 v_wp;
float wall_hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float wall_noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(wall_hash(i), wall_hash(i + vec2(1.0, 0.0)), f.x), mix(wall_hash(i + vec2(0.0, 1.0)), wall_hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
// (E9c3) the cut's line broken (m, added to the cut's height) at a place on the ground
float cut_broken(vec2 xz) { return 0.06 * (wall_noise(xz * 3.1) - 0.5) + 0.025 * (wall_noise(xz * 11.0 + 5.0) - 0.5); }
#endif
#ifdef OWN_ROOF
// Our own roofs (tools/assets/env_roof.py, KitLook.Roof; E9b2), on the walls' uniforms above and the roof sheet: its aux
// r the class (1 clay, .75 shingle, .5 timber taking the house's timber tint, 0 untinted), g roughness, b each tile's id;
// the vertex colour r occlusion, g the face's hash, b 1 on the covering (on a chimney: its soot), a the sag weight;
// each copy's custom data as the walls' with a = (treatment * 8 + roof tint + .5) / 32.
uniform vec3 clay_tints[4];      // (godot/data/house_look.json)
uniform vec3 shingle_tints[4];
uniform vec4 chimneys[32];       // each stack's top (xyz), w 1; OwnWalls.Build
uniform float roof_sag = 0.04;
#if !defined(OWN_FOLIAGE) && !defined(OWN_ROCK)
global uniform vec4 key_dir;
global uniform vec4 flora_light;  // (x: how much the key is the moon; declared above for the trees and stones)
#endif
uniform float roof_night = 0.8;
uniform float roof_debug = 0.0;  // (E9d r3) the night sky's fill on the roofs (x flora_light.x)
uniform float roof_lean = 0.14;          // (E9b6 r4) each roof racked sideways at its middle this much (m)
uniform vec2 roof_lean_dir = vec2(0.0, 1.0);  // world x, z: toward the play camera   // each house's roof sags this much more at most (m), by its copy's hash
uniform float tile_val = 0.12;   // each tile lighter or darker
uniform float tile_warm = 0.5;   // and warmer or cooler
uniform float roof_val_noise = 0.08;
uniform float roof_house_val = 0.06;
uniform float soot_r = 2.0;      // the soot round a chimney's top (m)
uniform float soot_dark = 0.6;
uniform float stack_soot = 0.75; // a stack's own top
uniform float roof_moss = 0.6;   // on slopes facing moss_dir (north), thickest toward the eaves
uniform vec2 moss_dir = vec2(0.0, -1.0);
uniform vec4 roof_moss_color : source_color = vec4(0.25, 0.29, 0.18, 1.0);
uniform float roof_occl = 0.55;
uniform float old_tile = 0.16;     // (E9b6 r4) the share of tiles old and dark: darker and browner (about one in 6)
uniform float tile_tilt = 0.09;    // each tile's normal turned +-this (a tile bedded a few degrees off its neighbours)
uniform float trough_dirt = 0.45;   // dirt streaks running down the slope (narrow, broken), this much darker
uniform float moss_any = 0.5;     // moss in patches on every slope's lower courses (not only the north ones)
varying vec3 v_wn;
varying float v_rh;
varying float v_lz;
#endif

varying float v_up;
varying float v_jit;
varying float v_y;

const vec3 LW = vec3(0.2126, 0.7152, 0.0722);

// How much of the piece is kept at this point of it (1 all, 0 none): a round
// window round her, wide enough for all of her, clear in its middle and
// feathered over its outer metre, measured on the screen in metres at her
// distance (so it is round, and the same at every zoom). Only what stands
// nearer the camera than she does, and above her ankles (never the floor at
// her feet), is opened, each eased in, so no line is drawn across a piece she
// stands in: a point only partly in the way has a smaller window, never a
// fainter one, so the window is always clear and only its rim is see-through
// (a piece drawn faint across the window, on the rim's translucent pass, lost
// its shading and stood pale in it: a roof's underside, a gable).
// (Its two parts: how far from her on the screen, in metres at her distance, and how far the
// point is opened, 0 none; see_through below puts them together.)
vec2 see_parts(vec3 vpos, mat4 view, mat4 inv_view, mat4 proj, vec3 cam) {
	// (A light's view stands far from the camera's: a lamp's at most a few metres up, the sun's far off.)
	if (survivor.w <= 0.0 || view_from.w <= 0.0 || distance(cam, view_from.xyz) > 1.0) return vec2(0.0);
	vec3 her = (view * vec4(survivor.xyz, 1.0)).xyz;
	float front = smoothstep(0.3, 1.3, vpos.z - her.z);
	float above = smoothstep(0.25, 0.7, (inv_view * vec4(vpos, 1.0)).y - (survivor.y - 1.1));
	float open = front * above;
	if (open <= 0.0) return vec2(0.0);
	vec4 a = proj * vec4(vpos, 1.0);
	vec4 b = proj * vec4(her, 1.0);
	vec2 d = a.xy / a.w - b.xy / b.w;
	// (The projection's own scales, not their signs: Vulkan's is flipped in y, and a
	// negative distance opened all that stands before her, at any distance.)
	float fy = abs(proj[1][1]);
	d.x *= fy / abs(proj[0][0]);
	float metres = length(d) * -her.z / fy;
	return vec2(metres, open);
}

float see_through(vec2 mo) {
	return mo.y <= 0.0 ? 1.0 : smoothstep(1.45 * mo.y, 2.5 * mo.y, mo.x);
}

void vertex() {
	vec3 ip = MODEL_MATRIX[3].xyz;
	// (E9c2: a copy's fade unit + 1 in its custom data's r, 0 none; ours below take theirs from its whole part too)
	v_unit = floor(INSTANCE_CUSTOM.r);
	v_inmode = INSTANCE_CUSTOM.g;
	v_kw = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_kl = VERTEX;
	v_kn = NORMAL;
	v_up = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz).y;
	v_jit = fract(sin(dot(ip.xz, vec2(12.9898, 78.233))) * 43758.5453);
	v_y = VERTEX.y;
	float h = max(VERTEX.y, 0.0);
	float ph = TIME * 1.1 + ip.x * 0.23 + ip.z * 0.19;
	float sway = (sin(ph) * 0.65 + sin(ph * 2.3 + 1.7) * 0.25 + sin(ph * 5.1 + ip.x) * 0.1) * wind * h * h * 0.02;
#ifdef OWN_FOLIAGE
	// (our own trees, env_trees.py: each branch's needles flutter on their own, more toward
	// the branch's end; the bark strip, u > .75, stands with the trunk)
	// (a broadleaf's leaves, flutter > 1, flutter faster and every way, not only up and down)
	if (UV.x < 0.75) {
		float fr = length(VERTEX.xz) * wind;
		VERTEX.y += sin(TIME * (2.7 + 1.6 * (flutter - 1.0)) + dot(VERTEX, vec3(1.3, 0.7, 1.1)) + ip.x * 0.5) * 0.035 * flutter * fr;
		VERTEX.xz += vec2(sin(TIME * 4.3 + dot(VERTEX, vec3(2.1, 1.3, 0.9))), cos(TIME * 3.7 + dot(VERTEX, vec3(0.8, 1.9, 1.7)))) * 0.02 * max(flutter - 1.0, 0.0) * fr;
	}
	if (stretch_hi != stretch_lo || leader_hi != leader_lo) {
		float hl = mix(leader_lo, leader_hi, fract(sin(dot(ip.xz, vec2(51.3, 27.9))) * 37281.41));
		if (VERTEX.y > leader_from) VERTEX.y = leader_from + (VERTEX.y - leader_from) * hl;
		VERTEX.y *= mix(stretch_lo, stretch_hi, fract(sin(dot(ip.xz, vec2(17.17, 63.41))) * 19417.83));
		h = max(VERTEX.y, 0.0);
	}
	if (lean > 0.0) {
		float la = radians(lean) * (fract(sin(dot(ip.xz, vec2(39.35, 11.13))) * 24634.63) * 2.0 - 1.0);
		float ld = fract(sin(dot(ip.xz, vec2(7.77, 93.51))) * 51721.17) * TAU;
		VERTEX.xz += vec2(cos(ld), sin(ld)) * tan(la) / (2.0 * lean_h) * h * h;
	}
	v_fade = 0.0;
	if (crown_hi > 0.0 && canopy_fade.w > 0.0 && survivor.w > 0.0 && view_from.w > 0.0 && distance(INV_VIEW_MATRIX[3].xyz, view_from.xyz) <= 1.0) {
		// the crown's base and top as this copy is drawn (its stretch and its leader, as above)
		float st = mix(stretch_lo, stretch_hi, fract(sin(dot(ip.xz, vec2(17.17, 63.41))) * 19417.83));
		float hl = mix(leader_lo, leader_hi, fract(sin(dot(ip.xz, vec2(51.3, 27.9))) * 37281.41));
		float top = (crown_hi > leader_from ? leader_from + (crown_hi - leader_from) * hl : crown_hi) * st;
		vec3 upv = MODEL_MATRIX[1].xyz;
		vec3 vb = (VIEW_MATRIX * vec4(ip + upv * (crown_lo * st), 1.0)).xyz;
		vec3 vt = (VIEW_MATRIX * vec4(ip + upv * top, 1.0)).xyz;
		vec3 hv = (VIEW_MATRIX * vec4(survivor.xyz, 1.0)).xyz;
		// (a crown wholly behind the camera's plane is not seen: none; one partly behind, cut at 1 m before the lens,
		// or its projection, flipped and huge, swept across her)
		float zb = vb.z, zt = vt.z, vb_z0 = vb.z, vt_z0 = vt.z;
		if (max(zb, zt) > -1.0) {
			if (min(zb, zt) > -1.0) zb = 1e9;
			else if (zb > -1.0) vb = mix(vt, vb, (-1.0 - zt) / (zb - zt));
			else vt = mix(vb, vt, (-1.0 - zb) / (zt - zb));
		}
		// on the screen, in metres at her distance (a perspective's x / z, y / z): the crown a segment, its radius about it
		float hz = min(hv.z, -0.5);
		vec2 a = vb.xy * (hz / min(vb.z, -0.5)), b = vt.xy * (hz / min(vt.z, -0.5));
		float rr = crown_r * length(upv) * hz / min(0.5 * (vb.z + vt.z), -0.5);
		if (zb > 1e8) a = b = vec2(1e6);
		// the ground round her seen foreshortened: screen heights stretched back to ground depth by the camera's pitch
		float ky = 1.0 / max(abs(INV_VIEW_MATRIX[2].y), 0.3);
		vec2 p = hv.xy;
		a.y *= ky; b.y *= ky; p.y *= ky;
		vec2 ab = b - a;
		float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 1e-4), 0.0, 1.0);
		float d = length(p - (a + ab * t)) - rr;
		v_fade = 1.0 - smoothstep(canopy_fade.x, canopy_fade.x + canopy_fade.y, d);
		// (a crown that reaches within 1 m of the lens's plane is cut whole: its axis behind the plane read as
		// "not seen", yet its needles hung in front and flashed across her for a few frames as the camera passed, judge e2)
		// (eased over the 1.5 m before it, so a crown that crosses it in view fades rather than pops: judge e3)
		v_fade = max(v_fade, smoothstep(-(crown_r * length(upv) + 2.5), -(crown_r * length(upv) + 1.0), max(vb_z0, vt_z0)));
	}
#endif
	VERTEX.x += sway;
	VERTEX.z += sway * 0.5;
#if defined(OWN_FOLIAGE) || defined(OWN_ROCK)
	if (packed && abs(COLOR.a - INSTANCE_CUSTOM.r) > 0.06) VERTEX = vec3(0.0);
#endif
#ifdef OWN_ROCK
	v_wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wnrm = normalize(MODEL_NORMAL_MATRIX * NORMAL);
	v_foot = v_wpos.y - MODEL_MATRIX[3].y;
	v_top = MODEL_MATRIX[3].y + wet_top * length(MODEL_MATRIX[1].xyz);
#endif
#ifdef OWN_WALL
	// (custom data r: its fade unit + 1 in the whole part, its tint in the fraction)
	v_wall = vec4(fract(INSTANCE_CUSTOM.r), INSTANCE_CUSTOM.g, fract(INSTANCE_CUSTOM.b), INSTANCE_CUSTOM.a);
	v_unit = floor(INSTANCE_CUSTOM.r);
	// (E9c3: custom data b's whole part 1 for a stone piece, its cut capped as rubble; else timber, capped by its sill beam)
	v_stone = floor(INSTANCE_CUSTOM.b);
	v_hgt = VERTEX.y + INSTANCE_CUSTOM.g;
	v_wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
#endif
#ifdef OWN_ROOF
	v_wall = vec4(fract(INSTANCE_CUSTOM.r), INSTANCE_CUSTOM.gba);
	v_unit = floor(INSTANCE_CUSTOM.r);
	VERTEX.y -= COLOR.a * roof_sag * fract(INSTANCE_CUSTOM.b * 7.13 + 0.31);
	{
		// (E9b6 r4) each roof racked sideways at its middle (the sag's weight): toward roof_lean_dir (the play camera)
		// where its slopes face that way, so the far eave's bow adds to its sag on screen; else by its hash
		vec3 lx = MODEL_MATRIX[0].xyz;
		float sx = max(length(lx), 1e-4);
		float t = dot(lx.xz / sx, roof_lean_dir);
		float sg = abs(t) > 0.3 ? sign(t) : (fract(INSTANCE_CUSTOM.b * 3.71) > 0.5 ? 1.0 : -1.0);
		VERTEX.x += COLOR.a * roof_lean * (0.8 + 0.4 * fract(INSTANCE_CUSTOM.b * 5.3)) * sg / sx;
	}
	v_hgt = VERTEX.y + INSTANCE_CUSTOM.g;
	v_rh = VERTEX.y;
	v_lz = VERTEX.z;
	v_wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
#endif
#ifdef REVEAL
	// The rim is drawn again only for a piece near the line from her to the
	// camera (within 14 m of it on the ground); every other copy is put out of
	// view whole, so the second pass costs next to nothing.
	vec2 s = survivor.xz, c = view_from.xz, o = ip.xz;
	vec2 sc = c - s;
	float t = clamp(dot(o - s, sc) / max(dot(sc, sc), 1e-4), 0.0, 1.0);
	bool near_line = survivor.w > 0.0 && view_from.w > 0.0 && distance(o, s + sc * t) < 14.0;
	POSITION = near_line ? PROJECTION_MATRIX * (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)) : vec4(2.0, 2.0, 2.0, 1.0);
#endif
}

void fragment() {
#if defined(OWN_WALL) || defined(OWN_ROOF)
	// (no round window: the house fade above)
	vec2 mo = vec2(0.0);
	float kept = 1.0;
	bool cap = false, lip = false;
	vec3 cap_at = vec3(0.0);
	if (view_from.w > 0.0 && distance(CAMERA_POSITION_WORLD, view_from.xyz) <= 1.0) {
		float f = house_fade_of(v_unit);
#ifdef OWN_WALL
		// (E9c2) the cutaway: faded above the cut only; the back faces (the walls are drawn both sides, OWN_WALL only)
		// only as the cut's cap, under the cut of a unit fading, else not at all in the camera's view (in a light's
		// they cast with the front, the same closed wall)
		// (E9c3) the cut's line knocked down, not sawn: +-3 cm over 10-40 cm, by the place across the ground (so both faces
		// of a wall and its cap meet on it); a 2-4 cm lip under it darker on the faces (the broken edge)
		float cy = house_cut_of(v_unit);
		float cb = cy + cut_broken(v_wp.xz);
		bool above = v_wp.y > cb;
		if (!FRONT_FACING) {
			if (f <= 0.0) discard;
			// the cap: where the eye's ray through this back face crosses the cut (the wall's top, seen from above), its
			// height broken as the faces' line; drawn there (its light taken there too), flat, nothing stretched down a face
			vec3 C = CAMERA_POSITION_WORLD, D = v_wp - C;
			if (D.y > -1e-4) discard;
			float t = (cy - C.y) / D.y;
			vec3 H = C + D * t;
			t = (cy + cut_broken(H.xz) - C.y) / D.y;
			H = C + D * t;
			if (t > 1.0) discard;
			cap_at = H;
			cap = true;
		}
		else if (f > 0.0 && above && coverage_cut(FRAGCOORD.xy) < f) discard;
		else if (f > 0.0 && v_wp.y > cb - (0.02 + 0.02 * wall_noise(v_wp.xz * 17.0 + 3.0))) lip = true;
#else
		// (the roof clears first, twice as fast: half way, it is gone and the walls half faded, never her under a
		// half-faded roof's striped tiles)
		f = min(1.0, f * 2.0);
		if (f > 0.0 && coverage_cut(FRAGCOORD.xy) < f) discard;
#endif
	}
#elif defined(OWN_FOLIAGE)
	// (no round window: the canopy fade, above; the trunk below crown_keep stands, its cut eased over 0.6 m)
	vec2 mo = vec2(0.0);
	float kept = 1.0;
	if (v_fade > 0.0) {
		// (lf6d: with stump_top, the bark cut level and hard, a saw's cut, not eased: the eased cut's band read as a dome)
		float ff = v_fade * canopy_fade.z * (UV.x < 0.75 ? 1.0 : (stump_top > 0.0 ? step(crown_keep, v_y) : smoothstep(crown_keep, crown_keep + 0.6, v_y)));
		if (coverage_cut(FRAGCOORD.xy) < ff) discard;
	}
#else
	vec2 mo = see_parts(VERTEX, VIEW_MATRIX, INV_VIEW_MATRIX, PROJECTION_MATRIX, CAMERA_POSITION_WORLD);
	float kept = see_through(mo);
	// (E9c2) a kit piece hung on one of our houses (a wall lantern, a torch) fades whole with its house
	if (v_unit > 0.5 && view_from.w > 0.0 && distance(CAMERA_POSITION_WORLD, view_from.xyz) <= 1.0) {
		float hf = house_fade_of(v_unit);
		if (v_inmode > 0.5 && v_kw.y <= house_cut_of(v_unit)) { if (coverage_cut(FRAGCOORD.xy + vec2(41.0, 23.0)) >= hf) discard; }
		else if (hf > 0.0 && coverage_cut(FRAGCOORD.xy) < hf) discard;
	}
#endif
#ifdef SEE_SCREEN
	// (The feather held to its width on the screen where how far the piece is opened
	// varies across it: the distance to the window's edge rescaled to change as fast
	// on the screen as the distance from her does.)
	float edge = mo.x - 2.5 * mo.y;
	float rate = min(fwidth(mo.x) / max(fwidth(edge), 1e-5), 8.0);
	if (mo.y > 0.0) kept = smoothstep(-1.05 * mo.y, 0.0, edge * rate);
#endif
#ifdef SEE_NARROW
	// (a narrow feather, 0.35 m at her distance, the clear radius kept)
	if (mo.y > 0.0) kept = smoothstep(1.45 * mo.y, 1.45 * mo.y + 0.35, mo.x);
#endif
#ifdef REVEAL
	// Only the feathered rim (the piece's whole part is drawn by the first pass).
	if (kept >= 0.999 || kept <= 0.004) discard;
#ifdef SEE_NORIM
	discard;
#endif
#ifdef SEE_BACK
	// (a face seen from behind, inside the window, cut whole: no rim)
	if (!FRONT_FACING) discard;
#endif
#ifdef SEE_UNDERCUT
	// (an underside, a ceiling or a roof's inside, seen only through the window: no rim)
	if (!leaves && v_up < -0.2) discard;
#endif
#ifdef SEE_UNDER
	// (an underside, a ceiling or a roof's inside, seen only through the window, under its
	// roof: the rim's translucent pass has no ambient occlusion, so it is given back here,
	// or the underside stands pale and flat in the rim)
	if (!leaves) AO = mix(1.0, 0.3, smoothstep(0.0, 0.6, -v_up));
#endif
#else
	if (kept < 0.999) discard;
#ifdef SEE_UNDERCUT
	// (its window wider, cut whole, so its edge lies under what still covers it)
	if (!leaves && v_up < -0.2 && mo.y > 0.0 && mo.x < 3.4 * sqrt(mo.y)) discard;
#endif
#endif
	vec4 c = texture(albedo_tex, UV) * albedo_color;
	if (use_vcolor) c *= COLOR;
#ifdef REVEAL
	if (alpha_scissor > 0.0 && c.a < alpha_scissor) discard;
	ALPHA = kept;
#else
	if (alpha_scissor > 0.0) {
		ALPHA = c.a;
		ALPHA_SCISSOR_THRESHOLD = alpha_scissor;
	}
#endif
	float l = dot(c.rgb, LW);
	vec3 col = mix(vec3(l), c.rgb, weather_sat) * weather_tint;
	vec3 rc = mix(recolor_a.rgb, recolor_b, v_jit);
	float lt = dot(col, LW);
	col = mix(col, rc * (lt / max(dot(rc, LW), 0.05)), recolor_a.a);
	col = mix(col, vec3(0.2, 0.3, 0.12) * (0.55 + lt), moss * smoothstep(0.45, 0.85, v_up));
	col *= 1.0 - jitter + 2.0 * jitter * v_jit;
	if (foot) col *= mix(0.6, 1.0, smoothstep(0.0, 1.3, v_y));
	ALBEDO = col;
	ROUGHNESS = roughness;
	if (use_normal) NORMAL_MAP = texture(normal_tex, UV).rgb;
#if !defined(OWN_WALL) && !defined(OWN_ROOF)
	if (v_inmode > 1.5 && v_inmode < 2.5) {
		// (E9c3) the cauldron (props/Cauldron: its bowl's inside under a rim at 0.71-0.81 m, 0.43-0.47 m out): its mouth
		// dark from above, sooted, deepest at the bottom; its rim's top worn bright iron (the hearth's light catches it)
		float kr = length(v_kl.xz);
		bool inner = kr < 0.432 && v_kl.y > 0.2 && v_kl.y < 0.79 && (dot(v_kn.xz, v_kl.xz) < 0.0 || v_kn.y > 0.5);
		if (inner) {
			// (E9c4: a near-black sooted bowl, no sky in it, so the mouth reads as a hole from above)
			ALBEDO = vec3(0.012, 0.010, 0.009) * (1.0 + 1.2 * smoothstep(0.55, 0.79, v_kl.y));
			ROUGHNESS = 0.95;
			SPECULAR = 0.05;
			NORMAL_MAP = vec3(0.5, 0.5, 1.0);
		} else if (v_kl.y > 0.765 && kr > 0.42 && v_kn.y > 0.3) {
			// (its rim's top worn iron, dark: the hearth's light picks it out, the sky does not whiten it)
			ALBEDO = vec3(0.09, 0.085, 0.08);
			ROUGHNESS = 0.5;
			METALLIC = 0.5;
		} else {
			// (E9c4) the body blackened cast iron (the kit's trim metal reads pale and flat): dark, warm, sooted low
			ALBEDO = vec3(0.045, 0.04, 0.036) * (0.7 + 0.3 * smoothstep(0.0, 0.6, v_kl.y)) * (0.85 + 0.3 * dot(ALBEDO, LW));
			ROUGHNESS = 0.7;
			METALLIC = 0.3;
		}
	}
#endif
#ifdef OWN_WALL
	{
		vec3 ax = texture(aux_tex, UV).rgb;
		int ti = clamp(int(v_wall.r * 8.0), 0, 5);
		vec3 tint = vec3(1.0);
		if (ax.r > 0.75) tint = plaster_tints[ti];
		else if (ax.r > 0.25 && COLOR.b > 0.5) tint = timber_tints[ti % 3];
		vec3 col = c.rgb * tint;
		// broad value patches over the town's walls (a run never reads as one flat paint), each house a little lighter or darker
		vec2 wq = vec2(v_wp.x + v_wp.z, v_wp.y);
		float vn = 0.6 * wall_noise(wq * 0.55) + 0.4 * wall_noise(wq * 0.13 + 7.3);
		col *= 1.0 + val_noise * (2.0 * vn - 1.0) + house_val * (2.0 * wall_hash(v_wall.ra * 17.0) - 1.0);
		// grime from the house's ground up, its line broken by the sheet's noise; the ground storey darker as a whole;
		// the splash band at the foot (rain off the street), browner
		float gn = ax.b;
		float h = v_hgt;
		// (E9b3) the height above the terrain itself where the town has its map, so the grime shows where grass or a slope hides the foot
		if (ground_rect.z > 0.0) {
			vec2 gq = (v_wp.xz - ground_rect.xy) / ground_rect.zw;
			if (gq.x > 0.0 && gq.y > 0.0 && gq.x < 1.0 && gq.y < 1.0) h = v_wp.y - texture(ground_h, gq).r;
		}
		if (ax.r > 0.75) {
			// plaster: mottled at 1-2 m, and here and there fallen off to the lath (30-60 cm patches, a dark broken rim)
			col *= 1.0 + plaster_mottle * (2.0 * wall_noise(wq * 0.75 + 3.1) - 1.0);
			float pn = 0.7 * wall_noise(wq * 1.9 + v_wall.b * 37.0) + 0.3 * wall_noise(wq * 7.0 + 1.3);
			float pm = smoothstep(0.55, 0.7, wall_noise(wq * 0.33 + 11.7 + v_wall.b * 5.0)) * smoothstep(0.7, 1.4, h) * lost_plaster;
			float lost = smoothstep(0.74, 0.76, pn) * pm;
			float rim = (smoothstep(0.7, 0.74, pn) - smoothstep(0.75, 0.78, pn)) * pm;
			float lath = smoothstep(0.25, 0.4, fract(v_wp.y * 26.0)) * (0.75 + 0.25 * wall_noise(vec2((v_wp.x + v_wp.z) * 6.0, v_wp.y * 26.0)));
			vec3 lc = mix(vec3(0.07, 0.055, 0.045), vec3(0.3, 0.24, 0.18) * (0.8 + 0.4 * wall_noise(wq * 9.0)), lath);
			// (E9b6) and a bigger patch now and then, 40-80 cm, ragged: one 2.5 m cell in about 2.5 has one (its centre
			// kept 0.5 m inside the cell, so no patch crosses a cell's edge), so a 6 m face shows one or two
			vec2 ci = floor(wq / 2.5);
			float ph = wall_hash(ci * 1.7 + 0.31);
			if (ph < big_lost) {
				vec2 pc = (ci + 0.2 + 0.6 * vec2(wall_hash(ci + 5.1), wall_hash(ci + 9.7))) * 2.5;
				float rx = 0.2 + 0.2 * wall_hash(ci + 2.9);
				vec2 pr = vec2(rx, rx * (0.6 + 0.4 * wall_hash(ci + 7.3)));
				float pd = length((wq - pc) / pr) + 0.45 * (wall_noise(wq * 6.0 + ci) - 0.5) + 0.2 * (wall_noise(wq * 17.0) - 0.5);
				float bl = (1.0 - smoothstep(0.97, 1.0, pd)) * smoothstep(0.5, 0.9, h);
				float br = (1.0 - smoothstep(1.0, 1.14, pd)) * smoothstep(0.5, 0.9, h) - bl;
				lost = max(lost, bl);
				rim = max(rim, max(br, 0.0));
			}
			col = mix(col * (1.0 - 0.35 * rim), lc, lost);
			if (grime_debug > 1.5) col = vec3(lost, rim, 0.3) * 3.0;  // (E9b6) 2: the lost plaster (r) and its rim (g)
		}
		// grime from the ground: a brown-green band, darkest to 0.6 m (E9b4: the street often meets the wall 0.4 m up), streaked with splash, gone by 1.2 m
		float sn = wall_noise(vec2((v_wp.x + v_wp.z) * 11.0, v_wp.y * 1.3));
		float hn = h + 0.25 * (gn - 0.5);
		float gr = 1.0 - smoothstep(0.6, grime_h, hn + 0.2 * (sn - 0.5));
		col *= (1.0 - grime_dark * gr) * mix(vec3(1.0), vec3(0.97, 0.98, 0.86), gr);
		col *= mix(1.0 - house_rise, 1.0, smoothstep(0.0, 6.0, h));
		float splash = 1.0 - smoothstep(0.0, splash_h, hn - 0.25 * sn);
		col *= mix(vec3(1.0), vec3(1.0 - splash_dark) * vec3(0.95, 0.97, 0.82), splash);
		// (E9d) dressed stone (the sheet's ashlar: quoins, sills, coping): grime from the ground to about 1.1 m, its arrises worn
		if (UV.x < 0.75 && UV.y > 0.8125 && UV.y < 0.90625) {
			col *= mix(1.0 - ashlar_grime, 1.0, smoothstep(0.2, ashlar_grime_h, hn + 0.15 * (sn - 0.5)));
			vec3 fw = fwidth(NORMAL);
			float edge = clamp((fw.x + fw.y + fw.z) * 6.0, 0.0, 1.0);
			col *= 1.0 - ashlar_edge * edge * (0.6 + 0.4 * wall_noise(wq * 9.0));
		}
		// (E9d) plaster stained: rain streaks from the eaves and sills in broad patches, to 0.85x
		if (ax.r > 0.75) {
			float st = wall_noise(vec2((v_wp.x + v_wp.z) * 1.6, v_wp.y * 0.22 + 3.0)) * wall_noise(wq * 0.4 + 2.2);
			col *= 1.0 - plaster_stain * smoothstep(0.18, 0.5, st) * vec3(1.0, 1.0, 1.06);
		}
		// stains under the sills: streaks running down (the sheet's noise stretched down the wall)
		float streak = smoothstep(0.25, 0.75, texture(aux_tex, vec2(UV.x * 1.7, UV.y * 0.1)).b);
		col *= 1.0 - stain_dark * COLOR.g * (0.3 + 0.7 * streak);
		col *= mix(1.0 - occl, 1.0, COLOR.r);
		if (grime_debug > 0.0 && grime_debug < 1.5) col = h < 0.4 ? vec3(1.0, 0.0, 0.0) : h < 1.2 ? vec3(0.0, 1.0, 0.0) : h < 3.0 ? vec3(0.0, 0.0, 1.0) : vec3(1.0);
		ALBEDO = col;
		ROUGHNESS = ax.g;
		// (E9d) a lit window: the glass (its sheet region) on about one wall piece in three glows warm from inside, at
		// dawn and by night only; brighter low (the hearth, a table's candle), uneven across the old crown glass
		vec2 gl = (UV - vec2(0.875, 0.8125)) / vec2(0.125, 0.09375);
		// (r2: the bakery on the square's edge, ZoneView.Town's town_bakery: its windows always lit, hotter, brighter)
		float bake = town_bakery.w > 0.0 ? 1.0 - smoothstep(town_bakery.w * 0.8, town_bakery.w, length(v_wp - town_bakery.xyz)) : 0.0;
		if (town_lit > 0.001 && gl.x > 0.0 && gl.x < 1.0 && gl.y > 0.0 && gl.y < 1.0
				&& (bake > 0.5 || wall_hash(vec2(v_wall.b * 91.7 + 0.37, floor(v_wall.r * 8.0) * 3.1)) < window_share)) {
			float wn = 0.6 + 0.4 * wall_noise(v_wp.xz * 2.7 + v_wp.y * 3.3);
			float low = 1.0 - 0.45 * smoothstep(0.0, 1.4, fract(h / 2.9) * 2.9 - 0.9);
			// (r2: the panes read flat cream: a deep amber with a hot spot low in the middle (the fire or the candle
			// seen through the old glass), the edges falling to a darker orange so the colour holds after the tonemap)
			float hot = exp(-dot((gl - vec2(0.5, 0.62)) * vec2(1.6, 1.9), (gl - vec2(0.5, 0.62)) * vec2(1.6, 1.9)) * 2.2);
			hot *= 0.8 + 0.4 * wall_hash(vec2(v_wall.b * 13.1, floor(v_wall.r * 8.0)));
			vec3 wc = mix(window_edge, window_hot, hot) * mix(window_edge_k, window_k, hot);
			EMISSION += wc * town_lit * wn * low * (1.0 + bake * window_bake) * (0.75 + 0.5 * dot(c.rgb, LW) / 0.12);
			ALBEDO *= 0.5;
			ROUGHNESS = 0.2;
		}
		if (lip) ALBEDO *= 0.55;
		if (cap) {
			// (E9c3) the cut's cap at the wall's top (cap_at): across the wall, how far in from its far face (the face this
			// is the back of) and its run along; a stone wall's rubble core (the sheet's rubble at half size: 10-20 cm
			// stones in dark mortar) with chips of broken stone lying on it; a timber wall's sill beam (the sheet's adzed oak,
			// its grain along the wall); both darker at their broken edges (2-4 cm)
			vec3 H = cap_at;
			vec3 gn = normalize(cross(dFdx(v_wp), dFdy(v_wp)));
			gn = normalize(vec3(gn.x, 0.0, gn.z) + vec3(1e-5, 0.0, 0.0));
			vec3 ta = vec3(-gn.z, 0.0, gn.x);
			float across = abs(dot(H - v_wp, gn));
			float along = dot(H, ta);
			vec2 hq = H.xz;
			float en = 0.02 + 0.02 * wall_noise(hq * 13.0 + 7.0);
			float edge = min(across, abs(0.2 - across));
			vec3 cc;
			if (v_stone > 0.5) {
				vec2 rq = hq / vec2(2.0, 1.0);
				cc = textureGrad(albedo_tex, vec2(fract(rq.x), fract(rq.y) * 0.5), dFdx(rq) * vec2(1.0, 0.5), dFdy(rq) * vec2(1.0, 0.5)).rgb * 0.72;
				float ch = wall_noise(hq * 28.0 + 1.7);
				cc = mix(cc, vec3(0.42, 0.39, 0.34) * (0.8 + 0.4 * wall_noise(hq * 60.0)), smoothstep(0.74, 0.78, ch));
				cc *= 1.0 - 0.45 * (smoothstep(0.66, 0.73, ch) - smoothstep(0.74, 0.76, ch));
			} else {
				vec2 bq = vec2(along / 4.0, clamp(across / 0.25, 0.0, 1.0));
				vec2 bu = vec2(fract(bq.x), 0.75 + bq.y * 0.0625);
				cc = textureGrad(albedo_tex, bu, dFdx(bq) * vec2(1.0, 0.0625), dFdy(bq) * vec2(1.0, 0.0625)).rgb * timber_tints[clamp(int(v_wall.r * 8.0), 0, 5) % 3] * 0.8;
				// (the beam's joints: a butt every 2-3 m)
				float jt = fract(along / 2.6 + v_wall.b);
				cc *= 1.0 - 0.6 * (1.0 - smoothstep(0.0, 0.006, min(jt, 1.0 - jt)));
			}
			cc *= mix(0.5, 1.0, smoothstep(en * 0.5, en, edge));
			ALBEDO = cc;
			NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
			NORMAL_MAP = vec3(0.5, 0.5, 1.0);
			ROUGHNESS = 0.95;
			LIGHT_VERTEX = (VIEW_MATRIX * vec4(H, 1.0)).xyz;
		}
	}
#endif
#ifdef OWN_ROOF
	{
		vec3 ax = texture(aux_tex, UV).rgb;
		int ti = clamp(int(v_wall.r * 8.0), 0, 5);
		int rt = int(v_wall.a * 32.0) % 8;
		vec3 tint = vec3(1.0);
		if (ax.r > 0.9) tint = clay_tints[rt % 4];
		else if (ax.r > 0.6) tint = shingle_tints[rt % 4];
		else if (ax.r > 0.25) tint = timber_tints[ti % 3];
		vec3 col = c.rgb * tint;
		bool cover = COLOR.b > 0.5 && ax.r > 0.6;
		if (cover) {
			// each tile again its own value and warmth: its id on the sheet (32 steps), its run's hash, its roof's
			float th = wall_hash(vec2(floor(ax.b * 32.0), COLOR.g * 131.0 + v_wall.b * 17.0));
			float tw = wall_hash(vec2(th * 91.0, 3.7));
			col *= 1.0 + tile_val * (2.0 * th - 1.0);
			col *= mix(vec3(0.95, 0.99, 1.04), vec3(1.05, 0.99, 0.93), mix(0.5, tw, tile_warm));
			// (E9b6 r4) now and then an old tile, darker and browner; each tile bedded a few degrees off true
			float to = wall_hash(vec2(th * 53.0 + 1.3, tw * 17.0));
			if (to < old_tile) col *= vec3(0.74, 0.69, 0.64) * (0.92 + 0.16 * wall_hash(vec2(to * 71.0, 2.1)));
			NORMAL_MAP.xy += (vec2(wall_hash(vec2(th * 37.0, 5.3)), wall_hash(vec2(tw * 29.0, 8.9))) - 0.5) * tile_tilt;
			// dirt run down the slope: narrow streaks (5-15 cm across, along the ridge), broken lengthwise, darker toward the eaves
			float sd = wall_noise(vec2(v_lz * 7.0, v_rh * 0.45 + v_wall.b * 13.0));
			float sb = wall_noise(vec2(v_lz * 1.3 + 4.1, v_rh * 1.6));
			col *= 1.0 - trough_dirt * smoothstep(0.56, 0.74, sd) * smoothstep(0.3, 0.6, sb) * mix(1.0, 0.5, smoothstep(1.0, 4.0, v_rh)) * vec3(1.0, 1.02, 1.08);
		}
		// broad value patches over the roofs, each roof a little lighter or darker
		float vn = 0.6 * wall_noise(v_wp.xz * 0.45 + v_wp.y * 0.3) + 0.4 * wall_noise(v_wp.xz * 0.11 + 5.1);
		col *= 1.0 + roof_val_noise * (2.0 * vn - 1.0) + roof_house_val * (2.0 * wall_hash(v_wall.ba * 23.0) - 1.0);
		// soot round each chimney's top, spreading down the roof more than up, patchy
		float soot = 0.0;
		for (int i = 0; i < 32; i++) {
			vec4 ch = chimneys[i];
			if (ch.w <= 0.0) break;
			vec3 d = v_wp - ch.xyz;
			float up = max(d.y + 1.2, 0.0);
			soot += exp(-(dot(d.xz, d.xz) + up * up * 3.0) / (soot_r * soot_r));
		}
		float sn = wall_noise(v_wp.xz * 2.3 + v_wp.y * 1.7);
		col *= 1.0 - soot_dark * clamp(soot * (0.55 + 0.9 * sn), 0.0, 1.0);
		if (ax.r < 0.25) col *= 1.0 - stack_soot * COLOR.b;
		// (E9d) a chimney's cap stone grey: its top 0.25 m, 0.9x the brick's value
		if (ax.r < 0.25) {
			for (int i = 0; i < 32; i++) {
				vec4 ch = chimneys[i];
				if (ch.w <= 0.0) break;
				vec3 d = v_wp - ch.xyz;
				if (dot(d.xz, d.xz) < 0.8 && d.y > -0.28 && d.y < 0.3) { col = vec3(dot(col, LW)) * vec3(0.95, 0.97, 1.0) * 0.9; break; }
			}
		}
		if (cover) {
			// (E9d) the eave's run-off: the lowest 0.6-0.9 m darker, its upper edge broken by the drips' streaks
			float er = wall_noise(vec2(v_lz * 5.0 + v_wall.b * 9.0, 0.5));
			col *= mix(1.0 - eave_run, 1.0, smoothstep(0.45 + 0.3 * er, 0.75 + 0.3 * er, v_rh));
			// 2-4 m blotches toward grey-brown, lighter or darker
			float bn = wall_noise(v_wp.xz * 0.33 + 17.0 + v_wall.b * 3.0);
			float bl = dot(col, LW);
			// (E9d r2: the clay still read clean, its rows even orange: on clay the blotches stronger, a second finer layer
			// (1-2 m), and leaning dark (weathered clay goes brown-grey, it doesn't bleach))
			float rb = ax.r > 0.9 ? roof_blotch_clay : roof_blotch;
			float bs = 2.0 * bn - 1.0;
			col = mix(col, vec3(bl) * vec3(1.05, 0.97, 0.88), rb * 2.5 * abs(bs)) * (1.0 + rb * (bs > 0.0 ? 0.45 * bs : bs));
			if (ax.r > 0.9) {
				// (0.6-1.2 m: a few tiles' worth, so a roof seen 4 m wide still breaks up; moss-dark and grey-brown by turns)
				float bf = wall_noise(v_wp.xz * 1.4 + 41.0 + v_wall.b * 5.0);
				float bg = wall_noise(v_wp.xz * 0.7 - 13.0 + v_wall.b * 7.0);
				col *= 1.0 - rb * 1.6 * smoothstep(0.42, 0.78, bf) * (0.7 + 0.3 * wall_noise(v_wp.xz * 3.1));
				col = mix(col, vec3(dot(col, LW)) * vec3(1.02, 0.97, 0.9), rb * 2.0 * smoothstep(0.5, 0.8, bg));
			}
			// lichen on clay: flecks (5-15 cm) in patches, most on the lower third, ochre or grey-green; (r2) its value
			// taken from the clay's own (a little lighter), not set: on shaded clay it stood as pale grey camouflage
			if (ax.r > 0.9) {
				float lp = smoothstep(0.55, 0.7, wall_noise(v_wp.xz * 0.6 + v_wall.b * 11.0)) * mix(1.0, 0.35, smoothstep(1.2, 2.4, v_rh));
				float lf = smoothstep(0.62, 0.7, wall_noise(v_wp.xz * 9.0 + v_wp.y * 4.0));
				vec3 lc = mix(vec3(1.18, 1.0, 0.56), vec3(0.96, 1.02, 0.84), wall_noise(v_wp.xz * 1.3));
				col = mix(col, lc * dot(col, LW) * 1.15 * (0.85 + 0.25 * wall_noise(v_wp.xz * 23.0)), lichen * lp * lf);
			}
		}
		float rough = ax.g;
		if (cover) {
			// moss on the slopes facing north, patchy, thickest toward the eaves and on the shaded roofs' lower courses
			float fn = dot(v_wn.xz, moss_dir);
			float mn = 0.6 * wall_noise(v_wp.xz * 1.7 + v_wp.y * 1.3) + 0.4 * wall_noise(v_wp.xz * 6.1 - v_wp.y * 2.9);
			float hm = 0.45 + 0.55 * wall_hash(v_wall.bb * 5.1 + 0.7);
			float em = mix(1.0, 0.35, smoothstep(0.4, 3.5, v_rh));
			float m = roof_moss * hm * em * smoothstep(0.05, 0.45, fn) * smoothstep(0.3, 0.7, mn);
			m += moss_any * hm * smoothstep(0.6, 0.72, mn) * mix(1.0, 0.6, smoothstep(0.4, 3.5, v_rh));
			m = clamp(m, 0.0, 0.85);
			col = mix(col, roof_moss_color.rgb * (0.55 + 0.4 * mn), m);   // (E9b6 r4: darker, it read chartreuse in the sun)
			rough = mix(rough, 1.0, m);
		}
		col *= mix(1.0 - roof_occl, 1.0, COLOR.r);
		ALBEDO = col;
		ROUGHNESS = rough;
		// (E9d r3) the night sky's light on a slope turned from the moon (only there: the moonlit slopes as they were): the moon's slope lit, the other went to pure black
		// under the night grade's toe (e9d3 townnight_o_01); the open sky over a roof lights it more than the ambient gives
		EMISSION += col * roof_night * flora_light.x * vec3(0.6, 0.72, 1.0) * smoothstep(0.15, 0.7, v_wn.y) * smoothstep(0.45, 0.05, dot(v_wn, key_dir.xyz));
		// (--roof-debug: red the clay covering, green the shingle, blue the rest)
		if (roof_debug > 0.5) { ALBEDO = cover ? (ax.r > 0.9 ? vec3(1.0, 0.0, 0.0) : vec3(0.0, 1.0, 0.0)) : vec3(0.0, 0.0, 1.0); EMISSION = ALBEDO * 0.6; }
	}
#endif
#ifdef OWN_FOLIAGE
	// The crown's normals point out from the trunk on both faces of a card (Godot turns a back
	// face's round), so a crown shades as one mass; light through the needles from behind; each
	// tree's green a little warmer or cooler (v_jit).
	// Each vertex's colour (env_trees.py): r how open it is (1 at the crown's skin, 0.35 at its axis),
	// g how far out along its spray (0 foot, 1 tip), b 1 on a spray card (its front its upper side).
	if (!FRONT_FACING) NORMAL = -NORMAL;
#ifdef OWN_BROADLEAF
	// (an alder's crown is a dome of leaves facing every way: its normals bent up toward the sky, so its
	// top takes the sun whole and its sides most of it; judge E4c: its sun-side half alone read lit)
	if (UV.x < 0.75) NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz * 0.6);
#endif
	float night = flora_light.x, low_sun = flora_light.y;
	float open_ = mix(1.0, COLOR.r, core);
	if (UV.x < 0.75) {
		// each tree its own green: hue within 7 degrees (olive to blue-green), value within 13% (two hashes, not one)
		float j2 = fract(v_jit * 7.31 + 0.37);
		// (up no more than 8%: a near tree jittered up read as the frame's brightest mint, judge E4c)
		ALBEDO = max(hue_turn(ALBEDO, radians(mix(-jit_hue, jit_hue, v_jit))), vec3(0.0)) * mix(jit_lo, jit_hi, j2);
		if (fract(v_jit * 13.37 + 0.11) < old_share) ALBEDO = mix(ALBEDO, vec3(dot(ALBEDO, LW)) * vec3(1.3, 1.0, 0.6), old_amt * mix(0.6, 1.0, fract(v_jit * 5.71)));
		// (a tree by the camera, in the frame's foreground, a shade darker by day: in full sun the nearest spruce
		// stood as the frame's brightest mint at roaddawn, judge E4c)
		ALBEDO *= 1.0 - near_dim * (1.0 - smoothstep(16.0, 30.0, length(VERTEX))) * (1.0 - night);
		// a tier's underside (a card seen from below) in its own shade
		if (COLOR.b > 0.5 && !FRONT_FACING) open_ *= 0.7;
		// a low sun's warmth only at the tips: the sunlit sprays a little greyer and cooler
		float tip = smoothstep(0.55, 1.0, COLOR.g) * smoothstep(0.75, 1.0, COLOR.r);
		float lum = dot(ALBEDO, LW);
		ALBEDO = mix(ALBEDO, vec3(lum) * vec3(0.8, 1.0, 1.16), 0.28 * low_sun * (1.0 - tip));
		// under a low sun the sunlit needles no warmer than hue_floor (sun x needle went yellow, judge E4b):
		// the hue the key gives them (sRGB, about) turned back up to it
		vec3 key = flora_light.z > 0.0 ? clamp(vec3(flora_light.z, 1.0, flora_light.w), vec3(0.2), vec3(5.0)) : vec3(1.0);
		float hl = hue_of(sqrt(max(ALBEDO * key, vec3(0.0))));
		ALBEDO = max(hue_turn(ALBEDO, radians(clamp(hue_floor - hl, 0.0, 60.0) * low_sun)), vec3(0.0));
		// the crown's dark core: inner sprays darker (their light shut out by the crown round them)
		ALBEDO *= mix(mix(0.5, core_night, night), 1.0, open_) * mix(1.0, 0.62, night);
		ALBEDO *= 1.0 + tip_lift * night * smoothstep(0.35, 1.0, COLOR.g) * smoothstep(0.6, 1.0, COLOR.r);  // (under the moon a crown's lit tips no brighter than the moonlit road)
		// (under the moon a crown in shade a deep blue-green, not the grade's navy: judge E4c)
		ALBEDO *= mix(vec3(1.0), vec3(0.7, 1.15, 0.9), night);
		ALBEDO = max(hue_turn(ALBEDO, radians(night_hue * night)), vec3(0.0)) * mix(1.0, night_value, night);
		{
			float tn = night * smoothstep(0.3, 1.0, COLOR.g) * smoothstep(0.55, 1.0, COLOR.r);
			ALBEDO = mix(ALBEDO, vec3(dot(ALBEDO, LW)), tip_night_sat * tn) * (1.0 - tip_night_dim * tn);
		}
#ifdef OWN_BROADLEAF
		// (Low Ford lf5p, judge lf4 #8: the night bushes too saturated) toward their own grey by flora_night.x by night; 0 as built
		ALBEDO = mix(ALBEDO, vec3(dot(ALBEDO, LW)), flora_night.x * night);
#endif
		// light through the needles from behind, a cool green (hue about 125) whatever the key's colour
		// (sun x needle colour went yellow at dawn, judge E4b): as strong as the needles' own would be,
		// the key's tint taken back out; under the moon a third of it, deep blue-green
		float bl = dot(ALBEDO * vec3(0.18, 0.22, 0.24) * key, LW) / dot(vec3(0.45, 1.0, 0.53), LW);
		BACKLIGHT = mix(vec3(0.45, 1.0, 0.53) * bl / key, ALBEDO * vec3(0.04, 0.07, 0.065), night) * open_;
		BACKLIGHT *= 1.0 - near_back * (1.0 - smoothstep(16.0, 30.0, length(VERTEX))) * (1.0 - night);
		// (the crown's up-facing normals would take the whole sky's light: inside a crown most of it is
		// shut out; at night the needles take less of the moonlit sky still)
		// (judge E4c: at 0.36 the shaded crowns under the moon went black, below the shaded road: the moonlit
		// sky's light let in whole, and less shut out at the core)
		AO = mix(0.5, 1.0, night) * mix(mix(0.45, 0.7, night), 1.0, open_);
#ifdef OWN_BROADLEAF
		AO *= mix(sky_amb, 1.0, night);
#endif
		// (and a moonlit fill the shade keeps, deep blue-green: the night sky's light under a crown is more than the
		// ambient alone gives, its shaded crowns as light as the shaded road, judge E4c)
		EMISSION += ALBEDO * vec3(0.45, 1.0, 0.82) * night_fill * night * mix(0.6, 1.0, open_);
		// (no wet sheen on needles: the moon's specks read as frost-blue glints)
		SPECULAR = 0.12;
		AO_LIGHT_AFFECT = 0.0;
	} else {
		ALBEDO *= mix(0.6, 1.0, open_);
		// (Low Ford lf5p, judge lf4 #4: the canopy fade's kept stump read from above as a black pit: its hollow, the trunk's
		// inside, seen down through the cut) the inside (back faces) of a faded tree's trunk drawn as the cut's pale wood,
		// facing up, so the stump reads as a sawn top with its bark round it; stump_top 0: as before
		if (v_fade > 0.0 && !FRONT_FACING && stump_top > 0.0) {
			// (lf6d) the cut's face where the view ray crosses the cut's plane (local y = crown_keep): its growth rings
			// about the trunk's middle, a darker heart, the pale sapwood under the bark, a check split across it
			mat4 im = inverse(MODEL_MATRIX);
			vec3 lp = (im * (INV_VIEW_MATRIX * vec4(VERTEX, 1.0))).xyz;
			vec3 lc = (im * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
			float tc = (crown_keep - lc.y) / min(lp.y - lc.y, -1e-4);
			vec2 hc = lc.xz + (lp.xz - lc.xz) * tc;
			float rr = length(hc);
			float rw = length(lp.xz);
			float ring = 0.5 + 0.5 * sin(rr * 160.0 + 2.0 * sin(atan(hc.y, hc.x) * 3.0 + v_jit * 6.0));
			vec3 cut = stump_wood * mix(0.85, 1.1, fract(v_jit * 7.3)) * mix(0.78, 1.0, ring);
			cut *= mix(0.72, 1.0, smoothstep(0.0, 0.05, rr));
			cut = mix(cut, stump_wood * 1.25, smoothstep(0.7, 0.92, rr / max(rw, 1e-3)) * 0.6);
			cut *= 1.0 - 0.45 * (1.0 - smoothstep(0.004, 0.012, abs(dot(hc, vec2(cos(v_jit * 6.28), sin(v_jit * 6.28)))))) * step(rr, rw * 0.8);
			ALBEDO = mix(ALBEDO, cut, stump_top);
			NORMAL = normalize(mix(NORMAL, (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, stump_top));
		}
	}
#endif

#ifdef OWN_ROCK
	{
		vec3 wp = v_wpos;
		vec3 wn = normalize(v_wnrm);
		vec3 bw = pow(abs(wn), vec3(4.0));
		bw /= dot(bw, vec3(1.0));
		vec2 ux = wp.zy / tile, uy = wp.xz / tile + 0.31, uz = wp.xy / tile + 0.57;
		vec4 st = texture(stone_tex, ux) * bw.x + texture(stone_tex, uy) * bw.y + texture(stone_tex, uz) * bw.z;
		vec2 nx = texture(stone_nor, ux).rg * 2.0 - 1.0, ny = texture(stone_nor, uy).rg * 2.0 - 1.0, nz = texture(stone_nor, uz).rg * 2.0 - 1.0;
		vec3 bn = normalize(wn + bump * (vec3(0.0, nx.y, nx.x) * bw.x + vec3(ny.x, 0.0, ny.y) * bw.y + vec3(nz.x, nz.y, 0.0) * bw.z));
		vec3 col = st.rgb * stone_tint;
		// (a broad value patch over many repeats, so a cliff's sheet does not read as tiles; each copy its own shade)
		float mac = texture(stone_tex, wp.xz / (tile * 7.3) + vec2(0.37, 0.11)).a;
		col *= mix(1.0 - macro, 1.0 + macro, mac) * (1.0 + inst_val * (2.0 * v_jit - 1.0));
		if (fract(v_jit * 13.71) < cool_share) col *= cool_tint;
		if (stone_mix > 0.0) {
			vec3 cls = UV.x < 0.3333 ? stone_a : UV.x < 0.6667 ? stone_b : stone_c;
			col *= mix(vec3(1.0), cls, stone_mix) * (1.0 + stone_val * (2.0 * UV.y - 1.0));
		}
		// the baked rims, cracks and hollows
		col *= (1.0 + edge_light * COLOR.r) * (1.0 - cavity_dark * COLOR.g) * (1.0 - occl_dark * COLOR.b);
		// grime from the foot up, its line broken by the sheet's patches
		if (grime_h > 0.0) col *= mix(1.0 - grime_dark, 1.0, smoothstep(0.0, grime_h, v_foot + 0.3 * grime_h * (st.a - 0.5)));
		if (sky_dark > 0.0) col *= mix(1.0 - sky_dark, 1.0, smoothstep(0.42, 0.82, textureLod(expo_tex, (wp.xz + zone_size * 0.5) / zone_size, 0.0).r));
		// moss on what faces up (and toward moss_side), in patches, more in the hollows, less on worn rims
		vec2 ms = moss_side / max(length(moss_side), 1e-4);
		float face = bn.y + moss_side_amount * dot(bn.xz, ms);
		float mz = smoothstep(moss_face.x, moss_face.y, face) * smoothstep(0.35, 0.75, st.a + 0.3 * COLOR.g + 0.2 * COLOR.b - moss_edge * COLOR.r);
		// lichen: pale spots on its tops and sides
		float lich = texture(stone_tex, wp.zx / (tile * 0.37) + 0.5).a;
		float lz = smoothstep(0.7, 0.8, lich) * smoothstep(-0.2, 0.4, bn.y) * lichen_amount;
		// wet: under the water's height + wet_above, dark and glossy, its edge ragged; no moss or lichen there
		float wy = water_level.w > 0.5 ? water_level.x : -1e5;
		float w0 = wet_share > 0.0 ? wy + wet_share * mix(0.45, 1.35, fract(v_jit * 7.13)) * (v_top - wy) - 0.02 : wy + wet_above * 0.5;
		float w1 = wet_share > 0.0 ? w0 + 0.03 + 0.06 * st.a : wy + wet_above * (1.0 + 0.8 * st.a);
		float wet = 1.0 - smoothstep(w0, w1, wp.y);
		mz *= moss_amount * (1.0 - wet);
		lz *= 1.0 - wet;
		col = mix(col, moss_color.rgb * (0.75 + 0.5 * st.a), mz);
		col = mix(col, lichen_color.rgb * (0.85 + 0.3 * st.r), lz);
		if (litter > 0.0) {
			float lsp = texture(stone_tex, wp.xz / (tile * 0.53) + vec2(0.21, 0.67)).a;
			float lt = smoothstep(0.78, 0.95, bn.y) * smoothstep(0.15, 0.5, COLOR.g + COLOR.b + 0.35 * mz) * smoothstep(0.55, 0.7, lsp) * (1.0 - wet);
			col = mix(col, litter_color.rgb * (0.7 + 0.6 * st.r), litter * lt);
		}
		col *= mix(1.0, wet_dark, wet);
		float damp = top_damp * smoothstep(0.0, 0.25, flora_light.x) * (1.0 - wet) * mix(0.55, 1.0, smoothstep(0.3, 0.7, st.a + 0.25 * COLOR.g));
		col *= (1.0 - damp) * mix(1.0, top_level, (1.0 - wet) * smoothstep(0.4, 0.8, v_up));
		if (algae > 0.0 && water_level.w > 0.5) {
			float ab = smoothstep(wy - 0.02, wy - 0.005, wp.y) * (1.0 - smoothstep(wy + algae_w * (0.5 + 0.8 * st.a), wy + algae_w * (0.9 + 1.0 * st.a), wp.y));
			col = mix(col, algae_color.rgb * (0.8 + 0.4 * st.a), algae * ab);
		}
		col *= mix(vec3(1.0), night_tint, flora_light.x);
		ALBEDO = col;
		ROUGHNESS = mix(mix(stone_rough, wet_rough, wet), wet_rough, damp_gloss * damp / max(top_damp, 1e-3));
		SPECULAR = mix(0.35, 0.5, wet);
		AO = amb_occl;
		AO_LIGHT_AFFECT = 0.0;
		NORMAL = normalize((VIEW_MATRIX * vec4(bn, 0.0)).xyz);
		// its shade keeps colour: a little of its own albedo given back, cool by day, more under the moon
		EMISSION += col * shade * mix(shade_floor, night_fill, flora_light.x);
	}
#endif

	// The Flare's drain and frost (flare_world.gdshaderinc).
	if (flare_live()) {
		vec3 fl_a = ALBEDO; float fl_r = ROUGHNESS; vec3 fl_e = EMISSION;
		flare_prop((INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz, NORMAL, INV_VIEW_MATRIX, fl_a, fl_r, fl_e);
		ALBEDO = fl_a; ROUGHNESS = fl_r; EMISSION = fl_e;
	}
}

#ifdef OWN_BROADLEAF
// The alder's own light (its leaves take only part of the key's shadow, self_shadow): Lambert with the
// built-in back light's transmission, wrapped (wrap) and floored; its bark (u > .75) the shadow whole.
void light() {
	float att = LIGHT_IS_DIRECTIONAL && UV.x < 0.75 ? mix(1.0, ATTENUATION, self_shadow) : ATTENUATION;
	// (leaves pass light round the crown: wrapped, so its far side from the sun is lit low, not the sky's blue alone)
	float d = max(clamp((dot(NORMAL, LIGHT) + wrap) / (1.0 + wrap), 0.0, 1.0), 0.45);
	// (the engine multiplies it by the albedo after; the back light's transmission as the built-in's)
	float lift = LIGHT_IS_DIRECTIONAL && UV.x < 0.75 ? 1.0 + sun_lift * smoothstep(0.55, 0.9, d) * (1.0 - flora_light.x) * (1.0 - flora_light.y) : 1.0;
	// (by day only, not under a low sun: at 0.7 it took the dawn alder's sunlit top to hue 86, under its floor of 90)
	DIFFUSE_LIGHT += LIGHT_COLOR * att * (d * lift + BACKLIGHT * (1.0 - d)) / PI;
	// (no highlight: matte leaves; a GGX one here blew the crown out cream by day)
}
#endif

#if defined(OWN_FOLIAGE) && !defined(OWN_BROADLEAF)
// (lf1b) The spruce's own light: Lambert with the built-in back light's transmission, as the engine's; a lamp's (not the
// key's) scaled by lamp_gain and its green cut by lamp_green on the needles (u < .75), so her warm light reads olive on
// them, not lime. No highlight (SPECULAR was 0.12: the moon's specks read as frost).
void light() {
	vec3 lc = LIGHT_COLOR;
	if (!LIGHT_IS_DIRECTIONAL && UV.x < 0.75) lc *= vec3(1.0, 1.0 - lamp_green, 1.0 - 0.5 * lamp_green) * lamp_gain;
	float d = max(dot(NORMAL, LIGHT), 0.0);
	DIFFUSE_LIGHT += lc * ATTENUATION * (d + BACKLIGHT * (1.0 - d)) / PI;
}
#endif
