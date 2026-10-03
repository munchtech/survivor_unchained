// Sheer hosiery: nearly clear where it is seen straight on, denser where it
// curves away (more threads in the line of sight), so her skin shows through
// the front of her leg and the stocking reads at its edges.
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_never;

uniform vec4 tint : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform float face_alpha = 0.12;
uniform float edge_alpha = 0.8;
// How far it stands off her as drawn, beyond what it was made with: sheer,
// it is drawn without writing depth, so wherever her skin, bending a little
// differently in motion, came out past it, her leg showed through as a hole.
uniform float push = 0.003;

void vertex() {
	VERTEX += NORMAL * push;
}

void fragment() {
	float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
	ALBEDO = tint.rgb;
	ROUGHNESS = 0.55;
	SPECULAR = 0.35;
	ALPHA = mix(edge_alpha, face_alpha, pow(facing, 0.6));
}
