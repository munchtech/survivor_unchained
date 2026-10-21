// The Warden's heart (E7c, look bible 10 "The trick" 4): a fist-sized wet stone with cold light in its cracks.
// The mesh (tools/assets/env_heart.py) carries the broad chipped faces and the bake (COLOR: r edge wear, g cavity,
// b broad occlusion); everything finer is drawn here in the stone's own space, so it stays sharp at an 85 mm close-up:
//   the stone: the one stone sheet (stone_albedo, E5) triplanar, cool slate, its grain a bump;
//   the veins: cracks along the borders of a warped 3D cell pattern, their width set by a gate noise, so half the cells
//     open and each crack tapers from ~4 px to a 1 px free end (E7c r2); each sunk in a groove with a darkened lip, only
//     its off-white core over the glow threshold, a deeper blue light in the stone either side; a fine network at 30%;
//   the water: a wet film, a few low-roughness runs down the world from the top face, and a wet highlight on the top edge.
// beat (0..1, the heartbeat's shape) and level (the orb's Light) come from OrbView each frame, so the veins and the
// light pulse together, the same in every run (no TIME).
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D stone_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float tex_rep = 1.3;                 // the sheet's repeats across the unit stone
uniform vec3 tint : source_color = vec3(0.64, 0.68, 0.74);  // the heart's stone: a cool slate
uniform float stone_gain = 4.0;              // the sheet's brightness (E7c r2: 1.6 -> 4.0, toward E5's slate: ~1.4x luma at mid distance: AgX and the wet spec make it slow)
uniform float grain_bump = 0.004;            // the grain's relief (unit-stone lengths)
uniform vec3 core_color : source_color = vec3(0.686, 0.863, 1.0);  // a crack's core: off-white (sRGB 175,220,255)
uniform vec3 glow_color : source_color = vec3(0.235, 0.51, 1.0);   // the light about it (sRGB 60,130,255)
uniform float vein_scale = 0.9;              // crack cells across the unit stone
uniform float vein_warp = 0.22;
uniform float vein_core = 0.009;             // a crack's half-width at its widest (unit-stone lengths: ~4 px at c03 s8)
uniform float vein_glow_w = 0.03;            // the light in the stone either side
uniform float vein_energy = 2.0;             // the core's emission at level 1, beat mid
uniform float vein_glow = 0.35;              // the light in the stone's emission (kept under the glow threshold)
uniform float vein_gate = 0.5;               // how much of the cell border network is a crack (higher: fewer)
uniform float vein_taper = 0.22;             // how long a crack's taper to its free end is (noise units)
uniform float open_freq = 2.6;               // the gate's fast noise: cuts single cell edges (open cells, free ends)
uniform float fine_core = 0.0025;            // the fine network's half-width at its widest (~1 px at s8)
uniform float fine_gate = 0.42;
uniform float fine_energy = 0.3;             // the fine network's brightness, of the main cracks'
uniform float groove = 0.012;                // a crack's depth (unit-stone lengths)
uniform float scorch = 0.5;                  // the dark lip either side of a crack (albedo x (1 - scorch))
uniform float beat_amp = 0.38;               // the veins' swing about their mean (+-)
uniform float beat = 0.5;
uniform float level = 1.0;
uniform float wet = 1.0;
uniform float flow_t = 0.0;
uniform float film_dark = 0.8;              // the wet film darkens the stone to
uniform float streak_rough = 0.15;           // the runs of water
uniform float film_rough = 0.42;             // the wet film between them
uniform float sheen = 0.35;                  // the wet top edge's highlight
uniform vec3 sheen_color : source_color = vec3(0.62, 0.72, 0.86);
uniform float unit = 0.05;                   // world metres per unit-stone length (OrbView: its scale)

varying vec3 op;
varying vec3 on;
varying vec3 wd;   // world direction from the stone's middle, in unit-stone lengths (streaks run down this)

// An integer hash of a lattice point (its coordinates are whole numbers): exact, so two neighbouring pixels that
// reach the same point by different sums hash it alike (a sin() hash flips on one ulp: blocks in the cracks, E7c).
vec3 hash3(vec3 p) {
	uvec3 q = uvec3(ivec3(floor(p + 0.5)) + 65536);
	q = q * uvec3(1597334673u, 3812015801u, 2798796415u);
	q = uvec3(q.x ^ q.y ^ q.z) * uvec3(1597334673u, 3812015801u, 2798796415u);
	return vec3(q) * (1.0 / 4294967295.0);
}

float vnoise(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	vec3 u = f * f * (3.0 - 2.0 * f);
	float a = hash3(i).x, b = hash3(i + vec3(1, 0, 0)).x, c = hash3(i + vec3(0, 1, 0)).x, d = hash3(i + vec3(1, 1, 0)).x;
	float e = hash3(i + vec3(0, 0, 1)).x, g = hash3(i + vec3(1, 0, 1)).x, h = hash3(i + vec3(0, 1, 1)).x, k = hash3(i + vec3(1, 1, 1)).x;
	return mix(mix(mix(a, b, u.x), mix(c, d, u.x), u.y), mix(mix(e, g, u.x), mix(h, k, u.x), u.y), u.z);
}

// Distance to the nearest cell border (iq's exact voronoi borders), in cell units.
float border(vec3 x) {
	vec3 n = floor(x), f = fract(x);
	vec3 mg = vec3(0.0), mr = vec3(0.0);
	float md = 8.0;
	for (int k = -1; k <= 1; k++) for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
		vec3 g = vec3(float(i), float(j), float(k));
		vec3 r = g + hash3(n + g) - f;
		float d = dot(r, r);
		if (d < md) { md = d; mr = r; mg = g; }
	}
	md = 8.0;
	// (the second pass over 5x5x5 about the nearest: 3x3x3 jogs the borders where a farther pair is nearer)
	for (int k = -2; k <= 2; k++) for (int j = -2; j <= 2; j++) for (int i = -2; i <= 2; i++) {
		vec3 g = mg + vec3(float(i), float(j), float(k));
		vec3 r = g + hash3(n + g) - f;
		if (dot(mr - r, mr - r) > 1e-5) md = min(md, dot(0.5 * (mr + r), normalize(r - mr)));
	}
	return md;
}

void vertex() {
	op = VERTEX;
	on = NORMAL;
	wd = (mat3(MODEL_MATRIX) * VERTEX) / max(unit, 1e-4);
}

void fragment() {
	// --- the veins: the borders' distance in unit-stone lengths, warped. A crack's half-width follows a gate noise
	// (slow: where the cracks gather; fast: cuts single cell edges), so cells open and each crack tapers to a free end
	// instead of stopping square; the AA is a pixel's width (fwidth), so an end goes down to a 1 px line, then out.
	vec3 w = op + vein_warp * (vec3(vnoise(op * 2.3), vnoise(op * 2.3 + 17.1), vnoise(op * 2.3 + 41.7)) - 0.5);
	float d1 = border(w * vein_scale) / vein_scale;
	float d2 = border(w * vein_scale * 2.6 + 7.3) / (vein_scale * 2.6);
	float n1 = 0.55 * vnoise(op * 0.85 + 3.1) + 0.45 * vnoise(op * open_freq + 9.7);
	float t1 = smoothstep(vein_gate, vein_gate + vein_taper, n1);
	float n2 = 0.5 * vnoise(op * 1.1 + 11.3) + 0.5 * vnoise(op * open_freq * 1.7 + 23.1);
	float t2 = smoothstep(fine_gate, fine_gate + vein_taper, n2);
	float wv = 0.75 + 0.5 * vnoise(op * 3.0 + 5.0);
	float hw1 = vein_core * wv * t1, hw2 = fine_core * wv * t2;
	float f1 = max(fwidth(d1), 1e-5), f2 = max(fwidth(d2), 1e-5);
	float e1 = smoothstep(0.0, 0.12, t1), e2 = smoothstep(0.0, 0.12, t2);
	// (a crack thinner than a pixel draws a pixel's line at its share of the light, so a far stone isn't a full web)
	float c1 = e1 * (1.0 - smoothstep(hw1 - 0.6 * f1, hw1 + 0.6 * f1, d1)) * clamp(2.0 * hw1 / f1, 0.0, 1.0);
	float c2 = e2 * (1.0 - smoothstep(hw2 - 0.6 * f2, hw2 + 0.6 * f2, d2)) * clamp(2.0 * hw2 / f2, 0.0, 1.0) * (1.0 - c1);
	float core = c1 + c2 * fine_energy;          // emission weight
	float hole = max(c1, c2);                    // what the core covers of the stone
	float glow = max(t1 * exp(-max(d1 - hw1, 0.0) / vein_glow_w), fine_energy * t2 * exp(-max(d2 - hw2, 0.0) / (vein_glow_w * 0.4)));
	// (the lip: 1-2 px of darkened stone either side of the core, where the crack's edge breaks down into the groove)
	float lip = max(e1 * smoothstep(hw1 + 2.2 * f1, hw1 + 0.6 * f1, d1), e2 * 0.7 * smoothstep(hw2 + 1.6 * f2, hw2 + 0.5 * f2, d2)) * (1.0 - hole);

	// --- the stone: the sheet triplanar in its own space, cool slate, the bake's rims and cavities
	vec3 bw = pow(abs(normalize(on)), vec3(4.0));
	bw /= bw.x + bw.y + bw.z;
	vec3 q = op * tex_rep;
	vec4 st = texture(stone_tex, q.yz) * bw.x + texture(stone_tex, q.zx + 0.31) * bw.y + texture(stone_tex, q.xy + 0.67) * bw.z;
	float lum = dot(st.rgb, vec3(0.333));
	vec3 col = mix(vec3(lum), st.rgb, 0.35) * tint * stone_gain;
	col *= 1.0 + 0.45 * COLOR.r - 0.5 * COLOR.g - 0.3 * COLOR.b;
	col *= 1.0 - scorch * lip;
	// (the light in the stone either side of a crack tints its face, as light through a thin edge)
	col = mix(col, col * 0.75 + glow_color * 0.1, glow * 0.35);

	// --- the water: a film over it, a few runs down the world from the top face (columns in the world's x/z, each
	// reaching down its own length), the top face pooled; the top edge an unbroken wet highlight
	vec3 wn = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	float top = smoothstep(0.3, 0.8, wn.y);
	float col_n = vnoise(vec3(wd.x * 1.7, wd.y * 0.25 - flow_t * 0.15, wd.z * 1.7) + 31.0);
	float reach = mix(-0.9, 0.2, vnoise(vec3(wd.x * 1.7, 0.0, wd.z * 1.7) + 57.0));
	float streak = smoothstep(0.56, 0.66, col_n) * smoothstep(reach - 0.25, reach + 0.1, wd.y);
	streak = max(streak, top);
	float film = wet * (0.75 + 0.25 * streak);
	col *= mix(1.0, film_dark, film);
	ALBEDO = col * (1.0 - hole);
	ROUGHNESS = mix(0.8, mix(film_rough, streak_rough, streak), wet);
	SPECULAR = mix(0.5, 0.75, film);
	METALLIC = 0.0;
	float fres = pow(1.0 - clamp(dot(normalize(NORMAL), VIEW), 0.0, 1.0), 3.0);
	float edge = fres * smoothstep(0.05, 0.45, wn.y) * wet;

	// --- the relief: the cracks' grooves (as wide as the lip), the grain, the runs' ripple, by screen-space derivatives
	float g1 = t1 * (1.0 - smoothstep(0.0, hw1 + vein_core * 1.5, d1));
	float g2 = t2 * 0.5 * (1.0 - smoothstep(0.0, hw2 + fine_core * 1.5, d2));
	float h = (-groove * max(g1, g2) + grain_bump * lum + 0.0015 * streak * wet) * unit;
	vec3 dpx = dFdx(VERTEX), dpy = dFdy(VERTEX);
	vec3 nn = normalize(NORMAL);
	vec3 r1 = cross(dpy, nn), r2 = cross(nn, dpx);
	float det = dot(dpx, r1);
	vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
	NORMAL = normalize(abs(det) * nn - grad);

	// --- the light: the cores cross the glow threshold; the light in the stone stays under it; the wet edge a sheen
	float b = (1.0 - beat_amp) + 2.0 * beat_amp * beat;
	EMISSION = level * b * (core_color * core * vein_energy + glow_color * glow * vein_glow * (1.0 - hole))
		+ sheen_color * sheen * edge * (1.0 - hole);
}
