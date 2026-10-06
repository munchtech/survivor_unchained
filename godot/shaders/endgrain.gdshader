// The sawn end of a log left out a season or two: growth rings about the
// pith, pale early wood and darker late wood, the heartwood warmer, greyed
// by the weather toward the rim; checks split in from the bark where the
// wood dried; a band of bark round the edge, uneven; faint kerf marks across
// it all. UV is the face's plane in metres from the pith, so the rings are
// true to size on any log; UV2.x runs from the axis (0) to the bark (1),
// and UV2.y is the face's own seed (Camp.cs).
shader_type spatial;
render_mode blend_mix, cull_back;

uniform float rings_per_m = 150.0;
uniform float bark_width = 0.02;
uniform float weather = 0.45;
uniform vec3 early : source_color = vec3(0.52, 0.44, 0.34);
uniform vec3 late : source_color = vec3(0.34, 0.25, 0.18);
uniform vec3 heart : source_color = vec3(0.46, 0.32, 0.21);
uniform vec3 grey : source_color = vec3(0.36, 0.34, 0.31);
uniform vec3 bark : source_color = vec3(0.16, 0.115, 0.085);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) { return noise(p) * 0.55 + noise(p * 2.03 + 7.1) * 0.28 + noise(p * 4.11 + 3.3) * 0.17; }

// Everything about a point of the face: its colour (rgb) and how deep it is (a).
vec4 face(vec2 p, float fr, float sd) {
	// Each face its own: the seed moves every pattern somewhere else.
	vec2 so = vec2(sd * 13.7, sd * 7.3);
	float r = length(p);
	float ang = atan(p.y, p.x);
	// How far the bark is here, along this line from the pith.
	float rim = r / max(fr, 0.02);
	// The rings wander: a slow wobble round the tree and a finer one.
	float wob = (fbm(vec2(cos(ang), sin(ang)) * 2.0 + so) - 0.5) * 0.010 + (noise(p * 60.0 + so) - 0.5) * 0.0025;
	float f = (r + wob) * rings_per_m;
	float w = fract(f);
	// Late wood: a narrow dark band at the end of each year, some years wider.
	float yr = hash(vec2(floor(f), 3.0) + so);
	float lw = smoothstep(0.62 - 0.18 * yr, 0.9, w) * (1.0 - smoothstep(0.96, 1.0, w));
	vec3 c = mix(early, late, lw * 0.85);
	c = mix(c, c * heart / early, (1.0 - smoothstep(0.42, 0.6, fr)) * 0.7);
	// The weather greys the face, more toward the rim, in blotches.
	float g = weather * (0.45 + 0.55 * smoothstep(0.2, 1.0, fr)) * (0.6 + 0.6 * fbm(p * 18.0 + so));
	c = mix(c, grey, clamp(g, 0.0, 0.9));
	// Dirt and fine grain.
	c *= 0.86 + 0.22 * noise(p * 260.0 + so);
	float depth = lw * 0.25;
	// Checks: a few splits running in from the rim, open at the bark, closing toward the pith.
	for (int k = 0; k < 5; k++) {
		if (hash(vec2(float(k), 21.0) + so) < 0.25) continue;
		float a0 = hash(vec2(float(k), 11.0) + so) * 6.2832;
		float reach = 0.3 + 0.45 * hash(vec2(float(k), 5.0) + so);
		float d = abs(sin((ang - a0) * 0.5)) * 2.0 * r;
		d += (noise(vec2(r * 90.0, float(k)) + so) - 0.5) * 0.004;
		float open = 0.004 * smoothstep(1.0 - reach, 1.0, fr);
		float crack = (1.0 - smoothstep(open * 0.35, open, d)) * step(1.0 - reach, fr);
		c = mix(c, c * 0.18, crack);
		depth += crack;
	}
	// The kerf: faint straight scores across the face.
	float kerf = noise(vec2(dot(p, vec2(0.97, 0.24)) * 420.0, 0.5));
	c *= 0.95 + 0.07 * kerf;
	// The bark round the rim, its inner edge ragged.
	float bw = bark_width * (0.7 + 0.6 * fbm(vec2(ang * 3.0, 0.0) + so)) / max(rim, 0.02);
	float b = smoothstep(1.0 - bw - 0.008, 1.0 - bw + 0.008, fr);
	float cambium = smoothstep(1.0 - bw - 0.03, 1.0 - bw, fr) * (1.0 - b);
	c = mix(c, c * 0.55, cambium);
	c = mix(c, bark * (0.75 + 0.5 * noise(p * 140.0 + so)), b);
	depth += b * (0.3 + 0.5 * noise(p * 120.0 + so));
	return vec4(c, depth);
}

void fragment() {
	float seed = UV2.y;
	vec4 a = face(UV, UV2.x, seed);
	ALBEDO = a.rgb;
	ROUGHNESS = 0.9 - 0.08 * (1.0 - min(a.a, 1.0));
	// The face's relief as a normal, from its depth a millimetre and a half
	// either way: a crack is a hollow, so the face leans away from it.
	float e = 0.0015;
	float rr = max(length(UV), 1e-4);
	float dx = face(UV + vec2(e, 0.0), UV2.x * length(UV + vec2(e, 0.0)) / rr, seed).a - a.a;
	float dy = face(UV + vec2(0.0, e), UV2.x * length(UV + vec2(0.0, e)) / rr, seed).a - a.a;
	NORMAL_MAP = normalize(vec3(dx * 2.2, dy * 2.2, 1.0)) * 0.5 + 0.5;
	AO = 1.0 - min(a.a, 1.0) * 0.4;
	AO_LIGHT_AFFECT = 0.4;
}
