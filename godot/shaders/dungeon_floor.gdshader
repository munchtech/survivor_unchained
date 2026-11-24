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
uniform sampler2DArray den_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray den_arh : filter_linear_mipmap_anisotropic, repeat_enable;
const float den_m[6] = float[](4.0, 4.0, 3.0, 3.0, 4.0, 4.0);
uniform vec3 den_tint = vec3(0.92, 0.92, 1.04);   // (round 8: cooler, less orange: the shade floor measured (58,35,27) against den_boss.png's (52,47,43))
// (before round 8: (0.95, 0.88, 0.94))   // (lead 6: 1.3 read as bright sand, frame median 68-80 against the targets' 40-57)
uniform float rim_dark = 1.0;   // 0: no damp lip, wall-foot or pit darkening (--env-off rim, the den pit halo diagnosis, 15 Nov)
uniform float den_grain = 0.6;   // the painted grain's value contrast, stretched about its local mean
uniform vec3 boss_c = vec3(0.0);   // the den's boss lair: centre x, z and radius (0: none)
uniform float open_lift = 1.08;
uniform float den_sat = 0.65;   // (round 8 judge: the earth 35% less saturated; warmth comes from the shafts and fires)
uniform float moss_k = 0.35;   // (round 8) the moss tongues' share: 0.8 washed the floor by the banks olive (the targets have no green floor)   // the rooms' open middles, lifted (round 7: <= 10 %)
uniform float boss_dim = 0.95;
uniform float boss_damp = 0.9;
uniform float boss_sat = 1.0;
uniform vec3 boss_tint = vec3(1.0);
uniform float den_chroma = 1.0;
uniform float den_chroma_lo = 0.03;
uniform float den_chroma_hi = 0.1;   // (r12) the darks' saturation cap (1: none)
uniform vec3 gloom_tint = vec3(0.8, 0.95, 1.25);   // (den r14) the lair's fall: the grey's tint (DungeonFloor sets the warm umber by default)
uniform float gloom_mix = 0.7;
uniform float open_grit = 0.0;   // (den r14 item 8) the open floor's fine grit contrast (DungeonFloor: --den-grit)
uniform float boss_gloom = 0.0;   // (r12) the lair falls dark and cool from its pools toward its walls (den_set.gdshaderinc's lair_gloom, the same rule)
uniform float boss_dry = 0.0;   // (r11) the damp tile (F8) kept out of the lair by this share: it read as a dark grey-mauve speckle   // (r11) the lair's damp dark patches' depth (the lair measured median 42 against den_boss.png's 68)
uniform float pit_decals = 0.0;  // 1: the den's painted pit decals own the holes (DungeonDress.FloorDecals): no ray, no lip here
// (den round 10) the painted set's floor (tools/look/den_set.py: art/dungeon/den/set/floor.png, 4 m tiles made seamless):
// F1 packed earth, F2 trodden, F3 damp with moss, F4 thin root runs, laid by the same weights as the layers above
uniform sampler2DArray set_floor : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float set_k = 0.0;   // 0: off (--den-set 0); 1: the set's tiles own the den floor's albedo
uniform float set_gain = 1.0;   // the set floor's albedo scale (--den-set-floor-gain)
uniform float set_band = 0.6;   // (r10b) the tiles' 3 cm-1 m masses stretched by this (0: as painted)
uniform float set_damp = 0.45;  // (r13) the damp patches' depth in the open: at 1 a 2-3 m one read as a black smudge on the seed-23 corridor (judge r12)
uniform float set_paths = 1.0;  // (r10b) worn ways and damp patches by the slow fields (0: the walls' vignette only)
// (r11) the floor read as a soft brown cloud: each tile was read twice at two turns and the two AVERAGED over wide
// bands (every stone at half strength, ghosted), the band stretch multiplied a blurred copy back in, and the slow
// damp, leaf and value clouds were laid on top. set_sharp 1: the two turns switch over a narrow seam, the tiles are read
// a little sharper (mip bias); set_clouds scales the slow clouds under the set (1: as before).
uniform float set_sharp = 1.0;
uniform float set_clouds = 0.35;
uniform float set_trod = 0.5;   // (r11) the trodden tile's share (F7: paw prints, few stones): the open middle was all of it
// (den r17 L, R16 item 2) the shafts' pools as light landing on this floor's albedo (DungeonLight.FloorPools): per pool
// x, z, radius (m), noise seed; the albedo times sp_gain * sp_tint inside, a ragged soft edge sp_edge (m) wide. sp_n 0: none.
uniform vec4 sp[64];
uniform int sp_n = 0;
uniform vec2 sp_lean = vec2(-0.58, -0.81);   // toward the shafts' tops on the ground: the pools a little longer that way
uniform float sp_gain = 1.5;
uniform float sp_edge = 0.3;
uniform vec3 sp_tint = vec3(1.0, 1.0, 0.84);
uniform float sp_grain = 0.0;   // the grain's value contrast in the light: albedo times (lum / sp_ref)^(sp_grain) inside (light shows texture)
uniform float sp_ref = 0.15;
uniform float sp_smooth = 0.0;   // (den r18 L3, R17 item 3) 1: a smooth elliptical mask (no grain term, no wobble) times the albedo, its gain soft-capped at sp_cap
uniform float sp_cap = 9.0;
uniform float sp_blur = 0.0;   // (den r18 L4) 0..1: the floor's grain blended toward its blurred self inside the pool
uniform float sp_blur_lod = 5.0;
uniform float sp_norm = 0.0;   // (den r18 L4) 1: each pool's gain set from its own floor so it lifts by sp_dl; 0: the flat sp_gain
uniform float sp_dl = 0.17;
uniform float sp_gmin = 1.3;   // (den r19 L2, R18b item 1) the per-pool gain's floor: a bright floor (s23) needs less than 1.3 for its dL
uniform float sp_soft = 0.7;
uniform float sp_knee = 0.6;
uniform float sp_lair = 1.0;   // (den r17 L2) a lair pool's strength (its seed + 1000): the lair's floor is lit brighter than the rooms'

varying vec3 wpos;
varying vec3 wnrm;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (ravine < 0.5) {
		// The den's pits are drawn, not modelled: the mesh's sink (MapGen, 2.4 m by smoothstep(0.3, -1.6, hole) on its
		// 1 m grid, a 5 m pit in a few faceted cells) is undone here and its tilted normals flattened, so the floor runs
		// level to the mouth; fragment() paints the hole below it (pit_w). The faceted slope read as an angular slab
		// and its normals, turned from the key, as a dark blob outside the pit (pit solver, 15 Nov).
		float hd = textureLod(field, ((wpos.xz + half_size) / step + 0.5) / res, 0.0).g;
		float sink = 2.4 * (1.0 - smoothstep(-1.6, 0.3, hd));
		VERTEX.y += sink;
		wpos.y += sink;
		NORMAL = normalize(mix(NORMAL, vec3(0.0, 1.0, 0.0), 1.0 - smoothstep(1.3, 1.7, hd)));
	}
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

// (tester lane, 23 Nov, coordinator option a) An integer hash (pcg2d, Jarzynski & Olano 2020) in place of fract(sin(dot) * 43758.5):
// sin of arguments near 10^4 and a fused or split multiply-add differ by GPU and driver, so the old pattern was not the same on
// D3D12 and Vulkan (parity round 2: the den floor busier on D3D12), nor (inference) across GPU makers. The input is quantized to
// 1/256 first (integer cells stay exact; a fraction an ulp apart only flips at a 1/256 step), out uniform in [0, 1) as before.
vec2 hash22(vec2 p) {
	uvec2 v = uvec2(ivec2(floor(p * 256.0 + 0.5)));
	v = v * 1664525u + 1013904223u;
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	v.x += v.y * 1664525u; v.y += v.x * 1664525u;
	v = v ^ (v >> 16u);
	return vec2(v >> 8u) * (1.0 / 16777216.0);
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

// The den's pit mouth as a field: metres outside it (the hole field, its edge wobbled a hand either way). The field is
// read as a cubic B-spline (four bilinear taps): read bilinear, its 1 m grid drew the mouth as a polygon.
float pit_w(vec2 xz) {
	vec2 t = (xz + half_size) / step;
	vec2 i = floor(t), f = t - i;
	vec2 w0 = (1.0 - f) * (1.0 - f) * (1.0 - f) / 6.0;
	vec2 w1 = (4.0 - 6.0 * f * f + 3.0 * f * f * f) / 6.0;
	vec2 w3 = f * f * f / 6.0;
	vec2 w2 = 1.0 - w0 - w1 - w3;
	vec2 g0 = w0 + w1, g1 = w2 + w3;
	vec2 h0 = (i - 0.5 + w1 / g0) / res, h1 = (i + 1.5 + w3 / g1) / res;
	float v = g0.y * (g0.x * textureLod(field, vec2(h0.x, h0.y), 0.0).g + g1.x * textureLod(field, vec2(h1.x, h0.y), 0.0).g)
		+ g1.y * (g0.x * textureLod(field, vec2(h0.x, h1.y), 0.0).g + g1.x * textureLod(field, vec2(h1.x, h1.y), 0.0).g);
	return v + 0.45 * (gnoise(xz * 0.8 + 3.7) - 0.5);
}
const float PIT_IN = 0.15;    // the inner wall leans in this much per metre down (more of the far wall in view)
const float PIT_DEEP = 3.0;   // below this the ray finds the black bottom

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
	float big = fbm(wpos.xz * 0.09 + vec2(-301.004, 22.973));   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
	float mid = fbm(wpos.xz * 0.45 + 17.0);
	vec3 col;
	float blr = 1.0;   // (den r18 L4, R18 item 3) the painted floor's lum blurred (lod sp_blur_lod, no band) over its lum: the pool's flattening factor
	if (ravine < 0.5) {
		// The den's own painted set (ground.json "den", tools/look/ground_paint.py): 0 earth, 1 trodden, 2 litter,
		// 3 rootmat, 4 dark, 5 pitface. Laid by rule from the fields: trodden earth in the rooms' open middles, litter in
		// patches, root mats spreading from the walls' feet, damp dark earth at the foot and the pit mouths, the pit
		// face on the steep. Each layer read twice at two turns and blended by a slow field, so no tile repeats.
		// Under and beyond the bank (DungeonWalls' den profile) the ground is gone: the bank's fall and its cap go black
		// below it, and a floor left there showed as a lit brown plain behind every bank (lead 6, 15 Nov).
		if (inside < -0.6) discard;
		float steep = 1.0 - smoothstep(0.55, 0.9, wnrm.y);
		float wob = (mid - 0.5) * 2.2;
		float w_tr = smoothstep(3.5, 7.5, inside + wob * 1.5) * (1.0 - steep);   // (the rooms' open middles, worn paler: a vignette by rule)
		float w_li = smoothstep(0.52, 0.7, fbm(wpos.xz * 0.23 + 41.0)) * smoothstep(0.6, 1.6, inside) * (1.0 - w_tr);
		float w_rm = 1.0 - smoothstep(0.4, 2.4, inside + wob * 0.8);
		float w_dk = rim_dark * (1.0 - smoothstep(-0.2, 0.9, inside + wob * 0.3));   // (a thin damp lip only: a wide dark ring read as a raised tub's shadow)
		float w_pf = steep * (1.0 - smoothstep(0.0, 2.0, hole));
		float hb[6];
		vec3 cb[6];
		float tw = smoothstep(0.35, 0.65, fbm(wpos.xz * 0.06 + vec2(207.030, -342.241)));   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
		const mat2 R1 = mat2(vec2(0.616, 0.788), vec2(-0.788, 0.616));
		for (int i = 0; i < 6; i++) {
			vec2 u0 = wpos.xz / den_m[i];
			vec2 u1 = R1 * wpos.xz / den_m[i] + 0.37;
			vec4 a0 = texture(den_alb, vec3(u0, float(i)));
			vec4 a1 = texture(den_alb, vec3(u1, float(i)));
			float h0 = texture(den_arh, vec3(u0, float(i))).b;
			float h1 = texture(den_arh, vec3(u1, float(i))).b;
			cb[i] = mix(a0.rgb, a1.rgb, tw);
			hb[i] = mix(h0, h1, tw);
		}
		float wts[6] = float[](1.0, w_tr, w_li, w_rm, w_dk, w_pf);
		// height blend: each layer's weight lifts its own high shapes over the one under it
		float best = -9.0;
		for (int i = 0; i < 6; i++) best = max(best, wts[i] * 1.0 + hb[i] * 0.35 * step(0.001, wts[i]) - (i == 0 ? 0.55 : 0.0));
		vec3 acc = vec3(0.0); float ws = 0.0;
		for (int i = 0; i < 6; i++) {
			float v = wts[i] * 1.0 + hb[i] * 0.35 * step(0.001, wts[i]) - (i == 0 ? 0.55 : 0.0);
			float w = max(v - best + 0.12, 0.0);
			acc += cb[i] * w; ws += w;
		}
		col = acc / max(ws, 1e-4);
		// the painted grain stretched about its local mean (the layers' mip), so the flakes and grit read at the play camera
		vec3 ref = mix(textureLod(den_alb, vec3(wpos.xz / den_m[0], 0.0), 5.0).rgb, textureLod(den_alb, vec3(R1 * wpos.xz / den_m[0] + 0.37, 0.0), 5.0).rgb, tw);
		float lr = max(lum(ref), 1e-3);
		col *= clamp(pow(max(lum(col), 1e-4) / lr, den_grain), 0.3, 2.5);
			if (set_k > 0.5) {
				// each tile read twice at two turns, the two switched by the slow field (no repeat reads); the painting's own grain
				vec2 s0 = wpos.xz / 4.0, s1 = R1 * wpos.xz / 4.0 + 0.37;
				float twf = fbm(wpos.xz * 0.06 + vec2(207.030, -342.241));   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov) (the same field as tw)
				float tws = mix(tw, smoothstep(0.47, 0.53, twf), set_sharp);
				float bi = -0.6 * set_sharp;
				vec4 t1 = mix(texture(set_floor, vec3(s0, 0.0), bi), texture(set_floor, vec3(s1, 0.0), bi), tws);
				vec4 t2 = mix(texture(set_floor, vec3(s0 + 0.5, 1.0), bi), texture(set_floor, vec3(s1 + 0.5, 1.0), bi), tws);
				vec4 t3 = mix(texture(set_floor, vec3(s0, 2.0), bi), texture(set_floor, vec3(s1, 2.0), bi), tws);
				vec4 t4 = mix(texture(set_floor, vec3(s0 + 0.25, 3.0), bi), texture(set_floor, vec3(s1 + 0.25, 3.0), bi), tws);
				// (r11) a second base earth (F6) in patches 6-12 m across, switched in by its high shapes
				vec4 t5 = mix(texture(set_floor, vec3(s0 + 0.62, 4.0), bi), texture(set_floor, vec3(s1 + 0.62, 4.0), bi), tws);
				float k5 = smoothstep(0.0, 1.0, (fbm(wpos.xz * 0.09 + vec2(-385.233, -126.283)) - 0.5) * 9.0 + 0.5 + 0.8 * (t5.a - t1.a));   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
				t1 = mix(t1, t5, k5);
				// (r10b) the frame's macro value structure: worn ways wandering through the open (F2, lighter) and damp
				// patches in the hollows between them (F3, darker and cool), 3-8 m across, besides the walls' vignette
				float path = (1.0 - smoothstep(0.04, 0.15, abs(fbm(wpos.xz * 0.05 + vec2(-97.914, -123.086)) - 0.5) + 0.05 * (mid - 0.5))) * smoothstep(0.8, 2.5, inside);   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
				float wtr = set_trod * clamp(w_tr * mix(1.0, 0.55, set_paths) + set_paths * path, 0.0, 1.0);
				float wdp = max(max(w_dk, w_li * 0.5), set_paths * set_damp * smoothstep(0.52, 0.76, fbm(wpos.xz * 0.11 + vec2(260.019, -17.196))) * (1.0 - path) * smoothstep(0.3, 1.5, inside));   // (pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
				float inb = boss_c.z > 0.0 ? 1.0 - smoothstep(boss_c.z * 0.85, boss_c.z * 1.05, distance(wpos.xz, boss_c.xy)) : 0.0;
				wdp *= 1.0 - boss_dry * inb;
				// height blend: a layer's high shapes (its alpha) come through first as its weight rises
				float k2 = smoothstep(0.0, 1.0, wtr * 1.6 - 0.3 + 0.6 * (t2.a - 0.5));
				float k4 = smoothstep(0.0, 1.0, w_rm * 1.6 - 0.3 + 0.6 * (t4.a - 0.5));
				float k3 = smoothstep(0.0, 1.0, wdp * 1.6 - 0.3 + 0.6 * (t3.a - 0.5));
				vec3 sc = mix(mix(mix(t1.rgb, t2.rgb, k2), t4.rgb, k4), t3.rgb, k3);
				// (r10b) the tiles' own clods, prints and patches (3 cm to 1 m) stretched about their metre's mean, so they
				// read at the play camera; the finest grain and the tiles' choice are left as they are
				vec3 n1 = mix(textureLod(set_floor, vec3(s0, 0.0), 2.0).rgb, textureLod(set_floor, vec3(s1, 0.0), 2.0).rgb, tw);
				vec3 n2 = mix(textureLod(set_floor, vec3(s0 + 0.5, 1.0), 2.0).rgb, textureLod(set_floor, vec3(s1 + 0.5, 1.0), 2.0).rgb, tw);
				vec3 n3 = mix(textureLod(set_floor, vec3(s0, 2.0), 2.0).rgb, textureLod(set_floor, vec3(s1, 2.0), 2.0).rgb, tw);
				vec3 n4 = mix(textureLod(set_floor, vec3(s0 + 0.25, 3.0), 2.0).rgb, textureLod(set_floor, vec3(s1 + 0.25, 3.0), 2.0).rgb, tw);
				vec3 m1 = mix(textureLod(set_floor, vec3(s0, 0.0), 7.0).rgb, textureLod(set_floor, vec3(s1, 0.0), 7.0).rgb, tw);
				vec3 m2 = mix(textureLod(set_floor, vec3(s0 + 0.5, 1.0), 7.0).rgb, textureLod(set_floor, vec3(s1 + 0.5, 1.0), 7.0).rgb, tw);
				vec3 m3 = mix(textureLod(set_floor, vec3(s0, 2.0), 7.0).rgb, textureLod(set_floor, vec3(s1, 2.0), 7.0).rgb, tw);
				vec3 m4 = mix(textureLod(set_floor, vec3(s0 + 0.25, 3.0), 7.0).rgb, textureLod(set_floor, vec3(s1 + 0.25, 3.0), 7.0).rgb, tw);
				float ln = lum(mix(mix(mix(n1, n2, k2), n4, k4), n3, k3)), lm = lum(mix(mix(mix(m1, m2, k2), m4, k4), m3, k3));
				if (set_band > 0.001) sc *= clamp(pow(max(ln, 1e-4) / max(lm, 1e-4), set_band), 0.45, 2.2);
				if (sp_blur > 0.0) {
					vec3 b1 = mix(textureLod(set_floor, vec3(s0, 0.0), sp_blur_lod).rgb, textureLod(set_floor, vec3(s1, 0.0), sp_blur_lod).rgb, tw);
					vec3 b2 = mix(textureLod(set_floor, vec3(s0 + 0.5, 1.0), sp_blur_lod).rgb, textureLod(set_floor, vec3(s1 + 0.5, 1.0), sp_blur_lod).rgb, tw);
					vec3 b3 = mix(textureLod(set_floor, vec3(s0, 2.0), sp_blur_lod).rgb, textureLod(set_floor, vec3(s1, 2.0), sp_blur_lod).rgb, tw);
					vec3 b4 = mix(textureLod(set_floor, vec3(s0 + 0.25, 3.0), sp_blur_lod).rgb, textureLod(set_floor, vec3(s1 + 0.25, 3.0), sp_blur_lod).rgb, tw);
					blr = clamp(lum(mix(mix(mix(b1, b2, k2), b4, k4), b3, k3)) / max(lum(sc), 1e-4), 0.4, 2.5);
				}
				col = sc * set_gain;
			}
		col *= den_tint;
		col = mix(vec3(lum(col)), col, den_sat);
		// slow value masses: damper and drier ground
		float cl = mix(1.0, set_clouds, set_k);   // (r11) the slow clouds' share under the painted set
		col *= mix(1.0, mix(0.86, 1.08, smoothstep(0.3, 0.7, big)), cl);
		// (lead 6, round 5) value and colour masses on a 6-15 m scale, so no stretch of plain grain is wider than ~4 m:
		// damp dark earth in broad pools, moss creeping out from the banks' feet in tongues, leaf litter in drifts.
		float m1 = fbm(wpos.xz * 0.075 + vec2(-151.967, 196.961)), m2 = fbm(wpos.xz * 0.11 - 61.0), m3 = fbm(wpos.xz * 0.16 + 5.0);   // (m1's pcg2d offset chosen to match the old fract(sin) field, tester lane 23 Nov)
		float damp = smoothstep(0.5, 0.66, m1 + 0.12 * (mid - 0.5));
		col = mix(col, col * vec3(0.5, 0.48, 0.5), damp * 0.85 * cl);
		float mossm = smoothstep(0.42, 0.62, m2 + 0.35 * (1.0 - smoothstep(0.5, 4.0, inside)) - 0.18) * (1.0 - smoothstep(4.5, 7.0, inside));
		mossm *= smoothstep(0.3, 0.6, fbm(wpos.xz * 0.9 + 3.0));
		col = mix(col, vec3(0.085, 0.09, 0.05) * (0.8 + 0.5 * lum(cb[0]) / max(lum(ref), 1e-3)), mossm * moss_k * (1.0 - set_k));
		float leaf = smoothstep(0.58, 0.7, m3) * (1.0 - damp);
		col = mix(col, col * vec3(1.08, 0.86, 0.62), leaf * 0.6 * cl * smoothstep(0.4, 0.6, fbm(wpos.xz * 1.7)));
		// the open floor a step down overall (the boss clearing measured 74 against the target's 58)
		col *= 0.88;
		// (round 7) the rooms' open middles lifted (den_room.png's centre reads warm mid-brown; the room measured 33
		// against ~40), the banks' feet and edges left dark; the boss lair instead takes damp dark patches (66 against 58)
		float in_boss = boss_c.z > 0.0 ? 1.0 - smoothstep(boss_c.z * 0.85, boss_c.z * 1.05, distance(wpos.xz, boss_c.xy)) : 0.0;
		col *= mix(vec3(1.0), open_lift * vec3(1.0, 1.03, 1.12), smoothstep(2.5, 5.5, inside) * (1.0 - in_boss));   // (and a touch less orange: den_room.png's centre (86,62,51) against ours (81,55,38))
		float bdamp = smoothstep(0.47, 0.62, fbm(wpos.xz * 0.14 + 71.0) + 0.1 * (mid - 0.5)) * in_boss;
		col = mix(col, mix(vec3(dot(col, vec3(0.3, 0.55, 0.15))), col, 0.4) * vec3(0.6, 0.59, 0.6), bdamp * boss_damp);   // (grey shade: den_boss.png's (52,47,43), ours ran (71,52,45))   // (r11: neutral damp; 0.56/0.52/0.52 pushed the lair red, (R-B)/L .48)
		col = mix(vec3(dot(col, vec3(0.3, 0.55, 0.15))), col, mix(1.0, boss_sat, in_boss));
		col *= mix(vec3(1.0), boss_tint, in_boss);   // (r11: desaturated it read mauve (131,88,78); den_boss.png lit (147,109,84))   // (r11: den_boss.png's floor is tan-grey, its shade near neutral (52,47,43))
		col *= mix(1.0, boss_dim, in_boss);
		if (boss_c.z > 0.0 && boss_gloom > 0.0) {
			float bdg = distance(wpos.xz, boss_c.xy);
			float gl = boss_gloom * smoothstep(boss_c.z * 0.3, boss_c.z * 0.75, bdg) * (1.0 - smoothstep(boss_c.z * 1.2, boss_c.z * 1.5, bdg));
			col = mix(col, vec3(dot(col, vec3(0.3, 0.55, 0.15))) * gloom_tint, gloom_mix * gl) * (1.0 - 0.55 * gl);   // (den r14: the fall to a warm umber, was cool (0.8, 0.95, 1.25) at 0.7: the lair's edges read mauve, h 0-10 and 290-360)
		}
		// (den r14 item 8) fine grit in the open floor, at den_room.png's density (floorstat grit 4.8-9.3): stones and clods a hand across
		col *= 1.0 + open_grit * (gnoise(wpos.xz * 13.0) - 0.5) * smoothstep(1.5, 4.0, inside) * (1.0 - smoothstep(0.35, 0.8, steep));
		// the wall's foot in shade of the overhang
		col *= mix(mix(1.0, 0.45, rim_dark), 1.0, smoothstep(0.0, 2.2, inside));
		// (r12) the floor's darks no more saturated than den_chroma (HSV-like, in albedo): the seed-23 room's shade read
		// red-brown (satShade .35 against den_room.png's .21) where its damp and leaf masses fell; the lit floor keeps its warmth
		if (den_chroma < 1.0) {
			float cmx = max(col.r, max(col.g, col.b)), cmn = min(col.r, min(col.g, col.b));
			float cs = (cmx - cmn) / max(cmx, 1e-4), cl0 = lum(col);
			float ck = min(1.0, den_chroma / max(cs, 1e-4)) ;
			col = mix(col, vec3(cl0) + (col - vec3(cl0)) * ck, 1.0 - smoothstep(den_chroma_lo, den_chroma_hi, cl0));
		}
		// (den r17 L, R16 item 2) sunlight landing on the earth at each shaft's foot: the albedo lifted and warmed, its grain kept
		if (sp_n > 0) {
			float spm = 0.0;
			for (int k = 0; k < 64; k++) {
				if (k >= sp_n) break;
				vec2 q = wpos.xz - sp[k].xy;
				if (dot(q, q) > 9.0 * sp[k].z * sp[k].z) continue;
				float pa = dot(q, sp_lean) / 1.25, pb = dot(q, vec2(-sp_lean.y, sp_lean.x));
				float rr = sp[k].z * (0.82 + 0.36 * fbm(wpos.xz * 1.1 + sp[k].w));
				float m = 1.0 - smoothstep(rr - sp_edge, rr + 0.25 * sp_edge, length(vec2(pa, pb)));
				m *= 0.8 + 0.2 * smoothstep(0.3, 0.7, fbm(wpos.xz * 2.3 - sp[k].w));
				if (sp_smooth > 0.5) { float r0 = sp[k].z * 1.0; m = 1.0 - smoothstep(r0 - sp_soft, r0 + 0.1, length(vec2(pa, pb))); m = m * m * (3.0 - 2.0 * m); }
				if (sp[k].w >= 1000.0) m *= sp_lair;
				spm = max(spm, m);
			}
			if (sp_smooth > 0.5) {
				// the light multiplies the albedo: no term of its own, so the floor's grain is lit, not amplified; the sum is soft-capped
				col *= mix(1.0, blr, sp_blur * spm);   // (den r18 L4, R18 item 3) light flattens the grain: toward the blurred floor by sp_blur x mask
					float l0 = max(lum(col), 1e-4);
					float pg = mix(sp_gain, clamp(pow(pow(l0, 0.3333) + sp_dl, 3.0) / l0, sp_gmin, 3.5), sp_norm);   // (den r18 L4) a gain per pool against its own floor: the lift in OKLab-ish L, sp_dl
					float l1 = l0 * mix(1.0, pg, spm);
				float kn = sp_knee * sp_cap, l2 = l1 < kn ? l1 : kn + (sp_cap - kn) * tanh((l1 - kn) / (sp_cap - kn));
				col *= mix(vec3(1.0), sp_tint, spm) * (l2 / l1) * mix(1.0, pg, spm) * pow(clamp(l0 / sp_ref, 0.05, 4.0), sp_grain * spm);
			} else
			col *= mix(vec3(1.0), sp_gain * sp_tint, spm) * pow(clamp(lum(col) / sp_ref, 0.05, 4.0), sp_grain * spm);
		}
		// the pits: the depths go black
		// (a pit reads as a hole only when its throat is black from the lip down: no lit inner face)
		// (lead 6: a pit reads as a hole by a LIT lip, the painted pit face down its throat falling to black over a metre
		// and more, never a dark ring outside it: that ring read as a raised tub's shadow)
		// (pit solver, 15 Nov) The floor runs level to the mouth (vertex()); the hole is painted by a ray: from this point
		// on and down the view ray to where it meets the inner wall (pit_w >= 0, leaning in PIT_IN a metre), and that
		// wall's own normal goes to the cel light, so the face turned from the key falls in its shade band as any wall.
		// The wall is the painted pit face, falling to black over a metre and a half; past PIT_DEEP the bottom is black.
		// The lip: a hand-wide round-over whose normal tips into the hole, so it catches the key on the side facing it.
		float pw = pit_w(wpos.xz);
		if (pit_decals > 0.5) {
			// (pit decal solver, 15 Nov) The painted pit, laid on this level floor with its mouth fitted to the hole's
			// outline, draws the hole: the ray's black ran past its painted lip. Only plain black well inside, under it.
			if (pw < -0.4) col = vec3(0.003, 0.0025, 0.002);
		} else if (pw < 0.25) {
			const float e = 0.12;
			vec2 g0 = vec2(pit_w(wpos.xz + vec2(e, 0.0)) - pit_w(wpos.xz - vec2(e, 0.0)), pit_w(wpos.xz + vec2(0.0, e)) - pit_w(wpos.xz - vec2(0.0, e)));
			vec2 gin = -normalize(g0 + 1e-5);   // into the hole
			if (pw >= 0.0) {
				// (an albedo lift only, strongest on the key's side, the upper left: a tipped normal read as a dark ring)
				col *= 1.0 + (0.15 + 0.7 * smoothstep(-0.2, 0.8, dot(-gin, vec2(-0.7071, -0.7071)))) * (1.0 - smoothstep(0.0, 0.28, pw));
			} else {
				vec3 rd = -normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);
				float dy = max(-rd.y, 0.2);
				float tmax = PIT_DEEP / dy, t0 = 0.0, t1 = tmax;
				bool hit = false;
				for (int s = 1; s <= 32; s++) {
					float t = tmax * float(s) / 32.0;
					vec3 p = wpos + rd * t;
					if (pit_w(p.xz) + PIT_IN * dy * t >= 0.0) { t1 = t; hit = true; break; }
					t0 = t;
				}
				if (hit) {
					for (int s = 0; s < 6; s++) {
						float t = 0.5 * (t0 + t1);
						vec3 p = wpos + rd * t;
						if (pit_w(p.xz) + PIT_IN * dy * t >= 0.0) t1 = t; else t0 = t;
					}
					vec3 p = wpos + rd * t1;
					float d = dy * t1;   // metres below the mouth
					vec2 g = vec2(pit_w(p.xz + vec2(e, 0.0)) - pit_w(p.xz - vec2(e, 0.0)), pit_w(p.xz + vec2(0.0, e)) - pit_w(p.xz - vec2(0.0, e)));
					vec3 nw = normalize(vec3(-g.x, PIT_IN * length(g), -g.y) + vec3(0.0, 1e-5, 0.0));
					vec3 tz = mix(texture(den_alb, vec3(vec2(p.x, d) / den_m[5], 5.0)).rgb, texture(den_alb, vec3(vec2(p.x, d) / den_m[5] + 0.37, 5.0)).rgb, tw);
					vec3 tx = mix(texture(den_alb, vec3(vec2(p.z, d) / den_m[5], 5.0)).rgb, texture(den_alb, vec3(vec2(p.z, d) / den_m[5] + 0.37, 5.0)).rgb, tw);
					col = mix(tz, tx, smoothstep(0.35, 0.65, abs(nw.x))) * den_tint * 1.6;
					col *= mix(1.0, 0.06, smoothstep(0.05, 2.6, d));   // (lead 6: the target shows the slate wall over half the depth)
					// (lit as a face tipped up toward the mouth: the true wall's normal put it all in the black shade band)
					NORMAL = normalize((VIEW_MATRIX * vec4(normalize(nw + vec3(0.0, 1.1, 0.0)), 0.0)).xyz);
				} else {
					col = vec3(0.003, 0.0025, 0.002);
				}
			}
		}
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
