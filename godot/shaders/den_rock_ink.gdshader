shader_type spatial;
// (dungeon lead 6, the den's boulders) The silhouette's INK: den_room.png's boulders carry a dark warm-brown line round
// their outline. An inverted hull (front faces culled), each vertex moved out on the screen from the rock's projected
// middle by `px` (at 1080p; a share of the frame's height, so a closer view keeps it as thin), and set `back` m behind its
// surface along the eye's ray, so only what passes the rock's own outline shows. No normals are read: the den rocks are
// star-shaped round their middle (tools/assets/env_rocks.py DEN: an ellipsoid cut by planes, along rays from it), so the
// push from the middle is continuous over their creases, where a push along split normals would crack.
// Chained after the rock's see-through rim pass (DungeonDress.Kit, den only), and cut in the see-through window (below).
render_mode unshaded, cull_front, shadows_disabled, depth_draw_opaque;

uniform vec3 ink_color : source_color = vec3(0.16, 0.12, 0.1);
uniform float px = 2.0;             // the line's width at 1080p
uniform float back = 0.08;          // m behind the surface
uniform vec3 center = vec3(0.0);    // the rock's middle (its mesh's bounds' centre, local)
uniform vec3 box_min = vec3(-1.0);  // its mesh's bounds (local)
uniform vec3 box_max = vec3(1.0);

// (the see-through window, kit.gdshader's see_parts and see_through: where the rock stands before her its front is cut
// round her, and this hull's far side would show through the hole as a dark blot, or darken the window's translucent
// rim. So the hull is cut wherever the rock's front along the same ray would be: that front taken where the ray enters
// the rock's bounds (never behind its true surface, so the cut is never short). The InkPass still draws the
// silhouette there.)
global uniform vec4 survivor;
global uniform vec4 view_from;
varying vec3 v_lpos;
varying flat vec3 v_lcam;

void vertex() {
	v_lpos = VERTEX;
	v_lcam = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	bool ortho = PROJECTION_MATRIX[3][3] != 0.0;
	vec3 ray = ortho ? -INV_VIEW_MATRIX[2].xyz : normalize(w - CAMERA_POSITION_WORLD);
	vec4 clip = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(w + ray * back, 1.0));
	vec4 cc = PROJECTION_MATRIX * (VIEW_MATRIX * (MODEL_MATRIX * vec4(center, 1.0)));
	vec2 d = (clip.xy / clip.w - cc.xy / cc.w) * VIEWPORT_SIZE;
	d = length(d) > 1e-4 ? normalize(d) : vec2(0.0);
	clip.xy += d * (px * (VIEWPORT_SIZE.y / 1080.0) * 2.0) / VIEWPORT_SIZE * clip.w;
	POSITION = clip;
}

void fragment() {
	if (IN_SHADOW_PASS) discard;
	if (survivor.w > 0.0 && view_from.w > 0.0 && distance(CAMERA_POSITION_WORLD, view_from.xyz) <= 1.0) {
		// (the ray's entry into the bounds, local: the slab method)
		vec3 rd = v_lpos - v_lcam;
		vec3 inv = 1.0 / mix(vec3(1e-6), rd, step(vec3(1e-6), abs(rd)));
		vec3 t0 = (box_min - v_lcam) * inv, t1 = (box_max - v_lcam) * inv;
		float tn = max(max(min(t0.x, t1.x), min(t0.y, t1.y)), min(t0.z, t1.z));
		vec3 fw = (MODEL_MATRIX * vec4(v_lcam + clamp(tn, 0.0, 1.0) * rd, 1.0)).xyz;
		vec3 fv = (VIEW_MATRIX * vec4(fw, 1.0)).xyz;
		// (kit.gdshader's see_parts on that front point)
		vec3 her = (VIEW_MATRIX * vec4(survivor.xyz, 1.0)).xyz;
		float open = smoothstep(0.3, 1.3, fv.z - her.z) * smoothstep(0.25, 0.7, fw.y - (survivor.y - 1.1));
		if (open > 0.0) {
			vec4 a = PROJECTION_MATRIX * vec4(fv, 1.0);
			vec4 b = PROJECTION_MATRIX * vec4(her, 1.0);
			vec2 d = a.xy / a.w - b.xy / b.w;
			float fy = abs(PROJECTION_MATRIX[1][1]);
			d.x *= fy / abs(PROJECTION_MATRIX[0][0]);
			if (length(d) * -her.z / fy < 2.5 * open) discard;
		}
	}
	ALBEDO = ink_color;
}
