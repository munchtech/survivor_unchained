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
uniform float grain = 0.6;                         // how strongly the fine grain shows
uniform float view_pull = 0.0;                     // metres drawn toward the camera (a decal on her skin: the ink, never z-fighting it)
uniform bool test_flat = false;                  // (the legal motion check: every garment flat grey, coverage unchanged)
uniform float gold_gloss = 0.0;                   // (0 = as before; 1 = gold's roughness drawn to gold_rough: crisper, brighter highlights, tint and albedo untouched)
uniform float gold_rough = 0.2;
uniform float gold_floor = 0.08;                  // (gold's own colour added as a dim emission, less in crevices, so it never goes black at night; 0.08 by judge g4: warm gold at night, no change by day, 0.15 turned shadowed trim to flat tan)
// (the Look's portrait rig, by its campfire at night: polished steel read as blue enamel with clipped white highlights and
// leather as wet vinyl there, judge s29 wd; under the rig only (People.HerLookRig sets look_rig), a floor on their roughness)
uniform float look_rig = 0.0;
uniform float look_metal_rough = 0.30;
uniform float look_metal_dim = 0.70;               // (and its reflectance: F0 is its colour, so its highlights under the rig's key stay graded, not clipped)
uniform float look_leather_rough = 0.60;
// Metal's standard (touch-up, 18 Oct): worn, forged; never a mirror.
uniform float metal_rough = 0.45;                  // (its plate's satin roughness, varied about this over the piece: 0.35-0.55 with the detail)
uniform float metal_rough_wear = 0.26;             // (where worn bright: its edges and, in patches, what stands out; 0.2-0.3)
uniform float metal_rough_floor = 0.22;            // (no metal smoother than this; only worn edges get near it, the plates stay over 0.3)
uniform float metal_grime = 1.0;                   // (dirt in its recesses: dark, brown, dull, not metal)
uniform float metal_dent = 0.08;                   // (the hammered unevenness)
uniform float brass_dim = 0.85;                    // (gold read as aged brass: a little darker and greyer than the bright alloy; the rest from grime)
uniform float brass_rough_add = 0.0;
uniform float metal_hammer = 0.05;                 // (planishing marks, 8 mm)
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
uniform vec3 blued : source_color = vec3(0.31, 0.35, 0.47);        // (blued steel: its reflectance; deep blue-black where it reflects the dark)
uniform vec3 blued_temper : source_color = vec3(0.36, 0.34, 0.52); // (its temper sheen: a faint violet in patches)
uniform float blued_chip = 1.0;                    // (how far its worn edges chip back to bright steel)
uniform float metal_env = 0.55;                    // (the sky's reflection kept: no probe, the rest is the dark around her)
uniform float metal_env_horizon = 0.45;            // (and less at the horizon, where trees, walls and the camp stand)
uniform float metal_spec_cap = 1.1;                // (a highlight never brighter than this times a white matte card facing that light)
uniform float metal_spec_knee = 0.4;               // (below this share of the cap, highlights as physical)
varying float v_metal;
uniform int debug_view = 0;                        // (1 edge distance, 2 convexity, 3 sky seen: to check what was baked; 4 gold flat magenta, a mask for measuring it; 5 its shape alone)

varying vec4 det;                                  // (edge distance m, convexity 0..1, sky seen, piece)
varying float painted;                             // (1 where stitches are painted; 0 where the piece is sewn with thread of its own)
varying float flag;                                // (COLOR.a: 0 a rolled binding, drawn matte if leather; 0.5 a plate brushed along its UVs' u; 1 neither)
varying vec3 opos;                                 // (the point in the piece's own space: metal is brushed by it, not by its UV islands)

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
	vec3 nrm = texture(normal_map, UV).rgb;
	float rough = has_orm ? texture(orm, UV).g : roughness_value;
	float metal = has_orm ? mix(metallic_value, texture(orm, UV).b, step(0.5, metallic_value)) : metallic_value;
	float edge = max(det.x, 0.0), conv = clamp(det.y, 0.0, 1.0), sky = clamp(det.z, 0.0, 1.0), piece = clamp(det.w, 0.0, 1.0);
	float near_edge = 1.0 - smoothstep(0.0, 0.003, edge);
	vec3 gold_emit = vec3(0.0);
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
		col = mean_col;
		// (gold and claspgold: mean linear red 0.95, blue 0.15 of it; every other metal's red is under 0.41)
		gold = smoothstep(0.6, 0.75, mean_col.r) * (1.0 - smoothstep(0.3, 0.45, mean_col.b / max(mean_col.r, 1e-4)));
		gold_emit = mean_col * gold * gold_floor;
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
		rough = metal_rough + 0.10 * (blot - 0.5) + 0.05 * (brush - 0.5);
		rough = mix(rough, metal_rough_wear, wear);
		rough = mix(rough, 0.72, grime);
		rough += (dtl.b - 0.5) * detail_rough * (0.7 + 0.6 * wear);
		// Colour: aged brass for gold (darker, less saturated, browner), the rest as built.
		vec3 brass = mix(vec3(dot(mean_col, vec3(0.3, 0.55, 0.15))), mean_col, 0.8) * brass_dim;
		col = mix(col, brass, gold);
		rough = mix(rough, rough + brass_rough_add, gold);
		col *= 0.9 + 0.2 * blot;                                  // (an uneven patina)
		col *= mix(mix(1.0, steel_dim, 1.0 - gold) * mix(vec3(1.0), steel_warm, 1.0 - gold), vec3(metal_wear_bright), wear);                              // (bright bare metal on the worn edges)
		if (finish == 1) {
			// Blued steel: a deep blue-black oxide (darker on a darker key), a faint violet temper
			// in patches; chipped back to the bright steel under it along the worn rims and, in
			// scuffs, on what stands out (the edge and convexity masks, never painted).
			float temper = smoothstep(0.4, 0.75, fbm(op * 9.0 + piece * 5.0));
			vec3 oxide = mix(blued, blued_temper, temper * 0.6) * clamp(dot(mean_col, vec3(0.3, 0.59, 0.11)) / 0.42, 0.55, 1.0) * (0.9 + 0.2 * blot);
			// (its rim sits under the trim: the chipping reaches 14 mm in, broken up, worst at the very edge)
			float rim = 1.0 - smoothstep(0.003, 0.014, edge);
			float chip = clamp(max(smoothstep(0.35, 0.6, wear * (0.75 + 0.5 * fleck)), rim * smoothstep(0.62, 0.8, fleck + 0.25 * rim + 0.15 * blot)) * blued_chip, 0.0, 1.0);
			col = mix(oxide, col, chip);
			rough = mix(rough + 0.03, rough, chip);
		}
		// grime is dirt, not metal: dark, brown, dielectric
		vec3 dirt = vec3(0.045, 0.036, 0.027);
		if (rusty > 0.5) {
			// rust: its scan kept (half), rough and mostly dull, its edges worn back to dark iron
			col = mix(mean_col, texture(albedo, UV).rgb * tint, 0.5) * (0.9 + 0.2 * blot);
			rough = max(rough + 0.2, 0.62) - 0.15 * wear;
		}
		col = mix(col, dirt, grime * 0.8);
		metal = mix(1.0, 0.0, grime * 0.85);
		if (rusty > 0.5) metal = mix(0.35, 0.9, wear) * (1.0 - grime * 0.85);
		// (the pauldron's plates and the bracers satin, the set matching: at the Look they
		// blew out 5.7% of the lower frame at 0.32, face lead; judge 7)
		if (flag > 0.25 && flag < 0.75) rough += 0.04;
		rough = clamp(rough, metal_rough_floor, 0.85);
		// (gold only, a trial knob: glossier by gold_gloss)
		rough = mix(rough, max(gold_rough - 0.04 * polish, 0.08), gold * gold_gloss);
#ifdef OUTFIT_METAL_LIGHT
		// Its reflection held to what it can see: no probe, so the sky's (a bright dome lit to
		// light the scene) is kept only in part, least at the horizon (trees, walls, the camp)
		// and in what the sky can't reach (specular occlusion from the baked sky seen).
		vec3 rw = (INV_VIEW_MATRIX * vec4(reflect(-VIEW, NORMAL), 0.0)).xyz;
		float keep = metal_env * mix(metal_env_horizon, 1.0, smoothstep(0.05, 0.6, abs(rw.y))) * mix(0.2, 1.0, sky * sky);
		RADIANCE = vec4(0.0, 0.0, 0.0, 1.0 - keep);
		v_metal = metal;
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
	} else {
		// Gloss: clean and smooth, barely a grain.
		nrm = blend_normals(vec3(0.5, 0.5, 1.0), nrm, 0.12);
		rough = clamp(0.16 + 0.1 * macro + 0.1 * (1.0 - sky), 0.1, 0.4);
		metal = 0.0;
	}
	if (kind == 1) rough = mix(rough, max(rough, look_metal_rough), look_rig * (1.0 - gold));
	if (kind == 1) col *= mix(1.0, look_metal_dim, look_rig * (1.0 - gold));
	if (kind == 0) rough = mix(rough, max(rough, look_leather_rough), look_rig);
#ifdef OUTFIT_METAL_LIGHT
	ALBEDO = clamp(col, 0.0, 1.0);                  // (metal: its reflectance physical; the occlusion is in its reflection and its grime)
#else
	ALBEDO = clamp(col * mix(0.55, 1.0, sky), 0.0, 1.0);
#endif
	NORMAL_MAP = nrm;
	ROUGHNESS = rough;
	METALLIC = metal;
	AO = sky;
	EMISSION = gold_emit * mix(0.4, 1.0, sky);
	AO_LIGHT_AFFECT = 0.3;
	if (debug_view == 1) { ALBEDO = vec3(1.0 - smoothstep(0.0, 0.01, edge), fract(edge / 0.004), 0.0); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 2) { ALBEDO = vec3(conv); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 4) { ALBEDO = vec3(0.0); EMISSION = vec3(gold, 0.0, gold) * 4.0; ROUGHNESS = 1.0; METALLIC = 0.0; SPECULAR = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 5) { ALBEDO = vec3(0.30, 0.30, 0.36); ROUGHNESS = 0.4; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }   // (its shape alone: flat colour, no normal map, no mottle)
	if (debug_view == 3) { ALBEDO = vec3(sky); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
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
	float f90 = clamp(50.0 * f0.g, 0.0, 1.0);
	vec3 F = f0 + (f90 - f0) * pow(1.0 - cLdotH, 5.0);
	vec3 s = cNdotL * D * G * F * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT;
	vec3 lw = vec3(0.2126, 0.7152, 0.0722);
	float cap = metal_spec_cap * dot(LIGHT_COLOR, lw) * ATTENUATION * SPECULAR_AMOUNT * (1.0 / PI);
	float knee = metal_spec_knee * cap;
	float sl = dot(s, lw);
	if (sl > knee && cap > 1e-6) {
		float over = cap - knee;
		s *= (knee + over * (1.0 - exp(-(sl - knee) / over))) / sl;
	}
	SPECULAR_LIGHT += s;
}
#endif
