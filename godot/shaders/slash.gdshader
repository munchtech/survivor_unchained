// A blade's arc: a thin crescent of light at the edge the steel travels,
// its head bright, fading behind it over the sweep (the web game's slash
// ribbon, src/render/fx/ribbons.ts). UV.x runs along the arc, UV.y from the
// inner edge (0) to the outer (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float head = 0.0;
uniform float alpha = 1.0;
uniform vec3 core : source_color = vec3(1.0, 0.95, 0.85);
uniform vec3 glow : source_color = vec3(1.0, 0.55, 0.2);

void fragment() {
	float behind = head - UV.x;
	// Bright at the head, a tail behind it.
	float trail = smoothstep(-0.015, 0.02, behind) * pow(1.0 - clamp(behind / 0.7, 0.0, 1.0), 2.0);
	// A thin edge of light at the outside, a faint smear inside it.
	float edge = smoothstep(0.55, 0.97, UV.y) * (1.0 - smoothstep(0.97, 1.0, UV.y));
	float smear = smoothstep(0.1, 0.9, UV.y) * 0.18;
	float k = trail * (edge + smear) * alpha;
	ALBEDO = mix(glow * 0.8, core * 2.4, edge) * k;
	ALPHA = 1.0;
}
