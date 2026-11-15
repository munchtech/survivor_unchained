// A dungeon's walls (src/World/DungeonWalls.cs): triplanar painted rock or roots over earth, dark toward the top, with a
// cutaway so a near wall never hides her. COLOR.r says what a vertex is: 0 the wall's face, 0.5 the top beyond it, 1 a root.
shader_type spatial;
render_mode cull_disabled;
#define CEL_INK 1
#include "res://shaders/cel.gdshaderinc"

global uniform vec4 survivor;   // her chest (xyz), w 1 while she is in the world

uniform sampler2DArray sheet : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float layer_a = 1.0;    // den: rot; ravine: face
uniform float layer_b = 2.0;    // den: roots
uniform float ravine = 0.0;
uniform float wall_h = 4.0;
uniform float tile = 5.0;

varying vec3 wpos;
varying vec3 wnrm;
varying float kind;
varying float floor_y;
varying float s_out;
varying float along_m;
varying float round_s;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	kind = COLOR.r;
	floor_y = UV2.x;
	s_out = COLOR.g * 8.0 - 1.0;
	along_m = UV2.y;
	round_s = COLOR.b;
}

float bayer8(ivec2 p) {
	int x = p.x & 7;
	int y = p.y & 7;
	int v = 0;
	for (int i = 2; i >= 0; i--) {
		v = (v << 2) | ((((x >> i) & 1) ^ ((y >> i) & 1)) << 1) | ((y >> i) & 1);
	}
	return (float(v) + 0.5) / 64.0;
}

vec3 tri(float layer, vec3 w) {
	vec3 b = pow(abs(wnrm), vec3(4.0));
	b /= b.x + b.y + b.z;
	return texture(sheet, vec3(wpos.zy / tile, layer)).rgb * b.x
		+ texture(sheet, vec3(wpos.xz / tile, layer)).rgb * b.y
		+ texture(sheet, vec3(wpos.xy / tile, layer)).rgb * b.z;
}

float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash2(i), hash2(i + vec2(1.0, 0.0)), f.x), mix(hash2(i + vec2(0.0, 1.0)), hash2(i + vec2(1.0, 1.0)), f.x), f.y);
}

// The ravine's rock, painted: tall plates parted by vertical fractures, stepped in three tones, thin strata across
// them, violet-grey; the flat tops a shade warmer where dust lies.
// One plane's plates (q: across, up), for the triplanar blend below: (tone, crack, the block's id). A block is a
// column between two fractures, broken across now and then; each block leans its own way (rock_tilt), so the cel
// light breaks the face into planes.
vec3 plates(vec2 q) {
	float w = vnoise(q + 3.1) * 0.65 + vnoise(q * 2.3) * 0.35;
	float fx = q.x * 1.3 + 0.35 * vnoise(q * vec2(0.4, 1.5));
	float crack = 1.0 - smoothstep(0.02, 0.07, abs(fract(fx) - 0.5) * (0.6 + 0.8 * vnoise(q * 0.7 + 9.0)));
	float col = floor(fx + 0.5);
	float fy = q.y * 1.6 + hash2(vec2(col, 3.7)) * 4.0;
	float row = floor(fy);
	crack = max(crack, (1.0 - smoothstep(0.02, 0.06, abs(fract(fy) - 0.5) - 0.44)) * 0.7 * step(0.45, hash2(vec2(col, row + 0.5))));
	return vec3(w, crack, hash2(vec2(col, row)));
}


vec3 rock(vec3 p, vec3 n, out vec3 rock_tilt) {
	// World-axis triplanar (a tangent from the normal flipped from facet to facet and drew chevrons).
	vec3 bw = pow(abs(n), vec3(4.0));
	bw /= bw.x + bw.y + bw.z;
	vec3 px = plates(vec2(p.z * 0.9, p.y * 0.4));
	vec3 pz = plates(vec2(p.x * 0.9, p.y * 0.4));
	vec3 py = plates(p.xz * 0.7);
	vec3 wc = px * bw.x + pz * bw.z + py * bw.y;
	float id = bw.x > max(bw.y, bw.z) ? px.z : (bw.z > bw.y ? pz.z : py.z);
	// The block's lean: sideways and up or down, a third of a radian at most.
	vec3 t = vec3(hash2(vec2(id, 1.3)), hash2(vec2(id, 7.1)), hash2(vec2(id, 4.9))) * 2.0 - 1.0;
	rock_tilt = normalize(n + 0.22 * (t - n * dot(t, n)));
	float steep = 1.0 - smoothstep(0.55, 0.85, n.y);
	float u = p.x * bw.z + p.z * bw.x;
	float w = wc.x;
	float tone = floor((w * 0.75 + 0.25 * id) * 4.0) / 4.0;
	float crack = wc.y;
	float band = smoothstep(0.85, 0.95, fract(p.y * 0.55 + 0.4 * vnoise(vec2(u * 0.1, 0.0))));
	vec3 base = mix(vec3(0.11, 0.1, 0.125), vec3(0.18, 0.165, 0.185), tone);
	// the tops: dust, and moss and grass in patches
	vec3 top = base * vec3(1.1, 1.02, 0.9);
	float moss = smoothstep(0.5, 0.62, vnoise(p.xz * 0.35) * 0.7 + vnoise(p.xz * 1.3) * 0.3);
	top = mix(top, vec3(0.13, 0.15, 0.06) * (0.8 + 0.4 * w), moss);
	base = mix(base, top, 1.0 - steep);
	base *= 1.0 - 0.55 * crack;
	base *= 1.0 - 0.18 * band * steep;
	return base;
}
void fragment() {
	// The cutaway: what stands nearer the camera than her, over her chest on screen, is cut away (dithered at its
	// edge), keeping a 0.9 m footing so the wall still stands round her feet.
	if (survivor.w > 0.0 && wpos.y > floor_y + 0.9) {
		vec3 her_v = (VIEW_MATRIX * vec4(survivor.xyz, 1.0)).xyz;
		if (-VERTEX.z < -her_v.z - 0.5) {
			vec4 hp = PROJECTION_MATRIX * vec4(her_v, 1.0);
			vec2 ndc = hp.xy / hp.w;
			vec2 her_px = vec2(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5) * VIEWPORT_SIZE;
			vec2 d = (FRAGCOORD.xy - her_px) / VIEWPORT_SIZE.y;
			float e = length(d / vec2(0.16, 0.22));
			if (e < 1.0 && (e < 0.75 || bayer8(ivec2(FRAGCOORD.xy)) < (1.0 - e) / 0.25)) discard;
		}
	}
	float h = max(wpos.y - floor_y, 0.0);
	float depth = max(floor_y - wpos.y, 0.0);
	// The dark beyond goes by how far outside the walkable edge a point is (not by height), so the band's top and the
	// coarse cap meet black on black.
	float beyond = smoothstep(0.9, 2.4, s_out);
	vec3 col;
	if (!FRONT_FACING) {
		// The cut mass inside.
		col = vec3(0.043, 0.035, 0.031);
	} else if (kind > 0.75) {
		// A root: dark warm bark, each root its own shade, fine streaks along it and a knot now and then.
		float id = hash2(floor(vec2(along_m * 0.02, round_s * 0.1) + floor(wpos.xz * 0.25)));
		vec3 bark = mix(vec3(0.12, 0.062, 0.035), vec3(0.2, 0.105, 0.055), id);
		float streak = vnoise(vec2(round_s * 9.0, along_m * 0.9)) * 0.6 + vnoise(vec2(round_s * 21.0, along_m * 2.3)) * 0.4;
		bark *= mix(0.62, 1.12, smoothstep(0.25, 0.75, streak));
		col = bark * (1.0 - 0.85 * smoothstep(1.4, 3.2, s_out)) * (1.0 - 0.3 * (1.0 - smoothstep(0.0, 0.5, h)));
	} else if (ravine > 0.5) {
		vec3 tilt;
		col = rock(wpos, wnrm, tilt);
		NORMAL = normalize((VIEW_MATRIX * vec4(tilt, 0.0)).xyz);
		// A drop falls away into violet shade; the rock above darkens a little toward its top.
		col = mix(col, vec3(0.05, 0.04, 0.08), smoothstep(0.5, 11.0, depth) * 0.92);
		col *= 1.0 - 0.25 * smoothstep(0.5 * wall_h, wall_h, h);
		if (kind > 0.25 && depth < 0.5) col *= 0.55;
	} else if (kind > 0.25) {
		col = vec3(0.012, 0.01, 0.009);
	} else {
		// The den's face: packed dark earth with the roots' own sheet in it, black beyond.
		vec3 bed = tri(layer_a, wpos);
		float lum = dot(bed, vec3(0.299, 0.587, 0.114));
		col = vec3(0.12, 0.08, 0.055) * (0.55 + 1.2 * lum);
		col *= 1.0 - beyond;
		col *= 1.0 - 0.35 * (1.0 - smoothstep(0.0, 0.6, h));
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}
