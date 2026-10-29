// The soft light round the Warden's lamp flame (LampIron.cs): a camera-facing card, added, a Gaussian
// that is nothing well inside the card's edge (the old halo's hard disc), and faded wherever it nears
// something solid (the cage's bars through it), so it never shows a line. Unshaded; the post glow does
// the rest.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec3 color = vec3(0.35, 0.6, 1.0);
uniform float strength = 0.35;
// Falloff: e^(-k r^2), r = 1 at the card's edge.
uniform float k = 9.0;
uniform float soft = 0.06;

void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0), vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec2 q = UV * 2.0 - 1.0;
	float r2 = dot(q, q);
	float g = exp(-k * r2) * (1.0 - smoothstep(0.55, 1.0, r2));
	float depth = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	behind.xyz /= behind.w;
	float fade = clamp((VERTEX.z - behind.z) / soft, 0.0, 1.0);
	ALBEDO = color * strength * g * fade;
}
