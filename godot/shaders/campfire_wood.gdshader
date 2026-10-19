// The camp fire's logs and ash bed (art/world/campfire, tools/assets/env_campfire.py):
// the atlas's albedo and normal, and its ember mask (how much each texel glows,
// raw 0-1) coloured like a blackbody and breathing slowly, a patch at a time,
// as air reaches it. Places are the fire's own (model space), so the pattern
// holds still as the camera moves. `bed`: the ash bed, which its fire's light
// leaves out (Campfire.CoalLayer), gets a warm wash from the fire over it.
shader_type spatial;
render_mode blend_mix, cull_back;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D ember_tex : hint_default_black, filter_linear_mipmap, repeat_disable;
uniform float heat : hint_range(0.0, 2.0) = 1.0;
uniform float ember_k = 2.2;
uniform float bed = 0.0;
uniform float bounce_k = 0.45;
// The logs are kept out of their fire's light (on Campfire.CoalLayer, so they read dark with their
// cracks glowing, not floodlit from the light over the flames): a warm wash from the flames' body instead.
uniform float wash_k = 0.0;
uniform vec3 flame_at = vec3(0.0, 0.45, 0.0);

varying vec3 lp;
varying vec3 ln;

void vertex() {
	lp = VERTEX;
	ln = NORMAL;
}

float hash3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

float noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash3(i), hash3(i + vec3(1, 0, 0)), u.x), mix(hash3(i + vec3(0, 1, 0)), hash3(i + vec3(1, 1, 0)), u.x), u.y),
		mix(mix(hash3(i + vec3(0, 0, 1)), hash3(i + vec3(1, 0, 1)), u.x), mix(hash3(i + vec3(0, 1, 1)), hash3(i + vec3(1, 1, 1)), u.x), u.y), u.z);
}

// Blackbody, roughly: dull red, orange, and yellow only at the hottest.
vec3 glow(float t) {
	vec3 c = mix(vec3(0.45, 0.03, 0.0), vec3(1.0, 0.22, 0.02), smoothstep(0.0, 0.55, t));
	return mix(c, vec3(1.0, 0.55, 0.16), smoothstep(0.7, 1.0, t));
}

void fragment() {
	vec3 alb = texture(albedo_tex, UV).rgb;
	ALBEDO = alb;
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	ROUGHNESS = 0.9;
	float m = texture(ember_tex, UV).r;
	float t = TIME;
	// Slow patches that come and go (a few seconds), and a little faster shimmer.
	float breath = noise3(lp * 7.0 + vec3(0.0, t * 0.22, t * 0.13)) * 0.6 + noise3(lp * 15.0 - vec3(t * 0.31, 0.0, t * 0.17)) * 0.4;
	breath = 0.45 + 0.75 * smoothstep(0.25, 0.75, breath);
	float shimmer = 0.9 + 0.1 * noise3(lp * 40.0 + vec3(t * 1.6, 0.0, t * 1.1));
	float hot = clamp(m * breath * shimmer * heat, 0.0, 1.2);
	vec3 e = glow(min(hot, 1.0)) * hot * ember_k;
	// The ash bed lit by the fire over it (its light leaves it out): warm, strongest under the flames.
	float r = length(lp.xz);
	e += bed * alb * vec3(1.0, 0.45, 0.16) * bounce_k * heat * (1.0 - smoothstep(0.05, 0.45, r)) * (0.9 + 0.1 * shimmer);
	vec3 to = flame_at - lp;
	float d = length(to);
	float lit = clamp(dot(normalize(ln), to / d) * 0.75 + 0.25, 0.0, 1.0) / (1.0 + d * d * 6.0);
	e += wash_k * heat * alb * vec3(1.0, 0.52, 0.22) * lit * (0.92 + 0.08 * shimmer);
	EMISSION = e;
}
