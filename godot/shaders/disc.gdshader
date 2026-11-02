// The Judgement Disc's head (BattleFx.DiscMesh), flat in the ground's plane, its mesh 1.6x the disc's
// radius so it carries its own halo. From the centre out:
//   the core: white-hot, 2-3x the old heart, fading into the face's hue;
//   the face: the instance's hue (holy gold; Aegis's ward-blue; Reckoning's deeper gold), crossed by
//     angular motion-blur smears (three arcs at different radii, each bright at its leading end and
//     fading round behind it: the eye reads a blur of a turning blade, never spokes or rays);
//   the rim: bright worn steel, 13% of the radius, lit by the world, a smeared glint running round it;
//   the halo: a soft glow from the rim out to 1.6x the radius (light only: premultiplied, alpha 0).
// The disc spins by its instance's basis (BattleFx.DiscFlight: world angle = local angle + spin),
// so the smears' leading ends are at their larger angle.
// UV.x: 0 at the centre to 1 at the halo's edge; UV.y: the angle round it, 0..1.
shader_type spatial;
render_mode blend_premul_alpha, cull_disabled, depth_draw_never;

#include "res://shaders/hero_clear.gdshaderinc"

const float DISC_EDGE = 0.625;   // the disc's edge in UV.x (1 / 1.6)
const float DISC_RIM = 0.87;     // the steel band's inner edge, as a share of the disc's radius

float smear(float a, float r, float at, float wid, float off, float turns) {
	float band = 1.0 - smoothstep(0.0, wid, abs(r - at));
	float s = fract(a * turns + off);
	return band * pow(s, 2.2) * smoothstep(1.0, 0.92, s);
}

void fragment() {
	float r = UV.x / DISC_EDGE;            // 0..1 across the disc, 1..1.6 over the halo
	float a = UV.y;
	float inside = 1.0 - smoothstep(0.985, 1.0, r);
	float rim = smoothstep(DISC_RIM - 0.015, DISC_RIM, r) * inside;
	float face = inside * (1.0 - rim);
	float lum = max(COLOR.r, max(COLOR.g, COLOR.b));
	vec3 white = vec3(1.0, 0.95, 0.84) * lum;

	float core = exp(-pow(r / 0.3, 2.0));
	float blur = smear(a, r, 0.42, 0.075, 0.0, 1.0) + smear(a, r, 0.62, 0.07, 0.37, 1.0) + 0.8 * smear(a, r, 0.78, 0.06, 0.71, 2.0);
	vec3 faceE = COLOR.rgb * (0.95 + 0.35 * (1.0 - r)) + white * (core * 3.2 + blur * 1.5);

	// The steel: bright, worn, its glint smeared round with the turn.
	float glint = pow(fract(a * 2.0 + 0.15), 4.0) * smoothstep(1.0, 0.94, fract(a * 2.0 + 0.15));
	vec3 rimE = COLOR.rgb * 0.18 + white * glint * 0.9;

	// The halo: from the rim's edge out to 1.6x, soft.
	float h = 1.0 - smoothstep(1.0, 1.6, r);
	vec3 haloE = COLOR.rgb * (h * h * 0.85) * (1.0 - inside);

	ALBEDO = vec3(0.5, 0.5, 0.52) * rim;
	METALLIC = rim;
	ROUGHNESS = mix(1.0, 0.28, rim);
	SPECULAR = 0.5 * rim;
	ALPHA = inside;
	EMISSION = (faceE * face + rimE * rim + haloE) * hero_clear(VERTEX, VIEW_MATRIX, PROJECTION_MATRIX, VIEWPORT_SIZE);
}
