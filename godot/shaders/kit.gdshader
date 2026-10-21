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
uniform float hue_floor = 100.0;
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
varying vec4 v_wall;
varying float v_hgt;
varying vec3 v_wp;

float wall_hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float wall_noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(wall_hash(i), wall_hash(i + vec2(1.0, 0.0)), f.x), mix(wall_hash(i + vec2(0.0, 1.0)), wall_hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
#endif
#ifdef OWN_ROOF
// Our own roofs (tools/assets/env_roof.py, KitLook.Roof; E9b2), on the walls' uniforms above and the roof sheet: its aux
// r the class (1 clay, .75 shingle, .5 timber taking the house's timber tint, 0 untinted), g roughness, b each tile's id;
// the vertex colour r occlusion, g the face's hash, b 1 on the covering (on a chimney: its soot), a the sag weight;
// each copy's custom data as the walls' with a = (treatment * 8 + roof tint + .5) / 32.
uniform vec3 clay_tints[4];      // (godot/data/house_look.json)
uniform vec3 shingle_tints[4];
uniform vec4 chimneys[32];       // each stack's top (xyz), w 1; OwnWalls.Build
uniform float roof_sag = 0.04;   // each house's roof sags this much more at most (m), by its copy's hash
uniform float tile_val = 0.12;   // each tile lighter or darker
uniform float tile_warm = 0.5;   // and warmer or cooler
uniform float roof_val_noise = 0.08;
uniform float roof_house_val = 0.06;
uniform float soot_r = 2.0;      // the soot round a chimney's top (m)
uniform float soot_dark = 0.6;
uniform float stack_soot = 0.75; // a stack's own top
uniform float roof_moss = 0.6;   // on slopes facing moss_dir (north), thickest toward the eaves
uniform vec2 moss_dir = vec2(0.0, -1.0);
uniform vec4 roof_moss_color : source_color = vec4(0.29, 0.32, 0.16, 1.0);
uniform float roof_occl = 0.55;
varying vec3 v_wn;
varying float v_rh;
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
	v_wall = INSTANCE_CUSTOM;
	v_hgt = VERTEX.y + INSTANCE_CUSTOM.g;
	v_wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
#endif
#ifdef OWN_ROOF
	v_wall = INSTANCE_CUSTOM;
	VERTEX.y -= COLOR.a * roof_sag * fract(INSTANCE_CUSTOM.b * 7.13 + 0.31);
	v_hgt = VERTEX.y + INSTANCE_CUSTOM.g;
	v_rh = VERTEX.y;
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
	vec2 mo = see_parts(VERTEX, VIEW_MATRIX, INV_VIEW_MATRIX, PROJECTION_MATRIX, CAMERA_POSITION_WORLD);
	float kept = see_through(mo);
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
			col = mix(col * (1.0 - 0.35 * rim), lc, lost);
		}
		// grime from the ground: a brown-green band, darkest to 0.5 m, streaked with splash, gone by 1.2 m
		float sn = wall_noise(vec2((v_wp.x + v_wp.z) * 11.0, v_wp.y * 1.3));
		float hn = h + 0.25 * (gn - 0.5);
		col *= 1.0 - grime_dark * (1.0 - smoothstep(0.35, grime_h, hn + 0.2 * (sn - 0.5)));
		col *= mix(1.0 - house_rise, 1.0, smoothstep(0.0, 6.0, h));
		float splash = 1.0 - smoothstep(0.0, splash_h, hn - 0.25 * sn);
		col *= mix(vec3(1.0), vec3(1.0 - splash_dark) * vec3(0.95, 0.97, 0.82), splash);
		// stains under the sills: streaks running down (the sheet's noise stretched down the wall)
		float streak = smoothstep(0.25, 0.75, texture(aux_tex, vec2(UV.x * 1.7, UV.y * 0.1)).b);
		col *= 1.0 - stain_dark * COLOR.g * (0.3 + 0.7 * streak);
		col *= mix(1.0 - occl, 1.0, COLOR.r);
		ALBEDO = col;
		ROUGHNESS = ax.g;
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
		float rough = ax.g;
		if (cover) {
			// moss on the slopes facing north, patchy, thickest toward the eaves and on the shaded roofs' lower courses
			float fn = dot(v_wn.xz, moss_dir);
			float mn = 0.6 * wall_noise(v_wp.xz * 1.7 + v_wp.y * 1.3) + 0.4 * wall_noise(v_wp.xz * 6.1 - v_wp.y * 2.9);
			float hm = 0.45 + 0.55 * wall_hash(v_wall.bb * 5.1 + 0.7);
			float em = mix(1.0, 0.35, smoothstep(0.4, 3.5, v_rh));
			float m = roof_moss * hm * em * smoothstep(0.05, 0.45, fn) * smoothstep(0.3, 0.7, mn);
			m += 0.25 * roof_moss * hm * smoothstep(0.62, 0.82, mn) * em;
			m = clamp(m, 0.0, 0.85);
			col = mix(col, roof_moss_color.rgb * (0.75 + 0.5 * mn), m);
			rough = mix(rough, 1.0, m);
		}
		col *= mix(1.0 - roof_occl, 1.0, COLOR.r);
		ALBEDO = col;
		ROUGHNESS = rough;
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
		ALBEDO = max(hue_turn(ALBEDO, radians(mix(-7.0, 7.0, v_jit))), vec3(0.0)) * mix(0.87, 1.08, j2);
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
		ALBEDO *= mix(mix(0.5, 0.8, night), 1.0, open_) * mix(1.0, 0.62, night);  // (under the moon a crown's lit tips no brighter than the moonlit road)
		// (under the moon a crown in shade a deep blue-green, not the grade's navy: judge E4c)
		ALBEDO *= mix(vec3(1.0), vec3(0.7, 1.15, 0.9), night);
		ALBEDO = max(hue_turn(ALBEDO, radians(night_hue * night)), vec3(0.0)) * mix(1.0, night_value, night);
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
		float w0 = wet_share > 0.0 ? wy + wet_share * (v_top - wy) - 0.02 : wy + wet_above * 0.5;
		float w1 = wet_share > 0.0 ? w0 + 0.015 + 0.035 * st.a : wy + wet_above * (1.0 + 0.8 * st.a);
		float wet = 1.0 - smoothstep(w0, w1, wp.y);
		mz *= moss_amount * (1.0 - wet);
		lz *= 1.0 - wet;
		col = mix(col, moss_color.rgb * (0.75 + 0.5 * st.a), mz);
		col = mix(col, lichen_color.rgb * (0.85 + 0.3 * st.r), lz);
		col *= mix(1.0, wet_dark, wet);
		if (algae > 0.0 && water_level.w > 0.5) {
			float ab = smoothstep(wy - 0.02, wy - 0.005, wp.y) * (1.0 - smoothstep(wy + algae_w * (0.5 + 0.8 * st.a), wy + algae_w * (0.9 + 1.0 * st.a), wp.y));
			col = mix(col, algae_color.rgb * (0.8 + 0.4 * st.a), algae * ab);
		}
		col *= mix(vec3(1.0), night_tint, flora_light.x);
		ALBEDO = col;
		ROUGHNESS = mix(stone_rough, wet_rough, wet);
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
