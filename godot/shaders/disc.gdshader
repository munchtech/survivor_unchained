// The Judgement Disc's head (BattleFx.DiscMesh): a small flat disc of white-gold light with a
// dark steel rim, so the eye can track its head over the pale dead and over lit ground alike.
// Three hot rays on its face turn with it (a plain bright disc never reads as spinning); its
// heart is white, its face the instance's hue (Palette's holy gold; Aegis's ward-blue), and the
// rim is worn dark steel lit by the world, never emissive.
// UV.x: 0 at the centre to 1 at the rim's edge; UV.y: the angle round it, 0..1.
shader_type spatial;
render_mode cull_disabled;

#include "res://shaders/hero_clear.gdshaderinc"

void fragment() {
	float r = UV.x;
	float a = UV.y * 6.2831853;
	float rim = smoothstep(0.76, 0.8, r);
	// The hot edge just inside the steel, where the light meets the rim.
	float lip = smoothstep(0.6, 0.76, r) * (1.0 - rim);
	float rays = pow(max(0.0, cos(a * 3.0)), 10.0) * smoothstep(0.12, 0.45, r) * (1.0 - rim);
	float heart = 1.0 - smoothstep(0.0, 0.32, r);
	float face = (1.0 - rim) * 0.42;
	ALBEDO = mix(vec3(0.0), vec3(0.06, 0.058, 0.055), rim);
	METALLIC = rim * 0.75;
	ROUGHNESS = 0.42;
	SPECULAR = 0.3 * rim;
	vec3 white = vec3(1.0, 0.96, 0.86) * max(COLOR.r, max(COLOR.g, COLOR.b));
	EMISSION = (COLOR.rgb * (face + lip * 0.9) + white * (rays * 0.9 + heart * 1.25)) * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
