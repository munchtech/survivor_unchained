// Instanced things that shine (ember stones, coins, flasks, steel in the
// air): lit, their colour the instance's, glowing by `emit` of it.
shader_type spatial;
render_mode cull_back;
// (the material library, godot/data/look/materials.json: this shader's default class, glass: a thing that shines (rule 8: no ink on a source); L1 B2r2)
#define CEL_INK 2
#define CEL_SPEC vec4(6.0, 0.75, 1.0, 0.85)
#define CEL_NO_RIM
#define CEL_EXACT_ROUGH
#include "res://shaders/cel.gdshaderinc"

uniform float emit = 1.0;
uniform float roughness = 0.35;
uniform float metallic = 0.0;

void fragment() {
	ALBEDO = min(COLOR.rgb, vec3(1.0));
	EMISSION = COLOR.rgb * emit;
	ROUGHNESS = roughness;
	METALLIC = metallic;
	CEL_FRAGMENT;
}
