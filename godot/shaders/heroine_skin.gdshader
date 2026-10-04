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
// UV unit (People.cs works it out from the mesh: one tile every 1.5 cm).
uniform sampler2D pores : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float pore_scale = 30.0;
uniform float pore_depth = 0.6;
uniform float rough = 0.5;
uniform float shine = 0.42;
uniform float scatter = 0.38;
// Her face's features drawn bold (tools/assets/heroine_features.py: red her
// eyes and brows, green her lips), deepened the smaller her face is on
// screen: from the game's camera her face is a few pixels across, and her
// paint's mipmaps average her eyes, brows and lips into her skin. Measured
// as how many of her paint's texels a pixel covers (2^far_from to 2^far_to).
uniform sampler2D features : hint_default_black, filter_linear_mipmap;
uniform float far_from = 3.5;
uniform float far_to = 6.0;
uniform float far_dark = 0.78;
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
uniform vec3 shadow_colour : source_color = vec3(0.16, 0.12, 0.1);

void fragment() {
	ALBEDO = texture(paint, UV).rgb * tone;
	vec2 tx = UV * vec2(textureSize(paint, 0));
	float lod = 0.5 * log2(max(dot(dFdx(tx), dFdx(tx)), dot(dFdy(tx), dFdy(tx))));
	float far = smoothstep(far_from, far_to, lod);
	vec2 f = texture(features, UV).rg * far;
	ALBEDO *= 1.0 - far_dark * f.x;
	ALBEDO = mix(ALBEDO, far_lips * tone, 0.75 * f.y);
	vec4 q = texture(pores, UV * pore_scale);
	float stubble = 0.0;
	if (beard_shadow > 0.0 || scalp_shadow > 0.0) {
		vec2 g = texture(shadow_mask, UV).rg;
		// (the stubs: the pore tile's grain, finer, as dots)
		float stubs = smoothstep(0.3, 0.7, texture(pores, UV * pore_scale * 2.7 + vec2(0.37, 0.11)).a);
		stubble = clamp(g.r * beard_shadow + g.g * scalp_shadow, 0.0, 1.0) * mix(0.55, 1.0, stubs);
		ALBEDO = mix(ALBEDO, ALBEDO * shadow_colour * 2.4, stubble * 0.85);
	}
	if (has_relief) {
		// The two reliefs as one (each from its x and y, as Godot keeps a
		// normal map): the pores' slopes added to the body's, at their depth.
		vec2 a = texture(relief, UV).xy * 2.0 - 1.0;
		vec2 b = (q.xy * 2.0 - 1.0) * pore_depth;
		vec3 n = normalize(vec3(a + b, sqrt(max(0.0, 1.0 - dot(a, a)))));
		NORMAL_MAP = vec3(n.xy * 0.5 + 0.5, 1.0);
		NORMAL_MAP_DEPTH = 1.0;
	} else {
		NORMAL_MAP = q.rgb;
		NORMAL_MAP_DEPTH = pore_depth;
	}
	ROUGHNESS = clamp(rough + (q.a - 0.5) * 0.3 + stubble * 0.15, 0.0, 1.0);
	SPECULAR = shine;
	SSS_STRENGTH = scatter;
	RIM = 0.25;
	RIM_TINT = 0.6;
	BACKLIGHT = ALBEDO * vec3(1.0, 0.45, 0.35) * 0.18;
}
