// Her silhouette through what stands between the play camera and her (H1 round 2C, the round-1 judge's "never hide
// her"): laid over her solid meshes as a MaterialOverlay (PlayerView.Xray). Drawn over everything (no depth test), it
// shows only where the scene's depth lies well in front of her own surface: a flat ember gold with a fresnel rim.
// Where she is in plain sight the scene's depth is her own (the difference under `near`), so nothing is drawn; the
// half metre also covers her own parts crossing each other (an arm over her chest). `strength` is 0 outside play.
// H8 (N36, the owner on demo-rc2: "my legs shining through my body while running"): a stride puts a leg more than
// half a metre behind her torso, so what hides a fragment counts only if it stands outside her own body: the scene's
// point is rebuilt in the world and dropped when it lies in an upright capsule round her (`her_at`, her feet, set by
// PlayerView each frame; `her_r` across, `her_top` up). A roof, a wall or a tree in front of her still shows her.
// N36 round 4 (the judge on the gatehouse frame: "an opaque, warm-cream lump ... dithered, grainy edges"): the
// overlay rides on every solid mesh of hers (body, each outfit layer) and draws with no depth test, so where layers
// stack (skin under cloth, both arms) it blended two to four times, each with its own fresnel: the stack made it
// opaque, and which layer's triangle landed last changed pixel by pixel, the grain. The stencil now lets one fragment
// per pixel through (the first writes `stencil_ref`, the rest fail), so it is one see-through layer. The look is the
// ARPG wall x-ray (Diablo IV, Path of Exile): a faint cool fill with a soft top light so head and shoulder still read,
// and a thin moonlight outline that carries her in the dark. The outline is its own pass (her_xray_rim.gdshader, the
// material's next pass, drawn after every fill): her meshes grown a pixel or two along their normals, drawn only where
// no fill is (the stencil), so it traces her outer silhouette once instead of every layer's edge (the first try put
// a fresnel rim in the fill: each layer's and fold's grazing edge lit up inside her, a scribble).
shader_type spatial;
render_mode unshaded, depth_test_disabled, depth_draw_never, cull_back, blend_mix, shadows_disabled, fog_disabled;
stencil_mode read, write, compare_not_equal, 7;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec3 fill_tint : source_color = vec3(0.13, 0.19, 0.30);
uniform float fill_alpha = 0.50;
uniform float strength = 0.0;
uniform float strength_ref = 0.6;
uniform float near = 0.5;
uniform float full = 1.1;
uniform vec3 her_at = vec3(0.0, -1000.0, 0.0);
uniform float her_r = 0.8;
uniform float her_top = 2.2;

void fragment() {
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -v.z / v.w;
	vec3 scene_w = (INV_VIEW_MATRIX * vec4(v.xyz / v.w, 1.0)).xyz;
	vec3 rel = scene_w - her_at;
	float own = (length(rel.xz) < her_r && rel.y > -0.3 && rel.y < her_top) ? 0.0 : 1.0;
	float occ = smoothstep(near, full, -VERTEX.z - scene_z) * own;
	if (occ <= 0.001) discard;
	float fres = 1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	float lit = 0.6 + 0.55 * clamp(dot(NORMAL, normalize(vec3(-0.35, 0.85, 0.4))), 0.0, 1.0) + 0.25 * fres * fres;
	ALBEDO = fill_tint * lit;
	ALPHA = clamp(occ * (strength / strength_ref) * fill_alpha, 0.0, 1.0);
}
