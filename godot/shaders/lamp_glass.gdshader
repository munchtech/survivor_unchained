// A lamp's glass (tools/assets/env_lamps.py, World/Lamps.cs): look bible 10, "the glass doesn't bloom".
// Unshaded, so no light ever drives it past the glow threshold: a faint tint of the flame inside while
// lit (well under 1.0 linear), a fresnel edge of sky at grazing angles, otherwise nearly clear.
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 glow : source_color = vec3(1.0, 0.62, 0.32);
uniform float glow_strength = 0.22;
// How much the lit glass covers what is behind it (the flame's light caught in it).
uniform float lit_alpha = 0.18;
uniform vec3 edge : source_color = vec3(0.30, 0.34, 0.40);
// The fresnel edge's brightness and cover (the ford's big iron, seen from above, shows two panes at a slant over
// every pixel of its cage: at 0.35/0.45 that edge made the whole cage a pale box).
uniform float edge_k = 0.35;
uniform float edge_alpha = 0.45;
instance uniform float lit = 1.0;

void fragment() {
	float f = pow(1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 3.0);
	// Soot toward the top of each pane (UV.y runs down the pane), as a lamp's glass smokes.
	float soot = smoothstep(0.55, 1.0, 1.0 - UV.y);
	vec3 inner = glow * glow_strength * lit * (1.0 - 0.6 * soot);
	ALBEDO = inner + edge * f * edge_k;
	ALPHA = clamp(0.10 + lit_alpha * lit * (1.0 - soot) + edge_alpha * f + 0.25 * soot, 0.0, 0.85);
}
