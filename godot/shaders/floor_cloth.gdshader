shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// (E9c3) What lies on a house's floor (Insides.cs): a wool rug (rug) or strewn rushes (else), a flat card 2 x 2 in its
// own frame, scaled by its transform (so its half sizes in metres are its x and z scales). The rug: woven wool in
// broad bands (a dark border, a madder field with an undyed lozenge band), worn paler down its middle, its ends fringed
// and its edges a little ragged, a contact shade round it. The rushes: dry stalks in three crossing layers of 10 cm
// cells, each a 5-8 mm wide stalk of 8-22 cm at its own angle and shade, thinning out to a ragged edge, so the boards
// show between. It comes in with its house's cutaway (kit.gdshader's house fade: "unit", its unit + 1) on the same
// curve, by its own scatter, so where the wall's ghost is kept it is not; out of view while the house stands.
#include "res://shaders/coverage.gdshaderinc"
global uniform vec4 house_fade_ids;
global uniform vec4 house_fade_ids2;
global uniform vec4 house_fade;
global uniform vec4 house_fade2;
global uniform vec4 view_from;
instance uniform float unit = 0.0;
instance uniform float seed = 0.0;
uniform bool rug = true;

varying vec2 v_m;      // metres from the card's middle
varying vec2 v_half;   // its half sizes, metres

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
float house_fade_of(float u) {
	vec4 a = step(abs(house_fade_ids - u), vec4(0.5)) * house_fade;
	vec4 b = step(abs(house_fade_ids2 - u), vec4(0.5)) * house_fade2;
	return u < 0.5 ? 0.0 : max(max(max(a.x, a.y), max(a.z, a.w)), max(max(b.x, b.y), max(b.z, b.w)));
}

void vertex() {
	v_half = vec2(length(MODEL_MATRIX[0].xyz), length(MODEL_MATRIX[2].xyz));
	v_m = VERTEX.xz * v_half;
}

// (a stalk in a cell: its colour's shade in r, 1 in g where it lies)
vec2 stalk(vec2 p, float cs, float k) {
	vec2 c = floor(p / cs);
	vec2 best = vec2(0.0);
	for (int j = -1; j <= 1; j++)
		for (int i = -1; i <= 1; i++) {
			vec2 q = c + vec2(float(i), float(j));
			float h = hash(q + k * 13.1 + seed);
			if (h > 0.85) continue;
			vec2 o = (q + vec2(hash(q + 3.7 + k), hash(q + 9.1 + k))) * cs;
			float a = hash(q + 5.3 + k) * 3.14159 + k * 0.7;
			vec2 d = vec2(cos(a), sin(a));
			float L = mix(0.16, 0.3, hash(q + 7.7 + k)) * 0.5;
			float w = mix(0.0065, 0.0095, hash(q + 1.9 + k));
			vec2 r = p - o;
			float t = dot(r, d);
			float s = abs(dot(r, vec2(-d.y, d.x)));
			float taper = 1.0 - smoothstep(0.6, 1.0, abs(t) / L);
			if (abs(t) < L && s < w * (0.5 + 0.5 * taper)) best = vec2(0.8 + 0.3 * hash(q + 2.3 + k), 1.0);
		}
	return best;
}

void fragment() {
	if (view_from.w > 0.0 && distance(CAMERA_POSITION_WORLD, view_from.xyz) <= 1.0) {
		float f = house_fade_of(unit);
		if (coverage_cut(FRAGCOORD.xy + vec2(41.0, 23.0)) >= f) discard;
	}
	vec2 m = v_m, hf = v_half;
	vec3 col;
	float rough = 0.95;
	if (rug) {
		// (along: the rug's long axis is its z; e: distance in from its edge, d: from its ends)
		float e = hf.x - abs(m.x) + 0.012 * (noise(m * 30.0 + seed) - 0.5);
		float d = hf.y - abs(m.y);
		// the fringe: 6 cm of warp threads past the woven end
		if (d < 0.06) {
			float th = fract(m.x * 55.0);
			if (th > 0.45 || d < 0.06 * hash(vec2(floor(m.x * 55.0), seed)) * 0.6) discard;
			col = vec3(0.66, 0.6, 0.48);
		} else if (e < 0.0) {
			discard;
		} else {
			vec3 border = vec3(0.17, 0.12, 0.10), field = vec3(0.42, 0.13, 0.09), band = vec3(0.70, 0.62, 0.46), blue = vec3(0.14, 0.2, 0.3);
			float w = min(e, d - 0.06);
			float bd = min(hf.x, hf.y - 0.06);
			col = w < 0.09 ? border : w < 0.12 ? band : w < 0.2 ? blue : field;
			// a lozenge band down the field
			vec2 lq = vec2(abs(m.x) * 3.0, fract(m.y * 1.6) - 0.5);
			float lz = abs(lq.x) + abs(lq.y * 1.4);
			if (w >= 0.2 && lz < 0.42 && lz > 0.3) col = band;
			if (w >= 0.2 && lz < 0.18) col = blue;
			// the weave: rows of weft, a fine stripe; patches of worn wool paler down the middle (where feet go)
			col *= 0.9 + 0.1 * smoothstep(0.3, 0.7, fract(m.y * 140.0)) + 0.12 * (noise(m * 9.0 + seed) - 0.5);
			float wear = smoothstep(0.35, 0.0, abs(m.x) / max(bd, 0.1)) * smoothstep(0.4, 0.75, noise(m * 2.2 + seed * 1.3));
			col = mix(col, col * 1.35 + vec3(0.03, 0.025, 0.02), wear * 0.55);
			// its edge rolled a little: darker at the very rim
			col *= mix(0.72, 1.0, smoothstep(0.0, 0.025, min(e, d - 0.06)));
		}
		rough = 0.97;
	} else {
		// the rushes: dense in the middle of the card, thinning out to a ragged edge
		vec2 r = abs(m) / max(hf, vec2(0.05));
		float edge = max(r.x, r.y) + 0.35 * (noise(m * 2.5 + seed) - 0.5);
		// (E9c4: a scatter of matted rushes on the boards, not a mat; stalks 1.3-1.9 cm, so they hold at the game camera)
		float dens = 0.7 * (1.0 - smoothstep(0.5, 1.0, edge)) * smoothstep(0.3, 0.65, noise(m * 1.4 + seed * 0.7));
		vec2 s = vec2(0.0);
		for (int k = 0; k < 3; k++) {
			vec2 t = stalk(m + float(k) * 0.37, 0.1, float(k));
			if (t.y > 0.0 && hash(floor(m * 10.0 + float(k) * 0.37) + 4.4) < dens) { s = t; }
		}
		if (s.y <= 0.0) discard;
		// (E9c4: old dry straw, warm and mid-dark, about 0.4 sRGB luma (linear albedo here), so it stays straw in shade)
		vec3 dry = mix(vec3(0.196, 0.113, 0.027), vec3(0.319, 0.188, 0.043), noise(m * 6.0 + seed));
		col = dry * s.x * (0.85 + 0.3 * noise(m * 40.0));
		rough = 0.9;
	}
	ALBEDO = col;
	ROUGHNESS = rough;
	SPECULAR = 0.2;
}
