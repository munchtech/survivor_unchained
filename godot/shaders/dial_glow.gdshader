// (P9 set) A dial: dark grooves that wake from a centre outward as the handle's k goes 0 -> 1 (the Vault's sigil).
shader_type spatial;
render_mode unshaded, cull_back;

uniform vec4 color : source_color = vec4(0.63, 0.44, 1.0, 1.0);
uniform float energy = 3.5;
uniform vec3 center = vec3(0.0);
uniform float radius = 1.0;
instance uniform float k = 0.0;

varying float dist;

void vertex() {
	dist = length(VERTEX - center) / max(radius, 0.0001);
}

void fragment() {
	ALBEDO = vec3(0.02, 0.018, 0.025);
	EMISSION = color.rgb * energy * smoothstep(dist - 0.08, dist, k * 1.08);
}
