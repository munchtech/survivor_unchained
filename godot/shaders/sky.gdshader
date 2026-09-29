// The sky (src/render/sky.ts): a gradient from the horizon, a glow round the
// key light flattened toward the horizon like haze, hashed stars, a
// cratered moon, faint high cloud. The game's camera looks down steeply
// enough that the sky is seldom seen; what it mostly does is light the
// world. In the radiance pass (the map every surface takes its ambient and
// reflections from) it is the web game's environment map and hemisphere
// light together: the sky times envIntensity, without stars or moon, plus
// the hemisphere's sky and ground colours (three.js lights a surface with
// those at 1/pi of their intensity).
shader_type sky;
render_mode use_debanding;

uniform vec3 top : source_color;
uniform vec3 horizon : source_color;
uniform vec3 bottom : source_color;
uniform vec3 glow : source_color;
uniform vec3 light_dir = vec3(0.0, 1.0, 0.0);
uniform float glow_power = 8.0;
uniform float stars = 0.0;
uniform float moon = 0.0;
uniform vec3 hemi_sky : source_color;
uniform vec3 hemi_ground : source_color;
uniform float hemi_intensity = 1.0;
uniform float env_intensity = 1.0;
// The clock, as a global: a sky shader that reads the built-in clock has its
// lighting re-baked every frame; this one only when its colours change.
global uniform float sky_time;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x), f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i + vec3(0, 0, 0)), hash(i + vec3(1, 0, 0)), f.x),
			mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x),
			mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

vec3 dome(vec3 d, bool lights) {
	float h = d.y;
	vec3 col = h > 0.0
		? mix(horizon, top, pow(smoothstep(0.0, 1.0, h), 0.55))
		: mix(horizon, bottom, smoothstep(0.0, 0.35, -h));
	float cos_a = max(dot(d, normalize(light_dir)), 0.0);
	col += glow * pow(cos_a, glow_power) * (0.6 + 0.4 * (1.0 - abs(h)));
	col += glow * 0.25 * pow(1.0 - abs(h), 6.0);
	if (lights && stars > 0.0 && h > 0.0) {
		vec3 sp = d * 420.0;
		vec3 cell = floor(sp);
		float r = hash(cell);
		if (r > 0.9965) {
			vec3 center = cell + 0.5 + (vec3(hash(cell + 1.3), hash(cell + 2.7), hash(cell + 4.1)) - 0.5) * 0.6;
			float dd = length(sp - center);
			float tw = 0.6 + 0.4 * sin(sky_time * (1.0 + r * 6.0) + r * 40.0);
			col += vec3(0.85, 0.9, 1.0) * smoothstep(0.35, 0.0, dd) * tw * stars * smoothstep(0.02, 0.3, h) * 3.0;
		}
	}
	if (lights && moon > 0.0) {
		float m = dot(d, normalize(light_dir));
		float disc = smoothstep(0.99955, 0.99975, m);
		float face = 0.78 + 0.22 * noise(d * 900.0);
		col = mix(col, vec3(1.25, 1.22, 1.12) * face * 2.2, disc * moon);
	}
	float c = noise(vec3(d.xz / max(h, 0.08) * 1.6, (lights ? sky_time : 0.0) * 0.01));
	col = mix(col, col * 0.82 + glow * 0.05, smoothstep(0.55, 0.85, c) * smoothstep(0.0, 0.25, h) * 0.5);
	return col;
}

void sky() {
	vec3 d = normalize(EYEDIR);
	if (AT_CUBEMAP_PASS) {
		// Steeper than three.js's blend by 3/2: the irradiance Godot takes
		// from this (a cosine-weighted mean) then has three.js's slope.
		vec3 hemi = max(mix(hemi_ground, hemi_sky, 0.5 + 0.75 * d.y), vec3(0.0)) * hemi_intensity / PI;
		COLOR = dome(d, false) * env_intensity + hemi;
	} else {
		COLOR = dome(d, true);
	}
}
