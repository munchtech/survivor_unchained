// (lane E lead 5, 17 Nov) The den elite's outline, shared by its two passes (vat_elite_mask.gdshader, vat_elite_rim.gdshader;
// Vat.Build chains them after each solid surface of a crowd's bake). The crowd's own vertex code (vat.gdshaderinc vertex()):
// the body where the bake puts it this frame. Every instance but a live den elite (class 1 in COLOR.a's 128s, its tint's
// mean at 0.6 or more, not dissolving; vat.gdshaderinc dn_cls, dn_live) is folded to one point outside the view, so the
// passes cost the pack and the boss a vertex read each and draw nothing for them.
uniform sampler2D vat_pos : filter_nearest, repeat_disable;
uniform sampler2D vat_nor : filter_nearest, repeat_disable;
uniform int vat_width = 1;
uniform int vat_rows = 1;
uniform int vat_offset = 0;
global uniform vec4 crowd_den;
global uniform float cel_on;

ivec2 vel_coord(int frame, int vid) {
	int row = vid / vat_width;
	return ivec2(vid - row * vat_width, frame * vat_rows + row);
}

// True for a live den elite; then pos and nor are its posed vertex and normal (model space).
bool vel_pose(int vertex_id, vec4 custom, vec4 color, out vec3 pos, out vec3 nor) {
	pos = vec3(0.0); nor = vec3(0.0, 1.0, 0.0);
	if (!(crowd_den.y > 0.0 && cel_on > 0.0)) return false;
	if (floor(color.a / 128.0) != 1.0) return false;
	if (dot(abs(color.rgb), vec3(0.333)) < 0.6) return false;
	int w = int(custom.w + 0.5);
	if (((w >> 8) & 255) > 0) return false;
	int vid = vat_offset + vertex_id;
	int f0 = int(custom.x + 0.5), f1 = int(custom.y + 0.5);
	pos = mix(texelFetch(vat_pos, vel_coord(f0, vid), 0).xyz, texelFetch(vat_pos, vel_coord(f1, vid), 0).xyz, custom.z);
	nor = normalize(mix(texelFetch(vat_nor, vel_coord(f0, vid), 0).xyz * 2.0 - 1.0, texelFetch(vat_nor, vel_coord(f1, vid), 0).xyz * 2.0 - 1.0, custom.z));
	return true;
}
