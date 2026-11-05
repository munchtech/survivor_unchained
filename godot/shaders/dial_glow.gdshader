// (P9 set) A dial: dark grooves that wake from a centre outward as the handle's k goes 0 -> 1 (the Vault's sigil).
// Dark, the groove's floor is cut stone a shade under the face (barely there); the wake's front runs out along each arm
// hotter than what it leaves lit, so a still mid-wake shows where it has reached (round 2: at k 0.4 the whole of a
// tight shot was already lit, two stills the same).
// (Round 3) The light is written to ALBEDO: the material is unshaded, and an unshaded material's EMISSION never reaches
// the screen (rounds 1-2: the sigil stayed black at every k with the material and k both measured on the mesh). The
// distance is per pixel (the notch's disc has no centre vertex: interpolated, all of it sat at its rim's distance), and
// the wake runs in two legs: the notch over the first `notch_k` of k, then the arms from `inner` (their root, as a
// fraction of `radius`) to their tips over the rest, so k 0.25 and 0.5 show the arms a quarter and a half lit.
// (C13 set) A cut, not paint: across each arm the light is a hot core line on the groove's axis falling to a dim violet at
// its lips (the perpendicular distance to the nearest of the seven arms' axes over the groove's half-width, narrowing over
// the V notch), and the socket at the centre hot at its heart, falling to its rim; saturated violet (round 3's flat fill
// read lavender through AgX at the night's exposure), the cores bright enough to bloom.
// (C13 set r2) A cut lit from within, not a rod: the mesh is the cut's own walls (door(): each arm a V, the notch a concave
// bowl), lit stone (the moon and the notch light on its walls, no specular: no gloss on the notch) with the glow as
// emission by depth under the face: hot at the floor, dark at the lips, the walls that face up a little hotter (the glow
// pooled in the cut; the crater cue that reads a hollow). Saturated violet at a low energy: the bloom carries the brightness
// (round 1: a hot core across each arm read as an emissive rod, the notch's hot centre as a glossy marble; lavender).
shader_type spatial;
render_mode cull_back, specular_disabled;

uniform vec4 color : source_color = vec4(0.54, 0.11, 1.0, 1.0);
uniform float energy = 1.0;
uniform vec3 center = vec3(0.0);
uniform float radius = 1.0;
uniform float inner = 0.0;
uniform float notch_k = 0.12;
uniform float groove = 0.025;
uniform float socket = 0.05;
uniform float sock = 0.11;
uniform vec4 stone : source_color = vec4(0.03, 0.03, 0.036, 1.0);
instance uniform float k = 0.0;

varying vec3 local;
varying vec3 lnorm;

void vertex() {
	local = VERTEX;
	lnorm = NORMAL;
}

void fragment() {
	vec2 p = local.xy - center.xy;
	float rr = length(p);
	float dist = rr / max(radius, 0.0001);
	float kn = clamp(k / max(notch_k, 0.001), 0.0, 1.0);
	float ka = clamp((k - notch_k) / max(1.0 - notch_k, 0.001), 0.0, 1.0);
	float reach = k < notch_k ? kn * inner : mix(inner, 1.04, ka);
	float lit = smoothstep(dist - 0.04, dist, reach) * step(0.0005, k);
	float front = exp(-pow((reach - dist) / 0.06, 2.0)) * step(0.001, k) * (1.0 - smoothstep(0.94, 1.0, k));
	// depth under the face, as a share of the cut's own (the arms' V, the notch's bowl)
	float full = rr < sock + 0.004 ? socket : groove;
	float d = clamp((center.z - local.z) / max(full, 0.0001), 0.0, 1.0);
	float ramp = d * d * (3.0 - 2.0 * d);
	float up = mix(0.75, 1.15, clamp(lnorm.y * 0.5 + 0.5, 0.0, 1.0));
	ALBEDO = stone.rgb;
	ROUGHNESS = 1.0;
	EMISSION = color.rgb * energy * ramp * up * (lit * 0.8 + front * 0.6);
}
