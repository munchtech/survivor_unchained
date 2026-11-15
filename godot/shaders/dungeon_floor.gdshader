// A dungeon's floor (src/World/DungeonFloor.cs), by rule from the walkable field: the den's packed warm earth (the
// Hollow's painted litter and mud, their luminance only, under the den's own browns), mottled, darker at the walls'
// feet, black down its pits; the ravine's cobbles (cells of worn stone, warm, dark joints) with moss in the joints
// and in patches away from the edge, and bare dirt where the cobbles give out.
shader_type spatial;
#define CEL_INK 1
#include "res://shaders/cel.gdshaderinc"

uniform sampler2DArray sheet : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D field : filter_linear, repeat_disable;   // r: metres inside the walkable edge; g: metres outside the holes
uniform float half_size = 100.0;
uniform float step = 1.0;
uniform float res = 200.0;
uniform float ravine = 0.0;

varying vec3 wpos;
varying vec3 wnrm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec2 hash22(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}
// Gradient noise (no value noise's square blobs), and a rotated fbm of it.
float gnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = dot(hash22(i) * 2.0 - 1.0, f);
	float b = dot(hash22(i + vec2(1.0, 0.0)) * 2.0 - 1.0, f - vec2(1.0, 0.0));
	float c = dot(hash22(i + vec2(0.0, 1.0)) * 2.0 - 1.0, f - vec2(0.0, 1.0));
	float d = dot(hash22(i + vec2(1.0, 1.0)) * 2.0 - 1.0, f - vec2(1.0, 1.0));
	return 0.5 + 0.7 * mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p) {
	const mat2 r = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8));
	float s = 0.0, a = 0.5;
	for (int o = 0; o < 4; o++) { s += a * gnoise(p); p = r * p * 2.03 + 3.1; a *= 0.5; }
	return s / 0.9375;
}
float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

// Cobbles: the distance to the nearest cell's edge (x), the cell's id hash (y).
vec2 cobble(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0, d2 = 8.0;
	vec2 best = vec2(0.0);
	for (int y = -1; y <= 1; y++)
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = 0.15 + 0.7 * hash22(i + g);
			vec2 r = g + o - f;
			float d = dot(r, r);
			if (d < d1) { d2 = d1; d1 = d; best = i + g; }
			else if (d < d2) { d2 = d; }
		}
	return vec2(sqrt(d2) - sqrt(d1), hash22(best).x);
}

void fragment() {
	vec2 fuv = ((wpos.xz + half_size) / step + 0.5) / res;
	vec2 f = texture(field, fuv).rg;
	float inside = f.x;
	float hole = f.y;
	float big = fbm(wpos.xz * 0.09);
	float mid = fbm(wpos.xz * 0.45 + 17.0);
	vec3 col;
	if (ravine < 0.5) {
		// Hollow sheet: 0 litter, 3 mud. Warm packed earth, mottled at two scales.
		float l1 = lum(texture(sheet, vec3(wpos.xz / 3.2, 0.0)).rgb);
		float l2 = lum(texture(sheet, vec3(wpos.xz / 6.5 + 0.37, 3.0)).rgb);
		float l = mix(l1, l2, smoothstep(0.4, 0.6, big)) * 2.0;
		l = l * 0.55 + 0.45 * clamp((mid - 0.5) * 3.0 + 0.5, 0.0, 1.0);
		// grit: small stones and crumbs
		float grit = fbm(wpos.xz * 4.5 + 5.0);
		l += 0.35 * (smoothstep(0.62, 0.7, grit) - smoothstep(0.38, 0.3, grit));
		col = mix(vec3(0.13, 0.072, 0.042), vec3(0.34, 0.205, 0.12), clamp(l, 0.0, 1.0));
		// darker, damper patches
		col *= mix(0.72, 1.06, smoothstep(0.42, 0.58, big));
		// the wall's foot in shade of the overhang
		col *= mix(0.4, 1.0, smoothstep(0.0, 2.6, inside));
		// the pits: steep sides and the depths go black
		float pit = 1.0 - smoothstep(0.0, 1.6, hole);
		float steep = 1.0 - smoothstep(0.5, 0.92, wnrm.y);
		col *= mix(1.0, 0.02, max(smoothstep(-0.3, 1.0, -hole), pit * steep));
	} else {
		// Beyond the shelf's edge the ground is gone (the drop's rock falls away below): only the walkable shelf stays.
		if (min(inside, hole) < -0.4) discard;
		// Cobbles, about 0.45 m, each its own worn tone and rounded top, set in dirt; moss in the joints where it is
		// damp; bare packed dirt where the cobbles give out (near the edge and in patches); moss patches on the dirt.
		float B = clamp((big - 0.5) * 3.5 + 0.5, 0.0, 1.0);
		float M = clamp((mid - 0.5) * 3.5 + 0.5, 0.0, 1.0);
		vec2 q = wpos.xz / 0.45 + vec2(0.0, 0.5 * fbm(wpos.xz * 0.3));
		vec2 cb = cobble(q);
		float tex = lum(texture(sheet, vec3(wpos.xz / 2.5, 2.0)).rgb);
		float id2 = fract(cb.y * 7.13);
		vec3 stone = mix(vec3(0.2, 0.175, 0.155), vec3(0.36, 0.31, 0.26), cb.y);
		stone = mix(stone, stone * vec3(1.08, 0.98, 0.86), step(0.7, id2));
		stone *= 0.85 + 0.3 * tex;
		// worn rounded tops: dark at the rim, lighter in the middle
		stone *= mix(0.62, 1.1, smoothstep(0.04, 0.32, cb.x));
		vec3 dirt = mix(vec3(0.15, 0.11, 0.08), vec3(0.24, 0.18, 0.125), tex) * (0.85 + 0.3 * M);
		float j = 1.0 - smoothstep(0.05, 0.11, cb.x + 0.04 * (tex - 0.5));
		vec3 moss = mix(vec3(0.085, 0.105, 0.045), vec3(0.15, 0.17, 0.075), M);
		vec3 gap = mix(dirt * 0.7, moss, smoothstep(0.55, 0.75, B));
		col = mix(stone, gap, j);
		// stones missing here and there; bare dirt by the edge and in patches
		float lost = step(0.86, id2) * (1.0 - B);
		float bare = max(smoothstep(0.4, 0.22, B), 1.0 - smoothstep(0.8, 2.2, inside));
		col = mix(col, dirt, max(bare, lost));
		float patchm = smoothstep(0.78, 0.9, B + 0.3 * (M - 0.5)) * smoothstep(1.0, 3.0, inside);
		patchm *= smoothstep(0.35, 0.6, fbm(wpos.xz * 2.7 + 9.0));
		col = mix(col, moss * (0.8 + 0.4 * tex), patchm * 0.85);
		col *= mix(0.7, 1.0, smoothstep(0.0, 1.5, inside));
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}
