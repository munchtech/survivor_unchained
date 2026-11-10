// Blood in the air (Fx/BloodDrops.cs; L1 lead 9 B6): droplets and strokes in the FX language, never the round
// 2-3 px dots that read as pepper (P7's judge, round 2). Each is a quad along its own velocity, turned to face the
// camera (spark.gdshader's streak). Two shapes:
//   a droplet: a teardrop, its round head leading, its tail thinning behind;
//   a stroke: the painted-stroke primitive (fx_cel.gdshaderinc fx_stroke), a cut's fling of blood.
// Both in three stepped bands, hard with a narrow soft edge (LOOK_BIBLE rule 13's bands, in matter's color): a deep
// edge, the body, a small wet light near the head. Blood is matter, not light (FX_LANGUAGE "Matter"): mixed, never
// added, no glow, and drawn before the spells (a negative render priority, set by BloodDrops) so a spell's light lies
// over it, as rule 13 wants the spell the most saturated thing in its frame. Transparent, so it writes nothing to the
// ink pass's roughness byte (rule 8: FX class 2, no ink).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/fx_cel.gdshaderinc"

// The bands' colors (linear), times the instance's body color over the red's own body (so an ichor's or a lampling's
// blood keeps its family): edge, body, light.
uniform vec3 band_edge : source_color = vec3(0.23, 0.024, 0.02);
uniform vec3 band_body : source_color = vec3(0.56, 0.05, 0.045);
uniform vec3 band_light : source_color = vec3(0.80, 0.26, 0.18);
// The droplet's bands, in its normalized distance from its centerline (0) to its rim (1): the edge band from, the
// light's radius (round the head's light point).
uniform vec2 drop_bands = vec2(0.62, 0.34);

varying vec4 tint;
varying float kind;
varying float life;
varying float aspect;

void vertex() {
	tint = COLOR;
	kind = INSTANCE_CUSTOM.x;
	life = INSTANCE_CUSTOM.y;
	float s = length(MODEL_MATRIX[0].xyz);
	vec3 ax = MODEL_MATRIX[1].xyz;
	vec3 to_cam = normalize(INV_VIEW_MATRIX[3].xyz - MODEL_MATRIX[3].xyz);
	// (the axis as the camera sees it: what is foreshortened end-on keeps at least its width, a round drop)
	vec3 axs = ax - to_cam * dot(ax, to_cam);
	vec3 side = cross(ax, to_cam);
	side = length(side) > 1e-5 ? normalize(side) : INV_VIEW_MATRIX[0].xyz;
	float len = max(length(axs), s * 1.25);
	vec3 dir = length(axs) > 1e-5 ? normalize(axs) : INV_VIEW_MATRIX[1].xyz;
	aspect = len / max(s, 1e-5);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(vec4(side * s, 0.0), vec4(dir * len, 0.0), vec4(to_cam * s, 0.0), MODEL_MATRIX[3]);
}

void fragment() {
	// across -1..1 over the width; along 1 at the head (the quad's top, the leading end) and 0 at the tail
	float across = UV.x * 2.0 - 1.0;
	float along = 1.0 - UV.y;
	vec3 body_k = tint.rgb / max(band_body, vec3(1e-3));
	float a;
	vec3 c;
	if (kind < 0.5) {
		// The teardrop, in units of the half-width: the head a circle of radius 1 at the leading end, the tail a
		// curved taper to a point.
		float y = (1.0 - along) * aspect * 2.0;            // 0 at the head's tip, back toward the tail
		float tail = max(aspect * 2.0 - 1.0, 1e-3);
		float h = y < 1.0 ? sqrt(max(0.0, 1.0 - (1.0 - y) * (1.0 - y))) : pow(clamp(1.0 - (y - 1.0) / tail, 0.0, 1.0), 1.35);
		float d = abs(across) / max(h, 1e-4);
		a = 1.0 - fx_hard(1.0, d, 0.0);
		// the edge band round the rim and down the thin tail; the light a small spot on the head, set toward the sky
		float edge = max(fx_hard(drop_bands.x, d, 0.02), fx_hard(0.72, (y - 1.0) / tail, 0.02));
		vec2 lp = vec2(across + 0.32, y - 0.78);
		float light = 1.0 - fx_hard(drop_bands.y, length(lp * vec2(1.0, 1.25)), 0.02);
		c = mix(mix(band_body, band_edge, edge), band_light, light * (1.0 - edge));
	} else {
		// The stroke: fx_stroke's own shape, bristles and steps, its bands read back as levels (fx_edge 0, fx_mid
		// 0.5, fx_core 1, set by BloodDrops) and painted in blood's three; no glow.
		vec4 s = fx_stroke(across, along, life);
		float lv = s.r;
		c = lv < 0.25 ? band_edge : lv < 0.75 ? band_body : band_light;
		a = s.a;
	}
	ALBEDO = c * body_k;
	ALPHA = a * tint.a;
}
