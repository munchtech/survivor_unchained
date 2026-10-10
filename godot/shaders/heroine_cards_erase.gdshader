// Drawn last over her blended lashes and brow cards (src/Actors/HairDraw.cs):
// the colour left as it is (multiplied by white) and the alpha, which Godot
// hands FSR 2 as its reactive mask, multiplied by `keep` (as heroine_hair_erase).
shader_type spatial;
render_mode blend_mul, unshaded, fog_disabled, depth_draw_never, cull_disabled;

uniform float keep = 0.0;

void fragment() {
	ALBEDO = vec3(1.0);
	ALPHA = keep;
}
