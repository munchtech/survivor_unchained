// The x-ray's outline (N36 round 4): the next pass of her_xray.gdshader, drawn after every fill (render_priority 1).
// Each of her meshes is grown `rim_px` screen pixels along its normals and drawn only where no fill is (the stencil
// her_xray writes), so a thin cool rim traces her outer silhouette where she is hidden, once (it writes the stencil
// too). The hidden test is her_xray's: something in front of her by more than `near`, outside her own body.
shader_type spatial;
render_mode unshaded, depth_test_disabled, depth_draw_never, cull_disabled, blend_mix, shadows_disabled, fog_disabled;
stencil_mode read, write, compare_not_equal, 7;

global uniform vec4 crowd_den;   // (.y > 0: the den; project global)
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform vec3 rim_tint : source_color = vec3(0.62, 0.80, 1.0);
uniform float rim_alpha = 0.85;
uniform float rim_px = 1.6;
uniform float strength = 0.0;
uniform float strength_ref = 0.6;
uniform float near = 0.15;   // (lane E lead 3: was 0.5; her own body is the mask pass now)
uniform float full = 0.45;   // (was 1.1)
uniform vec3 her_at = vec3(0.0, -1000.0, 0.0);
uniform float her_r = 0.0;   // (lane E lead 3: the capsule is off; was 0.8, it took a slab she stood against for her own body)
uniform float her_top = 2.2;

void vertex() {
	vec4 clip = PROJECTION_MATRIX * MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	vec3 nv = (MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	vec2 dir = (PROJECTION_MATRIX * vec4(nv, 0.0)).xy;
	float l = length(dir);
	if (l > 1e-5) clip.xy += dir / l * rim_px * 2.0 / VIEWPORT_SIZE * clip.w;
	POSITION = clip;
}

void fragment() {
	float d = textureLod(depth_tex, SCREEN_UV, 0.0).r;
	vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
	float scene_z = -v.z / v.w;
	vec3 scene_w = (INV_VIEW_MATRIX * vec4(v.xyz / v.w, 1.0)).xyz;
	vec3 rel = scene_w - her_at;
	float own = (length(rel.xz) < her_r && rel.y > -0.3 && rel.y < her_top) ? 0.0 : 1.0;
	float occ = smoothstep(near, full, -VERTEX.z - scene_z) * own;
	if (occ <= 0.001) discard;
	vec3 tint = rim_tint; float ra = rim_alpha;
	// den: warm, quiet x-ray so the boss reads solid; lane E 16 Nov
	if (crowd_den.y > 0.0) { tint = pow(vec3(0.95, 0.78, 0.52), vec3(2.2)); ra = 0.75; }
	ALBEDO = tint;
	ALPHA = clamp(occ * (strength / strength_ref) * ra, 0.0, 1.0);
}
