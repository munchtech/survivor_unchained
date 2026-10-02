// A blade's arc: a crescent, thick in the middle of the swing and tapering
// to points at either end, with a white-hot cutting edge on the outside that
// leads, a coloured body that fades behind it, and streaks drawn along the
// swing so it reads as speed rather than as a painted fan. Drawn over the
// bodies it cuts. UV.x runs along the arc, UV.y from the inner edge (0) to
// the outer (1).
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled, fog_disabled;

uniform float head = 0.0;
uniform float alpha = 1.0;
uniform float seed = 0.0;
// The physical school's colours (src/render/fx/palette.ts), linear.
uniform vec3 core = vec3(2.2, 2.03, 1.72);
uniform vec3 glow = vec3(1.4, 0.97, 0.49);

float hash(float n) { return fract(sin(n * 91.345 + seed * 17.13) * 47453.5453); }
float streaks(float y) {
	// Lines along the swing: a few bright, many faint, at random depths.
	float n = y * 34.0;
	float i = floor(n), f = fract(n);
	float a = mix(hash(i), hash(i + 1.0), smoothstep(0.0, 1.0, f));
	return 0.45 + 0.75 * pow(a, 2.0);
}

void fragment() {
	float behind = head - UV.x;
	if (behind < -0.015) discard;
	// The crescent: how far in from the outer edge the blade's wake reaches,
	// most at the middle of the swing.
	float bulge = sin(clamp(UV.x, 0.0, 1.0) * PI);
	float inner = 1.0 - (0.2 + 0.8 * bulge);
	float across = clamp((UV.y - inner) / max(1.0 - inner, 0.001), 0.0, 1.0);
	if (UV.y < inner) discard;
	float wake = exp(-max(behind, 0.0) * 4.5);
	float lb = behind * 14.0;
	float lead = exp(-lb * lb);
	float edge = smoothstep(0.72, 0.96, across) * smoothstep(1.0, 0.975, across);
	float body = pow(across, 1.8) * 0.9 * streaks(UV.y + behind * 0.15);
	float ends = smoothstep(0.0, 0.08, UV.x) * smoothstep(1.0, 0.92, UV.x);
	float a = (edge * 2.4 + body) * (wake * 0.85 + lead * 1.3) * ends;
	vec3 col = mix(glow, core, clamp(edge * (0.5 + lead * 0.8) + lead * 0.3, 0.0, 1.0));
	ALBEDO = col * 1.6 * clamp(a * alpha, 0.0, 2.5);
}
