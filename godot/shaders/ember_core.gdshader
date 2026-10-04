// The Kindling's ember-core: a lump of raw ember come up out of the scar, a dark crust
// split by fissures that glow from inside. It is broken by hurting it, and the more it is
// hurt the wider and hotter the fissures (heat 0 to 1).
shader_type spatial;
render_mode cull_back;

uniform float heat : hint_range(0.0, 1.0) = 0.0;
uniform vec3 crust : source_color = vec3(0.045, 0.038, 0.036);
uniform vec3 glow : source_color = vec3(1.0, 0.38, 0.09);
uniform vec3 core_white : source_color = vec3(1.0, 0.82, 0.55);

varying vec3 obj;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + 0.1);
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
	vec3 i = floor(x), f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
		mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

// Distance to the nearest and second-nearest cell point: their difference is small on a fissure.
vec2 cells(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	for (int x = -1; x <= 1; x++)
		for (int y = -1; y <= 1; y++)
			for (int z = -1; z <= 1; z++) {
				vec3 g = vec3(float(x), float(y), float(z));
				vec3 o = vec3(hash(i + g), hash(i + g + 11.3), hash(i + g + 27.1));
				vec3 r = g + o - f;
				float d = dot(r, r);
				if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) { d2 = d; }
			}
	return vec2(sqrt(d1), sqrt(d2));
}

void vertex() {
	obj = VERTEX;
	// A lump, not a ball: knobbled, flattened where it sits.
	float n = noise(VERTEX * 2.1) * 0.38 + noise(VERTEX * 4.7) * 0.14;
	VERTEX += NORMAL * (n - 0.22);
	VERTEX.y *= 0.82;
}

void fragment() {
	// The fissures wander (the cells read through a warp) and come and go along their length; at
	// heat 0 a few are lit, and the more it is broken the more open and the wider they glow.
	vec3 w = obj * 2.6 + vec3(noise(obj * 1.7), noise(obj * 1.7 + 5.2), noise(obj * 1.7 + 9.1)) * 1.3;
	vec2 c = cells(w);
	float gap = c.y - c.x;
	float open = smoothstep(0.48 - 0.4 * heat, 0.66 - 0.3 * heat, noise(w * 1.4 + 3.0));
	float width = (0.032 + 0.06 * heat) * (0.6 + 0.8 * noise(w * 3.1));
	float fissure = (1.0 - smoothstep(width * 0.4, width, gap)) * open;
	float hot = (1.0 - smoothstep(0.0, width * 0.35, gap)) * open;
	float pulse = 0.72 + 0.28 * sin(TIME * 3.2 + obj.y * 5.0 + noise(obj * 3.0) * 4.0);
	float grain = noise(obj * 13.0) * 0.6 + noise(obj * 31.0) * 0.4;
	// The crust: dark, with a faint warmth showing through it near the fissures.
	ALBEDO = crust * (0.55 + 0.8 * grain) + glow * 0.05 * (1.0 - smoothstep(0.0, 0.18, gap)) * open;
	ROUGHNESS = 0.95;
	SPECULAR = 0.15;
	vec3 e = mix(glow, core_white, hot * (0.35 + 0.65 * heat));
	EMISSION = e * fissure * (3.2 + 7.0 * heat) * pulse;
}
