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
shader_type spatial;
render_mode unshaded, cull_back;

uniform vec4 color : source_color = vec4(0.45, 0.16, 1.0, 1.0);
uniform float energy = 3.5;
uniform vec3 center = vec3(0.0);
uniform float radius = 1.0;
uniform float inner = 0.0;
uniform float notch_k = 0.12;
uniform float arms = 7.0;
uniform float hw = 0.0125;
uniform float vlen = 0.04;
uniform float sock = 0.11;
uniform float lip = 0.2;
uniform float core = 0.9;
uniform float heart = 1.15;
instance uniform float k = 0.0;

varying vec3 local;

void vertex() {
	local = VERTEX;
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
	// across the nearest arm: 0 on its axis, 1 at its lips (the half-width narrowing to the V's point)
	float step_a = 6.2831853 / arms;
	float a = 1.5707963 + round((atan(p.y, p.x) - 1.5707963) / step_a) * step_a;
	vec2 d = vec2(cos(a), sin(a));
	float along = dot(p, d);
	float across = abs(d.x * p.y - d.y * p.x);
	float hwl = max(hw * clamp((radius - along) / max(vlen, 0.001), 0.0, 1.0), 0.0015);
	float u = clamp(across / hwl, 0.0, 1.0);
	float arm = mix(lip, core, exp(-u * u * 5.0));
	// the socket: hot at its heart, falling to its rim (its walls at the rim's level)
	float s = mix(lip * 0.9, heart, exp(-pow(rr / max(sock, 0.001), 2.0) * 5.5));
	float prof = rr < sock + 0.003 ? s : arm;
	ALBEDO = vec3(0.008, 0.007, 0.011) + color.rgb * energy * prof * (lit * 0.8 + front * 0.7);
}
