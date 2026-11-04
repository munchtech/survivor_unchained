// Her silhouette through what stands between the play camera and her (H1 round 2C, the round-1 judge's "never hide
// her"): laid over her solid meshes as a MaterialOverlay (PlayerView.Xray). Drawn over everything (no depth test), it
// shows only where the scene's depth lies well in front of her own surface: a flat ember gold with a fresnel rim.
// Where she is in plain sight the scene's depth is her own (the difference under `near`), so nothing is drawn; the
// half metre also covers her own parts crossing each other (an arm over her chest). `strength` is 0 outside play.
shader_type spatial;
render_mode unshaded, depth_test_disabled, depth_draw_never, cull_back, blend_mix, shadows_disabled, fog_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec4 tint : source_color = vec4(1.0, 0.72, 0.36, 1.0);
uniform float strength = 0.0;
uniform float near = 0.5;
uniform float full = 1.1;

void fragment() {
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -v.z / v.w;
	float occ = smoothstep(near, full, -VERTEX.z - scene_z);
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALBEDO = tint.rgb * (0.75 + 0.6 * fres);
	ALPHA = clamp(occ * strength * (0.55 + 0.45 * fres), 0.0, 1.0);
}
