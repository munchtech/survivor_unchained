// Sheer hosiery: nearly clear where it is seen straight on, denser where it
// curves away (more threads in the line of sight), so her skin shows through
// the front of her leg and the stocking reads at its edges.
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_never;

uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float face_alpha = 0.12;
uniform float edge_alpha = 0.8;

void fragment() {
	float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	ALBEDO = tint.rgb;
	ROUGHNESS = 0.55;
	SPECULAR = 0.35;
	ALPHA = mix(edge_alpha, face_alpha, pow(facing, 0.6));
}
