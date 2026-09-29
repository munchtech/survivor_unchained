// What glows by itself and takes no light: a lantern's flame, the coals in a
// brazier, a campfire's bed (the web game's MeshBasicMaterial, its colour
// brighter than white so the bloom takes it). The colour is linear, as the
// web game's is. The additive variant (light spilled from a doorway onto
// the ground) is this with blend_add (World/Landmarks.cs).
shader_type spatial;
render_mode unshaded, cull_back, depth_draw_opaque;

uniform vec3 color = vec3(1.0);
uniform sampler2D tex : source_color, filter_linear_mipmap, hint_default_white;
uniform float opacity = 1.0;

void fragment() {
	vec4 t = texture(tex, UV);
	ALBEDO = color * t.rgb;
	ALPHA = t.a * opacity;
}
