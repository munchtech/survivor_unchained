// A person's clothes, dyed (Actors/People.cs; the web game's dyeMaterial).
// The painted texture keeps its folds and stitching; the part of it that is
// cloth (a band of hue, saturation and value) takes the dye, as bright as the
// paint was. What is not cloth (leather, buckles, skin) keeps its paint.
// Otherwise as the imported material: albedo, normal map, roughness from a
// channel of a texture, two-sided, a rim of light at the edge.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 albedo : source_color = vec4(1.0);
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool use_normal = false;
uniform sampler2D normal_tex : hint_roughness_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float normal_scale = 1.0;
uniform bool use_rough = false;
uniform sampler2D rough_tex : hint_roughness_gray, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 rough_channel = vec4(0.0, 1.0, 0.0, 0.0);
uniform float roughness = 1.0;
uniform float metallic = 0.0;
uniform bool use_metal = false;
uniform sampler2D metal_tex : hint_default_black, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 metal_channel = vec4(0.0, 0.0, 1.0, 0.0);
uniform float rim_amount = 0.45;
uniform float rim_tint = 0.35;
uniform vec3 emission = vec3(0.0);

uniform bool use_dye = false;
uniform vec3 dye_color = vec3(1.0);
// (lo, hi, soft) of the band the cloth's paint lies in.
uniform vec3 dye_h = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_s = vec3(0.0, 1.0, 0.05);
uniform vec3 dye_v = vec3(0.0, 1.0, 0.05);
// How bright the cloth's paint is: the dye is scaled by the paint's brightness over this.
uniform float dye_lum = 0.25;

float dye_band(float x, vec3 r) { return smoothstep(r.x - r.z, r.x, x) * (1.0 - smoothstep(r.y, r.y + r.z, x)); }

vec3 dye_hsv(vec3 c) {
	vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
	vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
	vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
	float d = q.x - min(q.w, q.y);
	return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + 1e-10)), d / (q.x + 1e-10), q.x);
}

void fragment() {
	vec3 c = albedo.rgb * texture(albedo_tex, UV).rgb;
	if (use_dye) {
		vec3 hsv = dye_hsv(pow(max(c, vec3(0.0)), vec3(1.0 / 2.2)));
		float m = dye_band(hsv.x, dye_h) * dye_band(hsv.y, dye_s) * dye_band(hsv.z, dye_v);
		float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
		c = mix(c, min(dye_color * (lum / dye_lum), vec3(1.0)), m);
	}
	ALBEDO = c;
	if (use_normal) {
		NORMAL_MAP = texture(normal_tex, UV).rgb;
		NORMAL_MAP_DEPTH = normal_scale;
	}
	ROUGHNESS = use_rough ? dot(texture(rough_tex, UV), rough_channel) * roughness : roughness;
	METALLIC = use_metal ? dot(texture(metal_tex, UV), metal_channel) * metallic : metallic;
	RIM = rim_amount;
	RIM_TINT = rim_tint;
	EMISSION = emission;
}
