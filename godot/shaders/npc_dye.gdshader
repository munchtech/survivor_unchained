// A Marionette package NPC's baked "generated" material with per-copy dye (Actors/NpcDye.cs; mask by
// tools/meshy/dye_mask.py). Otherwise exactly the StandardMaterial3D the glTF importer makes of it (albedo,
// metallic-roughness from one texture's B and G, normal map, two-sided, Burley diffuse, Schlick-GGX specular), so
// a copy with no dye draws as before. One material per package; each copy's colours are instance uniforms.
// In a channel (mask R = cloth "a", G = cloth "b", B = hair): out = target * lum(texel) / lum(base), so the paint's
// folds and shading stay; w of each instance uniform is the channel's strength (0: the paint as painted).
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
uniform vec3 dye_base_lum = vec3(1.0);
instance uniform vec4 dye_a = vec4(0.0);
instance uniform vec4 dye_b = vec4(0.0);
instance uniform vec4 dye_h = vec4(0.0);

void vertex() {
	UV = UV * uv1_scale.xy + uv1_offset.xy;
}

float dye_lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void fragment() {
	vec2 base_uv = UV;
	vec4 albedo_tex = texture(texture_albedo, base_uv);
	vec3 col = albedo.rgb * albedo_tex.rgb;
	if (dye_a.w + dye_b.w + dye_h.w > 0.0) {
		vec3 m = texture(dye_mask, base_uv).rgb * vec3(dye_a.w, dye_b.w, dye_h.w);
		float l = dye_lum(col);
		vec3 ra = dye_a.rgb * (l / max(dye_base_lum.x, 1e-4));
		vec3 rb = dye_b.rgb * (l / max(dye_base_lum.y, 1e-4));
		vec3 rh = dye_h.rgb * (l / max(dye_base_lum.z, 1e-4));
		vec3 o = col;
		o = mix(o, ra, m.r);
		o = mix(o, rb, m.g);
		o = mix(o, rh, m.b);
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
