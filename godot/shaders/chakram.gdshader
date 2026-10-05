// Gale Chakram's blade (BattleFx.ChakramMesh): dark steel, lit by the world, its five hooked
// edges honed bright in the instance's colour (the wind's, the frost's, the blood's), a faint
// lip round its hole. Read as a thrown blade by its edges, never as a ring of light: a pale
// ring, two in flight, read as a pair of handcuffs.
// UV.x: 0 at the hole to 1 at the edge, whatever the edge's shape.
shader_type spatial;
render_mode cull_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

void fragment() {
	float r = UV.x;
	float hone = smoothstep(0.78, 0.97, r);
	float lip = 1.0 - smoothstep(0.0, 0.1, r);
	ALBEDO = vec3(0.13, 0.14, 0.15) * (1.0 - hone * 0.6);
	METALLIC = 0.85;
	ROUGHNESS = 0.3;
	EMISSION = COLOR.rgb * (hone * 1.1 + lip * 0.18) * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
