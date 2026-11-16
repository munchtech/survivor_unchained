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
uniform sampler2DArray bank_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray bank_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float bank_m = 5.0;
uniform float bank_nk = 0.6;
uniform sampler2DArray den_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 void_col = vec3(0.004, 0.004, 0.006);   // the dark between and beyond: the concepts' cool grey (15, 16, 18), not black
uniform vec3 root_lit = vec3(0.13, 0.07, 0.05);     // a root's albedo, a muted warm brown (its lit top)
uniform vec3 root_under = vec3(0.4, 0.32, 0.5);    // its under side's purple
uniform vec3 face_col = vec3(0.03, 0.024, 0.028);    // the root mass behind the roots
uniform float wall_h = 4.0;
// (round 8, 15 Nov) The den's dark beyond the banks is no longer void black (value 0 read as a hole in the frame): a
// dark painted cave mass, the bank set itself at this share of its value, cooled, mottled by slow noise (den_room.png:
// the earth and root mass behind the roots sits at about 8-22 of 255). --den-beyond sets it.
uniform float beyond_k = 0.3;
uniform vec3 beyond_tint = vec3(0.8, 0.86, 1.0);
uniform float bank_sat = 0.65;   // (round 8 judge: the banks less saturated, cool in their gaps)
uniform float bank_gain = 1.0;     // (round 8) the bank set's value (--den-bank-gain)
uniform float hollow_min = 0.0;    // (round 8) the floor under the bank set's black hollows between roots (--den-hollow): earth, never void
uniform float tile = 5.0;
// (den round 9, bank lane, 15 Nov) r9 1: the banks with their big roots (src/World/DungeonWalls.BankRoots.cs, COLOR.r 0.8):
// a root's albedo warm only on the side the key falls on (cel_key), grey and a touch cool turned away from it (the
// targets' shade (36, 32, 32)), and the far wall (bank and roots) receding into the dark with height (wall_top_k at 7 m).
uniform float r9 = 0.0;
uniform vec3 broot_col = vec3(0.2, 0.12, 0.075);
uniform vec3 broot_cool = vec3(0.86, 0.9, 1.0);
uniform float wall_top_k = 0.3;

varying vec3 wpos;
varying vec3 wnrm;
varying float kind;
varying float floor_y;
varying float s_out;
varying float along_m;
varying float round_s;
varying float root_id;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	kind = COLOR.r;
	floor_y = UV2.x;
	s_out = COLOR.g * 8.0 - 1.0;
	along_m = UV2.y;
	round_s = COLOR.b;
	root_id = COLOR.a;
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
vec3 beyond_col() {
	vec2 uv = vec2(wpos.x, -(0.469 * wpos.y - 0.883 * wpos.z)) / bank_m;
	vec3 t = mix(texture(bank_alb, vec3(uv * 0.8 + vec2(0.21, 0.13), 1.0)).rgb, texture(bank_alb, vec3(uv * 0.8 + vec2(0.57, 0.71), 0.0)).rgb, smoothstep(0.4, 0.6, vnoise(wpos.xz * 0.06 + 3.0)));
	t = max(t, vec3(hollow_min) * vec3(1.0, 0.74, 0.58) * (0.7 + 0.6 * vnoise(wpos.xz * 0.7)));
	vec3 b = t * beyond_k * beyond_tint * (0.65 + 0.7 * vnoise(wpos.xz * 0.11 + 9.0));
	// (round 9) never under the targets' dark (their deep gaps sit at 12-20 of 255, cool): a mottled cool floor
	if (r9 > 0.5) b = max(b, vec3(0.0058, 0.006, 0.0072) * (0.75 + 0.5 * vnoise(wpos.xz * 0.23 + 4.0)));
	return b;
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
	vec3 col;
	if (!FRONT_FACING) {
		// The cut mass inside.
		col = vec3(0.043, 0.035, 0.031);
	} else if (kind > 0.75 && kind < 0.85) {
		// A big bank root (round 9): a smooth cel tube, its bark long broken grooves along it and lighter dabs on its lit
		// top; each root its own shade (COLOR.a). Warm where the key falls, grey turned from it; the far wall's dark above.
		vec3 base = broot_col * mix(0.8, 1.15, root_id);
		float a = round_s * 7.0 + 0.8 * (vnoise(vec2(along_m * 0.5, root_id * 37.0)) - 0.5);
		float fa = fwidth(a);
		float groove = 1.0 - smoothstep(0.05, 0.05 + 1.5 * fa, abs(fract(a) - 0.5));
		groove *= smoothstep(0.35, 0.6, vnoise(vec2(along_m * 0.9 + floor(a) * 5.3, root_id * 11.0 + floor(a) * 1.7)));
		groove *= 1.0 - smoothstep(0.2, 0.5, fa);
		base *= 1.0 - 0.4 * groove;
		float kl = dot(wnrm, normalize(cel_key.xyz));
		float dab = smoothstep(0.5, 0.75, vnoise(vec2(along_m * 1.4 + root_id * 7.0, round_s * 5.0)));
		base *= 1.0 + 0.3 * dab * smoothstep(0.2, 0.6, kl);
		float lb = dot(base, vec3(0.299, 0.587, 0.114));
		base = mix(vec3(lb) * broot_cool, base, smoothstep(-0.25, 0.35, kl));
		base *= mix(1.0, wall_top_k, smoothstep(2.6, 7.5, h));
		base *= 1.0 - 0.3 * (1.0 - smoothstep(-0.05, 0.25, wpos.y - floor_y));
		col = base;
	} else if (kind > 0.75) {
		// A root: a smooth cel tube (the concepts'), its bark sparse line work (grooves along it, wobbling, broken),
		// never the planks of a striped texture; each root its own shade (COLOR.a), the under side purple-brown, the
		// edge turning away a shade darker for the ink. Out over the top it sinks into the dark; down a pit (COLOR.r
		// 0.9) into the throat's.
		vec3 base = root_lit * mix(0.8, 1.18, root_id);
		float a = round_s * 5.0 + 0.7 * (vnoise(vec2(along_m * 0.6, root_id * 37.0)) - 0.5);
		float fa = fwidth(a);
		float line = 1.0 - smoothstep(0.03, 0.03 + 1.2 * fa, abs(fract(a) - 0.5));
		line *= smoothstep(0.4, 0.6, vnoise(vec2(along_m * 1.3 + floor(a) * 5.3, root_id * 11.0 + floor(a) * 1.7)));
		line *= 1.0 - smoothstep(0.15, 0.4, fa);
		base *= 1.0 - 0.5 * line;
		base *= 1.0 + 0.08 * sin(6.2832 * (round_s * 3.0 + 0.5 * vnoise(vec2(along_m * 0.4, root_id * 23.0))));
		base *= mix(vec3(1.0), root_under, smoothstep(0.35, -0.55, wnrm.y));
		float nv = abs(dot(normalize(NORMAL), normalize(-VERTEX)));
		base *= mix(0.55, 1.0, smoothstep(0.08, 0.4, nv));
		base *= 1.0 - 0.22 * (1.0 - smoothstep(0.0, 0.4, h));
		col = mix(base, void_col, 0.92 * smoothstep(1.6, 5.4, s_out));
		if (kind < 0.95) col = mix(col, void_col, smoothstep(0.25, 1.5, depth));
	} else if (ravine > 0.5) {
		vec3 tilt;
		col = rock(wpos, wnrm, tilt);
		NORMAL = normalize((VIEW_MATRIX * vec4(tilt, 0.0)).xyz);
		// A drop falls away into violet shade; the rock above darkens a little toward its top.
		col = mix(col, vec3(0.05, 0.04, 0.08), smoothstep(0.5, 11.0, depth) * 0.92);
		col *= 1.0 - 0.25 * smoothstep(0.5 * wall_h, wall_h, h);
		if (kind > 0.25 && depth < 0.5) col *= 0.55;
	} else if (kind > 0.25) {
		col = beyond_col();
	} else {
		// The den's bank (15 Nov): the painted bank set projected along the play camera's view so it is never stretched on
		// the slope; slice 1 main, slice 0 blended in by slow noise; past the crest (COLOR.b) it fades to black.
		vec2 uv = vec2(wpos.x, -(0.469 * wpos.y - 0.883 * wpos.z)) / bank_m;
		float vw = smoothstep(0.62 - 0.05, 0.62 + 0.05, vnoise(wpos.xz * 0.08));
		vec2 uv0 = uv + vec2(0.37, 0.61);
		col = mix(texture(bank_alb, vec3(uv, 1.0)).rgb, texture(bank_alb, vec3(uv0, 0.0)).rgb, vw);
		col = mix(vec3(dot(col, vec3(0.299, 0.587, 0.114))), col, bank_sat);
		col = max(col * bank_gain, vec3(hollow_min) * vec3(1.0, 0.74, 0.58) * (0.7 + 0.6 * vnoise(wpos.xz * 0.7 + wpos.y)));
		vec3 n = mix(texture(bank_nrm, vec3(uv, 1.0)).xyz, texture(bank_nrm, vec3(uv0, 0.0)).xyz, vw) * 2.0 - 1.0;
		vec3 wn = normalize(wnrm + bank_nk * (n.x * vec3(1.0, 0.0, 0.0) - n.y * vec3(0.0, 0.469, -0.883)));
		NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
		// down a pit the face goes to black within a couple of metres
		col *= mix(1.0, 0.06, smoothstep(0.15, 1.8, depth) * (1.0 - round_s));
		col *= 1.0 - 0.25 * (1.0 - smoothstep(0.0, 0.5, h));
		if (r9 > 0.5) {
			// (round 9) the painting's shade grey and a touch cool (warm only where it is lit); the far wall into the dark
			float lc = dot(col, vec3(0.299, 0.587, 0.114));
			col = mix(vec3(lc) * broot_cool, col, smoothstep(0.012, 0.07, lc));
			col *= mix(1.0, wall_top_k, smoothstep(2.4, 7.0, h));
		}
		col = mix(col, beyond_col(), smoothstep(0.0, 1.0, round_s));
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}
