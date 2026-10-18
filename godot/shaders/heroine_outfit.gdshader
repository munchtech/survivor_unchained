// Her outfits' pieces (tools/assets/heroine_outfits.py), drawn as what they
// are made of rather than as a texture laid on a shape. Each piece carries,
// at each point, how far it is from the piece's edge and how convex it is
// there (its second UV), and how much of the sky it sees and a number of
// its own (its vertex colour); its first UV is in its material's repeats
// (`repeats` a metre), so all detail is at true size.
//  - leather: its grain, fine and coarse; a dyed, burnished edge; a row of
//    stitches in from the edge; lighter and smoother where it is worn (on
//    what stands out), darker in its creases.
//  - metal: forged, not chrome: a faint hammered unevenness and the grain of
//    its polishing; polished bright at its edges and on what stands out,
//    dulled and darkened where pieces meet and dirt keeps.
//  - cloth: its weave, a soft sheen at its edges as seen across it.
//  - gloss: latex and satin, clean and smooth.
shader_type spatial;

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
uniform float metal_rough = 0.46;                  // (its satin roughness, varied about this by +-0.05 over the piece)
uniform float metal_rough_wear = 0.34;             // (where worn bright: its edges and what stands out)
uniform float metal_rough_floor = 0.32;            // (no metal smoother than this: a mirror took the fire and the sky as blown spots)
uniform float metal_grime = 1.0;                   // (dirt in its recesses: dark, brown, dull, not metal)
uniform float metal_dent = 0.08;                   // (the hammered unevenness)
uniform float brass_dim = 0.62;                    // (gold read as aged brass: darker and a little greyer than the bright alloy)
uniform float brass_rough_add = 0.0;
uniform float metal_hammer = 0.05;                 // (planishing marks, 8 mm)
uniform float steel_dim = 0.8;                      // (the plate's field darker, so its worn edges read against it)
uniform vec3 steel_warm = vec3(1.04, 1.0, 0.93);    // (steel a warm grey: under an open sky it went blue)
uniform float metal_wear_bright = 1.3;
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
		nrm = normalize(vec3(slope, 1.0)) * 0.5 + 0.5;
		// Wear and grime fields, in the piece's own space (never screen space).
		vec2 op = vec2(opos.x + 0.6 * opos.z, opos.y - 0.4 * opos.z);
		float blot = fbm(op * 22.0 + piece * 13.0);                 // (hand-worn and wiped patches, a few cm)
		float fleck = fbm(op * 140.0 + 5.0);                         // (fine wear, mm)
		float polish = max(near_edge, bulge);
		// (the rim worn bright all along, broken up; the high points of a dome only scuffed, in patches)
		float wear = clamp(near_edge * smoothstep(0.2, 0.55, fleck + 0.25) + bulge * smoothstep(0.62, 0.8, fleck) * 0.7, 0.0, 1.0);
		// grime: in the hollows, out of the sky's reach, and where pieces meet, patchy
		float grime = clamp((0.7 * hollow + 0.8 * (1.0 - sky)) * smoothstep(0.25, 0.75, blot + 0.15) + 0.45 * smoothstep(0.002, 0.005, edge) * (1.0 - smoothstep(0.008, 0.02, edge)) * smoothstep(0.3, 0.7, blot), 0.0, 1.0) * metal_grime;   // (and a band of dirt just inside the rim, along the rivets)
		float brush = brushed(vec2(opos.x + opos.z, opos.y));   // (fine level streaks, one way over the whole piece)
		if (flag > 0.25 && flag < 0.75) brush = brushed(m);     // (a plate laid out round her arm brushed along it, by its UVs, judge 6)
		// Roughness: satin, varied; smoother where worn, rougher where dirty.
		rough = metal_rough + 0.10 * (blot - 0.5) + 0.05 * (brush - 0.5);
		rough = mix(rough, metal_rough_wear, wear);
		rough = mix(rough, 0.72, grime);
		// Colour: aged brass for gold (darker, less saturated, browner), the rest as built.
		vec3 brass = mix(vec3(dot(mean_col, vec3(0.3, 0.55, 0.15))), mean_col, 0.8) * brass_dim;
		col = mix(col, brass, gold);
		rough = mix(rough, rough + brass_rough_add, gold);
		col *= 0.9 + 0.2 * blot;                                  // (an uneven patina)
		col *= mix(mix(1.0, steel_dim, 1.0 - gold) * mix(vec3(1.0), steel_warm, 1.0 - gold), vec3(metal_wear_bright), wear);                              // (bright bare metal on the worn edges)
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
		col *= mix(0.75, 1.0, sky);
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
	ALBEDO = clamp(col * mix(0.55, 1.0, sky), 0.0, 1.0);
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
