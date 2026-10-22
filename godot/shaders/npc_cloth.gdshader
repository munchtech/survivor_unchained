// A generated NPC package's clothes and gear (Marionette's baked "generated" surface: its colour, its ORM (G rough,
// B metal) and its normal map), drawn as the standard material does, except that light from all round (the sky) comes
// off it warmer (ambient_tint), as on package skin (People.NpcSkin). Without it the town sky's blue turned a deep
// green bodice navy in its shade beside olive where the sun fell, and cream linen's folds blue-gray (Marionette
// lead 12 solver L3, judge r5: "two-tone bodice", "blue-gray streaks"). The tint is taken back out of the lamps' light
// in light(), so the lit side is as before; metal (its B) keeps the sky as it is.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D albedo : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D orm : hint_default_white, filter_linear_mipmap_anisotropic;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic;
uniform bool has_orm = false;
uniform bool has_normal = false;
uniform float rough = 1.0;
uniform float metal = 0.0;
uniform vec3 ambient_tint = vec3(1.0);

varying vec3 tint;

void fragment() {
	vec3 c = texture(albedo, UV).rgb;
	vec3 o = has_orm ? texture(orm, UV).rgb : vec3(1.0);
	METALLIC = clamp(o.b * metal, 0.0, 1.0);
	ROUGHNESS = clamp(o.g * rough, 0.04, 1.0);
	tint = mix(ambient_tint, vec3(1.0), METALLIC);
	ALBEDO = c * tint;
	if (has_normal) NORMAL_MAP = texture(normal_map, UV).rgb;
}

void light() {
	float ndl = clamp(dot(NORMAL, LIGHT), 0.0, 1.0);
	vec3 un = 1.0 / max(tint, vec3(1e-3));
	DIFFUSE_LIGHT += LIGHT_COLOR * ATTENUATION * ndl / PI * un;
	// (the standard material's Schlick-GGX: Trowbridge-Reitz, Smith-Schlick visibility, Schlick Fresnel)
	vec3 h = normalize(VIEW + LIGHT);
	float ndh = clamp(dot(NORMAL, h), 0.0, 1.0), ndv = clamp(dot(NORMAL, VIEW), 1e-3, 1.0), ldh = clamp(dot(LIGHT, h), 0.0, 1.0);
	float a = ROUGHNESS * ROUGHNESS, a2 = a * a;
	float dd = ndh * ndh * (a2 - 1.0) + 1.0, d = a2 / (PI * dd * dd);
	float k = a * 0.5, vis = 0.25 / ((ndl * (1.0 - k) + k) * (ndv * (1.0 - k) + k));
	vec3 f0 = mix(vec3(0.04) * SPECULAR_AMOUNT * 2.0, ALBEDO * un, METALLIC);
	vec3 f = f0 + (1.0 - f0) * pow(1.0 - ldh, 5.0);
	SPECULAR_LIGHT += d * vis * f * ndl * LIGHT_COLOR * ATTENUATION;
}
