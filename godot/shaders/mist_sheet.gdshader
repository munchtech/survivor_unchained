// Mist lying low along a stream (View/ArenaEdge.cs): a sheet a little over
// the water, torn by a slow noise and drifting, thickest over the middle and
// gone before the sheet's edge, fading where it meets the ground so it has
// no edge of its own. Seen from above it softens the stream's banks into the
// litter and gives the cold air a body.
// UV: x metres across from the middle, y metres along; UV2.x 0 at the
// sheet's edge, 1 in its middle.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear;
uniform vec3 mist : source_color = vec3(0.45, 0.52, 0.55);
uniform float opacity = 0.32;
uniform float drift = 0.02;

void fragment() {
	vec2 p = vec2(UV.x * 0.06, UV.y * 0.025) + vec2(TIME * drift * 0.3, -TIME * drift);
	float n = texture(noise_tex, p).g * 0.6 + texture(noise_tex, p * 2.6 + vec2(0.3, TIME * drift * 0.7)).b * 0.4;
	float body = smoothstep(0.35, 0.75, n) * smoothstep(0.0, 0.7, UV2.x);
	float depth = texture(depth_tex, SCREEN_UV).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	float behind = -v.z / v.w + VERTEX.z;
	body *= smoothstep(0.0, 1.2, behind);
	ALBEDO = mist * (0.8 + 0.4 * n);
	ALPHA = clamp(body * opacity, 0.0, 1.0);
}
