// (P9 set) A dial: dark grooves that wake from a centre outward as the handle's k goes 0 -> 1 (the Vault's sigil).
// Dark, the groove's floor is cut stone a shade under the face (barely there); the wake's front runs out along each arm
// hotter than what it leaves lit, so a still mid-wake shows where it has reached (round 2: at k 0.4 the whole of a
// tight shot was already lit, two stills the same).
// (Round 3) The light is written to ALBEDO: the material is unshaded, and an unshaded material's EMISSION never reaches
// the screen (rounds 1-2: the sigil stayed black at every k with the material and k both measured on the mesh). The
// distance is per pixel (the notch's disc has no centre vertex: interpolated, all of it sat at its rim's distance), and
// the wake runs in two legs: the notch over the first `notch_k` of k, then the arms from `inner` (their root, as a
// fraction of `radius`) to their tips over the rest, so k 0.25 and 0.5 show the arms a quarter and a half lit.
shader_type spatial;
render_mode unshaded, cull_back;

uniform vec4 color : source_color = vec4(0.63, 0.44, 1.0, 1.0);
uniform float energy = 3.5;
uniform vec3 center = vec3(0.0);
uniform float radius = 1.0;
uniform float inner = 0.0;
uniform float notch_k = 0.12;
instance uniform float k = 0.0;

varying vec3 local;

void vertex() {
	local = VERTEX;
}

void fragment() {
	float dist = length(local - center) / max(radius, 0.0001);
	float kn = clamp(k / max(notch_k, 0.001), 0.0, 1.0);
	float ka = clamp((k - notch_k) / max(1.0 - notch_k, 0.001), 0.0, 1.0);
	float reach = k < notch_k ? kn * inner : mix(inner, 1.04, ka);
	float lit = smoothstep(dist - 0.04, dist, reach);
	float front = exp(-pow((reach - dist) / 0.06, 2.0)) * step(0.001, k) * (1.0 - smoothstep(0.94, 1.0, k));
	// the cut stone's floor, dark (at 0.022 the night's exposure lifted the dark grooves to a grey-blue line); the wake's
	// violet over it: lit, the brightest channel under 1 (round 3: at 3x it went white through the tonemap, at 1.1 lavender),
	// the front hotter so it blooms
	ALBEDO = vec3(0.008, 0.007, 0.011) + color.rgb * energy * (lit * 0.8 + front * 0.7);
}
