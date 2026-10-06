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
uniform float rough = 0.5;
uniform float shine = 0.42;
uniform float scatter = 0.38;
// The soft rim the fine down on skin gives against a light from behind.
uniform float rim = 0.25;
// Rougher where the skin is seen edge on: there a light from behind
// glanced off it as a hard white band (the Fresnel peak a matte skin's fine
// hairs and pores break up).
uniform float edge_rough = 0.0;
// Her face's features drawn bold (tools/assets/heroine_features.py: red her
// eyes and brows, green her lips), deepened the smaller her face is on
// screen: from the game's camera her face is a few pixels across, and her
// paint's mipmaps average her eyes, brows and lips into her skin. Measured
// as how many of her paint's texels a pixel covers (2^far_from to 2^far_to).
// (Begun sooner and darker since her face became a photograph's: its
// features are softer than the old paint's, and at the nearest play zoom,
// 12.5 m, her eyes had all but gone.)
uniform sampler2D features : hint_default_black, filter_linear_mipmap;
// Her head's own shade where light reaches it less (tools/assets/heroine_features.py's
// heroine_ao.png: under her jaw and chin, her nostrils, the corners of her mouth),
// on the light round her and on some of her lights' too (as a soft shadow).
uniform sampler2D ao_map : hint_default_white, filter_linear_mipmap;
uniform float ao_light = 0.0;
uniform float far_from = 3.0;
uniform float far_to = 5.0;
uniform float far_dark = 0.86;
uniform vec3 far_lips : source_color = vec3(0.62, 0.16, 0.15);
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
	ALBEDO = texture(paint, UV).rgb * tone;
	if (brow_dye > 0.0) {
		// (the hairs' own lightness kept, their black core lifted a little,
		// so a fair or red man's brows are not black ones tinted)
		float bm = texture(shadow_mask, UV).b * brow_dye;
		vec3 lw = vec3(0.3, 0.59, 0.11);
		float l = dot(ALBEDO, lw) / max(dot(brow_paint * tone, lw), 0.02);
		ALBEDO = mix(ALBEDO, brow_colour * tone * pow(clamp(l, 0.0, 1.15), 0.5), bm);
	}
	vec2 tx = UV * vec2(textureSize(paint, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	float far = smoothstep(far_from, far_to, lod);
	vec2 f = texture(features, UV).rg * far;
	ALBEDO *= 1.0 - far_dark * f.x;
	ALBEDO = mix(ALBEDO, far_lips * tone, 0.75 * f.y);
	// (two offset tiles, so no grid shows, their depth varying over her in
	// soft patches as real pores do)
	vec4 q = mix(texture(pores, UV * pore_scale), texture(pores, UV * pore_scale * 0.77 + vec2(0.53, 0.19)), 0.35);
	float patchy = smoothstep(0.2, 0.8, texture(pores, UV * pore_scale * 0.07 + vec2(0.31, 0.67)).a);
	float depth = pore_depth * mix(0.35, 1.0, patchy);
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
	AO = ao;
	AO_LIGHT_AFFECT = ao_light;
	SSS_STRENGTH = scatter;
	RIM = rim;
	RIM_TINT = 0.6;
	BACKLIGHT = ALBEDO * vec3(1.0, 0.45, 0.35) * 0.18;
}
