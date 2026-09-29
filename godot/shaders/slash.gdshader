// A blade's arc, as the web game draws it (src/render/fx/ribbons.ts, the
// slash): a thin, hot outer edge that leads the swing and a fading wake
// behind it that thins toward the inside. Drawn over the bodies it cuts.
// UV.x runs along the arc, UV.y from the inner edge (0) to the outer (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled, fog_disabled;

uniform float head = 0.0;
uniform float alpha = 1.0;
// The physical school's colours (src/render/fx/palette.ts), linear.
uniform vec3 core = vec3(2.2, 2.03, 1.72);
uniform vec3 glow = vec3(1.4, 0.97, 0.49);

void fragment() {
	float behind = head - UV.x;
	if (behind < -0.02) discard;
	float wake = exp(-max(behind, 0.0) * 5.5);
	float lb = behind * 16.0;
	float lead = exp(-lb * lb);
	float across = UV.y;
	float edge = smoothstep(0.78, 0.97, across) * smoothstep(1.0, 0.97, across);
	float body = pow(across, 2.2) * 0.55;
	float a = (edge * 1.2 + body) * (wake * 0.8 + lead * 0.9);
	ALBEDO = mix(glow, core, edge * (0.4 + lead * 0.6)) * clamp(a * alpha, 0.0, 1.0);
}
