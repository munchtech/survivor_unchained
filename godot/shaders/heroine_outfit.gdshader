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

uniform int kind = 0;                              // 0 leather, 1 metal, 2 cloth, 3 gloss
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
uniform int debug_view = 0;                        // (1 edge distance, 2 convexity, 3 sky seen: to check what was baked)

varying vec4 det;                                  // (edge distance m, convexity 0..1, sky seen, piece)
varying float painted;                             // (1 where stitches are painted; 0 where the piece is sewn with thread of its own)

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) { return 0.5 * noise(p) + 0.3 * noise(p * 2.13 + 7.1) + 0.2 * noise(p * 4.37 + 3.3); }

void vertex() {
	det = vec4(UV2.x, UV2.y, COLOR.r, COLOR.g);
	painted = COLOR.b;
}

vec3 blend_normals(vec3 a, vec3 b, float k) {      // (two normal-map texels, the second laid over the first; encoded as maps are)
	vec3 n1 = a * 2.0 - 1.0, n2 = b * 2.0 - 1.0;
	return normalize(vec3(n1.xy + n2.xy * k, n1.z)) * 0.5 + 0.5;
}

void fragment() {
	vec2 m = UV / repeats;                          // (metres)
	vec3 col = texture(albedo, UV).rgb * tint;
	vec3 nrm = texture(normal_map, UV).rgb;
	float rough = has_orm ? texture(orm, UV).g : roughness_value;
	float metal = has_orm ? mix(metallic_value, texture(orm, UV).b, step(0.5, metallic_value)) : metallic_value;
	float edge = det.x, conv = det.y, sky = det.z, piece = det.w;
	float near_edge = 1.0 - smoothstep(0.0, 0.003, edge);
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
		// (satin, not gloss: leather is never shinier than this but at its burnished edges)
		rough = clamp(rough * 0.9 - 0.08 * bulge - 0.15 * near_edge + 0.1 * hollow, mix(0.42, 0.28, near_edge), 0.95);
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
		metal = 0.0;
	} else if (kind == 1) {
		// Metal: the scan's grain kept faint, a hammered unevenness, its
		// polish brightest at the edges and on what stands out, dulled and
		// darkened in the crevices and where it meets other pieces.
		// (the scan's colour flattened to its mean: its stains read as dirt
		// on plate that is kept; the plate's own story is told below)
		// (one formed piece, not a patchwork: the scan's stains and dents
		// kept to a whisper, a faint planishing over all of it)
		// (a formed plate reads as one smooth surface: the scan's patches,
		// even faint, read in its reflections as lumps, so none of it here)
		vec3 mean_col = textureLod(albedo, vec2(0.5), 20.0).rgb * tint;   // (its smallest mip, one texel: the true mean; a 2x2 mip read through each UV island's own corner showed as pale patches)
		col = mean_col * (0.98 + 0.03 * macro);
		vec2 e = vec2(0.003, 0.0);
		float h0 = fbm(m * 40.0), hx = fbm((m + e.xy) * 40.0), hy = fbm((m + e.yx) * 40.0);
		vec3 dent = normalize(vec3((h0 - hx) * 0.08, (h0 - hy) * 0.08, 1.0)) * 0.5 + 0.5;
		nrm = dent;
		float polish = max(near_edge, bulge);
		// (brushed along one way: fine streaks in its roughness)
		float brush = noise(vec2(m.x * 1800.0, m.y * 40.0));
		rough = clamp(mix(0.3, 0.18, polish) + 0.1 * hollow + 0.14 * (1.0 - sky) + 0.06 * (brush - 0.5), 0.12, 0.6);
		col *= mix(0.7, 1.0, sky) * mix(1.0, 1.1, polish);
		metal = 1.0;   // (all metal: the scan's metal map has rust and dirt in it, and each patch of it showed as a pale fleck)
		ANISOTROPY = 0.35;
		ANISOTROPY_FLOW = vec2(1.0, 0.0);
	} else if (kind == 2) {
		// Cloth: its weave fine, rough, a sheen seen across it.
		nrm = blend_normals(nrm, texture(normal_map, UV * 3.7).rgb, 0.8);
		rough = clamp(rough * 0.3 + 0.7, 0.6, 1.0);
		metal = 0.0;
		RIM = 0.35;
		RIM_TINT = 0.6;
	} else {
		// Gloss: clean and smooth, barely a grain.
		nrm = blend_normals(vec3(0.5, 0.5, 1.0), nrm, 0.12);
		rough = clamp(0.16 + 0.1 * macro + 0.1 * (1.0 - sky), 0.1, 0.4);
		metal = 0.0;
	}
	ALBEDO = col * mix(0.55, 1.0, sky);
	NORMAL_MAP = nrm;
	ROUGHNESS = rough;
	METALLIC = metal;
	AO = sky;
	AO_LIGHT_AFFECT = 0.3;
	if (debug_view == 1) { ALBEDO = vec3(1.0 - smoothstep(0.0, 0.01, edge), fract(edge / 0.004), 0.0); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 2) { ALBEDO = vec3(conv); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
	if (debug_view == 3) { ALBEDO = vec3(sky); ROUGHNESS = 1.0; METALLIC = 0.0; NORMAL_MAP = vec3(0.5, 0.5, 1.0); }
}
