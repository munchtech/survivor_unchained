// The body of her outfits' shader (heroine_outfit.gdshader, and heroine_outfit_metal.gdshader for
// every metal key, which defines OUTFIT_METAL_LIGHT: the same, with metal's own light and reflection).

uniform int kind = 0;                              // 0 leather, 1 metal, 2 cloth, 3 gloss, 4 twill, 5 satin
uniform sampler2D albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D orm : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;   // (G rough, B metal)
uniform bool has_orm = false;
uniform float roughness_value = 0.55;
uniform float metallic_value = 0.0;
uniform float repeats = 3.0;                       // its texture's repeats a metre (its UVs' units)
uniform vec3 tint : source_color = vec3(1.0);
// Leather's stitches: in from the edge by `stitch_in`, `stitch_len` long.
uniform float stitch_in = 0.0045;
uniform float stitch_len = 0.004;
uniform vec3 thread : source_color = vec3(0.78, 0.7, 0.55);
uniform vec3 dye : source_color = vec3(1.0);        // (a dye zone's colour: HerWear sets it with dye_amount 1 on the surfaces of that zone)
uniform float dye_amount = 0.0;                    // (0 = as built, bit for bit)
uniform float grain = 0.6;                         // how strongly the fine grain shows
uniform float view_pull = 0.0;                     // metres drawn toward the camera (a decal on her skin: the ink, never z-fighting it)
uniform bool test_flat = false;                  // (the legal motion check: every garment flat grey, coverage unchanged)
uniform float gold_gloss = 0.0;                   // (0 = as before; 1 = gold's roughness drawn to gold_rough: crisper, brighter highlights, tint and albedo untouched)
uniform float gold_rough = 0.2;
uniform float gold_floor = 0.08;                  // (gold's own colour added as a dim emission, less in crevices, so it never goes black at night; 0.08 by judge g4: warm gold at night, no change by day, 0.15 turned shadowed trim to flat tan)
// (the Look's portrait rig, by its campfire at night: polished steel read as blue enamel with clipped white highlights and
// leather as wet vinyl there, judge s29 wd; under the rig only (People.HerLookRig sets look_rig), a floor on their roughness)
uniform float look_rig = 0.0;
uniform float look_metal_rough = 0.38;             // (N4: was 0.30; broader, the dome's facets never show through its highlights)
uniform float look_metal_dim = 1.0;                // (r4: was 0.70, older than the 1.2 highlight cap: the Look pauldron went a black lacquered ball. And its reflectance: F0 is its colour, so its highlights under the rig's key stay graded, not clipped)
uniform float look_leather_rough = 0.60;
// (armor 16, judge A2: at the Look her pauldrons read as flat toon navy. The rig's lights aim at her face, her shoulders
// at their cones' edges, and the night around the camp gives plate nothing to reflect: under the rig only, the key's
// softbox (high, near the lens, to camera right: GameFront's keyAt) and a dim cool dome over her, in its reflection)
uniform float look_metal_env = 0.0;               // (0 = as before, bit for bit; People sets 1.6 on her metal, N4)
uniform float look_metal_key = 6.0;
uniform float look_metal_dome = 0.45;
uniform vec3 look_key_dir = vec3(0.15, 0.85, 0.5);   // (view space: right, up, toward the lens)
// (armor 16 N4, OJ1: the round-1 lobe, a sharp power of one direction, drew a radial starburst on the pauldrons' domes
// (their normals fan out from the mesh's pole) in a pink chrome. Now the softbox is a soft rectangle, its middle flat so
// no facet shows through, neutral to cool; the rig's own lamps' highlights on the plate muted toward the steel's
// grey-blue (look_metal_mute); the gold trim its own share of the box, a bevel line on each roll)
uniform float look_box_soft = 0.8;                 // (its edge's share of it: a broad soft falloff, so a facet bends no hard line)
uniform float look_box_w = 0.7;                    // (the box's half-width and half-height, as tangents off its middle)
uniform float look_box_h = 0.45;
uniform vec3 look_box_tint = vec3(0.90, 0.95, 1.0);
uniform float look_metal_mute = 0.0;
uniform float look_gold_rough = 0.3;               // (armor 17 N5: gold's roughness under the Look's rig)
uniform float look_gold_floor_cut = 0.75;          // (and the share of its floor glow cut there)
uniform float look_gold_key = 1.0;                  // (the gold's share of the box, of the plate's)
uniform float leather_rough_floor = 0.0;          // (armor 14, 22 Oct: a leather's roughness floor off its burnished edges, from its outfit_materials.json row "rough_floor". The arcanist bodysuit's plumleather at 0.58: at 0.42 its cups caught the key as a pointed highlight at each apex (read as nipple pokes) and a dark band under it (a crease), and a plastic streak at night; the shape alone was smooth)
uniform float leather_rough_var = 1.0;            // (armor 14: its roughness map's spread kept, 1 as scanned; under 1 the map's blotches ease toward the floor)
uniform float leather_clearcoat = 0.0;            // (armor 14: a thin clear sheen over a leather, off its edges; 0 none)
uniform float leather_clearcoat_rough = 0.3;
// (armor 16, the arcanist's white opera gloves read as a flat paper tube by day: a stretch satin's
// light is mostly its sheen, so its body a little darker and turning darker round the form, and its
// sheen a long soft streak along the arm (heroine_outfit_satin.gdshader's light). Its outfit_materials.json
// row "sheen" sets it and picks that shader; 0 = as before, bit for bit, on every other satin)
uniform float satin_sheen = 0.0;
uniform float satin_body = 1.0;                   // (its body's value, of the texture's)
uniform float satin_turn = 1.0;                   // (its value where it turns from the eye, of its face-on value)
uniform float satin_along = 0.75;                 // (heroine_outfit_satin.gdshader: its sheen's roughness along the arm, a long streak)
uniform float satin_across = 0.22;                // (and across it, narrow: the streak follows the form)
uniform float satin_spec_cap = 1.6;               // (its sheen eases toward, never past, this times a white card's light)
uniform int satin_axis = 2;                       // (its long way: 2 its UVs' v, 1 their u)
// (armor 16 N4, OJ1: "satin gloves are never perfectly smooth, and the folds are what make satin read as satin". Its
// wrinkles as a bump: soft ruching just above the wrist, a few creases inside the elbow, two long diagonal folds round
// the forearm. Along the arm by its UVs' v (the glove's top at satin_top_v, its wrist at satin_wrist_v, satin_uv_per_m
// to the metre); round it by the angle People.SatinAround writes into UV2 as (cos, sin), 0 at her front. 0 = none)
uniform float satin_wrinkle = 0.0;
uniform float satin_top_v = 1.0;
uniform float satin_wrist_v = -9.0;
uniform float satin_uv_per_m = 40.0;
#ifdef OUTFIT_SATIN_LIGHT
varying vec3 v_axis;                              // (the form's long way here, view space)
varying float v_aniso;                            // (1: streaked along v_axis; 0 round)
#endif
// Metal's standard (touch-up, 18 Oct): worn, forged; never a mirror.
uniform float metal_rough = 0.45;                  // (its plate's satin roughness, varied about this over the piece: 0.35-0.55 with the detail)
uniform float metal_rough_wear = 0.26;             // (where worn bright: its edges and, in patches, what stands out; 0.2-0.3)
uniform float metal_rough_floor = 0.22;            // (no metal smoother than this; only worn edges get near it, the plates stay over 0.3)
uniform float metal_grime = 1.0;                   // (dirt in its recesses: dark, brown, dull, not metal)
uniform float metal_dent = 0.16;                   // (the hammered unevenness)
uniform float brass_dim = 0.85;                    // (gold read as aged brass: a little darker and greyer than the bright alloy; the rest from grime)
uniform float brass_rough_add = -0.18;            // (metal r3: raised trim smoother than the plate: it catches a line of light, gold not tan; r4: was -0.10, the thin rim band (in the gold mask, debug_view 4) still read tan by day)
uniform vec3 gold_tone : source_color = vec3(1.0, 0.847, 0.569);   // (metal r3: gold's reflectance, Filament's #ffd891; times brass_dim for aged brass. Was its scan's mean, greyed: it read tan and matte by day)
uniform float metal_hammer = 0.09;                 // (planishing marks, 8 mm)
uniform float steel_dim = 1.0;                      // (round 1 darkened the plate's field to 0.8; physical now, the reflection held instead)
uniform vec3 steel_warm = vec3(1.0);                // (round 1 warmed steel against the sky's blue; neutral now, the reflection held instead)
uniform float metal_wear_bright = 1.3;
// Round 2 (the look bible's page, items 1-4 and 6): one shared scratch-and-pit detail
// (tools/assets/metal_wear_detail.py: RG its normal, B a roughness offset, A cavity), a
// finish per key (0 bare, as built; 1 blued steel, worn back to bright steel at its edges),
// and (heroine_outfit_metal.gdshader only) metal's own light and reflection, below.
uniform sampler2D metal_detail : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool has_detail = false;
uniform float detail_repeats = 2.5;                // (a metre: 0.39 mm a texel)
uniform float detail_normal = 0.7;
uniform float detail_rough = 1.0;
uniform float detail_cavity = 1.0;
uniform int finish = 0;
uniform vec3 blued : source_color = vec3(0.43, 0.44, 0.49);        // (blued steel: its reflectance; deep blue-black where it reflects the dark. metal r3: was 0.36,0.38,0.47, black rubber in moonlit and dawn shade; r4: was 0.42,0.44,0.52, candy blue by the moon)
uniform vec3 blued_temper : source_color = vec3(0.46, 0.43, 0.53); // (its temper sheen: a faint violet in patches; scaled with blued, metal r3; r4: was 0.57)
uniform float blued_chip = 1.0;                    // (how far its worn edges chip back to bright steel)
// (body 16: finish 2, blue enamel chipped at its edges to bright steel, the look bible's other Warden finish. Fully
// metallic blued steel has no diffuse colour: its navy showed only in what it reflected, so a plate turned edge-on to a
// bright sky read pale glassy silver. Paint keeps its colour at every angle: mostly dielectric, satin. A dye recolours the
// paint, never the bare steel under it)
uniform vec3 enamel : source_color = vec3(0.06, 0.12, 0.30);   // (its navy, sRGB; scaled by the key's own value as the oxide is)
uniform float enamel_metal = 0.3;                  // (a little metal under the paint: a faint cool sheen, never a mirror)
uniform float enamel_rough = 0.6;                  // (satin paint; a piece's metal_rough override moves it by the same step)
uniform float enamel_grime = 0.35;                 // (its grime, of bare metal's: paint wipes cleaner, and brown dirt over navy read as warm grey)
uniform float enamel_spec_cap = 0.03;             // (its lights' highlights capped at this times a white card (metal_spec_cap's 1.2 for bare metal): satin paint's broad lobe at metal's cap whitened a whole plate turned to the sun, the pale lilac pauldron)
uniform float enamel_gloss_cap = 0.6;              // (and where it is polished (roughness 0.38 or less, the cups' 0.22 override) this: one small soft highlight kept)
uniform float enamel_f90 = 0.3;                    // (its highlight's Fresnel at grazing: a satin microsurface shadows its own glare)
uniform float enamel_env = 0.6;                    // (the sky's reflection kept on the paint, of bare metal's: satin paint shows a soft sheen, not the sky)
uniform float enamel_chip = 0.8;                   // (how far it chips back to the steel)
uniform float enamel_chip_reach = 0.007;           // (and how far in from a rim the chipping reaches, m: blued's was 14 mm, most of a small lame)
// (body 16 r3: finish 3, dyed metal: what HerWear.DyeMesh sets on an enamel key for a metal dye (silver, gold, "#hex:metal").
// Fully metallic with no oxide, as a dyed blued key, but brushed: an edge-on pauldron at blued's gloss mirrored the bright
// sky, a pale glassy cap unlike the plate beside it)
uniform float dyed_rough_min = 0.42;               // (its plate's least roughness; the scuff mask still varies it above)
uniform float dyed_gloss_min = 0.30;               // (and a polished piece's (its override 0.38 or less, the cups): one soft highlight kept, no chrome sky/ground split)
uniform float dyed_env = 0.65;                     // (the sky's reflection kept, of bare metal's)
uniform float dyed_grime_metal = 0.1;              // (its grime's dielectric share, of bare metal's 0.85)
uniform float dyed_sheen = 0.75;                  // (its brushed plate's lights' highlights scaled by this: the sun's broad lobe over an edge-on pauldron at full read as a pale glassy cap)
uniform float dyed_ao = 0.35;                      // (and in what the sky can't reach (lame undersides, the shoulder crease) this of it)
uniform float metal_env = 0.50;                    // (the sky's reflection kept: no probe, the rest is the dark around her; metal r3: was 0.55)
uniform float metal_env_horizon = 0.8;             // (and less at the horizon, where trees, walls and the camp stand; metal r3: was 0.5)
uniform float metal_ground = 1.0;                  // (metal r3: the lit ground it reflects below the horizon, Atmosphere's ground_bounce; the sky's lower half is near black, so in shade plate read as rubber)
uniform float metal_env_graze = 0.3;               // (metal r3: at grazing angles at least this much of the sky kept, the sheen that tells plate in shade from rubber)
uniform vec4 piece_id = vec4(-1.0);                // (up to four pieces of this key with a finish of their own: their baked piece number, People.PieceNumber; -1 none.
uniform vec4 piece_rough = vec4(-1.0);             //  Each piece's metal_rough and metal_env_graze, -1 the key's own; art/people/metal_finishes.json "pieces".
uniform vec4 piece_graze = vec4(-1.0);             //  Metal r4: the greaves and sabatons smoother with more edge sheen, a tube's line of light, not a boot's)
uniform vec4 piece_blot = vec4(-1.0);              //  (and its patina's patches' strength in its colour and roughness, 1 the key's own: armor 12, the cuirass's cloudy blotches halved)
uniform vec4 piece_rim_rough = vec4(-1.0);         //  (armor 13 c4: its rolled edges' (COLOR.a flag 0) roughness, -1 as the plate; glossier rims read as steel, not leather)
uniform vec4 piece_rim_bright = vec4(-1.0);        //  (and their colour scaled by this, -1 none)
uniform vec4 piece_fine = vec4(-1.0);              //  (fine scratches: thin streaks a few mm long worn bright through it, this strong; -1 none. Instead of cloudy patches)
uniform vec4 piece_rim_steel = vec4(-1.0);         //  (armor 13 c5: its rolled edges worn to bare steel, this grey (linear F0), fading `rim_fade` m onto the plate; -1 none)
uniform vec4 piece_spec_mute = vec4(-1.0);         //  (armor 16 N4: its lights' highlights muted toward cool steel this much (0..1), keeping their brightness: the night key's warm light read as a salmon-pink core in the cups, OJ1; -1 none)
uniform vec3 spec_mute_tint = vec3(0.80, 0.86, 0.95);   // (a muted highlight's colour, of its brightness: blued steel's grey-blue)
uniform vec4 piece_form = vec4(-1.0);              //  (and its wear and grime by its shape (high points bright, recesses dark) this strong, its oxide lifted toward steel grey; -1 none)
uniform float rim_fade = 0.002;                    // (the bare band's fade past the rolled edge's inner side, 3 mm in from the cut)
uniform float rim_floor = 0.10;                    // (its own grey added as a dim emission, as gold's gold_floor, less in crevices)
uniform float rim_metal = 0.85;                    // (and its metalness: scratched bright steel scatters a little, so the edge holds a light line by night, where a mirror shows the dark it faces)
uniform float metal_spec_cap = 1.2;                // (a highlight never brighter than this times a white matte card facing that light)
uniform float metal_spec_knee = 0.4;               // (below this share of the cap, highlights as physical)
varying float v_metal;
varying float v_paint;                             // (finish 2's paint here, for light())
varying float v_spec_mute;                         // (armor 16 N4: piece_spec_mute here, for light())
global uniform vec4 ground_bounce;                   // (Atmosphere: the key's light off the ground, linear; metal reflects it below the horizon)
uniform int debug_view = 0;                        // (1 edge distance, 2 convexity, 3 sky seen: to check what was baked; 4 gold flat magenta, a mask for measuring it; 5 its shape alone; 6 the c5 bare rim's mask)

varying vec4 det;                                  // (edge distance m, convexity 0..1, sky seen, piece)
varying float painted;                             // (1 where stitches are painted; 0 where the piece is sewn with thread of its own)
varying float flag;                                // (COLOR.a: 0 a rolled binding, drawn matte if leather; 0.5 a plate brushed along its UVs' u; 1 neither)
varying vec3 opos;                                 // (the point in the piece's own space: metal is brushed by it, not by its UV islands)

// A sampled colour c recoloured to the dye, keeping its texture's variation: the dye scaled by c's luma over the
// material's mean colour m. Untouched (not even clamped) when dye_amount is 0.
vec3 dye_apply(vec3 c, vec3 m) {
	if (dye_amount <= 0.0) return c;
	float lc = dot(c, vec3(0.2126, 0.7152, 0.0722));
	float lm = dot(m, vec3(0.2126, 0.7152, 0.0722));
	return clamp(mix(c, dye * (lc / max(lm, 1e-3)), dye_amount), 0.0, 1.0);
}
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { return 0.5 * noise(p) + 0.3 * noise(p * 2.13 + 7.1) + 0.2 * noise(p * 4.37 + 3.3); }
// Brushed metal: hairline rows 0.4 mm apart (st.y, metres), each varying
// smoothly along the stroke (st.x) at its own phase, so no cell ends line up
// across rows (value noise on one grid read as rectangular blocks, judge 7);
// eased to its mean where a pixel spans more than a row or two, so it never
// shimmers at a distance.
float brushed(vec2 st) {
	float row = floor(st.y * 2500.0);
	float ph = hash(vec2(row, 3.7)) * 64.0;
	float v = 0.6 * noise(vec2(st.x * 55.0 + ph, row * 0.37)) + 0.4 * noise(vec2(st.x * 210.0 + ph * 1.7, row * 0.11 + 5.0));
	return mix(v, 0.5, smoothstep(0.0003, 0.0009, fwidth(st.y)));
}

// (the satin's wrinkles' height, metres, at angle a round the arm and d metres up from the wrist; L the forearm's length)
float satin_h(float a, float d, float L) {
	// ruching: soft uneven rings bunched just above the wrist
	float e1 = smoothstep(-0.006, 0.004, d) * (1.0 - smoothstep(0.03, 0.07, d));
	float p1 = d * 6.2832 / 0.0105 + 0.9 * sin(2.0 * a + 1.3) + 0.5 * sin(3.0 * a - d * 60.0);
	float r1 = 0.5 + 0.5 * sin(p1);
	float h = 0.0007 * e1 * r1 * r1 * (0.55 + 0.45 * sin(a + d * 110.0 + 0.4));
	// creases inside the elbow: three narrow grooves, unevenly spaced, each bowed down round the front and
	// fading out to the sides at its own reach
	float bow = 0.006 * (1.0 - cos(a));
	h -= 0.0009 * exp(-pow((d - (L - 0.012) + bow) / 0.0022, 2.0)) * pow(0.5 + 0.5 * cos(a - 0.2), 3.0);
	h -= 0.0007 * exp(-pow((d - (L - 0.027) + bow * 1.3) / 0.0026, 2.0)) * pow(0.5 + 0.5 * cos(a + 0.35), 5.0);
	h -= 0.0005 * exp(-pow((d - (L - 0.046) + bow * 0.8) / 0.003, 2.0)) * pow(0.5 + 0.5 * cos(a - 0.5), 8.0);
	// two long diagonal folds winding a quarter turn down the forearm, soft ridges
	float e3 = smoothstep(0.025, 0.07, d) * (1.0 - smoothstep(L - 0.07, L - 0.03, d));
	float r3 = 0.5 + 0.5 * sin(2.0 * a + d * 14.0 + 0.7);
	h += 0.0045 * e3 * r3 * r3 * r3 * (0.6 + 0.4 * sin(a + d * 9.0 + 2.0));
	return h;
}

void vertex() {
	det = vec4(UV2.x, UV2.y, COLOR.r, COLOR.g);
	painted = COLOR.b;
	flag = COLOR.a;
	opos = VERTEX;
	// (moved toward the camera in its own space, not by writing POSITION:
	// written, Godot uses it for every vertex, and its motion vectors differ)
	if (view_pull > 0.0) {
		vec3 cam = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
		VERTEX += normalize(cam - VERTEX) * view_pull;
	}
}

// (a piece's baked number as the shader sees it: the vertex colour comes in as 8 bits, truncated, not rounded
// (c5: the cuirass's 0.227 arrived as 57/255, 0.0035 off, and none of its own finish matched))
bool piece_is(float p, float id) { return id >= 0.0 && (abs(p - id) < 0.0025 || abs(p - floor(id * 255.0) / 255.0) < 0.0015); }

vec3 blend_normals(vec3 a, vec3 b, float k) {      // (two normal-map texels, the second laid over the first; encoded as maps are)
	vec3 n1 = a * 2.0 - 1.0, n2 = b * 2.0 - 1.0;
	return normalize(vec3(n1.xy + n2.xy * k, n1.z)) * 0.5 + 0.5;
}

void fragment() {
	// Under MSAA the samples of a pixel on a piece's silhouette are shaded with
	// its values carried on past the triangle's edge: there the normal can come
	// out as no direction at all (no number once normalised), the tangents too,
	// and the baked edge, sky and piece values out of their range. Unrepaired,
	// such a sample's light went to no number and the pixel it was resolved into
	// sparkled blue on her steel and trims as she moved.
	if (!(dot(NORMAL, NORMAL) > 0.25)) NORMAL = VIEW;
	// (and a normal carried round to face away from the eye, which no seen point
	// of a closed piece has, laid back to the silhouette's own)
	NORMAL = normalize(NORMAL - min(dot(NORMAL, VIEW), 0.0) * 1.01 * VIEW);
	if (!(dot(TANGENT, TANGENT) > 0.25) || !(dot(BINORMAL, BINORMAL) > 0.25)) {
		vec3 up = abs(NORMAL.y) < 0.99 ? vec3(0.0, 1.0, 0.0) : vec3(1.0, 0.0, 0.0);
		TANGENT = normalize(cross(up, NORMAL));
		BINORMAL = cross(NORMAL, TANGENT);
	}
	vec2 m = UV / repeats;                          // (metres)
	vec3 col = texture(albedo, UV).rgb * tint;
	if (dye_amount > 0.0) col = dye_apply(col, textureLod(albedo, vec2(0.5), 20.0).rgb * tint);
	vec3 nrm = texture(normal_map, UV).rgb;
	float rough = has_orm ? texture(orm, UV).g : roughness_value;
	float cc = 0.0;
	float metal = has_orm ? mix(metallic_value, texture(orm, UV).b, step(0.5, metallic_value) * (1.0 - step(0.95, metallic_value))) : metallic_value;   // (touch-up 3: a fully metallic key ignores its scan's metal map, whose specks dropped to non-metal as white flecks on the steel; grime and pits come from the shared detail and the baked masks. Rust keeps its map)
	float edge = max(det.x, 0.0), conv = clamp(det.y, 0.0, 1.0), sky = clamp(det.z, 0.0, 1.0), piece = clamp(det.w, 0.0, 1.0);
	float near_edge = 1.0 - smoothstep(0.0, 0.003, edge);
	vec3 gold_emit = vec3(0.0);
	vec3 look_emit = vec3(0.0);                     // (the Look's softbox in her plate, armor 16)
	vec3 dbg6 = vec3(0.0);
	float dbg_paint = -1.0;                         // (debug_view 14: finish 2's paint, green; its bare steel red)
	float gold = 0.0;                               // (1 on a gold metal, from its own mean colour below)
	float bulge = smoothstep(0.55, 0.85, conv);
	float hollow = smoothstep(0.45, 0.2, conv);
	// Each piece a shade of its own, and broad unevenness across it.
	float macro = fbm(m * 9.0 + piece * 31.0);
	col *= 0.92 + 0.16 * macro + (piece - 0.5) * 0.06;
	if (kind == 0) {
		// Leather: the grain fine (the texture again at five times), the edge
		// dyed dark and burnished, worn where it stands out, dark in creases.
		nrm = blend_normals(nrm, texture(normal_map, UV * 5.13 + 0.37).rgb, grain);
		col *= mix(1.0, 0.62, near_edge);
		col = mix(col, col * 1.18 + 0.02, bulge * 0.5);
		col *= mix(1.0, 0.8, hollow);
		// (satin, not gloss: leather is never shinier than this but at its burnished edges;
		// burnished to 0.28, a rolled binding seen edge-on caught the sky as a pale
		// line along its top that read as a gap, judge 5)
		rough = clamp(rough * 0.9 - 0.08 * bulge - 0.1 * near_edge + 0.1 * hollow, mix(0.42, 0.36, near_edge), 0.95);
		rough = max(rough, leather_rough_floor * (1.0 - near_edge));
		rough = mix(max(leather_rough_floor, 0.42) * (1.0 - near_edge) + rough * near_edge, rough, leather_rough_var);
		cc = leather_clearcoat * (1.0 - near_edge);
		// Stitches: dashes along the edge, `stitch_in` in, square to the
		// edge's way (its direction from how the distance changes on screen).
		vec2 g = vec2(dFdx(edge), dFdy(edge));
		vec2 gm = vec2(dFdx(m.x), dFdy(m.x));
		vec2 gn = vec2(dFdx(m.y), dFdy(m.y));
		// (the edge's way in the texture's own metres, from screen derivatives)
		mat2 J = mat2(vec2(gm.x, gn.x), vec2(gm.y, gn.y));
		float det_j = J[0][0] * J[1][1] - J[0][1] * J[1][0];
		vec2 grad_m = abs(det_j) > 1e-12 ? inverse(J) * g : vec2(1.0, 0.0);
		vec2 along = normalize(vec2(-grad_m.y, grad_m.x) + 1e-6);
		float row = 1.0 - smoothstep(0.00045, 0.0008, abs(edge - stitch_in));
		float dash = smoothstep(0.15, 0.25, fract(dot(m, along) / stitch_len)) * (1.0 - smoothstep(0.7, 0.8, fract(dot(m, along) / stitch_len)));
		float st = row * dash * painted;
		col = mix(col, thread * (0.85 + 0.15 * macro), st);
		rough = mix(rough, 0.7, st);
		// (a rolled binding matte: satin, its top caught the backlight edge-on as a
		// pale line along the Ranger's neckline that read as a gap, judges 5 and 6)
		if (flag < 0.25) rough = max(rough, 0.8);
		metal = 0.0;
	} else if (kind == 1) {
		// Metal, one standard for every outfit (touch-up, 18 Oct: the owner's
		// "plastic armor"; it read as chrome or candy plastic with blown hot spots):
		// worn, forged metal. Never a mirror: a satin roughness that varies over the
		// piece; polished brighter and smoother only on its edges and on what stands
		// out (worn there); grime, dull and darker, in its recesses and where pieces
		// meet; gold as aged brass. Every field is in the piece's own space or its
		// baked data, so it holds still under TAA; no extra passes.
		// (the scan's colour flattened to its mean: a formed plate reads as one
		// smooth surface; its stains and patches, even faint, read as lumps)
		vec3 mean_col = textureLod(albedo, vec2(0.5), 20.0).rgb * tint;   // (its smallest mip, one texel: the true mean)
		col = dye_apply(mean_col, mean_col);
		// (gold and claspgold: mean linear red 0.95, blue 0.15 of it; every other metal's red is under 0.41)
		gold = smoothstep(0.6, 0.75, mean_col.r) * (1.0 - smoothstep(0.3, 0.45, mean_col.b / max(mean_col.r, 1e-4)));
		gold_emit = dye_apply(mean_col, mean_col) * gold * gold_floor;
		float rusty = 1.0 - step(0.95, metallic_value);   // (rust: the only metal not built fully metallic)
		vec2 e = vec2(0.003, 0.0);
		float h0 = fbm(m * 40.0), hx = fbm((m + e.xy) * 40.0), hy = fbm((m + e.yx) * 40.0);
		// (and the planishing: hammer marks about 8 mm across, faint, so the reflections break up as forged plate's do)
		vec2 e2 = vec2(0.001, 0.0);
		float k0 = noise(m * 125.0), kx = noise((m + e2.xy) * 125.0), ky = noise((m + e2.yx) * 125.0);
		vec2 slope = vec2(h0 - hx, h0 - hy) * metal_dent + vec2(k0 - kx, k0 - ky) * metal_hammer;
		// The shared detail: scratches and pits at true size (2.5 a metre), the same on every metal.
		vec4 dtl = has_detail ? texture(metal_detail, m * detail_repeats) : vec4(0.5, 0.5, 0.5, 1.0);
		nrm = normalize(vec3(slope + (dtl.rg - 0.5) * 2.0 * detail_normal, 1.0)) * 0.5 + 0.5;
		// Wear and grime fields, in the piece's own space (never screen space), from its baked
		// edge distance, convexity and sky seen: a new piece that carries them wears for free.
		vec2 op = vec2(opos.x + 0.6 * opos.z, opos.y - 0.4 * opos.z);
		float blot = fbm(op * 22.0 + piece * 13.0);                 // (hand-worn and wiped patches, a few cm)
		float fleck = fbm(op * 140.0 + 5.0);                         // (fine wear, mm)
		float polish = max(near_edge, bulge);
		// (the rim worn bright all along, broken up; the high points of a dome only scuffed, in patches)
		float wear = clamp(near_edge * smoothstep(0.2, 0.55, fleck + 0.25) + bulge * smoothstep(0.62, 0.8, fleck) * 0.7, 0.0, 1.0);
		// grime: in the hollows, out of the sky's reach, and where pieces meet, patchy; and in the detail's pits
		float grime = clamp((0.7 * hollow + 0.8 * (1.0 - sky)) * smoothstep(0.25, 0.75, blot + 0.15) + 0.45 * smoothstep(0.002, 0.005, edge) * (1.0 - smoothstep(0.008, 0.02, edge)) * smoothstep(0.3, 0.7, blot), 0.0, 1.0) * metal_grime;   // (and a band of dirt just inside the rim, along the rivets)
		grime = max(grime, (1.0 - dtl.a) * detail_cavity * (1.0 - wear) * 1.3);
		float brush = brushed(vec2(opos.x + opos.z, opos.y));   // (fine level streaks, one way over the whole piece)
		if (flag > 0.25 && flag < 0.75) brush = brushed(m);     // (a plate laid out round her arm brushed along it, by its UVs, judge 6)
		// Roughness: satin, varied; smoother where worn, rougher where dirty; scratched (more where worn).
		float p_rough = metal_rough;
		float p_blot = 1.0;
		for (int i = 0; i < 4; i++) if (piece_is(piece, piece_id[i]) && piece_rough[i] >= 0.0) p_rough = piece_rough[i];
		for (int i = 0; i < 4; i++) if (piece_is(piece, piece_id[i]) && piece_blot[i] >= 0.0) p_blot = piece_blot[i];
		float p_rimr = -1.0, p_rimb = 1.0, p_fine = 0.0, p_steel = -1.0, p_form = 0.0;
		for (int i = 0; i < 4; i++) if (piece_is(piece, piece_id[i])) {
			if (piece_rim_steel[i] >= 0.0) p_steel = piece_rim_steel[i];
			if (piece_form[i] >= 0.0) p_form = piece_form[i];
			if (piece_rim_rough[i] >= 0.0) p_rimr = piece_rim_rough[i];
			if (piece_rim_bright[i] >= 0.0) p_rimb = piece_rim_bright[i];
			if (piece_fine[i] >= 0.0) p_fine = piece_fine[i];
		}
		float p_mute = 0.0;
		for (int i = 0; i < 4; i++) if (piece_is(piece, piece_id[i]) && piece_spec_mute[i] >= 0.0) p_mute = piece_spec_mute[i];
		float rimm = flag < 0.25 ? 1.0 : 0.0;                       // (a rolled edge)
		// (armor 13 c5: a rolled edge worn to bare steel all along, its band fading onto the plate past the
		// roll's inner side, 3 mm in from the cut, broken a little by the fine wear; 0 on every other piece)
		float bare = 0.0;
		if (p_steel >= 0.0) bare = max(rimm, (1.0 - rimm) * (1.0 - smoothstep(0.003, 0.003 + rim_fade, edge + 0.0015 * (fleck - 0.5))));
		float fw_ = max(fwidth(op.x), fwidth(op.y));               // (outside the branch: derivatives in uniform control flow)
		if (p_fine > 0.0) {
			// Fine scratches: two crossing sets of thin streaks (about 0.6 mm by 12 mm), their heading wandering over
			// the piece; worn bright through the patina. Below about 1 mm a pixel they fade to their mean, never shimmer.
			float a = fbm(op * 6.0 + piece * 3.0) * 3.1416;
			vec2 q = mat2(vec2(cos(a), sin(a)), vec2(-sin(a), cos(a))) * op;
			vec2 q2 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * q;
			float s1 = smoothstep(0.80, 0.93, noise(vec2(q.x * 1600.0, q.y * 80.0)));
			float s2 = smoothstep(0.82, 0.94, noise(vec2(q2.x * 1400.0, q2.y * 60.0) + 11.0));
			float lod = 1.0 - smoothstep(0.0005, 0.0014, fw_);
			float fs = p_fine * mix(0.06, clamp(s1 + s2, 0.0, 1.0), lod) * (1.0 - 0.5 * rimm);
			wear = max(wear, fs);
		}
		if (p_form > 0.0) {
			// (its wear and dirt by its shape, not even clouds: high points rubbed brighter, recesses and the
			// skin-side shadowed (the baked sky seen) darker and duller)
			wear = max(wear, p_form * bulge * smoothstep(0.45, 0.75, fleck + 0.2 * blot) * 0.6);
			grime = max(grime, p_form * 0.5 * clamp(hollow * 0.8 + (1.0 - sky) * 0.6, 0.0, 1.0) * (1.0 - rimm));
		}
		float blot_c = 0.5 + (blot - 0.5) * p_blot;                 // (the patina's patches in its colour and roughness; grime's own patchiness keeps blot)
		rough = p_rough + 0.10 * (blot_c - 0.5) + 0.05 * (brush - 0.5);
		rough = mix(rough, metal_rough_wear, wear);
		rough = mix(rough, 0.72, grime);
		rough += (dtl.b - 0.5) * detail_rough * (0.7 + 0.6 * wear);
		// Colour: aged brass for gold (darker, less saturated, browner), the rest as built.
		vec3 brass = gold_tone * brass_dim;
		col = mix(col, brass, gold * (1.0 - dye_amount));   // (a dyed gold takes the dye, not the brass)
		rough = mix(rough, rough + brass_rough_add, gold);
		col *= 0.9 + 0.2 * blot_c;                                // (an uneven patina)
		col *= mix(mix(1.0, steel_dim, 1.0 - gold) * mix(vec3(1.0), steel_warm, 1.0 - gold), vec3(metal_wear_bright), wear);                              // (bright bare metal on the worn edges)
		// (a dyed blued key drops its oxide: the dye is the metal's colour, worn back at its edges as any bare
		// metal; the oxide over it hid every metal dye, armor 9)
		if (finish == 1 && dye_amount <= 0.0) {
			// Blued steel: a deep blue-black oxide (darker on a darker key), a faint violet temper
			// in patches; chipped back to the bright steel under it along the worn rims and, in
			// scuffs, on what stands out (the edge and convexity masks, never painted).
			float temper = smoothstep(0.4, 0.75, fbm(op * 9.0 + piece * 5.0));
			vec3 oxide = mix(blued, blued_temper, temper * 0.6) * clamp(dot(mean_col, vec3(0.3, 0.59, 0.11)) / 0.42, 0.55, 1.0) * (0.9 + 0.2 * blot);
			// (its rim sits under the trim: the chipping reaches 14 mm in, broken up, worst at the very edge)
			float rim = 1.0 - smoothstep(0.003, 0.014, edge);
			float chip = clamp(max(smoothstep(0.35, 0.6, wear * (0.75 + 0.5 * fleck)), rim * smoothstep(0.62, 0.8, fleck + 0.25 * rim + 0.15 * blot)) * blued_chip, 0.0, 1.0);
			if (p_form > 0.0) oxide = mix(oxide, vec3(0.50, 0.52, 0.56) * dot(oxide, vec3(0.3, 0.59, 0.11)) / 0.44, 0.10 * p_form);   // (lifted toward steel grey, never bluer)
			col = mix(oxide, col, chip);
			rough = mix(rough + 0.03, rough, chip);
		}
		float paint = 0.0;
		if (finish == 2) {
			// Blue enamel (or the dye) over the steel, chipped back to it where worn and along the rims, as blued's chipping
			float rim = 1.0 - smoothstep(min(0.003, enamel_chip_reach * 0.5), enamel_chip_reach, edge);
			// (its chips by the rims, and only a few small scuffs on the high points: a small dome is all bulge, and
			// blued's scuffs there stripped most of a pauldron back to bright steel)
			float e_wear = clamp(near_edge * smoothstep(0.2, 0.55, fleck + 0.25) + bulge * smoothstep(0.8, 0.92, fleck) * 0.6, 0.0, 1.0);
			float chip = clamp(max(smoothstep(0.35, 0.6, e_wear * (0.75 + 0.5 * fleck)), rim * smoothstep(0.62, 0.8, fleck + 0.25 * rim + 0.15 * blot)) * enamel_chip, 0.0, 1.0);
			vec3 steel_c = mean_col * (0.9 + 0.2 * blot_c) * mix(1.0, metal_wear_bright, wear);
			vec3 coat = dye_amount > 0.0 ? dye_apply(mean_col, mean_col)
				: enamel * clamp(dot(mean_col, vec3(0.3, 0.59, 0.11)) / 0.42, 0.55, 1.0);
			coat *= 0.95 + 0.1 * blot_c;
			paint = (1.0 - chip) * (1.0 - gold);
			col = mix(col, mix(steel_c, coat, 1.0 - chip), 1.0 - gold);
			float r_paint = enamel_rough + (p_rough - metal_rough) + 0.06 * (blot_c - 0.5) + (dtl.b - 0.5) * detail_rough * 0.5;
			rough = mix(rough, r_paint, paint);
			dbg_paint = paint;
		}
		// grime is dirt, not metal: dark, brown, dielectric
		vec3 dirt = vec3(0.045, 0.036, 0.027);
		if (rusty > 0.5) {
			// rust: its scan kept (half), rough and mostly dull, its edges worn back to dark iron
			col = mix(dye_apply(mean_col, mean_col), dye_apply(texture(albedo, UV).rgb * tint, mean_col), 0.5) * (0.9 + 0.2 * blot);
			rough = max(rough + 0.2, 0.62) - 0.15 * wear;
		}
		grime *= mix(1.0, enamel_grime, paint);
		col = mix(col, dirt, grime * 0.8);
		metal = mix(1.0, 0.0, grime * 0.85);
		metal *= mix(1.0, enamel_metal, paint);              // (paint: mostly dielectric, its colour held at every angle)
		if (finish == 3) metal = mix(metal, 1.0 - grime * dyed_grime_metal, 1.0 - gold);   // (dyed metal: its dirt stays a dull film on the metal; at bare metal's 0.85 a pale dye's grime, lit as paint, read as a chalky glassy cap)
		if (rusty > 0.5) metal = mix(0.35, 0.9, wear) * (1.0 - grime * 0.85);
		// (the pauldron's plates and the bracers satin, the set matching: at the Look they
		// blew out 5.7% of the lower frame at 0.32, face lead; judge 7)
		if (flag > 0.25 && flag < 0.75) rough += 0.04;
		rough = clamp(rough, metal_rough_floor, 0.85);
		if (finish == 3) rough = mix(rough, max(rough, p_rough <= 0.38 ? dyed_gloss_min : dyed_rough_min), 1.0 - gold);   // (dyed metal: brushed, never a sky mirror)
		// (gold only, a trial knob: glossier by gold_gloss)
		rough = mix(rough, max(gold_rough - 0.04 * polish, 0.08), gold * gold_gloss);
		// (armor 13 c4: a piece's rolled edges glossier and brighter than its plate, so its outline catches the light)
		if (p_rimr >= 0.0) rough = mix(rough, p_rimr, rimm * (1.0 - grime));
		col *= mix(1.0, p_rimb, rimm);
		if (bare > 0.0) {
			// (bare steel: neutral grey at its own F0, the oxide and its blue gone, smooth, never grimed)
			col = mix(col, vec3(p_steel) * (0.94 + 0.08 * fleck), bare);
			rough = mix(rough, p_rimr >= 0.0 ? p_rimr : 0.2, bare);
			grime *= 1.0 - bare;
			metal = mix(metal, rim_metal, bare);
			gold_emit += vec3(p_steel) * bare * rim_floor;          // (as gold's floor: the edge never goes black at night)
		}
		if (debug_view == 6) dbg6 = p_steel >= 0.0 ? (rimm > 0.5 ? vec3(1.0, 0.0, 1.0) : vec3(bare, 1.0, 0.0)) * 0.25 : vec3(0.0);   // (a mask: the piece's rolled edge magenta, its plate green, the band's fade yellow)
#ifdef OUTFIT_METAL_LIGHT
		// Its reflection held to what it can see: no probe, so the sky's (a bright dome lit to
		// light the scene) is kept only in part, least at the horizon (trees, walls, the camp)
		// and in what the sky can't reach (specular occlusion from the baked sky seen).
		vec3 rw = (INV_VIEW_MATRIX * vec4(reflect(-VIEW, NORMAL), 0.0)).xyz;
		float sky_k = mix(sky, max(sky, 0.85), bare);                // (a bare rolled edge stands proud: it sees the sky the baked value, eased over the plate, undercounts)
		float keep = metal_env * mix(metal_env_horizon, 1.0, smoothstep(0.05, 0.6, abs(rw.y))) * mix(0.3, 1.0, sky_k);
		float graze = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		float p_graze = metal_env_graze;
		for (int i = 0; i < 4; i++) if (piece_is(piece, piece_id[i]) && piece_graze[i] >= 0.0) p_graze = piece_graze[i];
		keep = max(keep, p_graze * graze * graze * mix(0.4, 1.0, sky) * (1.0 - grime));   // (the sheen at grazing angles: never in its grime or deep hollows)
		keep *= mix(1.0, enamel_env, paint);
		if (finish == 3) keep *= mix(1.0, dyed_env * mix(dyed_ao, 1.0, smoothstep(0.2, 0.8, sky)), (1.0 - gold) * (1.0 - bare));
		// Below the horizon it sees the ground, lit by the key (the sky's lower half is near black):
		// that light added as its own radiance (mix(env, rgb, a): rgb * a is what is added).
		float down = smoothstep(0.0, 0.35, -rw.y);
		vec3 ground = ground_bounce.rgb * metal_ground * down * mix(0.45, 1.0, sky) * (1.0 - grime);
		if (look_metal_env > 0.0 && look_rig > 0.0) {
			// (as emission: the Look's world gives no reflection to add it to)
			vec3 rv = reflect(-VIEW, NORMAL);
			vec3 kz = normalize(look_key_dir);
			vec3 kx = normalize(cross(vec3(0.0, 1.0, 0.0), kz)), ky = cross(kz, kx);
			float rz = dot(rv, kz);
			vec2 bt = vec2(dot(rv, kx), dot(rv, ky)) / max(rz, 0.05);
			float soft = mix(look_box_soft, 1.0, smoothstep(0.15, 0.7, rough));   // (its edge's share of the box: rougher, softer)
			vec2 bh = vec2(look_box_w, look_box_h) * (1.0 + 0.6 * smoothstep(0.15, 0.7, rough));
			vec2 q = abs(bt) / bh;
			float lobe = step(0.0, rz) * (1.0 - smoothstep(1.0 - soft, 1.0, q.x)) * (1.0 - smoothstep(1.0 - soft, 1.0, q.y));
			lobe *= mix(1.0, look_gold_key, gold);
			float dome = smoothstep(-0.2, 0.9, rw.y);
			float fr = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
			vec3 f0 = mix(vec3(0.04), clamp(col, 0.0, 1.0), metal);
			vec3 fres = f0 + (1.0 - f0) * pow(fr, 5.0);
			look_emit = fres * (look_box_tint * lobe * look_metal_key + vec3(0.62, 0.68, 0.8) * dome * look_metal_dome)
				* look_metal_env * look_rig * mix(0.3, 1.0, sky);
		}
		RADIANCE = vec4(ground / max(1.0 - keep, 1e-3), 1.0 - keep);
		v_metal = metal;
		v_paint = paint;
		v_spec_mute = max(p_mute, look_metal_mute * look_rig * (1.0 - gold)) * (1.0 - bare);
#else
		col *= mix(0.75, 1.0, sky);
#endif
	} else if (kind == 2 || kind == 4) {
		// Cloth: its weave fine, rough, a sheen seen across it.
		nrm = blend_normals(nrm, texture(normal_map, UV * 3.7).rgb, 0.8);
		if (kind == 4) {
			// Twill (a pant leg, breeches): diagonal ribs 2.8 mm apart and the
			// thread across them, so it reads as woven cloth, never as skin.
			// Each fades out before it is too fine for the pixels to hold.
			float fw = max(fwidth(m.x), fwidth(m.y));
			float k1 = 6.2832 / 0.0028, k2 = 6.2832 / 0.0008;
			float a1 = 1.0 - smoothstep(0.0006, 0.0013, fw), a2 = 1.0 - smoothstep(0.00018, 0.00035, fw);
			float c1 = cos(k1 * (m.x + m.y)), c2 = cos(k2 * (m.x - m.y));
			vec2 g = vec2(0.5 * k1 * c1 * a1 + 0.15 * k2 * c2 * a2, 0.5 * k1 * c1 * a1 - 0.15 * k2 * c2 * a2) * 0.00012;
			nrm = blend_normals(nrm, normalize(vec3(-g, 1.0)) * 0.5 + 0.5, 1.0);
			col *= 1.0 + 0.08 * a1 * sin(k1 * (m.x + m.y));
		}
		rough = clamp(rough * 0.3 + 0.7, 0.6, 1.0);
		metal = 0.0;
		RIM = 0.35;
		RIM_TINT = 0.6;
	} else if (kind == 5) {
		// Satin (her gloves, s22): a stretch satin, never latex. Its own roughness (the
		// material's, about 0.45: the linen's roughness map is flat white), a broad soft
		// highlight, a sheen at the grazing edges, the knit barely there.
		nrm = blend_normals(vec3(0.5, 0.5, 1.0), nrm, 0.3);
		// (s24 glove styles S1: a satin at 0.25 floors at 0.22, its streak kept; B1's 0.30 keeps 0.30)
		rough = clamp(roughness_value + 0.08 * (macro - 0.5) + 0.1 * (1.0 - sky), roughness_value < 0.295 ? 0.22 : 0.3, 0.75);
		metal = 0.0;
		// (s27, judge gl r2: a satin sheen at the grazing edges that reads in play; 0.3 left the forearm flat cream.
		// Not anisotropy: Godot's anisotropic path, even at 0, cost every other outfit material its fine grain)
		RIM = 0.4;
		RIM_TINT = 0.5;
		if (satin_wrinkle > 0.0) {
			// its wrinkles as a bump on the surface's own normal (Mikkelsen's surface gradient, by the chain rule
			// through its smooth coordinates, so no 2x2 blocks)
			vec2 cs = UV2 / max(length(UV2), 1e-4);
			float a = atan(cs.y, cs.x);
			float d = (UV.y - satin_wrist_v) / satin_uv_per_m, L = (satin_top_v - satin_wrist_v) / satin_uv_per_m;
			float h0 = satin_h(a, d, L);
			float ha = (satin_h(a + 0.01, d, L) - h0) / 0.01, hd = (satin_h(a, d + 0.0005, L) - h0) / 0.0005;
			float dax = cs.x * dFdx(cs.y) - cs.y * dFdx(cs.x), day = cs.x * dFdy(cs.y) - cs.y * dFdy(cs.x);
			float ddx = dFdx(UV.y) / satin_uv_per_m, ddy = dFdy(UV.y) / satin_uv_per_m;
			float hx = (ha * dax + hd * ddx) * satin_wrinkle, hy = (ha * day + hd * ddy) * satin_wrinkle;
			vec3 px = dFdx(VERTEX), py = dFdy(VERTEX);
			vec3 r1 = cross(py, NORMAL), r2 = cross(NORMAL, px);
			float dt = dot(px, r1);
			if (abs(dt) > 1e-12) NORMAL = normalize(NORMAL - (r1 * hx + r2 * hy) / dt);
		}
		if (satin_sheen > 0.0) {
			float nv = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
			col *= satin_body * mix(satin_turn, 1.0, smoothstep(0.05, 0.85, nv));
#ifdef OUTFIT_SATIN_LIGHT
			// The form's long way, its sheen's streak along it (light(), below): its UVs' v (satin_axis 2), which on her
			// gloves runs down the arm, or u (1)
			v_axis = normalize(satin_axis == 1 ? TANGENT : BINORMAL);
			v_aniso = 1.0;
#endif
		}
	} else {
		// Gloss: clean and smooth, barely a grain.
		nrm = blend_normals(vec3(0.5, 0.5, 1.0), nrm, 0.12);
		rough = clamp(0.16 + 0.1 * macro + 0.1 * (1.0 - sky), 0.1, 0.4);
		metal = 0.0;
	}
	if (kind == 1) rough = mix(rough, max(rough, look_metal_rough), look_rig * (1.0 - gold));
	// (armor 17 N5, OJ2: at the Look the gold trim read as a flat yellow cel outline: there it is polished gold at
	// look_gold_rough, its flat floor glow mostly gone, and darker where it sits in the plate's shadow (its baked sky))
	if (kind == 1) rough = mix(rough, look_gold_rough, look_rig * gold);
	if (kind == 1) col *= mix(1.0, mix(0.55, 1.0, sky), look_rig * gold);
	if (kind == 1) gold_emit *= 1.0 - look_gold_floor_cut * look_rig * gold;
	if (kind == 1) col *= mix(1.0, look_metal_dim, look_rig * (1.0 - gold));
	if (kind == 0) rough = mix(rough, max(rough, look_leather_rough), look_rig);
#ifdef OUTFIT_METAL_LIGHT
	ALBEDO = clamp(col, 0.0, 1.0);                  // (metal: its reflectance physical; the occlusion is in its reflection and its grime)
#else
	ALBEDO = clamp(col * mix(0.55, 1.0, sky), 0.0, 1.0);
#endif
	NORMAL_MAP = nrm;
	ROUGHNESS = rough;
	CLEARCOAT = cc;
	CLEARCOAT_ROUGHNESS = leather_clearcoat_rough;
	METALLIC = metal;
	AO = sky;
	EMISSION = gold_emit * mix(0.4, 1.0, sky) + look_emit;
	AO_LIGHT_AFFECT = 0.3;
	if (debug_view == 1) { ALBEDO = vec3(1.0 - smoothstep(0.0, 0.01, edge), fract(edge / 0.004), 0.0); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 2) { ALBEDO = vec3(conv); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 4) { ALBEDO = vec3(0.0); EMISSION = vec3(gold, 0.0, gold) * 4.0; ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 5) { ALBEDO = vec3(0.30, 0.30, 0.36); ROUGHNESS = 0.4; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }   // (its shape alone: flat colour, no normal map, no mottle)
	if (debug_view == 6) { ALBEDO = vec3(0.0); EMISSION = dbg6 * 4.0; ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 3) { ALBEDO = vec3(sky); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 7) { NORMAL_MAP = vec3(0.5, 0.5, 1.0); }   // (armor 14: its normal map alone off)
	if (debug_view == 8) { ALBEDO = vec3(0.10, 0.09, 0.16); }   // (armor 14: its albedo alone flat)
	if (debug_view == 10) { ALBEDO = clamp(col, 0.0, 1.0); }   // (armor 14: no sky occlusion)
	if (debug_view == 11) { ALBEDO = clamp(texture(albedo, UV).rgb * tint * mix(0.55, 1.0, sky), 0.0, 1.0); }   // (armor 14: the texture and sky only, no mottle/wear)
	if (debug_view == 9) { ROUGHNESS = 0.55; }
	if (debug_view == 14) { ALBEDO = vec3(0.0); ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; EMISSION = dbg_paint < 0.0 ? vec3(0.0) : vec3(1.0 - dbg_paint, dbg_paint, 0.0) * 0.6; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 12) { ALBEDO = vec3(0.0); ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; EMISSION = (NORMAL * 0.5 + 0.5) * 0.6; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }   // (armor 17 N5: its interpolated vertex normal, view space, as colour)
	if (debug_view == 13) { ALBEDO = vec3(0.0); ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; EMISSION = vec3(fract(UV * 8.0), 0.0) * 0.6; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }   // (and its UV, as colour)
	if (test_flat) { ALBEDO = vec3(0.0); METALLIC = 0.0; ROUGHNESS = 1.0; SPECULAR = 0.0; RIM = 0.0; EMISSION = vec3(0.5); }
}

#ifdef OUTFIT_METAL_LIGHT
// Metal's light: Godot's own (Burley diffuse for its dull share, GGX specular with Schlick
// Fresnel), with a highlight shoulder: past metal_spec_knee of the cap a highlight eases toward,
// never past, metal_spec_cap times what a white matte card facing that light would show. Its
// luminance only, so it keeps the light's hue (the fire orange, the moon cool). Without it a
// satin dome by a fire blew out (C01 s10/s11).
void light() {
	float cNdotL = max(dot(NORMAL, LIGHT), 0.0);
	float cNdotV = max(dot(NORMAL, VIEW), 1e-4);
	vec3 H = normalize(VIEW + LIGHT);
	float cNdotH = clamp(dot(NORMAL, H), 0.0, 1.0);
	float cLdotH = clamp(dot(LIGHT, H), 0.0, 1.0);
	float r = ROUGHNESS;
	float fd90 = 2.0 * cLdotH * cLdotH * r - 0.5;
	float fdv = 1.0 + fd90 * pow(1.0 - cNdotV, 5.0);
	float fdl = 1.0 + fd90 * pow(1.0 - cNdotL, 5.0);
	DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * (1.0 / PI) * fdv * fdl * cNdotL;
	float a = r * r;
	float ah = cNdotH * a;
	float kd = a / (1.0 - cNdotH * cNdotH + ah * ah);
	float D = kd * kd * (1.0 / PI);
	float G = 0.5 / mix(2.0 * cNdotL * cNdotV, cNdotL + cNdotV, a);
	vec3 f0 = mix(vec3(0.04), ALBEDO, v_metal);
	float f90 = mix(clamp(50.0 * f0.g, 0.0, 1.0), enamel_f90, v_paint);
	vec3 F = f0 + (f90 - f0) * pow(1.0 - cLdotH, 5.0);
	vec3 s = cNdotL * D * G * F * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT;
	vec3 lw = vec3(0.2126, 0.7152, 0.0722);
	float cap = mix(metal_spec_cap, mix(enamel_gloss_cap, enamel_spec_cap, smoothstep(0.38, 0.52, r)), v_paint) * dot(LIGHT_COLOR, lw) * ATTENUATION * SPECULAR_AMOUNT * (1.0 / PI);
	float knee = metal_spec_knee * cap;
	float sl = dot(s, lw);
	if (sl > knee && cap > 1e-6) {
		float over = cap - knee;
		s *= (knee + over * (1.0 - exp(-(sl - knee) / over))) / sl;
	}
	// (armor 16 N4: a muted piece's highlight takes the steel's grey-blue, not the lamp's hue: blued steel under a warm key)
	s = mix(s, vec3(dot(s, lw)) * spec_mute_tint, v_spec_mute);
	if (finish == 3) s *= mix(1.0, dyed_sheen, smoothstep(0.36, 0.5, r));   // (dyed metal's brushed plate: the sun's broad lobe muted (an edge-on pauldron at full read as a pale glassy cap); the polished cups keep theirs)
	SPECULAR_LIGHT += s;
}
#endif

#ifdef OUTFIT_SATIN_LIGHT
// A stretch satin's light (armor 16, the arcanist's opera gloves): a soft diffuse, a faint broad gloss,
// and its sheen, an anisotropic GGX whose highlight runs along the form (v_axis) as a long soft streak,
// eased toward a cap so a near lamp never blows it to white.
void light() {
	float cNdotL = max(dot(NORMAL, LIGHT), 0.0);
	float cNdotV = max(dot(NORMAL, VIEW), 1e-4);
	vec3 H = normalize(VIEW + LIGHT);
	float cNdotH = clamp(dot(NORMAL, H), 0.0, 1.0);
	float cLdotH = clamp(dot(LIGHT, H), 0.0, 1.0);
	float r = ROUGHNESS;
	float fd90 = 2.0 * cLdotH * cLdotH * r - 0.5;
	float fdv = 1.0 + fd90 * pow(1.0 - cNdotV, 5.0);
	float fdl = 1.0 + fd90 * pow(1.0 - cNdotL, 5.0);
	DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * (1.0 / PI) * fdv * fdl * cNdotL;
	// the sheen: anisotropic GGX (Burley's), rough along the axis, smooth across it
	vec3 T = normalize(v_axis - NORMAL * dot(v_axis, NORMAL) + 1e-6);
	vec3 B = cross(NORMAL, T);
	float at = mix(satin_across, satin_along, v_aniso), ab = satin_across;
	at = at * at; ab = ab * ab;
	float th = dot(T, H) / at, bh = dot(B, H) / ab;
	float den = th * th + bh * bh + cNdotH * cNdotH;
	float D = 1.0 / (PI * at * ab * den * den);
	float G = 0.5 / mix(2.0 * cNdotL * cNdotV, cNdotL + cNdotV, sqrt(at * ab));
	float F = 0.04 + 0.96 * pow(1.0 - cLdotH, 5.0);
	vec3 s = cNdotL * D * G * F * satin_sheen * 6.0 * mix(vec3(1.0), ALBEDO, 0.35) * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT;
	vec3 lw = vec3(0.2126, 0.7152, 0.0722);
	float cap = satin_spec_cap * dot(LIGHT_COLOR, lw) * ATTENUATION * SPECULAR_AMOUNT * (1.0 / PI);
	float knee = 0.6 * cap;
	float sl = dot(s, lw);
	if (sl > knee && cap > 1e-6) {
		float over = cap - knee;
		s *= (knee + over * (1.0 - exp(-(sl - knee) / over))) / sl;
	}
	SPECULAR_LIGHT += s;
}
#endif
