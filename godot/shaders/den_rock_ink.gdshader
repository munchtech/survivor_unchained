shader_type spatial;
// (dungeon lead 6, the den's boulders) The silhouette's INK: den_room.png's boulders carry a dark warm-brown line round
// their outline. An inverted hull (front faces culled), each vertex moved out on the screen from the rock's projected
// middle by `px` (at 1080p; a share of the frame's height, so a closer view keeps it as thin), and set `back` m behind its
// surface along the eye's ray, so only what passes the rock's own outline shows. No normals are read: the den rocks are
// star-shaped round their middle (tools/assets/env_rocks.py DEN: an ellipsoid cut by planes, along rays from it), so the
// push from the middle is continuous over their creases, where a push along split normals would crack.
// Chained after the rock's see-through rim pass (DungeonDress.Kit, den only).
render_mode unshaded, cull_front, shadows_disabled, depth_draw_opaque;

uniform vec3 ink_color : source_color = vec3(0.16, 0.12, 0.1);
uniform float px = 2.0;             // the line's width at 1080p
uniform float back = 0.08;          // m behind the surface
uniform vec3 center = vec3(0.0);    // the rock's middle (its mesh's bounds' centre, local)

void vertex() {
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
	ALBEDO = ink_color;
}
