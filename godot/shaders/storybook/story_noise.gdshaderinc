// Value noise for the storybook's shaders: smooth, cheap, and the same for
// the same inputs (no TIME: the player passes its own clock, so a frame at
// a given second always looks the same, seeks and movie captures included).

// Hashes without sine (Dave Hoskins): steady at large inputs on every GPU.
float sb_hash1(float p) { p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
float sb_hash2(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float sb_hash3(vec3 p) { p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }

// 1D noise (a lamp's flicker): 0..1.
float sb_noise1(float x) {
	float i = floor(x), f = fract(x);
	float u = f * f * (3.0 - 2.0 * f);
	return mix(sb_hash1(i), sb_hash1(i + 1.0), u);
}

float sb_noise2(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(sb_hash2(i), sb_hash2(i + vec2(1, 0)), u.x),
		mix(sb_hash2(i + vec2(0, 1)), sb_hash2(i + vec2(1, 1)), u.x), u.y);
}

float sb_noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = mix(mix(sb_hash3(i), sb_hash3(i + vec3(1, 0, 0)), u.x), mix(sb_hash3(i + vec3(0, 1, 0)), sb_hash3(i + vec3(1, 1, 0)), u.x), u.y);
	float b = mix(mix(sb_hash3(i + vec3(0, 0, 1)), sb_hash3(i + vec3(1, 0, 1)), u.x), mix(sb_hash3(i + vec3(0, 1, 1)), sb_hash3(i + vec3(1, 1, 1)), u.x), u.y);
	return mix(a, b, u.z);
}

// Fractal noise, 0..1 (about): four octaves, each turned so the grid never shows.
float sb_fbm2(vec2 p) {
	float s = 0.0, a = 0.5;
	mat2 r = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));
	for (int i = 0; i < 4; i++) { s += a * sb_noise2(p); p = r * p * 2.03 + 17.1; a *= 0.5; }
	return s / 0.9375;
}

float sb_fbm3(vec3 p) {
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 3; i++) { s += a * sb_noise3(p); p = p * 2.07 + vec3(17.1, 9.3, 4.7); a *= 0.5; }
	return s / 0.875;
}
