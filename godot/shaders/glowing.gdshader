// Instanced things that shine (ember stones, coins, flasks, steel in the
// air): lit, their colour the instance's, glowing by `emit` of it.
shader_type spatial;
render_mode cull_back;

uniform float emit = 1.0;
uniform float roughness = 0.35;
uniform float metallic = 0.0;

void fragment() {
	ALBEDO = min(COLOR.rgb, vec3(1.0));
	EMISSION = COLOR.rgb * emit;
	ROUGHNESS = roughness;
	METALLIC = metallic;
}
