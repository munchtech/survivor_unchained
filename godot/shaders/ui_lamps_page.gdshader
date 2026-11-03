// The Lamps board's page (src/Ui/LampBoard.cs), under the roads: C's warm glow under the lit cluster (§16: 15%,
// #ffcf86, about 1.6x the cluster's bbox) and, at the Valley, the three faint guides (§16 A4: 1 px, #d8cfbd at 18%).
// Coordinates are the rect's local px.
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform vec2 size = vec2(846.0, 642.0);
uniform vec2 glow_c = vec2(423.0, 321.0);
uniform vec2 glow_r = vec2(200.0, 160.0);
uniform float glow_a = 0.15;
uniform float glow_feather = 24.0;
uniform vec2 ring_c = vec2(423.0, 321.0);
uniform vec3 rings = vec3(0.0);          // radii px; 0 = off
uniform float ring_a = 0.18;
uniform float feather = 48.0;

void fragment() {
	vec2 p = UV * size;
	float rr = length((p - glow_c) / max(glow_r, vec2(1.0)));
	float ef = smoothstep(0.0, glow_feather, p.x) * smoothstep(0.0, glow_feather, size.x - p.x)
		* smoothstep(0.0, glow_feather, p.y) * smoothstep(0.0, glow_feather, size.y - p.y);
	float g = (1.0 - smoothstep(0.0, 1.0, rr)) * glow_a * ef;
	vec3 light = vec3(1.0, 0.812, 0.525) * g;
	float d = length(p - ring_c);
	float ra = 0.0;
	for (int k = 0; k < 3; k++) {
		float r = rings[k];
		if (r > 0.5) ra = max(ra, clamp(0.5 - (abs(d - r) - 0.5), 0.0, 1.0));
	}
	float wf = smoothstep(0.0, feather, p.x) * smoothstep(0.0, feather, size.x - p.x)
		* smoothstep(0.0, feather, p.y) * smoothstep(0.0, feather, size.y - p.y);
	ra *= ring_a * wf;
	COLOR = vec4(vec3(0.847, 0.812, 0.741) * ra + light, ra);
}
