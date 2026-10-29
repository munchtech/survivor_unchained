// A Marionette package NPC's baked "generated" material with per-copy dye (Actors/NpcDye.cs; mask by
// tools/meshy/dye_mask.py). Otherwise exactly the StandardMaterial3D the glTF importer makes of it (albedo,
// metallic-roughness from one texture's B and G, normal map, two-sided, Burley diffuse, Schlick-GGX specular), so
// a copy with no dye draws as before. One material per package; each copy's colours are instance uniforms.
// In a channel (mask R = cloth "a", G = cloth "b", B = hair, A = head cloth): out = target * gain, gain = lum(texel) /
// lum(base) with a soft knee (a highlight far over the region's mean no longer blows a dye out to candy), the result's
// Oklab chroma capped (dye_max_chroma: no copy goes neon however bright its texel), so the paint's folds and shading
// stay; w of each instance uniform is the channel's strength (0: the paint as painted). dye_s (the risen only): where
// the mask is 0 (bare skin) the paint times dye_s.rgb, w its strength. The mask is imported lossless: a block-
// compressed mask bleeds its channels into each other in 4x4 blocks (specks of one dye in another).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform vec4 albedo : source_color = vec4(1.0);
uniform sampler2D texture_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float roughness : hint_range(0.0, 1.0) = 1.0;
uniform sampler2D texture_metallic : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 metallic_texture_channel = vec4(0.0, 0.0, 1.0, 0.0);
uniform sampler2D texture_roughness : hint_roughness_g, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float specular : hint_range(0.0, 1.0, 0.01) = 0.5;
uniform float metallic : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform sampler2D texture_normal : hint_roughness_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float normal_scale : hint_range(-16.0, 16.0) = 1.0;
uniform vec3 uv1_scale = vec3(1.0);
uniform vec3 uv1_offset = vec3(0.0);

uniform sampler2D dye_mask : hint_default_black, filter_linear_mipmap, repeat_enable;
// each channel's base luminance (linear, the region's measured mean)
uniform vec4 dye_base_lum = vec4(1.0);
uniform float dye_max_chroma = 0.09;
instance uniform vec4 dye_a = vec4(0.0);
instance uniform vec4 dye_b = vec4(0.0);
instance uniform vec4 dye_h = vec4(0.0);
instance uniform vec4 dye_c = vec4(0.0);
instance uniform vec4 dye_s = vec4(0.0);

void vertex() {
	UV = UV * uv1_scale.xy + uv1_offset.xy;
}

float dye_lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

// gain over 1.5 eases towards 3.0 (as NpcDyePick.Gain)
vec4 dye_gain(vec4 g) {
	vec4 e = max(g - 1.5, vec4(0.0));
	return min(g, vec4(1.5)) + e / (1.0 + e / 1.5);
}

// a linear colour with its Oklab chroma held to at most cmax, lightness and hue kept (as NpcDyePick.CapChroma)
vec3 dye_cap(vec3 c, float cmax) {
	c = max(c, vec3(0.0));
	vec3 lms = pow(mat3(vec3(0.4122214708, 0.2119034982, 0.0883024619), vec3(0.5363325363, 0.6806995451, 0.2817188376),
		vec3(0.0514459929, 0.1073969566, 0.6299787005)) * c, vec3(1.0 / 3.0));
	vec3 o = mat3(vec3(0.2104542553, 1.9779984951, 0.0259040371), vec3(0.7936177850, -2.4285922050, 0.7827717662),
		vec3(-0.0040720468, 0.4505937099, -0.8086757660)) * lms;
	float ch = length(o.yz);
	if (ch <= cmax) return c;
	o.yz *= cmax / ch;
	vec3 l3 = mat3(vec3(1.0, 1.0, 1.0), vec3(0.3963377774, -0.1055613458, -0.0894841775),
		vec3(0.2158037573, -0.0638541728, -1.2914855480)) * o;
	l3 = l3 * l3 * l3;
	return clamp(mat3(vec3(4.0767416621, -1.2684380046, -0.0041960863), vec3(-3.3077115913, 2.6097574011, -0.7034186147),
		vec3(0.2309699292, -0.3413193965, 1.7076147010)) * l3, vec3(0.0), vec3(1.0));
}

void fragment() {
	vec2 base_uv = UV;
	vec4 albedo_tex = texture(texture_albedo, base_uv);
	vec3 col = albedo.rgb * albedo_tex.rgb;
	if (dye_a.w + dye_b.w + dye_h.w + dye_c.w + dye_s.w > 0.0) {
		vec4 mk = texture(dye_mask, base_uv);
		vec4 m = mk * vec4(dye_a.w, dye_b.w, dye_h.w, dye_c.w);
		vec4 g = dye_gain(vec4(dye_lum(col)) / max(dye_base_lum, vec4(1e-4)));
		vec3 o = col;
		if (m.r > 0.0) o = mix(o, dye_cap(dye_a.rgb * g.x, dye_max_chroma), m.r);
		if (m.g > 0.0) o = mix(o, dye_cap(dye_b.rgb * g.y, dye_max_chroma), m.g);
		if (m.b > 0.0) o = mix(o, dye_cap(dye_h.rgb * g.z, dye_max_chroma), m.b);
		if (m.a > 0.0) o = mix(o, dye_cap(dye_c.rgb * g.w, dye_max_chroma), m.a);
		// bare skin (the risen): where no cloth or hair channel is
		float sk = (1.0 - clamp(max(max(mk.r, mk.g), max(mk.b, mk.a)), 0.0, 1.0)) * dye_s.w;
		o = mix(o, o * dye_s.rgb, sk);
		col = clamp(o, vec3(0.0), vec3(1.0));
	}
	ALBEDO = col;
	float metallic_tex = dot(texture(texture_metallic, base_uv), metallic_texture_channel);
	METALLIC = metallic_tex * metallic;
	SPECULAR = specular;
	vec4 roughness_texture_channel = vec4(0.0, 1.0, 0.0, 0.0);
	float roughness_tex = dot(texture(texture_roughness, base_uv), roughness_texture_channel);
	ROUGHNESS = roughness_tex * roughness;
	NORMAL_MAP = texture(texture_normal, base_uv).rgb;
	NORMAL_MAP_DEPTH = normal_scale;
}
