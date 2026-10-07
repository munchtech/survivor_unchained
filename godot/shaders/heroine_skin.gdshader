// Her skin: her paint, warmed to her tone, with light carried under it
// (subsurface scattering, reddened as through flesh); its fine relief, pores
// and the creases between them (tools/assets/skin_pores.py, tiled a pore's
// size whatever her UVs' scale, so the same on her face as on her body),
// bending the light at a glance; its sheen soft and uneven, duller in the
// pores, never the even gloss of plastic; a soft rim at her edges, as the
// fine down on skin catches the light; light through her where she is thin.
shader_type spatial;
render_mode sss_mode_skin;

uniform sampler2D paint : source_color, filter_linear_mipmap_anisotropic;
uniform vec3 tone : source_color = vec3(1.0, 0.86, 0.74);
// Her pores' tile (RGB its normals, A how rough), and how many tiles to a
// UV unit (People.cs works it out from the mesh: one tile every 9 mm; at
// 1.5 cm they read as large and even on her hands).
uniform sampler2D pores : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float pore_scale = 30.0;
uniform float pore_depth = 0.6;
// Her skin's own fine grain (tools/assets/heroine_grain.py: her face paint's
// high frequencies, a 2.8 cm tile; 0.5 as she is, 0.25 a 6% change) up her
// neck, whose paint is smooth: against her face it read as another's skin,
// finer and flatter (her portrait's neck has nearly half her face's grain).
// Not on her face (the features' blue), which has its own, and not from her
// collarbones down (her freckles' map's blue): over her body it read as a
// speckle on her breasts, whose skin is smooth but for its pores and
// freckles. Two reads at two sizes, so the tile never shows.
uniform sampler2D grain : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float grain_amount = 0.0;
uniform float rough = 0.5;
uniform float shine = 0.42;
uniform float scatter = 0.38;
// The soft rim the fine down on skin gives against a light from behind.
uniform float rim = 0.25;
// Where her lit side ends, light carried under the skin reaches a little
// past where the surface turns from the lamp, red furthest, so the edge is
// soft and warm, never a hard grey line: each channel's reach past it, in
// N.L (beyond it her light is Godot's own). (Under the portraits' side key
// her lit side's edge ran straight down the middle of her throat as a dark
// line; Godot's screen-space scattering spreads a few pixels at a close-up,
// and spread wider it blurred away her skin's grain.)
uniform vec3 terminator = vec3(0.32, 0.15, 0.1);
// Her sheen's strength (SPECULAR), for her light() to read.
varying float sheen;
// Rougher where the skin is seen edge on: there a light from behind
// glanced off it as a hard white band (the Fresnel peak a matte skin's fine
// hairs and pores break up).
uniform float edge_rough = 0.0;
// Her face's features drawn bold (tools/assets/heroine_features.py: red her
// eyes and brows, green her lips), deepened the smaller her face is on
// screen: from the game's camera her face is a few pixels across, and her
// paint's mipmaps average her eyes, brows and lips into her skin. Measured
// as how many of her paint's texels a pixel covers (2^far_from to 2^far_to):
// none at the book's view (her face 100 pixels tall, where it read as a
// shadow round her eyes), all of it at play's (8 to 16 pixels).
uniform sampler2D features : hint_default_black, filter_linear_mipmap;
// Her head's own shade where light reaches it less (tools/assets/heroine_features.py's
// heroine_ao.png: under her jaw and chin, her nostrils, the corners of her mouth),
// on the light round her and on some of her lights' too (as a soft shadow).
uniform sampler2D ao_map : hint_default_white, filter_linear_mipmap;
uniform float ao_light = 0.0;
// Her freckles, a layer of their own (tools/assets/heroine_freckles.py: red
// each freckle, soft at its edge; green its rank), none to heavy: at an
// amount, those ranked under it show, deeper the more there are, in a warm
// brown laid over her skin's own colour.
uniform sampler2D freckles : hint_default_black, filter_linear_mipmap;
uniform float freckle_amount = 0.0;
uniform vec3 freckle_colour = vec3(0.62, 0.45, 0.33);
uniform float far_from = 4.5;
uniform float far_to = 6.5;
uniform float far_dark = 0.86;
uniform vec3 far_lips : source_color = vec3(0.62, 0.16, 0.15);
// The features' mask read at this pixel's own level of detail, but never
// coarser than far_mip of its own mipmaps, and drawn far_bold times as
// strong: at play zoom (her face 8 pixels across) a mip that fits the pixel
// averages each eye into a texel of skin, and her face was a blank. Coarser
// than this the marks blur into one another; finer, they flicker.
uniform float far_mip = 3.0;
uniform float far_bold = 3.0;
// Her face's own colour against her portrait's (People.HerFaceTone, in
// linear light), laid where her face's paint is (the features' blue): each
// face's paint a few per cent off its portrait, her neck and body untouched.
uniform vec3 face_tone = vec3(1.0);
// A body's own relief, baked from its sculpt (the hero's: every muscle and
// vein his reduced mesh has only in paint), the pores laid over it.
uniform sampler2D relief : hint_normal, filter_linear_mipmap_anisotropic;
uniform bool has_relief = false;
// A man's shaved shadow (the hero's: People.HisShadow): where his beard and
// his hair grow (shadow_mask, red his beard's ground, green his scalp's),
// each as dark as chosen, of the hair's own colour; stubble, not a stain:
// the darkening broken into the stubs of hairs.
uniform sampler2D shadow_mask : hint_default_black, filter_linear_mipmap;
uniform float beard_shadow = 0.0;
uniform float scalp_shadow = 0.0;
// (his scalp shaved, its shadow the stubs of hairs; hers under her hair, an
// even shade: broken into dots, her hairline read as speckled)
uniform float scalp_stubs = 1.0;
uniform vec3 shadow_colour : source_color = vec3(0.16, 0.12, 0.1);
// His brows (painted with his face; the blue of shadow_mask) dyed his
// hair's colour: their paint scaled from its own colour (brow_paint) to
// brow_colour, every hair of it kept.
uniform float brow_dye = 0.0;
uniform vec3 brow_paint : source_color = vec3(0.2, 0.15, 0.12);
uniform vec3 brow_colour : source_color = vec3(0.2, 0.15, 0.12);

// Her skin under her outfit's fitted pieces, tucked up to 8 mm in, and a
// nipple's tip under a plate 10 (less let it through for a pixel as she
// swung an axe)
// (heroine_outfits.py marks it, graded from a piece's edge, in the channel
// of her vertex colours tuck_channel names): it never shows through what
// she wears, and as nothing of her is cut away no gap opens in her where a
// piece swings off her.
uniform int tuck_channel = -1;
uniform float tuck = 0.010;

void vertex() {
	if (tuck_channel >= 0) {
		float h = tuck_channel == 0 ? COLOR.r : tuck_channel == 1 ? COLOR.g : tuck_channel == 2 ? COLOR.b : COLOR.a;
		VERTEX -= NORMAL * tuck * h;
	}
}

void fragment() {
	vec2 tx = UV * vec2(textureSize(paint, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	float far = smoothstep(far_from, far_to, lod);
	float fl = clamp(lod - log2(float(textureSize(paint, 0).x) / float(max(textureSize(features, 0).x, 1))), 0.0, far_mip);
	vec3 fm = textureLod(features, UV, fl).rgb;
	ALBEDO = texture(paint, UV).rgb * tone * mix(vec3(1.0), face_tone, fm.b);
	vec3 fk = texture(freckles, UV).rgb;
	if (freckle_amount > 0.001) {
		float fv = fk.r * (1.0 - smoothstep(freckle_amount - 0.04, freckle_amount + 0.04, fk.g));
		ALBEDO = mix(ALBEDO, ALBEDO * freckle_colour, fv * mix(0.5, 1.0, freckle_amount));
	}
	if (brow_dye > 0.0) {
		// (the hairs' own lightness kept, their black core lifted a little,
		// so a fair or red man's brows are not black ones tinted)
		float bm = texture(shadow_mask, UV).b * brow_dye;
		vec3 lw = vec3(0.3, 0.59, 0.11);
		float l = dot(ALBEDO, lw) / max(dot(brow_paint * tone, lw), 0.02);
		ALBEDO = mix(ALBEDO, brow_colour * tone * pow(clamp(l, 0.0, 1.15), 0.5), bm);
	}
	vec2 f = fm.rg;
	if (far > 0.0) {
		// (the marks grown to the pixel: the most of them anywhere in it, from its
		// corners, so an eye a third of a pixel high still darkens a whole one;
		// sampled at its middle, her eyes at play zoom were missed one frame in two)
		vec2 hx = 0.5 * dFdx(UV), hy = 0.5 * dFdy(UV);
		f = max(max(f, textureLod(features, UV + hx + hy, fl).rg), max(textureLod(features, UV + hx - hy, fl).rg,
			max(textureLod(features, UV - hx + hy, fl).rg, textureLod(features, UV - hx - hy, fl).rg)));
	}
	f = clamp(f * far_bold, 0.0, 1.0) * far;
	ALBEDO *= 1.0 - far_dark * f.x;
	ALBEDO = mix(ALBEDO, far_lips * tone, 0.75 * f.y);
	// (two offset tiles, so no grid shows, their depth varying over her in
	// soft patches as real pores do)
	vec4 q = mix(texture(pores, UV * pore_scale), texture(pores, UV * pore_scale * 0.77 + vec2(0.53, 0.19)), 0.35);
	float patchy = smoothstep(0.2, 0.8, texture(pores, UV * pore_scale * 0.07 + vec2(0.31, 0.67)).a);
	float depth = pore_depth * mix(0.35, 1.0, patchy);
	// (where her freckles' map says, its blue: her head and up her neck, none from her collarbones down)
	float ga = grain_amount * (1.0 - fm.b) * fk.b;
	if (ga > 0.0) {
		// (a tile every 28 mm: pore_scale is a tile every 9; the two reads' mean has
		// 0.71 of one's spread, given back)
		vec2 gu = UV * pore_scale * 0.321;
		float gr = texture(grain, gu + vec2(0.37, 0.11)).r + texture(grain, gu * 0.71 + vec2(0.83, 0.59)).r - 1.0;
		ALBEDO *= 1.0 + ga * gr * 0.707 * 0.24;
	}
	float stubble = 0.0;
	if (beard_shadow > 0.0 || scalp_shadow > 0.0) {
		vec2 g = texture(shadow_mask, UV).rg;
		// (the stubs: the pore tile's grain, finer, as dots)
		float stubs = smoothstep(0.3, 0.7, texture(pores, UV * pore_scale * 1.62 + vec2(0.37, 0.11)).a);
		float dots = mix(0.55, 1.0, stubs);
		stubble = clamp(g.r * beard_shadow * dots + g.g * scalp_shadow * mix(1.0, dots, scalp_stubs), 0.0, 1.0);
		ALBEDO = mix(ALBEDO, ALBEDO * shadow_colour * 2.4, stubble * 0.85);
	}
	if (has_relief) {
		// The two reliefs as one (each from its x and y, as Godot keeps a
		// normal map): the pores' slopes added to the body's, at their depth.
		vec2 a = texture(relief, UV).xy * 2.0 - 1.0;
		vec2 b = (q.xy * 2.0 - 1.0) * depth;
		vec3 n = normalize(vec3(a + b, sqrt(max(0.0, 1.0 - dot(a, a)))));
		NORMAL_MAP = vec3(n.xy * 0.5 + 0.5, 1.0);
		NORMAL_MAP_DEPTH = 1.0;
	} else {
		NORMAL_MAP = q.rgb;
		NORMAL_MAP_DEPTH = depth;
	}
	float edge = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ROUGHNESS = clamp(rough + (q.a - 0.5) * 0.3 + stubble * 0.15 + edge_rough * edge, 0.0, 1.0);
	// (no sheen where her head's own shade is deep: in the crease where her
	// lips meet and the mouth behind, the rim light's reflection on her lips'
	// inner linings showed as white slivers along their line at a turn)
	float ao = texture(ao_map, UV).r;
	SPECULAR = shine * smoothstep(0.45, 0.95, ao);
	sheen = SPECULAR;
	AO = ao;
	AO_LIGHT_AFFECT = ao_light;
	SSS_STRENGTH = scatter;
	BACKLIGHT = ALBEDO * vec3(1.0, 0.45, 0.35) * 0.18;
}

// Each lamp's light on her, as Godot's own (Burley's diffuse, GGX's sheen,
// the rim, the light through her) but for where her lit side ends (see
// `terminator`).
float schlick(float u) {
	float m = clamp(1.0 - u, 0.0, 1.0);
	float m2 = m * m;
	return m2 * m2 * m;
}

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float c_ndl = max(ndl, 0.0);
	float c_ndv = max(dot(NORMAL, VIEW), 1e-4);
	vec3 h = normalize(VIEW + LIGHT);
	float c_ndh = clamp(dot(NORMAL, h), 0.0, 1.0);
	float c_ldh = clamp(dot(LIGHT, h), 0.0, 1.0);
	// (the edge eased over each channel's reach, C1 with the light either side:
	// (n + w)^2 / 4w from -w to w, n itself beyond)
	vec3 w = max(terminator, vec3(1e-4));
	vec3 n = vec3(ndl);
	vec3 t = clamp(n + w, vec3(0.0), 2.0 * w);
	vec3 soft = mix(t * t / (4.0 * w), n, step(w, n));
	float fd90 = 2.0 * c_ldh * c_ldh * ROUGHNESS - 0.5;
	float burley = (1.0 + fd90 * schlick(c_ndv)) * (1.0 + fd90 * schlick(c_ndl));
	vec3 diffuse = soft * burley / PI;
	DIFFUSE_LIGHT += LIGHT_COLOR * diffuse * ATTENUATION;
	// the fine down at her edges
	float rim_light = pow(max(1e-4, 1.0 - c_ndv), max(0.0, (1.0 - ROUGHNESS) * 16.0));
	DIFFUSE_LIGHT += rim_light * rim * mix(vec3(1.0), ALBEDO, 0.6) * LIGHT_COLOR * ATTENUATION;
	// light through her where she is thin
	DIFFUSE_LIGHT += LIGHT_COLOR * max(vec3(1.0 / PI) - diffuse, vec3(0.0)) * BACKLIGHT * ATTENUATION;
	if (c_ndl > 0.0) {
		float a = ROUGHNESS * ROUGHNESS;
		float da = c_ndh * a;
		float k = a / (1.0 - c_ndh * c_ndh + da * da);
		float d_ggx = k * k / PI;
		float v_ggx = 0.5 / mix(2.0 * c_ndl * c_ndv, c_ndl + c_ndv, a);
		float f0 = 0.16 * sheen * sheen;
		float f90 = clamp(f0 * 50.0, 0.0, 1.0);
		float f = f0 + (f90 - f0) * schlick(c_ldh);
		SPECULAR_LIGHT += c_ndl * d_ggx * f * v_ggx * LIGHT_COLOR * ATTENUATION * SPECULAR_AMOUNT;
	}
}
