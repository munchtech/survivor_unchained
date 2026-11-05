// (P9 set) A dial: dark grooves that wake from a centre outward as the handle's k goes 0 -> 1 (the Vault's sigil).
// Dark, the groove's floor is cut stone a shade under the face (barely there); the wake's front runs out along each arm
// hotter than what it leaves lit, so a still mid-wake shows where it has reached (round 2: at k 0.4 the whole of a
// tight shot was already lit, two stills the same).
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
	float reach = k * 1.06;
	float lit = smoothstep(dist - 0.05, dist, reach);
	float front = exp(-pow((reach - dist) / 0.07, 2.0)) * step(0.001, k) * (1.0 - smoothstep(0.96, 1.0, k));
	ALBEDO = vec3(0.025, 0.023, 0.03);
	EMISSION = color.rgb * energy * (lit * 0.8 + front * 1.4);
}
