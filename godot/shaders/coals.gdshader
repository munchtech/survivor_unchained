// A fire's bed of coals and the burnt ends of its sticks. Charcoal is near
// black and crazed into small blocks; where it still burns it glows from
// inside, deep red to orange, brightest down in the gaps between lumps and
// along the cracks, while what faces up has crusted over with grey and white
// ash. The glow breathes, slowly, a patch at a time, as air reaches it.
// Toward the rim the sticks are wood that has not caught. Places are the
// fire's own (object space, metres from its middle), so the pattern holds
// still as the camera moves.
shader_type spatial;
render_mode blend_mix, cull_back;

uniform float heat : hint_range(0.0, 2.0) = 1.0;
uniform float size = 1.0;
uniform vec3 char_col : source_color = vec3(0.03, 0.027, 0.025);
uniform vec3 ash_col : source_color = vec3(0.30, 0.29, 0.28);
uniform vec3 wood_col : source_color = vec3(0.16, 0.11, 0.075);

varying vec3 lp;
varying vec3 ln;

void vertex() {
	lp = VERTEX / size;
	ln = NORMAL;
}

float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

float noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), u.x), mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), u.x), u.y),
		mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), u.x), mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), u.x), u.y), u.z);
}

float fbm3(vec3 p) { return noise3(p) * 0.5 + noise3(p * 2.1 + 3.7) * 0.3 + noise3(p * 4.3 + 9.1) * 0.2; }

// The crazing: how near a point is to the edge between two blocks (0 on it).
float craze(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) for (int z = -1; z <= 1; z++) {
		vec3 g = vec3(float(x), float(y), float(z));
		vec3 o = vec3(hash3(i + g), hash3(i + g + 19.1), hash3(i + g + 47.7));
		float d = length(g + o - f);
		if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d;
	}
	return d2 - d1;
}

// Blackbody, roughly: dull red, orange, and yellow only at the hottest.
vec3 glow(float t) {
	vec3 c = mix(vec3(0.45, 0.03, 0.0), vec3(1.0, 0.22, 0.02), smoothstep(0.0, 0.55, t));
	return mix(c, vec3(1.0, 0.55, 0.16), smoothstep(0.7, 1.0, t));
}

void fragment() {
	float r = length(lp.xz);
	// How burnt: all of it near the middle, none past the stones' inner edge.
	float burnt = 1.0 - smoothstep(0.24, 0.4, r + (noise3(lp * 9.0) - 0.5) * 0.08);
	float t = TIME;
	// Where the air reaches: slow patches that come and go, and a faster shimmer.
	float breath = smoothstep(0.3, 0.75, fbm3(lp * 8.0 + vec3(0.0, t * 0.18, t * 0.11)));
	float shimmer = 0.85 + 0.15 * noise3(lp * 30.0 + vec3(t * 1.7, 0.0, t * 1.1));
	// Fine cracks, in some places and not others.
	vec3 w = lp * 70.0 + vec3(fbm3(lp * 20.0), fbm3(lp * 20.0 + 5.0), 0.0) * 1.2;
	float crack = (1.0 - smoothstep(0.015, 0.07, craze(w))) * smoothstep(0.35, 0.6, noise3(lp * 14.0 + 2.0));
	// Down in the gaps and on the undersides you see into the fire.
	float gap = 1.0 - smoothstep(-0.2, 0.75, ln.y);
	// The ash: grey crust on what faces up, thickest where it has burnt longest
	// and gone cold; little on the hottest patches.
	float up = smoothstep(0.1, 0.85, ln.y);
	float ash = up * smoothstep(0.38, 0.7, fbm3(lp * 22.0)) * (0.35 + 0.65 * (1.0 - breath));
	ash = clamp(ash + smoothstep(0.22, 0.36, r) * up * 0.5, 0.0, 1.0);
	vec3 c = mix(char_col * (0.7 + 0.6 * noise3(lp * 90.0)), ash_col * (0.6 + 0.6 * noise3(lp * 60.0)), ash);
	c = mix(wood_col * (0.7 + 0.5 * noise3(vec3(lp.x * 6.0, lp.y * 60.0, lp.z * 6.0))), c, burnt);
	ALBEDO = c;
	ROUGHNESS = 0.92;
	float core = 1.0 - smoothstep(0.05, 0.34, r);
	float hot = (0.18 + 0.82 * breath) * (0.35 + 0.65 * core) * (0.25 + 0.75 * gap + 0.9 * crack);
	hot *= (1.0 - ash * 0.9) * burnt * heat * shimmer;
	hot = clamp(hot, 0.0, 1.0);
	// The coals light each other and the ash between them (their fire's
	// lights leave them out): a warm wash, strongest in the middle.
	vec3 bounce = c * vec3(1.0, 0.42, 0.14) * 0.9 * (1.0 - smoothstep(0.08, 0.42, r)) * heat;
	EMISSION = glow(hot) * hot * 2.6 + bounce;
}
