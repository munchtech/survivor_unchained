// A blade's arc: a band sweeping round, its head bright, fading behind it,
// brightest at the outer edge where the steel moves fastest (the web game's
// slash ribbon, src/render/fx/ribbons.ts). UV.x runs along the arc, UV.y from
// the inner edge (0) to the outer (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

uniform float head = 0.0;
uniform float alpha = 1.0;
uniform vec3 core : source_color = vec3(1.0, 0.95, 0.85);
uniform vec3 glow : source_color = vec3(1.0, 0.55, 0.2);

void fragment() {
	float behind = head - UV.x;
	float trail = smoothstep(-0.02, 0.04, behind) * (1.0 - smoothstep(0.0, 0.6, behind));
	float edge = UV.y;
	vec3 c = mix(glow * 1.6, core * 3.2, pow(edge, 4.0));
	ALBEDO = c;
	ALPHA = clamp(trail * (0.12 + 0.88 * pow(edge, 2.0)) * alpha, 0.0, 1.0);
}
