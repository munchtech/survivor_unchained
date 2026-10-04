// The smoke off an ember arena's ring (View/ArenaEdge.cs): a low curtain all
// the way round just past the edge, rising and thinning, lit from below by
// the char's glow; it takes the place beyond into the dark without a wall.
// UV: x metres round the ring, y 0 at the foot to 1 at the top.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
uniform vec3 ember : source_color = vec3(1.0, 0.35, 0.13);
uniform vec3 smoke : source_color = vec3(0.1, 0.09, 0.08);
uniform float opacity = 0.62;

void fragment() {
	float y = UV.y;
	vec2 p = vec2(UV.x * 0.08, y * 0.5 - TIME * 0.035);
	float n = texture(noise_tex, p).g * 0.6 + texture(noise_tex, p * 2.7 + vec2(TIME * 0.01, -TIME * 0.05)).b * 0.4;
	float body = smoothstep(0.25, 0.75, n + 0.25 - y * 0.55);
	float a = body * (1.0 - smoothstep(0.05, 0.95, y)) * opacity;
	// Where it meets the ground it fades into it (by depth, a metre and a
	// half), so its foot is never drawn as a line along the ring.
	float depth = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	float behind = -v.z / v.w - (-VERTEX.z);
	a *= smoothstep(0.0, 1.5, behind);
	// Lit from below, only just: a warm breath at the foot, the smoke dark
	// above. Seen from the camera the curtain lies past the lip as a band of
	// torn shapes; any light in them and they read as flames on the ground.
	float lit = pow(1.0 - y, 10.0) * (0.6 + 0.4 * sin(TIME * 0.8 + UV.x * 0.13));
	ALBEDO = smoke * 0.6 + ember * lit * 0.04;
	ALPHA = clamp(a, 0.0, 1.0);
}
